from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import true_range


def bollinger_squeeze_signals(
    df: pd.DataFrame, params: dict[str, Any], true_range=true_range
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
    tr = true_range(df)
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
