"""Bitunix Stream - Connection Lifecycle Management.

Refactored from bitunix_stream.py monolith.

Module 1/5 of bitunix_stream.py split.

Contains:
- connect: Establish WebSocket connection
- disconnect: Close connection
- _run_supervisor: Main connection/heartbeat loop
- _preflight_handshake: Early connection test
- _map_invalid_status: Error mapping
- _is_ws_open: WebSocket state check
"""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus

from src.core.market_data.errors import MarketDataAccessBlocked
from src.core.market_data.stream_client import StreamStatus

logger = logging.getLogger(__name__)


class BitunixStreamConnection:
    """Helper für BitunixStreamClient connection lifecycle."""

    def __init__(self, parent):
        """
        Args:
            parent: BitunixStreamClient Instanz
        """
        self.parent = parent

    async def connect(self) -> bool:
        """Establish WebSocket connection via supervisor task."""
        logger.info("📡 Bitunix Stream: Starting connection...")
        logger.debug(f"📡 Bitunix Stream: WS URL = {self.parent.ws_url}")
        logger.debug(f"📡 Bitunix Stream: Use Testnet = {self.parent.use_testnet}")

        if self.parent.connected:
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

        self.parent.connected = True
        self.parent.metrics.status = StreamStatus.CONNECTING
        self.parent._reconnect_count = 0
        self.parent.last_error = None

        # Start single supervisor task
        if not self.parent._stream_task or self.parent._stream_task.done():
            logger.info("📡 Bitunix Stream: Starting supervisor task...")
            self.parent._stream_task = asyncio.create_task(self._run_supervisor())
        else:
            logger.debug("📡 Bitunix Stream: Supervisor task already running")

        return True

    async def disconnect(self) -> None:
        """Disconnect from Bitunix WebSocket and stop supervisor."""
        logger.info("📡 Bitunix Stream: Disconnecting...")

        self.parent.connected = False
        self.parent.metrics.status = StreamStatus.DISCONNECTED

        # Signal closure to WebSocket
        if self.parent.ws:
            try:
                logger.debug("📡 Bitunix Stream: Closing WebSocket connection...")
                await self.parent.ws.close()
                logger.debug("📡 Bitunix Stream: WebSocket closed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Bitunix Stream: Error closing WebSocket: {e}")
            self.parent.ws = None

        # Supervisor task will exit naturally
        self.parent._stream_task = None
        self.parent._heartbeat_task = None

        logger.info("✅ Bitunix Stream: Disconnected")

    async def _run_supervisor(self) -> None:
        """Supervisor loop managing connection lifecycle and heartbeats."""
        logger.info("📡 Bitunix Stream: Supervisor loop started")

        while self.parent.connected:
            try:
                self.parent.metrics.status = StreamStatus.CONNECTING
                logger.info(f"📡 Bitunix Stream: Connecting to {self.parent.ws_url}")

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                async with websockets.connect(
                    self.parent.ws_url,
                    ssl=ssl_context,
                    ping_interval=None,  # Manual heartbeat
                    ping_timeout=10
                ) as ws:
                    self.parent.ws = websocket = ws  # Use local ref for loop
                    self.parent.metrics.status = StreamStatus.CONNECTED
                    self.parent.metrics.connected_at = datetime.utcnow()
                    self.parent._reconnect_count = 0
                    self.parent.metrics.reconnect_count = 0
                    logger.info(f"✅ Bitunix Stream: Connected successfully")

                    # Subscribe to symbols
                    if self.parent.metrics.subscribed_symbols:
                        logger.info(f"📡 Bitunix Stream: Subscribing to {len(self.parent.metrics.subscribed_symbols)} symbols...")
                        await self.parent._subscription.handle_subscription(list(self.parent.metrics.subscribed_symbols))
                    else:
                        logger.debug("📡 Bitunix Stream: No symbols to subscribe yet")

                    # Message and Heartbeat loop
                    last_ping = 0
                    message_count = 0
                    while self.parent.connected and self._is_ws_open(websocket):
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
                            await self.parent._messages.on_message(message)
                        except asyncio.TimeoutError:
                            continue  # Just loop back for heartbeat/status check

            except InvalidStatus as e:
                blocked = self._map_invalid_status(e)
                self.parent.last_error = blocked
                self.parent.metrics.status = StreamStatus.ERROR
                self.parent.connected = False
                logger.error(f"❌ Bitunix Stream: WebSocket blocked (HTTP {e.status_code if hasattr(e, 'status_code') else 'unknown'})")
                logger.error(f"❌ Bitunix Stream: Error details: {blocked}")
                break
            except ConnectionClosed as e:
                if not self.parent.connected:
                    logger.debug("📡 Bitunix Stream: Connection closed normally (disconnect requested)")
                    break

                self.parent.metrics.status = StreamStatus.RECONNECTING
                self.parent._reconnect_count += 1
                self.parent.metrics.reconnect_count = self.parent._reconnect_count
                delay = min(2 ** self.parent._reconnect_count, 30)
                logger.warning(f"⚠️ Bitunix Stream: Connection closed unexpectedly (code={e.code if hasattr(e, 'code') else 'unknown'}, reason={e.reason if hasattr(e, 'reason') else 'unknown'})")
                logger.warning(f"⚠️ Bitunix Stream: Reconnecting in {delay}s (attempt #{self.parent._reconnect_count})...")

                # Cleanup state
                self.parent.ws = None

                # Wait before retry
                for i in range(delay):
                    if not self.parent.connected:
                        logger.debug("📡 Bitunix Stream: Reconnect cancelled (disconnect requested)")
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                if not self.parent.connected:
                    logger.debug(f"📡 Bitunix Stream: Connection error during shutdown: {e}")
                    break

                self.parent.metrics.status = StreamStatus.RECONNECTING
                self.parent._reconnect_count += 1
                self.parent.metrics.reconnect_count = self.parent._reconnect_count
                delay = min(2 ** self.parent._reconnect_count, 30)
                logger.error(f"❌ Bitunix Stream: Unexpected error: {type(e).__name__}: {e}")
                logger.error(f"❌ Bitunix Stream: Reconnecting in {delay}s (attempt #{self.parent._reconnect_count})...", exc_info=True)

                # Cleanup state
                self.parent.ws = None

                # Wait before retry
                for i in range(delay):
                    if not self.parent.connected:
                        logger.debug("📡 Bitunix Stream: Reconnect cancelled (disconnect requested)")
                        break
                    await asyncio.sleep(1)

        self.parent.metrics.status = StreamStatus.DISCONNECTED
        logger.info("📡 Bitunix Stream: Supervisor stopped")

    async def _preflight_handshake(self) -> None:
        """Perform a single WS handshake to detect blocking (e.g., 403/Cloudflare)."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            async with websockets.connect(
                self.parent.ws_url,
                ssl=ssl_context,
                ping_interval=None,
                ping_timeout=10,
                close_timeout=5,
            ):
                self.parent.last_error = None
                return
        except InvalidStatus as e:
            blocked = self._map_invalid_status(e)
            self.parent.last_error = blocked
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
