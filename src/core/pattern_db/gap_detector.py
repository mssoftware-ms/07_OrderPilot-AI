"""Gap Detector for Pattern Database.

Intelligently detects data gaps in the Qdrant pattern database
and determines which time periods need to be filled from Bitunix API.
"""

import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from .qdrant_client import TradingPatternDB

logger = logging.getLogger(__name__)


@dataclass
class DataGap:
    """Represents a data gap that needs to be filled."""

    symbol: str
    timeframe: str
    gap_start: datetime
    gap_end: datetime
    estimated_candles: int
    gap_type: str  # "initial", "small", "medium", "large"

    @property
    def duration_hours(self) -> float:
        """Return gap duration in hours."""
        return (self.gap_end - self.gap_start).total_seconds() / 3600

    @property
    def duration_minutes(self) -> int:
        """Return gap duration in minutes."""
        return int((self.gap_end - self.gap_start).total_seconds() / 60)


class GapDetector:
    """Detects data gaps in pattern database for incremental updates."""

    def __init__(self, db: TradingPatternDB | None = None):
        """Initialize gap detector.

        Args:
            db: Qdrant pattern database instance (creates new if None)
        """
        self.db = db or TradingPatternDB()
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize Qdrant connection.

        Returns:
            True if successful
        """
        if not self._initialized:
            success = await self.db.initialize()
            self._initialized = success
            return success
        return True

    async def detect_gaps(
        self,
        symbol: str,
        timeframe: str,
        max_history_days: int = 365,
    ) -> list[DataGap]:
        """Detect all data gaps for a symbol/timeframe combination.

        Strategy:
        1. Check if any patterns exist
        2. Find gaps between existing patterns
        3. Find gap from latest pattern to now
        4. Classify gaps by size (initial/small/medium/large)

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            timeframe: Timeframe string (e.g., "1m", "5m", "15m")
            max_history_days: Maximum days to look back for initial gap

        Returns:
            List of DataGap objects, sorted by start time
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"🔍 Scanning for gaps: {symbol} {timeframe}")

        # Get all pattern timestamps for this symbol/timeframe
        pattern_timestamps = await self._get_pattern_timestamps(symbol, timeframe)

        if not pattern_timestamps:
            # No patterns exist → Initial gap (full historical load)
            now = datetime.now(timezone.utc)
            start = now - timedelta(days=max_history_days)
            gap = self._create_gap(symbol, timeframe, start, now, gap_type="initial")
            logger.info(f"📊 Initial gap detected: {gap.estimated_candles:,} candles")
            return [gap]

        # Find gaps between existing patterns + gap to now
        gaps = self._find_gaps_in_timeline(
            symbol, timeframe, pattern_timestamps, max_history_days
        )

        logger.info(f"✅ Found {len(gaps)} gaps for {symbol} {timeframe}")
        for gap in gaps:
            logger.info(
                f"   Gap: {gap.gap_start.strftime('%Y-%m-%d %H:%M')} → "
                f"{gap.gap_end.strftime('%Y-%m-%d %H:%M')} "
                f"({gap.estimated_candles:,} candles, {gap.gap_type})"
            )

        return gaps

    async def _get_pattern_timestamps(
        self, symbol: str, timeframe: str
    ) -> list[datetime]:
        """Get all pattern timestamps for symbol/timeframe from Qdrant.

        Uses Qdrant scroll API for efficient retrieval of timestamps only.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string

        Returns:
            Sorted list of pattern start_time datetimes
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            client = self.db._get_client()

            # Build filter for symbol + timeframe
            must_conditions = [
                FieldCondition(key="symbol", match=MatchValue(value=symbol)),
                FieldCondition(key="timeframe", match=MatchValue(value=timeframe)),
            ]

            query_filter = Filter(must=must_conditions)

            # Scroll through all matching patterns (efficient for large collections)
            # We only need the start_time field, not the full vector
            offset = None
            timestamps = []
            batch_size = 1000

            while True:
                result = client.scroll(
                    collection_name=self.db.collection_name,
                    scroll_filter=query_filter,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,  # Don't fetch vectors (faster)
                )

                if not result[0]:
                    break

                # Extract start_time from payload
                for point in result[0]:
                    start_time_str = point.payload.get("start_time")
                    if start_time_str:
                        timestamps.append(datetime.fromisoformat(start_time_str))

                offset = result[1]
                if offset is None:
                    break

            # Sort timestamps
            timestamps.sort()

            logger.debug(
                f"Retrieved {len(timestamps)} pattern timestamps for {symbol} {timeframe}"
            )
            return timestamps

        except Exception as e:
            logger.error(f"Failed to get pattern timestamps: {e}")
            return []

    def _find_gaps_in_timeline(
        self,
        symbol: str,
        timeframe: str,
        timestamps: list[datetime],
        max_history_days: int,
    ) -> list[DataGap]:
        """Find gaps in pattern timeline.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            timestamps: Sorted list of existing pattern timestamps
            max_history_days: Max days to look back before first pattern

        Returns:
            List of gaps found
        """
        gaps = []
        interval_minutes = self._timeframe_to_minutes(timeframe)

        # Define gap threshold: 2x interval = suspicious gap
        # e.g., for 1min timeframe: gap > 2min = data missing
        gap_threshold_minutes = interval_minutes * 2

        # 1. Check gap BEFORE first pattern (historical backfill)
        first_pattern = timestamps[0]
        max_history_start = datetime.now(timezone.utc) - timedelta(days=max_history_days)

        if first_pattern > max_history_start:
            # There's a gap between max_history and first pattern
            gap = self._create_gap(
                symbol,
                timeframe,
                max_history_start,
                first_pattern - timedelta(minutes=interval_minutes),
                gap_type="historical",
            )
            if gap.estimated_candles > 0:
                gaps.append(gap)

        # 2. Find gaps BETWEEN patterns
        for i in range(len(timestamps) - 1):
            current = timestamps[i]
            next_timestamp = timestamps[i + 1]

            gap_minutes = (next_timestamp - current).total_seconds() / 60

            if gap_minutes > gap_threshold_minutes:
                # Gap detected
                gap_start = current + timedelta(minutes=interval_minutes)
                gap_end = next_timestamp - timedelta(minutes=interval_minutes)

                gap = self._create_gap(symbol, timeframe, gap_start, gap_end)
                if gap.estimated_candles > 0:
                    gaps.append(gap)

        # 3. Check gap from LATEST pattern to NOW
        latest_pattern = timestamps[-1]
        now = datetime.now(timezone.utc)
        time_since_latest = (now - latest_pattern).total_seconds() / 60

        if time_since_latest > gap_threshold_minutes:
            # Gap from latest pattern to now
            gap_start = latest_pattern + timedelta(minutes=interval_minutes)
            gap = self._create_gap(symbol, timeframe, gap_start, now, gap_type="recent")
            if gap.estimated_candles > 0:
                gaps.append(gap)

        return gaps

    def _create_gap(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        gap_type: str | None = None,
    ) -> DataGap:
        """Create a DataGap object with metadata.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start: Gap start time
            end: Gap end time
            gap_type: Optional gap type override

        Returns:
            DataGap object
        """
        interval_minutes = self._timeframe_to_minutes(timeframe)
        gap_minutes = int((end - start).total_seconds() / 60)
        estimated_candles = max(0, gap_minutes // interval_minutes)

        # Auto-classify gap type if not provided
        if gap_type is None:
            if estimated_candles <= 10:
                gap_type = "small"  # < 10 candles (e.g., 5-10 minutes on 1m)
            elif estimated_candles <= 500:
                gap_type = "medium"  # 10-500 candles (e.g., 8 hours on 1m)
            else:
                gap_type = "large"  # > 500 candles (e.g., > 8 hours on 1m)

        return DataGap(
            symbol=symbol,
            timeframe=timeframe,
            gap_start=start,
            gap_end=end,
            estimated_candles=estimated_candles,
            gap_type=gap_type,
        )

    @staticmethod
    def _timeframe_to_minutes(timeframe: str) -> int:
        """Convert timeframe string to minutes.

        Args:
            timeframe: Timeframe string (e.g., "1m", "5m", "1h")

        Returns:
            Interval in minutes
        """
        mapping = {
            "1m": 1,
            "5m": 5,
            "10m": 10,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }
        return mapping.get(timeframe, 1)

    async def get_latest_pattern_time(
        self, symbol: str, timeframe: str
    ) -> datetime | None:
        """Get timestamp of latest pattern in database.

        Fast query for checking if updates are needed.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string

        Returns:
            Latest pattern timestamp or None if no patterns exist
        """
        timestamps = await self._get_pattern_timestamps(symbol, timeframe)
        return timestamps[-1] if timestamps else None

    async def needs_update(
        self, symbol: str, timeframe: str, threshold_minutes: int = 10
    ) -> bool:
        """Check if database needs update (quick check).

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            threshold_minutes: Consider update needed if latest pattern older than this

        Returns:
            True if update needed
        """
        latest = await self.get_latest_pattern_time(symbol, timeframe)

        if latest is None:
            # No patterns → definitely needs update
            return True

        # Check if latest pattern is too old
        now = datetime.now(timezone.utc)
        minutes_since_latest = (now - latest).total_seconds() / 60

        return minutes_since_latest > threshold_minutes
