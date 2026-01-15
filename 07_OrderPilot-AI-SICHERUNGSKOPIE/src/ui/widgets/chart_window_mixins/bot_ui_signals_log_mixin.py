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
        """Create Trading Bot Log group for Signals tab (Issue #23).

        Issue #2: Creates two side-by-side log sections:
        - Left: Log Trading Bot (filtered logs)
        - Right: KI Nachrichten (unfiltered AI output) with Prompt Management button
        """
        # Main container
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Left section: Log Trading Bot
        left_group = self._create_bot_log_section()
        main_layout.addWidget(left_group, stretch=1)

        # Right section: KI Nachrichten (Issue #2)
        right_group = self._create_ki_messages_section()
        main_layout.addWidget(right_group, stretch=1)

        return container

    def _create_bot_log_section(self) -> QGroupBox:
        """Create the filtered Trading Bot Log section."""
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

    def _create_ki_messages_section(self) -> QGroupBox:
        """Create the unfiltered KI Messages section (Issue #2)."""
        group = QGroupBox("KI Nachrichten")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Info label
        info_row = QHBoxLayout()
        info_label = QLabel("Ungefilterte Ausgaben vom Trading Bot")
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        info_row.addWidget(info_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        # KI Messages text field
        self.ki_messages_text = QPlainTextEdit()
        self.ki_messages_text.setReadOnly(True)
        self.ki_messages_text.setPlaceholderText("Ungefilterte KI-Ausgaben erscheinen hier...")
        self.ki_messages_text.setMinimumHeight(140)
        self.ki_messages_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d0d0d;
                color: #4CAF50;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.ki_messages_text)

        # Buttons
        btn_row = QHBoxLayout()

        # Prompt Management button (Issue #2)
        self.prompt_mgmt_btn = QPushButton("⚙️ Prompts verwalten")
        self.prompt_mgmt_btn.setToolTip("Öffnet Dialog zur Verwaltung und Bearbeitung der Bot-Prompts")
        self.prompt_mgmt_btn.clicked.connect(self._open_prompt_management)
        btn_row.addWidget(self.prompt_mgmt_btn)

        self.ki_messages_save_btn = QPushButton("💾 Speichern")
        self.ki_messages_save_btn.clicked.connect(self._save_ki_messages)
        btn_row.addWidget(self.ki_messages_save_btn)

        self.ki_messages_clear_btn = QPushButton("🧹 Leeren")
        self.ki_messages_clear_btn.clicked.connect(self._clear_ki_messages)
        btn_row.addWidget(self.ki_messages_clear_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return group

    def _append_ki_message(self, message: str, timestamp: str | None = None) -> None:
        """Append an unfiltered KI message to the KI Messages log (Issue #2).

        Args:
            message: The raw message from the KI/Trading Bot
            timestamp: Optional timestamp, defaults to current time
        """
        if not hasattr(self, 'ki_messages_text') or self.ki_messages_text is None:
            return
        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {message}"
        self.ki_messages_text.appendPlainText(entry)

    def _clear_ki_messages(self) -> None:
        """Clear all KI messages (Issue #2)."""
        if hasattr(self, 'ki_messages_text'):
            self.ki_messages_text.clear()

    def _save_ki_messages(self) -> None:
        """Save KI messages to file (Issue #2)."""
        if not hasattr(self, 'ki_messages_text'):
            return
        content = self.ki_messages_text.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Keine Nachrichten", "Es sind keine KI-Nachrichten vorhanden.")
            return
        default_name = f"ki_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "KI-Nachrichten speichern",
            default_name,
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)",
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Gespeichert", f"KI-Nachrichten gespeichert: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"KI-Nachrichten konnten nicht gespeichert werden: {e}")

    def _open_prompt_management(self) -> None:
        """Open the Prompt Management dialog (Issue #2)."""
        try:
            from src.ui.dialogs.prompt_management_dialog import PromptManagementDialog
            dialog = PromptManagementDialog(self)
            dialog.exec()
        except (ImportError, ModuleNotFoundError):
            # Fallback if dialog doesn't exist yet
            QMessageBox.information(
                self,
                "Prompt Management",
                "Prompt Management Dialog ist in Entwicklung.\n\n"
                "Hier werden Sie zukünftig die Bot-Prompts verwalten können."
            )

