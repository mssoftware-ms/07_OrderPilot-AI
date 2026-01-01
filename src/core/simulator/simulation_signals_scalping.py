from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import calculate_rsi


def scalping_signals(
    df: pd.DataFrame, params: dict[str, Any], calculate_rsi=calculate_rsi
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
