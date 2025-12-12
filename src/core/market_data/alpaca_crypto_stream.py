"""Alpaca Real-Time Cryptocurrency Market Data Stream Client.

Provides real-time crypto market data via WebSocket using Alpaca's Crypto Data Stream.
Endpoint: wss://stream.data.alpaca.markets/v1beta3/crypto/us
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from alpaca.data.live import CryptoDataStream
from alpaca.data.models import Bar, Quote, Trade

from src.common.event_bus import Event, EventType, event_bus
from src.core.market_data.stream_client import MarketTick, StreamClient, StreamStatus

logger = logging.getLogger(__name__)


class AlpacaCryptoStreamClient(StreamClient):
    """Real-time cryptocurrency market data client for Alpaca using WebSocket.

    Supports streaming of:
    - Crypto bars (OHLCV candlesticks)
    - Crypto trades (individual transactions)
    - Crypto quotes (bid/ask prices)
    - Crypto orderbooks (market depth)

    Supported trading pairs: BTC/USD, ETH/USD, ETH/BTC, SOL/USDT, etc.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        paper: bool = True,
        buffer_size: int = 10000
    ):
        """Initialize Alpaca crypto stream client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Use paper trading (default: True)
            buffer_size: Size of the data buffer
        """
        super().__init__(
            name="AlpacaCryptoStream",
            buffer_size=buffer_size,
            heartbeat_interval=30,
            reconnect_attempts=5,
            max_lag_ms=5000  # 5 seconds max acceptable lag
        )

        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper

        # Alpaca crypto stream client
        self._stream: CryptoDataStream | None = None

        logger.info(f"Alpaca crypto stream client initialized (paper={paper})")

    async def connect(self) -> bool:
        """Connect to Alpaca Crypto WebSocket stream.

        Returns:
            True if connection successful
        """
        if self.connected:
            logger.warning("Already connected")
            return True

        try:
            # Determine URL based on paper mode
            url_override = None
            if self.paper:
                # Use Sandbox URL for paper trading
                url_override = "wss://stream.data.sandbox.alpaca.markets/v1beta3/crypto/us"
                logger.info(f"Using Sandbox Crypto Stream: {url_override}")

            # Create crypto stream client
            self._stream = CryptoDataStream(
                api_key=self.api_key,
                secret_key=self.api_secret,
                url_override=url_override
            )

            # Set up handlers for subscribed symbols
            if self.metrics.subscribed_symbols:
                self._stream.subscribe_bars(
                    self._on_bar,
                    *list(self.metrics.subscribed_symbols)
                )
                self._stream.subscribe_trades(
                    self._on_trade,
                    *list(self.metrics.subscribed_symbols)
                )
                self._stream.subscribe_quotes(
                    self._on_quote,
                    *list(self.metrics.subscribed_symbols)
                )

            # Start stream in background
            asyncio.create_task(self._run_stream())

            self.connected = True
            self.metrics.status = StreamStatus.CONNECTED
            self.metrics.connected_at = datetime.utcnow()

            logger.info("Alpaca crypto stream connected")

            # Emit connection event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_CONNECTED,
                timestamp=datetime.utcnow(),
                data={"source": self.name, "asset_class": "crypto"}
            ))

            return True

        except Exception as e:
            logger.error(f"Failed to connect crypto stream: {e}")
            self.metrics.status = StreamStatus.ERROR
            return False

    async def _run_stream(self):
        """Run the Alpaca crypto stream with automatic reconnection."""
        while self.connected:
            try:
                if self._stream:
                    logger.info("Starting Alpaca crypto stream listener...")
                    await self._stream._run_forever()

                # If run_forever returns, it means the connection closed
                if self.connected:
                    logger.warning("Alpaca crypto stream connection closed unexpectedly. Reconnecting in 5s...")
                    await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Alpaca crypto stream error: {e}")
                self.metrics.status = StreamStatus.ERROR

                if self.connected:
                    logger.info("Attempting to reconnect in 5s...")
                    await asyncio.sleep(5)

    async def disconnect(self):
        """Disconnect from Alpaca crypto stream."""
        if not self.connected:
            return

        try:
            if self._stream:
                await self._stream.stop_ws()

            self.connected = False
            self.metrics.status = StreamStatus.DISCONNECTED

            logger.info("Alpaca crypto stream disconnected")

            # Emit disconnection event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_DISCONNECTED,
                timestamp=datetime.utcnow(),
                data={"source": self.name}
            ))

        except Exception as e:
            logger.error(f"Error disconnecting crypto stream: {e}")

    async def subscribe(self, symbols: list[str]):
        """Subscribe to crypto symbols.

        Args:
            symbols: List of crypto trading pairs (e.g., ["BTC/USD", "ETH/USD"])
        """
        # Add to subscribed set
        for symbol in symbols:
            if symbol not in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.add(symbol)

        # Subscribe to stream if connected
        if self.connected and self._stream:
            self._stream.subscribe_bars(self._on_bar, *symbols)
            self._stream.subscribe_trades(self._on_trade, *symbols)
            self._stream.subscribe_quotes(self._on_quote, *symbols)

            logger.info(f"Subscribed to {len(symbols)} crypto symbols: {', '.join(symbols)}")

    async def unsubscribe(self, symbols: list[str]):
        """Unsubscribe from crypto symbols.

        Args:
            symbols: List of crypto trading pairs to unsubscribe from
        """
        for symbol in symbols:
            if symbol in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.remove(symbol)

        # Unsubscribe from stream if connected
        if self.connected and self._stream:
            self._stream.unsubscribe_bars(*symbols)
            self._stream.unsubscribe_trades(*symbols)
            self._stream.unsubscribe_quotes(*symbols)

            logger.info(f"Unsubscribed from {len(symbols)} crypto symbols")

    async def _on_bar(self, bar: Bar):
        """Handle crypto bar (OHLCV) data.

        Args:
            bar: Alpaca crypto bar object
        """
        try:
            logger.info(
                f"📊 Received crypto bar: {bar.symbol} "
                f"OHLC: {bar.open}/{bar.high}/{bar.low}/{bar.close} "
                f"Vol: {bar.volume}"
            )
            request_time = datetime.now(timezone.utc)

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

            # Emit bar event
            event_bus.emit(Event(
                type=EventType.MARKET_BAR,
                timestamp=bar.timestamp,
                data={
                    "symbol": bar.symbol,
                    "asset_class": "crypto",
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": bar.volume,
                    "vwap": float(bar.vwap) if bar.vwap else None,
                    "trade_count": bar.trade_count if hasattr(bar, 'trade_count') else None,
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
                    "asset_class": "crypto",
                    "price": float(bar.close),
                    "volume": bar.volume,
                    "source": self.name
                }
            ))

        except Exception as e:
            logger.error(f"Error handling crypto bar: {e}")
            self.metrics.messages_dropped += 1

    async def _on_trade(self, trade: Trade):
        """Handle crypto trade data.

        Args:
            trade: Alpaca crypto trade object
        """
        try:
            logger.info(
                f"🔔 Received crypto trade: {trade.symbol} "
                f"@ ${trade.price} (size: {trade.size})"
            )

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
                    "asset_class": "crypto",
                    "price": float(trade.price),
                    "size": trade.size,
                    "exchange": trade.exchange if hasattr(trade, 'exchange') else None,
                    "source": self.name
                }
            ))

        except Exception as e:
            logger.error(f"Error handling crypto trade: {e}")

    async def _on_quote(self, quote: Quote):
        """Handle crypto quote (bid/ask) data.

        Args:
            quote: Alpaca crypto quote object
        """
        try:
            logger.debug(
                f"💬 Received crypto quote: {quote.symbol} "
                f"Bid: ${quote.bid_price} Ask: ${quote.ask_price}"
            )

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
            logger.error(f"Error handling crypto quote: {e}")

    def get_latest_tick(self, symbol: str) -> MarketTick | None:
        """Get the latest tick for a crypto symbol.

        Args:
            symbol: Crypto trading pair (e.g., "BTC/USD")

        Returns:
            Latest MarketTick or None
        """
        return self.symbol_cache.get(symbol)

    def get_metrics(self) -> dict:
        """Get crypto stream metrics.

        Returns:
            Dictionary with metrics
        """
        return {
            "status": self.metrics.status.value,
            "asset_class": "crypto",
            "connected_at": self.metrics.connected_at.isoformat() if self.metrics.connected_at else None,
            "last_message_at": self.metrics.last_message_at.isoformat() if self.metrics.last_message_at else None,
            "messages_received": self.metrics.messages_received,
            "messages_dropped": self.metrics.messages_dropped,
            "average_latency_ms": self.metrics.average_latency_ms,
            "subscribed_symbols": list(self.metrics.subscribed_symbols)
        }
