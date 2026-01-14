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



# Import mixins
from .simulation_indicators_mixin import SimulationIndicatorsMixin
from .simulation_trade_mixin import SimulationTradeMixin
from .simulation_results_mixin import SimulationResultsMixin

class StrategySimulator(
    SimulationIndicatorsMixin,
    SimulationTradeMixin,
    SimulationResultsMixin,
):
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

