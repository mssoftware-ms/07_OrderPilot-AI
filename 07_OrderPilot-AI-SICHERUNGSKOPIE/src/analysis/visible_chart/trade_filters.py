"""Trade Filters for No-Trade Zones.

Filters out entries during unfavorable market conditions:
- Volatility spikes (abnormal ATR)
- Spread spikes (wide bid-ask)
- Data gaps (missing candles)
- Low liquidity periods
- News events (if calendar provided)

Phase 4.4: No-Trade Zones
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .types import EntryEvent

logger = logging.getLogger(__name__)


class FilterReason(str, Enum):
    """Reasons for filtering an entry."""

    VOLATILITY_SPIKE = "volatility_spike"
    SPREAD_SPIKE = "spread_spike"
    DATA_GAP = "data_gap"
    LOW_VOLUME = "low_volume"
    NEWS_EVENT = "news_event"
    TIME_RESTRICTION = "time_restriction"
    CUSTOM = "custom"


@dataclass
class FilterResult:
    """Result of applying a filter to an entry.

    Attributes:
        entry: The original entry.
        is_filtered: Whether entry was filtered out.
        reason: Reason for filtering (if filtered).
        details: Additional filter details.
    """

    entry: EntryEvent
    is_filtered: bool
    reason: FilterReason | None = None
    details: str = ""


@dataclass
class FilterConfig:
    """Configuration for trade filters.

    Attributes:
        vol_spike_threshold: ATR multiplier for volatility spike (e.g., 2.5 = 2.5x normal ATR).
        vol_lookback: Bars to calculate normal volatility.
        spread_spike_threshold: Spread multiplier for spike detection.
        avg_spread_lookback: Bars to calculate average spread.
        gap_threshold_pct: Minimum gap as % of price to be considered a gap.
        min_volume_ratio: Minimum volume as ratio of average.
        volume_lookback: Bars to calculate average volume.
        excluded_hours_utc: Hours (0-23) to exclude from trading.
        excluded_weekdays: Weekdays to exclude (0=Monday, 6=Sunday).
        custom_filters: List of custom filter functions.
    """

    # Volatility filters
    vol_spike_threshold: float = 2.5
    vol_lookback: int = 20

    # Spread filters
    spread_spike_threshold: float = 3.0
    avg_spread_lookback: int = 20

    # Gap filters
    gap_threshold_pct: float = 0.5

    # Volume filters
    min_volume_ratio: float = 0.3
    volume_lookback: int = 20

    # Time filters
    excluded_hours_utc: list[int] = field(default_factory=list)
    excluded_weekdays: list[int] = field(default_factory=list)

    # Custom filters
    custom_filters: list[Callable[[EntryEvent, list[dict], int], tuple[bool, str]]] = (
        field(default_factory=list)
    )


@dataclass
class FilterStats:
    """Statistics from filter application.

    Attributes:
        total_entries: Total entries processed.
        filtered_count: Number of entries filtered out.
        by_reason: Count by filter reason.
        pass_rate: Percentage of entries that passed.
    """

    total_entries: int = 0
    filtered_count: int = 0
    by_reason: dict[str, int] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.total_entries == 0:
            return 0.0
        return (self.total_entries - self.filtered_count) / self.total_entries


class TradeFilter:
    """Filters entries based on market conditions.

    Applies multiple filters to remove entries during
    unfavorable conditions (no-trade zones).
    """

    def __init__(self, config: FilterConfig | None = None) -> None:
        """Initialize the filter.

        Args:
            config: Filter configuration.
        """
        self.config = config or FilterConfig()
        self._stats = FilterStats()

    def filter_entries(
        self,
        entries: list[EntryEvent],
        candles: list[dict],
        spreads: list[float] | None = None,
    ) -> tuple[list[EntryEvent], FilterStats]:
        """Filter entries based on market conditions.

        Args:
            entries: List of entry events to filter.
            candles: OHLCV candle data.
            spreads: Optional spread data (bid-ask).

        Returns:
            Tuple of (filtered entries, filter stats).
        """
        self._stats = FilterStats()

        if not entries or not candles:
            return entries, self._stats

        # Build timestamp -> index mapping
        ts_to_idx = {c["timestamp"]: i for i, c in enumerate(candles)}

        # Pre-calculate metrics
        atr_values = self._calculate_atr(candles, self.config.vol_lookback)
        avg_atr = self._calculate_rolling_avg(atr_values, self.config.vol_lookback)
        volumes = [c.get("volume", 0) for c in candles]
        avg_volumes = self._calculate_rolling_avg(volumes, self.config.volume_lookback)

        # Filter spreads if provided
        avg_spreads = None
        if spreads:
            avg_spreads = self._calculate_rolling_avg(spreads, self.config.avg_spread_lookback)

        passed_entries: list[EntryEvent] = []
        self._stats.total_entries = len(entries)

        for entry in entries:
            idx = ts_to_idx.get(entry.timestamp)
            if idx is None:
                # Entry timestamp not in candles - pass through
                passed_entries.append(entry)
                continue

            # Apply filters
            result = self._apply_filters(
                entry=entry,
                candles=candles,
                idx=idx,
                atr_values=atr_values,
                avg_atr=avg_atr,
                volumes=volumes,
                avg_volumes=avg_volumes,
                spreads=spreads,
                avg_spreads=avg_spreads,
            )

            if result.is_filtered:
                self._stats.filtered_count += 1
                reason_key = result.reason.value if result.reason else "unknown"
                self._stats.by_reason[reason_key] = (
                    self._stats.by_reason.get(reason_key, 0) + 1
                )
                logger.debug(
                    "Filtered entry at %d: %s (%s)",
                    entry.timestamp,
                    result.reason,
                    result.details,
                )
            else:
                passed_entries.append(entry)

        logger.info(
            "Filter complete: %d/%d passed (%.1f%%)",
            len(passed_entries),
            len(entries),
            self._stats.pass_rate * 100,
        )

        return passed_entries, self._stats

    def _apply_filters(
        self,
        entry: EntryEvent,
        candles: list[dict],
        idx: int,
        atr_values: list[float],
        avg_atr: list[float],
        volumes: list[float],
        avg_volumes: list[float],
        spreads: list[float] | None,
        avg_spreads: list[float] | None,
    ) -> FilterResult:
        """Apply all filters to a single entry.

        Args:
            entry: Entry to filter.
            candles: All candles.
            idx: Index of entry candle.
            atr_values: Current ATR values.
            avg_atr: Rolling average ATR.
            volumes: Volume data.
            avg_volumes: Rolling average volume.
            spreads: Spread data.
            avg_spreads: Rolling average spread.

        Returns:
            FilterResult indicating if entry was filtered.
        """
        # 1. Volatility spike filter
        if idx < len(atr_values) and idx < len(avg_atr) and avg_atr[idx] > 0:
            vol_ratio = atr_values[idx] / avg_atr[idx]
            if vol_ratio > self.config.vol_spike_threshold:
                return FilterResult(
                    entry=entry,
                    is_filtered=True,
                    reason=FilterReason.VOLATILITY_SPIKE,
                    details=f"ATR ratio: {vol_ratio:.2f}x",
                )

        # 2. Spread spike filter
        if spreads and avg_spreads and idx < len(spreads) and idx < len(avg_spreads):
            if avg_spreads[idx] > 0:
                spread_ratio = spreads[idx] / avg_spreads[idx]
                if spread_ratio > self.config.spread_spike_threshold:
                    return FilterResult(
                        entry=entry,
                        is_filtered=True,
                        reason=FilterReason.SPREAD_SPIKE,
                        details=f"Spread ratio: {spread_ratio:.2f}x",
                    )

        # 3. Data gap filter
        if idx > 0:
            candle = candles[idx]
            prev_candle = candles[idx - 1]

            # Check for price gap
            gap = abs(candle["open"] - prev_candle["close"])
            gap_pct = gap / prev_candle["close"] * 100 if prev_candle["close"] > 0 else 0

            if gap_pct > self.config.gap_threshold_pct:
                return FilterResult(
                    entry=entry,
                    is_filtered=True,
                    reason=FilterReason.DATA_GAP,
                    details=f"Gap: {gap_pct:.2f}%",
                )

            # Check for time gap (missing candles)
            expected_interval = self._estimate_candle_interval(candles)
            if expected_interval > 0:
                time_gap = candle["timestamp"] - prev_candle["timestamp"]
                if time_gap > expected_interval * 2:
                    return FilterResult(
                        entry=entry,
                        is_filtered=True,
                        reason=FilterReason.DATA_GAP,
                        details=f"Time gap: {time_gap}s (expected {expected_interval}s)",
                    )

        # 4. Volume filter
        if idx < len(volumes) and idx < len(avg_volumes) and avg_volumes[idx] > 0:
            vol_ratio = volumes[idx] / avg_volumes[idx]
            if vol_ratio < self.config.min_volume_ratio:
                return FilterResult(
                    entry=entry,
                    is_filtered=True,
                    reason=FilterReason.LOW_VOLUME,
                    details=f"Volume ratio: {vol_ratio:.2f}x",
                )

        # 5. Time restriction filter
        if self.config.excluded_hours_utc or self.config.excluded_weekdays:
            from datetime import datetime, timezone

            dt = datetime.fromtimestamp(entry.timestamp, tz=timezone.utc)

            if dt.hour in self.config.excluded_hours_utc:
                return FilterResult(
                    entry=entry,
                    is_filtered=True,
                    reason=FilterReason.TIME_RESTRICTION,
                    details=f"Excluded hour: {dt.hour}",
                )

            if dt.weekday() in self.config.excluded_weekdays:
                return FilterResult(
                    entry=entry,
                    is_filtered=True,
                    reason=FilterReason.TIME_RESTRICTION,
                    details=f"Excluded weekday: {dt.weekday()}",
                )

        # 6. Custom filters
        for custom_filter in self.config.custom_filters:
            try:
                is_filtered, details = custom_filter(entry, candles, idx)
                if is_filtered:
                    return FilterResult(
                        entry=entry,
                        is_filtered=True,
                        reason=FilterReason.CUSTOM,
                        details=details,
                    )
            except Exception as e:
                logger.warning("Custom filter error: %s", e)

        # Passed all filters
        return FilterResult(entry=entry, is_filtered=False)

    def _calculate_atr(self, candles: list[dict], period: int = 14) -> list[float]:
        """Calculate ATR values."""
        if len(candles) < 2:
            return [0.0] * len(candles)

        tr_values = []
        for i, c in enumerate(candles):
            high = c["high"]
            low = c["low"]
            prev_close = candles[i - 1]["close"] if i > 0 else c["close"]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            tr_values.append(tr)

        # EMA-based ATR
        atr = []
        multiplier = 2 / (period + 1)

        for i, tr in enumerate(tr_values):
            if i == 0:
                atr.append(tr)
            else:
                atr.append(tr * multiplier + atr[-1] * (1 - multiplier))

        return atr

    def _calculate_rolling_avg(
        self, values: list[float], period: int
    ) -> list[float]:
        """Calculate rolling average."""
        result = []
        for i in range(len(values)):
            if i < period - 1:
                # Not enough data - use available
                avg = sum(values[: i + 1]) / (i + 1) if i >= 0 else values[i]
            else:
                avg = sum(values[i - period + 1 : i + 1]) / period
            result.append(avg)
        return result

    def _estimate_candle_interval(self, candles: list[dict]) -> int:
        """Estimate expected interval between candles in seconds."""
        if len(candles) < 3:
            return 60  # Default 1m

        # Calculate median interval
        intervals = []
        for i in range(1, min(20, len(candles))):
            intervals.append(candles[i]["timestamp"] - candles[i - 1]["timestamp"])

        intervals.sort()
        return intervals[len(intervals) // 2]

    def get_stats(self) -> FilterStats:
        """Get filter statistics."""
        return self._stats

    def reset_stats(self) -> None:
        """Reset filter statistics."""
        self._stats = FilterStats()


def create_default_filter() -> TradeFilter:
    """Create a trade filter with sensible defaults."""
    config = FilterConfig(
        vol_spike_threshold=2.5,
        spread_spike_threshold=3.0,
        gap_threshold_pct=0.5,
        min_volume_ratio=0.3,
        # Exclude overnight for stocks (simplified)
        excluded_hours_utc=[],  # User should configure based on market
        excluded_weekdays=[5, 6],  # Saturday, Sunday
    )
    return TradeFilter(config)


def create_crypto_filter() -> TradeFilter:
    """Create a trade filter tuned for crypto markets.

    Crypto trades 24/7 but has specific characteristics:
    - Higher volatility spikes
    - Less predictable volume patterns
    """
    config = FilterConfig(
        vol_spike_threshold=3.0,  # Higher threshold for crypto
        spread_spike_threshold=4.0,
        gap_threshold_pct=1.0,  # Crypto can have larger gaps
        min_volume_ratio=0.2,  # More lenient on volume
        excluded_hours_utc=[],  # 24/7 trading
        excluded_weekdays=[],  # 24/7 trading
    )
    return TradeFilter(config)
