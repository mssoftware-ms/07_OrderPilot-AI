"""Execution Engine - Approval & Cancellation.

Refactored from engine.py monolith.

Module 6/7 of engine.py split.

Contains:
- Manual approval handling
- Order cancellation
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from src.common.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class EngineApproval:
    """Helper für ExecutionEngine approval & cancellation."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

    async def get_manual_approval(self, task) -> bool:
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

    async def cancel_order(self, task) -> None:
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
