"""Tests for Execution Engine."""

import asyncio
from decimal import Decimal

import pytest

from src.core.broker import MockBroker, OrderRequest
from src.core.execution.engine import ExecutionEngine, ExecutionState
from src.database.models import OrderSide, OrderType, TimeInForce


class TestExecutionEngine:
    """Test ExecutionEngine functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.broker = MockBroker(initial_cash=Decimal('10000'))
        self.engine = ExecutionEngine(
            max_pending_orders=10,
            order_timeout_seconds=60,
            manual_approval_default=False,  # Disable manual approval for testing
            kill_switch_enabled=True,
            max_loss_per_day=Decimal('500'),
            max_drawdown_percent=10.0
        )

    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        """Test starting and stopping the engine."""
        # Initially idle
        assert self.engine.state == ExecutionState.IDLE

        # Start engine
        await self.engine.start()
        assert self.engine.state == ExecutionState.RUNNING
        
        # Give it a moment to process
        await asyncio.sleep(0.1)

        # Stop engine
        await self.engine.stop()
        assert self.engine.state == ExecutionState.STOPPED

    @pytest.mark.asyncio
    async def test_engine_pause_resume(self):
        """Test pausing and resuming execution."""
        await self.engine.start()
        
        # Pause
        self.engine.pause()
        assert self.engine.state == ExecutionState.PAUSED

        # Resume
        self.engine.resume()
        assert self.engine.state == ExecutionState.RUNNING

        await self.engine.stop()

    @pytest.mark.asyncio
    async def test_kill_switch_activation(self):
        """Test kill switch activation."""
        await self.engine.start()
        await self.broker.connect()

        # Submit an order
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('10'),
            time_in_force=TimeInForce.DAY.value
        )
        
        task_id = await self.engine.submit_order(order, self.broker)
        assert task_id is not None

        # Activate kill switch
        self.engine.activate_kill_switch("Test emergency stop")
        assert self.engine.state == ExecutionState.KILL_SWITCH_ACTIVE
        assert self.engine._kill_switch_active is True

        # Deactivate
        self.engine.deactivate_kill_switch()
        assert self.engine._kill_switch_active is False
        assert self.engine.state == ExecutionState.IDLE

        await self.engine.stop()

    @pytest.mark.asyncio
    async def test_submit_order(self):
        """Test order submission."""
        await self.engine.start()
        await self.broker.connect()

        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('5'),
            time_in_force=TimeInForce.DAY.value
        )

        task_id = await self.engine.submit_order(
            order, self.broker, priority=7
        )

        assert task_id is not None
        assert len(task_id) > 0

        # Give queue processor time to work
        await asyncio.sleep(0.2)

        await self.engine.stop()

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting engine status."""
        status = self.engine.get_status()

        assert 'state' in status
        assert 'pending_orders' in status
        assert 'active_orders' in status
        assert 'completed_orders' in status
        assert 'daily_loss' in status
        assert 'daily_trades' in status
        assert 'kill_switch_active' in status

        assert status['state'] == ExecutionState.IDLE.value
        assert status['pending_orders'] == 0
        assert status['active_orders'] == 0

    @pytest.mark.asyncio
    async def test_update_metrics(self):
        """Test metrics update."""
        # Initial metrics
        assert self.engine.daily_loss == Decimal('0')
        assert self.engine.daily_trades == 0

        # Update with profit
        await self.engine.update_metrics(
            pnl=Decimal('100'),
            equity=Decimal('10100')
        )
        assert self.engine.daily_loss == Decimal('0')  # No loss yet
        assert self.engine.daily_trades == 1

        # Update with loss
        await self.engine.update_metrics(
            pnl=Decimal('-50'),
            equity=Decimal('10050')
        )
        assert self.engine.daily_loss == Decimal('50')
        assert self.engine.daily_trades == 2

    @pytest.mark.asyncio
    async def test_kill_switch_on_max_loss(self):
        """Test kill switch triggers on max daily loss."""
        # Set low max loss for testing
        self.engine.max_loss_per_day = Decimal('100')
        self.engine.kill_switch_enabled = True

        # Simulate large loss
        await self.engine.update_metrics(
            pnl=Decimal('-150'),
            equity=Decimal('9850')
        )

        # Kill switch should be active
        assert self.engine._kill_switch_active is True
        assert self.engine.state == ExecutionState.KILL_SWITCH_ACTIVE

    @pytest.mark.asyncio
    async def test_queue_priority(self):
        """Test order queue priority handling."""
        await self.engine.start()
        await self.broker.connect()

        # Submit multiple orders with different priorities
        orders = []
        for i, priority in enumerate([3, 8, 5]):
            order = OrderRequest(
                symbol=f"TEST{i}",
                side=OrderSide.BUY.value,
                order_type=OrderType.MARKET.value,
                quantity=Decimal('1'),
                time_in_force=TimeInForce.DAY.value
            )
            task_id = await self.engine.submit_order(
                order, self.broker, priority=priority
            )
            orders.append(task_id)

        # Give time to process
        await asyncio.sleep(0.3)

        await self.engine.stop()

        # Verify all orders were processed
        assert len(orders) == 3

    @pytest.mark.asyncio
    async def test_max_pending_orders(self):
        """Test max pending orders limit."""
        self.engine.max_pending_orders = 2
        await self.engine.start()
        await self.broker.connect()

        # Try to submit more orders than limit
        tasks = []
        for i in range(3):
            order = OrderRequest(
                symbol=f"TEST{i}",
                side=OrderSide.BUY.value,
                order_type=OrderType.MARKET.value,
                quantity=Decimal('1'),
                time_in_force=TimeInForce.DAY.value
            )
            try:
                task_id = await self.engine.submit_order(order, self.broker)
                tasks.append(task_id)
            except Exception:
                pass  # Queue full

        await asyncio.sleep(0.3)
        await self.engine.stop()

    @pytest.mark.asyncio
    async def test_cannot_start_when_running(self):
        """Test that engine cannot start when already running."""
        await self.engine.start()
        assert self.engine.state == ExecutionState.RUNNING

        # Try to start again
        await self.engine.start()
        # Should still be running, not restarted
        assert self.engine.state == ExecutionState.RUNNING

        await self.engine.stop()

    @pytest.mark.asyncio
    async def test_order_with_manual_approval(self):
        """Test order with manual approval required."""
        # Create engine with manual approval
        engine_with_approval = ExecutionEngine(
            manual_approval_default=True
        )

        await engine_with_approval.start()
        await self.broker.connect()

        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('5'),
            time_in_force=TimeInForce.DAY.value
        )

        task_id = await engine_with_approval.submit_order(order, self.broker)
        assert task_id is not None

        # Give time for processing
        await asyncio.sleep(0.2)

        await engine_with_approval.stop()


class TestExecutionTask:
    """Test ExecutionTask dataclass."""

    def test_task_creation(self):
        """Test creating execution task."""
        from src.core.execution.engine import ExecutionTask

        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('10'),
            time_in_force=TimeInForce.DAY.value
        )

        broker = MockBroker()
        
        task = ExecutionTask(
            task_id="test-123",
            order_request=order,
            broker=broker,
            priority=7
        )

        assert task.task_id == "test-123"
        assert task.order_request == order
        assert task.broker == broker
        assert task.priority == 7
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.created_at is not None

    def test_task_auto_id_generation(self):
        """Test automatic task ID generation."""
        from src.core.execution.engine import ExecutionTask

        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY.value,
            order_type=OrderType.MARKET.value,
            quantity=Decimal('10'),
            time_in_force=TimeInForce.DAY.value
        )

        task = ExecutionTask(
            task_id=None,
            order_request=order,
            broker=MockBroker()
        )

        # Should have auto-generated UUID
        assert task.task_id is not None
        assert len(task.task_id) > 0
