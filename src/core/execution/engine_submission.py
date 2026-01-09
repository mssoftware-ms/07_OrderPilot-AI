"""Execution Engine - Order Submission.

Refactored from engine.py monolith.

Module 3/7 of engine.py split.

Contains:
- Order submission
- Risk limits checking
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from src.ai import OrderAnalysis
from src.common.event_bus import Event, EventType, event_bus
from src.core.broker import BrokerAdapter, OrderRequest

logger = logging.getLogger(__name__)


class EngineSubmission:
    """Helper für ExecutionEngine order submission."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

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
        from ..execution.engine import ExecutionTask

        # Check kill switch
        if self.parent._kill_switch_active:
            raise ValueError("Kill switch active - trading halted")

        # Check queue size
        if self.parent.pending_queue.qsize() >= self.parent.max_pending_orders:
            raise ValueError("Execution queue full")

        # Check risk limits
        if not await self.check_risk_limits(order_request):
            raise ValueError("Risk limits exceeded")

        # Create execution task
        task = ExecutionTask(
            task_id=str(uuid4()),
            order_request=order_request,
            broker=broker,
            priority=priority,
            ai_analysis=ai_analysis,
            manual_approval=manual_approval if manual_approval is not None else self.parent.manual_approval_default
        )

        # Add to queue (priority queue uses negative priority for max heap)
        await self.parent.pending_queue.put((-priority, task))

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

    async def check_risk_limits(self, order: OrderRequest) -> bool:
        """Check if order passes risk limits.

        Args:
            order: Order to check

        Returns:
            True if within limits
        """
        # Reset daily metrics if new day
        if datetime.utcnow().date() > self.parent.metrics_reset_time.date():
            self.parent.daily_loss = Decimal('0')
            self.parent.daily_trades = 0
            self.parent.metrics_reset_time = datetime.utcnow()

        # Check daily loss limit
        if self.parent.daily_loss >= self.parent.max_loss_per_day:
            logger.warning("Daily loss limit exceeded")
            if self.parent.kill_switch_enabled:
                self.parent._kill_switch.activate_kill_switch("Daily loss limit exceeded")
            return False

        # Check drawdown
        if self.parent.current_drawdown >= self.parent.max_drawdown_percent:
            logger.warning("Maximum drawdown exceeded")
            if self.parent.kill_switch_enabled:
                self.parent._kill_switch.activate_kill_switch("Maximum drawdown exceeded")
            return False

        return True
