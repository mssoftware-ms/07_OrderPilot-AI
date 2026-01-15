"""Execution Engine - Task Execution.

Refactored from engine.py monolith.

Module 4/7 of engine.py split.

Contains:
- Task execution
- Timeout checking
- Retry logic
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EngineExecution:
    """Helper für ExecutionEngine task execution."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

    async def execute_task(self, task) -> None:
        """Execute a single task.

        Args:
            task: Task to execute
        """
        try:
            if self.is_task_timed_out(task):
                logger.warning(f"Order {task.task_id} timed out")
                return

            # Add to active orders
            self.parent.active_orders[task.task_id] = task

            # Check manual approval
            if task.manual_approval:
                if not await self.parent._approval.get_manual_approval(task):
                    logger.info(f"Order {task.task_id} rejected by user")
                    return

            await self.execute_and_record(task)

        finally:
            # Remove from active orders
            self.parent.active_orders.pop(task.task_id, None)

    def is_task_timed_out(self, task) -> bool:
        return datetime.utcnow() - task.created_at > timedelta(
            seconds=self.parent.order_timeout_seconds
        )

    async def execute_and_record(self, task) -> None:
        try:
            response = await task.broker.place_order(task.order_request)
            await self.parent._persistence.store_order(task, response)
            self.parent._events.emit_order_submitted(task, response)
            self.parent._events.emit_filled_events(task, response)
            logger.info(f"Order executed: {task.task_id}")
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            await self.handle_execution_retry(task)

    async def handle_execution_retry(self, task) -> None:
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            logger.info(f"Retrying order {task.task_id} (attempt {task.retry_count})")
            await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
            await self.parent.pending_queue.put((-task.priority, task))
        else:
            logger.error(f"Order {task.task_id} failed after {task.max_retries} retries")
