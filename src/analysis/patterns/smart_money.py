"""Simple Smart Money Concepts detectors: Order Block and Fair Value Gap."""

from __future__ import annotations

from typing import List, Dict

import pandas as pd

from .named_patterns import Pattern


def detect_order_blocks(df: pd.DataFrame, lookback: int = 5) -> List[Pattern]:
    """Detect bullish order blocks: last down candle before close breaks prior high."""
    patterns: List[Pattern] = []
    if df.empty or len(df) < lookback + 2:
        return patterns

    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values

    for i in range(lookback, len(df) - 1):
        # bullish OB: candle i is down and candle i+1 closes above highest high of previous lookback
        if closes[i] < df["open"].iloc[i]:
            prev_high = highs[i - lookback : i].max()
            if closes[i + 1] > prev_high:
                patterns.append(
                    Pattern(
                        name="Bullish Order Block",
                        pivots=[],
                        score=70.0,
                        metadata={"index": i, "break_high": prev_high},
                    )
                )
        # bearish OB: candle i is up and next close below lowest low of lookback
        if closes[i] > df["open"].iloc[i]:
            prev_low = lows[i - lookback : i].min()
            if closes[i + 1] < prev_low:
                patterns.append(
                    Pattern(
                        name="Bearish Order Block",
                        pivots=[],
                        score=70.0,
                        metadata={"index": i, "break_low": prev_low},
                    )
                )
    return patterns


def detect_fvg(df: pd.DataFrame) -> List[Pattern]:
    """Detect fair value gaps (simple 3-candle gap)."""
    patterns: List[Pattern] = []
    if len(df) < 3:
        return patterns
    for i in range(1, len(df) - 1):
        prev_high = df["high"].iloc[i - 1]
        prev_low = df["low"].iloc[i - 1]
        curr_low = df["low"].iloc[i]
        curr_high = df["high"].iloc[i]
        next_low = df["low"].iloc[i + 1]
        next_high = df["high"].iloc[i + 1]

        # Bullish FVG: prev_high < next_low (gap up)
        if prev_high < next_low:
            patterns.append(
                Pattern(
                    name="Bullish FVG",
                    pivots=[],
                    score=60.0,
                    metadata={"from": i - 1, "to": i + 1, "gap": next_low - prev_high},
                )
            )
        # Bearish FVG: prev_low > next_high (gap down)
        if prev_low > next_high:
            patterns.append(
                Pattern(
                    name="Bearish FVG",
                    pivots=[],
                    score=60.0,
                    metadata={"from": i - 1, "to": i + 1, "gap": prev_low - next_high},
                )
            )
    return patterns


__all__ = ["detect_order_blocks", "detect_fvg"]
