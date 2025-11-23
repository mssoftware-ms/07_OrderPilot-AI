"""Mock Broker Implementation for Testing.

Provides a simulated broker for development and testing purposes.
"""

import asyncio
import logging
import random
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from src.database.models import OrderSide, OrderStatus

from .base import (
    Balance,
    BrokerAdapter,
    BrokerConnectionError,
    FeeModel,
    InsufficientFundsError,
    OrderRequest,
    OrderResponse,
    Position,
)

logger = logging.getLogger(__name__)


class MockBroker(BrokerAdapter):
    """Mock broker for testing and development."""

    def __init__(self, initial_cash: Decimal = Decimal('10000'), **kwargs):
        """Initialize mock broker.

        Args:
            initial_cash: Starting cash balance
            **kwargs: Additional arguments for base class
        """
        # Default fee model for mock broker
        if 'fee_model' not in kwargs:
            kwargs['fee_model'] = FeeModel(
                broker="mock",
                fee_type="flat",
                flat_fee=Decimal('1.00')
            )

        super().__init__(name="MockBroker", **kwargs)

        # Internal state
        self._cash = initial_cash
        self._positions: dict[str, Position] = {}
        self._orders: dict[str, OrderResponse] = {}
        self._order_counter = 0
        self._market_prices: dict[str, Decimal] = {}

        # Simulation parameters
        self.fill_probability = 0.9  # Probability of order getting filled
        self.partial_fill_probability = 0.1  # Probability of partial fill
        self.rejection_probability = 0.02  # Probability of order rejection

    # ==================== Template Method Implementations ====================

    async def _establish_connection(self) -> None:
        """Simulate broker connection (template method implementation)."""
        await asyncio.sleep(0.1)  # Simulate connection delay

    async def _cleanup_resources(self) -> None:
        """Clean up mock broker resources (template method implementation)."""
        # No resources to clean up in mock broker
        pass

    async def _place_order_impl(
        self,
        order: OrderRequest,
        estimated_fee: Decimal
    ) -> OrderResponse:
        """Place order in mock broker."""
        if not self._connected:
            raise BrokerConnectionError("NOT_CONNECTED", "Broker not connected")

        # Generate order ID
        self._order_counter += 1
        broker_order_id = f"MOCK_{self._order_counter:06d}"
        internal_order_id = order.internal_order_id or str(uuid4())

        # Check for sufficient funds (for buy orders)
        if order.side == OrderSide.BUY:
            required_cash = (order.quantity * (order.limit_price or self._get_market_price(order.symbol))) + estimated_fee
            if required_cash > self._cash:
                raise InsufficientFundsError(
                    "INSUFFICIENT_FUNDS",
                    f"Required: {required_cash}, Available: {self._cash}"
                )

        # Simulate order rejection
        if random.random() < self.rejection_probability:
            response = OrderResponse(
                broker_order_id=broker_order_id,
                internal_order_id=internal_order_id,
                status=OrderStatus.REJECTED.value,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                estimated_fee=estimated_fee,
                message="Order rejected by exchange"
            )
        else:
            # Create successful order response
            response = OrderResponse(
                broker_order_id=broker_order_id,
                internal_order_id=internal_order_id,
                status=OrderStatus.SUBMITTED.value,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                created_at=datetime.utcnow(),
                submitted_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                estimated_fee=estimated_fee
            )

            # Simulate immediate fill for market orders
            if order.order_type == "market":
                await self._simulate_fill(broker_order_id, order, response)

        self._orders[broker_order_id] = response
        logger.info(f"Order placed: {broker_order_id} - {order.symbol} {order.side} {order.quantity}")

        return response

    async def _simulate_fill(
        self,
        order_id: str,
        order: OrderRequest,
        response: OrderResponse
    ) -> None:
        """Simulate order fill."""
        if random.random() > self.fill_probability:
            return  # Order remains pending

        # Determine fill quantity
        if random.random() < self.partial_fill_probability:
            filled_qty = order.quantity * Decimal(str(random.uniform(0.3, 0.8)))
        else:
            filled_qty = order.quantity

        # Determine fill price
        market_price = self._get_market_price(order.symbol)
        if order.limit_price:
            fill_price = order.limit_price
        else:
            # Add some slippage for market orders
            slippage = Decimal(str(random.uniform(-0.001, 0.001)))
            fill_price = market_price * (Decimal('1') + slippage)

        # Update response
        response.filled_quantity = filled_qty
        response.average_fill_price = fill_price
        response.actual_fee = self.fee_model.calculate(filled_qty * fill_price)
        response.status = OrderStatus.FILLED.value if filled_qty == order.quantity else OrderStatus.PARTIALLY_FILLED.value

        # Update internal state
        if order.side == "buy":
            self._cash -= (filled_qty * fill_price + response.actual_fee)
            self._update_position(order.symbol, filled_qty, fill_price)
        else:  # SELL
            self._cash += (filled_qty * fill_price - response.actual_fee)
            self._update_position(order.symbol, -filled_qty, fill_price)

        logger.info(f"Order filled: {order_id} - {filled_qty} @ {fill_price}")

    def _update_position(self, symbol: str, quantity: Decimal, price: Decimal) -> None:
        """Update position after fill."""
        if symbol not in self._positions:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                average_cost=price,
                realized_pnl=Decimal('0')
            )
        else:
            pos = self._positions[symbol]
            if quantity > 0:  # Buy
                total_cost = (pos.quantity * pos.average_cost) + (quantity * price)
                new_quantity = pos.quantity + quantity
                pos.average_cost = total_cost / new_quantity if new_quantity != 0 else Decimal('0')
                pos.quantity = new_quantity
            else:  # Sell
                sell_quantity = abs(quantity)
                if sell_quantity >= pos.quantity:
                    # Close position
                    realized_pnl = (price - pos.average_cost) * pos.quantity
                    pos.realized_pnl += realized_pnl
                    del self._positions[symbol]
                else:
                    # Partial close
                    realized_pnl = (price - pos.average_cost) * sell_quantity
                    pos.realized_pnl += realized_pnl
                    pos.quantity -= sell_quantity

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id not in self._orders:
            return False

        order = self._orders[order_id]
        if order.status in [OrderStatus.PENDING.value, OrderStatus.SUBMITTED.value]:
            order.status = OrderStatus.CANCELLED.value
            order.updated_at = datetime.utcnow()
            logger.info(f"Order cancelled: {order_id}")
            return True

        return False

    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get order status."""
        if order_id not in self._orders:
            raise ValueError(f"Order not found: {order_id}")

        # Simulate delayed fills for limit orders
        order = self._orders[order_id]
        if order.status == OrderStatus.SUBMITTED.value and random.random() < 0.3:
            original_request = OrderRequest(
                symbol=order.symbol,
                side=order.side,  # Already a string value
                order_type=order.order_type,  # Already a string value
                quantity=order.quantity,
                time_in_force="DAY"  # Add missing field
            )
            await self._simulate_fill(order_id, original_request, order)

        return order

    async def get_positions(self) -> list[Position]:
        """Get all positions."""
        # Update current prices
        for position in self._positions.values():
            position.current_price = self._get_market_price(position.symbol)
            position.market_value = position.quantity * position.current_price
            position.unrealized_pnl = (position.current_price - position.average_cost) * position.quantity
            if position.average_cost > 0:
                position.pnl_percentage = float(
                    (position.current_price - position.average_cost) / position.average_cost * 100
                )

        return list(self._positions.values())

    async def get_balance(self) -> Balance:
        """Get account balance."""
        positions = await self.get_positions()
        market_value = sum(p.market_value for p in positions if p.market_value)
        total_equity = self._cash + market_value

        return Balance(
            cash=self._cash,
            market_value=market_value,
            total_equity=total_equity,
            buying_power=self._cash,  # Simplified for mock
            daily_pnl=sum(p.unrealized_pnl for p in positions if p.unrealized_pnl)
        )

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get current quote for symbol."""
        price = self._get_market_price(symbol)
        spread = price * Decimal('0.001')  # 0.1% spread

        return {
            'symbol': symbol,
            'bid': price - spread / 2,
            'ask': price + spread / 2,
            'last': price,
            'bid_size': random.randint(100, 1000),
            'ask_size': random.randint(100, 1000),
            'volume': random.randint(100000, 10000000),
            'timestamp': datetime.utcnow()
        }

    def _get_market_price(self, symbol: str) -> Decimal:
        """Get simulated market price."""
        if symbol not in self._market_prices:
            # Generate random initial price
            base_price = Decimal(str(random.uniform(10, 500)))
            self._market_prices[symbol] = base_price

        # Add some random movement
        current = self._market_prices[symbol]
        change = Decimal(str(random.uniform(-0.02, 0.02)))  # +/- 2%
        new_price = current * (Decimal('1') + change)
        self._market_prices[symbol] = new_price

        return new_price

    def set_market_price(self, symbol: str, price: Decimal) -> None:
        """Set market price for testing."""
        self._market_prices[symbol] = price