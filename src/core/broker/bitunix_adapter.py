"""Bitunix Futures Trading Adapter.

Broker adapter for Bitunix Futures trading with HMAC authentication.
Supports order placement, position management, and account queries.
"""

import asyncio
import hashlib
import hmac
import logging
import time
from decimal import Decimal

import aiohttp

from src.core.broker.base import BrokerAdapter
from src.core.broker.broker_types import (
    Balance,
    BrokerConnectionError,
    BrokerError,
    FeeModel,
    OrderRequest,
    OrderResponse,
    Position,
)
from src.database.models import OrderSide, OrderStatus, OrderType as DBOrderType

logger = logging.getLogger(__name__)


class BitunixAdapter(BrokerAdapter):
    """Bitunix Futures trading adapter.

    Provides trading functionality for Bitunix Futures (Perpetual Contracts).

    Features:
        - HMAC-SHA256 authenticated requests
        - Market and Limit orders
        - Position management
        - Account balance queries
        - Testnet/Mainnet support

    Environments:
        - Testnet: https://testnet-api.bitunix.com
        - Mainnet: https://api.bitunix.com

    Fee Model:
        - Maker: 0.02% (0.0002)
        - Taker: 0.06% (0.0006)
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        use_testnet: bool = True,
        fee_model: FeeModel | None = None
    ):
        """Initialize Bitunix adapter.

        Args:
            api_key: Bitunix API key
            api_secret: Bitunix API secret
            use_testnet: Use testnet environment (default: True for safety)
            fee_model: Custom fee model (optional)
        """
        # Default Bitunix fee model
        if not fee_model:
            fee_model = FeeModel(
                broker="bitunix",
                fee_type="percentage",
                maker_fee=Decimal("0.0002"),  # 0.02%
                taker_fee=Decimal("0.0006")   # 0.06%
            )

        super().__init__(name="Bitunix", fee_model=fee_model)

        self.api_key = api_key
        self.api_secret = api_secret
        self.use_testnet = use_testnet
        self.base_url = self._get_base_url()
        self._session: aiohttp.ClientSession | None = None

    def _get_base_url(self) -> str:
        """Get API base URL based on environment.

        Returns:
            Base URL for Bitunix API
        """
        if self.use_testnet:
            return "https://testnet-api.bitunix.com"
        return "https://api.bitunix.com"

    def _generate_signature(self, params: dict) -> str:
        """Generate HMAC-SHA256 signature for Bitunix API.

        Args:
            params: Request parameters

        Returns:
            Hex-encoded signature string
        """
        # Sort parameters alphabetically
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _build_headers(self, params: dict) -> dict:
        """Build request headers with API key and signature.

        Args:
            params: Request parameters (will be modified with timestamp)

        Returns:
            Headers dictionary for HTTP request
        """
        # Add timestamp (required for signature)
        params['timestamp'] = int(time.time() * 1000)

        # Generate signature
        signature = self._generate_signature(params)

        return {
            'X-API-KEY': self.api_key,
            'X-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }

    # ==================== Connection Management ====================

    async def _establish_connection(self) -> None:
        """Establish connection to Bitunix API.

        Creates aiohttp session and validates credentials.
        """
        try:
            # Create aiohttp session
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

            # Validate connection by fetching account info
            balance = await self.get_balance()
            if not balance:
                raise BrokerConnectionError(
                    code="BITUNIX_AUTH_FAILED",
                    message="Failed to authenticate with Bitunix API",
                    details={"api_key": self.api_key[:8] + "..."}
                )

            logger.info(f"✓ Connected to Bitunix ({self.base_url})")

        except Exception as e:
            if self._session:
                await self._session.close()
                self._session = None
            raise BrokerConnectionError(
                code="BITUNIX_CONNECT_FAILED",
                message=f"Failed to connect to Bitunix: {str(e)}",
                details={"error": str(e)}
            )

    async def _cleanup_resources(self) -> None:
        """Clean up resources on disconnect."""
        if self._session:
            await self._session.close()
            self._session = None

    # ==================== Order Management ====================

    async def _place_order_impl(
        self,
        order: OrderRequest,
        estimated_fee: Decimal
    ) -> OrderResponse:
        """Place order on Bitunix.

        Args:
            order: Order request
            estimated_fee: Estimated fee for the order

        Returns:
            Order response with broker order ID

        Raises:
            BrokerError: If order placement fails
        """
        if not self._session:
            raise BrokerConnectionError(
                code="BITUNIX_NOT_CONNECTED",
                message="Not connected to Bitunix"
            )

        # Build order parameters
        params = {
            'symbol': order.symbol,
            'side': self._map_order_side(order.side),
            'type': self._map_order_type(order.order_type),
            'quantity': str(order.quantity),
        }

        # Add price for limit orders
        if order.order_type == DBOrderType.LIMIT:
            if not order.limit_price:
                raise BrokerError(
                    code="BITUNIX_INVALID_ORDER",
                    message="Limit price required for limit orders"
                )
            params['price'] = str(order.limit_price)

        # Build authenticated headers
        headers = self._build_headers(params.copy())

        try:
            async with self._session.post(
                f"{self.base_url}/api/v1/futures/trade/place_order",
                json=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_order_response(data, order)
                else:
                    error_text = await response.text()
                    raise BrokerError(
                        code="BITUNIX_ORDER_FAILED",
                        message=f"Order placement failed: {error_text}",
                        details={"status": response.status, "response": error_text}
                    )

        except aiohttp.ClientError as e:
            raise BrokerError(
                code="BITUNIX_NETWORK_ERROR",
                message=f"Network error during order placement: {str(e)}",
                details={"error": str(e)}
            )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Broker order ID

        Returns:
            True if cancellation successful
        """
        if not self._session:
            return False

        params = {
            'orderId': order_id,
        }

        headers = self._build_headers(params.copy())

        try:
            async with self._session.post(
                f"{self.base_url}/api/v1/futures/trade/cancel_orders",
                json=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('code') == 0
                return False

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get current order status.

        Args:
            order_id: Broker order ID

        Returns:
            Current order information
        """
        if not self._session:
            raise BrokerConnectionError(
                code="BITUNIX_NOT_CONNECTED",
                message="Not connected to Bitunix"
            )

        params = {
            'orderId': order_id,
        }

        headers = self._build_headers(params.copy())

        try:
            async with self._session.get(
                f"{self.base_url}/api/v1/futures/trade/get_order_detail",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Parse order details from response
                    order_data = data.get('data', {})
                    return OrderResponse(
                        broker_order_id=order_data.get('orderId'),
                        status=self._parse_order_status(order_data.get('status')),
                        symbol=order_data.get('symbol'),
                        side=self._parse_order_side(order_data.get('side')),
                        quantity=Decimal(str(order_data.get('quantity', 0))),
                        filled_quantity=Decimal(str(order_data.get('filledQuantity', 0))),
                        average_price=Decimal(str(order_data.get('avgPrice', 0))),
                        message="Order status retrieved"
                    )
                else:
                    raise BrokerError(
                        code="BITUNIX_ORDER_STATUS_FAILED",
                        message=f"Failed to get order status: {response.status}"
                    )

        except Exception as e:
            raise BrokerError(
                code="BITUNIX_ORDER_STATUS_ERROR",
                message=f"Error getting order status: {str(e)}",
                details={"error": str(e)}
            )

    # ==================== Account Information ====================

    async def get_positions(self) -> list[Position]:
        """Get all current positions.

        Returns:
            List of open positions
        """
        if not self._session:
            return []

        params = {}
        headers = self._build_headers(params.copy())

        try:
            async with self._session.get(
                f"{self.base_url}/api/v1/futures/position/get_pending_positions",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_positions(data)
                return []

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    async def get_balance(self) -> Balance | None:
        """Get account balance.

        Returns:
            Account balance information
        """
        if not self._session:
            return None

        params = {}
        headers = self._build_headers(params.copy())

        try:
            async with self._session.get(
                f"{self.base_url}/api/v1/futures/account",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_balance(data)
                return None

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return None

    # ==================== Helper Methods ====================

    def _map_order_side(self, side: OrderSide) -> str:
        """Map OrderSide enum to Bitunix side string."""
        mapping = {
            OrderSide.BUY: "buy",
            OrderSide.SELL: "sell",
        }
        return mapping.get(side, "buy")

    def _map_order_type(self, order_type: DBOrderType) -> str:
        """Map OrderType enum to Bitunix order type string."""
        mapping = {
            DBOrderType.MARKET: "market",
            DBOrderType.LIMIT: "limit",
        }
        return mapping.get(order_type, "market")

    def _parse_order_side(self, side_str: str) -> OrderSide:
        """Parse Bitunix side string to OrderSide enum."""
        mapping = {
            "buy": OrderSide.BUY,
            "sell": OrderSide.SELL,
        }
        return mapping.get(side_str.lower(), OrderSide.BUY)

    def _parse_order_status(self, status_str: str) -> OrderStatus:
        """Parse Bitunix status string to OrderStatus enum."""
        mapping = {
            "pending": OrderStatus.PENDING_SUBMIT,
            "submitted": OrderStatus.SUBMITTED,
            "partial_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "cancelled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }
        return mapping.get(status_str.lower(), OrderStatus.PENDING_SUBMIT)

    def _parse_order_response(self, data: dict, original_order: OrderRequest) -> OrderResponse:
        """Parse Bitunix order response to OrderResponse.

        Args:
            data: API response data
            original_order: Original order request

        Returns:
            Parsed order response
        """
        order_data = data.get('data', {})

        return OrderResponse(
            broker_order_id=order_data.get('orderId'),
            status=OrderStatus.SUBMITTED,  # Newly placed order
            symbol=original_order.symbol,
            side=original_order.side,
            quantity=original_order.quantity,
            filled_quantity=Decimal("0"),
            average_price=Decimal("0"),
            message="Order placed successfully"
        )

    def _parse_positions(self, data: dict) -> list[Position]:
        """Parse Bitunix positions response.

        Args:
            data: API response data

        Returns:
            List of Position objects
        """
        positions = []
        position_data = data.get('data', [])

        for pos in position_data:
            positions.append(Position(
                symbol=pos.get('symbol'),
                quantity=Decimal(str(pos.get('quantity', 0))),
                average_cost=Decimal(str(pos.get('avgPrice', 0))),
                current_price=Decimal(str(pos.get('markPrice', 0))),
                market_value=Decimal(str(pos.get('positionValue', 0))),
                unrealized_pnl=Decimal(str(pos.get('unrealizedPnl', 0))),
                pnl_percentage=float(pos.get('pnlPercentage', 0)),
                exchange="bitunix",
                currency="USDT"
            ))

        return positions

    def _parse_balance(self, data: dict) -> Balance:
        """Parse Bitunix balance response.

        Args:
            data: API response data

        Returns:
            Balance object
        """
        account_data = data.get('data', {})

        return Balance(
            currency="USDT",
            cash=Decimal(str(account_data.get('availableBalance', 0))),
            market_value=Decimal(str(account_data.get('positionValue', 0))),
            total_equity=Decimal(str(account_data.get('totalEquity', 0))),
            buying_power=Decimal(str(account_data.get('availableMargin', 0))),
            margin_used=Decimal(str(account_data.get('usedMargin', 0))),
            margin_available=Decimal(str(account_data.get('availableMargin', 0))),
            daily_pnl=Decimal(str(account_data.get('dailyPnl', 0))),
            daily_pnl_percentage=float(account_data.get('dailyPnlPercentage', 0))
        )
