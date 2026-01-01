from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import calculate_rsi


def trend_following_signals(
    df: pd.DataFrame, params: dict[str, Any], calculate_rsi=calculate_rsi
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
    rsi = calculate_rsi(df["close"], rsi_period)

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
