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

# Hard cap for spike filtering (matches historical/context filters)
OUTLIER_PCT = 0.03  # 3% vs letzter Close


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
        self._last_close: dict[str, float] = {}

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
            # IMPORTANT: Crypto streams use the LIVE URL for both paper and live trading
            # The Sandbox URL does not support crypto streaming (auth fails)
            # Alpaca crypto market data is the same for paper and live accounts
            logger.info("Using Live Crypto Stream (same for paper and live trading)")

            # Create crypto stream client (no url_override = uses default live URL)
            self._stream = CryptoDataStream(
                api_key=self.api_key,
                secret_key=self.api_secret
            )

            # Set up handlers for subscribed symbols
            print(f"🔍 DEBUG: subscribed_symbols at connect = {self.metrics.subscribed_symbols}")
            if self.metrics.subscribed_symbols:
                symbols_list = list(self.metrics.subscribed_symbols)
                print(f"🔍 DEBUG: Subscribing to {symbols_list} during connect")
                self._stream.subscribe_bars(
                    self._on_bar,
                    *symbols_list
                )
                self._stream.subscribe_trades(
                    self._on_trade,
                    *symbols_list
                )
                self._stream.subscribe_quotes(
                    self._on_quote,
                    *symbols_list
                )
            else:
                print("⚠️ DEBUG: No symbols to subscribe during connect!")

            # Start stream in background
            asyncio.create_task(self._run_stream())

            self.connected = True
            self.metrics.status = StreamStatus.CONNECTED
            self.metrics.connected_at = datetime.utcnow()

            print("✅ CRYPTO STREAM CONNECTED!")
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
            # Set connected=False FIRST to stop the _run_stream loop
            self.connected = False
            self.metrics.status = StreamStatus.DISCONNECTED
            self.metrics.subscribed_symbols.clear()

            if self._stream:
                # Run in thread to avoid blocking - stop_ws may be synchronous
                await asyncio.to_thread(self._stop_stream_sync)

            print("🔴 CRYPTO STREAM DISCONNECTED!")
            logger.info("Alpaca crypto stream disconnected")

            # Emit disconnection event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_DISCONNECTED,
                timestamp=datetime.utcnow(),
                data={"source": self.name}
            ))

        except Exception as e:
            logger.error(f"Error disconnecting crypto stream: {e}")

    def _stop_stream_sync(self):
        """Synchronous stream stop (runs in thread)."""
        if self._stream:
            # CryptoDataStream.stop_ws() is synchronous
            self._stream.stop_ws()
            self._stream = None

    async def subscribe(self, symbols: list[str]):
        """Subscribe to crypto symbols.

        Args:
            symbols: List of crypto trading pairs (e.g., ["BTC/USD", "ETH/USD"])
        """
        print(f"🔔 SUBSCRIBE called with symbols: {symbols}")
        print(f"🔔 connected={self.connected}, _stream={self._stream is not None}")

        # Add to subscribed set
        for symbol in symbols:
            if symbol not in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.add(symbol)

        # Subscribe to stream if connected
        if self.connected and self._stream:
            print(f"🔔 Subscribing to bars/trades/quotes for: {symbols}")
            self._stream.subscribe_bars(self._on_bar, *symbols)
            self._stream.subscribe_trades(self._on_trade, *symbols)
            self._stream.subscribe_quotes(self._on_quote, *symbols)
            print(f"✅ Subscription complete for: {symbols}")

            logger.info(f"Subscribed to {len(symbols)} crypto symbols: {', '.join(symbols)}")
        else:
            print(f"⚠️ Cannot subscribe - not connected or no stream!")

    async def unsubscribe(self, symbols: list[str]):
        """Unsubscribe from crypto symbols.

        Args:
            symbols: List of crypto trading pairs to unsubscribe from
        """
        for symbol in symbols:
            if symbol in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.remove(symbol)

        # Unsubscribe from stream if connected - run in thread to avoid blocking
        if self.connected and self._stream:
            await asyncio.to_thread(self._unsubscribe_sync, symbols)
            logger.info(f"Unsubscribed from {len(symbols)} crypto symbols")

    def _unsubscribe_sync(self, symbols: list[str]):
        """Synchronous unsubscribe (runs in thread)."""
        self._stream.unsubscribe_bars(*symbols)
        self._stream.unsubscribe_trades(*symbols)
        self._stream.unsubscribe_quotes(*symbols)

    async def _on_bar(self, bar: Bar):
        """Handle crypto bar (OHLCV) data.

        Args:
            bar: Alpaca crypto bar object
        """
        try:
            # Print to console for debugging
            print(f"📊 CRYPTO BAR: {bar.symbol} | Close: ${float(bar.close):.2f} | O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close} | Vol: {bar.volume}")
            logger.info(
                f"📊 Received crypto bar: {bar.symbol} "
                f"OHLC: {bar.open}/{bar.high}/{bar.low}/{bar.close} "
                f"Vol: {bar.volume}"
            )
            request_time = datetime.now(timezone.utc)

            last_close = self._last_close.get(bar.symbol)
            if self._is_outlier_bar(bar, last_close):
                logger.warning(
                    "⏭️  Dropping outlier CRYPTO bar "
                    f"{bar.symbol} O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close} "
                    f"(prev_close={last_close})"
                )
                self.metrics.messages_dropped += 1
                return

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
            self._last_close[bar.symbol] = float(bar.close)
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
            # Print to console for debugging
            print(f"💰 CRYPTO TRADE: {trade.symbol} | Price: ${float(trade.price):.2f} | Size: {trade.size}")
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
                    "timestamp": trade.timestamp,  # Include timestamp in data for consistency
                    "exchange": trade.exchange if hasattr(trade, 'exchange') else None,
                    "source": self.name,
                    "type": "trade"  # Mark as trade update
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
            # Calculate mid-price from bid/ask
            mid_price = (quote.bid_price + quote.ask_price) / 2

            logger.debug(
                f"💬 Received crypto quote: {quote.symbol} "
                f"Bid: ${quote.bid_price} Ask: ${quote.ask_price} Mid: ${mid_price:.2f}"
            )

            # Create tick with bid/ask
            tick = MarketTick(
                symbol=quote.symbol,
                bid=Decimal(str(quote.bid_price)),
                ask=Decimal(str(quote.ask_price)),
                last=Decimal(str(mid_price)),  # Use mid-price as "last" for chart updates
                timestamp=quote.timestamp,
                source=self.name
            )

            # Update cache
            self.symbol_cache[quote.symbol] = tick

            # Emit quote event as tick for real-time chart updates
            # This provides much higher frequency updates than trades alone
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_TICK,
                timestamp=quote.timestamp,
                data={
                    "symbol": quote.symbol,
                    "asset_class": "crypto",
                    "price": float(mid_price),  # Mid-price
                    "bid": float(quote.bid_price),
                    "ask": float(quote.ask_price),
                    "spread": float(quote.ask_price - quote.bid_price),
                    "source": self.name,
                    "type": "quote"  # Mark as quote update
                }
            ))

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

    @staticmethod
    def _is_outlier_bar(bar: Bar, prev_close: float | None) -> bool:
        """Return True if bar looks implausible compared to previous close."""
        try:
            high = float(bar.high)
            low = float(bar.low)
            close = float(bar.close)
        except Exception:
            return False

        if low > high:
            return True

        if prev_close is None or prev_close == 0:
            return False

        def deviates(val: float) -> bool:
            return abs(val - prev_close) / prev_close > OUTLIER_PCT

        return deviates(high) or deviates(low) or deviates(close)

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
