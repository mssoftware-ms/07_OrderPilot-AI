"""
Binance Force Order WebSocket Client

Connects to Binance USD-M Futures liquidation stream and parses events.
Implements robust reconnection with exponential backoff and 24h reconnect.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import random

import websockets
from websockets.client import WebSocketClientProtocol


logger = logging.getLogger(__name__)


@dataclass
class LiquidationEvent:
    """Parsed liquidation event from Binance forceOrder stream."""

    ts_ms: int  # Event timestamp in milliseconds
    symbol: str  # Trading pair (e.g., BTCUSDT)
    side: str  # BUY (long liquidation) or SELL (short liquidation)
    price: float  # Liquidation price
    qty: float  # Quantity liquidated
    notional: float  # price * qty
    source: str  # Always "BINANCE_USDM" for this implementation
    raw_json: str  # Original payload for debugging/replay

    @classmethod
    def from_binance_payload(cls, payload: Dict[str, Any]) -> "LiquidationEvent":
        """
        Parse Binance forceOrder payload into internal event model.

        Example payload:
        {
            "e": "forceOrder",
            "E": 1668680518494,  # Event time
            "o": {
                "s": "BTCUSDT",
                "S": "SELL",  # Side of the taker
                "o": "LIMIT",
                "f": "IOC",
                "q": "0.014",
                "p": "15479.50",
                "ap": "15479.50",  # Average price
                "X": "FILLED",
                "l": "0.014",
                "z": "0.014",
                "T": 1668680518494
            }
        }
        """
        try:
            order = payload.get("o", {})

            symbol = order.get("s", "")
            side = order.get("S", "")  # BUY or SELL
            price = float(order.get("p", 0))
            qty = float(order.get("q", 0))
            ts_ms = payload.get("E", 0)

            if not all([symbol, side, price > 0, qty > 0, ts_ms > 0]):
                raise ValueError(f"Invalid event data: {payload}")

            return cls(
                ts_ms=ts_ms,
                symbol=symbol,
                side=side,
                price=price,
                qty=qty,
                notional=price * qty,
                source="BINANCE_USDM",
                raw_json=json.dumps(payload),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse Binance payload: {e}, payload: {payload}")
            raise


class BinanceForceOrderClient:
    """
    WebSocket client for Binance USD-M Futures liquidation stream.

    Features:
    - Auto-reconnect with exponential backoff and jitter
    - Ping/pong keepalive handling
    - 24-hour automatic reconnection (Binance limit)
    - Clean shutdown support
    """

    BASE_URL = "wss://fstream.binance.com/ws"
    MAX_CONNECTION_LIFETIME = 23.5 * 3600  # 23.5 hours in seconds (reconnect before 24h)
    INITIAL_RECONNECT_DELAY = 1.0  # seconds
    MAX_RECONNECT_DELAY = 60.0  # seconds
    BACKOFF_MULTIPLIER = 2.0
    JITTER_FACTOR = 0.1

    def __init__(
        self,
        symbol: str = "btcusdt",
        on_event: Optional[Callable[[LiquidationEvent], None]] = None,
    ):
        """
        Initialize WebSocket client.

        Args:
            symbol: Trading pair symbol (lowercase, e.g., 'btcusdt')
            on_event: Callback function called for each parsed event
        """
        self.symbol = symbol.lower()
        self.stream_name = f"{self.symbol}@forceOrder"
        self.url = f"{self.BASE_URL}/{self.stream_name}"
        self.on_event = on_event

        self._ws: Optional[WebSocketClientProtocol] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._reconnect_delay = self.INITIAL_RECONNECT_DELAY
        self._connection_start_time: Optional[float] = None

    async def start(self) -> None:
        """Start the WebSocket client (runs in background task)."""
        if self._running:
            logger.warning("Client already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Started Binance forceOrder client for {self.symbol}")

    async def stop(self) -> None:
        """Stop the WebSocket client gracefully."""
        if not self._running:
            return

        logger.info("Stopping Binance forceOrder client...")
        self._running = False

        if self._ws:
            await self._ws.close()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Binance forceOrder client stopped")

    def is_running(self) -> bool:
        """Check if client is running."""
        return self._running

    async def _run_loop(self) -> None:
        """Main event loop with reconnection logic."""
        while self._running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                logger.info("Client task cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in run loop: {e}", exc_info=True)

            if self._running:
                # Calculate backoff with jitter
                delay = self._reconnect_delay
                jitter = delay * self.JITTER_FACTOR * (2 * random.random() - 1)
                delay_with_jitter = max(0.1, delay + jitter)

                logger.info(f"Reconnecting in {delay_with_jitter:.1f}s...")
                await asyncio.sleep(delay_with_jitter)

                # Exponential backoff
                self._reconnect_delay = min(
                    self._reconnect_delay * self.BACKOFF_MULTIPLIER,
                    self.MAX_RECONNECT_DELAY
                )

    async def _connect_and_listen(self) -> None:
        """Establish connection and listen for messages."""
        logger.info(f"Connecting to {self.url}...")

        async with websockets.connect(
            self.url,
            ping_interval=20,  # Send ping every 20 seconds
            ping_timeout=10,   # Wait 10 seconds for pong
            close_timeout=5,
        ) as ws:
            self._ws = ws
            self._connection_start_time = time.time()
            self._reconnect_delay = self.INITIAL_RECONNECT_DELAY  # Reset on successful connect

            logger.info(f"Connected to {self.stream_name}")

            # Listen for messages until connection lifetime expires or error occurs
            while self._running:
                # Check if we need to reconnect (before 24h limit)
                elapsed = time.time() - self._connection_start_time
                if elapsed >= self.MAX_CONNECTION_LIFETIME:
                    logger.info("Connection lifetime reached (23.5h), reconnecting...")
                    break

                try:
                    # Wait for message with timeout
                    timeout = self.MAX_CONNECTION_LIFETIME - elapsed
                    message = await asyncio.wait_for(
                        ws.recv(),
                        timeout=min(timeout, 30)  # Check every 30s max
                    )

                    await self._handle_message(message)

                except asyncio.TimeoutError:
                    # No message in timeout window, continue loop
                    continue
                except websockets.ConnectionClosed as e:
                    logger.warning(f"Connection closed: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}", exc_info=True)
                    break

    async def _handle_message(self, message: str) -> None:
        """Parse and process incoming WebSocket message."""
        try:
            payload = json.loads(message)

            # Binance sends both forceOrder events and ping/pong messages
            event_type = payload.get("e")

            if event_type == "forceOrder":
                event = LiquidationEvent.from_binance_payload(payload)

                if self.on_event:
                    # Call callback (should be non-blocking)
                    if asyncio.iscoroutinefunction(self.on_event):
                        await self.on_event(event)
                    else:
                        self.on_event(event)

                logger.debug(
                    f"Liquidation: {event.symbol} {event.side} "
                    f"{event.qty}@{event.price} = ${event.notional:.2f}"
                )
            else:
                # Unknown event type, log for debugging
                logger.debug(f"Received non-forceOrder event: {event_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message JSON: {e}, message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)


# Example usage
async def _example():
    """Example usage of BinanceForceOrderClient."""

    def on_liquidation(event: LiquidationEvent):
        print(f"[{datetime.fromtimestamp(event.ts_ms / 1000)}] "
              f"{event.symbol} {event.side} {event.qty}@{event.price}")

    client = BinanceForceOrderClient(symbol="btcusdt", on_event=on_liquidation)

    try:
        await client.start()
        # Run for 1 hour
        await asyncio.sleep(3600)
    finally:
        await client.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    asyncio.run(_example())
