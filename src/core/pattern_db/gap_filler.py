"""Gap Filler for Pattern Database.

Intelligently fills data gaps detected by GapDetector using Bitunix API.
Respects rate limits, handles errors, and provides progress tracking.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from src.core.market_data.providers.bitunix_provider import BitunixProvider
from src.core.market_data.types import Timeframe

from .extractor import PatternExtractor
from .gap_detector import DataGap, GapDetector
from .qdrant_client import TradingPatternDB

logger = logging.getLogger(__name__)


class GapFiller:
    """Fills data gaps in pattern database using Bitunix API.

    Features:
    - Intelligent batching based on gap size
    - Rate-limit-respecting API calls
    - Progress tracking via callbacks
    - Error handling with retry logic
    - Pattern extraction + Qdrant insertion
    """

    def __init__(
        self,
        provider: BitunixProvider | None = None,
        extractor: PatternExtractor | None = None,
        db: TradingPatternDB | None = None,
    ):
        """Initialize gap filler.

        Args:
            provider: Bitunix data provider (creates new if None)
            extractor: Pattern extractor (creates new if None)
            db: Qdrant database (creates new if None)
        """
        self.provider = provider or BitunixProvider()
        self.extractor = extractor or PatternExtractor(
            window_size=20,
            step_size=5,
            outcome_bars=5,
        )
        self.db = db or TradingPatternDB()
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize database connection.

        Returns:
            True if successful
        """
        if not self._initialized:
            success = await self.db.initialize()
            self._initialized = success
            return success
        return True

    async def fill_gap(
        self,
        gap: DataGap,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> int:
        """Fill a single data gap.

        Args:
            gap: DataGap to fill
            progress_callback: Optional callback(current, total, status_msg)

        Returns:
            Number of patterns inserted
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"📥 Filling gap: {gap.symbol} {gap.timeframe}")
        logger.info(
            f"   Period: {gap.gap_start.strftime('%Y-%m-%d %H:%M')} → "
            f"{gap.gap_end.strftime('%Y-%m-%d %H:%M')}"
        )
        logger.info(f"   Estimated candles: {gap.estimated_candles:,}")

        try:
            # 1. Fetch bars from Bitunix
            if progress_callback:
                progress_callback(
                    0,
                    gap.estimated_candles,
                    f"📡 Lade {gap.estimated_candles:,} Kerzen von Bitunix..."
                )

            timeframe_enum = self._string_to_timeframe(gap.timeframe)

            bars = await self.provider.fetch_bars(
                symbol=gap.symbol,
                start_date=gap.gap_start,
                end_date=gap.gap_end,
                timeframe=timeframe_enum,
                progress_callback=lambda batch_num, total_bars, status: (
                    progress_callback(total_bars, gap.estimated_candles, status)
                    if progress_callback
                    else None
                ),
            )

            if not bars:
                logger.warning(f"⚠️ No bars fetched for gap {gap.symbol} {gap.timeframe}")
                return 0

            logger.info(f"✅ Fetched {len(bars)} bars from Bitunix")

            # 2. Extract patterns
            if progress_callback:
                progress_callback(
                    len(bars),
                    gap.estimated_candles,
                    f"🔍 Extrahiere Patterns aus {len(bars)} Bars..."
                )

            patterns = list(
                self.extractor.extract_patterns(bars, gap.symbol, gap.timeframe)
            )

            if not patterns:
                logger.warning(f"⚠️ No patterns extracted from {len(bars)} bars")
                return 0

            logger.info(f"✅ Extracted {len(patterns)} patterns")

            # 3. Insert patterns into Qdrant
            if progress_callback:
                progress_callback(
                    len(bars),
                    gap.estimated_candles,
                    f"💾 Speichere {len(patterns)} Patterns in Qdrant..."
                )

            inserted = await self.db.insert_patterns_batch(
                patterns,
                batch_size=500,
                progress_callback=lambda current, total: (
                    progress_callback(
                        len(bars), gap.estimated_candles, f"💾 Speichere Patterns ({current}/{total})..."
                    )
                    if progress_callback
                    else None
                ),
            )

            logger.info(f"✅ Gap filled: {inserted} patterns inserted for {gap.symbol} {gap.timeframe}")

            return inserted

        except Exception as e:
            logger.error(f"❌ Failed to fill gap for {gap.symbol} {gap.timeframe}: {e}")
            print(f"❌ FEHLER beim Gap-Filling: {e}")
            return 0

    async def fill_all_gaps(
        self,
        symbol: str,
        timeframe: str,
        max_history_days: int = 365,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> int:
        """Detect and fill all gaps for a symbol/timeframe.

        This is the main entry point for gap-filling.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            timeframe: Timeframe string (e.g., "1m", "5m", "15m")
            max_history_days: Maximum days to look back for initial gap
            progress_callback: Optional callback(current, total, status_msg)

        Returns:
            Total number of patterns inserted
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"🔍 Starting gap-fill process for {symbol} {timeframe}")

        # 1. Detect gaps
        if progress_callback:
            progress_callback(0, 0, f"🔍 Scanne nach Datenlücken für {symbol}...")

        detector = GapDetector(db=self.db)
        await detector.initialize()

        gaps = await detector.detect_gaps(symbol, timeframe, max_history_days)

        if not gaps:
            logger.info(f"✅ No gaps found for {symbol} {timeframe}")
            if progress_callback:
                progress_callback(0, 0, "✅ Keine Lücken gefunden - Datenbank aktuell!")
            return 0

        logger.info(f"📊 Found {len(gaps)} gaps to fill")

        # 2. Fill each gap
        total_patterns = 0
        gap_num = 0

        for gap in gaps:
            gap_num += 1

            if progress_callback:
                progress_callback(
                    gap_num,
                    len(gaps),
                    f"📥 Fülle Lücke {gap_num}/{len(gaps)}: "
                    f"{gap.estimated_candles:,} Kerzen ({gap.gap_type})..."
                )

            patterns_inserted = await self.fill_gap(
                gap,
                progress_callback=lambda current, total, status: (
                    progress_callback(gap_num, len(gaps), status)
                    if progress_callback
                    else None
                ),
            )

            total_patterns += patterns_inserted

            # Small delay between gaps (avoid API spam)
            if gap_num < len(gaps):
                await asyncio.sleep(0.5)

        logger.info(f"✅ Gap-fill complete: {total_patterns} patterns inserted across {len(gaps)} gaps")

        if progress_callback:
            progress_callback(
                len(gaps),
                len(gaps),
                f"✅ Fertig! {total_patterns:,} Patterns eingefügt"
            )

        return total_patterns

    async def update_to_now(
        self,
        symbol: str,
        timeframe: str,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> int:
        """Quick update: Fill gap from latest pattern to now.

        This is optimized for small updates (e.g., after 5 minutes offline).

        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            progress_callback: Optional progress callback

        Returns:
            Number of patterns inserted
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"🔄 Quick update for {symbol} {timeframe}")

        # 1. Get latest pattern time
        detector = GapDetector(db=self.db)
        await detector.initialize()

        latest = await detector.get_latest_pattern_time(symbol, timeframe)

        if latest is None:
            # No patterns exist → Full gap fill
            logger.info("No patterns exist, triggering full gap fill")
            return await self.fill_all_gaps(symbol, timeframe, progress_callback=progress_callback)

        # 2. Check if update needed
        now = datetime.now(timezone.utc)
        interval_minutes = detector._timeframe_to_minutes(timeframe)
        time_since_latest = (now - latest).total_seconds() / 60

        threshold_minutes = interval_minutes * 2  # 2x interval

        if time_since_latest < threshold_minutes:
            logger.info(f"✅ Database up-to-date (last pattern: {latest.strftime('%Y-%m-%d %H:%M')})")
            if progress_callback:
                progress_callback(0, 0, "✅ Datenbank bereits aktuell!")
            return 0

        # 3. Create gap from latest to now
        gap_start = latest + timedelta(minutes=interval_minutes)
        gap = detector._create_gap(symbol, timeframe, gap_start, now, gap_type="recent")

        logger.info(f"📥 Filling recent gap: {gap.estimated_candles} candles")

        # 4. Fill gap
        return await self.fill_gap(gap, progress_callback)

    @staticmethod
    def _string_to_timeframe(timeframe_str: str) -> Timeframe:
        """Convert timeframe string to Timeframe enum.

        Args:
            timeframe_str: Timeframe string (e.g., "1m", "5m")

        Returns:
            Timeframe enum
        """
        mapping = {
            "1m": Timeframe.MINUTE_1,
            "5m": Timeframe.MINUTE_5,
            "10m": Timeframe.MINUTE_10,
            "15m": Timeframe.MINUTE_15,
            "30m": Timeframe.MINUTE_30,
            "1h": Timeframe.HOUR_1,
            "4h": Timeframe.HOUR_4,
            "1d": Timeframe.DAY_1,
        }
        return mapping.get(timeframe_str, Timeframe.MINUTE_1)

    async def estimate_fill_time(self, gap: DataGap) -> tuple[int, str]:
        """Estimate time required to fill a gap.

        Args:
            gap: DataGap to estimate

        Returns:
            Tuple of (seconds, human_readable_string)
        """
        # Calculate based on Bitunix rate limits and pattern extraction
        # Rate limit: 10 req/s → 0.15s delay
        # 200 bars per request
        # Pattern extraction + Qdrant insert: ~0.5s per 200 bars

        requests_needed = max(1, gap.estimated_candles // 200)
        api_time = requests_needed * 0.15  # Rate-limit delay
        processing_time = requests_needed * 0.5  # Pattern extraction + insert
        total_seconds = int(api_time + processing_time)

        # Human-readable format
        if total_seconds < 60:
            readable = f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            readable = f"{minutes} Min"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            readable = f"{hours}h {minutes}m"

        return total_seconds, readable
