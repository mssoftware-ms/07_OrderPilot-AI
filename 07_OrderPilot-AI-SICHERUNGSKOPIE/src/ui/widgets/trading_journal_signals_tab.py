"""Trading Journal - Signals Tab.

Refactored from trading_journal_widget.py monolith.

Module 1/5 of trading_journal_widget.py split.

Contains:
- SignalsTab: Signal history table + Trading Bot Log
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QGroupBox,
    QTextEdit,
    QLabel,
    QSplitter,
    QFileDialog,
    QMessageBox,
)


class SignalsTab(QWidget):
    """Tab für Signal-Historie (Entry-Signale des Bots) + Trading Bot Log."""

    # Signal emitted when bot status changes (for external listeners)
    bot_status_changed = pyqtSignal(bool)  # is_running

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._signals: list[dict] = []
        self._log_entries: list[str] = []
        self._is_bot_running = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt die UI für die Signal-Tabelle und Trading Bot Log."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Use splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # === TOP SECTION: Signal Table ===
        signals_widget = QWidget()
        signals_layout = QVBoxLayout(signals_widget)
        signals_layout.setContentsMargins(0, 0, 0, 0)

        # Tabelle
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Zeit", "Symbol", "Richtung", "Score", "Quality", "Gate", "Trigger"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 5px;
                font-weight: bold;
                border: 1px solid #444;
            }
        """)
        signals_layout.addWidget(self._table)

        # Signal Buttons
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("Clear Signals")
        btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(btn_clear)
        btn_layout.addStretch()
        signals_layout.addLayout(btn_layout)

        splitter.addWidget(signals_widget)

        # === BOTTOM SECTION: Trading Bot Log ===
        self._setup_bot_log_section(splitter)

        # Set splitter sizes (50% top, 50% bottom)
        splitter.setSizes([250, 250])

        layout.addWidget(splitter)

    def _setup_bot_log_section(self, splitter: QSplitter) -> None:
        """Setup the Trading Bot Log section."""
        log_group = QGroupBox("🤖 Trading Bot Log")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(6)

        # Status row: Running label + buttons
        status_row = QHBoxLayout()

        # Running indicator
        self._running_indicator = QLabel("●")
        self._running_indicator.setStyleSheet("font-size: 16px; color: #666;")
        status_row.addWidget(self._running_indicator)

        self._running_label = QLabel("Stopped")
        self._running_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #888;")
        status_row.addWidget(self._running_label)

        status_row.addStretch()

        # Clear button
        self._btn_clear_log = QPushButton("🗑️ Clear")
        self._btn_clear_log.setToolTip("Log-Einträge löschen")
        self._btn_clear_log.clicked.connect(self.clear_log)
        self._btn_clear_log.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 5px 12px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #666; }
        """)
        status_row.addWidget(self._btn_clear_log)

        # Save button
        self._btn_save_log = QPushButton("💾 Save")
        self._btn_save_log.setToolTip("Log in Datei speichern")
        self._btn_save_log.clicked.connect(self.save_log)
        self._btn_save_log.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 12px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        status_row.addWidget(self._btn_save_log)

        log_layout.addLayout(status_row)

        # Current task label
        task_row = QHBoxLayout()
        task_row.addWidget(QLabel("Aktuelle Aufgabe:"))
        self._current_task_label = QLabel("—")
        self._current_task_label.setStyleSheet("""
            font-weight: bold;
            color: #4CAF50;
            padding: 2px 8px;
            background-color: #1e1e1e;
            border-radius: 3px;
        """)
        task_row.addWidget(self._current_task_label, 1)
        log_layout.addLayout(task_row)

        # Log text field
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setPlaceholderText(
            "Bot-Aktivitäten werden hier angezeigt...\n"
            "Starten Sie den Trading Bot um Log-Einträge zu sehen."
        )
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self._log_text)

        splitter.addWidget(log_group)

    def add_signal(self, signal_data: dict) -> None:
        """Fügt ein Signal zur Historie hinzu.

        Args:
            signal_data: Dict mit Keys: timestamp, symbol, direction, entry_score, quality_state, gate_status, trigger_status
        """
        self._signals.append(signal_data)

        row = self._table.rowCount()
        self._table.insertRow(row)

        self._table.setItem(row, 0, QTableWidgetItem(signal_data.get("timestamp", "")))
        self._table.setItem(row, 1, QTableWidgetItem(signal_data.get("symbol", "")))
        self._table.setItem(row, 2, QTableWidgetItem(signal_data.get("direction", "")))
        self._table.setItem(row, 3, QTableWidgetItem(str(signal_data.get("entry_score", ""))))
        self._table.setItem(row, 4, QTableWidgetItem(signal_data.get("quality_state", "")))
        self._table.setItem(row, 5, QTableWidgetItem(signal_data.get("gate_status", "")))
        self._table.setItem(row, 6, QTableWidgetItem(signal_data.get("trigger_status", "")))

    def clear(self) -> None:
        """Löscht alle Signale."""
        self._signals.clear()
        self._table.setRowCount(0)

    def get_signals(self) -> list[dict]:
        """Gibt alle gespeicherten Signale zurück."""
        return self._signals

    # ==================== Trading Bot Log Methods ====================

    def append_log(self, log_type: str, message: str) -> None:
        """Fügt einen Log-Eintrag hinzu.

        Args:
            log_type: Log-Typ (z.B. "INFO", "SIGNAL", "TRADE", "ERROR", "SCORE", etc.)
            message: Log-Nachricht
        """
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        full_entry = f"[{timestamp}] [{log_type}] {message}"
        self._log_entries.append(full_entry)

        # Format with color based on log type
        color = self._get_log_color(log_type)
        formatted_html = f'<span style="color: {color};">{full_entry}</span>'

        # Append to text edit
        cursor = self._log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log_text.setTextCursor(cursor)
        self._log_text.insertHtml(formatted_html + "<br>")

        # Auto-scroll to bottom
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # Update current task for specific log types
        if log_type in ("STATE", "SIGNAL", "TRADE", "ANALYZING", "ENTRY", "EXIT"):
            self.set_current_task(message)

    def _get_log_color(self, log_type: str) -> str:
        """Returns color for log type."""
        colors = {
            "INFO": "#d4d4d4",
            "DEBUG": "#888888",
            "STATE": "#2196F3",
            "SIGNAL": "#9C27B0",
            "SCORE": "#03A9F4",
            "TRADE": "#4CAF50",
            "ENTRY": "#4CAF50",
            "EXIT": "#FF9800",
            "ERROR": "#F44336",
            "WARNING": "#FFC107",
            "BLOCKED": "#FF5722",
            "UNBLOCKED": "#8BC34A",
            "BIAS": "#E91E63",
            "STRATEGY": "#00BCD4",
            "REGIME": "#673AB7",
            "PATTERN_WARN": "#FF9800",
            "ANALYZING": "#03A9F4",
            "POSITION": "#4CAF50",
            "TRAILING": "#FF9800",
            "SL_UPDATE": "#FFC107",
        }
        return colors.get(log_type.upper(), "#d4d4d4")

    def set_current_task(self, task: str) -> None:
        """Setzt die aktuelle Bot-Aufgabe.

        Args:
            task: Beschreibung der aktuellen Aufgabe
        """
        # Truncate long messages
        display_task = task[:80] + "..." if len(task) > 80 else task
        self._current_task_label.setText(display_task)
        self._current_task_label.setToolTip(task)

    def set_bot_running(self, is_running: bool) -> None:
        """Aktualisiert den Running-Status.

        Args:
            is_running: True wenn Bot läuft
        """
        self._is_bot_running = is_running

        if is_running:
            self._running_indicator.setStyleSheet("font-size: 16px; color: #4CAF50;")
            self._running_label.setText("Running")
            self._running_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #4CAF50;")
            self.append_log("STATE", "Trading Bot gestartet")
        else:
            self._running_indicator.setStyleSheet("font-size: 16px; color: #666;")
            self._running_label.setText("Stopped")
            self._running_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #888;")
            self._current_task_label.setText("—")
            self.append_log("STATE", "Trading Bot gestoppt")

        self.bot_status_changed.emit(is_running)

    def clear_log(self) -> None:
        """Löscht alle Log-Einträge."""
        self._log_entries.clear()
        self._log_text.clear()
        self._current_task_label.setText("—")

    def save_log(self) -> None:
        """Speichert Log in eine Datei."""
        if not self._log_entries:
            QMessageBox.information(self, "Keine Logs", "Es sind keine Log-Einträge vorhanden.")
            return

        # Default filename with timestamp
        default_name = f"trading_bot_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        default_path = Path.home() / "Documents" / default_name

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Log speichern",
            str(default_path),
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("TRADING BOT LOG\n")
                    f.write(f"Exportiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Einträge: {len(self._log_entries)}\n")
                    f.write("=" * 60 + "\n\n")
                    for entry in self._log_entries:
                        f.write(entry + "\n")

                QMessageBox.information(
                    self,
                    "Gespeichert",
                    f"Log erfolgreich gespeichert:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Fehler beim Speichern:\n{e}"
                )

    def get_log_entries(self) -> list[str]:
        """Gibt alle Log-Einträge zurück."""
        return self._log_entries.copy()

    def is_bot_running(self) -> bool:
        """Gibt zurück ob der Bot läuft."""
        return self._is_bot_running
