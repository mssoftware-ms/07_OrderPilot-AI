"""Execution Engine - Order Submission.

Refactored from engine.py monolith.

Module 3/7 of engine.py split.

Contains:
- Order submission
- Risk limits checking
- Duplicate order prevention (BLOCKER #9)
- Pre-trade risk validation (BLOCKER #9)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from src.ai import OrderAnalysis
from src.common.event_bus import Event, EventType, event_bus
from src.core.broker import BrokerAdapter, OrderRequest

if TYPE_CHECKING:
    from src.core.tradingbot.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class EngineSubmission:
    """Helper für ExecutionEngine order submission."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

        # BLOCKER #9 FIX: Duplicate order prevention
        # Track recent orders: key -> (timestamp, order_request)
        self._recent_orders: dict[str, tuple[datetime, OrderRequest]] = {}
        self._duplicate_window_seconds = 5  # Time window to check for duplicates

        # BLOCKER #9 FIX: Pre-trade risk validation
        # Optional RiskManager for pre-trade validation
        self._risk_manager: RiskManager | None = None

    def set_risk_manager(self, risk_manager: RiskManager) -> None:
        """Set risk manager for pre-trade validation.

        Args:
            risk_manager: RiskManager instance for validation
        """
        self._risk_manager = risk_manager
        logger.info("RiskManager set for pre-trade validation")

    def _check_duplicate_order(self, order_request: OrderRequest) -> None:
        """Check for duplicate orders within time window.

        Args:
            order_request: Order to check

        Raises:
            ValueError: If duplicate order detected
        """
        # Create unique key for this order
        order_key = f"{order_request.symbol}_{order_request.side}_{order_request.quantity}"

        # Clean up old entries (older than window)
        now = datetime.utcnow()
        expired_keys = [
            key for key, (timestamp, _) in self._recent_orders.items()
            if (now - timestamp).total_seconds() > self._duplicate_window_seconds
        ]
        for key in expired_keys:
            del self._recent_orders[key]

        # Check for duplicate
        if order_key in self._recent_orders:
            last_time, last_order = self._recent_orders[order_key]
            seconds_ago = (now - last_time).total_seconds()

            if seconds_ago < self._duplicate_window_seconds:
                logger.warning(
                    f"Duplicate order detected: {order_key} "
                    f"(previous order {seconds_ago:.1f}s ago)"
                )
                raise ValueError(
                    f"Duplicate order detected for {order_request.symbol} "
                    f"{order_request.side} {order_request.quantity} within "
                    f"{self._duplicate_window_seconds} seconds"
                )

        # Record this order
        self._recent_orders[order_key] = (now, order_request)

    def _validate_with_risk_manager(self, order_request: OrderRequest) -> None:
        """Validate order with RiskManager before execution.

        Args:
            order_request: Order to validate

        Raises:
            ValueError: If risk validation fails
        """
        if self._risk_manager is None:
            # No risk manager configured, skip validation
            logger.debug("No RiskManager configured, skipping pre-trade validation")
            return

        # Check if trading is allowed
        can_trade, reasons = self._risk_manager.can_trade()

        if not can_trade:
            reasons_str = ", ".join(reasons)
            logger.warning(
                f"RiskManager blocked order for {order_request.symbol}: {reasons_str}"
            )
            raise ValueError(f"Risk validation failed: {reasons_str}")

        logger.debug(f"RiskManager pre-trade validation passed for {order_request.symbol}")

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
            ValueError: If queue is full, kill switch active, duplicate order,
                       or risk validation fails
        """
        from ..execution.engine import ExecutionTask

        # Check kill switch
        if self.parent._kill_switch_active:
            raise ValueError("Kill switch active - trading halted")

        # Check queue size
        if self.parent.pending_queue.qsize() >= self.parent.max_pending_orders:
            raise ValueError("Execution queue full")

        # BLOCKER #9 FIX: Pre-trade risk validation
        self._validate_with_risk_manager(order_request)

        # BLOCKER #9 FIX: Duplicate order prevention
        self._check_duplicate_order(order_request)

        # Check risk limits (existing check)
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
