"""Bitunix WebSocket Stream Client.

Real-time market data streaming for Bitunix Futures via WebSocket.
Supports ticker, kline, depth, and trade channels.
"""

import asyncio
import json
import logging
import ssl
import time
from datetime import datetime, timezone
from decimal import Decimal

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus

from src.common.event_bus import Event, EventType, event_bus
from src.core.market_data.errors import MarketDataAccessBlocked
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
        self._heartbeat_task = None
        self._reconnect_count = 0
        self._kline_channel = "market_kline_1min"
        self.last_error: Exception | None = None

    def _get_ws_url(self) -> str:
        """Get WebSocket URL based on environment.

        Returns:
            WebSocket URL
        """
        # Offizielle öffentliche Futures-WS-Domain lt. Projekt-RTF:
        #   wss://fapi.bitunix.com/public/Main
        # Wir folgen exakt dem Pfad inklusive /Main, um Kompatibilität sicherzustellen.
        return "wss://fapi.bitunix.com/public/Main"

    async def connect(self) -> bool:
        """Establish WebSocket connection via supervisor task.

        Returns:
            True if supervisor started
        """
        logger.info("📡 Bitunix Stream: Starting connection...")
        logger.debug(f"📡 Bitunix Stream: WS URL = {self.ws_url}")
        logger.debug(f"📡 Bitunix Stream: Use Testnet = {self.use_testnet}")

        if self.connected:
            logger.warning("📡 Bitunix Stream: Already connected or connecting")
            return True

        # Preflight WS handshake to surface 403/Cloudflare immediately
        logger.debug("📡 Bitunix Stream: Running preflight handshake...")
        try:
            await self._preflight_handshake()
            logger.debug("📡 Bitunix Stream: Preflight handshake successful")
        except Exception as e:
            logger.error(f"❌ Bitunix Stream: Preflight handshake failed: {e}")
            raise

        self.connected = True
        self.metrics.status = StreamStatus.CONNECTING
        self._reconnect_count = 0
        self.last_error = None

        # Start single supervisor task
        if not self._stream_task or self._stream_task.done():
            logger.info("📡 Bitunix Stream: Starting supervisor task...")
            self._stream_task = asyncio.create_task(self._run_supervisor())
        else:
            logger.debug("📡 Bitunix Stream: Supervisor task already running")

        return True

    async def disconnect(self) -> None:
        """Disconnect from Bitunix WebSocket and stop supervisor."""
        logger.info("📡 Bitunix Stream: Disconnecting...")

        self.connected = False
        self.metrics.status = StreamStatus.DISCONNECTED

        # Signal closure to WebSocket
        if self.ws:
            try:
                logger.debug("📡 Bitunix Stream: Closing WebSocket connection...")
                await self.ws.close()
                logger.debug("📡 Bitunix Stream: WebSocket closed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Bitunix Stream: Error closing WebSocket: {e}")
            self.ws = None

        # Supervisor task will exit naturally because self.connected is False
        # and it awaits current operations with timeouts or exception handling.
        # We don't await self._stream_task here to avoid any potential UI hang.
        self._stream_task = None
        self._heartbeat_task = None # Obsolete

        await super().disconnect()
        logger.info("✅ Bitunix Stream: Disconnected")

    async def _run_supervisor(self) -> None:
        """Supervisor loop managing connection lifecycle and heartbeats."""
        logger.info("📡 Bitunix Stream: Supervisor loop started")

        while self.connected:
            try:
                self.metrics.status = StreamStatus.CONNECTING
                logger.info(f"📡 Bitunix Stream: Connecting to {self.ws_url}")

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                async with websockets.connect(
                    self.ws_url,
                    ssl=ssl_context,
                    ping_interval=None, # Manual heartbeat
                    ping_timeout=10
                ) as ws:
                    self.ws = websocket = ws # Use local ref for loop
                    self.metrics.status = StreamStatus.CONNECTED
                    self.metrics.connected_at = datetime.utcnow()
                    self._reconnect_count = 0
                    self.metrics.reconnect_count = 0
                    logger.info(f"✅ Bitunix Stream: Connected successfully")

                    # Subscribe to symbols
                    if self.metrics.subscribed_symbols:
                        logger.info(f"📡 Bitunix Stream: Subscribing to {len(self.metrics.subscribed_symbols)} symbols...")
                        await self._handle_subscription(list(self.metrics.subscribed_symbols))
                    else:
                        logger.debug("📡 Bitunix Stream: No symbols to subscribe yet")

                    # Message and Heartbeat loop
                    last_ping = 0
                    message_count = 0
                    while self.connected and self._is_ws_open(websocket):
                        # 1. Check Heartbeat (3s interval)
                        now = time.time()
                        if now - last_ping >= 3:
                            ping_msg = {"op": "ping", "ping": int(now)}
                            await websocket.send(json.dumps(ping_msg))
                            logger.debug(f"💓 Bitunix Stream: Heartbeat sent")
                            last_ping = now

                        # 2. Process Messages with timeout to allow heartbeat check
                        try:
                            # Use wait_for to keep loop responsive
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            message_count += 1
                            if message_count <= 5:
                                logger.debug(f"📨 Bitunix Stream: Received message #{message_count}")
                            await self._on_message(message)
                        except asyncio.TimeoutError:
                            continue # Just loop back for heartbeat/status check

            except InvalidStatus as e:
                blocked = self._map_invalid_status(e)
                self.last_error = blocked
                self.metrics.status = StreamStatus.ERROR
                self.connected = False
                logger.error(f"❌ Bitunix Stream: WebSocket blocked (HTTP {e.status_code if hasattr(e, 'status_code') else 'unknown'})")
                logger.error(f"❌ Bitunix Stream: Error details: {blocked}")
                break
            except ConnectionClosed as e:
                if not self.connected:
                    logger.debug("📡 Bitunix Stream: Connection closed normally (disconnect requested)")
                    break

                self.metrics.status = StreamStatus.RECONNECTING
                self._reconnect_count += 1
                self.metrics.reconnect_count = self._reconnect_count
                delay = min(2 ** self._reconnect_count, 30)
                logger.warning(f"⚠️ Bitunix Stream: Connection closed unexpectedly (code={e.code if hasattr(e, 'code') else 'unknown'}, reason={e.reason if hasattr(e, 'reason') else 'unknown'})")
                logger.warning(f"⚠️ Bitunix Stream: Reconnecting in {delay}s (attempt #{self._reconnect_count})...")

                # Cleanup state
                self.ws = None

                # Wait before retry
                for i in range(delay):
                    if not self.connected:
                        logger.debug("📡 Bitunix Stream: Reconnect cancelled (disconnect requested)")
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                if not self.connected:
                    logger.debug(f"📡 Bitunix Stream: Connection error during shutdown: {e}")
                    break

                self.metrics.status = StreamStatus.RECONNECTING
                self._reconnect_count += 1
                self.metrics.reconnect_count = self._reconnect_count
                delay = min(2 ** self._reconnect_count, 30)
                logger.error(f"❌ Bitunix Stream: Unexpected error: {type(e).__name__}: {e}")
                logger.error(f"❌ Bitunix Stream: Reconnecting in {delay}s (attempt #{self._reconnect_count})...", exc_info=True)

                # Cleanup state
                self.ws = None

                # Wait before retry
                for i in range(delay):
                    if not self.connected:
                        logger.debug("📡 Bitunix Stream: Reconnect cancelled (disconnect requested)")
                        break
                    await asyncio.sleep(1)

        self.metrics.status = StreamStatus.DISCONNECTED
        logger.info("📡 Bitunix Stream: Supervisor stopped")

    async def _run_stream(self) -> None:
        """Deprecated: Logic moved to _run_supervisor."""
        pass

    async def _run_heartbeat(self) -> None:
        """Deprecated: Logic moved to _run_supervisor."""
        pass

    async def _handle_reconnect(self) -> None:
        """Deprecated: Logic moved to _run_supervisor."""
        pass

    async def _preflight_handshake(self) -> None:
        """Perform a single WS handshake to detect blocking (e.g., 403/Cloudflare)."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            async with websockets.connect(
                self.ws_url,
                ssl=ssl_context,
                ping_interval=None,
                ping_timeout=10,
                close_timeout=5,
            ):
                self.last_error = None
                return
        except InvalidStatus as e:
            blocked = self._map_invalid_status(e)
            self.last_error = blocked
            raise blocked

    def _map_invalid_status(self, exc: InvalidStatus) -> MarketDataAccessBlocked:
        """Convert websockets InvalidStatus to a rich exception for UI handling."""
        status = getattr(exc, "status_code", None)
        response = getattr(exc, "response", None)
        if response:
            status = status or getattr(response, "status_code", None) or getattr(response, "status", None)

        body_snippet = ""
        if response and hasattr(response, "body"):
            raw_body = getattr(response, "body", b"")
            try:
                if isinstance(raw_body, (bytes, bytearray)):
                    body_snippet = raw_body[:400].decode("utf-8", errors="ignore")
                else:
                    body_snippet = str(raw_body)[:400]
            except Exception:
                body_snippet = ""

        reason = "WebSocket handshake rejected"
        text = body_snippet.lower() if body_snippet else ""
        if status == 403:
            if "api key does not support this operation" in text:
                reason = "Forbidden: API key lacks permission for this operation"
            elif "api key" in text:
                reason = "Forbidden: API key/permission issue"
            else:
                reason = "Forbidden / Bot-Protection (Cloudflare?)"

        return MarketDataAccessBlocked(
            provider="bitunix-ws",
            status_code=status,
            reason=reason,
            body_snippet=body_snippet,
        )

    @staticmethod
    def _is_ws_open(ws) -> bool:
        """Compatibility helper: determine if websockets connection is open."""
        try:
            closed = getattr(ws, "closed", None)
            if closed is not None:
                return not closed

            state = getattr(ws, "state", None)
            if state is not None:
                name = getattr(state, "name", "").lower()
                return name in ("open", "connected")
        except Exception:
            pass

        # Fallback: assume open to avoid premature disconnect
        return True

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

            # Log first few messages to help debug (including pings)
            if self.metrics.messages_received <= 5:
                logger.debug(f"📨 Bitunix message #{self.metrics.messages_received}: {data}")

            if op == 'ping':
                # Heartbeat response (keep-alive)
                logger.debug("💓 Heartbeat ping/pong received")
                return

            if op in {"subscribe", "unsubscribe"}:
                logger.info(f"Bitunix WS ack: {data}")
                return

            if op == "connect":
                logger.info("✅ Bitunix Stream: Server confirmed connection")
                return

            if op == "error":
                error_code = data.get('code', 'unknown')
                error_msg = data.get('message', data.get('msg', 'Unknown error'))
                error_data = data.get('data', {})
                logger.error(f"❌ Bitunix Stream: Server error received!")
                logger.error(f"   Error Code: {error_code}")
                logger.error(f"   Error Message: {error_msg}")
                if error_data:
                    logger.error(f"   Error Data: {error_data}")
                logger.error(f"   Full Response: {data}")
                return

            # Channel messages
            channel = data.get('ch', '')

            if 'kline' in channel or 'market_kline' in channel:
                await self._handle_kline(data)
            elif 'ticker' in channel:
                await self._handle_ticker(data)
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

        # Process tick (latency calculation, callbacks, caching)
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

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Normalize symbols to Bitunix format (uppercase, no separators)."""
        return str(symbol).replace("/", "").replace("-", "").upper()

    def _build_subscription_args(self, symbols: list[str]) -> list[dict[str, str]]:
        """Build subscription args for ticker + 1m kline channels."""
        args: list[dict[str, str]] = []
        for symbol in symbols:
            normalized = self._normalize_symbol(symbol)
            args.append({"symbol": normalized, "ch": self._kline_channel})
            args.append({"symbol": normalized, "ch": "ticker"})
        return args

    async def _handle_subscription(self, symbols: list[str]) -> None:
        """Send subscription request for given symbols."""
        if not self.ws or not self._is_ws_open(self.ws):
            logger.warning("⚠️ Bitunix Stream: WebSocket not connected; subscription deferred")
            return

        args = self._build_subscription_args(symbols)
        if not args:
            logger.warning("⚠️ Bitunix Stream: No subscription args generated (no symbols)")
            return

        payload = {"op": "subscribe", "args": args}
        logger.info(f"📡 Bitunix Stream: Subscribing to {len(args)} channels for {len(symbols)} symbols...")
        logger.debug(f"📡 Bitunix Stream: Subscription payload: {payload}")

        try:
            await self.ws.send(json.dumps(payload))
            logger.info(f"✅ Bitunix Stream: Subscription request sent for {len(symbols)} symbols")
        except Exception as e:
            logger.error(f"❌ Bitunix Stream: Failed to send subscription: {e}")

    async def _handle_unsubscription(self, symbols: list[str]) -> None:
        """Send unsubscription request for given symbols."""
        if not self.ws or not self._is_ws_open(self.ws):
            logger.warning("⚠️ Bitunix Stream: WebSocket not connected; unsubscription skipped")
            return

        args = self._build_subscription_args(symbols)
        payload = {"op": "unsubscribe", "args": args}
        logger.info(f"📡 Bitunix Stream: Unsubscribing from {len(args)} channels for {len(symbols)} symbols...")
        logger.debug(f"📡 Bitunix Stream: Unsubscription payload: {payload}")

        try:
            await self.ws.send(json.dumps(payload))
            logger.info(f"✅ Bitunix Stream: Unsubscription request sent for {len(symbols)} symbols")
        except Exception as e:
            logger.error(f"❌ Bitunix Stream: Failed to send unsubscription: {e}")

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
