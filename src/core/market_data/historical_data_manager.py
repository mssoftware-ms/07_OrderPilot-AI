"""Historical Data Manager for bulk downloading and caching market data.

Manages downloading and storing historical market data from various providers
with support for multi-source storage using provider-prefixed symbols.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.core.market_data.types import (
    DataSource,
    HistoricalBar,
    Timeframe,
    format_symbol_with_source,
)
from src.database import get_db_manager
from src.database.models import MarketBar

logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """Manages bulk downloading and caching of historical market data."""

    def __init__(self):
        """Initialize the historical data manager."""
        self.db_manager = get_db_manager()

    async def bulk_download(
        self,
        provider,
        symbols: list[str],
        days_back: int = 365,
        timeframe: Timeframe = Timeframe.MINUTE_1,
        source: DataSource = DataSource.ALPACA_CRYPTO,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """Download historical data for multiple symbols in bulk.

        Args:
            provider: Data provider instance (e.g., AlpacaProvider, BitunixProvider)
            symbols: List of symbols to download
            days_back: Number of days of history to download (default: 365)
            timeframe: Timeframe for bars (default: 1min)
            source: Data source enum for symbol prefixing
            batch_size: Number of bars to save per batch (default: 100)

        Returns:
            Dictionary mapping symbols to number of bars saved

        Example:
            >>> from src.core.market_data.providers.bitunix_provider import BitunixProvider
            >>> provider = BitunixProvider(api_key, api_secret)
            >>> manager = HistoricalDataManager()
            >>> results = await manager.bulk_download(
            ...     provider,
            ...     ["BTCUSDT", "ETHUSDT"],
            ...     days_back=365,
            ...     source=DataSource.BITUNIX
            ... )
            >>> print(results)  # {"BTCUSDT": 525600, "ETHUSDT": 525600}
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"📥 Bulk download started:")
        logger.info(f"   Symbols: {symbols}")
        logger.info(f"   Period: {start_date.date()} to {end_date.date()} ({days_back} days)")
        logger.info(f"   Timeframe: {timeframe.value}")
        logger.info(f"   Source: {source.value}")

        results = {}

        for symbol in symbols:
            try:
                logger.info(f"📡 Downloading {symbol} from {source.value}...")

                # Fetch bars from provider
                bars = await provider.fetch_bars(symbol, start_date, end_date, timeframe)

                if not bars:
                    logger.warning(f"⚠️ No data received for {symbol}")
                    results[symbol] = 0
                    continue

                # Format symbol with source prefix for database
                db_symbol = format_symbol_with_source(symbol, source)

                # Save to database in batches
                saved_count = await self._save_bars_batched(
                    bars,
                    db_symbol,
                    source.value,
                    batch_size
                )

                results[symbol] = saved_count
                logger.info(f"✅ {symbol}: Saved {saved_count} bars to database")

            except Exception as e:
                logger.error(f"❌ Failed to download {symbol}: {e}", exc_info=True)
                results[symbol] = 0

        logger.info(f"📥 Bulk download completed. Total: {sum(results.values())} bars")
        return results

    async def _save_bars_batched(
        self,
        bars: list[HistoricalBar],
        db_symbol: str,
        source: str,
        batch_size: int = 100,
    ) -> int:
        """Save bars to database in batches.

        Args:
            bars: List of historical bars
            db_symbol: Symbol with source prefix (e.g., "bitunix:BTCUSDT")
            source: Source name for metadata
            batch_size: Number of bars per batch

        Returns:
            Number of bars saved (excluding duplicates)
        """
        total_saved = 0
        total_batches = (len(bars) + batch_size - 1) // batch_size

        for i in range(0, len(bars), batch_size):
            batch = bars[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            try:
                saved = await asyncio.to_thread(
                    self._save_batch_sync,
                    batch,
                    db_symbol,
                    source
                )
                total_saved += saved

                if batch_num % 10 == 0 or batch_num == total_batches:
                    logger.debug(f"   Batch {batch_num}/{total_batches}: Saved {saved} bars")

            except Exception as e:
                logger.error(f"   Batch {batch_num} failed: {e}")

        return total_saved

    def _save_batch_sync(
        self,
        bars: list[HistoricalBar],
        db_symbol: str,
        source: str,
    ) -> int:
        """Synchronously save a batch of bars (runs in thread).

        Args:
            bars: List of bars to save
            db_symbol: Database symbol with source prefix
            source: Source name

        Returns:
            Number of bars saved (duplicates are skipped via ON CONFLICT)
        """
        saved_count = 0

        with self.db_manager.session() as session:
            for bar in bars:
                try:
                    # Create MarketBar instance
                    market_bar = MarketBar(
                        symbol=db_symbol,
                        timestamp=bar.timestamp,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=bar.volume,
                        vwap=bar.vwap,
                        source=source,
                        is_interpolated=False,
                    )

                    # Add and commit (unique constraint will skip duplicates)
                    session.add(market_bar)
                    session.flush()  # Flush to check for constraint violations
                    saved_count += 1

                except Exception as e:
                    # Skip duplicates (unique constraint violation)
                    session.rollback()
                    if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
                        continue  # Skip duplicate
                    else:
                        logger.warning(f"Error saving bar for {db_symbol}: {e}")

            session.commit()

        return saved_count

    async def get_data_coverage(
        self,
        symbol: str,
        source: DataSource,
    ) -> dict:
        """Get coverage information for a symbol.

        Args:
            symbol: Symbol to check
            source: Data source

        Returns:
            Dictionary with coverage info (first_date, last_date, total_bars)
        """
        db_symbol = format_symbol_with_source(symbol, source)

        return await asyncio.to_thread(
            self._get_coverage_sync,
            db_symbol
        )

    def _get_coverage_sync(self, db_symbol: str) -> dict:
        """Get coverage info synchronously."""
        with self.db_manager.session() as session:
            from sqlalchemy import func

            result = session.query(
                func.min(MarketBar.timestamp).label('first_date'),
                func.max(MarketBar.timestamp).label('last_date'),
                func.count(MarketBar.id).label('total_bars')
            ).filter(
                MarketBar.symbol == db_symbol
            ).first()

            if not result or result.total_bars == 0:
                return {
                    'symbol': db_symbol,
                    'first_date': None,
                    'last_date': None,
                    'total_bars': 0,
                    'coverage_days': 0
                }

            coverage_days = (result.last_date - result.first_date).days if result.first_date else 0

            return {
                'symbol': db_symbol,
                'first_date': result.first_date,
                'last_date': result.last_date,
                'total_bars': result.total_bars,
                'coverage_days': coverage_days
            }

    async def verify_data_integrity(
        self,
        symbol: str,
        source: DataSource,
        expected_timeframe: Timeframe = Timeframe.MINUTE_1,
    ) -> dict:
        """Verify data integrity and find gaps.

        Args:
            symbol: Symbol to verify
            source: Data source
            expected_timeframe: Expected timeframe between bars

        Returns:
            Dictionary with integrity info (gaps, missing_bars, etc.)
        """
        db_symbol = format_symbol_with_source(symbol, source)

        return await asyncio.to_thread(
            self._verify_integrity_sync,
            db_symbol,
            expected_timeframe
        )

    def _verify_integrity_sync(
        self,
        db_symbol: str,
        expected_timeframe: Timeframe,
    ) -> dict:
        """Verify integrity synchronously."""
        with self.db_manager.session() as session:
            bars = session.query(MarketBar).filter(
                MarketBar.symbol == db_symbol
            ).order_by(MarketBar.timestamp).all()

            if len(bars) < 2:
                return {
                    'symbol': db_symbol,
                    'total_bars': len(bars),
                    'gaps_found': 0,
                    'missing_bars': 0,
                    'integrity': 'insufficient_data'
                }

            # Calculate expected interval
            interval_map = {
                Timeframe.MINUTE_1: timedelta(minutes=1),
                Timeframe.MINUTE_5: timedelta(minutes=5),
                Timeframe.MINUTE_15: timedelta(minutes=15),
                Timeframe.HOUR_1: timedelta(hours=1),
                Timeframe.HOUR_4: timedelta(hours=4),
                Timeframe.DAY_1: timedelta(days=1),
            }
            expected_interval = interval_map.get(expected_timeframe, timedelta(minutes=1))

            # Find gaps
            gaps = []
            missing_bars = 0

            for i in range(1, len(bars)):
                actual_interval = bars[i].timestamp - bars[i-1].timestamp
                if actual_interval > expected_interval * 1.5:  # Allow 50% tolerance
                    gap_minutes = actual_interval.total_seconds() / 60
                    expected_bars = int(gap_minutes / (expected_interval.total_seconds() / 60))
                    gaps.append({
                        'start': bars[i-1].timestamp,
                        'end': bars[i].timestamp,
                        'duration': actual_interval,
                        'missing_bars': expected_bars
                    })
                    missing_bars += expected_bars

            return {
                'symbol': db_symbol,
                'total_bars': len(bars),
                'gaps_found': len(gaps),
                'missing_bars': missing_bars,
                'gaps': gaps[:10],  # First 10 gaps
                'integrity': 'good' if len(gaps) == 0 else 'gaps_found'
            }
