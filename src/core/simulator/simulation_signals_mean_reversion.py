from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import calculate_rsi


def mean_reversion_signals(
    df: pd.DataFrame, params: dict[str, Any], calculate_rsi=calculate_rsi
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
    rsi = calculate_rsi(df["close"], rsi_period)

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
