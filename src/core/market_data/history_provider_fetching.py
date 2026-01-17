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
        """Fetch historical data with fallback.

        Args:
            request: Data request

        Returns:
            Tuple of (bars, source_used)
        """
        needs_fresh_data = self._needs_fresh_data(request)

        bars, source_used = await self._try_specific_source(request)
        if bars:
            return bars, source_used

        # Try providers in priority order
        for source in self.parent.priority_order:
            bars = await self._try_provider_source(request, source, needs_fresh_data)
            if bars:
                return bars, source.value

        logger.warning(f"No data available for {request.symbol}")
        return [], "none"

    def _needs_fresh_data(self, request: DataRequest) -> bool:
        if not request.end_date:
            return False
        end_dt = request.end_date
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)
        time_diff = now_utc - end_dt.astimezone(timezone.utc)
        if time_diff < timedelta(minutes=5):
            logger.info(
                f"Fresh data needed for {request.symbol} (end_date is {time_diff.total_seconds():.0f}s ago)"
            )
            return True
        return False

    async def _try_specific_source(
        self, request: DataRequest
    ) -> tuple[list[HistoricalBar], str]:
        if not (request.source and request.source in self.parent.providers):
            return [], ""
        provider = self.parent.providers[request.source]
        if not await provider.is_available():
            logger.warning(f"Provider {request.source.value} not available, trying fallback...")
            return [], ""

        logger.info(f"Using specific source: {request.source.value} for {request.symbol}")
        bars = await provider.fetch_bars(
            request.symbol,
            request.start_date,
            request.end_date,
            request.timeframe,
        )
        if bars:
            await self._store_to_database(bars, request.symbol)
            logger.info(f"Got {len(bars)} bars from {request.source.value}")
            return bars, request.source.value
        logger.warning(f"No bars returned from {request.source.value}, trying fallback...")
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
