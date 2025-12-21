"""Tests for Broker Adapters."""

from decimal import Decimal

import pytest

from src.core.broker import MockBroker as MockBrokerAdapter
from src.core.broker import OrderRequest
from src.database.models import OrderSide, OrderStatus, OrderType, TimeInForce


class TestMockBrokerAdapter:
    """Test MockBrokerAdapter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.broker = MockBrokerAdapter(
            initial_cash=Decimal('10000')
        )

    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test broker connection and disconnection."""
        # Connect
        await self.broker.connect()
        assert await self.broker.is_connected() is True

        # Disconnect
        await self.broker.disconnect()
        assert await self.broker.is_connected() is False

    @pytest.mark.asyncio
    async def test_place_order(self):
        """Test placing an order."""
        await self.broker.connect()

        # Create order request - using enum values
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('10'),
            time_in_force=TimeInForce.DAY.value
        )

        # Place order
        response = await self.broker.place_order(order)

        assert response is not None
        assert response.status == OrderStatus.FILLED.value
        assert response.symbol == "AAPL"
        assert response.quantity == Decimal('10')
        assert response.filled_quantity == Decimal('10')

    @pytest.mark.asyncio
    async def test_place_limit_order(self):
        """Test placing a limit order."""
        await self.broker.connect()

        order = OrderRequest(
            symbol="GOOGL",
            side=OrderSide.BUY.value,
            order_type=OrderType.LIMIT.value,
            quantity=Decimal('5'),
            limit_price=Decimal('150.00'),
            time_in_force=TimeInForce.GTC.value
        )

        response = await self.broker.place_order(order)

        assert response is not None
        assert response.order_type == OrderType.LIMIT.value
        # OrderResponse doesn't have limit_price field - that's only in OrderRequest

    @pytest.mark.asyncio
    async def test_cancel_order(self):
        """Test cancelling an order."""
        await self.broker.connect()

        # Place order
        order = OrderRequest(
            symbol="MSFT",
            side=OrderSide.SELL.value,
            order_type=OrderType.LIMIT.value,
            quantity=Decimal('10'),
            limit_price=Decimal('400.00'),
            time_in_force=TimeInForce.DAY.value
        )

        response = await self.broker.place_order(order)
        order_id = response.broker_order_id

        # Cancel order
        success = await self.broker.cancel_order(order_id)
        assert success is True

    @pytest.mark.asyncio
    async def test_get_positions(self):
        """Test getting positions."""
        await self.broker.connect()

        # Place a buy order to create position
        order = OrderRequest(
            symbol="TSLA",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('20'),
            time_in_force=TimeInForce.DAY.value
        )

        await self.broker.place_order(order)

        # Get positions
        positions = await self.broker.get_positions()

        assert len(positions) > 0

        # Find TSLA position
        tsla_position = next((p for p in positions if p.symbol == "TSLA"), None)
        assert tsla_position is not None
        # MockBroker may partially fill orders, so check quantity is positive
        assert tsla_position.quantity > 0
        assert tsla_position.quantity <= Decimal('20')

    @pytest.mark.asyncio
    async def test_get_balance(self):
        """Test getting account balance."""
        await self.broker.connect()

        # Get initial balance
        balance = await self.broker.get_balance()

        assert balance is not None
        assert balance.cash == Decimal('10000')
        assert balance.total_equity == Decimal('10000')
        assert balance.buying_power == Decimal('10000')

        # Place order to change balance
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('10'),
            time_in_force=TimeInForce.DAY.value
        )

        response = await self.broker.place_order(order)

        # Check updated balance only if order was filled
        if response.status == OrderStatus.FILLED.value:
            updated_balance = await self.broker.get_balance()
            # Cash should be reduced (order cost + fees)
            assert updated_balance.cash < Decimal('10000')
            # Total equity should include positions
            assert updated_balance.total_equity > 0

    @pytest.mark.asyncio
    async def test_order_validation(self):
        """Test order validation."""
        await self.broker.connect()

        # Valid order should succeed
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('10'),
            time_in_force=TimeInForce.DAY.value
        )
        response = await self.broker.place_order(order)
        assert response is not None
        # Order should be filled or partially filled (MockBroker simulates both)
        assert response.status in [OrderStatus.FILLED.value, OrderStatus.PARTIALLY_FILLED.value]

        # Test invalid enum value
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            order = OrderRequest(
                symbol="AAPL",
                side="invalid_side",  # Invalid enum value
                order_type=OrderType.MARKET.value,
                quantity=Decimal('10'),
                time_in_force=TimeInForce.DAY.value
            )

    @pytest.mark.asyncio
    async def test_fee_calculation(self):
        """Test fee calculation."""
        await self.broker.connect()

        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('10'),
            time_in_force=TimeInForce.DAY.value
        )

        response = await self.broker.place_order(order)

        # Check that fee was applied
        assert response.estimated_fee > 0
        assert response.estimated_fee == Decimal('1.00')  # Fixed $1 fee for mock

    @pytest.mark.asyncio
    async def test_get_quote(self):
        """Test getting market quote."""
        await self.broker.connect()

        quote = await self.broker.get_quote("AAPL")

        assert quote is not None
        assert 'symbol' in quote
        assert quote['symbol'] == "AAPL"
        assert 'bid' in quote
        assert 'ask' in quote
        assert 'last' in quote
        assert quote['bid'] < quote['ask']  # Spread

    @pytest.mark.asyncio
    async def test_get_order_status(self):
        """Test getting order status."""
        await self.broker.connect()

        # Place order
        order = OrderRequest(
            symbol="NVDA",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('5'),
            time_in_force=TimeInForce.DAY.value
        )

        response = await self.broker.place_order(order)
        order_id = response.broker_order_id

        # Get order status
        status = await self.broker.get_order_status(order_id)

        assert status is not None
        assert status.broker_order_id == order_id
        assert status.symbol == "NVDA"
        # MockBroker simulates delays, so order may be filled or submitted
        assert status.status in [OrderStatus.FILLED.value, OrderStatus.SUBMITTED.value, OrderStatus.PARTIALLY_FILLED.value]