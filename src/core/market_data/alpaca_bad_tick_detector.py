"""Alpaca Bad Tick Detector - Provider-Specific Implementation.

Inherits from BaseBadTickDetector and only implements Alpaca-specific bar conversion.

Refactored: 2026-01-31 (CODER-006, Tasks 1.3.1+1.3.2)
Reduction: 313 LOC → 60 LOC (-80%)
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from .alpaca_historical_data_config import FilterConfig, FilterStats
from .base_bad_tick_detector import BaseBadTickDetector


class BadTickDetector(BaseBadTickDetector[FilterConfig, FilterStats, object]):
    """Alpaca-specific bad tick detector.

    Inherits all detection and cleaning logic from BaseBadTickDetector.
    Only implements Alpaca-specific bar conversion logic.
    """

    def _convert_bars_to_dataframe(self, bars: list) -> pd.DataFrame:
        """Convert Alpaca Bar objects to DataFrame.

        Args:
            bars: List of Alpaca Bar objects

        Returns:
            DataFrame with OHLCV columns
        """
        return pd.DataFrame(
            [
                {
                    "timestamp": b.timestamp,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
                for b in bars
            ]
        )

    def _convert_dataframe_to_bars(
        self, df: pd.DataFrame, original_bars: list, symbol: str
    ) -> list:
        """Convert DataFrame back to Alpaca Bar objects.

        Args:
            df: DataFrame with OHLCV data
            original_bars: Original bars (for metadata)
            symbol: Trading symbol

        Returns:
            List of Alpaca Bar objects
        """
        from alpaca.data.models.bars import Bar

        cleaned_bars = []
        for _, row in df.iterrows():
            ts = row["timestamp"]
            if not isinstance(ts, datetime):
                ts = pd.to_datetime(ts)

            cleaned_bars.append(
                Bar(
                    symbol=original_bars[0].symbol if original_bars else symbol,
                    timestamp=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                    trade_count=getattr(original_bars[0], "trade_count", 0)
                    if original_bars
                    else 0,
                    vwap=getattr(original_bars[0], "vwap", None)
                    if original_bars
                    else None,
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
        """Create Alpaca FilterStats object.

        Args:
            total_bars: Total bars processed
            bad_ticks_found: Bad ticks detected
            bad_ticks_removed: Bad ticks removed
            bad_ticks_interpolated: Bad ticks interpolated
            filtering_percentage: Filter percentage

        Returns:
            Alpaca FilterStats instance
        """
        return FilterStats(
            total_bars=total_bars,
            bad_ticks_found=bad_ticks_found,
            bad_ticks_removed=bad_ticks_removed,
            bad_ticks_interpolated=bad_ticks_interpolated,
            filtering_percentage=filtering_percentage,
        )
