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
        )

        # Calculate indicators and signals
        signals = self._generate_signals(strategy_name, parameters)

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
            logger.warning(f"Unknown strategy: {strategy_name}, no signals generated")
            signals = pd.Series(0, index=df.index)

        df["signal"] = signals
        return df

    def _breakout_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate breakout strategy signals."""
        sr_window = params.get("sr_window", 20)
        volume_ratio = params.get("volume_ratio", 1.5)
        adx_threshold = params.get("adx_threshold", 25)
        price_change_pct = params.get("price_change_pct", 0.01)

        # Calculate ATR for dynamic thresholds
        tr = self._true_range(df)
        atr_period = params.get("atr_period", 14)
        atr = tr.rolling(atr_period).mean()

        # Calculate resistance/support with ATR buffer for more realistic breakouts
        # Use percentile-based levels instead of absolute max/min for better sensitivity
        resistance = df["high"].rolling(sr_window).quantile(0.95).shift(1)
        support = df["low"].rolling(sr_window).quantile(0.05).shift(1)

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
        dm_plus = (df["high"].diff()).clip(lower=0)
        dm_minus = (-df["low"].diff()).clip(lower=0)
        di_plus = 100 * (dm_plus.rolling(adx_period).mean() / atr.replace(0, np.nan))
        di_minus = 100 * (dm_minus.rolling(adx_period).mean() / atr.replace(0, np.nan))
        di_sum = di_plus + di_minus
        dx = 100 * abs(di_plus - di_minus) / di_sum.replace(0, np.nan)
        adx = dx.rolling(adx_period).mean().fillna(0)

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
        has_obv = obv_change > 0  # Just positive OBV change

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
        bb_low = bb_pct < bb_pct_entry + 0.1  # More lenient

        buy_condition = (near_lower | rsi_low) & (bb_pct < 0.3)

        # Sell: Overbought - relaxed
        near_upper = df["close"] >= upper * 0.99
        rsi_high = rsi > rsi_overbought
        bb_high = bb_pct > bb_pct_exit - 0.1

        sell_condition = (near_upper | rsi_high) & (bb_pct > 0.7)

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
        macd_signal = macd.ewm(span=9, adjust=False).mean()

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

        signals = pd.Series(0, index=df.index)

        # Buy: EMA bullish AND (above VWAP OR stochastic OK)
        buy_condition = ema_bullish & (above_vwap | stoch_ok)

        # Sell: EMA crossdown OR stochastic overbought
        sell_condition = ema_cross_down | (stoch_k_val > stoch_upper)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _bollinger_squeeze_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate Bollinger Squeeze Breakout signals.

        The squeeze occurs when Bollinger Bands contract inside Keltner Channels,
        indicating low volatility. A breakout from the squeeze often leads to
        explosive moves.
        """
        bb_period = params.get("bb_period", 20)
        bb_std = params.get("bb_std", 2.0)
        kc_atr_period = params.get("kc_atr_period", 10)
        kc_multiplier = params.get("kc_multiplier", 1.5)
        vol_period = params.get("vol_period", 20)
        vol_factor = params.get("vol_factor", 1.5)

        # Bollinger Bands
        bb_middle = df["close"].rolling(bb_period).mean()
        bb_std_val = df["close"].rolling(bb_period).std().fillna(0)
        bb_upper = bb_middle + bb_std * bb_std_val
        bb_lower = bb_middle - bb_std * bb_std_val

        # Keltner Channels (using ATR)
        tr = self._true_range(df)
        atr = tr.rolling(kc_atr_period).mean()
        kc_middle = df["close"].rolling(kc_atr_period).mean()
        kc_upper = kc_middle + kc_multiplier * atr
        kc_lower = kc_middle - kc_multiplier * atr

        # Squeeze detection: BB inside KC
        squeeze_on = (bb_lower > kc_lower) & (bb_upper < kc_upper)
        squeeze_off = ~squeeze_on

        # Momentum (using close - midline)
        momentum = df["close"] - bb_middle

        # Volume confirmation
        avg_volume = df["volume"].rolling(vol_period).mean()
        has_volume_data = avg_volume.iloc[-1] > 0 if len(avg_volume) > 0 else False
        if has_volume_data:
            volume_spike = df["volume"] > avg_volume * vol_factor
        else:
            volume_spike = pd.Series(True, index=df.index)

        # Squeeze release detection (was squeezed, now released)
        squeeze_release = squeeze_off & squeeze_on.shift(1).fillna(False)

        signals = pd.Series(0, index=df.index)

        # Buy: Squeeze releases with positive momentum and volume
        buy_condition = squeeze_release & (momentum > 0) & volume_spike

        # Alternative: No squeeze but strong upward momentum with volume
        strong_momentum_up = (momentum > momentum.shift(1)) & (momentum > 0) & volume_spike
        buy_condition = buy_condition | (squeeze_off & strong_momentum_up)

        # Sell: Momentum turns negative or squeeze releases downward
        sell_condition = (squeeze_release & (momentum < 0)) | (momentum < -atr)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _trend_pullback_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate Trend Pullback signals.

        Classic trend following: Buy dips in uptrends when RSI shows oversold
        conditions while price remains above the trend EMA.
        """
        ema_trend = params.get("ema_trend", 200)
        rsi_period = params.get("rsi_period", 14)
        rsi_pullback = params.get("rsi_pullback", 40)
        rsi_exit = params.get("rsi_exit", 70)

        # Adjust EMA period for short data
        data_len = len(df)
        effective_ema = min(ema_trend, max(20, data_len // 4))

        # Trend EMA
        ema_vals = df["close"].ewm(span=effective_ema, adjust=False).mean()

        # RSI
        rsi = self._calculate_rsi(df["close"], rsi_period)

        # Trend detection
        uptrend = df["close"] > ema_vals
        price_above_ema = df["close"] > ema_vals

        # Pullback detection: RSI dips while still in uptrend
        pullback = (rsi < rsi_pullback) & uptrend

        # Additional: Price approaching EMA (within 1%)
        near_ema = (df["close"] - ema_vals).abs() / ema_vals < 0.01

        signals = pd.Series(0, index=df.index)

        # Buy: Pullback in uptrend OR price bouncing off EMA
        buy_condition = pullback | (uptrend & near_ema & (rsi < 50))

        # Sell: RSI overbought OR price breaks below EMA
        sell_condition = (rsi > rsi_exit) | (~uptrend & uptrend.shift(1).fillna(False))

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _opening_range_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate Opening Range Breakout signals.

        Trades breakouts from the high/low range established in the first
        N minutes of the trading session.
        """
        range_minutes = params.get("range_minutes", 15)
        vol_factor = params.get("vol_factor", 1.5)
        atr_period = params.get("atr_period", 14)

        # Calculate ATR for dynamic thresholds
        tr = self._true_range(df)
        atr = tr.rolling(atr_period).mean()

        # Volume analysis
        avg_volume = df["volume"].rolling(20).mean()
        has_volume_data = avg_volume.iloc[-1] > 0 if len(avg_volume) > 0 else False
        if has_volume_data:
            volume_spike = df["volume"] > avg_volume * vol_factor
        else:
            volume_spike = pd.Series(True, index=df.index)

        # For intraday data, detect session opens
        # For daily/longer timeframes, use rolling high/low as "range"
        range_bars = max(1, range_minutes // 5)  # Assume 5-min bars

        # Opening range: rolling high/low over range_bars
        range_high = df["high"].rolling(range_bars).max().shift(1)
        range_low = df["low"].rolling(range_bars).min().shift(1)

        # Breakout detection
        breakout_up = (df["close"] > range_high) & (df["close"].shift(1) <= range_high.shift(1))
        breakout_down = (df["close"] < range_low) & (df["close"].shift(1) >= range_low.shift(1))

        # Price momentum confirmation
        price_momentum = df["close"].pct_change().fillna(0)

        signals = pd.Series(0, index=df.index)

        # Buy: Breakout above range with volume
        buy_condition = breakout_up & volume_spike & (price_momentum > 0)

        # Alternative: Strong move above range high even without perfect breakout timing
        above_range = (df["close"] > range_high) & (price_momentum > 0.001)
        buy_condition = buy_condition | (above_range & volume_spike)

        # Sell: Breakout below range OR price drops below range after breakout
        sell_condition = breakout_down | (df["close"] < range_low)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def _regime_hybrid_signals(
        self, df: pd.DataFrame, params: dict[str, Any]
    ) -> pd.Series:
        """Generate Regime Switching Hybrid signals.

        Detects market regime (Trending, Ranging, High Volatility) and applies
        the appropriate sub-strategy:
        - Trending: Trend following (buy dips in uptrend)
        - Ranging: Mean reversion (buy oversold, sell overbought)
        - High Vol: Reduced position sizing / stay out
        """
        adx_period = params.get("adx_period", 14)
        trend_threshold = params.get("trend_threshold", 25)
        range_threshold = params.get("range_threshold", 20)
        bb_period = params.get("bb_period", 20)
        bb_std = params.get("bb_std", 2.0)

        # Calculate ADX for regime detection
        tr = self._true_range(df)
        atr = tr.rolling(adx_period).mean()
        dm_plus = (df["high"].diff()).clip(lower=0)
        dm_minus = (-df["low"].diff()).clip(lower=0)
        di_plus = 100 * (dm_plus.rolling(adx_period).mean() / atr.replace(0, np.nan))
        di_minus = 100 * (dm_minus.rolling(adx_period).mean() / atr.replace(0, np.nan))
        di_sum = di_plus + di_minus
        dx = 100 * abs(di_plus - di_minus) / di_sum.replace(0, np.nan)
        adx = dx.rolling(adx_period).mean().fillna(0)

        # Regime detection
        trending = adx > trend_threshold
        ranging = adx < range_threshold
        # High volatility: ATR expanding
        atr_expanding = atr > atr.rolling(20).mean() * 1.5

        # Bollinger Bands for mean reversion in ranging markets
        bb_middle = df["close"].rolling(bb_period).mean()
        bb_std_val = df["close"].rolling(bb_period).std().fillna(0)
        bb_upper = bb_middle + bb_std * bb_std_val
        bb_lower = bb_middle - bb_std * bb_std_val
        bb_pct = (df["close"] - bb_lower) / (bb_upper - bb_lower).replace(0, np.nan)
        bb_pct = bb_pct.fillna(0.5)

        # RSI
        rsi = self._calculate_rsi(df["close"], 14)

        # Trend direction
        ema_fast = df["close"].ewm(span=12, adjust=False).mean()
        ema_slow = df["close"].ewm(span=26, adjust=False).mean()
        uptrend = ema_fast > ema_slow

        signals = pd.Series(0, index=df.index)

        # TRENDING REGIME: Buy pullbacks in uptrend
        trend_buy = trending & uptrend & (rsi < 50) & (rsi > 30)
        trend_sell = trending & ~uptrend

        # RANGING REGIME: Mean reversion
        range_buy = ranging & (bb_pct < 0.2) & (rsi < 35)
        range_sell = ranging & (bb_pct > 0.8) & (rsi > 65)

        # HIGH VOLATILITY: Stay cautious, only trade with strong signals
        vol_buy = atr_expanding & uptrend & (rsi < 40)
        vol_sell = atr_expanding & (rsi > 75)

        # Combine signals
        buy_condition = trend_buy | range_buy | vol_buy
        sell_condition = trend_sell | range_sell | vol_sell

        signals[buy_condition] = 1
        signals[sell_condition] = -1

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
