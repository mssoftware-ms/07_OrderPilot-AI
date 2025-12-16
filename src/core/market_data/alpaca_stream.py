"""Alpaca Real-Time Market Data Stream Client.

Provides real-time market data via WebSocket using Alpaca's IEX feed.
Free tier includes: 30 concurrent symbols, 200 REST calls/min, real-time bars.
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from alpaca.data.live import StockDataStream
from alpaca.data.models import Bar, Quote, Trade
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrame

from src.common.event_bus import Event, EventType, event_bus
from src.core.market_data.stream_client import MarketTick, StreamClient, StreamStatus

logger = logging.getLogger(__name__)


class AlpacaStreamClient(StreamClient):
    """Real-time market data client for Alpaca using WebSocket."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        paper: bool = True,
        buffer_size: int = 10000,
        feed: str = "iex"  # iex (free) or sip (premium)
    ):
        """Initialize Alpaca stream client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Use paper trading (default: True)
            buffer_size: Size of the data buffer
            feed: Data feed type - 'iex' (free, 30 symbols) or 'sip' (premium)
        """
        super().__init__(
            name="AlpacaStream",
            buffer_size=buffer_size,
            heartbeat_interval=30,
            reconnect_attempts=5,
            max_lag_ms=5000  # 5 seconds max acceptable lag
        )

        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper
        self.feed = feed

        # Alpaca stream client
        self._stream: StockDataStream | None = None
        self._historical_client: StockHistoricalDataClient | None = None

        # Connection limits
        self.max_symbols = 30 if feed == "iex" else 10000  # IEX free tier limit

        logger.info(
            f"Alpaca stream client initialized "
            f"(feed: {feed}, paper: {paper}, max symbols: {self.max_symbols})"
        )

    async def connect(self) -> bool:
        """Connect to Alpaca WebSocket stream.

        Returns:
            True if connection successful
        """
        if self.connected:
            logger.warning("Already connected")
            return True

        try:
            # Convert feed string to DataFeed enum
            from alpaca.data.enums import DataFeed

            feed_map = {
                "iex": DataFeed.IEX,
                "sip": DataFeed.SIP,
                "otc": DataFeed.OTC
            }
            feed_enum = feed_map.get(self.feed.lower(), DataFeed.IEX)

            # Create stream client
            self._stream = StockDataStream(
                api_key=self.api_key,
                secret_key=self.api_secret,
                feed=feed_enum
            )

            # Create historical data client
            self._historical_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.api_secret
            )

            # Set up handlers
            self._stream.subscribe_bars(self._on_bar, *list(self.metrics.subscribed_symbols))
            self._stream.subscribe_trades(self._on_trade, *list(self.metrics.subscribed_symbols))
            self._stream.subscribe_quotes(self._on_quote, *list(self.metrics.subscribed_symbols))

            # Start stream in background
            asyncio.create_task(self._run_stream())

            self.connected = True
            self.metrics.status = StreamStatus.CONNECTED
            self.metrics.connected_at = datetime.utcnow()

            print("✅ STOCK STREAM CONNECTED!")
            logger.info("Alpaca stream connected")

            # Emit connection event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_CONNECTED,
                timestamp=datetime.utcnow(),
                data={"source": self.name, "feed": self.feed}
            ))

            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.metrics.status = StreamStatus.ERROR
            return False

    async def _run_stream(self):
        """Run the Alpaca stream with automatic reconnection."""
        while self.connected:
            try:
                if self._stream:
                    logger.info("Starting Alpaca stream listener...")
                    await self._stream._run_forever()

                # If run_forever returns, it means the connection closed
                if self.connected:
                    logger.warning("Alpaca stream connection closed unexpectedly. Reconnecting in 5s...")
                    await asyncio.sleep(5)

            except ValueError as e:
                error_msg = str(e)
                if "connection limit exceeded" in error_msg.lower():
                    print("\n" + "="*60)
                    print("⚠️  ALPACA CONNECTION LIMIT EXCEEDED!")
                    print("="*60)
                    print("Eine alte Verbindung ist noch auf Alpaca's Server aktiv.")
                    print("Das passiert wenn die App nicht sauber beendet wurde.")
                    print("\nLösung: Warte 1-2 Minuten und versuche es erneut.")
                    print("="*60 + "\n")
                    self.connected = False
                    self.metrics.status = StreamStatus.ERROR
                    # Emit error event for UI popup
                    event_bus.emit(Event(
                        type=EventType.MARKET_DATA_ERROR,
                        timestamp=datetime.utcnow(),
                        data={
                            "source": self.name,
                            "error": "connection_limit_exceeded",
                            "message": "Alpaca Verbindungslimit erreicht!\n\n"
                                       "Eine alte Verbindung ist noch auf Alpaca's Server aktiv.\n"
                                       "Das passiert wenn die App nicht sauber beendet wurde.\n\n"
                                       "Lösung: Warte 1-2 Minuten und versuche es erneut."
                        }
                    ))
                    return  # Don't retry - wait for user
                else:
                    raise

            except Exception as e:
                logger.error(f"Alpaca stream error: {e}")
                self.metrics.status = StreamStatus.ERROR

                if self.connected:
                    logger.info("Attempting to reconnect in 5s...")
                    await asyncio.sleep(5)

    async def disconnect(self):
        """Disconnect from Alpaca stream."""
        if not self.connected:
            return

        try:
            # Set connected=False FIRST to stop the _run_stream loop
            self.connected = False
            self.metrics.status = StreamStatus.DISCONNECTED
            self.metrics.subscribed_symbols.clear()

            if self._stream:
                # Run in thread to avoid blocking - stop_ws may be synchronous
                await asyncio.to_thread(self._stop_stream_sync)

            print("🔴 STOCK STREAM DISCONNECTED!")
            logger.info("Alpaca stream disconnected")

            # Emit disconnection event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_DISCONNECTED,
                timestamp=datetime.utcnow(),
                data={"source": self.name}
            ))

        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def _stop_stream_sync(self):
        """Synchronous stream stop (runs in thread)."""
        if self._stream:
            # StockDataStream.stop_ws() is synchronous
            self._stream.stop_ws()
            self._stream = None

    async def subscribe(self, symbols: list[str]):
        """Subscribe to symbols.

        Args:
            symbols: List of symbols to subscribe to
        """
        # Check symbol limit
        total_symbols = len(self.metrics.subscribed_symbols) + len(symbols)
        if total_symbols > self.max_symbols:
            logger.warning(
                f"Symbol limit exceeded: {total_symbols} > {self.max_symbols}. "
                f"Only subscribing to first {self.max_symbols} symbols."
            )
            symbols = symbols[:self.max_symbols - len(self.metrics.subscribed_symbols)]

        # Add to subscribed set
        for symbol in symbols:
            if symbol not in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.add(symbol)

        # Subscribe to stream if connected
        if self.connected and self._stream:
            self._stream.subscribe_bars(self._on_bar, *symbols)
            self._stream.subscribe_trades(self._on_trade, *symbols)
            self._stream.subscribe_quotes(self._on_quote, *symbols)

            logger.info(f"Subscribed to {len(symbols)} symbols: {', '.join(symbols)}")

    async def unsubscribe(self, symbols: list[str]):
        """Unsubscribe from symbols.

        Args:
            symbols: List of symbols to unsubscribe from
        """
        for symbol in symbols:
            if symbol in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.remove(symbol)

        # Unsubscribe from stream if connected - run in thread to avoid blocking
        if self.connected and self._stream:
            await asyncio.to_thread(self._unsubscribe_sync, symbols)
            logger.info(f"Unsubscribed from {len(symbols)} symbols")

    def _unsubscribe_sync(self, symbols: list[str]):
        """Synchronous unsubscribe (runs in thread)."""
        self._stream.unsubscribe_bars(*symbols)
        self._stream.unsubscribe_trades(*symbols)
        self._stream.unsubscribe_quotes(*symbols)

    async def _on_bar(self, bar: Bar):
        """Handle bar (OHLCV) data.

        Args:
            bar: Alpaca bar object
        """
        try:
            logger.info(f"📊 Received bar: {bar.symbol} OHLC: {bar.open}/{bar.high}/{bar.low}/{bar.close} Vol: {bar.volume}")
            request_time = datetime.now(timezone.utc)  # Use timezone-aware datetime

            # Convert to MarketTick
            tick = MarketTick(
                symbol=bar.symbol,
                last=Decimal(str(bar.close)),
                volume=bar.volume,
                timestamp=bar.timestamp,
                source=self.name,
                latency_ms=(request_time - bar.timestamp).total_seconds() * 1000
            )

            # Add to buffer
            self.buffer.append(tick)
            self.symbol_cache[bar.symbol] = tick
            self.metrics.messages_received += 1
            self.metrics.last_message_at = datetime.utcnow()
            self.metrics.update_latency(tick.latency_ms or 0)

            # Emit bar event (more detailed than tick)
            event_bus.emit(Event(
                type=EventType.MARKET_BAR,
                timestamp=bar.timestamp,
                data={
                    "symbol": bar.symbol,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": bar.volume,
                    "vwap": float(bar.vwap) if bar.vwap else None,
                    "trade_count": bar.trade_count,
                    "timestamp": bar.timestamp.isoformat(),
                    "source": self.name
                }
            ))

            # Also emit tick event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_TICK,
                timestamp=bar.timestamp,
                data={
                    "symbol": bar.symbol,
                    "price": float(bar.close),
                    "volume": bar.volume,
                    "source": self.name
                }
            ))

        except Exception as e:
            logger.error(f"Error handling bar: {e}")
            self.metrics.messages_dropped += 1

    async def _on_trade(self, trade: Trade):
        """Handle trade data.

        Args:
            trade: Alpaca trade object
        """
        try:
            logger.info(f"🔔 Received trade: {trade.symbol} @ ${trade.price} (size: {trade.size})")

            # Create tick from trade
            tick = MarketTick(
                symbol=trade.symbol,
                last=Decimal(str(trade.price)),
                volume=trade.size,
                timestamp=trade.timestamp,
                source=self.name
            )

            # Update cache
            self.symbol_cache[trade.symbol] = tick

            # Emit trade event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_TICK,
                timestamp=trade.timestamp,
                data={
                    "symbol": trade.symbol,
                    "price": float(trade.price),
                    "size": trade.size,
                    "exchange": trade.exchange if hasattr(trade, 'exchange') else None,
                    "conditions": trade.conditions if hasattr(trade, 'conditions') else None,
                    "source": self.name
                }
            ))

        except Exception as e:
            logger.error(f"Error handling trade: {e}")

    async def _on_quote(self, quote: Quote):
        """Handle quote (bid/ask) data.

        Args:
            quote: Alpaca quote object
        """
        try:
            logger.debug(f"💬 Received quote: {quote.symbol} Bid: ${quote.bid_price} Ask: ${quote.ask_price}")
            # Create tick with bid/ask
            tick = MarketTick(
                symbol=quote.symbol,
                bid=Decimal(str(quote.bid_price)),
                ask=Decimal(str(quote.ask_price)),
                timestamp=quote.timestamp,
                source=self.name
            )

            # Update cache
            self.symbol_cache[quote.symbol] = tick

        except Exception as e:
            logger.error(f"Error handling quote: {e}")

    def get_latest_tick(self, symbol: str) -> MarketTick | None:
        """Get the latest tick for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest MarketTick or None
        """
        return self.symbol_cache.get(symbol)

    async def get_latest_bar(self, symbol: str) -> dict | None:
        """Get the latest bar from Alpaca REST API.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with bar data or None
        """
        if not self._historical_client:
            return None

        try:
            request = StockLatestBarRequest(symbol_or_symbols=symbol)
            bars = self._historical_client.get_stock_latest_bar(request)

            if symbol in bars:
                bar = bars[symbol]
                return {
                    "symbol": symbol,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": bar.volume,
                    "vwap": float(bar.vwap) if bar.vwap else None,
                    "timestamp": bar.timestamp.isoformat()
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching latest bar: {e}")
            return None

    def get_metrics(self) -> dict:
        """Get stream metrics.

        Returns:
            Dictionary with metrics
        """
        return {
            "status": self.metrics.status.value,
            "connected_at": self.metrics.connected_at.isoformat() if self.metrics.connected_at else None,
            "last_message_at": self.metrics.last_message_at.isoformat() if self.metrics.last_message_at else None,
            "messages_received": self.metrics.messages_received,
            "messages_dropped": self.metrics.messages_dropped,
            "average_latency_ms": self.metrics.average_latency_ms,
            "subscribed_symbols": list(self.metrics.subscribed_symbols),
            "max_symbols": self.max_symbols,
            "feed": self.feed
        }
