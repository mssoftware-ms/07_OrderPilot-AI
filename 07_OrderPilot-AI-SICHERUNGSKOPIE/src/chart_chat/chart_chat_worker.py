from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QFont
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

            # Create a fresh event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Ensure AI service session is initialized with the current loop
                # This is critical to avoid "Event loop is closed" errors
                if hasattr(self.service.ai_service, 'close'):
                    # Close old session if it exists (may be tied to old loop)
                    await_task = self.service.ai_service.close()
                    if await_task:
                        loop.run_until_complete(await_task)

                if hasattr(self.service.ai_service, 'initialize'):
                    # Initialize with fresh session on current loop
                    loop.run_until_complete(self.service.ai_service.initialize())

                # Now run the actual analysis
                if self.action == "full_analysis":
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            self.service.analyze_chart(),
                            timeout=30.0
                        )
                    )
                elif self.action == "ask" and self.question:
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            self.service.ask_question(self.question),
                            timeout=30.0
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
                # Clean up: close AI service session and loop
                try:
                    if hasattr(self.service.ai_service, 'close'):
                        close_task = self.service.ai_service.close()
                        if close_task:
                            loop.run_until_complete(close_task)
                except Exception as e:
                    logger.warning(f"Error closing AI service: {e}")

                # Close the loop to free resources
                try:
                    loop.close()
                except Exception:
                    pass

                # Clear loop from thread
                asyncio.set_event_loop(None)

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
