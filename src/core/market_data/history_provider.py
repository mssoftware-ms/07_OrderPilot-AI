"""Historical Market Data Manager.

Manages historical market data with fallback support across multiple providers.
Primary source: Alpaca, with fallbacks to Yahoo, Alpha Vantage, etc.

REFACTORED: Provider classes moved to providers/ package for better organization.
REFACTORED (v2): Split into 3 helper modules using composition pattern:
- history_provider_config.py: Configuration and provider initialization
- history_provider_fetching.py: Data fetching logic with fallback
- history_provider_streaming.py: Real-time streaming (stocks, crypto, Bitunix)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from src.common.event_bus import Event, EventType, event_bus
from src.config.loader import config_manager
from src.core.broker import BrokerAdapter
from src.core.market_data.types import AssetClass, DataRequest, DataSource, HistoricalBar, Timeframe
from src.database import get_db_manager
from src.database.models import MarketBar

# Import providers from new package
from src.core.market_data.providers import (
    HistoricalDataProvider,
    AlpacaProvider,
    BitunixProvider,
    YahooFinanceProvider,
    AlphaVantageProvider,
    FinnhubProvider,
    IBKRHistoricalProvider,
    DatabaseProvider,
)

# Import helper modules (composition pattern)
from src.core.market_data.history_provider_config import HistoryProviderConfig
from src.core.market_data.history_provider_fetching import HistoryProviderFetching
from src.core.market_data.history_provider_streaming import HistoryProviderStreaming

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = [
    "HistoricalDataProvider",
    "AlpacaProvider",
    "BitunixProvider",
    "YahooFinanceProvider",
    "AlphaVantageProvider",
    "FinnhubProvider",
    "IBKRHistoricalProvider",
    "DatabaseProvider",
    "HistoryManager",
]


class HistoryManager:
    """Manager for historical data with fallback support."""

    def __init__(self, ibkr_adapter: BrokerAdapter | None = None):
        """Initialize history manager.

        Args:
            ibkr_adapter: Optional broker adapter for live IBKR data
        """
        self.providers: dict[DataSource, HistoricalDataProvider] = {}
        self.priority_order = []
        self.stream_client = None  # Real-time stream client

        # Locks to prevent race conditions when multiple charts open simultaneously
        self._crypto_stream_lock = asyncio.Lock()
        self._stock_stream_lock = asyncio.Lock()

        # Instantiate helper modules (composition pattern)
        self._config = HistoryProviderConfig(parent=self)
        self._fetching = HistoryProviderFetching(parent=self)
        self._streaming = HistoryProviderStreaming(parent=self)

        # Initialize database provider (always available)
        self.providers[DataSource.DATABASE] = DatabaseProvider()
        self._config.configure_priority()
        self._config.initialize_providers_from_config(ibkr_adapter)

        logger.info("History manager initialized")

    def register_provider(
        self,
        source: DataSource,
        provider: HistoricalDataProvider
    ) -> None:
        """Register a data provider.

        Args:
            source: Data source type
            provider: Provider instance
        """
        self.providers[source] = provider
        logger.info(f"Registered {source.value} provider")

    def set_ibkr_adapter(self, adapter: BrokerAdapter) -> None:
        """Register or update the IBKR provider on-demand."""
        self.register_provider(DataSource.IBKR, IBKRHistoricalProvider(adapter))

    async def fetch_data(
        self,
        request: DataRequest
    ) -> tuple[list[HistoricalBar], str]:
        """Fetch historical data with fallback.

        Delegates to HistoryProviderFetching.fetch_data().

        Args:
            request: Data request

        Returns:
            Tuple of (bars, source_used)
        """
        return await self._fetching.fetch_data(request)

    async def get_latest_price(self, symbol: str) -> Decimal | None:
        """Get latest price for symbol.

        Delegates to HistoryProviderFetching.get_latest_price().
        """
        return await self._fetching.get_latest_price(symbol)

    def get_available_sources(self) -> list[str]:
        """Get list of available data sources.

        Delegates to HistoryProviderFetching.get_available_sources().
        """
        return self._fetching.get_available_sources()

    async def start_realtime_stream(
        self,
        symbols: list[str],
        enable_indicators: bool = True
    ) -> bool:
        """Start real-time market data streaming.

        Delegates to HistoryProviderStreaming.start_realtime_stream().
        """
        return await self._streaming.start_realtime_stream(symbols, enable_indicators)

    async def stop_realtime_stream(self):
        """Stop real-time market data streaming.

        Delegates to HistoryProviderStreaming.stop_realtime_stream().
        """
        await self._streaming.stop_realtime_stream()

    async def start_crypto_realtime_stream(
        self,
        crypto_symbols: list[str]
    ) -> bool:
        """Start real-time cryptocurrency market data streaming.

        Delegates to HistoryProviderStreaming.start_crypto_realtime_stream().
        """
        return await self._streaming.start_crypto_realtime_stream(crypto_symbols)

    async def stop_crypto_realtime_stream(self):
        """Stop real-time cryptocurrency market data streaming.

        Delegates to HistoryProviderStreaming.stop_crypto_realtime_stream().
        """
        await self._streaming.stop_crypto_realtime_stream()

    async def start_bitunix_stream(
        self,
        bitunix_symbols: list[str]
    ) -> bool:
        """Start real-time Bitunix WebSocket streaming for crypto futures.

        Delegates to HistoryProviderStreaming.start_bitunix_stream().
        """
        return await self._streaming.start_bitunix_stream(bitunix_symbols)

    async def stop_bitunix_stream(self):
        """Stop real-time Bitunix WebSocket streaming.

        Delegates to HistoryProviderStreaming.stop_bitunix_stream().
        """
        await self._streaming.stop_bitunix_stream()

    def get_realtime_tick(self, symbol: str):
        """Get latest real-time tick for a symbol.

        Delegates to HistoryProviderStreaming.get_realtime_tick().
        """
        return self._streaming.get_realtime_tick(symbol)

    def get_stream_metrics(self) -> dict | None:
        """Get real-time stream metrics.

        Delegates to HistoryProviderStreaming.get_stream_metrics().
        """
        return self._streaming.get_stream_metrics()

    async def fetch_realtime_indicators(
        self,
        symbol: str,
        interval: str = "1min"
    ) -> dict:
        """Fetch real-time technical indicators.

        Delegates to HistoryProviderStreaming.fetch_realtime_indicators().
        """
        return await self._streaming.fetch_realtime_indicators(symbol, interval)
