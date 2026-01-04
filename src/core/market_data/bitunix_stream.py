"""Bitunix WebSocket Stream Client.

Real-time market data streaming for Bitunix Futures via WebSocket.
Supports ticker, kline, depth, and trade channels.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal

import websockets
from websockets.exceptions import ConnectionClosed

from src.common.event_bus import Event, EventType, event_bus
from src.core.market_data.stream_client import MarketTick, StreamClient, StreamStatus

logger = logging.getLogger(__name__)


class BitunixStreamClient(StreamClient):
    """Bitunix WebSocket stream client for real-time market data.

    Supports the following channels:
    - ticker: Real-time ticker updates
    - market_kline: Live candlestick data
    - depth_book: Order book updates
    - trade: Trade feed

    Authentication:
        Public channels do not require authentication.
        Private channels (orders, positions) require API key (not implemented here).

    Environments:
        - Futures public (recommended for both paper and live data): wss://fapi.bitunix.com/public/
        - Legacy testnet endpoint (unstable, not used by default): wss://testnet-stream.bitunix.com/public/
    """

    def __init__(
        self,
        use_testnet: bool = True,
        buffer_size: int = 10000,
        heartbeat_interval: int = 30,
        reconnect_attempts: int = 5,
        max_lag_ms: float = 1000
    ):
        """Initialize Bitunix stream client.

        Args:
            use_testnet: Use testnet WebSocket URL (default: True)
            buffer_size: Size of the data buffer
            heartbeat_interval: Heartbeat interval in seconds
            reconnect_attempts: Maximum reconnection attempts
            max_lag_ms: Maximum acceptable lag in milliseconds
        """
        super().__init__(
            name="Bitunix Stream",
            buffer_size=buffer_size,
            heartbeat_interval=heartbeat_interval,
            reconnect_attempts=reconnect_attempts,
            max_lag_ms=max_lag_ms
        )
        self.use_testnet = use_testnet
        self.ws_url = self._get_ws_url()
        self.ws = None
        self._stream_task = None
        self._reconnect_count = 0

    def _get_ws_url(self) -> str:
        """Get WebSocket URL based on environment.

        Returns:
            WebSocket URL
        """
        # Official futures WebSocket endpoint (matches SDK config files)
        # Using the fapi host for both environments avoids DNS failures seen on legacy testnet hosts.
        return "wss://fapi.bitunix.com/public/"

    async def connect(self) -> bool:
        """Connect to Bitunix WebSocket.

        Returns:
            True if connection successful
        """
        if self.connected:
            logger.warning("Already connected")
            return True

        try:
            self.metrics.status = StreamStatus.CONNECTING
            logger.info(f"Connecting to {self.ws_url}")

            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=self.heartbeat_interval,
                ping_timeout=self.heartbeat_interval * 2
            )

            self.connected = True
            self.metrics.status = StreamStatus.CONNECTED
            self.metrics.connected_at = datetime.utcnow()
            self._reconnect_count = 0

            # Start message handler
            self._stream_task = asyncio.create_task(self._run_stream())

            logger.info(f"✓ Connected to {self.ws_url}")
            return True

        except Exception as e:
            self.metrics.status = StreamStatus.ERROR
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Bitunix WebSocket."""
        self.connected = False
        self.metrics.status = StreamStatus.DISCONNECTED

        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
            self._stream_task = None

        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None

        await super().disconnect()
        logger.info("Disconnected from Bitunix WebSocket")

    async def _handle_subscription(self, symbols: list[str]) -> None:
        """Handle subscription to symbols.

        Subscribes to ticker and 1m kline channels for each symbol.

        Args:
            symbols: List of symbols to subscribe to
        """
        if not self.ws:
            logger.warning("WebSocket not connected, cannot subscribe")
            return

        # Bitunix WS docs (01_Projectplan/Bitunix_API):
        # {
        #   "op": "subscribe",
        #   "args": [{"symbol":"BTCUSDT","ch":"market_kline_1min"}]
        # }
        kline_msg = {
            "op": "subscribe",
            "args": [{"symbol": s, "ch": "market_kline_1min"} for s in symbols],
        }
        await self.ws.send(json.dumps(kline_msg))
        logger.info(f"📡 Bitunix: Subscribed to market_kline_1min for symbols: {symbols}")

    async def _handle_unsubscription(self, symbols: list[str]) -> None:
        """Handle unsubscription from symbols.

        Args:
            symbols: List of symbols to unsubscribe from
        """
        if not self.ws:
            return

        unsub_msg = {
            "op": "unsubscribe",
            "args": [{"symbol": s, "ch": "market_kline_1min"} for s in symbols],
        }
        await self.ws.send(json.dumps(unsub_msg))

        logger.debug(f"Unsubscribed from kline for {len(symbols)} symbols")

    async def _run_stream(self) -> None:
        """Main message loop with auto-reconnect."""
        while self.connected:
            try:
                async for message in self.ws:
                    await self._on_message(message)

            except ConnectionClosed as e:
                if self.connected:
                    logger.warning(f"Connection closed: {e}, attempting reconnect...")
                    await self._handle_reconnect()
                    # After reconnect, connect() starts a new _stream_task
                    # This old task should exit to avoid duplicates
                    return
                else:
                    break

            except Exception as e:
                logger.error(f"Stream error: {e}")
                if self.connected:
                    # Avoid tight loops; let reconnect logic run
                    await self._handle_reconnect()
                    return
                else:
                    break

    async def _handle_reconnect(self) -> None:
        """Handle reconnection logic with exponential backoff."""
        if self._reconnect_count >= self.reconnect_attempts:
            logger.error(f"Max reconnect attempts ({self.reconnect_attempts}) reached")
            await self.disconnect()
            return

        self._reconnect_count += 1
        self.metrics.reconnect_count = self._reconnect_count
        self.metrics.status = StreamStatus.RECONNECTING

        # Exponential backoff: 2^n seconds
        delay = min(2 ** self._reconnect_count, 60)  # Max 60 seconds
        logger.info(f"Reconnecting in {delay}s (attempt {self._reconnect_count}/{self.reconnect_attempts})")
        await asyncio.sleep(delay)

        # Close old WebSocket and reset connection state
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass  # Ignore errors when closing dead connection

        # Cancel old stream task if it's still running (should have exited already)
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass

        self.ws = None
        self._stream_task = None
        self.connected = False  # CRITICAL: Reset flag before reconnect

        success = await self.connect()

        # Re-subscribe to previous symbols
        if success and self.metrics.subscribed_symbols:
            symbols = list(self.metrics.subscribed_symbols)
            await self._handle_subscription(symbols)
            logger.info(f"Re-subscribed to {len(symbols)} symbols")
        elif not success:
            # If reconnect fails (e.g., auth/endpoint issues), stop attempting to avoid tight loops
            self.connected = False
            self.metrics.status = StreamStatus.ERROR

    async def _on_message(self, message: str) -> None:
        """Parse and handle incoming WebSocket messages.

        Args:
            message: JSON message string
        """
        try:
            data = json.loads(message)

            # Update metrics
            self.metrics.messages_received += 1
            self.metrics.last_message_at = datetime.utcnow()

            # Handle different message types
            op = data.get('op')

            # Log first few messages to help debug (including pongs)
            if self.metrics.messages_received <= 5:
                logger.debug(f"📨 Bitunix message #{self.metrics.messages_received}: {data}")

            if op == 'pong':
                # Heartbeat response (keep-alive)
                logger.debug(f"💓 Heartbeat pong received")
                return

            # Channel messages
            channel = data.get('ch', '')

            if 'kline' in channel or 'market_kline' in channel:
                await self._handle_kline(data)
            elif 'depth' in channel:
                await self._handle_depth(data)
            elif 'trade' in channel:
                await self._handle_trade(data)
            else:
                # Unknown/heartbeat noise -> debug only
                logger.debug(f"⚠ Bitunix: Unknown message type (op={op}, ch={channel}): {data}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            self.metrics.messages_dropped += 1
        except Exception as e:
            logger.error(f"Message processing error: {e}", exc_info=True)
            self.metrics.messages_dropped += 1

    async def _handle_ticker(self, data: dict) -> None:
        """Handle ticker updates.

        Example data:
        {
            "ch": "ticker",
            "data": {
                "symbol": "BTCUSDT",
                "lastPrice": "45000.0",
                "markPrice": "45010.0",
                "open": "44000.0",
                "high": "46000.0",
                "low": "43500.0",
                "baseVol": "1234.56",
                "quoteVol": "55000000.0"
            }
        }

        Args:
            data: Ticker data
        """
        ticker = data.get('data', {})
        symbol = ticker.get('symbol')

        if not symbol:
            return

        # Create MarketTick
        tick = MarketTick(
            symbol=symbol,
            last=Decimal(str(ticker.get('lastPrice', 0))),
            volume=int(float(ticker.get('baseVol', 0))),
            timestamp=datetime.utcnow(),
            source=self.name
        )

        # Add to buffer and cache
        self.buffer.append(tick)
        self.symbol_cache[symbol] = tick

        # Process tick (latency calculation, callbacks)
        self.process_tick(tick)

        # Emit event
        event_bus.emit(
            Event(
                type=EventType.MARKET_DATA_TICK,
                timestamp=tick.timestamp or datetime.utcnow(),
                data={
                    "symbol": symbol,
                    "tick": tick,
                    "price": float(tick.last) if tick.last is not None else 0.0,
                    "volume": tick.volume,
                    "timestamp": tick.timestamp or datetime.utcnow(),
                },
                source=self.name,
            )
        )

    async def _handle_kline(self, data: dict) -> None:
        """Handle kline (candlestick) updates.

        Example data:
        {
            "ch": "market_kline",
            "data": {
                "symbol": "BTCUSDT",
                "time": 1609459200000,
                "open": "29000.0",
                "high": "29500.0",
                "low": "28800.0",
                "close": "29300.0",
                "baseVol": "123.45",
                "closed": true
            }
        }

        Args:
            data: Kline data
        """
        # Bitunix WS docs format:
        # {
        #   "ch": "mark_kline_1min",
        #   "symbol": "BNBUSDT",
        #   "ts": 1732178884994,
        #   "data": {"o":"...","h":"...","l":"...","c":"...","b":"...","q":"..."}
        # }
        symbol = data.get("symbol")
        ts_ms = data.get("ts")
        kline = data.get("data") or {}

        if not symbol or not ts_ms:
            logger.warning(f"⚠ Bitunix: Kline missing symbol or timestamp: {data}")
            return

        ts = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)
        open_ = float(kline.get("o", 0))
        high = float(kline.get("h", 0))
        low = float(kline.get("l", 0))
        close = float(kline.get("c", 0))
        volume = float(kline.get("b", 0))

        # Log first kline to confirm data flow
        if not hasattr(self, '_kline_count'):
            self._kline_count = 0
        self._kline_count += 1
        if self._kline_count <= 3:
            logger.info(f"📊 Bitunix kline #{self._kline_count}: {symbol} @ ${close:.2f} (vol={volume:.2f})")

        # NOTE: Only emit MARKET_DATA_TICK, not MARKET_BAR
        # The streaming_mixin's _on_market_tick handler already aggregates ticks into candles.
        # Emitting MARKET_BAR would cause duplicate candles since both handlers would
        # update the chart independently with potentially different timestamps.

        # Emit tick event - the chart's tick handler will aggregate this into candles
        event_bus.emit(
            Event(
                type=EventType.MARKET_DATA_TICK,
                timestamp=ts,
                data={
                    "symbol": symbol,
                    "price": close,
                    "volume": volume,
                    "open": open_,    # Include OHLC for better tick handling
                    "high": high,
                    "low": low,
                    "timestamp": ts,
                },
                source=self.name,
            )
        )

    async def _handle_depth(self, data: dict) -> None:
        """Handle order book depth updates.

        Args:
            data: Depth data
        """
        # TODO: Implement depth handling if needed
        logger.debug(f"Depth update: {data.get('data', {}).get('symbol')}")

    async def _handle_trade(self, data: dict) -> None:
        """Handle trade feed updates.

        Args:
            data: Trade data
        """
        # TODO: Implement trade handling if needed
        logger.debug(f"Trade update: {data.get('data', {}).get('symbol')}")

    def get_latest_tick(self, symbol: str) -> MarketTick | None:
        """Get latest tick for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest MarketTick or None
        """
        return self.symbol_cache.get(symbol)

    def get_metrics(self) -> dict:
        """Get stream metrics.

        Returns:
            Dictionary of metrics
        """
        return {
            "status": self.metrics.status.value,
            "connected": self.connected,
            "messages_received": self.metrics.messages_received,
            "messages_dropped": self.metrics.messages_dropped,
            "average_latency_ms": round(self.metrics.average_latency_ms, 2),
            "current_lag_ms": round(self.metrics.current_lag_ms, 2),
            "reconnect_count": self.metrics.reconnect_count,
            "subscribed_symbols": list(self.metrics.subscribed_symbols),
            "buffer_size": len(self.buffer)
        }
