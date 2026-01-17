"""Alpaca Historical Data Manager - Separated from Bitunix.

Manages bulk downloading and caching of historical market data exclusively for Alpaca.
Uses helper classes for filtering and database operations.

This is a SEPARATE implementation from BitunixHistoricalDataManager.
NO shared code between Alpaca and Bitunix workflows.
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

from .alpaca_historical_data_config import FilterConfig, FilterStats
from .alpaca_bad_tick_detector import BadTickDetector
from .alpaca_historical_data_db import HistoricalDataDB

logger = logging.getLogger(__name__)


class AlpacaHistoricalDataManager:
    """Manages bulk downloading and caching of historical market data for ALPACA ONLY.

    Uses helper classes via composition:
    - BadTickDetector: Detection and cleaning of bad ticks
    - HistoricalDataDB: Database persistence operations

    COMPLETELY SEPARATE from BitunixHistoricalDataManager.
    """

    def __init__(self, filter_config: FilterConfig | None = None):
        """Initialize the Alpaca historical data manager.

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
        """Download historical data for multiple Alpaca symbols in bulk.

        Args:
            provider: Alpaca provider instance (AlpacaCryptoProvider)
            symbols: List of Alpaca symbols to download (e.g., ["BTC/USD", "ETH/USD"])
            days_back: Number of days of history to download (default: 365)
            timeframe: Timeframe for bars (default: 1min)
            source: Data source enum (fixed to ALPACA_CRYPTO)
            batch_size: Number of bars to save per batch (default: 100)
            filter_config: Override filter configuration for this download
            replace_existing: Delete existing data before downloading (default: True)
            progress_callback: Optional callback(batch_num, total_bars, status_msg) for UI updates

        Returns:
            Dictionary mapping symbols to number of bars saved

        Example:
            >>> from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
            >>> provider = AlpacaCryptoProvider()
            >>> manager = AlpacaHistoricalDataManager()
            >>> results = await manager.bulk_download(
            ...     provider,
            ...     ["BTC/USD", "ETH/USD"],
            ...     days_back=365,
            ...     source=DataSource.ALPACA_CRYPTO
            ... )
            >>> print(results)  # {"BTC/USD": 525600, "ETH/USD": 525600}
        """
        # Use provided config or fall back to instance config
        config = filter_config or self.filter_config
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"📥 Alpaca bulk download started:")
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
                    logger.info(f"🗑️  Deleted existing Alpaca data for {db_symbol}")

                logger.info(f"📡 Downloading Alpaca {symbol} from {source.value}...")

                # Fetch bars from Alpaca provider
                fetch_kwargs = {
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date,
                    'timeframe': timeframe,
                }
                # Alpaca provider doesn't support progress_callback in fetch_bars
                # Progress is handled at the batch level instead

                bars = await provider.fetch_bars(**fetch_kwargs)

                if not bars:
                    logger.warning(f"⚠️ No Alpaca data received for {symbol}")
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
                logger.info(f"✅ Alpaca {symbol}: Saved {len(bars)} bars to database")

            except Exception as e:
                logger.error(f"❌ Failed to download Alpaca {symbol}: {e}", exc_info=True)
                results[symbol] = 0

        # Log filter summary
        if config.enabled and config.log_stats:
            total_filter_stats.filtering_percentage = (
                total_filter_stats.bad_ticks_found / total_filter_stats.total_bars * 100
                if total_filter_stats.total_bars > 0 else 0
            )
            self._last_filter_stats = total_filter_stats
            logger.info(f"🛡️  Alpaca Filter Summary: {total_filter_stats.bad_ticks_found} bad ticks "
                       f"({total_filter_stats.filtering_percentage:.2f}%) in {total_filter_stats.total_bars} bars")

        logger.info(f"📥 Alpaca bulk download completed. Total: {sum(results.values())} bars")
        return results

    async def sync_history_to_now(
        self,
        provider,
        symbols: list[str],
        timeframe: Timeframe = Timeframe.MINUTE_1,
        source: DataSource = DataSource.ALPACA_CRYPTO,
        batch_size: int = 100,
        filter_config: FilterConfig | None = None,
        progress_callback: callable = None,
    ) -> dict[str, int]:
        """Sync Alpaca historical data up to now without re-downloading everything.

        Checks the last stored date for each symbol and downloads only the missing
        period. If no data exists, it downloads the full default period (365 days).

        Args:
            provider: Alpaca provider instance
            symbols: List of Alpaca symbols to sync
            timeframe: Timeframe for bars
            source: Data source enum (fixed to ALPACA_CRYPTO)
            batch_size: Number of bars to save per batch
            filter_config: Override filter configuration
            progress_callback: Optional callback for UI updates

        Returns:
            Dictionary mapping symbols to number of bars saved
        """
        logger.info(f"🔄 Alpaca Smart Sync started for {len(symbols)} symbols...")
        results = {}

        for i, symbol in enumerate(symbols):
            try:
                # Update progress callback if provided (overall progress)
                if progress_callback:
                    progress_callback(0, 0, f"Checking Alpaca coverage for {symbol}...")

                # 1. Check existing coverage
                db_symbol = format_symbol_with_source(symbol, source)
                coverage = await self._db_handler.get_data_coverage(db_symbol)

                days_to_fetch = 365  # Default fallback if no data

                if coverage and coverage.get('last_date'):
                    last_date = coverage['last_date']
                    # Ensure timezone awareness
                    if last_date.tzinfo is None:
                        last_date = last_date.replace(tzinfo=timezone.utc)

                    now = datetime.now(timezone.utc)
                    delta = now - last_date

                    # Add 1 day buffer to handle timezone overlaps safely
                    days_to_fetch = max(1, delta.days + 1)

                    logger.info(f"📅 Alpaca {symbol}: Last data from {last_date.date()} ({delta.days} days ago). Fetching {days_to_fetch} days.")
                else:
                    logger.info(f"📅 Alpaca {symbol}: No existing data found. Fetching full year.")

                # 2. Download only the missing period (reuse bulk_download for single symbol)
                symbol_result = await self.bulk_download(
                    provider=provider,
                    symbols=[symbol],
                    days_back=days_to_fetch,
                    timeframe=timeframe,
                    source=source,
                    batch_size=batch_size,
                    filter_config=filter_config,
                    replace_existing=False,  # CRITICAL: Keep existing Alpaca data
                    progress_callback=progress_callback
                )

                results.update(symbol_result)

            except Exception as e:
                logger.error(f"❌ Failed to sync Alpaca {symbol}: {e}", exc_info=True)
                results[symbol] = 0

        logger.info(f"✅ Alpaca Smart Sync completed. Updated {len(results)} symbols.")
        return results

    def get_last_filter_stats(self) -> FilterStats | None:
        """Get statistics from the last Alpaca filtering operation."""
        return self._last_filter_stats

    async def get_data_coverage(
        self,
        symbol: str,
        source: DataSource,
    ) -> dict:
        """Get coverage information for an Alpaca symbol (delegated to DB handler).

        Args:
            symbol: Alpaca symbol to check
            source: Data source (ALPACA_CRYPTO)

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
        """Verify Alpaca data integrity and find gaps (delegated to DB handler).

        Args:
            symbol: Alpaca symbol to verify
            source: Data source (ALPACA_CRYPTO)
            expected_timeframe: Expected timeframe between bars

        Returns:
            Dictionary with integrity info (gaps, missing_bars, etc.)
        """
        db_symbol = format_symbol_with_source(symbol, source)
        return await self._db_handler.verify_data_integrity(db_symbol)
