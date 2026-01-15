"""Trading Journal - Trades Tab.

Refactored from trading_journal_widget.py monolith.

Module 2/5 of trading_journal_widget.py split.

Contains:
- TradesTab: Trade history with date filtering and file loading
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QSplitter,
    QHeaderView,
    QMessageBox,
)
from PyQt6.QtCore import Qt


class TradesTab(QWidget):
    """Tab für abgeschlossene Trades (aus logs/trades/*.json)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._trades_dir = Path("logs/trades")
        self._trades_dir.mkdir(parents=True, exist_ok=True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt die UI für die Trades-Tabelle."""
        layout = QVBoxLayout(self)

        # Filter nach Datum
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Datum:"))
        self._date_combo = QComboBox()
        self._date_combo.currentTextChanged.connect(self._on_date_changed)
        filter_layout.addWidget(self._date_combo)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._refresh_dates)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Splitter: Tabelle oben, Details unten
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Tabelle
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["Zeit", "Symbol", "Seite", "Entry", "Exit", "PnL", "PnL %", "Dauer"]
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

        # Initial laden
        self._refresh_dates()

    def _refresh_dates(self) -> None:
        """Lädt verfügbare Datumswerte (Unterordner in logs/trades/)."""
        self._date_combo.clear()
        self._date_combo.addItem("Alle")

        if not self._trades_dir.exists():
            return

        # Suche nach Ordnern im Format YYYY-MM-DD
        date_dirs = sorted(
            [d.name for d in self._trades_dir.iterdir() if d.is_dir()],
            reverse=True
        )
        for date_dir in date_dirs:
            self._date_combo.addItem(date_dir)

        # Lade Daten für das erste Datum
        if self._date_combo.count() > 1:
            self._date_combo.setCurrentIndex(1)

    def _on_date_changed(self, date_str: str) -> None:
        """Lädt Trades für das gewählte Datum."""
        self._table.setRowCount(0)
        self._detail_view.clear()

        if date_str == "Alle":
            self._load_all_trades()
        else:
            self._load_trades(date_str)

    def _load_all_trades(self) -> None:
        """Lädt alle Trades aus allen Unterordnern."""
        if not self._trades_dir.exists():
            return

        for day_dir in sorted(self._trades_dir.iterdir(), reverse=True):
            if not day_dir.is_dir():
                continue
            self._load_trades_from_dir(day_dir)

    def _load_trades(self, date_str: str) -> None:
        """Lädt Trades für ein bestimmtes Datum."""
        day_dir = self._trades_dir / date_str
        if not day_dir.exists():
            return
        self._load_trades_from_dir(day_dir)

    def _load_trades_from_dir(self, day_dir: Path) -> None:
        """Lädt alle trade_*.json Dateien aus einem Ordner."""
        for json_file in sorted(day_dir.glob("trade_*.json")):
            try:
                with open(json_file, encoding="utf-8") as f:
                    trade = json.load(f)
                self._add_trade_row(trade)
            except Exception as e:
                print(f"Fehler beim Laden von {json_file}: {e}")

    def _add_trade_row(self, trade: dict) -> None:
        """Fügt einen Trade zur Tabelle hinzu."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Zeit
        timestamp = trade.get("exit_time", trade.get("entry_time", ""))
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = timestamp
        else:
            time_str = ""

        # Dauer
        duration_str = ""
        if trade.get("entry_time") and trade.get("exit_time"):
            try:
                entry_dt = datetime.fromisoformat(trade["entry_time"].replace("Z", "+00:00"))
                exit_dt = datetime.fromisoformat(trade["exit_time"].replace("Z", "+00:00"))
                duration = exit_dt - entry_dt
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                duration_str = f"{hours}h {minutes}m"
            except Exception:
                pass

        self._table.setItem(row, 0, QTableWidgetItem(time_str))
        self._table.setItem(row, 1, QTableWidgetItem(trade.get("symbol", "")))
        self._table.setItem(row, 2, QTableWidgetItem(trade.get("side", "")))
        self._table.setItem(row, 3, QTableWidgetItem(str(trade.get("entry_price", ""))))
        self._table.setItem(row, 4, QTableWidgetItem(str(trade.get("exit_price", ""))))
        self._table.setItem(row, 5, QTableWidgetItem(str(trade.get("pnl", ""))))
        self._table.setItem(row, 6, QTableWidgetItem(str(trade.get("pnl_percent", ""))))
        self._table.setItem(row, 7, QTableWidgetItem(duration_str))

        # Speichere den kompletten Trade als UserRole
        self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, trade)

    def _on_selection_changed(self) -> None:
        """Zeigt Details zum ausgewählten Trade."""
        selected = self._table.selectedItems()
        if not selected:
            self._detail_view.clear()
            return

        row = selected[0].row()
        trade = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if trade:
            self._detail_view.setPlainText(json.dumps(trade, indent=2, ensure_ascii=False))
