from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .simulation_signal_utils import true_range


def opening_range_signals(
    df: pd.DataFrame, params: dict[str, Any], true_range=true_range
) -> pd.Series:
    """Generate Opening Range Breakout signals.

    Trades breakouts from the high/low range established in the first
    N minutes of the trading session.
    """
    range_minutes = params.get("range_minutes", 15)
    vol_factor = params.get("vol_factor", 1.5)
    atr_period = params.get("atr_period", 14)

    # Calculate ATR for dynamic thresholds
    tr = true_range(df)
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
