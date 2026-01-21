"""History Provider Streaming - Real-time streaming for stocks, crypto, Bitunix.

Refactored from 700 LOC monolith using composition pattern.

Module 3/3 of history_provider.py split.

Contains:
- start_realtime_stream(): Start stock stream (Alpaca/AlphaVantage)
- stop_realtime_stream(): Stop stock stream
- start_crypto_realtime_stream(): Start crypto stream (Alpaca Crypto)
- stop_crypto_realtime_stream(): Stop crypto stream
- start_bitunix_stream(): Start Bitunix stream
- stop_bitunix_stream(): Stop Bitunix stream
- get_realtime_tick(): Get latest tick
- get_stream_metrics(): Get stream metrics
- fetch_realtime_indicators(): Fetch realtime indicators
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from src.core.market_data.types import DataSource

from src.core.market_data.providers import AlpacaProvider, AlphaVantageProvider

if TYPE_CHECKING:
    from decimal import Decimal

logger = logging.getLogger(__name__)


class HistoryProviderStreaming:
    """Helper für HistoryManager Streaming (Stock, Crypto, Bitunix)."""

    def __init__(self, parent):
        """
        Args:
            parent: HistoryManager Instanz
        """
        self.parent = parent

    async def start_realtime_stream(
        self,
        symbols: list[str],
        enable_indicators: bool = True
    ) -> bool:
        """Start real-time market data streaming.

        Uses asyncio.Lock to prevent race conditions when multiple charts
        or broker connections attempt to start the stream simultaneously.
        """
        async with self.parent._stock_stream_lock:
            logger.warning(f"📡 STOCK STREAM: start_realtime_stream called for {symbols}")
            logger.warning(f"📡 Available providers: {list(self.parent.providers.keys())}")
            logger.info(f"Starting real-time stream for {len(symbols)} symbols. Available providers: {list(self.parent.providers.keys())}")

            try:
                # Priority 1: Try Alpaca WebSocket
                if DataSource.ALPACA in self.parent.providers:
                    logger.info("Attempting to use Alpaca WebSocket for streaming...")
                    alpaca_provider = self.parent.providers[DataSource.ALPACA]
                    if isinstance(alpaca_provider, AlpacaProvider):
                        try:
                            from src.core.market_data.alpaca_stream import AlpacaStreamClient

                            # Force disconnect any existing client to avoid connection limit
                            if self.parent.stream_client:
                                logger.info("📡 Force disconnecting existing stock stream client...")
                                try:
                                    await self.parent.stream_client.disconnect()
                                    await asyncio.sleep(2)  # Give Alpaca time to release connection
                                except Exception as e:
                                    logger.warning(f"Error during force disconnect: {e}")

                            # Always create NEW client to avoid stale state
                            logger.info("📡 Creating NEW stock stream client")
                            self.parent.stream_client = AlpacaStreamClient(
                                api_key=alpaca_provider.api_key,
                                api_secret=alpaca_provider.api_secret,
                                paper=True,
                                feed="iex"
                            )

                            connected = await self.parent.stream_client.connect()
                            if connected:
                                await self.parent.stream_client.subscribe(symbols)
                                logger.info(f"Started Alpaca real-time WebSocket stream for {len(symbols)} symbols")
                                return True
                            else:
                                logger.warning("Failed to connect Alpaca stream, trying fallback...")
                        except Exception as e:
                            logger.warning(f"Alpaca streaming failed: {e}, trying fallback...")

                # Priority 2: Fallback to Alpha Vantage polling
                logger.info("Falling back to Alpha Vantage polling (60s intervals)")
                if DataSource.ALPHA_VANTAGE in self.parent.providers:
                    av_provider = self.parent.providers[DataSource.ALPHA_VANTAGE]
                    if isinstance(av_provider, AlphaVantageProvider):
                        from src.core.market_data.alpha_vantage_stream import AlphaVantageStreamClient

                        if not self.parent.stream_client:
                            self.parent.stream_client = AlphaVantageStreamClient(
                                api_key=av_provider.api_key,
                                enable_indicators=enable_indicators
                            )

                        connected = await self.parent.stream_client.connect()
                        if connected:
                            await self.parent.stream_client.subscribe(symbols)
                            logger.info(f"Started Alpha Vantage polling stream for {len(symbols)} symbols (60s interval)")
                            return True

                logger.error("No streaming provider available (need Alpaca or Alpha Vantage)")
                return False

            except Exception as e:
                logger.error(f"Error starting real-time stream: {e}")
                return False

    async def stop_realtime_stream(self):
        """Stop real-time market data streaming."""
        if self.parent.stream_client:
            await self.parent.stream_client.disconnect()
            logger.info("Stopped real-time stream")

    async def start_crypto_realtime_stream(
        self,
        crypto_symbols: list[str]
    ) -> bool:
        """Start real-time cryptocurrency market data streaming.

        Uses asyncio.Lock to prevent race conditions when multiple charts
        or broker connections attempt to start the stream simultaneously.
        """
        async with self.parent._crypto_stream_lock:
            print(f"📡 CRYPTO STREAM: start_crypto_realtime_stream called for {crypto_symbols}")
            print(f"📡 Available providers: {list(self.parent.providers.keys())}")
            logger.info(f"Starting crypto real-time stream for {len(crypto_symbols)} symbols")

            try:
                if DataSource.ALPACA_CRYPTO in self.parent.providers:
                    from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
                    from src.core.market_data.alpaca_crypto_stream import AlpacaCryptoStreamClient

                    crypto_provider = self.parent.providers[DataSource.ALPACA_CRYPTO]
                    if isinstance(crypto_provider, AlpacaCryptoProvider):
                        try:
                            # Reuse existing client if available (avoid connection limit)
                            if not hasattr(self.parent, 'crypto_stream_client') or self.parent.crypto_stream_client is None:
                                print("📡 Creating NEW crypto stream client")
                                self.parent.crypto_stream_client = AlpacaCryptoStreamClient(
                                    api_key=crypto_provider.api_key,
                                    api_secret=crypto_provider.api_secret,
                                    paper=True
                                )
                            else:
                                print("📡 Reusing EXISTING crypto stream client")

                            # Only connect if not already connected
                            if not self.parent.crypto_stream_client.connected:
                                print("📡 Connecting crypto stream...")
                                connected = await self.parent.crypto_stream_client.connect()
                            else:
                                print("📡 Already connected")
                                connected = True

                            if connected:
                                print(f"📡 Subscribing to {crypto_symbols}...")
                                await self.parent.crypto_stream_client.subscribe(crypto_symbols)
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
        if hasattr(self.parent, 'crypto_stream_client') and self.parent.crypto_stream_client:
            await self.parent.crypto_stream_client.disconnect()
            logger.info("Stopped crypto real-time stream")

    async def start_bitunix_stream(
        self,
        bitunix_symbols: list[str]
    ) -> bool:
        """Start real-time Bitunix WebSocket streaming for crypto futures.

        Args:
            bitunix_symbols: List of Bitunix symbols (e.g., ['BTCUSDT', 'ETHUSDT'])

        Returns:
            True if stream started successfully, False otherwise
        """
        # Create lock if it doesn't exist
        if not hasattr(self.parent, '_bitunix_stream_lock'):
            self.parent._bitunix_stream_lock = asyncio.Lock()

        async with self.parent._bitunix_stream_lock:
            logger.warning(f"📡 BITUNIX STREAM: start_bitunix_stream called for {bitunix_symbols}")
            logger.warning(f"📡 Available providers: {list(self.parent.providers.keys())}")

            try:
                if DataSource.BITUNIX in self.parent.providers:
                    from src.core.market_data.bitunix_stream import BitunixStreamClient

                    try:
                        # Reuse existing client if available
                        if not hasattr(self.parent, 'bitunix_stream_client') or self.parent.bitunix_stream_client is None:
                            logger.warning("📡 Creating NEW Bitunix stream client")
                            self.parent.bitunix_stream_client = BitunixStreamClient(
                                use_testnet=False,  # Use production WebSocket
                                buffer_size=10000
                            )
                        else:
                            logger.warning("📡 Reusing EXISTING Bitunix stream client")

                        # Only connect if not already connected
                        if not self.parent.bitunix_stream_client.connected:
                            logger.warning("📡 Connecting Bitunix stream...")
                            connected = await self.parent.bitunix_stream_client.connect()
                        else:
                            logger.warning("📡 Already connected to Bitunix")
                            connected = True

                        if connected:
                            logger.warning(f"📡 Subscribing to {bitunix_symbols}...")
                            await self.parent.bitunix_stream_client.subscribe(bitunix_symbols)
                            logger.info(
                                f"✅ Started Bitunix WebSocket stream "
                                f"for {len(bitunix_symbols)} symbols"
                            )
                            return True
                        else:
                            logger.error("❌ Failed to connect Bitunix stream")
                    except Exception as e:
                        logger.error(f"❌ Bitunix streaming failed: {e}", exc_info=True)

                logger.error("❌ No Bitunix streaming provider available")
                return False

            except Exception as e:
                logger.error(f"❌ Error starting Bitunix real-time stream: {e}", exc_info=True)
                return False

    async def stop_bitunix_stream(self):
        """Stop real-time Bitunix WebSocket streaming."""
        if hasattr(self.parent, 'bitunix_stream_client') and self.parent.bitunix_stream_client:
            await self.parent.bitunix_stream_client.disconnect()
            logger.info("Stopped Bitunix real-time stream")

    def get_realtime_tick(self, symbol: str):
        """Get latest real-time tick for a symbol."""
        if self.parent.stream_client:
            return self.parent.stream_client.get_latest_tick(symbol)
        return None

    def get_stream_metrics(self) -> dict | None:
        """Get real-time stream metrics."""
        if self.parent.stream_client:
            return self.parent.stream_client.get_metrics()
        return None

    async def fetch_realtime_indicators(
        self,
        symbol: str,
        interval: str = "1min"
    ) -> dict:
        """Fetch real-time technical indicators."""
        if DataSource.ALPHA_VANTAGE not in self.parent.providers:
            return {}

        av_provider = self.parent.providers[DataSource.ALPHA_VANTAGE]
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
