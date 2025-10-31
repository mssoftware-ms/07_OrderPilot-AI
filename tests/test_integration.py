"""Integration Tests for OrderPilot-AI.

Tests end-to-end workflows combining multiple components.
"""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from src.config.loader import BrokerType, ConfigManager, TradingEnvironment
from src.core.broker import MockBroker, OrderRequest
from src.database import DatabaseManager
from src.database.models import OrderSide, OrderStatus, OrderType, TimeInForce


class TestEndToEndWorkflow:
    """Test complete trading workflows."""

    def setup_method(self):
        """Setup test fixtures."""
        # Setup config
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        self.profile = self.config_manager.load_profile("test_integration")

        # Setup database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.profile.database.path = self.temp_db.name
        self.db_manager = DatabaseManager(self.profile.database)
        self.db_manager.initialize()

        # Setup broker
        self.broker = MockBroker(initial_cash=Decimal('100000'))

    @pytest.mark.asyncio
    async def test_complete_trade_lifecycle(self):
        """Test complete trade: order -> fill -> position -> close."""
        await self.broker.connect()

        # 1. Check initial state
        initial_balance = await self.broker.get_balance()
        assert initial_balance.cash == Decimal('100000')

        initial_positions = await self.broker.get_positions()
        assert len(initial_positions) == 0

        # 2. Place buy order
        buy_order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('100'),
            time_in_force=TimeInForce.DAY.value
        )

        buy_response = await self.broker.place_order(buy_order)
        assert buy_response is not None
        assert buy_response.symbol == "AAPL"

        # 3. Verify position was created
        positions = await self.broker.get_positions()
        if buy_response.status in [OrderStatus.FILLED.value, OrderStatus.PARTIALLY_FILLED.value]:
            assert len(positions) > 0
            aapl_position = next((p for p in positions if p.symbol == "AAPL"), None)
            assert aapl_position is not None
            assert aapl_position.quantity > 0

            # 4. Place sell order to close position
            sell_order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL.value,
                order_type=OrderType.MARKET.value,
                quantity=aapl_position.quantity,
                time_in_force=TimeInForce.DAY.value
            )

            sell_response = await self.broker.place_order(sell_order)
            assert sell_response is not None

            # 5. Verify balance changed
            final_balance = await self.broker.get_balance()
            # Balance should be different due to trading
            assert final_balance.cash != initial_balance.cash

    @pytest.mark.asyncio
    async def test_order_rejection_workflow(self):
        """Test order rejection and error handling."""
        await self.broker.connect()

        # Invalid order (negative quantity via validation)
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            OrderRequest(
                symbol="INVALID",
                side="invalid_side",
                order_type=OrderType.MARKET.value,
                quantity=Decimal('10'),
                time_in_force=TimeInForce.DAY.value
            )

    @pytest.mark.asyncio
    async def test_multiple_symbols_portfolio(self):
        """Test trading multiple symbols simultaneously."""
        await self.broker.connect()

        symbols = ["AAPL", "GOOGL", "MSFT"]

        # Place orders for multiple symbols
        for symbol in symbols:
            order = OrderRequest(
                symbol=symbol,
                side=OrderSide.BUY.value,
                order_type=OrderType.MARKET.value,
                quantity=Decimal('10'),
                time_in_force=TimeInForce.DAY.value
            )

            response = await self.broker.place_order(order)
            assert response is not None

        # Verify positions
        positions = await self.broker.get_positions()
        position_symbols = {p.symbol for p in positions}

        # At least some positions should be created
        assert len(position_symbols) > 0

    @pytest.mark.asyncio
    async def test_balance_tracking_accuracy(self):
        """Test balance calculations remain accurate."""
        await self.broker.connect()

        initial_balance = await self.broker.get_balance()
        initial_equity = initial_balance.total_equity

        # Place and fill order
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('50'),
            time_in_force=TimeInForce.DAY.value
        )

        response = await self.broker.place_order(order)

        if response.status in [OrderStatus.FILLED.value, OrderStatus.PARTIALLY_FILLED.value]:
            final_balance = await self.broker.get_balance()

            # Total equity should account for positions
            assert final_balance.total_equity > 0
            # Cash should be reduced
            assert final_balance.cash < initial_balance.cash


class TestConfigurationIntegration:
    """Test configuration management integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def test_profile_workflow(self):
        """Test creating, modifying, and loading profiles."""
        manager = ConfigManager(self.temp_dir)

        # Create profile
        profile = manager.load_profile("integration_test")
        assert profile.profile_name == "integration_test"

        # Modify profile
        profile.environment = TradingEnvironment.PRODUCTION
        profile.broker.broker_type = BrokerType.IBKR
        profile.broker.port = 7496

        # Save profile
        manager.save_profile(profile)

        # Reload and verify
        reloaded = manager.load_profile("integration_test")
        assert reloaded.environment == TradingEnvironment.PRODUCTION.value
        assert reloaded.broker.broker_type == BrokerType.IBKR
        assert reloaded.broker.port == 7496

    def test_multiple_profiles(self):
        """Test managing multiple profiles."""
        manager = ConfigManager(self.temp_dir)

        # Create multiple profiles
        paper_profile = manager.load_profile("paper")
        paper_profile.environment = TradingEnvironment.PAPER
        manager.save_profile(paper_profile)

        prod_profile = manager.load_profile("production")
        prod_profile.environment = TradingEnvironment.PRODUCTION
        manager.save_profile(prod_profile)

        # List profiles
        profiles = manager.list_profiles()
        assert "paper" in profiles
        assert "production" in profiles


class TestDatabaseIntegration:
    """Test database operations integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        from src.config.loader import DatabaseConfig
        config = DatabaseConfig(
            engine="sqlite",
            path=self.temp_db.name
        )
        self.db_manager = DatabaseManager(config)
        self.db_manager.initialize()

    def test_order_persistence(self):
        """Test persisting orders to database."""
        from src.database.models import Order

        with self.db_manager.session() as session:
            order = Order(
                order_id="TEST_001",
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal('100'),
                time_in_force=TimeInForce.DAY,
                status=OrderStatus.PENDING
            )

            session.add(order)
            session.commit()

            # Query order
            retrieved = session.query(Order).filter_by(order_id="TEST_001").first()
            assert retrieved is not None
            assert retrieved.symbol == "AAPL"
            assert retrieved.quantity == Decimal('100')
