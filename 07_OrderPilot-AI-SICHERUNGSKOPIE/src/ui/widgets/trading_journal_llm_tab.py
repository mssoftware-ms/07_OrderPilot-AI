"""Trading Journal - LLM Outputs Tab.

Refactored from trading_journal_widget.py monolith.

Module 3/5 of trading_journal_widget.py split.

Contains:
- LLMOutputsTab: LLM validation outputs with JSON viewer
"""

from __future__ import annotations

import json
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QTextEdit,
    QSplitter,
    QHeaderView,
)
from PyQt6.QtCore import Qt


class LLMOutputsTab(QWidget):
    """Tab für LLM-Validierungsausgaben."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._outputs: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt die UI für die LLM-Ausgaben."""
        layout = QVBoxLayout(self)

        # Splitter: Tabelle oben, Details unten
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Tabelle
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Zeit", "Symbol", "Richtung", "Ergebnis", "Reason"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._table)

        # Detail-Ansicht (JSON)
        self._detail_view = QTextEdit()
        self._detail_view.setReadOnly(True)
        splitter.addWidget(self._detail_view)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("Clear Outputs")
        btn_clear.clicked.connect(self.clear)
        btn_layout.addWidget(btn_clear)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def add_output(self, output_data: dict) -> None:
        """Fügt eine LLM-Ausgabe hinzu.

        Args:
            output_data: Dict mit Keys: timestamp, symbol, direction, approved, reason, raw_response, etc.
        """
        self._outputs.append(output_data)

        row = self._table.rowCount()
        self._table.insertRow(row)

        self._table.setItem(row, 0, QTableWidgetItem(output_data.get("timestamp", "")))
        self._table.setItem(row, 1, QTableWidgetItem(output_data.get("symbol", "")))
        self._table.setItem(row, 2, QTableWidgetItem(output_data.get("direction", "")))

        # Ergebnis (approved/rejected)
        result = "✓ Approved" if output_data.get("approved") else "✗ Rejected"
        self._table.setItem(row, 3, QTableWidgetItem(result))

        # Reason (gekürzt für Tabelle)
        reason = output_data.get("reason", "")
        if len(reason) > 50:
            reason = reason[:47] + "..."
        self._table.setItem(row, 4, QTableWidgetItem(reason))

        # Speichere den kompletten Output als UserRole
        self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, output_data)

    def _on_selection_changed(self) -> None:
        """Zeigt Details zur ausgewählten LLM-Ausgabe."""
        selected = self._table.selectedItems()
        if not selected:
            self._detail_view.clear()
            return

        row = selected[0].row()
        output = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if output:
            self._detail_view.setPlainText(json.dumps(output, indent=2, ensure_ascii=False))

    def clear(self) -> None:
        """Löscht alle LLM-Ausgaben."""
        self._outputs.clear()
        self._table.setRowCount(0)
        self._detail_view.clear()

    def get_outputs(self) -> list[dict]:
        """Gibt alle gespeicherten LLM-Ausgaben zurück."""
        return self._outputs
