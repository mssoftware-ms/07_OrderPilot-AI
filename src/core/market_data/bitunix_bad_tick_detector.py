"""Bitunix Bad Tick Detector - Provider-Specific Implementation.

Inherits from BaseBadTickDetector and only implements Bitunix-specific bar conversion.

Refactored: 2026-01-31 (CODER-006, Tasks 1.3.1+1.3.2)
Reduction: 314 LOC → 70 LOC (-78%)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd

from .base_bad_tick_detector import BaseBadTickDetector
from .bitunix_historical_data_config import FilterConfig, FilterStats
from .types import HistoricalBar


class BadTickDetector(BaseBadTickDetector[FilterConfig, FilterStats, HistoricalBar]):
    """Bitunix-specific bad tick detector.

    Inherits all detection and cleaning logic from BaseBadTickDetector.
    Only implements Bitunix-specific bar conversion logic with Decimal handling.
    """

    def _convert_bars_to_dataframe(self, bars: list[HistoricalBar]) -> pd.DataFrame:
        """Convert Bitunix HistoricalBar objects to DataFrame.

        Args:
            bars: List of HistoricalBar objects

        Returns:
            DataFrame with OHLCV columns

        Note:
            Explicit float conversion needed for Decimal compatibility.
        """
        return pd.DataFrame(
            [
                {
                    "timestamp": b.timestamp,
                    "open": float(b.open),
                    "high": float(b.high),
                    "low": float(b.low),
                    "close": float(b.close),
                    "volume": float(b.volume),
                }
                for b in bars
            ]
        )

    def _convert_dataframe_to_bars(
        self, df: pd.DataFrame, original_bars: list[HistoricalBar], symbol: str
    ) -> list[HistoricalBar]:
        """Convert DataFrame back to Bitunix HistoricalBar objects.

        Args:
            df: DataFrame with OHLCV data
            original_bars: Original bars (for metadata)
            symbol: Trading symbol

        Returns:
            List of HistoricalBar objects

        Note:
            Converts back to Decimal for precision.
        """
        cleaned_bars = []
        for _, row in df.iterrows():
            ts = row["timestamp"]
            if not isinstance(ts, datetime):
                ts = pd.to_datetime(ts)

            cleaned_bars.append(
                HistoricalBar(
                    timestamp=ts,
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=int(row["volume"]),
                    vwap=Decimal(str(original_bars[0].vwap))
                    if original_bars and original_bars[0].vwap
                    else None,
                    trades=original_bars[0].trades
                    if original_bars and original_bars[0].trades
                    else None,
                    source="bitunix",
                )
            )

        return cleaned_bars

    def _create_filter_stats(
        self,
        total_bars: int = 0,
        bad_ticks_found: int = 0,
        bad_ticks_removed: int = 0,
        bad_ticks_interpolated: int = 0,
        filtering_percentage: float = 0.0,
    ) -> FilterStats:
        """Create Bitunix FilterStats object.

        Args:
            total_bars: Total bars processed
            bad_ticks_found: Bad ticks detected
            bad_ticks_removed: Bad ticks removed
            bad_ticks_interpolated: Bad ticks interpolated
            filtering_percentage: Filter percentage

        Returns:
            Bitunix FilterStats instance
        """
        return FilterStats(
            total_bars=total_bars,
            bad_ticks_found=bad_ticks_found,
            bad_ticks_removed=bad_ticks_removed,
            bad_ticks_interpolated=bad_ticks_interpolated,
            filtering_percentage=filtering_percentage,
        )
