"""Base Worker for Background Tasks.

Provides common infrastructure for background workers to avoid code duplication.
Uses Template Method Pattern for shared error handling, signals, and lifecycle management.
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)


# Resolve metaclass conflict between QObject and ABC
class QABCMeta(type(QObject), ABCMeta):
    """Metaclass combining Qt's metaclass and Python's ABCMeta."""
    pass


class BaseWorker(QObject, metaclass=QABCMeta):
    """Abstract base class for background workers.

    Provides:
    - Common signal definitions
    - Cancellation mechanism
    - Error handling pattern
    - Template Method for execution flow

    Subclasses must implement:
    - _execute(): Main work implementation
    """

    # Standard signals for all workers
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    finished = pyqtSignal(bool, str, dict)  # (success, message, results)
    error = pyqtSignal(str)  # error_message

    def __init__(self):
        """Initialize base worker."""
        super().__init__()
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the worker.

        Sets internal flag that subclasses should check during execution.
        """
        self._cancelled = True
        logger.info(f"{self.__class__.__name__} cancellation requested")

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested.

        Returns:
            True if worker should stop execution
        """
        return self._cancelled

    def emit_cancellation_result(self, message: str = "Operation cancelled") -> None:
        """Emit cancellation result with standard format.

        Args:
            message: Cancellation message to emit
        """
        logger.info(f"{self.__class__.__name__} cancelled: {message}")
        self.finished.emit(False, message, {})

    def run(self):
        """Execute the worker in background thread.

        Template method that handles error catching and emits error signal.
        Calls _execute() for actual work.
        """
        try:
            self._execute()
        except Exception as e:
            error_msg = f"{self.__class__.__name__} error: {e}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(str(e))

    @abstractmethod
    def _execute(self):
        """Execute the actual work.

        Must be implemented by subclasses.
        Should check self.is_cancelled() periodically.
        Should emit progress signals during execution.
        Should emit finished signal on completion.
        """
        pass


class WorkerThread(QThread):
    """Generic thread wrapper for BaseWorker instances.

    Eliminates need for per-worker thread classes.
    """

    def __init__(self, worker: BaseWorker):
        """Initialize thread wrapper.

        Args:
            worker: Worker instance to run in this thread
        """
        super().__init__()
        self.worker = worker

    def run(self):
        """Run the worker."""
        self.worker.run()


class AsyncBaseWorker(BaseWorker):
    """Base worker with asyncio support.

    For workers that need async/await functionality.
    Manages event loop creation and cleanup.
    """

    def run(self):
        """Execute async worker with event loop management."""
        import asyncio

        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._execute_async())
            finally:
                loop.close()
        except Exception as e:
            error_msg = f"{self.__class__.__name__} error: {e}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(str(e))

    def _execute(self):
        """Not used in AsyncBaseWorker - override _execute_async instead."""
        raise NotImplementedError("AsyncBaseWorker uses _execute_async()")

    @abstractmethod
    async def _execute_async(self):
        """Execute the actual async work.

        Must be implemented by subclasses.
        Should check self.is_cancelled() periodically.
        Should emit progress signals during execution.
        Should emit finished signal on completion.
        """
        pass
