"""Stream Client for Real-Time Market Data.

Handles WebSocket/streaming connections to brokers for 1-second market data.
"""

import asyncio
import json
import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from src.common.event_bus import Event, EventType, event_bus
from src.database import get_db_manager
from src.database.models import MarketBar

logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Stream connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class StreamMetrics:
    """Metrics for stream performance."""
    status: StreamStatus = StreamStatus.DISCONNECTED
    connected_at: datetime | None = None
    last_message_at: datetime | None = None
    messages_received: int = 0
    messages_dropped: int = 0
    average_latency_ms: float = 0.0
    current_lag_ms: float = 0.0
    reconnect_count: int = 0
    subscribed_symbols: set[str] = field(default_factory=set)

    def update_latency(self, latency_ms: float):
        """Update average latency."""
        # Simple moving average
        alpha = 0.1  # Smoothing factor
        if self.average_latency_ms == 0:
            self.average_latency_ms = latency_ms
        else:
            self.average_latency_ms = (
                alpha * latency_ms + (1 - alpha) * self.average_latency_ms
            )


@dataclass
class MarketTick:
    """Market data tick."""
    symbol: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    last: Decimal | None = None
    volume: int | None = None
    timestamp: datetime | None = None
    source: str = ""
    latency_ms: float | None = None


class StreamClient:
    """Base class for market data stream clients."""

    def __init__(
        self,
        name: str,
        buffer_size: int = 10000,
        heartbeat_interval: int = 30,
        reconnect_attempts: int = 5,
        max_lag_ms: float = 1000
    ):
        """Initialize stream client.

        Args:
            name: Client name
            buffer_size: Size of the data buffer
            heartbeat_interval: Heartbeat interval in seconds
            reconnect_attempts: Maximum reconnection attempts
            max_lag_ms: Maximum acceptable lag in milliseconds
        """
        self.name = name
        self.buffer_size = buffer_size
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_attempts = reconnect_attempts
        self.max_lag_ms = max_lag_ms

        # State
        self.metrics = StreamMetrics()
        self.connected = False

        # Data buffer
        self.buffer: deque = deque(maxlen=buffer_size)
        self.symbol_cache: dict[str, MarketTick] = {}

        # Subscriptions
        self.subscriptions: set[str] = set()
        self.subscription_callbacks: dict[str, list[Callable]] = {}

        # Tasks
        self._heartbeat_task: asyncio.Task | None = None
        self._processing_task: asyncio.Task | None = None

        # Backpressure handling
        self.batch_size = 100
        self.batch_interval = 0.1  # Process batch every 100ms

        logger.info(f"Stream client {name} initialized")

    async def connect(self) -> None:
        """Connect to data stream."""
        raise NotImplementedError("Subclasses must implement connect()")

    async def disconnect(self) -> None:
        """Disconnect from data stream."""
        self.connected = False
        self.metrics.status = StreamStatus.DISCONNECTED

        # Cancel tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._processing_task:
            self._processing_task.cancel()

        logger.info(f"Stream client {self.name} disconnected")

    async def subscribe(self, symbols: list[str], callback: Callable | None = None) -> None:
        """Subscribe to market data for symbols.

        Args:
            symbols: List of symbols to subscribe to
            callback: Optional callback for data updates
        """
        for symbol in symbols:
            self.subscriptions.add(symbol)

            if callback:
                if symbol not in self.subscription_callbacks:
                    self.subscription_callbacks[symbol] = []
                self.subscription_callbacks[symbol].append(callback)

            self.metrics.subscribed_symbols.add(symbol)

        # Notify subclass to handle subscription
        await self._handle_subscription(symbols)

        logger.info(f"Subscribed to {len(symbols)} symbols")

    async def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from market data.

        Args:
            symbols: List of symbols to unsubscribe from
        """
        for symbol in symbols:
            self.subscriptions.discard(symbol)
            self.subscription_callbacks.pop(symbol, None)
            self.metrics.subscribed_symbols.discard(symbol)

        # Notify subclass to handle unsubscription
        await self._handle_unsubscription(symbols)

        logger.info(f"Unsubscribed from {len(symbols)} symbols")

    async def _handle_subscription(self, symbols: list[str]) -> None:
        """Handle subscription request (override in subclass)."""
        pass

    async def _handle_unsubscription(self, symbols: list[str]) -> None:
        """Handle unsubscription request (override in subclass)."""
        pass

    def process_tick(self, tick: MarketTick) -> None:
        """Process incoming market tick.

        Args:
            tick: Market data tick
        """
        # Calculate latency if timestamp provided
        if tick.timestamp:
            latency_ms = (datetime.utcnow() - tick.timestamp).total_seconds() * 1000
            tick.latency_ms = latency_ms
            self.metrics.current_lag_ms = latency_ms
            self.metrics.update_latency(latency_ms)

            # Check for excessive lag
            if latency_ms > self.max_lag_ms:
                logger.warning(f"High latency detected: {latency_ms:.0f}ms for {tick.symbol}")

        # Update cache
        self.symbol_cache[tick.symbol] = tick

        # Add to buffer
        self.buffer.append(tick)

        # Update metrics
        self.metrics.messages_received += 1
        self.metrics.last_message_at = datetime.utcnow()

        # Call callbacks
        if tick.symbol in self.subscription_callbacks:
            for callback in self.subscription_callbacks[tick.symbol]:
                try:
                    asyncio.create_task(self._safe_callback(callback, tick))
                except Exception as e:
                    logger.error(f"Error in callback: {e}")

    async def _safe_callback(self, callback: Callable, tick: MarketTick) -> None:
        """Safely execute callback.

        Args:
            callback: Callback function
            tick: Market tick data
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(tick)
            else:
                callback(tick)
        except Exception as e:
            logger.error(f"Callback error: {e}")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to keep connection alive."""
        while self.connected:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def _send_heartbeat(self) -> None:
        """Send heartbeat (override in subclass)."""
        pass

    async def _reconnect(self) -> None:
        """Reconnect with exponential backoff."""
        self.metrics.status = StreamStatus.RECONNECTING

        for attempt in range(self.reconnect_attempts):
            wait_time = min(2 ** attempt, 60)  # Max 60 seconds
            logger.info(f"Reconnecting {self.name} in {wait_time} seconds (attempt {attempt + 1})")

            await asyncio.sleep(wait_time)

            try:
                await self.connect()

                # Resubscribe to symbols
                if self.subscriptions:
                    await self.subscribe(list(self.subscriptions))

                self.metrics.reconnect_count += 1
                logger.info(f"Reconnection successful for {self.name}")
                return

            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")

        self.metrics.status = StreamStatus.ERROR
        logger.error(f"Failed to reconnect {self.name} after {self.reconnect_attempts} attempts")

    async def _process_buffer(self) -> None:
        """Process buffered data in batches."""
        batch = []

        while self.connected:
            try:
                # Collect batch
                while len(batch) < self.batch_size and self.buffer:
                    batch.append(self.buffer.popleft())

                # Process batch if ready
                if batch:
                    await self._process_batch(batch)
                    batch.clear()

                # Wait for next batch interval
                await asyncio.sleep(self.batch_interval)

            except Exception as e:
                logger.error(f"Buffer processing error: {e}")

    async def _process_batch(self, batch: list[MarketTick]) -> None:
        """Process a batch of market ticks.

        Args:
            batch: List of market ticks
        """
        # Emit event for batch
        event_bus.emit(Event(
            type=EventType.MARKET_TICK,
            timestamp=datetime.utcnow(),
            data={
                "ticks": [self._tick_to_dict(tick) for tick in batch],
                "count": len(batch)
            },
            source=self.name
        ))

        # Store in database if configured
        await self._store_ticks(batch)

    def _tick_to_dict(self, tick: MarketTick) -> dict[str, Any]:
        """Convert tick to dictionary.

        Args:
            tick: Market tick

        Returns:
            Dictionary representation
        """
        return {
            "symbol": tick.symbol,
            "bid": float(tick.bid) if tick.bid else None,
            "ask": float(tick.ask) if tick.ask else None,
            "last": float(tick.last) if tick.last else None,
            "volume": tick.volume,
            "timestamp": tick.timestamp.isoformat() if tick.timestamp else None,
            "latency_ms": tick.latency_ms
        }

    async def _store_ticks(self, ticks: list[MarketTick]) -> None:
        """Store ticks in database.

        Args:
            ticks: List of market ticks
        """
        try:
            db_manager = get_db_manager()

            with db_manager.session() as session:
                for tick in ticks:
                    # For 1-second bars, aggregate ticks
                    bar = MarketBar(
                        symbol=tick.symbol,
                        timestamp=tick.timestamp or datetime.utcnow(),
                        open=tick.last or tick.bid or Decimal('0'),
                        high=tick.last or tick.bid or Decimal('0'),
                        low=tick.last or tick.bid or Decimal('0'),
                        close=tick.last or tick.bid or Decimal('0'),
                        volume=tick.volume or 0,
                        bid=tick.bid,
                        ask=tick.ask,
                        source=tick.source or self.name
                    )
                    session.add(bar)

                session.commit()

        except Exception as e:
            logger.error(f"Failed to store ticks: {e}")

    def get_latest_tick(self, symbol: str) -> MarketTick | None:
        """Get latest tick for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest market tick or None
        """
        return self.symbol_cache.get(symbol)

    def get_metrics(self) -> dict[str, Any]:
        """Get stream metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "status": self.metrics.status.value,
            "connected_duration": (
                (datetime.utcnow() - self.metrics.connected_at).total_seconds()
                if self.metrics.connected_at else 0
            ),
            "messages_received": self.metrics.messages_received,
            "messages_dropped": self.metrics.messages_dropped,
            "average_latency_ms": round(self.metrics.average_latency_ms, 2),
            "current_lag_ms": round(self.metrics.current_lag_ms, 2),
            "reconnect_count": self.metrics.reconnect_count,
            "subscribed_symbols": len(self.metrics.subscribed_symbols),
            "buffer_size": len(self.buffer)
        }


class IBKRStreamClient(StreamClient):
    """IBKR-specific stream client implementation."""

    def __init__(self, ibkr_client, **kwargs):
        """Initialize IBKR stream client.

        Args:
            ibkr_client: IBKR API client instance
        """
        super().__init__(name="IBKR_Stream", **kwargs)
        self.ibkr_client = ibkr_client
        self.req_ids: dict[str, int] = {}

    async def connect(self) -> None:
        """Connect to IBKR data stream."""
        if not self.ibkr_client.isConnected():
            raise ConnectionError("IBKR client not connected")

        self.connected = True
        self.metrics.status = StreamStatus.CONNECTED
        self.metrics.connected_at = datetime.utcnow()

        # Start tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._processing_task = asyncio.create_task(self._process_buffer())

        logger.info("IBKR stream client connected")

    async def _handle_subscription(self, symbols: list[str]) -> None:
        """Handle subscription to IBKR market data."""
        for symbol in symbols:
            if symbol not in self.req_ids:
                req_id = self._get_next_req_id()
                self.req_ids[symbol] = req_id

                # Create contract
                from ibapi.contract import Contract
                contract = Contract()
                contract.symbol = symbol
                contract.secType = "STK"
                contract.exchange = "SMART"
                contract.currency = "USD"

                # Request real-time bars (5 second bars are minimum for live)
                self.ibkr_client.reqRealTimeBars(
                    req_id,
                    contract,
                    5,  # Bar size in seconds
                    "TRADES",
                    False,
                    []
                )

    def _get_next_req_id(self) -> int:
        """Get next request ID."""
        return max(self.req_ids.values(), default=0) + 1


class TradeRepublicStreamClient(StreamClient):
    """Trade Republic-specific stream client implementation."""

    def __init__(self, ws_connection, **kwargs):
        """Initialize Trade Republic stream client.

        Args:
            ws_connection: WebSocket connection
        """
        super().__init__(name="TR_Stream", **kwargs)
        self.ws = ws_connection

    async def connect(self) -> None:
        """Connect to Trade Republic data stream."""
        if not self.ws or self.ws.closed:
            raise ConnectionError("WebSocket not connected")

        self.connected = True
        self.metrics.status = StreamStatus.CONNECTED
        self.metrics.connected_at = datetime.utcnow()

        # Start tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._processing_task = asyncio.create_task(self._process_buffer())

        # Start listening
        asyncio.create_task(self._listen())

        logger.info("Trade Republic stream client connected")

    async def _listen(self) -> None:
        """Listen for WebSocket messages."""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except Exception as e:
            logger.error(f"Stream listening error: {e}")
            self.connected = False
            await self._reconnect()

    async def _handle_message(self, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "ticker":
                tick = MarketTick(
                    symbol=data.get("symbol"),
                    bid=Decimal(str(data.get("bid", 0))),
                    ask=Decimal(str(data.get("ask", 0))),
                    last=Decimal(str(data.get("last", 0))),
                    volume=data.get("volume"),
                    timestamp=datetime.fromisoformat(data.get("timestamp")),
                    source="trade_republic"
                )
                self.process_tick(tick)

        except Exception as e:
            logger.error(f"Message handling error: {e}")

    async def _handle_subscription(self, symbols: list[str]) -> None:
        """Handle subscription to Trade Republic market data."""
        if self.ws and not self.ws.closed:
            subscribe_msg = {
                "type": "subscribe",
                "symbols": symbols
            }
            await self.ws.send(json.dumps(subscribe_msg))

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to Trade Republic."""
        if self.ws and not self.ws.closed:
            await self.ws.send(json.dumps({"type": "ping"}))