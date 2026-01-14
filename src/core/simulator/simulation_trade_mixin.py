from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

class SimulationTradeMixin:
    """Trade management (entry, exit, trailing stop)"""

    def _check_entry_signal(self, signal: int, config: SimulationConfig) -> str | None:
        """Check if entry signal matches trade direction filter.

        Args:
            signal: Trading signal (1=long, -1=short)
            config: Simulation configuration

        Returns:
            Entry side ("long" or "short") or None if filtered out
        """
        direction = config.trade_direction

        if signal == 1:  # Long signal
            if direction in ("BOTH", "AUTO", "LONG_ONLY"):
                return "long"
        elif signal == -1:  # Short signal
            if direction in ("BOTH", "AUTO", "SHORT_ONLY"):
                return "short"

        return None

    def _open_position(
        self,
        timestamp,
        price: float,
        config: SimulationConfig,
        capital: float,
        current_atr: float = 0.0,
        side: str = "long",
    ) -> tuple[dict, float]:
        """Open a new position with ATR-based or percentage-based SL/TP.

        Args:
            timestamp: Entry timestamp
            price: Entry price
            config: Simulation configuration
            capital: Available capital
            current_atr: Current ATR value (used if ATR-based SL/TP enabled)
            side: Position side ("long" or "short")

        Returns:
            Tuple of (position dict, remaining capital)
        """
        # Apply slippage
        if side == "long":
            entry_price = price * (1 + config.slippage_pct)
        else:
            entry_price = price * (1 - config.slippage_pct)

        position_value = capital * config.position_size_pct
        size = position_value / entry_price

        # Entry is typically a market order (taker fee)
        entry_fee_pct = config.taker_fee_pct if config.taker_fee_pct > 0 else config.commission_pct
        commission = position_value * entry_fee_pct

        # Calculate SL/TP based on ATR or percentage
        if config.sl_atr_multiplier > 0 and current_atr > 0:
            # ATR-based stop loss (from Bot-Tab settings)
            sl_distance = current_atr * config.sl_atr_multiplier
            if side == "long":
                stop_loss = entry_price - sl_distance
            else:
                stop_loss = entry_price + sl_distance
        else:
            # Percentage-based stop loss (legacy)
            if side == "long":
                stop_loss = entry_price * (1 - config.stop_loss_pct)
            else:
                stop_loss = entry_price * (1 + config.stop_loss_pct)

        if config.tp_atr_multiplier > 0 and current_atr > 0:
            # ATR-based take profit (from Bot-Tab settings)
            tp_distance = current_atr * config.tp_atr_multiplier
            if side == "long":
                take_profit = entry_price + tp_distance
            else:
                take_profit = entry_price - tp_distance
        else:
            # Percentage-based take profit (legacy)
            if side == "long":
                take_profit = entry_price * (1 + config.take_profit_pct)
            else:
                take_profit = entry_price * (1 - config.take_profit_pct)

        position = {
            "entry_time": timestamp,
            "entry_price": entry_price,
            "size": size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "commission": commission,
            "side": side,
            "entry_atr": current_atr,
            "trailing_stop_active": False,
        }
        return position, capital - commission

    def _close_position(
        self,
        position: dict,
        timestamp,
        exit_info: dict,
        config: SimulationConfig,
        capital: float,
    ) -> tuple[TradeRecord, float]:
        """Close position and calculate P&L with maker/taker fees."""
        exit_price = exit_info["price"]
        side = position.get("side", "long")
        exit_reason = exit_info["reason"]

        # Calculate P&L based on side
        if side == "long":
            pnl = (exit_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - exit_price) * position["size"]

        # Use maker fee for limit orders (TP, trailing), taker for market (SL, signal)
        # TP and trailing stops are typically limit orders (maker)
        # SL and signal exits are typically market orders (taker)
        if exit_reason in ("TAKE_PROFIT", "TRAILING_STOP"):
            exit_fee_pct = config.maker_fee_pct
        else:
            exit_fee_pct = config.taker_fee_pct

        # Fallback to commission_pct if fees are 0 (legacy mode)
        if exit_fee_pct == 0:
            exit_fee_pct = config.commission_pct

        exit_commission = exit_price * position["size"] * exit_fee_pct
        total_commission = exit_commission + position["commission"]
        pnl -= exit_commission

        trade = TradeRecord(
            entry_time=position["entry_time"],
            entry_price=position["entry_price"],
            exit_time=timestamp,
            exit_price=exit_price,
            side=side,
            size=position["size"],
            pnl=pnl,
            pnl_pct=pnl / (position["entry_price"] * position["size"]),
            exit_reason=exit_reason,
            stop_loss=position["stop_loss"],
            take_profit=position["take_profit"],
            commission=total_commission,
        )
        return trade, capital + pnl

    def _close_position_end(
        self,
        signals_df: pd.DataFrame,
        position: dict,
        config: SimulationConfig,
    ) -> TradeRecord:
        """Close position at end of data."""
        last_row = signals_df.iloc[-1]
        exit_price = last_row["close"]
        side = position.get("side", "long")

        # Calculate P&L based on side
        if side == "long":
            pnl = (exit_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - exit_price) * position["size"]

        commission = exit_price * position["size"] * config.commission_pct
        pnl -= commission

        return TradeRecord(
            entry_time=position["entry_time"],
            entry_price=position["entry_price"],
            exit_time=signals_df.index[-1],
            exit_price=exit_price,
            side=side,
            size=position["size"],
            pnl=pnl,
            pnl_pct=pnl / (position["entry_price"] * position["size"]),
            exit_reason="END_OF_DATA",
            stop_loss=position["stop_loss"],
            take_profit=position["take_profit"],
            commission=commission + position["commission"],
        )

    def _check_exit_conditions(
        self,
        row: pd.Series,
        signal: int,
        position: dict,
        config: SimulationConfig,
        current_atr: float = 0.0,
    ) -> dict | None:
        """Check exit conditions including trailing stop.

        Args:
            row: Current bar data
            signal: Trading signal (-1=sell, 0=hold, 1=buy)
            position: Current position dict
            config: Simulation configuration
            current_atr: Current ATR value for trailing stop updates

        Returns:
            Exit info dict or None if no exit triggered
        """
        side = position.get("side", "long")

        if side == "long":
            # Long position exits
            if row["low"] <= position["stop_loss"]:
                reason = "TRAILING_STOP" if position.get("trailing_stop_active") else "STOP_LOSS"
                return {"price": position["stop_loss"], "reason": reason}
            if row["high"] >= position["take_profit"]:
                return {"price": position["take_profit"], "reason": "TAKE_PROFIT"}
            if signal == -1:
                return {"price": row["close"] * (1 - config.slippage_pct), "reason": "SIGNAL"}
        else:
            # Short position exits
            if row["high"] >= position["stop_loss"]:
                reason = "TRAILING_STOP" if position.get("trailing_stop_active") else "STOP_LOSS"
                return {"price": position["stop_loss"], "reason": reason}
            if row["low"] <= position["take_profit"]:
                return {"price": position["take_profit"], "reason": "TAKE_PROFIT"}
            if signal == 1:
                return {"price": row["close"] * (1 + config.slippage_pct), "reason": "SIGNAL"}

        return None

    def _update_trailing_stop(
        self,
        position: dict,
        current_price: float,
        current_atr: float,
        config: SimulationConfig,
        current_adx: float = 25.0,
        bb_lower: float = 0.0,
        bb_upper: float = 0.0,
    ) -> dict:
        """Update trailing stop if price moved favorably.

        Supports three trailing modes:
        - PCT: Fixed percentage distance from current price
        - ATR: Volatility-based (ATR multiple), regime-adaptive
        - SWING: Bollinger Bands as support/resistance

        For long positions: move stop up when price increases
        For short positions: move stop down when price decreases
        """
        side = position.get("side", "long")
        entry_price = position["entry_price"]

        # Check activation threshold (profit % before trailing activates)
        if config.trailing_activation_pct > 0:
            if side == "long":
                profit_pct = (current_price - entry_price) / entry_price * 100
            else:
                profit_pct = (entry_price - current_price) / entry_price * 100

            if profit_pct < config.trailing_activation_pct:
                # Not enough profit yet, don't activate trailing
                return position

        # Calculate trailing distance based on mode
        mode = config.trailing_stop_mode

        if mode == "PCT":
            # Fixed percentage distance
            trailing_distance = current_price * (config.trailing_pct_distance / 100.0)

        elif mode == "SWING":
            # Bollinger Band based - use BB as dynamic support/resistance
            if side == "long":
                # For long: use lower BB as trailing stop
                new_trailing_stop = bb_lower
                if new_trailing_stop > position["stop_loss"]:
                    position["stop_loss"] = new_trailing_stop
                    position["trailing_stop_active"] = True
                return position
            else:
                # For short: use upper BB as trailing stop
                new_trailing_stop = bb_upper
                if new_trailing_stop < position["stop_loss"]:
                    position["stop_loss"] = new_trailing_stop
                    position["trailing_stop_active"] = True
                return position

        else:  # ATR mode (default)
            # Regime-adaptive ATR multiplier
            if config.regime_adaptive:
                if current_adx > 25:
                    # Trending market: use tighter stop
                    atr_mult = config.atr_trending_mult
                elif current_adx < 20:
                    # Ranging market: use wider stop
                    atr_mult = config.atr_ranging_mult
                else:
                    # Neutral: use base multiplier
                    atr_mult = config.trailing_stop_atr_multiplier
            else:
                atr_mult = config.trailing_stop_atr_multiplier

            trailing_distance = current_atr * atr_mult

        # Apply trailing stop (PCT and ATR modes)
        if side == "long":
            # For long: trailing stop follows price up
            new_trailing_stop = current_price - trailing_distance
            if new_trailing_stop > position["stop_loss"]:
                position["stop_loss"] = new_trailing_stop
                position["trailing_stop_active"] = True
        else:
            # For short: trailing stop follows price down
            new_trailing_stop = current_price + trailing_distance
            if new_trailing_stop < position["stop_loss"]:
                position["stop_loss"] = new_trailing_stop
                position["trailing_stop_active"] = True

        return position

