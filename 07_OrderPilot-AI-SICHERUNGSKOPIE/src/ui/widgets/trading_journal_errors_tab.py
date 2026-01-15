"""Trading Journal - Errors Tab.

Refactored from trading_journal_widget.py monolith.

Module 4/5 of trading_journal_widget.py split.

Contains:
- ErrorsTab: Bot error log display
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


class ErrorsTab(QWidget):
    """Tab für Bot-Fehler."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._errors: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt die UI für die Fehler-Tabelle."""
        layout = QVBoxLayout(self)

        # Tabelle
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Zeit", "Symbol", "Fehlertyp", "Nachricht"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("Clear Errors")
        btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(btn_clear)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def add_error(self, error_data: dict) -> None:
        """Fügt einen Fehler hinzu.

        Args:
            error_data: Dict mit Keys: timestamp, symbol, error_type, message
        """
        self._errors.append(error_data)

        row = self._table.rowCount()
        self._table.insertRow(row)

        self._table.setItem(row, 0, QTableWidgetItem(error_data.get("timestamp", "")))
        self._table.setItem(row, 1, QTableWidgetItem(error_data.get("symbol", "")))
        self._table.setItem(row, 2, QTableWidgetItem(error_data.get("error_type", "")))
        self._table.setItem(row, 3, QTableWidgetItem(error_data.get("message", "")))

    def clear(self) -> None:
        """Löscht alle Fehler."""
        self._errors.clear()
        self._table.setRowCount(0)

    def get_errors(self) -> list[dict]:
        """Gibt alle gespeicherten Fehler zurück."""
        return self._errors
