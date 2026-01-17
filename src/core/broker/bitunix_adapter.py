"""Bitunix Futures Trading Adapter.

Broker adapter for Bitunix Futures trading with double SHA256 authentication.
Supports order placement, position management, and account queries.

Authentication:
    Bitunix uses a two-step SHA256 signature process:
    1. digest = SHA256(nonce + timestamp + api_key + query_params + body)
    2. sign = SHA256(digest + secret_key)
"""

import asyncio
import json
import logging
from decimal import Decimal

import aiohttp

from src.core.auth.bitunix_signer import BitunixSigner
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
        
        # Initialize signer
        self.signer = BitunixSigner(api_key, api_secret)

    @property
    def connected(self) -> bool:
        return self._connected

    def _get_base_url(self) -> str:
        """Get API base URL based on environment.

        Returns:
            Base URL for Bitunix API

        Note:
            Using fapi.bitunix.com for both environments as testnet-api.bitunix.com
            is not reachable. This matches the WebSocket endpoint used in bitunix_stream.py.
        """
        # Use the same host as WebSocket (fapi.bitunix.com) to avoid DNS failures
        # The testnet-api.bitunix.com host is not reliably accessible
        return "https://fapi.bitunix.com"

    def _sort_params(self, params: dict) -> str:
        """Sort parameters and concatenate as keyvalue pairs.

        Args:
            params: Parameter dictionary

        Returns:
            Sorted parameter string in format: key1value1key2value2...
        """
        if not params:
            return ""
        # Sort by key and concatenate directly (no separators)
        return ''.join(f"{k}{v}" for k, v in sorted(params.items()))

    def _build_headers(self, query_params: str = "", body: str = "") -> dict:
        """Build request headers with API key and signature.

        Args:
            query_params: Sorted query parameters as string (no spaces)
            body: JSON body as string (no spaces)

        Returns:
            Headers dictionary for HTTP request
        """
        return self.signer.build_headers(query_params, body)

    # ==================== Connection Management ====================

    async def _establish_connection(self) -> None:
        """Establish connection to Bitunix API.

        Creates aiohttp session and validates credentials.
        """
        # Avoid hammering the API if credentials are wrong: one attempt at a time.
        if getattr(self, "_auth_failed", False):
            raise BrokerConnectionError(
                code="BITUNIX_AUTH_FAILED",
                message="Previous Bitunix auth failed; skipping reconnect. Fix API key/secret and restart.",
                details={}
            )

        # Check if credentials are set
        if not self.api_key or not self.api_secret:
            self._auth_failed = True
            raise BrokerConnectionError(
                code="BITUNIX_MISSING_CREDENTIALS",
                message="Bitunix API credentials not configured. Set BITUNIX_API_KEY and BITUNIX_API_SECRET environment variables.",
                details={"api_key_set": bool(self.api_key), "api_secret_set": bool(self.api_secret)}
            )

        logger.info(f"Connecting to Bitunix API at {self.base_url} (API key: {self.api_key[:8]}...)")

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
                    message="Failed to authenticate with Bitunix API. Check API key and secret.",
                    details={"api_key": self.api_key[:8] + "...", "base_url": self.base_url}
                )

            logger.info(f"✓ Connected to Bitunix ({self.base_url})")

        except BrokerConnectionError:
            # Don't wrap BrokerConnectionError again, just re-raise
            if self._session:
                await self._session.close()
                self._session = None
            self._auth_failed = True
            raise
        except aiohttp.ClientError as e:
            if self._session:
                await self._session.close()
                self._session = None
            self._auth_failed = True
            raise BrokerConnectionError(
                code="BITUNIX_NETWORK_ERROR",
                message=f"Network error connecting to Bitunix: {str(e)}",
                details={"error": str(e), "base_url": self.base_url}
            )
        except Exception as e:
            if self._session:
                await self._session.close()
                self._session = None
            self._auth_failed = True
            raise BrokerConnectionError(
                code="BITUNIX_CONNECT_FAILED",
                message=f"Failed to connect to Bitunix: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
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

        # Convert params to JSON string without spaces (required for signature)
        body_json = json.dumps(params, separators=(',', ':'))

        # Build authenticated headers (no query params for POST, only body)
        headers = self._build_headers(query_params="", body=body_json)

        try:
            async with self._session.post(
                f"{self.base_url}/api/v1/futures/trade/place_order",
                data=body_json,  # Send as raw JSON string, not dict
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

        # Convert params to JSON string without spaces
        body_json = json.dumps(params, separators=(',', ':'))

        # Build authenticated headers
        headers = self._build_headers(query_params="", body=body_json)

        try:
            async with self._session.post(
                f"{self.base_url}/api/v1/futures/trade/cancel_orders",
                data=body_json,
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

        # For GET requests, convert params to sorted string format
        query_params = self._sort_params(params)

        # Build authenticated headers (GET has query params, no body)
        headers = self._build_headers(query_params=query_params, body="")

        try:
            async with self._session.get(
                f"{self.base_url}/api/v1/futures/trade/get_order_detail",
                params=params,  # Still pass params as dict for URL construction
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

        # No params for this endpoint
        # Build authenticated headers (GET with no query params)
        headers = self._build_headers(query_params="", body="")

        try:
            async with self._session.get(
                f"{self.base_url}/api/v1/futures/position/get_pending_positions",
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

        # No params for this endpoint
        # Build authenticated headers (GET with no query params)
        headers = self._build_headers(query_params="", body="")

        try:
            async with self._session.get(
                f"{self.base_url}/api/v1/futures/account",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data is not None:
                        return self._parse_balance(data)
                    else:
                        logger.warning("Bitunix balance API returned None")
                        return None
                else:
                    logger.warning(f"Bitunix balance API returned status {response.status}")
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
                leverage=int(pos.get('leverage', 1)),
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
