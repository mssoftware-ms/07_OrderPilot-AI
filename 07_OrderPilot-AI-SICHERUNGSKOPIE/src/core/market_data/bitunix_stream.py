"""Bitunix WebSocket Stream Client (REFACTORED).

Real-time market data streaming for Bitunix Futures via WebSocket.
Supports ticker, kline, depth, and trade channels.

Module 5/5 of bitunix_stream.py split - Main Orchestrator
"""

import logging

from src.core.market_data.stream_client import MarketTick, StreamClient

from .bitunix_stream_connection import BitunixStreamConnection
from .bitunix_stream_handlers import BitunixStreamHandlers
from .bitunix_stream_messages import BitunixStreamMessages
from .bitunix_stream_subscription import BitunixStreamSubscription

logger = logging.getLogger(__name__)


class BitunixStreamClient(StreamClient):
    """Bitunix WebSocket stream client for real-time market data (REFACTORED).

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

        # Composition pattern - Helper-Klassen
        self._connection = BitunixStreamConnection(parent=self)
        self._messages = BitunixStreamMessages(parent=self)
        self._handlers = BitunixStreamHandlers(parent=self)
        self._subscription = BitunixStreamSubscription(parent=self)

    def _get_ws_url(self) -> str:
        """Get WebSocket URL based on environment.

        Returns:
            WebSocket URL
        """
        # Offizielle öffentliche Futures-WS-Domain lt. Projekt-RTF:
        #   wss://fapi.bitunix.com/public/Main
        # Wir folgen exakt dem Pfad inklusive /Main, um Kompatibilität sicherzustellen.
        return "wss://fapi.bitunix.com/public/Main"

    # =========================================================================
    # CONNECTION LIFECYCLE (delegiert an BitunixStreamConnection)
    # =========================================================================

    async def connect(self) -> bool:
        """Establish WebSocket connection via supervisor task."""
        return await self._connection.connect()

    async def disconnect(self) -> None:
        """Disconnect from Bitunix WebSocket and stop supervisor."""
        await self._connection.disconnect()
        await super().disconnect()

    # =========================================================================
    # DEPRECATED METHODS (kept for backward compatibility)
    # =========================================================================

    async def _run_stream(self) -> None:
        """Deprecated: Logic moved to _run_supervisor."""
        pass

    async def _run_heartbeat(self) -> None:
        """Deprecated: Logic moved to _run_supervisor."""
        pass

    async def _handle_reconnect(self) -> None:
        """Deprecated: Logic moved to _run_supervisor."""
        pass

    # =========================================================================
    # PUBLIC API
    # =========================================================================

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


__all__ = ["BitunixStreamClient"]
