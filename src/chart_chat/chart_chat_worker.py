from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from .chat_service import ChartChatService
    from .models import ChartAnalysisResult, QuickAnswerResult

logger = logging.getLogger(__name__)

class AnalysisWorker(QThread):
    """Background worker for AI analysis calls."""

    finished = pyqtSignal(object)  # ChartAnalysisResult or QuickAnswerResult
    error = pyqtSignal(str)

    def __init__(
        self,
        service: "ChartChatService",
        action: str,
        question: str | None = None,
    ):
        super().__init__()
        self.service = service
        self.action = action
        self.question = question

    def run(self) -> None:
        """Execute the AI call in background."""
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.action == "full_analysis":
                result = loop.run_until_complete(self.service.analyze_chart())
            elif self.action == "ask" and self.question:
                result = loop.run_until_complete(
                    self.service.ask_question(self.question)
                )
            else:
                self.error.emit("Unbekannte Aktion")
                return

            loop.close()
            self.finished.emit(result)

        except Exception as e:
            logger.exception("Analysis worker error")
            self.error.emit(str(e))
