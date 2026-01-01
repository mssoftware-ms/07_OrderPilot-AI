from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import true_range


def breakout_signals(
    df: pd.DataFrame, params: dict[str, Any], true_range=true_range
) -> pd.Series:
    """Generate breakout strategy signals."""
    sr_window = params.get("sr_window", 20)
    volume_ratio = params.get("volume_ratio", 1.5)
    adx_threshold = params.get("adx_threshold", 25)
    price_change_pct = params.get("price_change_pct", 0.01)

    # Calculate ATR for dynamic thresholds
    tr = true_range(df)
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
