"""
Trading Journal Widget - Logging/Journal UI für den Trading Bot.

Phase 5.4 - Zeigt:
- Signal History (alle generierten Signale)
- Trade History (Trades mit Details)
- LLM Validation Outputs (JSON)
- Errors (Bot-Fehler)
- Export Funktionen
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QPushButton,
    QLabel,
    QGroupBox,
    QHeaderView,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QFrame,
)
from PyQt6.QtGui import QColor

if TYPE_CHECKING:
    from src.core.trading_bot import TradeLogEntry

logger = logging.getLogger(__name__)


class SignalsTab(QWidget):
    """Tab für Signal-Historie."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._signals: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Signal Historie</b>"))
        header_layout.addStretch()

        self._count_label = QLabel("0 Signale")
        self._count_label.setStyleSheet("color: #888;")
        header_layout.addWidget(self._count_label)

        clear_btn = QPushButton("Löschen")
        clear_btn.clicked.connect(self._clear_signals)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Zeit", "Symbol", "Richtung", "Score", "Quality", "Gate", "Trigger"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
            }
            QTableWidget::item:selected {
                background-color: #2d5a88;
            }
        """)
        layout.addWidget(self._table)

    def add_signal(self, signal_data: dict) -> None:
        """Fügt ein Signal zur Historie hinzu."""
        self._signals.append(signal_data)

        row = self._table.rowCount()
        self._table.insertRow(row)

        # Zeit
        time_str = signal_data.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        self._table.setItem(row, 0, QTableWidgetItem(time_str))

        # Symbol
        self._table.setItem(row, 1, QTableWidgetItem(signal_data.get("symbol", "-")))

        # Richtung
        direction = signal_data.get("direction", "NEUTRAL")
        dir_item = QTableWidgetItem(direction)
        if direction == "LONG":
            dir_item.setForeground(QColor("#4CAF50"))
        elif direction == "SHORT":
            dir_item.setForeground(QColor("#f44336"))
        self._table.setItem(row, 2, dir_item)

        # Score
        score = signal_data.get("score", 0)
        self._table.setItem(row, 3, QTableWidgetItem(f"{score:.2f}"))

        # Quality
        quality = signal_data.get("quality", "-")
        quality_item = QTableWidgetItem(quality)
        quality_colors = {
            "EXCELLENT": "#4CAF50",
            "GOOD": "#8BC34A",
            "MODERATE": "#FFC107",
            "WEAK": "#FF9800",
        }
        quality_item.setForeground(QColor(quality_colors.get(quality, "#888")))
        self._table.setItem(row, 4, quality_item)

        # Gate
        gate = signal_data.get("gate_status", "-")
        gate_item = QTableWidgetItem(gate)
        if gate == "BLOCKED":
            gate_item.setForeground(QColor("#f44336"))
        elif gate == "BOOSTED":
            gate_item.setForeground(QColor("#2196F3"))
        self._table.setItem(row, 5, gate_item)

        # Trigger
        self._table.setItem(row, 6, QTableWidgetItem(signal_data.get("trigger", "-")))

        # Auto-scroll
        self._table.scrollToBottom()
        self._count_label.setText(f"{len(self._signals)} Signale")

    def _clear_signals(self) -> None:
        """Löscht alle Signale."""
        self._signals.clear()
        self._table.setRowCount(0)
        self._count_label.setText("0 Signale")

    def get_signals(self) -> list[dict]:
        """Gibt alle Signale zurück."""
        return self._signals.copy()


class TradesTab(QWidget):
    """Tab für Trade-Historie."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._trades_dir = Path("logs/trades")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Trade Historie</b>"))
        header_layout.addStretch()

        self._date_combo = QComboBox()
        self._date_combo.setMinimumWidth(120)
        self._date_combo.currentTextChanged.connect(self._load_trades)
        header_layout.addWidget(QLabel("Datum:"))
        header_layout.addWidget(self._date_combo)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Aktualisieren")
        refresh_btn.clicked.connect(self._refresh_dates)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Splitter für Tabelle und Details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Trade ID", "Symbol", "Richtung", "Entry", "Exit", "PnL", "Outcome", "Dauer"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
            }
        """)
        splitter.addWidget(self._table)

        # Details
        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #aaa;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        self._details_text.setPlaceholderText("Wähle einen Trade für Details...")
        splitter.addWidget(self._details_text)

        splitter.setSizes([300, 200])
        layout.addWidget(splitter)

        # Initial load
        self._refresh_dates()

    def _refresh_dates(self) -> None:
        """Lädt verfügbare Datums-Ordner."""
        self._date_combo.clear()

        if not self._trades_dir.exists():
            self._date_combo.addItem("Keine Trades")
            return

        dates = []
        for d in self._trades_dir.iterdir():
            if d.is_dir():
                try:
                    datetime.strptime(d.name, "%Y-%m-%d")
                    dates.append(d.name)
                except ValueError:
                    continue

        if dates:
            dates.sort(reverse=True)
            self._date_combo.addItems(dates)
        else:
            self._date_combo.addItem("Keine Trades")

    def _load_trades(self, date_str: str) -> None:
        """Lädt Trades für ein Datum."""
        self._table.setRowCount(0)
        self._details_text.clear()

        if date_str == "Keine Trades" or not date_str:
            return

        day_dir = self._trades_dir / date_str
        if not day_dir.exists():
            return

        for json_file in sorted(day_dir.glob("trade_*.json")):
            try:
                with open(json_file, encoding="utf-8") as f:
                    trade = json.load(f)
                self._add_trade_row(trade)
            except Exception as e:
                logger.warning(f"Failed to load trade {json_file}: {e}")

    def _add_trade_row(self, trade: dict) -> None:
        """Fügt eine Trade-Zeile hinzu."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Trade ID
        self._table.setItem(row, 0, QTableWidgetItem(trade.get("trade_id", "-")))

        # Symbol
        self._table.setItem(row, 1, QTableWidgetItem(trade.get("symbol", "-")))

        # Richtung
        side = trade.get("entry_side", "-")
        side_item = QTableWidgetItem(side)
        if side == "BUY":
            side_item.setForeground(QColor("#4CAF50"))
        elif side == "SELL":
            side_item.setForeground(QColor("#f44336"))
        self._table.setItem(row, 2, side_item)

        # Entry
        entry = trade.get("entry_price", "-")
        self._table.setItem(row, 3, QTableWidgetItem(f"${entry}" if entry != "-" else "-"))

        # Exit
        exit_p = trade.get("exit_price", "-")
        self._table.setItem(row, 4, QTableWidgetItem(f"${exit_p}" if exit_p != "-" else "-"))

        # PnL
        pnl = trade.get("net_pnl", 0)
        pnl_pct = trade.get("realized_pnl_percent", 0)
        pnl_item = QTableWidgetItem(f"${pnl} ({pnl_pct}%)")
        if pnl and float(pnl) > 0:
            pnl_item.setForeground(QColor("#4CAF50"))
        elif pnl and float(pnl) < 0:
            pnl_item.setForeground(QColor("#f44336"))
        self._table.setItem(row, 5, pnl_item)

        # Outcome
        outcome = trade.get("outcome", "-")
        outcome_item = QTableWidgetItem(outcome)
        if outcome == "WIN":
            outcome_item.setForeground(QColor("#4CAF50"))
        elif outcome == "LOSS":
            outcome_item.setForeground(QColor("#f44336"))
        self._table.setItem(row, 6, outcome_item)

        # Dauer
        self._table.setItem(row, 7, QTableWidgetItem(trade.get("duration_formatted", "-")))

        # Store trade data
        self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, trade)

    def _on_selection_changed(self) -> None:
        """Zeigt Details des ausgewählten Trades."""
        items = self._table.selectedItems()
        if not items:
            return

        trade = items[0].data(Qt.ItemDataRole.UserRole)
        if trade:
            self._details_text.setText(json.dumps(trade, indent=2, ensure_ascii=False))


class LLMOutputsTab(QWidget):
    """Tab für LLM Validation Outputs."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._outputs: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>LLM Validation Outputs</b>"))
        header_layout.addStretch()

        self._count_label = QLabel("0 Outputs")
        self._count_label.setStyleSheet("color: #888;")
        header_layout.addWidget(self._count_label)

        clear_btn = QPushButton("Löschen")
        clear_btn.clicked.connect(self._clear_outputs)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # List
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Zeit", "Symbol", "Action", "Confidence", "Tier"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
            }
        """)
        splitter.addWidget(self._table)

        # JSON Output
        self._json_text = QTextEdit()
        self._json_text.setReadOnly(True)
        self._json_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #00ff00;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        self._json_text.setPlaceholderText("Wähle einen Output für JSON Details...")
        splitter.addWidget(self._json_text)

        splitter.setSizes([200, 300])
        layout.addWidget(splitter)

    def add_output(self, llm_result: dict) -> None:
        """Fügt einen LLM Output hinzu."""
        self._outputs.append(llm_result)

        row = self._table.rowCount()
        self._table.insertRow(row)

        # Zeit
        time_str = llm_result.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        self._table.setItem(row, 0, QTableWidgetItem(time_str))

        # Symbol
        self._table.setItem(row, 1, QTableWidgetItem(llm_result.get("symbol", "-")))

        # Action
        action = llm_result.get("action", "-")
        action_item = QTableWidgetItem(action.upper() if action else "-")
        action_colors = {
            "approve": "#4CAF50",
            "boost": "#2196F3",
            "veto": "#f44336",
            "caution": "#FF9800",
        }
        action_item.setForeground(QColor(action_colors.get(action, "#888")))
        self._table.setItem(row, 2, action_item)

        # Confidence
        conf = llm_result.get("confidence", 0)
        self._table.setItem(row, 3, QTableWidgetItem(f"{conf}%"))

        # Tier
        self._table.setItem(row, 4, QTableWidgetItem(llm_result.get("tier", "-")))

        # Store data
        self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, llm_result)

        self._table.scrollToBottom()
        self._count_label.setText(f"{len(self._outputs)} Outputs")

    def _on_selection_changed(self) -> None:
        """Zeigt JSON des ausgewählten Outputs."""
        items = self._table.selectedItems()
        if not items:
            return

        data = items[0].data(Qt.ItemDataRole.UserRole)
        if data:
            self._json_text.setText(json.dumps(data, indent=2, ensure_ascii=False))

    def _clear_outputs(self) -> None:
        """Löscht alle Outputs."""
        self._outputs.clear()
        self._table.setRowCount(0)
        self._json_text.clear()
        self._count_label.setText("0 Outputs")

    def get_outputs(self) -> list[dict]:
        """Gibt alle Outputs zurück."""
        return self._outputs.copy()


class ErrorsTab(QWidget):
    """Tab für Bot-Fehler."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._errors: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Bot Errors</b>"))
        header_layout.addStretch()

        self._count_label = QLabel("0 Fehler")
        self._count_label.setStyleSheet("color: #888;")
        header_layout.addWidget(self._count_label)

        clear_btn = QPushButton("Löschen")
        clear_btn.clicked.connect(self._clear_errors)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Error Log
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a0000;
                color: #ff6b6b;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        self._log_text.setPlaceholderText("Keine Fehler aufgetreten...")
        layout.addWidget(self._log_text)

    def add_error(self, error_data: dict) -> None:
        """Fügt einen Fehler hinzu."""
        self._errors.append(error_data)

        timestamp = error_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        error_type = error_data.get("type", "ERROR")
        message = error_data.get("message", "Unknown error")
        context = error_data.get("context", "")

        entry = f"[{timestamp}] {error_type}: {message}"
        if context:
            entry += f"\n  Context: {context}"
        entry += "\n" + "-" * 60 + "\n"

        self._log_text.append(entry)
        self._count_label.setText(f"{len(self._errors)} Fehler")

    def _clear_errors(self) -> None:
        """Löscht alle Fehler."""
        self._errors.clear()
        self._log_text.clear()
        self._count_label.setText("0 Fehler")

    def get_errors(self) -> list[dict]:
        """Gibt alle Fehler zurück."""
        return self._errors.copy()


class TradingJournalWidget(QWidget):
    """
    Trading Journal Widget - Umfassende Logging/Journal UI.

    Zeigt:
    - Signal History
    - Trade History
    - LLM Outputs
    - Errors
    - Export Funktionen
    """

    export_requested = pyqtSignal(str, str)  # format, path

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)

        header_layout.addWidget(QLabel("<b>📔 Trading Journal</b>"))
        header_layout.addStretch()

        # Export Buttons
        export_json_btn = QPushButton("📤 JSON Export")
        export_json_btn.clicked.connect(lambda: self._export("json"))
        header_layout.addWidget(export_json_btn)

        export_csv_btn = QPushButton("📊 CSV Export")
        export_csv_btn.clicked.connect(lambda: self._export("csv"))
        header_layout.addWidget(export_csv_btn)

        layout.addWidget(header_frame)

        # Tabs
        self._tabs = QTabWidget()

        # Create tabs
        self._signals_tab = SignalsTab()
        self._tabs.addTab(self._signals_tab, "📊 Signale")

        self._trades_tab = TradesTab()
        self._tabs.addTab(self._trades_tab, "💰 Trades")

        self._llm_tab = LLMOutputsTab()
        self._tabs.addTab(self._llm_tab, "🤖 LLM Outputs")

        self._errors_tab = ErrorsTab()
        self._tabs.addTab(self._errors_tab, "❌ Errors")

        layout.addWidget(self._tabs)

    def add_signal(self, signal_data: dict) -> None:
        """Fügt ein Signal zum Journal hinzu."""
        self._signals_tab.add_signal(signal_data)

    def add_llm_output(self, llm_result: dict) -> None:
        """Fügt einen LLM Output hinzu."""
        self._llm_tab.add_output(llm_result)

    def add_error(self, error_data: dict) -> None:
        """Fügt einen Fehler hinzu."""
        self._errors_tab.add_error(error_data)

    def refresh_trades(self) -> None:
        """Aktualisiert die Trade-Liste."""
        self._trades_tab._refresh_dates()

    def _export(self, format_type: str) -> None:
        """Exportiert Journal-Daten."""
        # File dialog
        if format_type == "json":
            file_filter = "JSON Files (*.json)"
            default_name = f"trading_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            file_filter = "CSV Files (*.csv)"
            default_name = f"trading_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Trading Journal", default_name, file_filter
        )

        if not file_path:
            return

        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "signals": self._signals_tab.get_signals(),
                "llm_outputs": self._llm_tab.get_outputs(),
                "errors": self._errors_tab.get_errors(),
            }

            if format_type == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                # CSV export - signals only for now
                import csv
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    if data["signals"]:
                        writer = csv.DictWriter(f, fieldnames=data["signals"][0].keys())
                        writer.writeheader()
                        writer.writerows(data["signals"])

            self.export_requested.emit(format_type, file_path)
            QMessageBox.information(
                self, "Export erfolgreich",
                f"Journal exportiert nach:\n{file_path}"
            )
            logger.info(f"Trading journal exported to {file_path}")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self, "Export Fehler",
                f"Export fehlgeschlagen:\n{e}"
            )
