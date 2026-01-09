"""Trading Journal - Signals Tab.

Refactored from trading_journal_widget.py monolith.

Module 1/5 of trading_journal_widget.py split.

Contains:
- SignalsTab: Signal history table
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
)


class SignalsTab(QWidget):
    """Tab für Signal-Historie (Entry-Signale des Bots)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._signals: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt die UI für die Signal-Tabelle."""
        layout = QVBoxLayout(self)

        # Tabelle
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Zeit", "Symbol", "Richtung", "Score", "Quality", "Gate", "Trigger"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("Clear Signals")
        btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(btn_clear)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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
