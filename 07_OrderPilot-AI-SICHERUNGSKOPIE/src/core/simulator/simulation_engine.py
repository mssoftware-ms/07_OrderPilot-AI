"""Strategy Simulation Engine.

Runs backtests with configurable parameters against provided chart data.
This is a simplified simulator focused on the 5 base strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import numpy as np
import pandas as pd

from .strategy_params import StrategyName
from .simulation_signals import StrategySignalGenerator
from .result_types import SimulationResult, TradeRecord


@dataclass
class SimulationConfig:
    """Configuration for a simulation run.

    Supports two SL/TP modes:
    1. Percentage-based (legacy): stop_loss_pct, take_profit_pct
    2. ATR-based (from Bot-Tab): sl_atr_multiplier, tp_atr_multiplier

    When ATR multipliers are set (> 0), they take precedence over percentage values.

    Trailing Stop Modes:
    - PCT: Fixed percentage distance from current price
    - ATR: Volatility-based (ATR multiple), regime-adaptive
    - SWING: Bollinger Bands as support/resistance
    """

    strategy_name: StrategyName
    parameters: dict[str, Any]
    initial_capital: float = 1000.0  # 1000€ Startkapital
    position_size_pct: float = 1.0   # 100% = voller Einsatz pro Trade (1000€)
    slippage_pct: float = 0.001  # 0.1% slippage
    commission_pct: float = 0.001  # 0.1% commission
    # Legacy percentage-based SL/TP
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.05  # 5% take profit
    # ATR-based SL/TP (from Bot-Tab settings)
    sl_atr_multiplier: float = 0.0  # 0 = use stop_loss_pct instead
    tp_atr_multiplier: float = 0.0  # 0 = use take_profit_pct instead
    atr_period: int = 14  # ATR calculation period
    # Trailing Stop (from Bot-Tab settings)
    trailing_stop_enabled: bool = False
    trailing_stop_atr_multiplier: float = 1.5  # Trailing distance in ATR
    trailing_stop_mode: str = "ATR"  # PCT, ATR, SWING
    trailing_pct_distance: float = 1.0  # Distance in % for PCT mode
    trailing_activation_pct: float = 5.0  # Activation threshold (% profit)
    # Regime-adaptive trailing (from Bot-Tab)
    regime_adaptive: bool = True
    atr_trending_mult: float = 1.2  # ATR mult for trending markets
    atr_ranging_mult: float = 2.0  # ATR mult for ranging markets
    # Trading fees (from Bot-Tab BitUnix settings)
    maker_fee_pct: float = 0.0002  # 0.02% maker fee
    taker_fee_pct: float = 0.0006  # 0.06% taker fee
    # Trade direction filter
    trade_direction: str = "BOTH"  # AUTO, BOTH, LONG_ONLY, SHORT_ONLY
    # Leverage (for position sizing display)
    leverage: float = 1.0


class StrategySimulator:
    """Simulator for running strategies with configurable parameters.

    This class provides a simplified backtesting engine that:
    - Uses existing chart data (no data fetching)
    - Supports configurable strategy parameters
    - Calculates comprehensive performance metrics
    """

    def __init__(self, data: pd.DataFrame, symbol: str):
        """Initialize simulator with chart data.

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume
                  Index should be DatetimeIndex or have a 'timestamp' column
            symbol: Trading symbol
        """
        self.data = self._prepare_data(data)
        self.symbol = symbol
        self._signal_generator = StrategySignalGenerator(self.data)
        self._trades: list[TradeRecord] = []
        self._equity_curve: list[tuple[datetime, float]] = []

    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data."""
        df = data.copy()

        # Ensure we have required columns
        required = ["open", "high", "low", "close", "volume"]
        # Try lowercase first
        if not all(c in df.columns for c in required):
            # Try uppercase
            for col in required:
                if col.upper() in df.columns:
                    df[col] = df[col.upper()]

        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if "timestamp" in df.columns:
                df.set_index("timestamp", inplace=True)
            elif "date" in df.columns:
                df.set_index("date", inplace=True)
            else:
                df.index = pd.to_datetime(df.index)

        return df.sort_index()

    async def run_simulation(
        self,
        strategy_name: StrategyName | str,
        parameters: dict[str, Any],
        initial_capital: float = 1000.0,  # 1000€ Startkapital
        position_size_pct: float = 1.0,   # 100% = voller Einsatz pro Trade
        slippage_pct: float = 0.001,
        commission_pct: float = 0.001,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.05,
        progress_callback: Callable[[int, int], None] | None = None,
        entry_only: bool = False,
        entry_side: str = "long",
        entry_lookahead_mode: str = "session_end",
        entry_lookahead_bars: int | None = None,
        # ATR-based SL/TP from Bot-Tab settings
        sl_atr_multiplier: float = 0.0,
        tp_atr_multiplier: float = 0.0,
        atr_period: int = 14,
        # Trailing Stop from Bot-Tab settings
        trailing_stop_enabled: bool = False,
        trailing_stop_atr_multiplier: float = 1.5,
        trailing_stop_mode: str = "ATR",  # PCT, ATR, SWING
        trailing_pct_distance: float = 1.0,  # Distance in % for PCT mode
        trailing_activation_pct: float = 5.0,  # Activation threshold
        # Regime-adaptive trailing
        regime_adaptive: bool = True,
        atr_trending_mult: float = 1.2,
        atr_ranging_mult: float = 2.0,
        # Trading fees
        maker_fee_pct: float = 0.0002,
        taker_fee_pct: float = 0.0006,
        # Trade direction filter
        trade_direction: str = "BOTH",
        # Leverage
        leverage: float = 1.0,
    ) -> SimulationResult:
        """Run a single simulation with given parameters.

        Args:
            strategy_name: Strategy to simulate
            parameters: Strategy parameters
            initial_capital: Starting capital
            position_size_pct: Position size as percentage of capital
            slippage_pct: Slippage percentage
            commission_pct: Commission percentage
            stop_loss_pct: Default stop loss percentage (used if sl_atr_multiplier=0)
            take_profit_pct: Default take profit percentage (used if tp_atr_multiplier=0)
            progress_callback: Optional callback(current_bar, total_bars)
            entry_only: If True, only evaluate entry signals without full trade simulation
            entry_side: Side to evaluate ("long" or "short") when entry_only=True
            entry_lookahead_mode: Mode for lookahead evaluation ("session_end", "bars", "fixed")
            entry_lookahead_bars: Number of bars to look ahead (if mode="bars")
            sl_atr_multiplier: Stop loss in ATR multiples (0 = use stop_loss_pct)
            tp_atr_multiplier: Take profit in ATR multiples (0 = use take_profit_pct)
            atr_period: ATR calculation period (default 14)
            trailing_stop_enabled: Enable trailing stop
            trailing_stop_atr_multiplier: Trailing distance in ATR multiples
            trailing_stop_mode: Trailing mode (PCT, ATR, SWING)
            trailing_pct_distance: Distance in % for PCT mode
            trailing_activation_pct: Activation threshold (% profit)
            regime_adaptive: Enable regime-adaptive trailing
            atr_trending_mult: ATR mult for trending markets
            atr_ranging_mult: ATR mult for ranging markets
            maker_fee_pct: Maker fee as decimal (0.0002 = 0.02%)
            taker_fee_pct: Taker fee as decimal (0.0006 = 0.06%)
            trade_direction: Direction filter (AUTO, BOTH, LONG_ONLY, SHORT_ONLY)
            leverage: Leverage multiplier

        Returns:
            SimulationResult with trades and metrics
        """
        if isinstance(strategy_name, str):
            strategy_name = StrategyName(strategy_name)

        config = SimulationConfig(
            strategy_name=strategy_name,
            parameters=parameters,
            initial_capital=initial_capital,
            position_size_pct=position_size_pct,
            slippage_pct=slippage_pct,
            commission_pct=commission_pct,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            sl_atr_multiplier=sl_atr_multiplier,
            tp_atr_multiplier=tp_atr_multiplier,
            atr_period=atr_period,
            trailing_stop_enabled=trailing_stop_enabled,
            trailing_stop_atr_multiplier=trailing_stop_atr_multiplier,
            trailing_stop_mode=trailing_stop_mode,
            trailing_pct_distance=trailing_pct_distance,
            trailing_activation_pct=trailing_activation_pct,
            regime_adaptive=regime_adaptive,
            atr_trending_mult=atr_trending_mult,
            atr_ranging_mult=atr_ranging_mult,
            maker_fee_pct=maker_fee_pct,
            taker_fee_pct=taker_fee_pct,
            trade_direction=trade_direction,
            leverage=leverage,
        )

        # Calculate indicators and signals
        signals = self._generate_signals(strategy_name, parameters)

        # Entry-only mode: only evaluate entry signals without full trade simulation
        if entry_only:
            result = self._run_entry_only_simulation(
                strategy_name=strategy_name,
                parameters=parameters,
                signals=signals,
                initial_capital=initial_capital,
                entry_side=entry_side,
                entry_lookahead_mode=entry_lookahead_mode,
                entry_lookahead_bars=entry_lookahead_bars,
            )
            return result

        # Full simulation: Simulate trades
        trades = self._simulate_trades(signals, config)

        # Calculate metrics
        result = self._calculate_result(
            strategy_name=strategy_name.value,
            parameters=parameters,
            trades=trades,
            initial_capital=initial_capital,
        )

        return result

    def _generate_signals(
        self,
        strategy_name: StrategyName,
        parameters: dict[str, Any],
    ) -> pd.DataFrame:
        """Generate trading signals based on strategy logic."""
        return self._signal_generator.generate(strategy_name, parameters)

    def _run_entry_only_simulation(
        self,
        strategy_name: StrategyName,
        parameters: dict[str, Any],
        signals: pd.DataFrame,
        initial_capital: float,
        entry_side: str = "long",
        entry_lookahead_mode: str = "session_end",
        entry_lookahead_bars: int | None = None,
    ) -> SimulationResult:
        """Run entry-only simulation evaluating entry signal quality.

        Args:
            strategy_name: Strategy being evaluated
            parameters: Strategy parameters
            signals: DataFrame with signals and OHLCV data
            initial_capital: Starting capital
            entry_side: Side to evaluate ("long" or "short")
            entry_lookahead_mode: How to evaluate entries ("session_end", "bars", "fixed")
            entry_lookahead_bars: Number of bars to look ahead for evaluation

        Returns:
            SimulationResult with entry quality metrics
        """
        entries = []
        entry_scores = []

        # Determine lookahead bars
        if entry_lookahead_bars is None:
            entry_lookahead_bars = min(20, len(signals) // 10) or 10

        signal_value = 1 if entry_side == "long" else -1

        for i, (timestamp, row) in enumerate(signals.iterrows()):
            signal = row.get("signal", 0)

            # Check for entry signal matching the side
            if signal == signal_value or (entry_side == "long" and signal == 1):
                entry_price = row["close"]

                # Calculate entry quality based on lookahead
                lookahead_end = min(i + entry_lookahead_bars, len(signals) - 1)
                if lookahead_end > i:
                    future_prices = signals.iloc[i + 1 : lookahead_end + 1]

                    if entry_side == "long":
                        # For long: positive if price goes up
                        max_price = future_prices["high"].max()
                        min_price = future_prices["low"].min()
                        max_gain_pct = (max_price - entry_price) / entry_price * 100
                        max_loss_pct = (entry_price - min_price) / entry_price * 100
                    else:
                        # For short: positive if price goes down
                        max_price = future_prices["high"].max()
                        min_price = future_prices["low"].min()
                        max_gain_pct = (entry_price - min_price) / entry_price * 100
                        max_loss_pct = (max_price - entry_price) / entry_price * 100

                    # Entry score: reward/risk ratio
                    entry_score = max_gain_pct / max_loss_pct if max_loss_pct > 0 else max_gain_pct
                    entry_scores.append(entry_score)

                    entries.append({
                        "timestamp": timestamp,
                        "entry_price": entry_price,
                        "side": entry_side,
                        "max_gain_pct": max_gain_pct,
                        "max_loss_pct": max_loss_pct,
                        "entry_score": entry_score,
                    })

        # Calculate aggregate metrics
        total_entries = len(entries)
        avg_entry_score = np.mean(entry_scores) if entry_scores else 0.0
        positive_entries = sum(1 for e in entries if e["max_gain_pct"] > e["max_loss_pct"])
        win_rate = positive_entries / total_entries if total_entries > 0 else 0.0

        # Create synthetic trades for result compatibility
        trades: list[TradeRecord] = []
        for entry in entries:
            # Create a synthetic trade representing the entry evaluation
            trades.append(TradeRecord(
                entry_time=entry["timestamp"],
                entry_price=entry["entry_price"],
                exit_time=entry["timestamp"],  # Same as entry for entry-only
                exit_price=entry["entry_price"] * (1 + entry["max_gain_pct"] / 100),
                side=entry["side"],
                size=1.0,
                pnl=entry["max_gain_pct"] - entry["max_loss_pct"],
                pnl_pct=(entry["max_gain_pct"] - entry["max_loss_pct"]) / 100,
                exit_reason="ENTRY_EVALUATION",
                stop_loss=entry["entry_price"] * (1 - entry["max_loss_pct"] / 100),
                take_profit=entry["entry_price"] * (1 + entry["max_gain_pct"] / 100),
                commission=0.0,
            ))

        return SimulationResult(
            strategy_name=strategy_name.value,
            parameters=parameters,
            symbol=self.symbol,
            trades=trades,
            total_pnl=sum(t.pnl for t in trades),
            total_pnl_pct=avg_entry_score * 100 if avg_entry_score else 0.0,
            win_rate=win_rate,
            profit_factor=avg_entry_score if avg_entry_score > 0 else 0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=None,
            sortino_ratio=None,
            total_trades=total_entries,
            winning_trades=positive_entries,
            losing_trades=total_entries - positive_entries,
            avg_win=np.mean([e["max_gain_pct"] for e in entries if e["max_gain_pct"] > e["max_loss_pct"]]) if positive_entries > 0 else 0.0,
            avg_loss=np.mean([e["max_loss_pct"] for e in entries if e["max_gain_pct"] <= e["max_loss_pct"]]) if (total_entries - positive_entries) > 0 else 0.0,
            largest_win=max((e["max_gain_pct"] for e in entries), default=0.0),
            largest_loss=max((e["max_loss_pct"] for e in entries), default=0.0),
            avg_trade_duration_seconds=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            initial_capital=initial_capital,
            final_capital=initial_capital,
            data_start=self.data.index[0],
            data_end=self.data.index[-1],
            bars_processed=len(self.data),
        )

    def _breakout_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._breakout_signals(df, params)

    def _momentum_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._momentum_signals(df, params)

    def _mean_reversion_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._mean_reversion_signals(df, params)

    def _trend_following_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._trend_following_signals(df, params)

    def _scalping_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._scalping_signals(df, params)

    def _bollinger_squeeze_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._bollinger_squeeze_signals(df, params)

    def _trend_pullback_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._trend_pullback_signals(df, params)

    def _opening_range_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._opening_range_signals(df, params)

    def _regime_hybrid_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        return self._signal_generator._regime_hybrid_signals(df, params)

    def _simulate_trades(
        self,
        signals_df: pd.DataFrame,
        config: SimulationConfig,
    ) -> list[TradeRecord]:
        """Simulate trades based on signals.

        Supports ATR-based SL/TP, trailing stop from Bot-Tab settings,
        trade direction filter, and maker/taker fees.
        """
        trades: list[TradeRecord] = []
        position: dict | None = None
        capital = config.initial_capital

        # Calculate ATR for the entire dataset if ATR-based SL/TP is enabled
        atr_series = None
        if config.sl_atr_multiplier > 0 or config.tp_atr_multiplier > 0 or config.trailing_stop_enabled:
            atr_series = self._calculate_atr(signals_df, config.atr_period)

        # Calculate Bollinger Bands for SWING mode
        bb_lower, bb_upper = None, None
        if config.trailing_stop_mode == "SWING" and config.trailing_stop_enabled:
            bb_lower, bb_upper = self._calculate_bollinger_bands(signals_df)

        # Calculate ADX for regime detection (regime-adaptive trailing)
        adx_series = None
        if config.regime_adaptive and config.trailing_stop_enabled:
            adx_series = self._calculate_adx(signals_df)

        for i, (timestamp, row) in enumerate(signals_df.iterrows()):
            signal = row["signal"]
            price = row["close"]
            current_atr = atr_series.iloc[i] if atr_series is not None else 0.0
            current_adx = adx_series.iloc[i] if adx_series is not None else 25.0
            current_bb_lower = bb_lower.iloc[i] if bb_lower is not None else 0.0
            current_bb_upper = bb_upper.iloc[i] if bb_upper is not None else 0.0

            # Check for exit conditions if in position
            if position is not None:
                exit_info = self._check_exit_conditions(
                    row, signal, position, config, current_atr
                )
                if exit_info:
                    trade, capital = self._close_position(
                        position,
                        timestamp,
                        exit_info,
                        config,
                        capital,
                    )
                    trades.append(trade)
                    position = None
                elif config.trailing_stop_enabled:
                    # Update trailing stop if price moved favorably
                    position = self._update_trailing_stop(
                        position, price, current_atr, config,
                        current_adx=current_adx,
                        bb_lower=current_bb_lower,
                        bb_upper=current_bb_upper,
                    )

            # Check for entry signal with direction filter
            if position is None:
                entry_side = self._check_entry_signal(signal, config)
                if entry_side:
                    position, capital = self._open_position(
                        timestamp, price, config, capital, current_atr, side=entry_side
                    )

        # Close any open position at end
        if position is not None:
            trade = self._close_position_end(signals_df, position, config)
            trades.append(trade)

        return trades

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

    def _calculate_bollinger_bands(
        self, df: pd.DataFrame, period: int = 20, std_mult: float = 2.0
    ) -> tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands for SWING trailing mode.

        Returns:
            Tuple of (lower_band, upper_band)
        """
        close = df["close"]
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        lower_band = sma - (std * std_mult)
        upper_band = sma + (std * std_mult)

        # Backfill NaN values
        lower_band = lower_band.bfill()
        upper_band = upper_band.bfill()

        return lower_band, upper_band

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX (Average Directional Index) for regime detection.

        ADX > 25 = Trending market
        ADX < 20 = Ranging market
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # True Range
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[(plus_dm < minus_dm) | (plus_dm < 0)] = 0
        minus_dm[(minus_dm < plus_dm) | (minus_dm < 0)] = 0

        # Wilder's smoothing
        alpha = 1.0 / period
        atr = tr.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean() / atr)

        # ADX calculation
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

        # Backfill NaN values
        adx = adx.bfill().fillna(25.0)

        return adx

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range using Wilder's Smoothing Method.

        Reference: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-true-range-atr
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Use Wilder's smoothing (EMA with alpha = 1/period)
        alpha = 1.0 / period
        atr = true_range.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

        # Fill NaN values with the first valid ATR (backfill)
        atr = atr.bfill()
        return atr

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

    def _calculate_result(
        self,
        strategy_name: str,
        parameters: dict[str, Any],
        trades: list[TradeRecord],
        initial_capital: float,
    ) -> SimulationResult:
        """Calculate simulation result from trades."""
        if not trades:
            return self._empty_result(strategy_name, parameters, initial_capital)

        metrics = self._calculate_trade_metrics(trades, initial_capital)

        return SimulationResult(
            strategy_name=strategy_name,
            parameters=parameters,
            symbol=self.symbol,
            trades=trades,
            total_pnl=metrics["total_pnl"],
            total_pnl_pct=(metrics["total_pnl"] / initial_capital) * 100,
            win_rate=metrics["win_rate"],
            profit_factor=metrics["profit_factor"],
            max_drawdown_pct=metrics["max_drawdown_pct"],
            sharpe_ratio=metrics["sharpe_ratio"],
            sortino_ratio=metrics["sortino_ratio"],
            total_trades=len(trades),
            winning_trades=metrics["total_wins"],
            losing_trades=metrics["total_losses"],
            avg_win=metrics["avg_win"],
            avg_loss=metrics["avg_loss"],
            largest_win=metrics["largest_win"],
            largest_loss=metrics["largest_loss"],
            avg_trade_duration_seconds=metrics["avg_duration"],
            max_consecutive_wins=metrics["max_cons_wins"],
            max_consecutive_losses=metrics["max_cons_losses"],
            initial_capital=initial_capital,
            final_capital=metrics["final_capital"],
            data_start=self.data.index[0],
            data_end=self.data.index[-1],
            bars_processed=len(self.data),
        )

    def _empty_result(
        self,
        strategy_name: str,
        parameters: dict[str, Any],
        initial_capital: float,
    ) -> SimulationResult:
        return SimulationResult(
            strategy_name=strategy_name,
            parameters=parameters,
            symbol=self.symbol,
            trades=[],
            total_pnl=0.0,
            total_pnl_pct=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=None,
            sortino_ratio=None,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            avg_win=0.0,
            avg_loss=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            avg_trade_duration_seconds=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            initial_capital=initial_capital,
            final_capital=initial_capital,
            data_start=self.data.index[0],
            data_end=self.data.index[-1],
            bars_processed=len(self.data),
        )

    def _calculate_trade_metrics(
        self,
        trades: list[TradeRecord],
        initial_capital: float,
    ) -> dict[str, Any]:
        total_pnl = sum(t.pnl for t in trades)
        winning_trades = [t for t in trades if t.is_winner]
        losing_trades = [t for t in trades if not t.is_winner]

        total_wins = len(winning_trades)
        total_losses = len(losing_trades)
        win_rate = total_wins / len(trades) if trades else 0.0

        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        profit_factor = profit_factor if profit_factor != float("inf") else 99.99

        avg_win = gross_profit / total_wins if total_wins > 0 else 0.0
        avg_loss = gross_loss / total_losses if total_losses > 0 else 0.0

        largest_win = max((t.pnl for t in winning_trades), default=0.0)
        largest_loss = min((t.pnl for t in losing_trades), default=0.0)

        max_dd = self._max_drawdown_pct(trades, initial_capital)
        final_capital = initial_capital + total_pnl

        max_cons_wins, max_cons_losses = self._max_consecutive_runs(trades)
        avg_duration = self._avg_trade_duration(trades)
        sharpe, sortino = self._risk_ratios(trades)

        return {
            "total_pnl": total_pnl,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_dd,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "avg_duration": avg_duration,
            "max_cons_wins": max_cons_wins,
            "max_cons_losses": max_cons_losses,
            "final_capital": final_capital,
        }

    def _max_drawdown_pct(self, trades: list[TradeRecord], initial_capital: float) -> float:
        equity = initial_capital
        peak = equity
        max_dd = 0.0
        for trade in trades:
            equity += trade.pnl
            peak = max(peak, equity)
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)
        return max_dd * 100

    def _max_consecutive_runs(self, trades: list[TradeRecord]) -> tuple[int, int]:
        max_cons_wins = max_cons_losses = 0
        current_wins = current_losses = 0
        for trade in trades:
            if trade.is_winner:
                current_wins += 1
                current_losses = 0
                max_cons_wins = max(max_cons_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_cons_losses = max(max_cons_losses, current_losses)
        return max_cons_wins, max_cons_losses

    def _avg_trade_duration(self, trades: list[TradeRecord]) -> float:
        durations = [t.duration_seconds for t in trades]
        return np.mean(durations) if durations else 0.0

    def _risk_ratios(self, trades: list[TradeRecord]) -> tuple[float | None, float | None]:
        returns = [t.pnl_pct for t in trades]
        if len(returns) <= 1:
            return None, None
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        neg_returns = [r for r in returns if r < 0]
        downside_std = np.std(neg_returns) if neg_returns else 0.0
        sharpe = (mean_return * 252) / (std_return * np.sqrt(252)) if std_return > 0 else None
        sortino = (mean_return * 252) / (downside_std * np.sqrt(252)) if downside_std > 0 else None
        return sharpe, sortino

    # Helper methods for indicator calculations
    def _true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range."""
        return self._signal_generator._true_range(df)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        return self._signal_generator._calculate_rsi(prices, period)

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        return self._signal_generator._calculate_obv(df)

    def get_entry_exit_points(
        self, result: SimulationResult
    ) -> list[dict[str, Any]]:
        """Extract entry/exit points for chart visualization.

        Returns list of dicts with timestamp, price, type, and metadata.
        """
        points = []

        for trade in result.trades:
            # Entry point
            points.append(
                {
                    "timestamp": trade.entry_time,
                    "price": trade.entry_price,
                    "type": "entry",
                    "side": trade.side,
                    "stop_loss": trade.stop_loss,
                    "take_profit": trade.take_profit,
                }
            )
            # Exit point
            points.append(
                {
                    "timestamp": trade.exit_time,
                    "price": trade.exit_price,
                    "type": "exit",
                    "side": trade.side,
                    "reason": trade.exit_reason,
                    "pnl": trade.pnl,
                }
            )

        return points
