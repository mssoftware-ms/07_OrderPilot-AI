"""Execution Engine for OrderPilot-AI Trading Application.

Manages order execution with manual approval, queuing, retry logic,
and kill switch functionality.

REFACTORED: Split into focused helper modules.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import uuid4

from src.ai import OrderAnalysis
from src.core.broker import BrokerAdapter, OrderRequest

# Import helpers
from .engine_approval import EngineApproval
from .engine_events import EngineEvents
from .engine_execution import EngineExecution
from .engine_kill_switch import EngineKillSwitch
from .engine_lifecycle import EngineLifecycle
from .engine_persistence import EnginePersistence
from .engine_submission import EngineSubmission

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

        # Initialize helpers
        self._lifecycle = EngineLifecycle(parent=self)
        self._kill_switch = EngineKillSwitch(parent=self)
        self._submission = EngineSubmission(parent=self)
        self._execution = EngineExecution(parent=self)
        self._events = EngineEvents(parent=self)
        self._approval = EngineApproval(parent=self)
        self._persistence = EnginePersistence(parent=self)

        logger.info("Execution engine initialized")

    async def start(self) -> None:
        """Start the execution engine."""
        await self._lifecycle.start()

    async def stop(self) -> None:
        """Stop the execution engine."""
        await self._lifecycle.stop()

    def pause(self) -> None:
        """Pause execution engine."""
        self._lifecycle.pause()

    def resume(self) -> None:
        """Resume execution engine."""
        self._lifecycle.resume()

    def activate_kill_switch(self, reason: str = "") -> None:
        """Activate kill switch to halt all trading."""
        self._kill_switch.activate_kill_switch(reason)

    def deactivate_kill_switch(self) -> None:
        """Deactivate kill switch."""
        self._kill_switch.deactivate_kill_switch()

    async def submit_order(
        self,
        order_request: OrderRequest,
        broker: BrokerAdapter,
        priority: int = 5,
        manual_approval: bool | None = None,
        ai_analysis: OrderAnalysis | None = None
    ) -> str:
        """Submit an order for execution."""
        return await self._submission.submit_order(
            order_request, broker, priority, manual_approval, ai_analysis
        )

    def get_status(self) -> dict[str, Any]:
        """Get execution engine status."""
        return self._persistence.get_status()

    async def update_metrics(self, pnl: Decimal, equity: Decimal) -> None:
        """Update risk metrics."""
        await self._persistence.update_metrics(pnl, equity)
