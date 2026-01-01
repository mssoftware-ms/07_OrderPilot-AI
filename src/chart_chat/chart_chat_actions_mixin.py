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

# Import AnalysisWorker here to avoid NameError
from .chart_chat_worker import AnalysisWorker

if TYPE_CHECKING:
    from .chat_service import ChartChatService
    from .models import ChartAnalysisResult, QuickAnswerResult

logger = logging.getLogger(__name__)


class ChartChatActionsMixin:
    """ChartChatActionsMixin extracted from ChartChatWidget."""
    def _on_quick_action(self) -> None:
        """Handle quick action button click."""
        button = self.sender()
        if not button:
            return

        action_type = button.property("action_type")
        question = button.property("question")

        if action_type == "full_analysis":
            self._on_full_analysis()
        elif action_type == "ask" and question:
            self._input_field.setText(question)
            self._on_send()
    def _on_send(self) -> None:
        """Handle send button click."""
        question = self._input_field.text().strip()
        if not question:
            return

        self._input_field.clear()
        self._append_message("user", question)
        self._start_analysis("ask", question)
    def _on_full_analysis(self) -> None:
        """Handle full analysis button click."""
        self._append_message(
            "user",
            f"[Vollständige Chartanalyse angefordert]"
        )
        self._start_analysis("full_analysis")
        # Emit signal with action type (signal expects str argument)
        if hasattr(self, 'analysis_requested'):
            self.analysis_requested.emit("full_analysis")
    def _start_analysis(
        self, action: str, question: str | None = None
    ) -> None:
        """Start background analysis.

        Args:
            action: 'full_analysis' or 'ask'
            question: Optional question for 'ask' action
        """
        # Check if a worker is already running
        if self._worker and self._worker.isRunning():
            logger.warning("Analysis already in progress, ignoring new request")
            self._append_message(
                "assistant",
                "⏳ Bitte warte, bis die aktuelle Anfrage abgeschlossen ist."
            )
            return

        # Check if AI service is available
        if not self.service.ai_service:
            self._append_message(
                "assistant",
                "⚠️ **AI Service nicht verfügbar!**\n\n"
                "Bitte konfiguriere einen AI-Provider:\n"
                "1. Gehe zu File → Settings → AI Tab\n"
                "2. Wähle OpenAI, Anthropic oder Gemini\n"
                "3. Setze den entsprechenden API-Key\n\n"
                "Alternativ kannst du eine Umgebungsvariable setzen:\n"
                "• OPENAI_API_KEY\n"
                "• ANTHROPIC_API_KEY\n"
                "• GEMINI_API_KEY"
            )
            return

        # Check if AI service has required methods
        ai_service = self.service.ai_service
        has_methods = (
            hasattr(ai_service, "complete") or
            hasattr(ai_service, "chat_completion") or
            hasattr(ai_service, "generate")
        )
        if not has_methods:
            self._append_message(
                "assistant",
                f"⚠️ **AI Service fehlerhaft!**\n\n"
                f"Der AI-Service ({type(ai_service).__name__}) unterstützt keine "
                f"bekannte Completion-Methode.\n\n"
                f"Bitte überprüfe deine AI-Konfiguration."
            )
            return

        self._set_loading(True)

        self._worker = AnalysisWorker(self.service, action, question)
        self._worker.finished.connect(self._on_analysis_complete)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()
    def _on_analysis_complete(self, result: Any) -> None:
        """Handle completed analysis.

        Args:
            result: ChartAnalysisResult or QuickAnswerResult
        """
        self._set_loading(False)

        # Clean up worker reference
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

        # Format response based on type
        if hasattr(result, "to_markdown"):
            # ChartAnalysisResult
            content = result.to_markdown()
        elif hasattr(result, "answer"):
            # QuickAnswerResult
            content = result.answer
            if result.follow_up_suggestions:
                content += "\n\n**Weitere Fragen:**\n"
                for suggestion in result.follow_up_suggestions:
                    content += f"- {suggestion}\n"
        else:
            content = str(result)

        self._append_message("assistant", content)
    def _on_analysis_error(self, error: str) -> None:
        """Handle analysis error.

        Args:
            error: Error message
        """
        self._set_loading(False)

        # Clean up worker reference
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

        self._append_message(
            "assistant",
            f"⚠️ **Fehler:** {error}"
        )
    def _set_loading(self, loading: bool) -> None:
        """Set loading state.

        Args:
            loading: True if loading
        """
        self._progress_bar.setVisible(loading)
        self._send_button.setEnabled(not loading)
        self._analyze_button.setEnabled(not loading)
        self._input_field.setEnabled(not loading)
