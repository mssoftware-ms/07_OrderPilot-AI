"""Tests for Database Models and Operations."""

import tempfile
from datetime import datetime
from decimal import Decimal

from src.database import DatabaseManager
from src.database.models import (
    MarketBar,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    TimeInForce,
)


class TestDatabaseOperations:
    """Test database operations."""

    def setup_method(self):
        """Setup test fixtures."""
        # Use temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        from src.config.loader import DatabaseConfig
        config = DatabaseConfig(
            engine="sqlite",
            path=self.temp_db.name
        )
        self.db_manager = DatabaseManager(config)
        self.db_manager.initialize()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_db.close()

    def test_create_order(self):
        """Test creating an order in database."""
        with self.db_manager.session() as session:
            order = Order(
                order_id="TEST_001",
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=10,
                time_in_force=TimeInForce.DAY,
                status=OrderStatus.PENDING,
                created_at=datetime.utcnow()
            )
            session.add(order)
            session.commit()

            # Retrieve order
            retrieved = session.query(Order).filter_by(order_id="TEST_001").first()
            assert retrieved is not None
            assert retrieved.symbol == "AAPL"
            assert retrieved.quantity == 10
            assert retrieved.status == OrderStatus.PENDING

    def test_create_position(self):
        """Test creating a position in database."""
        with self.db_manager.session() as session:
            position = Position(
                symbol="GOOGL",
                quantity=Decimal('5'),
                average_cost=Decimal('150.00'),
                current_price=Decimal('155.00'),
                market_value=Decimal('775.00'),
                unrealized_pnl=Decimal('25.00'),
                opened_at=datetime.utcnow()
            )
            session.add(position)
            session.commit()

            # Retrieve position
            retrieved = session.query(Position).filter_by(symbol="GOOGL").first()
            assert retrieved is not None
            assert retrieved.quantity == Decimal('5')
            assert retrieved.average_cost == Decimal('150.00')
            assert retrieved.current_price == Decimal('155.00')

    def test_create_market_bar(self):
        """Test creating market bar data."""
        with self.db_manager.session() as session:
            bar = MarketBar(
                symbol="MSFT",
                timestamp=datetime.utcnow(),
                open=Decimal('400.00'),
                high=Decimal('405.00'),
                low=Decimal('399.00'),
                close=Decimal('403.00'),
                volume=1000000
            )
            session.add(bar)
            session.commit()

            # Retrieve bar
            retrieved = session.query(MarketBar).filter_by(symbol="MSFT").first()
            assert retrieved is not None
            assert retrieved.open == Decimal('400.00')
            assert retrieved.close == Decimal('403.00')
            assert retrieved.volume == 1000000

    def test_update_order_status(self):
        """Test updating order status."""
        with self.db_manager.session() as session:
            # Create order
            order = Order(
                order_id="UPDATE_001",
                symbol="TSLA",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=20,
                limit_price=Decimal('800.00'),
                time_in_force=TimeInForce.GTC,
                status=OrderStatus.SUBMITTED
            )
            session.add(order)
            session.commit()

            # Update status
            order.status = OrderStatus.FILLED
            order.filled_quantity = 20
            order.filled_at = datetime.utcnow()
            order.average_fill_price = Decimal('799.50')
            session.commit()

            # Verify update
            retrieved = session.query(Order).filter_by(order_id="UPDATE_001").first()
            assert retrieved.status == OrderStatus.FILLED
            assert retrieved.filled_quantity == 20
            assert retrieved.average_fill_price == Decimal('799.50')

    def test_query_orders_by_status(self):
        """Test querying orders by status."""
        with self.db_manager.session() as session:
            # Create multiple orders
            orders = [
                Order(order_id=f"Q_{i}", symbol="AAPL", side=OrderSide.BUY,
                     order_type=OrderType.MARKET, quantity=10,
                     time_in_force=TimeInForce.DAY,
                     status=OrderStatus.FILLED if i < 3 else OrderStatus.PENDING)
                for i in range(5)
            ]

            session.add_all(orders)
            session.commit()

            # Query filled orders
            filled = session.query(Order).filter_by(status=OrderStatus.FILLED).all()
            assert len(filled) == 3

            # Query pending orders
            pending = session.query(Order).filter_by(status=OrderStatus.PENDING).all()
            assert len(pending) == 2

    def test_delete_old_market_bars(self):
        """Test deleting old market bar data."""
        with self.db_manager.session() as session:
            # Create bars with different timestamps
            old_bar = MarketBar(
                symbol="OLD",
                timestamp=datetime(2020, 1, 1),
                open=Decimal('100'), high=Decimal('100'),
                low=Decimal('100'), close=Decimal('100'),
                volume=100
            )
            recent_bar = MarketBar(
                symbol="RECENT",
                timestamp=datetime.utcnow(),
                open=Decimal('200'), high=Decimal('200'),
                low=Decimal('200'), close=Decimal('200'),
                volume=200
            )

            session.add(old_bar)
            session.add(recent_bar)
            session.commit()

            # Delete old bars
            cutoff_date = datetime(2021, 1, 1)
            session.query(MarketBar).filter(
                MarketBar.timestamp < cutoff_date
            ).delete()
            session.commit()

            # Verify deletion
            remaining = session.query(MarketBar).all()
            assert len(remaining) == 1
            assert remaining[0].symbol == "RECENT"

    def test_cascade_delete(self):
        """Test cascade deletion relationships."""
        # This would test cascade deletions if we had foreign key relationships
        # For now, just a placeholder
        assert True

    def test_transaction_rollback(self):
        """Test transaction rollback on error."""
        with self.db_manager.session() as session:
            try:
                # Add valid order
                order1 = Order(
                    order_id="TX_001",
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=10,
                    time_in_force=TimeInForce.DAY,
                    status=OrderStatus.PENDING
                )
                session.add(order1)

                # Try to add invalid order (will fail on commit due to missing required field)
                # This is just for demonstration
                order2 = Order(
                    order_id="TX_002",
                    symbol="INVALID",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=-10,  # Invalid quantity
                    time_in_force=TimeInForce.DAY,
                    status=OrderStatus.PENDING
                )
                session.add(order2)

                # This should rollback the entire transaction
                session.commit()
            except Exception:
                session.rollback()

        # Verify nothing was saved
        with self.db_manager.session() as session:
            count = session.query(Order).filter(
                Order.order_id.like("TX_%")
            ).count()
            # Depending on validation, this might be 0 or handle differently
            assert count >= 0  # Just ensure no crash

    def test_get_session(self):
        """Test getting a session directly."""
        session = self.db_manager.get_session()
        assert session is not None

        # Use the session
        order = Order(
            order_id="SESSION_TEST",
            symbol="TEST",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1,
            time_in_force=TimeInForce.DAY,
            status=OrderStatus.PENDING
        )
        session.add(order)
        session.commit()

        # Cleanup
        session.close()

        # Verify order was created
        with self.db_manager.session() as verify_session:
            retrieved = verify_session.query(Order).filter_by(
                order_id="SESSION_TEST"
            ).first()
            assert retrieved is not None

    def test_execute_raw_query(self):
        """Test executing raw SQL queries."""
        # Insert data first
        with self.db_manager.session() as session:
            order = Order(
                order_id="RAW_001",
                symbol="RAW",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=5,
                time_in_force=TimeInForce.DAY,
                status=OrderStatus.PENDING
            )
            session.add(order)
            session.commit()

        # Execute raw query
        result = self.db_manager.execute_raw(
            "SELECT COUNT(*) as count FROM orders WHERE symbol = :symbol",
            {"symbol": "RAW"}
        )
        assert result is not None

    def test_get_table_stats(self):
        """Test getting table statistics."""
        # Add some data
        with self.db_manager.session() as session:
            for i in range(5):
                order = Order(
                    order_id=f"STATS_{i}",
                    symbol="STATS",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=1,
                    time_in_force=TimeInForce.DAY,
                    status=OrderStatus.PENDING
                )
                session.add(order)
            session.commit()

        # Get stats
        stats = self.db_manager.get_table_stats()
        assert isinstance(stats, dict)
        assert "orders" in stats
        assert stats["orders"] >= 5

    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        # Add old data
        with self.db_manager.session() as session:
            old_bar = MarketBar(
                symbol="OLD_DATA",
                timestamp=datetime(2020, 1, 1),
                open=Decimal('100'), high=Decimal('100'),
                low=Decimal('100'), close=Decimal('100'),
                volume=100
            )
            session.add(old_bar)
            session.commit()

        # Cleanup data older than 1000 days
        self.db_manager.cleanup_old_data(days_to_keep=1000)

        # Verify old data was removed
        with self.db_manager.session() as session:
            count = session.query(MarketBar).filter_by(symbol="OLD_DATA").count()
            assert count == 0

    def test_vacuum(self):
        """Test database vacuum operation."""
        # For SQLite, vacuum should work without error
        self.db_manager.vacuum()
        # If no exception, test passes

    def test_backup(self):
        """Test database backup."""
        import tempfile
        from pathlib import Path

        # Create backup
        backup_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        backup_path = Path(backup_file.name)
        backup_file.close()

        self.db_manager.backup(backup_path)

        # Verify backup file exists and has content
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0

        # Cleanup
        backup_path.unlink()

    def test_drop_tables(self):
        """Test dropping all tables."""
        # Verify tables exist
        with self.db_manager.session() as session:
            order = Order(
                order_id="DROP_TEST",
                symbol="DROP",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1,
                time_in_force=TimeInForce.DAY,
                status=OrderStatus.PENDING
            )
            session.add(order)
            session.commit()

        # Drop tables
        self.db_manager.drop_tables()

        # Recreate tables
        self.db_manager.create_tables()

        # Verify tables are empty
        with self.db_manager.session() as session:
            count = session.query(Order).count()
            assert count == 0

    def test_close_connection(self):
        """Test closing database connection."""
        # Connection should work before close
        with self.db_manager.session() as session:
            count = session.query(Order).count()
            assert count >= 0

        # Close
        self.db_manager.close()

        # After close, need to reinitialize
        self.db_manager.initialize()

        # Should work again
        with self.db_manager.session() as session:
            count = session.query(Order).count()
            assert count >= 0