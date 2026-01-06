from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

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


class ChartChatExportMixin:
    """ChartChatExportMixin extracted from ChartChatWidget."""
    def _on_export(self) -> None:
        """Handle export button click."""
        from PyQt6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Chat exportieren",
            f"chat_{self.service.current_symbol}_{self.service.current_timeframe}.md",
            "Markdown (*.md)",
        )

        if filename:
            self._export_to_markdown(filename)
    def _export_to_markdown(self, filename: str) -> None:
        """Export chat history to Markdown file.

        Args:
            filename: Output file path
        """
        lines = [
            f"# Chart Analysis Chat",
            f"**Symbol:** {self.service.current_symbol}",
            f"**Timeframe:** {self.service.current_timeframe}",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
        ]

        for msg in self.service.conversation_history:
            ts = msg.timestamp.strftime("%Y-%m-%d %H:%M")
            role = "Du" if msg.role.value == "user" else "AI"
            lines.append(f"### [{ts}] {role}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            logger.info("Chat exported to %s", filename)
        except Exception as e:
            logger.error("Export failed: %s", e)
