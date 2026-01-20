"""Timeframe Converter for Pattern Analysis.

Converts OHLCV bars between different timeframes (e.g., 1m → 5m, 1m → 15m).
Supports upsampling (aggregation) for pattern analysis on different timeframes.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from src.core.market_data.types import HistoricalBar

logger = logging.getLogger(__name__)


class TimeframeConverter:
    """Converts bars between different timeframes."""

    # Timeframe definitions in minutes
    TIMEFRAME_MINUTES = {
        "1m": 1,
        "5m": 5,
        "10m": 10,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
    }

    @classmethod
    def resample_bars(
        cls,
        bars: List[HistoricalBar],
        from_timeframe: str,
        to_timeframe: str,
    ) -> List[HistoricalBar]:
        """Resample bars from one timeframe to another.

        Currently supports upsampling (aggregation) only:
        - 1m → 5m, 15m, 1h, etc.

        Downsampling (interpolation) is NOT supported:
        - 5m → 1m would require guessing intermediate values

        Args:
            bars: Input bars in source timeframe
            from_timeframe: Source timeframe (e.g., "1m")
            to_timeframe: Target timeframe (e.g., "5m")

        Returns:
            Resampled bars in target timeframe

        Raises:
            ValueError: If downsampling is requested or invalid timeframe
        """
        if not bars:
            return []

        # Validate timeframes
        if from_timeframe not in cls.TIMEFRAME_MINUTES:
            raise ValueError(f"Invalid source timeframe: {from_timeframe}")
        if to_timeframe not in cls.TIMEFRAME_MINUTES:
            raise ValueError(f"Invalid target timeframe: {to_timeframe}")

        from_minutes = cls.TIMEFRAME_MINUTES[from_timeframe]
        to_minutes = cls.TIMEFRAME_MINUTES[to_timeframe]

        # Check if same timeframe
        if from_minutes == to_minutes:
            logger.debug(f"No resampling needed: {from_timeframe} == {to_timeframe}")
            return bars

        # Check if downsampling (not supported)
        if from_minutes > to_minutes:
            raise ValueError(
                f"Downsampling not supported: {from_timeframe} → {to_timeframe}. "
                f"Can only aggregate smaller timeframes into larger ones."
            )

        # Upsample (aggregate smaller into larger)
        logger.info(f"Resampling {len(bars)} bars from {from_timeframe} → {to_timeframe}")

        resampled = cls._aggregate_bars(bars, from_minutes, to_minutes)

        logger.info(f"Resampled to {len(resampled)} bars")
        return resampled

    @classmethod
    def _aggregate_bars(
        cls,
        bars: List[HistoricalBar],
        from_minutes: int,
        to_minutes: int,
    ) -> List[HistoricalBar]:
        """Aggregate bars into larger timeframe.

        Algorithm:
        1. Group bars into buckets based on target timeframe
        2. For each bucket, create aggregated bar:
           - Open: First bar's open
           - High: Max of all highs
           - Low: Min of all lows
           - Close: Last bar's close
           - Volume: Sum of all volumes

        Args:
            bars: Input bars
            from_minutes: Source interval in minutes
            to_minutes: Target interval in minutes

        Returns:
            Aggregated bars
        """
        if not bars:
            return []

        # Calculate aggregation ratio
        ratio = to_minutes // from_minutes

        if ratio == 1:
            # No aggregation needed
            return bars

        logger.debug(f"Aggregation ratio: {ratio}:1 (every {ratio} bars → 1 bar)")

        # Group bars into buckets
        resampled_bars = []
        current_bucket = []

        for i, bar in enumerate(bars):
            current_bucket.append(bar)

            # Check if bucket is complete (or last bar)
            if len(current_bucket) == ratio or i == len(bars) - 1:
                # Create aggregated bar
                aggregated = cls._create_aggregated_bar(current_bucket, to_minutes)
                resampled_bars.append(aggregated)

                # Reset bucket
                current_bucket = []

        return resampled_bars

    @classmethod
    def _create_aggregated_bar(
        cls,
        bars: List[HistoricalBar],
        timeframe_minutes: int,
    ) -> HistoricalBar:
        """Create aggregated bar from multiple bars.

        Args:
            bars: Bars to aggregate (must have at least 1 bar)
            timeframe_minutes: Target timeframe in minutes (for timestamp alignment)

        Returns:
            Aggregated HistoricalBar
        """
        if not bars:
            raise ValueError("Cannot aggregate empty bar list")

        # Extract OHLCV values
        opens = [bar.open for bar in bars]
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        closes = [bar.close for bar in bars]
        volumes = [bar.volume for bar in bars]

        # Aggregate
        first_bar = bars[0]
        last_bar = bars[-1]

        aggregated_bar = HistoricalBar(
            timestamp=first_bar.timestamp,  # Use first bar's timestamp
            open=opens[0],  # First bar's open
            high=max(highs),  # Highest high
            low=min(lows),  # Lowest low
            close=closes[-1],  # Last bar's close
            volume=sum(volumes),  # Total volume
        )

        return aggregated_bar

    @classmethod
    def can_convert(
        cls,
        from_timeframe: str,
        to_timeframe: str,
    ) -> tuple[bool, str]:
        """Check if conversion is possible.

        Args:
            from_timeframe: Source timeframe
            to_timeframe: Target timeframe

        Returns:
            Tuple of (is_possible, reason_if_not)
        """
        # Validate timeframes exist
        if from_timeframe not in cls.TIMEFRAME_MINUTES:
            return False, f"Invalid source timeframe: {from_timeframe}"
        if to_timeframe not in cls.TIMEFRAME_MINUTES:
            return False, f"Invalid target timeframe: {to_timeframe}"

        from_minutes = cls.TIMEFRAME_MINUTES[from_timeframe]
        to_minutes = cls.TIMEFRAME_MINUTES[to_timeframe]

        # Check if same
        if from_minutes == to_minutes:
            return True, "No conversion needed"

        # Check if downsampling (not supported)
        if from_minutes > to_minutes:
            return (
                False,
                f"Downsampling not supported ({from_timeframe} → {to_timeframe})",
            )

        # Check if exact multiple (for clean aggregation)
        if to_minutes % from_minutes != 0:
            return (
                False,
                f"Target timeframe must be exact multiple of source "
                f"({to_minutes} is not multiple of {from_minutes})",
            )

        return True, "Conversion possible"

    @classmethod
    def get_supported_conversions(cls, from_timeframe: str) -> List[str]:
        """Get list of supported target timeframes for given source.

        Args:
            from_timeframe: Source timeframe

        Returns:
            List of supported target timeframes
        """
        if from_timeframe not in cls.TIMEFRAME_MINUTES:
            return []

        from_minutes = cls.TIMEFRAME_MINUTES[from_timeframe]
        supported = []

        for tf, minutes in cls.TIMEFRAME_MINUTES.items():
            # Include same timeframe + all larger exact multiples
            if minutes >= from_minutes and minutes % from_minutes == 0:
                supported.append(tf)

        return supported

    @classmethod
    def estimate_bar_count(
        cls,
        source_bar_count: int,
        from_timeframe: str,
        to_timeframe: str,
    ) -> int:
        """Estimate resulting bar count after resampling.

        Args:
            source_bar_count: Number of source bars
            from_timeframe: Source timeframe
            to_timeframe: Target timeframe

        Returns:
            Estimated bar count after resampling
        """
        if from_timeframe not in cls.TIMEFRAME_MINUTES:
            return 0
        if to_timeframe not in cls.TIMEFRAME_MINUTES:
            return 0

        from_minutes = cls.TIMEFRAME_MINUTES[from_timeframe]
        to_minutes = cls.TIMEFRAME_MINUTES[to_timeframe]

        if from_minutes == to_minutes:
            return source_bar_count

        if from_minutes > to_minutes:
            # Downsampling (not supported)
            return 0

        # Upsampling: divide by ratio
        ratio = to_minutes // from_minutes
        return source_bar_count // ratio


# Convenience functions for common conversions


def resample_to_5min(bars_1min: List[HistoricalBar]) -> List[HistoricalBar]:
    """Quick helper: Resample 1min bars to 5min."""
    return TimeframeConverter.resample_bars(bars_1min, "1m", "5m")


def resample_to_15min(bars_1min: List[HistoricalBar]) -> List[HistoricalBar]:
    """Quick helper: Resample 1min bars to 15min."""
    return TimeframeConverter.resample_bars(bars_1min, "1m", "15m")


def resample_to_1hour(bars_1min: List[HistoricalBar]) -> List[HistoricalBar]:
    """Quick helper: Resample 1min bars to 1hour."""
    return TimeframeConverter.resample_bars(bars_1min, "1m", "1h")
