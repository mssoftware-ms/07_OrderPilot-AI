"""
Backtest Tab Worker - Background thread for batch processing.

Provides non-blocking batch test execution via QThread.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BatchTestWorker(QThread):
    """Worker thread to run batch tests without blocking the UI."""

    progress = pyqtSignal(int, str)  # progress_pct, message
    log = pyqtSignal(str)
    finished = pyqtSignal(object, list)  # summary, results
    error = pyqtSignal(str)

    def __init__(
        self,
        batch_config,
        *,
        signal_callback: Callable | None,
        initial_data: Any | None = None,  # pd.DataFrame
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize batch test worker.

        Args:
            batch_config: Batch configuration dict
            signal_callback: Optional signal generation callback
            initial_data: Optional pre-loaded DataFrame
            parent: Parent widget
        """
        super().__init__(parent)
        self._batch_config = batch_config
        self._signal_callback = signal_callback
        self._initial_data = initial_data

    def run(self) -> None:
        """Execute batch test in background thread."""
        try:
            self.log.emit("🧵 Batch-Worker gestartet (separater Thread)")
            from src.core.backtesting import BatchRunner

            runner = BatchRunner(
                self._batch_config,
                signal_callback=self._signal_callback,
                initial_data=self._initial_data,
            )
            runner.set_progress_callback(lambda p, m: self.progress.emit(p, m))

            summary = asyncio.run(runner.run())
            self.finished.emit(summary, runner.results)
        except Exception as exc:
            logger.exception("Batch worker failed")
            self.error.emit(str(exc))
