from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QProgressBar, QPushButton, QSplitter, QTableWidget, QVBoxLayout, QWidget,
    QMessageBox, QPlainTextEdit, QFileDialog
)

from .bot_sltp_progressbar import SLTPProgressBar

logger = logging.getLogger(__name__)

class BotUISignalsLogMixin:
    """Bot log management"""

    def _append_bot_log(self, log_type: str, message: str, timestamp: str | None = None) -> None:
        """Append a log line to the Trading Bot Log UI."""
        if not hasattr(self, 'bot_log_text') or self.bot_log_text is None:
            return
        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] [{log_type.upper()}] {message}"
        self.bot_log_text.appendPlainText(entry)

    def _set_bot_run_status_label(self, running: bool) -> None:
        if not hasattr(self, 'bot_run_status_label'):
            return
        color = "#26a69a" if running else "#9e9e9e"
        state = "RUNNING" if running else "STOPPED"
        self.bot_run_status_label.setText(f"Status: {state}")
        self.bot_run_status_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def _clear_bot_log(self) -> None:
        if hasattr(self, 'bot_log_text'):
            self.bot_log_text.clear()

    def _save_bot_log(self) -> None:
        if not hasattr(self, 'bot_log_text'):
            return
        content = self.bot_log_text.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Keine Logs", "Es sind keine Log-Einträge vorhanden.")
            return
        default_name = f"trading_bot_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Log speichern",
            default_name,
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)",
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Gespeichert", f"Log gespeichert: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Log konnte nicht gespeichert werden: {e}")

    def _build_bot_log_widget(self) -> QWidget:
        """Create Trading Bot Log group for Signals tab (Issue #23)."""
        group = QGroupBox("Log Trading Bot")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Status label
        status_row = QHBoxLayout()
        self.bot_run_status_label = QLabel("Status: STOPPED")
        self.bot_run_status_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
        status_row.addWidget(self.bot_run_status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Log text field
        self.bot_log_text = QPlainTextEdit()
        self.bot_log_text.setReadOnly(True)
        self.bot_log_text.setPlaceholderText("Bot-Aktivitäten, Status und Fehler werden hier protokolliert...")
        self.bot_log_text.setMinimumHeight(140)
        layout.addWidget(self.bot_log_text)

        # Buttons
        btn_row = QHBoxLayout()
        self.bot_log_save_btn = QPushButton("💾 Speichern")
        self.bot_log_save_btn.clicked.connect(self._save_bot_log)
        btn_row.addWidget(self.bot_log_save_btn)

        self.bot_log_clear_btn = QPushButton("🧹 Leeren")
        self.bot_log_clear_btn.clicked.connect(self._clear_bot_log)
        btn_row.addWidget(self.bot_log_clear_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return group

