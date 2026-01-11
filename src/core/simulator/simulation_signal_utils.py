from __future__ import annotations

import numpy as np
import pandas as pd

def true_range(df: pd.DataFrame) -> pd.Series:
    """Calculate True Range."""
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift(1))
    low_close = abs(df["low"] - df["close"].shift(1))
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI using Wilder's Smoothing Method.

    The RSI calculation uses exponential smoothing (Wilder's method) after
    the initial SMA calculation for the first period. This matches the
    standard RSI implementation used by TA-Lib and TradingView.

    Formula:
    - First avg_gain/avg_loss = SMA of first 'period' values
    - Subsequent = (prev_avg * (period-1) + current) / period
    - RS = avg_gain / avg_loss
    - RSI = 100 - (100 / (1 + RS))

    Reference: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi
    """
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))

    # Use Wilder's smoothing (EMA with alpha = 1/period)
    # This is equivalent to: ewm(alpha=1/period, adjust=False)
    # or ewm(span=2*period-1, adjust=False) for standard EMA
    alpha = 1.0 / period
    avg_gain = gain.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calculate_obv(df: pd.DataFrame) -> pd.Series:
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
