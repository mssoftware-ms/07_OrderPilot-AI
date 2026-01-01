from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import calculate_rsi


def trend_pullback_signals(
    df: pd.DataFrame, params: dict[str, Any], calculate_rsi=calculate_rsi
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
    rsi = calculate_rsi(df["close"], rsi_period)

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
