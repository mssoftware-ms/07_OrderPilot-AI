"""Alpaca Broker Adapter for OrderPilot-AI.

Provides integration with Alpaca trading platform for paper and live trading.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest
)
from alpaca.trading.enums import (
    OrderSide as AlpacaOrderSide,
    TimeInForce as AlpacaTimeInForce,
    OrderType as AlpacaOrderType,
    OrderStatus as AlpacaOrderStatus
)

from src.core.broker.base import (
    Balance,
    BrokerAdapter,
    BrokerConnectionError,
    BrokerError,
    FeeModel,
    OrderRequest,
    OrderResponse,
    Position,
)
from src.database.models import OrderSide, OrderStatus, OrderType, TimeInForce

logger = logging.getLogger(__name__)


class AlpacaAdapter(BrokerAdapter):
    """Alpaca broker adapter."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        paper: bool = True,
        **kwargs
    ):
        """Initialize Alpaca adapter.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Use paper trading (default: True)
            **kwargs: Additional arguments passed to BrokerAdapter
        """
        # Create fee model for Alpaca (commission-free)
        fee_model = FeeModel(
            broker="alpaca",
            fee_type="flat",
            flat_fee=Decimal('0'),  # Commission-free trading!
            exchange_fee=Decimal('0'),
            regulatory_fee=Decimal('0.000119')  # SEC fee: $0.0000119 per dollar
        )

        super().__init__(
            broker_name="Alpaca",
            fee_model=fee_model,
            **kwargs
        )

        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper

        # Trading client
        self._client: TradingClient | None = None

        logger.info(f"Alpaca adapter initialized (paper: {paper})")

    # ==================== Template Method Implementations ====================

    async def _establish_connection(self) -> None:
        """Establish connection to Alpaca (template method implementation)."""
        self._client = TradingClient(
            api_key=self.api_key,
            secret_key=self.api_secret,
            paper=self.paper
        )

    async def _verify_connection(self) -> None:
        """Verify Alpaca connection by fetching account info."""
        if not self._client:
            raise BrokerConnectionError(
                code="ALPACA_NO_CLIENT",
                message="Alpaca client not initialized"
            )

        # Test connection
        account = self._client.get_account()
        logger.info(
            f"Alpaca connection verified (account: {account.account_number}, "
            f"status: {account.status})"
        )

    async def _cleanup_resources(self) -> None:
        """Clean up Alpaca resources (template method implementation)."""
        self._client = None

    async def is_connected(self) -> bool:
        """Check if connected to Alpaca.

        Returns:
            True if connected
        """
        if not self._client:
            return False

        try:
            self._client.get_account()
            return True
        except Exception:
            return False

    def _map_order_side(self, side: OrderSide) -> AlpacaOrderSide:
        """Map internal order side to Alpaca order side."""
        mapping = {
            OrderSide.BUY: AlpacaOrderSide.BUY,
            OrderSide.SELL: AlpacaOrderSide.SELL
        }
        return mapping[side]

    def _map_time_in_force(self, tif: TimeInForce) -> AlpacaTimeInForce:
        """Map internal time in force to Alpaca time in force."""
        mapping = {
            TimeInForce.DAY: AlpacaTimeInForce.DAY,
            TimeInForce.GTC: AlpacaTimeInForce.GTC,
            TimeInForce.IOC: AlpacaTimeInForce.IOC,
            TimeInForce.FOK: AlpacaTimeInForce.FOK
        }
        return mapping.get(tif, AlpacaTimeInForce.DAY)

    def _map_order_status(self, status: AlpacaOrderStatus) -> OrderStatus:
        """Map Alpaca order status to internal order status."""
        mapping = {
            AlpacaOrderStatus.NEW: OrderStatus.PENDING,
            AlpacaOrderStatus.ACCEPTED: OrderStatus.SUBMITTED,
            AlpacaOrderStatus.PENDING_NEW: OrderStatus.PENDING,
            AlpacaOrderStatus.ACCEPTED_FOR_BIDDING: OrderStatus.SUBMITTED,
            AlpacaOrderStatus.PARTIALLY_FILLED: OrderStatus.PARTIALLY_FILLED,
            AlpacaOrderStatus.FILLED: OrderStatus.FILLED,
            AlpacaOrderStatus.DONE_FOR_DAY: OrderStatus.FILLED,
            AlpacaOrderStatus.CANCELED: OrderStatus.CANCELLED,
            AlpacaOrderStatus.EXPIRED: OrderStatus.EXPIRED,
            AlpacaOrderStatus.REPLACED: OrderStatus.MODIFIED,
            AlpacaOrderStatus.PENDING_CANCEL: OrderStatus.CANCELLING,
            AlpacaOrderStatus.PENDING_REPLACE: OrderStatus.PENDING,
            AlpacaOrderStatus.REJECTED: OrderStatus.REJECTED,
            AlpacaOrderStatus.SUSPENDED: OrderStatus.REJECTED,
            AlpacaOrderStatus.STOPPED: OrderStatus.CANCELLED,
            AlpacaOrderStatus.CALCULATED: OrderStatus.PENDING,
        }
        return mapping.get(status, OrderStatus.REJECTED)

    async def _place_order_impl(
        self,
        order: OrderRequest,
        estimated_fee: Decimal
    ) -> OrderResponse:
        """Place order on Alpaca.

        Args:
            order: Order request
            estimated_fee: Estimated fee

        Returns:
            Order response
        """
        if not self._client:
            raise BrokerConnectionError(
                code="ALPACA_NOT_CONNECTED",
                message="Not connected to Alpaca"
            )

        try:
            # Map order parameters
            side = self._map_order_side(order.side)
            tif = self._map_time_in_force(order.time_in_force)

            # Create order request based on type
            if order.order_type == OrderType.MARKET:
                alpaca_order = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=side,
                    time_in_force=tif
                )

            elif order.order_type == OrderType.LIMIT:
                alpaca_order = LimitOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=side,
                    time_in_force=tif,
                    limit_price=float(order.limit_price)
                )

            elif order.order_type == OrderType.STOP:
                alpaca_order = StopOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=side,
                    time_in_force=tif,
                    stop_price=float(order.stop_price)
                )

            elif order.order_type == OrderType.STOP_LIMIT:
                alpaca_order = StopLimitOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=side,
                    time_in_force=tif,
                    limit_price=float(order.limit_price),
                    stop_price=float(order.stop_price)
                )

            else:
                raise BrokerError(
                    code="INVALID_ORDER_TYPE",
                    message=f"Unsupported order type: {order.order_type}"
                )

            # Add stop loss and take profit if specified
            if order.stop_loss or order.take_profit:
                alpaca_order.order_class = "bracket"
                if order.stop_loss:
                    alpaca_order.stop_loss = {
                        "stop_price": float(order.stop_loss)
                    }
                if order.take_profit:
                    alpaca_order.take_profit = {
                        "limit_price": float(order.take_profit)
                    }

            # Submit order
            alpaca_response = self._client.submit_order(alpaca_order)

            # Convert to OrderResponse
            response = OrderResponse(
                broker_order_id=alpaca_response.id,
                internal_order_id=order.internal_order_id or alpaca_response.client_order_id,
                status=self._map_order_status(alpaca_response.status),
                symbol=alpaca_response.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=Decimal(str(alpaca_response.qty)),
                filled_quantity=Decimal(str(alpaca_response.filled_qty or 0)),
                average_fill_price=(
                    Decimal(str(alpaca_response.filled_avg_price))
                    if alpaca_response.filled_avg_price else None
                ),
                created_at=alpaca_response.created_at,
                submitted_at=alpaca_response.submitted_at,
                updated_at=alpaca_response.updated_at or alpaca_response.created_at,
                estimated_fee=estimated_fee,
                message=f"Order placed on Alpaca: {alpaca_response.id}"
            )

            logger.info(
                f"Order placed: {order.symbol} {order.side.value} {order.quantity} "
                f"@ {order.order_type.value} (ID: {alpaca_response.id})"
            )

            return response

        except Exception as e:
            raise BrokerError(
                code="ORDER_PLACEMENT_FAILED",
                message=f"Failed to place order: {e}",
                details={"order": order.dict()}
            )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on Alpaca.

        Args:
            order_id: Broker order ID

        Returns:
            True if cancelled successfully
        """
        if not self._client:
            raise BrokerConnectionError(
                code="ALPACA_NOT_CONNECTED",
                message="Not connected to Alpaca"
            )

        try:
            self._client.cancel_order_by_id(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get order status from Alpaca.

        Args:
            order_id: Broker order ID

        Returns:
            Order response with current status
        """
        if not self._client:
            raise BrokerConnectionError(
                code="ALPACA_NOT_CONNECTED",
                message="Not connected to Alpaca"
            )

        try:
            alpaca_order = self._client.get_order_by_id(order_id)

            # Determine order type
            order_type_map = {
                AlpacaOrderType.MARKET: OrderType.MARKET,
                AlpacaOrderType.LIMIT: OrderType.LIMIT,
                AlpacaOrderType.STOP: OrderType.STOP,
                AlpacaOrderType.STOP_LIMIT: OrderType.STOP_LIMIT,
            }
            order_type = order_type_map.get(alpaca_order.type, OrderType.MARKET)

            # Determine side
            side = OrderSide.BUY if alpaca_order.side == AlpacaOrderSide.BUY else OrderSide.SELL

            return OrderResponse(
                broker_order_id=alpaca_order.id,
                internal_order_id=alpaca_order.client_order_id,
                status=self._map_order_status(alpaca_order.status),
                symbol=alpaca_order.symbol,
                side=side,
                order_type=order_type,
                quantity=Decimal(str(alpaca_order.qty)),
                filled_quantity=Decimal(str(alpaca_order.filled_qty or 0)),
                average_fill_price=(
                    Decimal(str(alpaca_order.filled_avg_price))
                    if alpaca_order.filled_avg_price else None
                ),
                created_at=alpaca_order.created_at,
                submitted_at=alpaca_order.submitted_at,
                updated_at=alpaca_order.updated_at or alpaca_order.created_at
            )

        except Exception as e:
            raise BrokerError(
                code="ORDER_STATUS_FAILED",
                message=f"Failed to get order status: {e}",
                details={"order_id": order_id}
            )

    async def get_positions(self) -> list[Position]:
        """Get current positions from Alpaca.

        Returns:
            List of positions
        """
        if not self._client:
            raise BrokerConnectionError(
                code="ALPACA_NOT_CONNECTED",
                message="Not connected to Alpaca"
            )

        try:
            alpaca_positions = self._client.get_all_positions()

            positions = []
            for pos in alpaca_positions:
                # Calculate P&L percentage
                cost_basis = float(pos.avg_entry_price) * float(pos.qty)
                market_value = float(pos.current_price) * float(pos.qty)
                pnl_pct = ((market_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

                position = Position(
                    symbol=pos.symbol,
                    quantity=Decimal(str(pos.qty)),
                    average_cost=Decimal(str(pos.avg_entry_price)),
                    current_price=Decimal(str(pos.current_price)),
                    market_value=Decimal(str(pos.market_value)),
                    unrealized_pnl=Decimal(str(pos.unrealized_pl)),
                    pnl_percentage=pnl_pct,
                    exchange=pos.exchange,
                    currency="USD"  # Alpaca uses USD
                )
                positions.append(position)

            logger.info(f"Retrieved {len(positions)} positions")
            return positions

        except Exception as e:
            raise BrokerError(
                code="POSITIONS_FETCH_FAILED",
                message=f"Failed to get positions: {e}"
            )

    async def get_balance(self) -> Balance:
        """Get account balance from Alpaca.

        Returns:
            Account balance
        """
        if not self._client:
            raise BrokerConnectionError(
                code="ALPACA_NOT_CONNECTED",
                message="Not connected to Alpaca"
            )

        try:
            account = self._client.get_account()

            # Calculate daily P&L percentage
            equity = float(account.equity)
            last_equity = float(account.last_equity)
            daily_pnl_pct = ((equity - last_equity) / last_equity * 100) if last_equity > 0 else 0

            balance = Balance(
                currency="USD",
                cash=Decimal(str(account.cash)),
                market_value=Decimal(str(account.long_market_value or 0)),
                total_equity=Decimal(str(account.equity)),
                buying_power=Decimal(str(account.buying_power)),
                margin_used=Decimal(str(account.initial_margin or 0)),
                margin_available=Decimal(str(account.buying_power)),
                daily_pnl=Decimal(str(equity - last_equity)),
                daily_pnl_percentage=daily_pnl_pct,
                maintenance_margin=Decimal(str(account.maintenance_margin or 0)),
                initial_margin=Decimal(str(account.initial_margin or 0)),
                as_of=datetime.utcnow()
            )

            logger.info(f"Account balance: ${account.equity} (buying power: ${account.buying_power})")
            return balance

        except Exception as e:
            raise BrokerError(
                code="BALANCE_FETCH_FAILED",
                message=f"Failed to get balance: {e}"
            )

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get latest quote for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Quote dictionary or None
        """
        # Note: Quote data is better handled by the AlpacaStreamClient
        # This is a fallback using latest trade
        try:
            if not self._client:
                return None

            # Get latest quote from historical client
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest

            hist_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.api_secret
            )

            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = hist_client.get_stock_latest_quote(request)

            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    "symbol": symbol,
                    "bid": float(quote.bid_price),
                    "ask": float(quote.ask_price),
                    "bid_size": quote.bid_size,
                    "ask_size": quote.ask_size,
                    "timestamp": quote.timestamp.isoformat()
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None
