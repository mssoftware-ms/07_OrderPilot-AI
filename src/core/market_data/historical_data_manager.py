"""Historical Data Manager - Main Orchestrator.

Manages bulk downloading and caching of historical market data.
Uses helper classes for filtering and database operations.

Module 4/4 of historical_data_manager.py split - Main orchestrator.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pandas as pd

from src.core.market_data.types import (
    DataSource,
    HistoricalBar,
    Timeframe,
    format_symbol_with_source,
)
from src.database import get_db_manager

from .historical_data_config import FilterConfig, FilterStats
from .bad_tick_detector import BadTickDetector
from .historical_data_db import HistoricalDataDB

logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """Manages bulk downloading and caching of historical market data.

    Uses helper classes via composition:
    - BadTickDetector: Detection and cleaning of bad ticks
    - HistoricalDataDB: Database persistence operations
    """

    def __init__(self, filter_config: FilterConfig | None = None):
        """Initialize the historical data manager.

        Args:
            filter_config: Configuration for bad tick filtering (default: enabled with Hampel)
        """
        self.db_manager = get_db_manager()
        self.filter_config = filter_config or FilterConfig()
        self._last_filter_stats: FilterStats | None = None

        # Helper classes (composition pattern)
        self._detector = BadTickDetector(self.filter_config)
        self._db_handler = HistoricalDataDB(self.db_manager)

    async def bulk_download(
        self,
        provider,
        symbols: list[str],
        days_back: int = 365,
        timeframe: Timeframe = Timeframe.MINUTE_1,
        source: DataSource = DataSource.ALPACA_CRYPTO,
        batch_size: int = 100,
        filter_config: FilterConfig | None = None,
        replace_existing: bool = True,
        progress_callback: callable = None,
    ) -> dict[str, int]:
        """Download historical data for multiple symbols in bulk.

        Args:
            provider: Data provider instance (e.g., AlpacaProvider, BitunixProvider)
            symbols: List of symbols to download
            days_back: Number of days of history to download (default: 365)
            timeframe: Timeframe for bars (default: 1min)
            source: Data source enum for symbol prefixing
            batch_size: Number of bars to save per batch (default: 100)
            filter_config: Override filter configuration for this download
            replace_existing: Delete existing data before downloading (default: True)
                             This ensures clean data without old bad ticks.
            progress_callback: Optional callback(batch_num, total_bars, status_msg) for UI updates

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

        Note:
            Bad ticks are automatically filtered using Hampel Filter with Volume
            Confirmation. Price spikes without corresponding high volume are
            interpolated to maintain data continuity without gaps.
        """
        # Use provided config or fall back to instance config
        config = filter_config or self.filter_config
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"📥 Bulk download started:")
        logger.info(f"   Symbols: {symbols}")
        logger.info(f"   Period: {start_date.date()} to {end_date.date()} ({days_back} days)")
        logger.info(f"   Timeframe: {timeframe.value}")
        logger.info(f"   Source: {source.value}")
        logger.info(f"   Replace Existing: {'YES' if replace_existing else 'NO'}")
        logger.info(f"   Bad Tick Filter: {'ENABLED' if config.enabled else 'DISABLED'} ({config.method})")

        results = {}
        total_filter_stats = FilterStats()

        for symbol in symbols:
            try:
                # Format symbol with source prefix for database
                db_symbol = format_symbol_with_source(symbol, source)

                # Delete existing data if replace mode is enabled
                if replace_existing:
                    await self._db_handler.delete_symbol_data(db_symbol)
                    logger.info(f"🗑️  Deleted existing data for {db_symbol}")

                logger.info(f"📡 Downloading {symbol} from {source.value}...")

                # Fetch bars from provider with progress callback
                # Check if provider supports progress_callback (BitunixProvider does)
                fetch_kwargs = {
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date,
                    'timeframe': timeframe,
                }
                # Add progress_callback if provider supports it
                if progress_callback is not None:
                    import inspect
                    sig = inspect.signature(provider.fetch_bars)
                    if 'progress_callback' in sig.parameters:
                        fetch_kwargs['progress_callback'] = progress_callback

                bars = await provider.fetch_bars(**fetch_kwargs)

                if not bars:
                    logger.warning(f"⚠️ No data received for {symbol}")
                    results[symbol] = 0
                    continue

                # Apply bad tick filtering before saving (delegated)
                if config.enabled:
                    # Update detector config if different from instance config
                    if config != self.filter_config:
                        detector = BadTickDetector(config)
                    else:
                        detector = self._detector

                    bars, stats = await detector.filter_bad_ticks(bars, symbol)
                    total_filter_stats.total_bars += stats.total_bars
                    total_filter_stats.bad_ticks_found += stats.bad_ticks_found
                    total_filter_stats.bad_ticks_interpolated += stats.bad_ticks_interpolated
                    total_filter_stats.bad_ticks_removed += stats.bad_ticks_removed

                # Format symbol with source prefix for database
                db_symbol = format_symbol_with_source(symbol, source)

                # Save to database in batches (delegated)
                await self._db_handler.save_bars_batched(
                    bars,
                    db_symbol,
                    source.value,
                    batch_size
                )

                results[symbol] = len(bars)
                logger.info(f"✅ {symbol}: Saved {len(bars)} bars to database")

            except Exception as e:
                logger.error(f"❌ Failed to download {symbol}: {e}", exc_info=True)
                results[symbol] = 0

        # Log filter summary
        if config.enabled and config.log_stats:
            total_filter_stats.filtering_percentage = (
                total_filter_stats.bad_ticks_found / total_filter_stats.total_bars * 100
                if total_filter_stats.total_bars > 0 else 0
            )
            self._last_filter_stats = total_filter_stats
            logger.info(f"🛡️  Filter Summary: {total_filter_stats.bad_ticks_found} bad ticks "
                       f"({total_filter_stats.filtering_percentage:.2f}%) in {total_filter_stats.total_bars} bars")

        logger.info(f"📥 Bulk download completed. Total: {sum(results.values())} bars")
        return results

    def get_last_filter_stats(self) -> FilterStats | None:
        """Get statistics from the last filtering operation."""
        return self._last_filter_stats

    async def get_data_coverage(
        self,
        symbol: str,
        source: DataSource,
    ) -> dict:
        """Get coverage information for a symbol (delegated to DB handler).

        Args:
            symbol: Symbol to check
            source: Data source

        Returns:
            Dictionary with coverage info (first_date, last_date, total_bars)
        """
        db_symbol = format_symbol_with_source(symbol, source)
        return await self._db_handler.get_data_coverage(db_symbol)

    async def verify_data_integrity(
        self,
        symbol: str,
        source: DataSource,
        expected_timeframe: Timeframe = Timeframe.MINUTE_1,
    ) -> dict:
        """Verify data integrity and find gaps (delegated to DB handler).

        Args:
            symbol: Symbol to verify
            source: Data source
            expected_timeframe: Expected timeframe between bars

        Returns:
            Dictionary with integrity info (gaps, missing_bars, etc.)
        """
        db_symbol = format_symbol_with_source(symbol, source)
        return await self._db_handler.verify_data_integrity(db_symbol)

    async def clean_existing_data(
        self,
        symbol: str,
        source: DataSource,
        filter_config: FilterConfig | None = None,
        dry_run: bool = True,
    ) -> FilterStats:
        """Clean bad ticks from already stored data (NOT IMPLEMENTED - requires DB handler extension).

        This method would need to:
        1. Load existing data from DB
        2. Detect bad ticks using BadTickDetector
        3. Update/remove bad ticks in DB

        Currently returns empty stats.

        Args:
            symbol: Symbol to clean (e.g., "BTC/USD")
            source: Data source (e.g., DataSource.ALPACA_CRYPTO)
            filter_config: Filter configuration (uses instance config if None)
            dry_run: If True, only report what would be cleaned without modifying

        Returns:
            FilterStats with cleaning results
        """
        logger.warning("clean_existing_data not yet implemented with new architecture")
        return FilterStats()

    async def scan_all_symbols_for_bad_ticks(
        self,
        filter_config: FilterConfig | None = None,
    ) -> dict[str, FilterStats]:
        """Scan all symbols in database for bad ticks (NOT IMPLEMENTED).

        Would require DB handler to provide symbol iteration.

        Args:
            filter_config: Filter configuration

        Returns:
            Dictionary mapping symbols to their filter stats
        """
        logger.warning("scan_all_symbols_for_bad_ticks not yet implemented with new architecture")
        return {}
