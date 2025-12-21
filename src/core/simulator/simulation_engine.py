"""Strategy Simulation Engine.

Runs backtests with configurable parameters against provided chart data.
This is a simplified simulator focused on the 5 base strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable

import numpy as np
import pandas as pd

from .strategy_params import StrategyName, get_strategy_parameters
from .result_types import SimulationResult, TradeRecord

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""

    strategy_name: StrategyName
    parameters: dict[str, Any]
    initial_capital: float = 1000.0  # 1000€ Startkapital
    position_size_pct: float = 1.0   # 100% = voller Einsatz pro Trade (1000€)
    slippage_pct: float = 0.001  # 0.1% slippage
    commission_pct: float = 0.001  # 0.1% commission
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.05  # 5% take profit
    max_spread_pct: float | None = None  # Max allowed bar range (pct) for entry
    min_hold_seconds: int = 0  # Minimum hold time before signal exit


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

    def _is_crypto_symbol(self) -> bool:
        """Basic heuristic for crypto symbols."""
        return "/" in self.symbol

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
    ) -> SimulationResult:
        """Run a single simulation with given parameters.

        Args:
            strategy_name: Strategy to simulate
            parameters: Strategy parameters
            initial_capital: Starting capital
            position_size_pct: Position size as percentage of capital
            slippage_pct: Slippage percentage
            commission_pct: Commission percentage
            stop_loss_pct: Default stop loss percentage
            take_profit_pct: Default take profit percentage
            progress_callback: Optional callback(current_bar, total_bars)

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
            max_spread_pct=parameters.get("max_spread_pct"),
            min_hold_seconds=int(parameters.get("min_hold_seconds", 0) or 0),
        )

        # Calculate indicators and signals
        signals = self._generate_signals(strategy_name, parameters)

        if entry_only:
            entry_stats = self._simulate_entries(
                signals,
                entry_side,
                entry_lookahead_mode=entry_lookahead_mode,
                entry_lookahead_bars=entry_lookahead_bars,
            )
            return SimulationResult(
                strategy_name=strategy_name.value,
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
                total_trades=entry_stats["entry_count"],
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
                entry_only=True,
                entry_side=entry_side.lower(),
                entry_count=entry_stats["entry_count"],
                entry_score=entry_stats["entry_score"],
                entry_avg_offset_pct=entry_stats["entry_avg_offset_pct"],
                entry_best_price=entry_stats["entry_best_price"],
                entry_best_time=entry_stats["entry_best_time"],
                entry_points=entry_stats["entry_points"],
            )

        # Simulate trades
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
        """Generate trading signals based on strategy logic.

        Returns DataFrame with 'signal' column: 1=buy, -1=sell, 0=hold
        """
        df = self.data.copy()

        if strategy_name == StrategyName.BREAKOUT:
            signals = self._breakout_signals(df, parameters)
        elif strategy_name == StrategyName.MOMENTUM:
            signals = self._momentum_signals(df, parameters)
        elif strategy_name == StrategyName.MEAN_REVERSION:
            signals = self._mean_reversion_signals(df, parameters)
        elif strategy_name == StrategyName.TREND_FOLLOWING:
            signals = self._trend_following_signals(df, parameters)
        elif strategy_name == StrategyName.SCALPING:
            signals = self._scalping_signals(df, parameters)
        elif strategy_name == StrategyName.BOLLINGER_SQUEEZE:
            signals = self._bollinger_squeeze_signals(df, parameters)
        elif strategy_name == StrategyName.TREND_PULLBACK:
            signals = self._trend_pullback_signals(df, parameters)
        elif strategy_name == StrategyName.OPENING_RANGE:
            signals = self._opening_range_signals(df, parameters)
        elif strategy_name == StrategyName.REGIME_HYBRID:
            signals = self._regime_hybrid_signals(df, parameters)
        else:
            signals = pd.Series(0, index=df.index)

        df["signal"] = signals
        return df

    def _breakout_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate breakout strategy signals."""
        sr_window = params.get("sr_window", 20)
        sr_levels = params.get("sr_levels", 3)
        volume_ratio = params.get("volume_ratio", 1.5)
        adx_threshold = params.get("adx_threshold", 25)
        price_change_pct = params.get("price_change_pct", 0.01)

        # Calculate ATR for dynamic thresholds
        tr = self._true_range(df)
        atr_period = params.get("atr_period", 14)
        atr = tr.rolling(atr_period).mean()

        # Calculate resistance/support with adaptive quantiles based on sr_levels
        level_factor = min(max(int(sr_levels), 1), 5)
        resistance_q = max(0.5, 1 - 0.05 * level_factor)
        support_q = min(0.5, 0.05 * level_factor)
        resistance = df["high"].rolling(sr_window).quantile(resistance_q).shift(1)
        support = df["low"].rolling(sr_window).quantile(support_q).shift(1)

        # Volume analysis - handle missing volume data
        avg_volume = df["volume"].rolling(20).mean()
        # If volume is all zeros or missing, don't use volume filter
        has_volume_data = avg_volume.iloc[-1] > 0 if len(avg_volume) > 0 else False
        if has_volume_data:
            volume_ratio_series = (df["volume"] / avg_volume.replace(0, np.nan)).fillna(1)
        else:
            volume_ratio_series = pd.Series(1.0, index=df.index)  # Neutral

        # Price change (multi-bar momentum for short timeframes)
        price_change_1 = df["close"].pct_change().fillna(0)
        price_change_3 = df["close"].pct_change(3).fillna(0)  # 3-bar momentum

        # ADX approximation (simplified)
        adx_period = params.get("adx_period", 14)
        adx = self._calculate_adx(df, adx_period, atr=atr)

        # Generate signals
        signals = pd.Series(0, index=df.index)

        # Breakout conditions (more sensitive):
        # 1. Classic breakout: Close > Resistance
        classic_breakout = df["close"] > resistance
        # 2. Near breakout: Close within 0.5 ATR of resistance and pushing higher
        near_breakout = (df["close"] > resistance - 0.5 * atr) & (price_change_1 > 0)
        # 3. High makes new high above resistance
        high_breakout = df["high"] > resistance

        # Any breakout type counts
        breakout = classic_breakout | (near_breakout & high_breakout)

        # Secondary filters (at least one should be true)
        has_volume = volume_ratio_series > volume_ratio
        has_momentum_1 = price_change_1 > price_change_pct
        has_momentum_3 = price_change_3 > price_change_pct * 2  # Stronger 3-bar move
        has_trend = adx > adx_threshold

        # Buy conditions:
        # Option A: Breakout with volume
        # Option B: Breakout with momentum (single or multi-bar)
        # Option C: Near breakout with strong trend and momentum
        buy_condition = (
            (breakout & (has_volume | has_momentum_1 | has_momentum_3)) |
            (near_breakout & has_trend & has_momentum_3)
        )

        # Sell: Price breaks below support OR significant reversal
        sell_condition = (
            (df["close"] < support) |
            (price_change_1 < -price_change_pct * 2) |
            (price_change_3 < -price_change_pct * 3)
        )

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _momentum_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate momentum strategy signals."""
        roc_period = params.get("roc_period", 10)
        mom_period = params.get("mom_period", 10)
        rsi_period = params.get("rsi_period", 14)
        roc_threshold = params.get("roc_threshold", 5.0)
        obv_change_threshold = params.get("obv_change_threshold", 5.0)
        rsi_lower = params.get("rsi_lower", 50)
        rsi_upper = params.get("rsi_upper", 80)
        rsi_exit = params.get("rsi_exit_threshold", 85)

        # Rate of Change (use lower threshold for practical trading)
        close_shifted = df["close"].shift(roc_period)
        roc = (100 * (df["close"] - close_shifted) / close_shifted.replace(0, np.nan)).fillna(0)

        # Momentum
        mom = (df["close"] - df["close"].shift(mom_period)).fillna(0)

        # RSI
        rsi = self._calculate_rsi(df["close"], rsi_period)

        # OBV
        obv = self._calculate_obv(df)
        obv_change = (obv.pct_change(10) * 100).fillna(0)

        signals = pd.Series(0, index=df.index)

        # Buy: Momentum signals (relaxed - use OR instead of all AND)
        # Lower the ROC threshold significantly (was 5%, now dynamic based on param)
        effective_roc_threshold = roc_threshold / 5  # e.g., 5% -> 1%

        has_roc = roc > effective_roc_threshold
        has_momentum = mom > 0
        has_good_rsi = (rsi > rsi_lower) & (rsi < rsi_upper)
        has_obv = obv_change > obv_change_threshold

        # Buy when we have momentum AND RSI is in good range
        buy_condition = has_momentum & has_good_rsi & (has_roc | has_obv)

        # Sell: Momentum reversal (any of these)
        sell_condition = (roc < -effective_roc_threshold) | (rsi > rsi_exit)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _mean_reversion_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate mean reversion strategy signals."""
        bb_period = params.get("bb_period", 20)
        bb_std = params.get("bb_std", 2.0)
        rsi_period = params.get("rsi_period", 14)
        rsi_oversold = params.get("rsi_oversold", 30)
        rsi_overbought = params.get("rsi_overbought", 70)
        bb_pct_entry = params.get("bb_percent_entry", 0.1)
        bb_pct_exit = params.get("bb_percent_exit", 0.9)

        # Bollinger Bands
        middle = df["close"].rolling(bb_period).mean()
        std = df["close"].rolling(bb_period).std().fillna(0)
        upper = middle + bb_std * std
        lower = middle - bb_std * std

        # BB%
        bb_width = upper - lower
        bb_pct = (df["close"] - lower) / bb_width.replace(0, np.nan)
        bb_pct = bb_pct.fillna(0.5)  # Default to middle if no range

        # RSI
        rsi = self._calculate_rsi(df["close"], rsi_period)

        signals = pd.Series(0, index=df.index)

        # Buy: Oversold - relaxed (price near lower band OR RSI oversold)
        near_lower = df["close"] <= lower * 1.01  # Within 1% of lower band
        rsi_low = rsi < rsi_oversold
        bb_low = bb_pct <= bb_pct_entry

        buy_condition = (near_lower | rsi_low) & bb_low

        # Sell: Overbought - relaxed
        near_upper = df["close"] >= upper * 0.99
        rsi_high = rsi > rsi_overbought
        bb_high = bb_pct >= bb_pct_exit

        sell_condition = (near_upper | rsi_high) & bb_high

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _trend_following_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate trend following strategy signals."""
        sma_fast = params.get("sma_fast", 50)
        sma_slow = params.get("sma_slow", 200)
        rsi_period = params.get("rsi_period", 14)
        rsi_upper_limit = params.get("rsi_upper_limit", 70)
        rsi_lower_limit = params.get("rsi_lower_limit", 30)
        macd_fast = params.get("macd_fast", 12)
        macd_slow = params.get("macd_slow", 26)
        macd_signal = params.get("macd_signal", 9)

        # Use smaller SMA periods if data is limited
        data_len = len(df)
        effective_sma_fast = min(sma_fast, max(5, data_len // 10))
        effective_sma_slow = min(sma_slow, max(20, data_len // 4))

        # SMAs with fillna to handle NaN at start
        sma_fast_vals = df["close"].rolling(effective_sma_fast, min_periods=1).mean()
        sma_slow_vals = df["close"].rolling(effective_sma_slow, min_periods=1).mean()

        # RSI
        rsi = self._calculate_rsi(df["close"], rsi_period)

        # MACD
        ema_fast = df["close"].ewm(span=macd_fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=macd_slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=macd_signal, adjust=False).mean()

        signals = pd.Series(0, index=df.index)

        # Trend detection
        uptrend = sma_fast_vals > sma_slow_vals
        price_above_fast = df["close"] > sma_fast_vals
        macd_bullish = macd > macd_signal
        rsi_not_overbought = rsi < rsi_upper_limit

        # Buy: Uptrend confirmed (relaxed - need uptrend AND one of the others)
        buy_condition = uptrend & (price_above_fast | macd_bullish) & rsi_not_overbought

        # Downtrend
        downtrend = sma_fast_vals < sma_slow_vals
        price_below_fast = df["close"] < sma_fast_vals
        macd_bearish = macd < macd_signal
        rsi_not_oversold = rsi > rsi_lower_limit

        # Sell: Downtrend confirmed
        sell_condition = downtrend & (price_below_fast | macd_bearish)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _scalping_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate scalping strategy signals."""
        ema_fast = params.get("ema_fast", 5)
        ema_slow = params.get("ema_slow", 9)
        stoch_k = params.get("stoch_k", 5)
        stoch_d = params.get("stoch_d", 3)
        stoch_upper = params.get("stoch_upper", 80)
        stoch_lower = params.get("stoch_lower", 20)

        # EMAs
        ema_fast_vals = df["close"].ewm(span=ema_fast, adjust=False).mean()
        ema_slow_vals = df["close"].ewm(span=ema_slow, adjust=False).mean()

        # EMA crossover detection
        ema_cross_up = (ema_fast_vals > ema_slow_vals) & (ema_fast_vals.shift(1) <= ema_slow_vals.shift(1))
        ema_cross_down = (ema_fast_vals < ema_slow_vals) & (ema_fast_vals.shift(1) >= ema_slow_vals.shift(1))
        ema_bullish = ema_fast_vals > ema_slow_vals

        # VWAP (simplified - use rolling calculation)
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        volume_sum = df["volume"].rolling(20).sum()
        vwap = (typical_price * df["volume"]).rolling(20).sum() / volume_sum.replace(0, np.nan)
        vwap = vwap.fillna(df["close"])  # Use close price as fallback
        above_vwap = df["close"] > vwap

        # Stochastic
        lowest_low = df["low"].rolling(stoch_k).min()
        highest_high = df["high"].rolling(stoch_k).max()
        stoch_range = highest_high - lowest_low
        stoch_k_val = 100 * (df["close"] - lowest_low) / stoch_range.replace(0, np.nan)
        stoch_k_val = stoch_k_val.fillna(50)  # Default to middle if no range
        stoch_d_val = stoch_k_val.rolling(stoch_d).mean().fillna(50)

        # Stochastic not overbought
        stoch_ok = stoch_k_val < stoch_upper
        stoch_in_range = (stoch_k_val > stoch_lower) & stoch_ok
        stoch_bullish = stoch_k_val > stoch_d_val

        signals = pd.Series(0, index=df.index)

        # Buy: EMA bullish AND (above VWAP OR stochastic OK)
        buy_condition = ema_bullish & stoch_bullish & (above_vwap | stoch_in_range)

        # Sell: EMA crossdown OR stochastic overbought
        sell_condition = ema_cross_down | (stoch_k_val > stoch_upper) | (stoch_k_val < stoch_d_val)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _bollinger_squeeze_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate Bollinger Squeeze breakout signals."""
        bb_period = params.get("bb_period", 20)
        bb_std_mult = params.get("bb_std", 2.0)
        kc_atr_period = params.get("kc_atr_period", 10)
        kc_multiplier = params.get("kc_multiplier", 1.5)
        vol_period = params.get("vol_period", 20)
        vol_factor = params.get("vol_factor", 1.5)

        close = df["close"]
        bb_mid = close.rolling(bb_period).mean()
        bb_std = close.rolling(bb_period).std()
        bb_upper = bb_mid + (bb_std_mult * bb_std)
        bb_lower = bb_mid - (bb_std_mult * bb_std)

        tr = self._true_range(df)
        atr = tr.rolling(kc_atr_period).mean()
        kc_mid = close.ewm(span=kc_atr_period, adjust=False).mean()
        kc_upper = kc_mid + (kc_multiplier * atr)
        kc_lower = kc_mid - (kc_multiplier * atr)

        squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)
        squeeze_released = squeeze_on.shift(1).fillna(False) & ~squeeze_on

        avg_volume = df["volume"].rolling(vol_period).mean()
        has_volume = avg_volume.iloc[-1] > 0 if len(avg_volume) > 0 else False
        if has_volume:
            volume_ok = df["volume"] > (avg_volume.replace(0, np.nan) * vol_factor)
        else:
            volume_ok = pd.Series(True, index=df.index)

        breakout_up = squeeze_released & (close > bb_upper)
        breakout_down = squeeze_released & (close < bb_lower)

        signals = pd.Series(0, index=df.index)
        signals[breakout_up & volume_ok] = 1
        signals[breakout_down & volume_ok] = -1

        return signals

    def _trend_pullback_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate trend pullback signals (long-only)."""
        ema_trend = params.get("ema_trend", 200)
        rsi_period = params.get("rsi_period", 14)
        rsi_pullback = params.get("rsi_pullback", 40)
        rsi_exit = params.get("rsi_exit", 70)

        ema_trend_vals = df["close"].ewm(span=ema_trend, adjust=False).mean()
        rsi = self._calculate_rsi(df["close"], rsi_period)

        in_uptrend = df["close"] > ema_trend_vals
        buy_condition = in_uptrend & (rsi <= rsi_pullback)
        sell_condition = (rsi >= rsi_exit) | (df["close"] < ema_trend_vals)

        signals = pd.Series(0, index=df.index)
        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _opening_range_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate opening range breakout signals."""
        range_minutes = params.get("range_minutes", 15)
        vol_factor = params.get("vol_factor", 1.5)
        atr_period = params.get("atr_period", 14)

        # Estimate bar duration in minutes
        if len(df.index) > 1:
            median_delta = df.index.to_series().diff().median()
            bar_minutes = max(1, int(round(median_delta.total_seconds() / 60)))
        else:
            bar_minutes = 1
        bars_in_range = max(1, int(range_minutes / bar_minutes))

        # Compute opening range per day
        range_high = pd.Series(index=df.index, dtype=float)
        range_low = pd.Series(index=df.index, dtype=float)
        for _, group in df.groupby(df.index.date):
            opening_slice = group.iloc[:bars_in_range]
            if opening_slice.empty:
                continue
            rh = opening_slice["high"].max()
            rl = opening_slice["low"].min()
            range_high.loc[group.index] = rh
            range_low.loc[group.index] = rl

        tr = self._true_range(df)
        atr = tr.rolling(atr_period).mean()
        buffer = atr * 0.1

        avg_volume = df["volume"].rolling(20).mean()
        has_volume = avg_volume.iloc[-1] > 0 if len(avg_volume) > 0 else False
        if has_volume:
            volume_ok = df["volume"] > (avg_volume.replace(0, np.nan) * vol_factor)
        else:
            volume_ok = pd.Series(True, index=df.index)

        breakout_up = df["close"] > (range_high + buffer)
        breakout_down = df["close"] < (range_low - buffer)

        signals = pd.Series(0, index=df.index)
        signals[breakout_up & volume_ok] = 1
        signals[breakout_down] = -1

        return signals

    def _regime_hybrid_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate regime-based hybrid signals (trend vs range)."""
        adx_period = params.get("adx_period", 14)
        trend_threshold = params.get("trend_threshold", 25)
        range_threshold = params.get("range_threshold", 20)
        bb_period = params.get("bb_period", 20)
        bb_std_mult = params.get("bb_std", 2.0)

        adx = self._calculate_adx(df, adx_period)
        close = df["close"]
        bb_mid = close.rolling(bb_period).mean()
        bb_std = close.rolling(bb_period).std()
        bb_upper = bb_mid + (bb_std_mult * bb_std)
        bb_lower = bb_mid - (bb_std_mult * bb_std)

        trend_regime = adx >= trend_threshold
        range_regime = adx <= range_threshold

        trend_buy = trend_regime & (close > bb_mid) & (close > close.shift(1))
        trend_exit = trend_regime & (close < bb_mid)

        range_buy = range_regime & (close < bb_lower)
        range_exit = range_regime & (close > bb_upper)

        signals = pd.Series(0, index=df.index)
        signals[trend_buy | range_buy] = 1
        signals[trend_exit | range_exit] = -1

        return signals

    def _simulate_trades(
        self,
        signals_df: pd.DataFrame,
        config: SimulationConfig,
    ) -> list[TradeRecord]:
        """Simulate trades based on signals."""
        trades: list[TradeRecord] = []
        position: dict | None = None
        capital = config.initial_capital

        for i, (timestamp, row) in enumerate(signals_df.iterrows()):
            signal = row["signal"]
            price = row["close"]

            # Check for exit conditions if in position
            if position is not None:
                should_exit = False
                exit_reason = ""

                # Check stop loss
                if row["low"] <= position["stop_loss"]:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                    exit_price = position["stop_loss"]
                # Check take profit
                elif row["high"] >= position["take_profit"]:
                    should_exit = True
                    exit_reason = "TAKE_PROFIT"
                    exit_price = position["take_profit"]
                # Check exit signal
                elif signal == -1:
                    hold_seconds = (timestamp - position["entry_time"]).total_seconds()
                    if hold_seconds >= config.min_hold_seconds:
                        should_exit = True
                        exit_reason = "SIGNAL"
                        exit_price = price * (1 - config.slippage_pct)

                if should_exit:
                    # Close position
                    pnl = (exit_price - position["entry_price"]) * position["size"]
                    commission = exit_price * position["size"] * config.commission_pct
                    pnl -= commission

                    trade = TradeRecord(
                        entry_time=position["entry_time"],
                        entry_price=position["entry_price"],
                        exit_time=timestamp,
                        exit_price=exit_price,
                        side="long",
                        size=position["size"],
                        pnl=pnl,
                        pnl_pct=pnl / (position["entry_price"] * position["size"]),
                        exit_reason=exit_reason,
                        stop_loss=position["stop_loss"],
                        take_profit=position["take_profit"],
                        commission=commission + position["commission"],
                    )
                    trades.append(trade)
                    capital += pnl
                    position = None

            # Check for entry signal
            if position is None and signal == 1:
                if config.max_spread_pct is not None and config.max_spread_pct > 0:
                    bar_spread_pct = ((row["high"] - row["low"]) / price) * 100 if price else 0
                    if bar_spread_pct > config.max_spread_pct:
                        continue
                entry_price = price * (1 + config.slippage_pct)
                position_value = capital * config.position_size_pct
                size = position_value / entry_price
                commission = position_value * config.commission_pct

                position = {
                    "entry_time": timestamp,
                    "entry_price": entry_price,
                    "size": size,
                    "stop_loss": entry_price * (1 - config.stop_loss_pct),
                    "take_profit": entry_price * (1 + config.take_profit_pct),
                    "commission": commission,
                }
                capital -= commission

        # Close any open position at end
        if position is not None:
            last_row = signals_df.iloc[-1]
            exit_price = last_row["close"]
            pnl = (exit_price - position["entry_price"]) * position["size"]
            commission = exit_price * position["size"] * config.commission_pct
            pnl -= commission

            trade = TradeRecord(
                entry_time=position["entry_time"],
                entry_price=position["entry_price"],
                exit_time=signals_df.index[-1],
                exit_price=exit_price,
                side="long",
                size=position["size"],
                pnl=pnl,
                pnl_pct=pnl / (position["entry_price"] * position["size"]),
                exit_reason="END_OF_DATA",
                stop_loss=position["stop_loss"],
                take_profit=position["take_profit"],
                commission=commission + position["commission"],
            )
            trades.append(trade)

        return trades

    def _get_entry_window_bars(self, index: pd.DatetimeIndex) -> int:
        """Estimate lookahead window size in bars for entry-only scoring."""
        default_bars = 30
        if len(index) < 2:
            return default_bars

        try:
            deltas = np.diff(index.view("int64")) / 1_000_000_000
            deltas = deltas[deltas > 0]
            if deltas.size == 0:
                return default_bars
            median_seconds = float(np.median(deltas))
        except Exception:
            return default_bars

        # If around 1-minute candles, use 30 bars
        if 50.0 <= median_seconds <= 70.0:
            return 30

        window_seconds = 30 * 60  # ~30 minutes
        bars = int(round(window_seconds / max(median_seconds, 1.0)))
        return max(1, bars)

    def _is_uptrend(self, closes: np.ndarray, idx: int, lookback: int) -> bool:
        """Simple trend filter: uptrend if close is higher than lookback bars ago."""
        if idx <= 0:
            return False
        start = max(0, idx - max(1, lookback))
        return float(closes[idx]) > float(closes[start])

    def _get_session_end_index(
        self,
        index: pd.DatetimeIndex,
        start_idx: int,
    ) -> int:
        """Get the last bar index before session end (22:00 Europe/Berlin)."""
        if len(index) == 0:
            return start_idx

        try:
            idx = index
            if idx.tz is None:
                idx = idx.tz_localize("UTC")
            local_idx = idx.tz_convert("Europe/Berlin")
            entry_local = local_idx[start_idx]
            session_end_local = entry_local.normalize() + pd.Timedelta(hours=22)
            if entry_local > session_end_local:
                session_end_local += pd.Timedelta(days=1)
            session_end = session_end_local.tz_convert(idx.tz)
            end_pos = int(idx.searchsorted(session_end, side="right") - 1)
            if end_pos < start_idx:
                end_pos = start_idx
            return min(end_pos, len(idx) - 1)
        except Exception:
            return start_idx

    def _apply_entry_lookahead(
        self,
        index: pd.DatetimeIndex,
        start_idx: int,
        end_idx: int,
        lookahead_mode: str,
        lookahead_bars: int | None,
    ) -> int:
        mode = (lookahead_mode or "session_end").lower()
        if mode == "fixed_bars":
            bars = lookahead_bars or self._get_entry_window_bars(index)
            end_idx = min(end_idx, min(len(index) - 1, start_idx + max(1, bars)))
            return end_idx
        if mode == "session_end":
            if self._is_crypto_symbol():
                return end_idx
            session_end_idx = self._get_session_end_index(index, start_idx)
            return min(end_idx, session_end_idx)
        return end_idx

    def _simulate_entries(
        self,
        signals_df: pd.DataFrame,
        entry_side: str,
        entry_lookahead_mode: str = "session_end",
        entry_lookahead_bars: int | None = None,
    ) -> dict[str, Any]:
        """Simulate entry quality only (no exits).

        Evaluates entry quality within a lookahead window (counter-signal, session end, or fixed bars).
        """
        side = (entry_side or "long").lower()
        entry_signal = 1 if side == "long" else -1
        exit_signal = -entry_signal

        signals = signals_df["signal"].to_numpy()
        closes = signals_df["close"].to_numpy()
        highs = signals_df["high"].to_numpy()
        lows = signals_df["low"].to_numpy()

        scores: list[float] = []
        adverse_moves: list[float] = []
        entry_points: list[tuple[float, datetime, float]] = []
        best_score: float | None = None
        best_entry_price: float | None = None
        best_entry_time: datetime | None = None
        window_bars = self._get_entry_window_bars(signals_df.index)
        trend_lookback = max(1, min(window_bars, 30))
        i = 0
        total = len(signals)
        while i < total:
            if signals[i] == entry_signal:
                entry_price = closes[i]
                if entry_price:
                    j = i + 1
                    while j < total and signals[j] != exit_signal:
                        j += 1
                    end_idx = j if j < total else total - 1
                    end_idx = self._apply_entry_lookahead(
                        signals_df.index,
                        i,
                        end_idx,
                        entry_lookahead_mode,
                        entry_lookahead_bars,
                    )
                    if side == "long":
                        window_low = float(np.min(lows[i:end_idx + 1]))
                        window_high = float(np.max(highs[i:end_idx + 1]))
                        favorable_move = max(0.0, (window_high - entry_price) / entry_price)
                        adverse_move = max(0.0, (entry_price - window_low) / entry_price)
                    else:
                        window_low = float(np.min(lows[i:end_idx + 1]))
                        window_high = float(np.max(highs[i:end_idx + 1]))
                        favorable_move = max(0.0, (entry_price - window_low) / entry_price)
                        adverse_move = max(0.0, (window_high - entry_price) / entry_price)

                    total_move = favorable_move + adverse_move
                    score = 0.0
                    if side == "short" and self._is_uptrend(closes, i, trend_lookback):
                        score = 0.0
                    elif total_move > 0:
                        score = (favorable_move / total_move) * 100.0

                    entry_time = signals_df.index[i].to_pydatetime()
                    entry_points.append((float(entry_price), entry_time, float(score)))
                    scores.append(float(score))
                    adverse_moves.append(float(adverse_move))
                    if best_score is None or score > best_score:
                        best_score = score
                        best_entry_price = float(entry_price)
                        best_entry_time = entry_time
                    i = end_idx + 1
                    continue
            i += 1

        if not scores:
            return {
                "entry_count": 0,
                "entry_score": 0.0,
                "entry_avg_offset_pct": None,
                "entry_best_price": None,
                "entry_best_time": None,
                "entry_points": [],
            }

        avg_offset_pct = float(np.mean(adverse_moves)) * 100.0 if adverse_moves else 0.0
        entry_score = float(np.mean(scores))
        return {
            "entry_count": len(scores),
            "entry_score": float(entry_score),
            "entry_avg_offset_pct": float(avg_offset_pct),
            "entry_best_price": best_entry_price,
            "entry_best_time": best_entry_time,
            "entry_points": entry_points,
        }

    def _calculate_result(
        self,
        strategy_name: str,
        parameters: dict[str, Any],
        trades: list[TradeRecord],
        initial_capital: float,
    ) -> SimulationResult:
        """Calculate simulation result from trades."""
        if not trades:
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

        # Calculate metrics
        total_pnl = sum(t.pnl for t in trades)
        winning_trades = [t for t in trades if t.is_winner]
        losing_trades = [t for t in trades if not t.is_winner]

        total_wins = len(winning_trades)
        total_losses = len(losing_trades)
        win_rate = total_wins / len(trades) if trades else 0.0

        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        avg_win = gross_profit / total_wins if total_wins > 0 else 0.0
        avg_loss = gross_loss / total_losses if total_losses > 0 else 0.0

        largest_win = max((t.pnl for t in winning_trades), default=0.0)
        largest_loss = min((t.pnl for t in losing_trades), default=0.0)

        # Calculate max drawdown
        equity = initial_capital
        peak = equity
        max_dd = 0.0
        for trade in trades:
            equity += trade.pnl
            peak = max(peak, equity)
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)

        final_capital = initial_capital + total_pnl

        # Calculate consecutive wins/losses
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

        # Calculate avg trade duration
        durations = [t.duration_seconds for t in trades]
        avg_duration = np.mean(durations) if durations else 0.0

        # Calculate returns for Sharpe/Sortino
        returns = [t.pnl_pct for t in trades]
        if len(returns) > 1:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            neg_returns = [r for r in returns if r < 0]
            downside_std = np.std(neg_returns) if neg_returns else 0.0

            # Annualized (assuming 252 trading days)
            sharpe = (mean_return * 252) / (std_return * np.sqrt(252)) if std_return > 0 else None
            sortino = (mean_return * 252) / (downside_std * np.sqrt(252)) if downside_std > 0 else None
        else:
            sharpe = None
            sortino = None

        return SimulationResult(
            strategy_name=strategy_name,
            parameters=parameters,
            symbol=self.symbol,
            trades=trades,
            total_pnl=total_pnl,
            total_pnl_pct=(total_pnl / initial_capital) * 100,
            win_rate=win_rate,
            profit_factor=profit_factor if profit_factor != float("inf") else 99.99,
            max_drawdown_pct=max_dd * 100,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            total_trades=len(trades),
            winning_trades=total_wins,
            losing_trades=total_losses,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_trade_duration_seconds=avg_duration,
            max_consecutive_wins=max_cons_wins,
            max_consecutive_losses=max_cons_losses,
            initial_capital=initial_capital,
            final_capital=final_capital,
            data_start=self.data.index[0],
            data_end=self.data.index[-1],
            bars_processed=len(self.data),
        )

    # Helper methods for indicator calculations
    def _calculate_adx(
        self,
        df: pd.DataFrame,
        period: int,
        atr: pd.Series | None = None,
    ) -> pd.Series:
        """Calculate ADX (simplified)."""
        tr = self._true_range(df)
        atr_series = atr if atr is not None else tr.rolling(period).mean()
        dm_plus = (df["high"].diff()).clip(lower=0)
        dm_minus = (-df["low"].diff()).clip(lower=0)
        di_plus = 100 * (dm_plus.rolling(period).mean() / atr_series.replace(0, np.nan))
        di_minus = 100 * (dm_minus.rolling(period).mean() / atr_series.replace(0, np.nan))
        di_sum = di_plus + di_minus
        dx = 100 * abs(di_plus - di_minus) / di_sum.replace(0, np.nan)
        return dx.rolling(period).mean().fillna(0)

    def _true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range."""
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift(1))
        low_close = abs(df["low"] - df["close"].shift(1))
        return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # Default to neutral if no data

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        obv = pd.Series(0.0, index=df.index)
        obv.iloc[0] = df["volume"].iloc[0]
        for i in range(1, len(df)):
            if df["close"].iloc[i] > df["close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] + df["volume"].iloc[i]
            elif df["close"].iloc[i] < df["close"].iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] - df["volume"].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]
        return obv

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
