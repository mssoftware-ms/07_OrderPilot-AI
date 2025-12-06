"""Tests for order and execution event emitters.

Tests cover:
- OrderEvent and ExecutionEvent dataclasses
- OrderEventEmitter for order lifecycle events
- ExecutionEventEmitter for trade entry/exit
- BacktraderEventAdapter for integration with Backtrader
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from src.common import EventType, event_bus, OrderEvent, ExecutionEvent
from src.core.execution import OrderEventEmitter, ExecutionEventEmitter, BacktraderEventAdapter


@pytest.fixture(autouse=True)
def clear_event_history():
    """Clear event history before each test."""
    event_bus.clear_history()
    yield
    event_bus.clear_history()


class TestOrderEvent:
    """Tests for OrderEvent dataclass."""

    def test_order_event_creation(self):
        """Test creating an OrderEvent."""
        event = OrderEvent(
            type=EventType.ORDER_CREATED,
            timestamp=datetime.now(),
            data={},
            symbol="AAPL",
            order_id="order_123",
            order_type="market",
            side="buy",
            quantity=100.0,
            price=150.0,
            status="created"
        )

        assert event.symbol == "AAPL"
        assert event.order_id == "order_123"
        assert event.side == "buy"
        assert event.quantity == 100.0

    def test_order_event_data_sync(self):
        """Test that fields are synced to data dict."""
        event = OrderEvent(
            type=EventType.ORDER_FILLED,
            timestamp=datetime.now(),
            data={},
            symbol="TSLA",
            order_id="order_456",
            filled_quantity=50.0,
            avg_fill_price=700.0
        )

        # Check that fields are in data dict
        assert event.data["symbol"] == "TSLA"
        assert event.data["order_id"] == "order_456"
        assert event.data["filled_quantity"] == 50.0
        assert event.data["avg_fill_price"] == 700.0


class TestExecutionEvent:
    """Tests for ExecutionEvent dataclass."""

    def test_execution_event_creation(self):
        """Test creating an ExecutionEvent."""
        event = ExecutionEvent(
            type=EventType.TRADE_ENTRY,
            timestamp=datetime.now(),
            data={},
            symbol="MSFT",
            trade_id="trade_789",
            action="entry",
            side="long",
            quantity=200.0,
            price=300.0
        )

        assert event.symbol == "MSFT"
        assert event.trade_id == "trade_789"
        assert event.action == "entry"
        assert event.side == "long"

    def test_execution_event_with_pnl(self):
        """Test ExecutionEvent with P&L information."""
        event = ExecutionEvent(
            type=EventType.TRADE_EXIT,
            timestamp=datetime.now(),
            data={},
            symbol="GOOGL",
            trade_id="trade_101",
            action="exit",
            side="long",
            quantity=50.0,
            price=2800.0,
            pnl=500.0,
            pnl_pct=2.5,
            reason="take_profit"
        )

        assert event.pnl == 500.0
        assert event.pnl_pct == 2.5
        assert event.reason == "take_profit"


class TestOrderEventEmitter:
    """Tests for OrderEventEmitter."""

    def test_emit_order_created(self):
        """Test emitting ORDER_CREATED event."""
        emitter = OrderEventEmitter(symbol="AAPL", source="test")

        emitter.emit_order_created(
            order_id="order_1",
            order_type="market",
            side="buy",
            quantity=100.0
        )

        # Check event was emitted
        history = event_bus.get_history(EventType.ORDER_CREATED)
        assert len(history) == 1

        event = history[0]
        assert event.type == EventType.ORDER_CREATED
        assert event.symbol == "AAPL"
        assert event.order_id == "order_1"
        assert event.side == "buy"

    def test_emit_order_filled(self):
        """Test emitting ORDER_FILLED event."""
        emitter = OrderEventEmitter(symbol="TSLA")

        emitter.emit_order_filled(
            order_id="order_2",
            filled_quantity=50.0,
            avg_fill_price=700.0
        )

        history = event_bus.get_history(EventType.ORDER_FILLED)
        assert len(history) == 1

        event = history[0]
        assert event.filled_quantity == 50.0
        assert event.avg_fill_price == 700.0

    def test_emit_order_cancelled(self):
        """Test emitting ORDER_CANCELLED event."""
        emitter = OrderEventEmitter(symbol="MSFT")

        emitter.emit_order_cancelled(order_id="order_3", reason="user_cancelled")

        history = event_bus.get_history(EventType.ORDER_CANCELLED)
        assert len(history) == 1

        event = history[0]
        assert event.order_id == "order_3"
        assert event.data["reason"] == "user_cancelled"

    def test_emit_order_rejected(self):
        """Test emitting ORDER_REJECTED event."""
        emitter = OrderEventEmitter(symbol="GOOGL")

        emitter.emit_order_rejected(order_id="order_4", reason="insufficient_funds")

        history = event_bus.get_history(EventType.ORDER_REJECTED)
        assert len(history) == 1

        event = history[0]
        assert event.order_id == "order_4"
        assert event.data["reason"] == "insufficient_funds"


class TestExecutionEventEmitter:
    """Tests for ExecutionEventEmitter."""

    def test_emit_trade_entry(self):
        """Test emitting TRADE_ENTRY event."""
        emitter = ExecutionEventEmitter(symbol="AAPL")

        emitter.emit_trade_entry(
            trade_id="trade_1",
            side="long",
            quantity=100.0,
            price=150.0
        )

        history = event_bus.get_history(EventType.TRADE_ENTRY)
        assert len(history) == 1

        event = history[0]
        assert event.trade_id == "trade_1"
        assert event.side == "long"
        assert event.price == 150.0

    def test_emit_trade_exit(self):
        """Test emitting TRADE_EXIT event."""
        emitter = ExecutionEventEmitter(symbol="TSLA")

        emitter.emit_trade_exit(
            trade_id="trade_2",
            side="long",
            quantity=50.0,
            price=720.0,
            pnl=1000.0,
            pnl_pct=3.5,
            reason="signal"
        )

        history = event_bus.get_history(EventType.TRADE_EXIT)
        assert len(history) == 1

        event = history[0]
        assert event.trade_id == "trade_2"
        assert event.pnl == 1000.0
        assert event.pnl_pct == 3.5
        assert event.reason == "signal"

    def test_emit_stop_loss_hit(self):
        """Test emitting STOP_LOSS_HIT event."""
        emitter = ExecutionEventEmitter(symbol="MSFT")

        emitter.emit_stop_loss_hit(
            trade_id="trade_3",
            side="long",
            quantity=75.0,
            price=295.0,
            pnl=-375.0,
            pnl_pct=-2.0
        )

        history = event_bus.get_history(EventType.STOP_LOSS_HIT)
        assert len(history) == 1

        event = history[0]
        assert event.reason == "stop_loss"
        assert event.pnl == -375.0

    def test_emit_take_profit_hit(self):
        """Test emitting TAKE_PROFIT_HIT event."""
        emitter = ExecutionEventEmitter(symbol="GOOGL")

        emitter.emit_take_profit_hit(
            trade_id="trade_4",
            side="long",
            quantity=25.0,
            price=2900.0,
            pnl=1250.0,
            pnl_pct=5.0
        )

        history = event_bus.get_history(EventType.TAKE_PROFIT_HIT)
        assert len(history) == 1

        event = history[0]
        assert event.reason == "take_profit"
        assert event.pnl == 1250.0


class TestBacktraderEventAdapter:
    """Tests for BacktraderEventAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = BacktraderEventAdapter(symbol="AAPL", source="backtest")

        assert adapter.symbol == "AAPL"
        assert adapter.order_emitter.symbol == "AAPL"
        assert adapter.execution_emitter.symbol == "AAPL"

    def test_on_order_created(self):
        """Test handling order created."""
        adapter = BacktraderEventAdapter(symbol="TSLA")

        # Mock Backtrader order
        mock_order = MagicMock()
        mock_order.size = 100.0
        mock_order.exectype = 1  # Market order
        mock_order.isbuy.return_value = True

        adapter.on_order_created(mock_order)

        history = event_bus.get_history(EventType.ORDER_CREATED)
        assert len(history) == 1

        event = history[0]
        assert event.symbol == "TSLA"
        assert event.quantity == 100.0
        assert event.side == "buy"

    def test_on_order_filled_with_entry(self):
        """Test handling order filled with trade entry."""
        adapter = BacktraderEventAdapter(symbol="MSFT")

        # Mock order and execution
        mock_order = MagicMock()
        mock_order.size = 50.0
        mock_order.executed.size = 50.0
        mock_order.executed.price = 300.0
        mock_order.isbuy.return_value = True

        mock_execution = MagicMock()
        mock_execution.justopened = True
        mock_execution.isclosed = False
        mock_execution.price = 300.0

        adapter.on_order_filled(mock_order, mock_execution)

        # Check ORDER_FILLED event
        order_history = event_bus.get_history(EventType.ORDER_FILLED)
        assert len(order_history) == 1

        # Check TRADE_ENTRY event
        entry_history = event_bus.get_history(EventType.TRADE_ENTRY)
        assert len(entry_history) == 1

        event = entry_history[0]
        assert event.side == "long"
        assert event.quantity == 50.0
        assert event.price == 300.0

    def test_on_order_filled_with_exit(self):
        """Test handling order filled with trade exit."""
        adapter = BacktraderEventAdapter(symbol="GOOGL")

        # Simulate entry first
        mock_entry_order = MagicMock()
        mock_entry_order.size = 25.0
        mock_entry_order.executed.size = 25.0
        mock_entry_order.executed.price = 2800.0
        mock_entry_order.isbuy.return_value = True

        mock_entry_execution = MagicMock()
        mock_entry_execution.justopened = True
        mock_entry_execution.isclosed = False
        mock_entry_execution.price = 2800.0

        adapter.on_order_filled(mock_entry_order, mock_entry_execution)
        trade_id = str(id(mock_entry_execution))

        # Clear history
        event_bus.clear_history()

        # Simulate exit
        mock_exit_order = MagicMock()
        mock_exit_order.size = -25.0
        mock_exit_order.executed.size = -25.0
        mock_exit_order.executed.price = 2900.0
        mock_exit_order.isbuy.return_value = False

        mock_exit_execution = MagicMock()
        mock_exit_execution.justopened = False
        mock_exit_execution.isclosed = True
        mock_exit_execution.price = 2900.0
        mock_exit_execution.pnl = 2500.0
        mock_exit_execution.pnlcomm = 2490.0  # After commission
        mock_exit_execution.value = 70000.0

        # Use same ID as entry to simulate same trade
        adapter._trades[trade_id] = {
            'side': 'long',
            'entry_price': 2800.0,
            'quantity': 25.0
        }

        adapter.on_order_filled(mock_exit_order, mock_exit_execution)

        # Check TRADE_EXIT event
        exit_history = event_bus.get_history(EventType.TRADE_EXIT)
        assert len(exit_history) == 1

        event = exit_history[0]
        assert event.pnl == 2500.0
        assert event.reason == "signal"

    def test_get_order_type(self):
        """Test order type detection."""
        import backtrader as bt

        mock_order = MagicMock()

        # Market order
        mock_order.exectype = bt.Order.Market
        assert BacktraderEventAdapter._get_order_type(mock_order) == "market"

        # Limit order
        mock_order.exectype = bt.Order.Limit
        assert BacktraderEventAdapter._get_order_type(mock_order) == "limit"

        # Stop order
        mock_order.exectype = bt.Order.Stop
        assert BacktraderEventAdapter._get_order_type(mock_order) == "stop"


class TestEventIntegration:
    """Integration tests for event system."""

    def test_full_order_lifecycle(self):
        """Test full order lifecycle from creation to fill."""
        emitter = OrderEventEmitter(symbol="AAPL")

        # Order created
        emitter.emit_order_created(
            order_id="order_full",
            order_type="limit",
            side="buy",
            quantity=100.0,
            price=150.0
        )

        # Order submitted
        emitter.emit_order_submitted(order_id="order_full")

        # Order filled
        emitter.emit_order_filled(
            order_id="order_full",
            filled_quantity=100.0,
            avg_fill_price=149.95
        )

        # Verify all events
        created_events = event_bus.get_history(EventType.ORDER_CREATED)
        submitted_events = event_bus.get_history(EventType.ORDER_SUBMITTED)
        filled_events = event_bus.get_history(EventType.ORDER_FILLED)

        assert len(created_events) == 1
        assert len(submitted_events) == 1
        assert len(filled_events) == 1

    def test_full_trade_lifecycle(self):
        """Test full trade lifecycle from entry to exit."""
        exec_emitter = ExecutionEventEmitter(symbol="TSLA")

        # Trade entry
        exec_emitter.emit_trade_entry(
            trade_id="trade_full",
            side="long",
            quantity=50.0,
            price=700.0
        )

        # Trade exit
        exec_emitter.emit_trade_exit(
            trade_id="trade_full",
            side="long",
            quantity=50.0,
            price=720.0,
            pnl=1000.0,
            pnl_pct=2.86,
            reason="take_profit"
        )

        # Verify all events
        entry_events = event_bus.get_history(EventType.TRADE_ENTRY)
        exit_events = event_bus.get_history(EventType.TRADE_EXIT)

        assert len(entry_events) == 1
        assert len(exit_events) == 1

        exit_event = exit_events[0]
        assert exit_event.trade_id == "trade_full"
        assert exit_event.pnl > 0
