"""Trade Republic Broker Adapter (Unofficial/Private API).

IMPORTANT: This uses unofficial/private APIs. Use at your own risk.
Trade Republic does not provide official API support for third-party applications.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import aiohttp
import websockets

from src.common.logging_setup import log_order_action
from src.database.models import OrderSide, OrderStatus

from .base import (
    Balance,
    BrokerAdapter,
    BrokerConnectionError,
    FeeModel,
    OrderRequest,
    OrderResponse,
    OrderValidationError,
    Position,
)

logger = logging.getLogger(__name__)


class TradeRepublicAdapter(BrokerAdapter):
    """Trade Republic broker adapter using unofficial API.

    WARNING: This implementation uses unofficial/private APIs that may:
    - Change without notice
    - Violate Terms of Service
    - Result in account suspension
    - Not work reliably

    Use at your own risk. Consider using IBKR for production trading.
    """

    BASE_URL = "https://api.traderepublic.com"
    WS_URL = "wss://api.traderepublic.com"

    def __init__(self, phone_number: str, pin: str, **kwargs):
        """Initialize Trade Republic adapter.

        Args:
            phone_number: Phone number for authentication
            pin: PIN for authentication
            **kwargs: Additional arguments for base class
        """
        # Set up fee model for Trade Republic (€1 flat fee)
        if 'fee_model' not in kwargs:
            kwargs['fee_model'] = FeeModel(
                broker="trade_republic",
                fee_type="flat",
                flat_fee=Decimal('1.00')
            )

        super().__init__(name="TradeRepublic", **kwargs)

        self.phone_number = phone_number
        self.pin = pin
        self.session_token: str | None = None
        self.device_id = str(uuid4())
        self.ws: websockets.WebSocketClientProtocol | None = None
        self._heartbeat_task: asyncio.Task | None = None

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests

        # ISIN to symbol mapping cache
        self.symbol_cache: dict[str, str] = {}

        logger.warning(
            "Trade Republic adapter initialized. "
            "WARNING: This uses unofficial APIs. "
            "Your account may be suspended for violating ToS."
        )

    # ==================== Template Method Implementations ====================

    async def _establish_connection(self) -> None:
        """Establish connection to Trade Republic (template method implementation)."""
        # Authenticate
        await self._authenticate()

        # Connect WebSocket
        await self._connect_websocket()

    async def _setup_initial_state(self) -> None:
        """Set up initial state after connection (template method implementation)."""
        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Trade Republic heartbeat started")

    async def _authenticate(self) -> None:
        """Authenticate with Trade Republic."""
        # Rate limiting
        await self._rate_limit()

        async with aiohttp.ClientSession() as session:
            # Step 1: Request PIN verification
            auth_data = {
                "phoneNumber": self.phone_number,
                "pin": self.pin,
                "deviceId": self.device_id
            }

            try:
                async with session.post(
                    f"{self.BASE_URL}/api/v1/auth/login",
                    json=auth_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session_token = data.get("sessionToken")
                        logger.info("Authentication successful")
                    else:
                        error = await response.text()
                        raise BrokerConnectionError(
                            "AUTH_FAILED",
                            f"Authentication failed: {error}"
                        )
            except aiohttp.ClientError as e:
                raise BrokerConnectionError("NETWORK_ERROR", str(e))

    async def _connect_websocket(self) -> None:
        """Connect to Trade Republic WebSocket."""
        if not self.session_token:
            raise BrokerConnectionError("NO_SESSION", "Not authenticated")

        headers = {
            "Authorization": f"Bearer {self.session_token}"
        }

        try:
            self.ws = await websockets.connect(
                self.WS_URL,
                extra_headers=headers
            )
            logger.info("WebSocket connected")

            # Start listening for messages
            asyncio.create_task(self._listen_websocket())

        except Exception as e:
            raise BrokerConnectionError("WS_CONNECT", str(e))

    async def _listen_websocket(self) -> None:
        """Listen for WebSocket messages."""
        if not self.ws:
            return

        try:
            async for message in self.ws:
                await self._handle_ws_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self._connected = False
            # Attempt reconnection
            await self._reconnect()

    async def _handle_ws_message(self, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "ticker":
                # Handle price updates
                await self._handle_ticker(data)
            elif msg_type == "order_update":
                # Handle order status updates
                await self._handle_order_update(data)
            elif msg_type == "error":
                logger.error(f"WebSocket error: {data}")

        except json.JSONDecodeError:
            logger.error(f"Invalid WebSocket message: {message}")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to keep connection alive."""
        while self._connected:
            try:
                if self.ws and not self.ws.closed:
                    await self.ws.send(json.dumps({"type": "heartbeat"}))
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                break

    async def _reconnect(self) -> None:
        """Reconnect with exponential backoff."""
        for attempt in range(5):
            wait_time = 2 ** attempt
            logger.info(f"Reconnecting in {wait_time} seconds...")
            await asyncio.sleep(wait_time)

            try:
                await self.connect()
                logger.info("Reconnection successful")
                return
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")

        logger.error("Failed to reconnect after 5 attempts")

    async def _cleanup_resources(self) -> None:
        """Clean up Trade Republic resources (template method implementation)."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()

    async def is_connected(self) -> bool:
        """Check if connected to Trade Republic."""
        return self._connected and self.ws and not self.ws.closed

    async def _place_order_impl(
        self,
        order: OrderRequest,
        estimated_fee: Decimal
    ) -> OrderResponse:
        """Place order with Trade Republic."""
        await self._rate_limit()

        # Generate idempotency key for retry safety
        idempotency_key = str(uuid4())

        # Map symbol to ISIN if needed
        isin = await self._get_isin(order.symbol)

        # Build order payload
        order_payload = {
            "isin": isin,
            "side": order.side.value.lower(),
            "orderType": self._map_order_type(order.order_type),
            "quantity": int(order.quantity),
            "venue": "LSX",  # Default to Lang & Schwarz
            "idempotencyKey": idempotency_key
        }

        if order.limit_price:
            order_payload["limitPrice"] = float(order.limit_price)
        if order.stop_price:
            order_payload["stopPrice"] = float(order.stop_price)

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }

            try:
                async with session.post(
                    f"{self.BASE_URL}/api/v1/orders",
                    json=order_payload,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        data = await response.json()

                        # Log order action
                        log_order_action(
                            action="placed",
                            order_id=data.get("orderId"),
                            symbol=order.symbol,
                            details={
                                "broker": "trade_republic",
                                "isin": isin,
                                "ai_analysis": order.ai_analysis
                            }
                        )

                        return OrderResponse(
                            broker_order_id=data.get("orderId"),
                            internal_order_id=order.internal_order_id or idempotency_key,
                            status=OrderStatus.SUBMITTED,
                            symbol=order.symbol,
                            side=order.side,
                            order_type=order.order_type,
                            quantity=order.quantity,
                            created_at=datetime.utcnow(),
                            submitted_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            estimated_fee=estimated_fee
                        )
                    else:
                        error = await response.text()
                        raise OrderValidationError(
                            "ORDER_REJECTED",
                            f"Order rejected: {error}"
                        )

            except aiohttp.ClientError as e:
                raise BrokerConnectionError("NETWORK_ERROR", str(e))

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        await self._rate_limit()

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }

            try:
                async with session.delete(
                    f"{self.BASE_URL}/api/v1/orders/{order_id}",
                    headers=headers
                ) as response:
                    return response.status == 200

            except aiohttp.ClientError as e:
                logger.error(f"Failed to cancel order: {e}")
                return False

    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get current order status."""
        await self._rate_limit()

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }

            try:
                async with session.get(
                    f"{self.BASE_URL}/api/v1/orders/{order_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_order_response(data)
                    else:
                        raise ValueError(f"Order not found: {order_id}")

            except aiohttp.ClientError as e:
                raise BrokerConnectionError("NETWORK_ERROR", str(e))

    async def get_positions(self) -> list[Position]:
        """Get all current positions."""
        await self._rate_limit()

        positions = []

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }

            try:
                async with session.get(
                    f"{self.BASE_URL}/api/v1/portfolio/positions",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        for pos_data in data.get("positions", []):
                            positions.append(self._parse_position(pos_data))

            except aiohttp.ClientError as e:
                logger.error(f"Failed to get positions: {e}")

        return positions

    async def get_balance(self) -> Balance:
        """Get account balance."""
        await self._rate_limit()

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }

            try:
                async with session.get(
                    f"{self.BASE_URL}/api/v1/account/cash",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        return Balance(
                            cash=Decimal(str(data.get("availableCash", 0))),
                            market_value=Decimal(str(data.get("portfolioValue", 0))),
                            total_equity=Decimal(str(data.get("totalValue", 0))),
                            buying_power=Decimal(str(data.get("buyingPower", 0))),
                            daily_pnl=Decimal(str(data.get("dailyPnl", 0)))
                        )

            except aiohttp.ClientError as e:
                logger.error(f"Failed to get balance: {e}")
                raise BrokerConnectionError("NETWORK_ERROR", str(e))

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    async def _get_isin(self, symbol: str) -> str:
        """Convert symbol to ISIN."""
        # Check cache first
        if symbol in self.symbol_cache:
            return self.symbol_cache[symbol]

        # For now, return symbol as-is (should implement proper lookup)
        # In production, would query TR API for symbol resolution
        logger.warning(f"ISIN lookup not implemented for {symbol}")
        return symbol

    def _map_order_type(self, order_type) -> str:
        """Map internal order type to TR API format."""
        mapping = {
            "limit": "limit",
            "market": "market",
            "stop": "stop",
            "stop_limit": "stopLimit"
        }
        return mapping.get(order_type.value, "limit")

    def _parse_order_response(self, data: dict[str, Any]) -> OrderResponse:
        """Parse order response from API."""
        status_map = {
            "open": OrderStatus.SUBMITTED,
            "executed": OrderStatus.FILLED,
            "cancelled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED
        }

        return OrderResponse(
            broker_order_id=data.get("orderId"),
            internal_order_id=data.get("clientOrderId"),
            status=status_map.get(data.get("status"), OrderStatus.PENDING),
            symbol=data.get("symbol"),
            side=OrderSide.BUY if data.get("side") == "buy" else OrderSide.SELL,
            order_type=data.get("orderType"),
            quantity=Decimal(str(data.get("quantity", 0))),
            filled_quantity=Decimal(str(data.get("filledQuantity", 0))),
            average_fill_price=Decimal(str(data.get("averagePrice", 0))) if data.get("averagePrice") else None,
            created_at=datetime.fromisoformat(data.get("createdAt")),
            updated_at=datetime.utcnow()
        )

    def _parse_position(self, data: dict[str, Any]) -> Position:
        """Parse position from API response."""
        return Position(
            symbol=data.get("symbol"),
            quantity=Decimal(str(data.get("quantity", 0))),
            average_cost=Decimal(str(data.get("averageCost", 0))),
            current_price=Decimal(str(data.get("currentPrice", 0))) if data.get("currentPrice") else None,
            market_value=Decimal(str(data.get("marketValue", 0))) if data.get("marketValue") else None,
            unrealized_pnl=Decimal(str(data.get("unrealizedPnl", 0))) if data.get("unrealizedPnl") else None
        )

    async def _handle_ticker(self, data: dict[str, Any]) -> None:
        """Handle ticker updates from WebSocket."""
        # Implement ticker handling
        pass

    async def _handle_order_update(self, data: dict[str, Any]) -> None:
        """Handle order status updates from WebSocket."""
        # Implement order update handling
        pass