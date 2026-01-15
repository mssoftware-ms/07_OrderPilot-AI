"""Execution Engine - Kill Switch.

Refactored from engine.py monolith.

Module 2/7 of engine.py split.

Contains:
- Kill switch activation/deactivation
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from src.common.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class EngineKillSwitch:
    """Helper für ExecutionEngine kill switch."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

    def activate_kill_switch(self, reason: str = "") -> None:
        """Activate kill switch to halt all trading.

        Args:
            reason: Reason for activation
        """
        from ..execution.engine import ExecutionState

        self.parent._kill_switch_active = True
        self.parent.state = ExecutionState.KILL_SWITCH_ACTIVE

        # Cancel all active orders
        for task_id, task in self.parent.active_orders.items():
            asyncio.create_task(self.parent._approval.cancel_order(task))

        # Clear pending queue
        self.parent.pending_queue = asyncio.PriorityQueue()

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
        from ..execution.engine import ExecutionState

        self.parent._kill_switch_active = False
        self.parent.state = ExecutionState.IDLE
        logger.info("Kill switch deactivated")
