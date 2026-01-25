"""Pivot/ZigZag detection utilities.

Implements percent- und ATR-basierte Pivot-Erkennung inkl. Cleanup.
Designziel: schnell, deterministisch, konfigurierbar, testbar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal

import numpy as np
import pandas as pd

PivotType = Literal["high", "low"]


@dataclass
class Pivot:
    idx: int
    type: PivotType
    price: float


def _ensure_series(data: Iterable[float]) -> pd.Series:
    if isinstance(data, pd.Series):
        return data
    return pd.Series(list(data))


def detect_pivots_percent(
    prices: Iterable[float] | pd.Series,
    threshold_pct: float = 1.0,
) -> List[Pivot]:
    """Percent-basierte ZigZag-Pivots.

    Args:
        prices: Iterable oder Series der Close-Preise.
        threshold_pct: Mindeständerung in % vom letzten Pivot, um neuen Pivot zu setzen.

    Returns:
        Liste von Pivot-Objekten in chronologischer Reihenfolge.
    """
    series = _ensure_series(prices)
    if series.empty:
        return []
    threshold = threshold_pct / 100.0

    pivots: List[Pivot] = []
    last_pivot_idx = 0
    last_pivot_price = series.iloc[0]
    last_type: PivotType = "low"  # Start annehmen

    pivots.append(Pivot(idx=0, type=last_type, price=last_pivot_price))

    for i in range(1, len(series)):
        price = series.iloc[i]
        change = (price - last_pivot_price) / last_pivot_price

        if last_type == "low" and change >= threshold:
            last_type = "high"
            last_pivot_price = price
            last_pivot_idx = i
            pivots.append(Pivot(idx=i, type="high", price=price))
        elif last_type == "high" and change <= -threshold:
            last_type = "low"
            last_pivot_price = price
            last_pivot_idx = i
            pivots.append(Pivot(idx=i, type="low", price=price))
        else:
            # Update extreme within same swing for better accuracy
            if last_type == "high" and price > last_pivot_price:
                last_pivot_price = price
                pivots[-1] = Pivot(idx=i, type="high", price=price)
            elif last_type == "low" and price < last_pivot_price:
                last_pivot_price = price
                pivots[-1] = Pivot(idx=i, type="low", price=price)

    return pivots


def _true_range(df: pd.DataFrame) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def detect_pivots_atr(
    df: pd.DataFrame,
    atr_mult: float = 1.5,
    atr_period: int = 14,
) -> List[Pivot]:
    """ATR-basierte Pivot-Erkennung auf Basis von OHLC.

    Args:
        df: DataFrame mit Spalten high, low, close.
        atr_mult: Multiplikator für ATR, der überschritten werden muss.
        atr_period: ATR-Periode.
    """
    if df.empty or not {"high", "low", "close"} <= set(df.columns):
        return []
    tr = _true_range(df)
    atr = tr.rolling(atr_period, min_periods=atr_period).mean()
    pivots: List[Pivot] = []
    last_pivot = df.iloc[0].close
    last_type: PivotType = "low"
    pivots.append(Pivot(idx=0, type=last_type, price=last_pivot))

    for i in range(1, len(df)):
        row = df.iloc[i]
        move = row.close - last_pivot
        threshold = atr.iloc[i] * atr_mult if not np.isnan(atr.iloc[i]) else np.nan
        if np.isnan(threshold):
            continue

        if last_type == "low" and move >= threshold:
            last_type = "high"
            last_pivot = row.close
            pivots.append(Pivot(idx=i, type="high", price=row.close))
        elif last_type == "high" and move <= -threshold:
            last_type = "low"
            last_pivot = row.close
            pivots.append(Pivot(idx=i, type="low", price=row.close))
        else:
            # tighten pivot extremes
            if last_type == "high" and row.close > last_pivot:
                last_pivot = row.close
                pivots[-1] = Pivot(idx=i, type="high", price=row.close)
            elif last_type == "low" and row.close < last_pivot:
                last_pivot = row.close
                pivots[-1] = Pivot(idx=i, type="low", price=row.close)

    return pivots


def validate_swing_point(
    prices: Iterable[float] | pd.Series,
    pivot_idx: int,
    lookback_left: int = 3,
    lookback_right: int = 3,
) -> bool:
    """Check if pivot_idx is local extrema in window."""
    series = _ensure_series(prices)
    if pivot_idx <= 0 or pivot_idx >= len(series) - 1:
        return False
    left = series.iloc[max(0, pivot_idx - lookback_left) : pivot_idx]
    right = series.iloc[pivot_idx + 1 : pivot_idx + 1 + lookback_right]
    price = series.iloc[pivot_idx]
    is_high = price > left.max() and price > right.max()
    is_low = price < left.min() and price < right.min()
    return is_high or is_low


def filter_minor_pivots(pivots: List[Pivot], min_distance_bars: int = 3) -> List[Pivot]:
    """Remove pivots that are too close; keep more extreme."""
    if not pivots:
        return []
    filtered: List[Pivot] = [pivots[0]]
    for p in pivots[1:]:
        last = filtered[-1]
        if p.idx - last.idx < min_distance_bars and p.type == last.type:
            # keep the more extreme pivot
            if (p.type == "high" and p.price > last.price) or (p.type == "low" and p.price < last.price):
                filtered[-1] = p
        else:
            filtered.append(p)
    return filtered


__all__ = [
    "Pivot",
    "detect_pivots_percent",
    "detect_pivots_atr",
    "validate_swing_point",
    "filter_minor_pivots",
]
