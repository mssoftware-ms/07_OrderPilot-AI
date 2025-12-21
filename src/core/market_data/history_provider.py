"""Historical Market Data Manager.

Manages historical market data with fallback support across multiple providers.
Primary source: Alpaca, with fallbacks to Yahoo, Alpha Vantage, etc.

REFACTORED: Provider classes moved to providers/ package for better organization.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
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
    YahooFinanceProvider,
    AlphaVantageProvider,
    FinnhubProvider,
    IBKRHistoricalProvider,
    DatabaseProvider,
)

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = [
    "HistoricalDataProvider",
    "AlpacaProvider",
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

        # Initialize database provider (always available)
        self.providers[DataSource.DATABASE] = DatabaseProvider()
        self._configure_priority()
        self._initialize_providers_from_config(ibkr_adapter)

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

    def _configure_priority(self) -> None:
        """Configure provider priority order from settings."""
        profile = config_manager.load_profile()
        market_config = profile.market_data

        live_first = market_config.prefer_live_broker

        if live_first:
            self.priority_order = [
                DataSource.DATABASE,
                DataSource.IBKR,
                DataSource.ALPACA,
                DataSource.ALPACA_CRYPTO,
                DataSource.ALPHA_VANTAGE,
                DataSource.FINNHUB,
                DataSource.YAHOO
            ]
        else:
            self.priority_order = [
                DataSource.DATABASE,
                DataSource.ALPACA,
                DataSource.ALPACA_CRYPTO,
                DataSource.ALPHA_VANTAGE,
                DataSource.FINNHUB,
                DataSource.YAHOO,
                DataSource.IBKR
            ]

    def _initialize_providers_from_config(self, ibkr_adapter: BrokerAdapter | None) -> None:
        """Register providers according to configuration and credentials."""
        profile = config_manager.load_profile()
        market_config = profile.market_data

        # Register IBKR if adapter supplied
        if ibkr_adapter:
            self.register_provider(DataSource.IBKR, IBKRHistoricalProvider(ibkr_adapter))

        # Alpaca (Stocks)
        if market_config.alpaca_enabled:
            api_key = config_manager.get_credential("alpaca_api_key")
            api_secret = config_manager.get_credential("alpaca_api_secret")
            if api_key and api_secret:
                self.register_provider(DataSource.ALPACA, AlpacaProvider(api_key, api_secret))
                logger.info(f"Registered Alpaca stock provider (key: {api_key[:8]}...)")

                # Also register Alpaca Crypto provider with same credentials
                from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
                self.register_provider(DataSource.ALPACA_CRYPTO, AlpacaCryptoProvider(api_key, api_secret))
                logger.info(f"Registered Alpaca crypto provider (key: {api_key[:8]}...)")
            else:
                logger.warning("Alpaca provider enabled but API credentials not found")
        else:
            logger.warning("Alpaca provider is DISABLED in config")

        # Alpha Vantage
        if market_config.alpha_vantage_enabled:
            api_key = config_manager.get_credential("alpha_vantage_api_key")
            if api_key:
                self.register_provider(DataSource.ALPHA_VANTAGE, AlphaVantageProvider(api_key))
            else:
                logger.warning("Alpha Vantage provider enabled but API key not found")

        # Finnhub
        if market_config.finnhub_enabled:
            api_key = config_manager.get_credential("finnhub_api_key")
            if api_key:
                self.register_provider(DataSource.FINNHUB, FinnhubProvider(api_key))
            else:
                logger.warning("Finnhub provider enabled but API key not found")

        # Yahoo Finance (no API key required)
        if market_config.yahoo_enabled:
            self.register_provider(DataSource.YAHOO, YahooFinanceProvider())

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
        needs_fresh_data = False

        if request.end_date:
            end_dt = request.end_date
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)

            now_utc = datetime.now(timezone.utc)
            time_diff = now_utc - end_dt.astimezone(timezone.utc)

            if time_diff < timedelta(minutes=5):
                needs_fresh_data = True
                logger.info(f"Fresh data needed for {request.symbol} (end_date is {time_diff.total_seconds():.0f}s ago)")

        # Try specific source if requested
        if request.source and request.source in self.providers:
            provider = self.providers[request.source]
            if await provider.is_available():
                logger.info(f"Using specific source: {request.source.value} for {request.symbol}")
                bars = await provider.fetch_bars(
                    request.symbol,
                    request.start_date,
                    request.end_date,
                    request.timeframe
                )
                if bars:
                    await self._store_to_database(bars, request.symbol)
                    logger.info(f"Got {len(bars)} bars from {request.source.value}")
                    return bars, request.source.value
                else:
                    logger.warning(f"No bars returned from {request.source.value}, trying fallback...")
            else:
                logger.warning(f"Provider {request.source.value} not available, trying fallback...")

        # Try providers in priority order
        for source in self.priority_order:
            if source not in self.providers:
                continue

            # Skip DATABASE if we need fresh data
            if needs_fresh_data and source == DataSource.DATABASE:
                logger.debug(f"Skipping {source.value} because fresh data is needed")
                continue

            # Skip providers based on asset class
            if request.asset_class == AssetClass.CRYPTO:
                if source not in [DataSource.ALPACA_CRYPTO, DataSource.DATABASE]:
                    logger.debug(f"Skipping {source.value} for crypto asset class")
                    continue
            elif request.asset_class == AssetClass.STOCK:
                if source == DataSource.ALPACA_CRYPTO:
                    logger.debug(f"Skipping {source.value} for stock asset class")
                    continue

            # Skip Yahoo Finance for intraday timeframes
            if source == DataSource.YAHOO:
                intraday_timeframes = [
                    Timeframe.MINUTE_1, Timeframe.MINUTE_5, Timeframe.MINUTE_15,
                    Timeframe.MINUTE_30, Timeframe.HOUR_1, Timeframe.HOUR_4
                ]
                if request.timeframe in intraday_timeframes:
                    logger.debug(f"Skipping Yahoo Finance for intraday timeframe {request.timeframe.value}")
                    continue

            provider = self.providers[source]
            if not await provider.is_available():
                continue

            try:
                await asyncio.sleep(provider.rate_limit_delay)

                bars = await provider.fetch_bars(
                    request.symbol,
                    request.start_date,
                    request.end_date,
                    request.timeframe
                )

                if bars:
                    if source != DataSource.DATABASE:
                        await self._store_to_database(bars, request.symbol)

                    event_bus.emit(Event(
                        type=EventType.MARKET_DATA_FETCHED,
                        timestamp=datetime.utcnow(),
                        data={
                            "symbol": request.symbol,
                            "source": source.value,
                            "bars_count": len(bars),
                            "timeframe": request.timeframe.value
                        },
                        source="history_manager"
                    ))

                    logger.info(f"Fetched {len(bars)} bars from {source.value}")
                    return bars, source.value

            except Exception as e:
                logger.error(f"Error with {source.value} provider: {e}")
                continue

        logger.warning(f"No data available for {request.symbol}")
        return [], "none"

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
        return [source.value for source in self.providers.keys()]

    async def start_realtime_stream(
        self,
        symbols: list[str],
        enable_indicators: bool = True
    ) -> bool:
        """Start real-time market data streaming."""
        try:
            logger.warning(f"📡 STOCK STREAM: start_realtime_stream called for {symbols}")
            logger.warning(f"📡 Available providers: {list(self.providers.keys())}")
            logger.info(f"Starting real-time stream for {len(symbols)} symbols. Available providers: {list(self.providers.keys())}")

            # Priority 1: Try Alpaca WebSocket
            if DataSource.ALPACA in self.providers:
                logger.info("Attempting to use Alpaca WebSocket for streaming...")
                alpaca_provider = self.providers[DataSource.ALPACA]
                if isinstance(alpaca_provider, AlpacaProvider):
                    try:
                        from src.core.market_data.alpaca_stream import AlpacaStreamClient

                        if not self.stream_client or not isinstance(self.stream_client, AlpacaStreamClient):
                            self.stream_client = AlpacaStreamClient(
                                api_key=alpaca_provider.api_key,
                                api_secret=alpaca_provider.api_secret,
                                paper=True,
                                feed="iex"
                            )

                        connected = await self.stream_client.connect()
                        if connected:
                            await self.stream_client.subscribe(symbols)
                            logger.info(f"Started Alpaca real-time WebSocket stream for {len(symbols)} symbols")
                            return True
                        else:
                            logger.warning("Failed to connect Alpaca stream, trying fallback...")
                    except Exception as e:
                        logger.warning(f"Alpaca streaming failed: {e}, trying fallback...")

            # Priority 2: Fallback to Alpha Vantage polling
            logger.info("Falling back to Alpha Vantage polling (60s intervals)")
            if DataSource.ALPHA_VANTAGE in self.providers:
                av_provider = self.providers[DataSource.ALPHA_VANTAGE]
                if isinstance(av_provider, AlphaVantageProvider):
                    from src.core.market_data.alpha_vantage_stream import AlphaVantageStreamClient

                    if not self.stream_client:
                        self.stream_client = AlphaVantageStreamClient(
                            api_key=av_provider.api_key,
                            enable_indicators=enable_indicators
                        )

                    connected = await self.stream_client.connect()
                    if connected:
                        await self.stream_client.subscribe(symbols)
                        logger.info(f"Started Alpha Vantage polling stream for {len(symbols)} symbols (60s interval)")
                        return True

            logger.error("No streaming provider available (need Alpaca or Alpha Vantage)")
            return False

        except Exception as e:
            logger.error(f"Error starting real-time stream: {e}")
            return False

    async def stop_realtime_stream(self):
        """Stop real-time market data streaming."""
        if self.stream_client:
            await self.stream_client.disconnect()
            logger.info("Stopped real-time stream")

    async def start_crypto_realtime_stream(
        self,
        crypto_symbols: list[str]
    ) -> bool:
        """Start real-time cryptocurrency market data streaming."""
        try:
            print(f"📡 CRYPTO STREAM: start_crypto_realtime_stream called for {crypto_symbols}")
            print(f"📡 Available providers: {list(self.providers.keys())}")
            logger.info(f"Starting crypto real-time stream for {len(crypto_symbols)} symbols")

            if DataSource.ALPACA_CRYPTO in self.providers:
                from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
                from src.core.market_data.alpaca_crypto_stream import AlpacaCryptoStreamClient

                crypto_provider = self.providers[DataSource.ALPACA_CRYPTO]
                if isinstance(crypto_provider, AlpacaCryptoProvider):
                    try:
                        # Reuse existing client if available
                        if not hasattr(self, 'crypto_stream_client') or self.crypto_stream_client is None:
                            print("📡 Creating NEW crypto stream client")
                            self.crypto_stream_client = AlpacaCryptoStreamClient(
                                api_key=crypto_provider.api_key,
                                api_secret=crypto_provider.api_secret,
                                paper=True
                            )
                        else:
                            print("📡 Reusing EXISTING crypto stream client")

                        if not self.crypto_stream_client.connected:
                            print("📡 Connecting crypto stream...")
                            connected = await self.crypto_stream_client.connect()
                        else:
                            print("📡 Already connected")
                            connected = True

                        if connected:
                            print(f"📡 Subscribing to {crypto_symbols}...")
                            await self.crypto_stream_client.subscribe(crypto_symbols)
                            logger.info(
                                f"Started Alpaca crypto WebSocket stream "
                                f"for {len(crypto_symbols)} symbols"
                            )
                            return True
                        else:
                            logger.warning("Failed to connect Alpaca crypto stream")
                    except Exception as e:
                        logger.error(f"Alpaca crypto streaming failed: {e}")

            logger.error("No crypto streaming provider available (need Alpaca Crypto)")
            return False

        except Exception as e:
            logger.error(f"Error starting crypto real-time stream: {e}")
            return False

    async def stop_crypto_realtime_stream(self):
        """Stop real-time cryptocurrency market data streaming."""
        if hasattr(self, 'crypto_stream_client') and self.crypto_stream_client:
            await self.crypto_stream_client.disconnect()
            logger.info("Stopped crypto real-time stream")

    def get_realtime_tick(self, symbol: str):
        """Get latest real-time tick for a symbol."""
        if self.stream_client:
            return self.stream_client.get_latest_tick(symbol)
        return None

    def get_stream_metrics(self) -> dict | None:
        """Get real-time stream metrics."""
        if self.stream_client:
            return self.stream_client.get_metrics()
        return None

    async def fetch_realtime_indicators(
        self,
        symbol: str,
        interval: str = "1min"
    ) -> dict:
        """Fetch real-time technical indicators."""
        if DataSource.ALPHA_VANTAGE not in self.providers:
            return {}

        av_provider = self.providers[DataSource.ALPHA_VANTAGE]
        if not isinstance(av_provider, AlphaVantageProvider):
            return {}

        try:
            rsi_task = av_provider.fetch_rsi(symbol, interval)
            macd_task = av_provider.fetch_macd(symbol, interval)

            rsi_data, macd_data = await asyncio.gather(rsi_task, macd_task)

            result = {}

            if not rsi_data.empty:
                result["rsi"] = {
                    "value": float(rsi_data.iloc[-1]),
                    "timestamp": rsi_data.index[-1].isoformat(),
                    "series": rsi_data.tail(50).to_dict()
                }

            if not macd_data.empty:
                latest_macd = macd_data.iloc[-1]
                result["macd"] = {
                    "macd": float(latest_macd["macd"]),
                    "signal": float(latest_macd["signal"]),
                    "histogram": float(latest_macd["histogram"]),
                    "timestamp": macd_data.index[-1].isoformat(),
                    "series": macd_data.tail(50).to_dict("index")
                }

            return result

        except Exception as e:
            logger.error(f"Error fetching realtime indicators: {e}")
            return {}
