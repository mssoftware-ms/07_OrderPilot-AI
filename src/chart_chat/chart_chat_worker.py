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
            # Verify AI service is available before starting
            if not self.service.ai_service:
                self.error.emit(
                    "AI Service nicht verfügbar. "
                    "Bitte konfiguriere einen AI-Provider in den Einstellungen."
                )
                return

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                if self.action == "full_analysis":
                    # Add timeout to prevent hanging
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            self.service.analyze_chart(),
                            timeout=30.0  # 30 second timeout
                        )
                    )
                elif self.action == "ask" and self.question:
                    # Add timeout to prevent hanging
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            self.service.ask_question(self.question),
                            timeout=30.0  # 30 second timeout
                        )
                    )
                else:
                    self.error.emit("Unbekannte Aktion")
                    return

                self.finished.emit(result)

            except asyncio.TimeoutError:
                logger.error("Analysis request timed out after 30 seconds")
                self.error.emit(
                    "Zeitüberschreitung: Die Anfrage hat zu lange gedauert. "
                    "Bitte überprüfe deine Netzwerkverbindung und API-Konfiguration."
                )
            finally:
                loop.close()

        except Exception as e:
            logger.exception("Analysis worker error")
            error_msg = str(e)
            # Make error messages more user-friendly
            if "API key" in error_msg or "api_key" in error_msg:
                error_msg = (
                    "API-Key fehlt oder ungültig. "
                    "Bitte überprüfe deine AI-Konfiguration."
                )
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                error_msg = (
                    "Netzwerkfehler: Bitte überprüfe deine Internetverbindung."
                )
            self.error.emit(error_msg)
