"""Execution Engine for OrderPilot-AI Trading Application.

Manages order execution with manual approval, queuing, retry logic,
and kill switch functionality.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import uuid4

from src.core.broker import BrokerAdapter, OrderRequest, OrderResponse
from src.ai import OrderAnalysis
from src.common.event_bus import Event, EventType, event_bus
from src.database import get_db_manager
from src.database.models import Order as DBOrder

logger = logging.getLogger(__name__)


class ExecutionState(Enum):
    """Execution engine states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    KILL_SWITCH_ACTIVE = "kill_switch_active"


@dataclass
class ExecutionTask:
    """Represents a task in the execution queue."""
    task_id: str
    order_request: OrderRequest
    broker: BrokerAdapter
    priority: int = 5  # 1-10, higher is more important
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    ai_analysis: OrderAnalysis | None = None
    manual_approval: bool = True
    approval_callback: Callable | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.task_id is None:
            self.task_id = str(uuid4())


class ExecutionEngine:
    """Manages order execution with safety controls."""

    def __init__(
        self,
        max_pending_orders: int = 50,
        order_timeout_seconds: int = 300,
        manual_approval_default: bool = True,
        kill_switch_enabled: bool = True,
        max_loss_per_day: Decimal = Decimal('500'),
        max_drawdown_percent: float = 10.0
    ):
        """Initialize execution engine.

        Args:
            max_pending_orders: Maximum orders in queue
            order_timeout_seconds: Timeout for order execution
            manual_approval_default: Require manual approval
            kill_switch_enabled: Enable kill switch
            max_loss_per_day: Maximum daily loss allowed
            max_drawdown_percent: Maximum drawdown percentage
        """
        self.max_pending_orders = max_pending_orders
        self.order_timeout_seconds = order_timeout_seconds
        self.manual_approval_default = manual_approval_default
        self.kill_switch_enabled = kill_switch_enabled
        self.max_loss_per_day = max_loss_per_day
        self.max_drawdown_percent = max_drawdown_percent

        # State
        self.state = ExecutionState.IDLE
        self._kill_switch_active = False

        # Queues
        self.pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_orders: dict[str, ExecutionTask] = {}
        self.completed_orders: list[ExecutionTask] = []

        # Metrics
        self.daily_loss = Decimal('0')
        self.daily_trades = 0
        self.peak_equity = Decimal('0')
        self.current_drawdown = 0.0
        self.metrics_reset_time = datetime.utcnow()

        # Processing task
        self._processing_task: asyncio.Task | None = None

        logger.info("Execution engine initialized")

    async def start(self) -> None:
        """Start the execution engine."""
        if self.state != ExecutionState.IDLE:
            logger.warning(f"Cannot start from state {self.state}")
            return

        self.state = ExecutionState.RUNNING
        self._processing_task = asyncio.create_task(self._process_queue())

        event_bus.emit(Event(
            type=EventType.APP_START,
            timestamp=datetime.utcnow(),
            data={"component": "execution_engine"}
        ))

        logger.info("Execution engine started")

    async def stop(self) -> None:
        """Stop the execution engine."""
        self.state = ExecutionState.STOPPED

        if self._processing_task:
            self._processing_task.cancel()

        # Cancel all pending orders
        while not self.pending_queue.empty():
            try:
                _, task = await self.pending_queue.get()
                logger.info(f"Cancelling pending order {task.task_id}")
            except asyncio.QueueEmpty:
                break

        logger.info("Execution engine stopped")

    def pause(self) -> None:
        """Pause execution engine."""
        self.state = ExecutionState.PAUSED
        logger.info("Execution engine paused")

    def resume(self) -> None:
        """Resume execution engine."""
        if self.state == ExecutionState.PAUSED:
            self.state = ExecutionState.RUNNING
            logger.info("Execution engine resumed")

    def activate_kill_switch(self, reason: str = "") -> None:
        """Activate kill switch to halt all trading.

        Args:
            reason: Reason for activation
        """
        self._kill_switch_active = True
        self.state = ExecutionState.KILL_SWITCH_ACTIVE

        # Cancel all active orders
        for task_id, task in self.active_orders.items():
            asyncio.create_task(self._cancel_order(task))

        # Clear pending queue
        self.pending_queue = asyncio.PriorityQueue()

        event_bus.emit(Event(
            type=EventType.APP_ERROR,
            timestamp=datetime.utcnow(),
            data={
                "error": "KILL_SWITCH_ACTIVATED",
                "reason": reason
            }
        ))

        logger.critical(f"Kill switch activated: {reason}")

    def deactivate_kill_switch(self) -> None:
        """Deactivate kill switch."""
        self._kill_switch_active = False
        self.state = ExecutionState.IDLE
        logger.info("Kill switch deactivated")

    async def submit_order(
        self,
        order_request: OrderRequest,
        broker: BrokerAdapter,
        priority: int = 5,
        manual_approval: bool | None = None,
        ai_analysis: OrderAnalysis | None = None
    ) -> str:
        """Submit an order for execution.

        Args:
            order_request: Order to execute
            broker: Broker to use
            priority: Execution priority (1-10)
            manual_approval: Override manual approval setting
            ai_analysis: Pre-computed AI analysis

        Returns:
            Task ID

        Raises:
            ValueError: If queue is full or kill switch active
        """
        # Check kill switch
        if self._kill_switch_active:
            raise ValueError("Kill switch active - trading halted")

        # Check queue size
        if self.pending_queue.qsize() >= self.max_pending_orders:
            raise ValueError("Execution queue full")

        # Check risk limits
        if not await self._check_risk_limits(order_request):
            raise ValueError("Risk limits exceeded")

        # Create execution task
        task = ExecutionTask(
            task_id=str(uuid4()),
            order_request=order_request,
            broker=broker,
            priority=priority,
            ai_analysis=ai_analysis,
            manual_approval=manual_approval if manual_approval is not None else self.manual_approval_default
        )

        # Add to queue (priority queue uses negative priority for max heap)
        await self.pending_queue.put((-priority, task))

        # Emit event
        event_bus.emit(Event(
            type=EventType.ORDER_CREATED,
            timestamp=datetime.utcnow(),
            data={
                "task_id": task.task_id,
                "symbol": order_request.symbol,
                "side": order_request.side,  # Already a string from Pydantic
                "quantity": str(order_request.quantity)
            }
        ))

        logger.info(f"Order submitted: {task.task_id}")
        return task.task_id

    async def _process_queue(self) -> None:
        """Process orders from the queue."""
        while self.state == ExecutionState.RUNNING:
            try:
                # Check if paused or kill switch active
                if self.state == ExecutionState.PAUSED or self._kill_switch_active:
                    await asyncio.sleep(1)
                    continue

                # Get next task
                try:
                    _, task = await asyncio.wait_for(
                        self.pending_queue.get(),
                        timeout=1.0
                    )
                except TimeoutError:
                    continue

                # Process task
                await self._execute_task(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: ExecutionTask) -> None:
        """Execute a single task.

        Args:
            task: Task to execute
        """
        try:
            if self._is_task_timed_out(task):
                logger.warning(f"Order {task.task_id} timed out")
                return

            # Add to active orders
            self.active_orders[task.task_id] = task

            # Check manual approval
            if task.manual_approval:
                if not await self._get_manual_approval(task):
                    logger.info(f"Order {task.task_id} rejected by user")
                    return

            await self._execute_and_record(task)

        finally:
            # Remove from active orders
            self.active_orders.pop(task.task_id, None)

    def _is_task_timed_out(self, task: ExecutionTask) -> bool:
        return datetime.utcnow() - task.created_at > timedelta(
            seconds=self.order_timeout_seconds
        )

    async def _execute_and_record(self, task: ExecutionTask) -> None:
        try:
            response = await task.broker.place_order(task.order_request)
            await self._store_order(task, response)
            self._emit_order_submitted(task, response)
            self._emit_filled_events(task, response)
            logger.info(f"Order executed: {task.task_id}")
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            await self._handle_execution_retry(task)

    def _emit_order_submitted(self, task: ExecutionTask, response: OrderResponse) -> None:
        event_bus.emit(
            Event(
                type=EventType.ORDER_SUBMITTED,
                timestamp=datetime.utcnow(),
                data={
                    "task_id": task.task_id,
                    "broker_order_id": response.broker_order_id,
                    "status": response.status.value,
                },
                source="execution_engine",
            )
        )

    def _emit_filled_events(self, task: ExecutionTask, response: OrderResponse) -> None:
        if not response.filled_qty or response.filled_qty <= 0:
            return

        from src.common.event_bus import OrderEvent

        side_str = self._order_side_str(task)
        order_type_str = self._order_type_str(task)
        avg_price = response.filled_avg_price or response.limit_price or 0.0

        event_bus.emit(
            OrderEvent(
                type=EventType.ORDER_FILLED,
                timestamp=datetime.utcnow(),
                symbol=task.order_request.symbol,
                order_id=response.broker_order_id,
                order_type=order_type_str,
                side=side_str,
                quantity=task.order_request.quantity,
                filled_quantity=response.filled_qty,
                avg_fill_price=avg_price,
                status="filled",
                data={
                    "symbol": task.order_request.symbol,
                    "order_id": response.broker_order_id,
                    "side": side_str,
                    "filled_quantity": response.filled_qty,
                    "avg_fill_price": avg_price,
                    "order_type": order_type_str,
                },
                source="execution_engine",
            )
        )

        logger.info(
            f"✅ ORDER_FILLED event emitted for {task.order_request.symbol} @ {response.filled_avg_price}"
        )

        self._emit_trade_entry_exit(task, response, side_str, avg_price)

    def _emit_trade_entry_exit(
        self,
        task: ExecutionTask,
        response: OrderResponse,
        side_str: str,
        avg_price: float,
    ) -> None:
        from src.common.event_bus import ExecutionEvent

        is_buy = side_str.upper() in ["BUY", "LONG"]
        trade_id = f"trade_{task.order_request.symbol}_{response.broker_order_id}"

        if is_buy:
            event_bus.emit(
                ExecutionEvent(
                    type=EventType.TRADE_ENTRY,
                    timestamp=datetime.utcnow(),
                    symbol=task.order_request.symbol,
                    trade_id=trade_id,
                    action="entry",
                    side="LONG",
                    quantity=response.filled_qty,
                    price=avg_price,
                    data={
                        "symbol": task.order_request.symbol,
                        "side": "LONG",
                        "quantity": response.filled_qty,
                        "price": avg_price,
                    },
                    source="execution_engine",
                )
            )
            logger.info(f"✅ TRADE_ENTRY event emitted for {task.order_request.symbol}")
            return

        event_bus.emit(
            ExecutionEvent(
                type=EventType.TRADE_EXIT,
                timestamp=datetime.utcnow(),
                symbol=task.order_request.symbol,
                trade_id=trade_id,
                action="exit",
                side="SHORT",  # Exiting long = short action
                quantity=response.filled_qty,
                price=avg_price,
                pnl=None,  # Would need position tracking for real P&L
                pnl_pct=None,
                reason="manual_exit",
                data={
                    "symbol": task.order_request.symbol,
                    "side": "SHORT",
                    "quantity": response.filled_qty,
                    "price": avg_price,
                },
                source="execution_engine",
            )
        )
        logger.info(f"✅ TRADE_EXIT event emitted for {task.order_request.symbol}")

    async def _handle_execution_retry(self, task: ExecutionTask) -> None:
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            logger.info(f"Retrying order {task.task_id} (attempt {task.retry_count})")
            await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
            await self.pending_queue.put((-task.priority, task))
        else:
            logger.error(f"Order {task.task_id} failed after {task.max_retries} retries")

    def _order_side_str(self, task: ExecutionTask) -> str:
        return (
            task.order_request.side.value
            if hasattr(task.order_request.side, "value")
            else str(task.order_request.side)
        )

    def _order_type_str(self, task: ExecutionTask) -> str:
        return (
            task.order_request.order_type.value
            if hasattr(task.order_request.order_type, "value")
            else str(task.order_request.order_type)
        )

    async def _get_manual_approval(self, task: ExecutionTask) -> bool:
        """Get manual approval for order.

        Args:
            task: Task requiring approval

        Returns:
            True if approved, False otherwise
        """
        # Emit approval request event
        event_bus.emit(Event(
            type=EventType.ORDER_APPROVAL_REQUEST,
            timestamp=datetime.utcnow(),
            data={
                "task_id": task.task_id,
                "order": task.order_request.dict(),
                "ai_analysis": task.ai_analysis.dict() if task.ai_analysis else None
            },
            source="execution_engine"
        ))

        # If approval callback provided, use it
        if task.approval_callback:
            return await task.approval_callback(task)

        # Otherwise, wait for approval through event bus
        # (This would be implemented with a proper approval mechanism)
        # For now, auto-approve after delay
        await asyncio.sleep(2)
        return True

    async def _cancel_order(self, task: ExecutionTask) -> None:
        """Cancel an active order.

        Args:
            task: Task to cancel
        """
        try:
            if task.order_request.internal_order_id:
                success = await task.broker.cancel_order(
                    task.order_request.internal_order_id
                )
                if success:
                    logger.info(f"Order {task.task_id} cancelled")
                else:
                    logger.warning(f"Failed to cancel order {task.task_id}")
        except Exception as e:
            logger.error(f"Error cancelling order {task.task_id}: {e}")

    async def _check_risk_limits(self, order: OrderRequest) -> bool:
        """Check if order passes risk limits.

        Args:
            order: Order to check

        Returns:
            True if within limits
        """
        # Reset daily metrics if new day
        if datetime.utcnow().date() > self.metrics_reset_time.date():
            self.daily_loss = Decimal('0')
            self.daily_trades = 0
            self.metrics_reset_time = datetime.utcnow()

        # Check daily loss limit
        if self.daily_loss >= self.max_loss_per_day:
            logger.warning("Daily loss limit exceeded")
            if self.kill_switch_enabled:
                self.activate_kill_switch("Daily loss limit exceeded")
            return False

        # Check drawdown
        if self.current_drawdown >= self.max_drawdown_percent:
            logger.warning("Maximum drawdown exceeded")
            if self.kill_switch_enabled:
                self.activate_kill_switch("Maximum drawdown exceeded")
            return False

        return True

    async def _store_order(self, task: ExecutionTask, response: OrderResponse) -> None:
        """Store order in database.

        Args:
            task: Execution task
            response: Order response from broker
        """
        try:
            db_manager = get_db_manager()
            with db_manager.session() as session:
                db_order = DBOrder(
                    order_id=response.internal_order_id,
                    broker_order_id=response.broker_order_id,
                    symbol=task.order_request.symbol,
                    side=task.order_request.side,
                    order_type=task.order_request.order_type,
                    quantity=task.order_request.quantity,
                    limit_price=task.order_request.limit_price,
                    stop_price=task.order_request.stop_price,
                    time_in_force=task.order_request.time_in_force,
                    status=response.status,
                    strategy_name=task.order_request.strategy_name,
                    signal_confidence=task.order_request.signal_confidence,
                    ai_analysis=task.ai_analysis.dict() if task.ai_analysis else None,
                    manual_override=not task.manual_approval,
                    created_at=task.created_at,
                    submitted_at=datetime.utcnow()
                )
                session.add(db_order)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to store order in database: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get execution engine status.

        Returns:
            Status information
        """
        return {
            "state": self.state.value,
            "kill_switch_active": self._kill_switch_active,
            "pending_orders": self.pending_queue.qsize(),
            "active_orders": len(self.active_orders),
            "completed_orders": len(self.completed_orders),
            "daily_trades": self.daily_trades,
            "daily_loss": float(self.daily_loss),
            "current_drawdown": self.current_drawdown
        }

    async def update_metrics(self, pnl: Decimal, equity: Decimal) -> None:
        """Update risk metrics.

        Args:
            pnl: Daily P&L
            equity: Current equity
        """
        # Increment daily trades
        self.daily_trades += 1

        # Update daily loss
        if pnl < 0:
            self.daily_loss += abs(pnl)

        # Update peak equity and drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = float(
                (self.peak_equity - equity) / self.peak_equity * 100
            ) if self.peak_equity > 0 else 0.0

        # Check kill switch conditions
        if self.kill_switch_enabled:
            # Check max daily loss
            if self.daily_loss >= self.max_loss_per_day:
                self.activate_kill_switch(
                    f"Max daily loss exceeded: ${self.daily_loss} >= ${self.max_loss_per_day}"
                )

            # Check max drawdown
            if self.current_drawdown >= self.max_drawdown_percent:
                self.activate_kill_switch(
                    f"Max drawdown exceeded: {self.current_drawdown:.2f}% >= {self.max_drawdown_percent}%"
                )
