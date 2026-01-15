"""Backtest Tab Logging - Logging and Progress Handlers.

Refactored from backtest_tab_main.py.

Contains:
- _on_progress_updated: Progress bar update handler
- _on_log_message: Log message handler
- _log: Thread-safe logging method
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QTextCursor

if TYPE_CHECKING:
    from .backtest_tab_main import BacktestTab


class BacktestTabLogging:
    """Helper for logging and progress display."""

    def __init__(self, parent: "BacktestTab"):
        self.parent = parent

    @pyqtSlot(int, str)
    def on_progress_updated(self, progress: int, message: str) -> None:
        """Update Progress Bar."""
        self.parent.progress_bar.setValue(progress)
        self.parent.status_detail.setText(message)

    @pyqtSlot(str)
    def on_log_message(self, message: str) -> None:
        """Fügt Log-Nachricht hinzu."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.parent.log_text.append(f"[{timestamp}] {message}")
        self.parent.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def log(self, message: str) -> None:
        """Log-Nachricht (thread-safe)."""
        self.parent.log_message.emit(message)
