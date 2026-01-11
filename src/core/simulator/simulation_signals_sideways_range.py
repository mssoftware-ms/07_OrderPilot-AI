"""Signal generation for Sideways Range Market strategy (Issue #45).

Specialized strategy for sideways/ranging markets with max 0.6% range.
Uses: SMA 20/50, RSI 14, Bollinger Bands, Stochastic, Volume, MACD, ADX.
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd


def sideways_range_signals(
    df: pd.DataFrame,
    params: dict[str, Any],
    calculate_rsi: Callable[[pd.Series, int], pd.Series],
) -> pd.Series:
    """Generate sideways range market strategy signals.

    Entry Logic:
    - ADX < threshold confirms sideways market (no strong trend)
    - Price range within max_range_pct over lookback period
    - Long: Price near lower BB + RSI oversold + Stoch oversold
    - Short: Price near upper BB + RSI overbought + Stoch overbought

    Exit Logic:
    - Price returns to BB middle (mean reversion target)
    - RSI/Stoch return to neutral zone
    - MACD cross against position

    Args:
        df: OHLCV DataFrame
        params: Strategy parameters
        calculate_rsi: RSI calculation function

    Returns:
        Signal series: 1=buy, -1=sell, 0=hold
    """
    # Extract parameters with defaults
    sma_short = params.get("sma_short", 20)
    sma_long = params.get("sma_long", 50)
    rsi_period = params.get("rsi_period", 14)
    rsi_oversold = params.get("rsi_oversold", 30)
    rsi_overbought = params.get("rsi_overbought", 70)
    bb_period = params.get("bb_period", 20)
    bb_std = params.get("bb_std", 2.0)
    stoch_k = params.get("stoch_k", 14)
    stoch_d = params.get("stoch_d", 3)
    stoch_oversold = params.get("stoch_oversold", 20)
    stoch_overbought = params.get("stoch_overbought", 80)
    adx_period = params.get("adx_period", 14)
    adx_threshold = params.get("adx_threshold", 20)
    macd_fast = params.get("macd_fast", 12)
    macd_slow = params.get("macd_slow", 26)
    macd_signal = params.get("macd_signal", 9)
    max_range_pct = params.get("max_range_pct", 0.6)

    # Calculate indicators
    close = df["close"]
    high = df["high"]
    low = df["low"]

    # SMA
    sma_20 = close.rolling(sma_short).mean()
    sma_50 = close.rolling(sma_long).mean()

    # RSI
    rsi = calculate_rsi(close, rsi_period)

    # Bollinger Bands
    bb_middle = close.rolling(bb_period).mean()
    bb_std_val = close.rolling(bb_period).std().fillna(0)
    bb_upper = bb_middle + bb_std * bb_std_val
    bb_lower = bb_middle - bb_std * bb_std_val
    bb_width = bb_upper - bb_lower
    bb_pct = (close - bb_lower) / bb_width.replace(0, np.nan)
    bb_pct = bb_pct.fillna(0.5)

    # Stochastic Oscillator
    lowest_low = low.rolling(stoch_k).min()
    highest_high = high.rolling(stoch_k).max()
    stoch_range = highest_high - lowest_low
    stoch_k_val = ((close - lowest_low) / stoch_range.replace(0, np.nan)) * 100
    stoch_k_val = stoch_k_val.fillna(50)
    stoch_d_val = stoch_k_val.rolling(stoch_d).mean()

    # ADX for sideways confirmation
    adx = _calculate_adx(df, adx_period)

    # MACD
    ema_fast = close.ewm(span=macd_fast, adjust=False).mean()
    ema_slow = close.ewm(span=macd_slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    macd_signal_line = macd_line.ewm(span=macd_signal, adjust=False).mean()
    macd_hist = macd_line - macd_signal_line

    # Price Range Check (for sideways market confirmation)
    lookback = bb_period
    rolling_high = high.rolling(lookback).max()
    rolling_low = low.rolling(lookback).min()
    price_range_pct = ((rolling_high - rolling_low) / rolling_low * 100).fillna(0)

    # Volume relative to average
    volume_sma = df["volume"].rolling(20).mean()
    volume_ratio = (df["volume"] / volume_sma.replace(0, 1)).fillna(1)

    # Initialize signals
    signals = pd.Series(0, index=df.index)

    # Sideways market confirmation
    is_sideways = (adx < adx_threshold) & (price_range_pct < max_range_pct)

    # Long Entry Conditions (buy at lower band in sideways market)
    near_lower_bb = bb_pct < 0.15  # Near lower Bollinger Band
    rsi_low = rsi < rsi_oversold
    stoch_low = stoch_k_val < stoch_oversold
    macd_turning_up = macd_hist > macd_hist.shift(1)

    long_condition = (
        is_sideways
        & (near_lower_bb | rsi_low)
        & (stoch_low | rsi_low)
        & (volume_ratio > 0.5)  # Some volume confirmation
    )

    # Short Entry Conditions (sell at upper band in sideways market)
    near_upper_bb = bb_pct > 0.85  # Near upper Bollinger Band
    rsi_high = rsi > rsi_overbought
    stoch_high = stoch_k_val > stoch_overbought
    macd_turning_down = macd_hist < macd_hist.shift(1)

    short_condition = (
        is_sideways
        & (near_upper_bb | rsi_high)
        & (stoch_high | rsi_high)
        & (volume_ratio > 0.5)
    )

    # Exit conditions for longs
    long_exit = (
        (bb_pct > 0.5)  # Price returned to middle
        | (rsi > 50)  # RSI neutral
        | (stoch_k_val > 50)  # Stoch neutral
        | (macd_hist < 0)  # MACD bearish
    )

    # Exit conditions for shorts
    short_exit = (
        (bb_pct < 0.5)  # Price returned to middle
        | (rsi < 50)  # RSI neutral
        | (stoch_k_val < 50)  # Stoch neutral
        | (macd_hist > 0)  # MACD bullish
    )

    # Apply signals
    signals[long_condition] = 1
    signals[short_condition] = -1

    return signals


def _calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index (ADX)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)

    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

    # Smoothed values
    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan))

    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(span=period, adjust=False).mean()

    return adx.fillna(0)
