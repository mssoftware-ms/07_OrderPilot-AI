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


class ChartChatHistoryMixin:
    """ChartChatHistoryMixin extracted from ChartChatWidget."""
    def _load_existing_history(self) -> None:
        """Load and display existing chat history."""
        for msg in self.service.conversation_history:
            self._append_message(
                msg.role.value if hasattr(msg.role, 'value') else msg.role,
                msg.content,
                msg.timestamp,
            )
    def _append_message(
        self,
        role: str,
        content: str,
        timestamp: datetime | None = None,
    ) -> None:
        """Append a message to the chat display with bubble styling.

        Args:
            role: 'user' or 'assistant'
            content: Message content
            timestamp: Optional timestamp
        """
        ts = timestamp or datetime.now()
        time_str = ts.strftime("%H:%M:%S")

        # Clean up excessive newlines in content
        import re
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Create custom widget for this message
        message_widget = self._create_message_widget(role, content, time_str)

        # Add to list
        item = QListWidgetItem(self._chat_display)
        item.setSizeHint(message_widget.sizeHint())
        self._chat_display.addItem(item)
        self._chat_display.setItemWidget(item, message_widget)

        # Scroll to bottom
        self._chat_display.scrollToBottom()

    def _append_system_message(self, text: str) -> None:
        """Convenience helper to append an assistant/system note."""
        self._append_message("assistant", text)
    def _on_clear_history(self) -> None:
        """Handle clear history button click."""
        self.service.clear_history()
        self._chat_display.clear()

        # Add welcome message back
        self._append_message(
            "assistant",
            "Chat-Verlauf wurde gelöscht. Wie kann ich dir helfen?"
        )
