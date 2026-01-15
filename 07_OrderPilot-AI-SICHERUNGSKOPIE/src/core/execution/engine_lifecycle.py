"""Execution Engine - Lifecycle Management.

Refactored from engine.py monolith.

Module 1/7 of engine.py split.

Contains:
- Start/stop/pause/resume operations
- Queue processing loop
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from src.common.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class EngineLifecycle:
    """Helper für ExecutionEngine lifecycle management."""

    def __init__(self, parent):
        """
        Args:
            parent: ExecutionEngine Instanz
        """
        self.parent = parent

    async def start(self) -> None:
        """Start the execution engine."""
        from ..execution.engine import ExecutionState

        if self.parent.state != ExecutionState.IDLE:
            logger.warning(f"Cannot start from state {self.parent.state}")
            return

        self.parent.state = ExecutionState.RUNNING
        self.parent._processing_task = asyncio.create_task(self.process_queue())

        event_bus.emit(Event(
            type=EventType.APP_START,
            timestamp=datetime.utcnow(),
            data={"component": "execution_engine"}
        ))

        logger.info("Execution engine started")

    async def stop(self) -> None:
        """Stop the execution engine."""
        from ..execution.engine import ExecutionState

        self.parent.state = ExecutionState.STOPPED

        if self.parent._processing_task:
            self.parent._processing_task.cancel()

        # Cancel all pending orders
        while not self.parent.pending_queue.empty():
            try:
                _, task = await self.parent.pending_queue.get()
                logger.info(f"Cancelling pending order {task.task_id}")
            except asyncio.QueueEmpty:
                break

        logger.info("Execution engine stopped")

    def pause(self) -> None:
        """Pause execution engine."""
        from ..execution.engine import ExecutionState

        self.parent.state = ExecutionState.PAUSED
        logger.info("Execution engine paused")

    def resume(self) -> None:
        """Resume execution engine."""
        from ..execution.engine import ExecutionState

        if self.parent.state == ExecutionState.PAUSED:
            self.parent.state = ExecutionState.RUNNING
            logger.info("Execution engine resumed")

    async def process_queue(self) -> None:
        """Process orders from the queue."""
        from ..execution.engine import ExecutionState

        while self.parent.state == ExecutionState.RUNNING:
            try:
                # Check if paused or kill switch active
                if self.parent.state == ExecutionState.PAUSED or self.parent._kill_switch_active:
                    await asyncio.sleep(1)
                    continue

                # Get next task
                try:
                    _, task = await asyncio.wait_for(
                        self.parent.pending_queue.get(),
                        timeout=1.0
                    )
                except TimeoutError:
                    continue

                # Process task
                await self.parent._execution.execute_task(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(1)
