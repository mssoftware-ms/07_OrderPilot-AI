"""History Provider Fetching - Data fetching logic with fallback.

Refactored from 700 LOC monolith using composition pattern.

Module 2/3 of history_provider.py split.

Contains:
- fetch_data(): Main fetch with fallback
- _needs_fresh_data(): Freshness check
- _try_specific_source(): Try specific source first
- _try_provider_source(): Try provider source
- _should_skip_source(): Skip logic (crypto/stock separation)
- _handle_provider_success(): Handle success (store + emit event)
- _store_to_database(): Database caching
- get_latest_price(): Get latest price
- get_available_sources(): Get available sources
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from src.common.event_bus import Event, EventType, event_bus
from src.core.market_data.types import AssetClass, DataRequest, DataSource, HistoricalBar, Timeframe
from src.database import get_db_manager
from src.database.models import MarketBar

if TYPE_CHECKING:
    from src.core.market_data.providers import HistoricalDataProvider

logger = logging.getLogger(__name__)


class HistoryProviderFetching:
    """Helper für HistoryManager Fetching (Data Fetch, Fallback, Caching)."""

    def __init__(self, parent):
        """
        Args:
            parent: HistoryManager Instanz
        """
        self.parent = parent

    async def fetch_data(
        self,
        request: DataRequest
    ) -> tuple[list[HistoricalBar], str]:
        """Fetch historical data with incremental sync support.

        Strategy:
        1. Check database first for existing data
        2. If DB has partial data (last_bar < end_date), fetch missing data from API
        3. Merge DB + API data and cache new API bars
        4. If specific source requested, use only that source

        Args:
            request: Data request

        Returns:
            Tuple of (bars, source_used)
        """
        needs_fresh_data = self._needs_fresh_data(request)

        # CRITICAL FIX: If specific source is requested, ONLY try that source (no fallback)
        if request.source:
            bars, source_used = await self._try_specific_source(request)
            if bars:
                return bars, source_used
            # No fallback - user explicitly requested this source
            logger.error(f"Failed to get data from requested source {request.source.value} for {request.symbol}")
            return [], "none"

        # No specific source requested - try incremental sync with database
        bars, source_used = await self._fetch_with_incremental_sync(request, needs_fresh_data)
        if bars:
            return bars, source_used

        # Fallback: Try providers in priority order (old behavior)
        for source in self.parent.priority_order:
            bars = await self._try_provider_source(request, source, needs_fresh_data)
            if bars:
                return bars, source.value

        logger.warning(f"No data available for {request.symbol}")
        return [], "none"

    def _needs_fresh_data(self, request: DataRequest) -> bool:
        """Check if request needs fresh data from API (skip database cache).

        Fresh data is needed when end_date is in the recent past (< 5 minutes ago).
        If end_date is in the future (e.g., end of day), database can be used.

        Args:
            request: Data request to check

        Returns:
            True if fresh API data needed, False if database can be used
        """
        if not request.end_date:
            return False
        end_dt = request.end_date
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)
        end_dt_utc = end_dt.astimezone(timezone.utc)

        # If end_date is in the future, database can be used (no fresh data needed)
        if end_dt_utc > now_utc:
            logger.debug(
                f"End date is {(end_dt_utc - now_utc).total_seconds():.0f}s in future - using database"
            )
            return False

        # Check if end_date is recent past (< 5 minutes ago)
        time_diff = now_utc - end_dt_utc
        if time_diff < timedelta(minutes=5):
            logger.info(
                f"Fresh data needed for {request.symbol} (end_date is {time_diff.total_seconds():.0f}s ago)"
            )
            return True

        # Older data can use database cache
        logger.debug(
            f"End date is {time_diff.total_seconds():.0f}s ago - using database"
        )
        return False

    async def _fetch_with_incremental_sync(
        self,
        request: DataRequest,
        needs_fresh_data: bool,
    ) -> tuple[list[HistoricalBar], str]:
        """Fetch data with incremental sync: DB cache + API for missing recent data.

        Strategy:
        1. Check database for existing data and last timestamp
        2. If DB has complete data (last_bar >= end_date): return DB data
        3. If DB has partial data (last_bar < end_date):
           - Load DB data (start_date → last_bar)
           - Fetch missing data from API (last_bar → end_date)
           - Merge DB + API data
           - Cache new API bars to DB
        4. If DB empty: fetch all from API

        Args:
            request: Data request
            needs_fresh_data: Whether fresh data is needed

        Returns:
            Tuple of (bars, source_used) or ([], "") if failed
        """
        # Get database provider
        db_provider = self.parent.providers.get(DataSource.DATABASE)
        if not db_provider:
            logger.debug("Database provider not available for incremental sync")
            return [], ""

        # Check last timestamp in database
        last_db_timestamp = await db_provider.get_last_timestamp(request.symbol)

        if not last_db_timestamp:
            logger.info(f"📂 No data in database for {request.symbol} - will fetch from API")
            return [], ""

        # Convert timestamps for comparison
        if last_db_timestamp.tzinfo is None:
            last_db_timestamp = last_db_timestamp.replace(tzinfo=timezone.utc)
        end_dt = request.end_date
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        end_dt_utc = end_dt.astimezone(timezone.utc)
        last_db_utc = last_db_timestamp.astimezone(timezone.utc)

        # Case 1: Database has complete data (last_bar >= end_date)
        if last_db_utc >= end_dt_utc:
            logger.info(f"📂 Database has complete data for {request.symbol} (last bar: {last_db_utc.strftime('%Y-%m-%d %H:%M:%S UTC')})")
            db_bars = await db_provider.fetch_bars(
                request.symbol,
                request.start_date,
                request.end_date,
                request.timeframe,
            )
            if db_bars:
                return db_bars, "database"
            else:
                logger.warning("Database query returned no bars despite last_timestamp check")
                return [], ""

        # Case 2: Database has partial data - incremental sync needed
        time_gap = (end_dt_utc - last_db_utc).total_seconds() / 60  # minutes
        logger.info(f"📂 Database has partial data for {request.symbol}")
        logger.info(f"   Last DB bar: {last_db_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"   Requested until: {end_dt_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"   Gap: {time_gap:.1f} minutes → fetching from API")

        # Load existing DB data
        db_bars = await db_provider.fetch_bars(
            request.symbol,
            request.start_date,
            last_db_timestamp,  # Until last DB bar
            request.timeframe,
        )
        logger.info(f"📂 Loaded {len(db_bars)} bars from database")

        # Fetch missing data from API
        api_source = self._get_api_source_for_symbol(request)
        if not api_source:
            logger.warning(f"No API provider available for {request.symbol}")
            # Return partial DB data
            return db_bars, "database (partial)" if db_bars else ([], "")

        api_provider = self.parent.providers.get(api_source)
        if not api_provider or not await api_provider.is_available():
            logger.warning(f"API provider {api_source.value} not available")
            # Return partial DB data
            return db_bars, "database (partial)" if db_bars else ([], "")

        try:
            # Fetch from last_db_timestamp + 1 minute to end_date
            sync_start = last_db_timestamp + timedelta(minutes=1)
            logger.info(f"🔄 Fetching missing data from {api_source.value} ({sync_start.strftime('%Y-%m-%d %H:%M:%S')} → {request.end_date.strftime('%Y-%m-%d %H:%M:%S')})")

            await asyncio.sleep(api_provider.rate_limit_delay)
            api_bars = await api_provider.fetch_bars(
                request.symbol,
                sync_start,
                request.end_date,
                request.timeframe,
            )

            if api_bars:
                logger.info(f"🔄 Fetched {len(api_bars)} new bars from {api_source.value}")
                # Store new bars to database
                await self._store_to_database(api_bars, request.symbol)

                # Merge DB + API bars
                all_bars = db_bars + api_bars
                logger.info(f"✅ Merged data: {len(db_bars)} (DB) + {len(api_bars)} (API) = {len(all_bars)} total bars")
                return all_bars, f"database+{api_source.value}"
            else:
                logger.warning(f"API returned no data for missing period")
                # Return partial DB data
                return db_bars, "database (partial)" if db_bars else ([], "")

        except Exception as e:
            logger.error(f"Error fetching missing data from API: {e}", exc_info=True)
            # Return partial DB data on error
            return db_bars, "database (partial)" if db_bars else ([], "")

    def _get_api_source_for_symbol(self, request: DataRequest) -> DataSource | None:
        """Determine appropriate API source for symbol.

        Args:
            request: Data request with symbol and asset_class

        Returns:
            DataSource enum for API, or None if no suitable provider
        """
        symbol = request.symbol
        asset_class = request.asset_class

        # Crypto: Bitunix or Alpaca Crypto
        if asset_class == AssetClass.CRYPTO:
            if "USDT" in symbol or "USDC" in symbol:
                return DataSource.BITUNIX  # BTCUSDT → Bitunix
            elif "/" in symbol:
                return DataSource.ALPACA_CRYPTO  # BTC/USD → Alpaca
            else:
                return DataSource.BITUNIX  # Default for crypto

        # Stocks: Alpaca
        return DataSource.ALPACA

    async def _try_specific_source(
        self, request: DataRequest
    ) -> tuple[list[HistoricalBar], str]:
        if not (request.source and request.source in self.parent.providers):
            return [], ""
        provider = self.parent.providers[request.source]
        if not await provider.is_available():
            from src.ui.dialogs.error_dialog import show_error_dialog
            error_msg = f"Provider {request.source.value} ist nicht verfügbar!"
            logger.error(error_msg)
            show_error_dialog("Provider Fehler", error_msg)
            return [], ""

        logger.info(f"Using specific source: {request.source.value} for {request.symbol}")
        try:
            bars = await provider.fetch_bars(
                request.symbol,
                request.start_date,
                request.end_date,
                request.timeframe,
            )
        except Exception as e:
            from src.ui.dialogs.error_dialog import show_error_dialog
            error_msg = f"Fehler beim Laden von {request.symbol} von {request.source.value}:\n{str(e)}"
            logger.error(error_msg, exc_info=True)
            show_error_dialog("Datenfehler", error_msg)
            return [], ""

        if bars:
            await self._store_to_database(bars, request.symbol)
            logger.info(f"Got {len(bars)} bars from {request.source.value}")
            return bars, request.source.value

        from src.ui.dialogs.error_dialog import show_error_dialog
        error_msg = f"Keine Daten von {request.source.value} für {request.symbol} erhalten!"
        logger.error(error_msg)
        show_error_dialog("Keine Daten", error_msg)
        return [], ""

    async def _try_provider_source(
        self,
        request: DataRequest,
        source: DataSource,
        needs_fresh_data: bool,
    ) -> list[HistoricalBar]:
        if source not in self.parent.providers:
            return []

        if self._should_skip_source(request, source, needs_fresh_data):
            return []

        provider = self.parent.providers[source]
        if not await provider.is_available():
            return []

        try:
            await asyncio.sleep(provider.rate_limit_delay)
            bars = await provider.fetch_bars(
                request.symbol,
                request.start_date,
                request.end_date,
                request.timeframe,
            )
            if bars:
                await self._handle_provider_success(request, source, bars)
                logger.info(f"Fetched {len(bars)} bars from {source.value}")
            return bars
        except Exception as e:
            logger.error(f"Error with {source.value} provider: {e}")
            return []

    def _should_skip_source(
        self,
        request: DataRequest,
        source: DataSource,
        needs_fresh_data: bool,
    ) -> bool:
        if needs_fresh_data and source == DataSource.DATABASE:
            logger.debug(f"Skipping {source.value} because fresh data is needed")
            return True

        if request.asset_class == AssetClass.CRYPTO:
            # CRITICAL: Strict separation of Alpaca and Bitunix crypto providers
            # Alpaca Crypto: BTC/USD, ETH/USD (symbols with slash)
            # Bitunix: BTCUSDT, ETHUSDT (symbols with USDT/USDC suffix)
            symbol = request.symbol
            is_alpaca_crypto = "/" in symbol  # BTC/USD format
            is_bitunix = "USDT" in symbol or "USDC" in symbol  # BTCUSDT format

            if source == DataSource.ALPACA_CRYPTO and is_bitunix:
                logger.debug(f"Skipping Alpaca Crypto for Bitunix symbol {symbol}")
                return True
            if source == DataSource.BITUNIX and is_alpaca_crypto:
                logger.debug(f"Skipping Bitunix for Alpaca Crypto symbol {symbol}")
                return True
            if source not in [DataSource.ALPACA_CRYPTO, DataSource.BITUNIX, DataSource.DATABASE]:
                logger.debug(f"Skipping {source.value} for crypto asset class")
                return True
        else:
            # Additional safeguard: symbols like BTCUSDT should never hit Alpaca crypto even if asset_class not set
            symbol = request.symbol
            if source == DataSource.ALPACA_CRYPTO and ("USDT" in symbol or "USDC" in symbol) and "/" not in symbol:
                logger.debug(f"Skipping Alpaca Crypto (safety) for Bitunix-style symbol {symbol}")
                return True

        if request.asset_class == AssetClass.STOCK:
            if source in [DataSource.ALPACA_CRYPTO, DataSource.BITUNIX]:
                logger.debug(f"Skipping {source.value} for stock asset class")
                return True

        if source == DataSource.YAHOO:
            intraday_timeframes = [
                Timeframe.MINUTE_1, Timeframe.MINUTE_5, Timeframe.MINUTE_15,
                Timeframe.MINUTE_30, Timeframe.HOUR_1, Timeframe.HOUR_4,
            ]
            if request.timeframe in intraday_timeframes:
                logger.debug(
                    f"Skipping Yahoo Finance for intraday timeframe {request.timeframe.value}"
                )
                return True

        return False

    async def _handle_provider_success(
        self,
        request: DataRequest,
        source: DataSource,
        bars: list[HistoricalBar],
    ) -> None:
        if source != DataSource.DATABASE:
            await self._store_to_database(bars, request.symbol)

        event_bus.emit(
            Event(
                type=EventType.MARKET_DATA_FETCHED,
                timestamp=datetime.utcnow(),
                data={
                    "symbol": request.symbol,
                    "source": source.value,
                    "bars_count": len(bars),
                    "timeframe": request.timeframe.value,
                },
                source="history_manager",
            )
        )

    async def _store_to_database(
        self,
        bars: list[HistoricalBar],
        symbol: str
    ) -> None:
        """Store bars to database for caching."""
        if not bars:
            return

        try:
            db_manager = get_db_manager()
            with db_manager.session() as session:
                timestamps = [bar.timestamp for bar in bars]
                min_ts = min(timestamps)
                max_ts = max(timestamps)

                existing_rows = session.query(MarketBar.timestamp).filter(
                    MarketBar.symbol == symbol,
                    MarketBar.timestamp >= min_ts,
                    MarketBar.timestamp <= max_ts
                ).all()
                existing_timestamps = {row[0] for row in existing_rows}

                new_bars = []
                for bar in bars:
                    if bar.timestamp in existing_timestamps:
                        continue
                    new_bars.append(MarketBar(
                        symbol=symbol,
                        timestamp=bar.timestamp,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=bar.volume,
                        vwap=bar.vwap,
                        source=bar.source
                    ))

                if new_bars:
                    session.bulk_save_objects(new_bars)
                    session.commit()
                    logger.debug(f"Stored {len(new_bars)} bars to database")
                else:
                    logger.debug("All fetched bars already cached locally")

        except Exception as e:
            logger.error(f"Failed to store bars to database: {e}")

    async def get_latest_price(self, symbol: str) -> Decimal | None:
        """Get latest price for symbol."""
        request = DataRequest(
            symbol=symbol,
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            timeframe=Timeframe.MINUTE_1
        )

        bars, _ = await self.fetch_data(request)

        if bars:
            return bars[-1].close

        return None

    def get_available_sources(self) -> list[str]:
        """Get list of available data sources."""
        return [source.value for source in self.parent.providers.keys()]
