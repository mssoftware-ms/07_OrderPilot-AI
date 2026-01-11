"""Entry Analyzer Popup Dialog.

Displays analysis results for the visible chart range,
including optimized indicator sets and entry signals.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult, EntryEvent

logger = logging.getLogger(__name__)


class EntryAnalyzerPopup(QDialog):
    """Popup dialog for Entry Analyzer results.

    Displays:
    - Current regime detection
    - Optimized indicator set with parameters
    - List of detected entries (LONG green / SHORT red)
    - Signal statistics
    """

    # Signal when user requests analysis
    analyze_requested = pyqtSignal()
    # Signal when user wants to draw entries on chart
    draw_entries_requested = pyqtSignal(list)  # List[EntryEvent]
    # Signal when user wants to clear entries
    clear_entries_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the Entry Analyzer popup.

        Args:
            parent: Parent widget (usually the chart widget).
        """
        super().__init__(parent)
        self.setWindowTitle("🎯 Entry Analyzer - Visible Chart")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)

        self._result: AnalysisResult | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI components."""
        layout = QVBoxLayout(self)

        # Header with status
        header = self._create_header()
        layout.addWidget(header)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Indicator Set info
        indicator_group = self._create_indicator_group()
        splitter.addWidget(indicator_group)

        # Bottom: Entry table
        entries_group = self._create_entries_group()
        splitter.addWidget(entries_group)

        splitter.setSizes([200, 300])
        layout.addWidget(splitter, stretch=1)

        # Footer with actions
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create the header section with regime and stats."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 10)

        # Regime indicator
        self._regime_label = QLabel("Regime: --")
        self._regime_label.setStyleSheet(
            "font-weight: bold; font-size: 14pt; padding: 5px;"
        )
        layout.addWidget(self._regime_label)

        layout.addStretch()

        # Signal count
        self._signal_count_label = QLabel("Signals: 0 LONG / 0 SHORT")
        self._signal_count_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(self._signal_count_label)

        # Signal rate
        self._signal_rate_label = QLabel("Rate: 0/h")
        self._signal_rate_label.setStyleSheet("font-size: 11pt; color: #888;")
        layout.addWidget(self._signal_rate_label)

        return widget

    def _create_indicator_group(self) -> QGroupBox:
        """Create the indicator set display group."""
        group = QGroupBox("📊 Optimized Indicator Set")

        layout = QVBoxLayout(group)

        # Active set info
        self._set_name_label = QLabel("Active Set: --")
        self._set_name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._set_name_label)

        # Parameters table
        self._params_table = QTableWidget()
        self._params_table.setColumnCount(3)
        self._params_table.setHorizontalHeaderLabels(["Family", "Parameter", "Value"])
        self._params_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._params_table.setMaximumHeight(150)
        layout.addWidget(self._params_table)

        # Score info
        self._score_label = QLabel("Score: --")
        layout.addWidget(self._score_label)

        # Alternatives info (Phase 2)
        self._alternatives_label = QLabel("Alternatives: --")
        self._alternatives_label.setStyleSheet("color: #888; font-size: 10pt;")
        self._alternatives_label.setVisible(False)
        layout.addWidget(self._alternatives_label)

        return group

    def _create_entries_group(self) -> QGroupBox:
        """Create the entries list group."""
        group = QGroupBox("🎯 Detected Entries")

        layout = QVBoxLayout(group)

        # Entries table
        self._entries_table = QTableWidget()
        self._entries_table.setColumnCount(5)
        self._entries_table.setHorizontalHeaderLabels(
            ["Time", "Side", "Price", "Confidence", "Reasons"]
        )
        self._entries_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._entries_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self._entries_table)

        return group

    def _create_footer(self) -> QWidget:
        """Create the footer with action buttons."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        # Analyze button
        self._analyze_btn = QPushButton("🔄 Analyze Visible Range")
        self._analyze_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #3b82f6; color: white;"
        )
        self._analyze_btn.clicked.connect(self._on_analyze_clicked)
        layout.addWidget(self._analyze_btn)

        # Progress bar (hidden by default)
        self._progress = QProgressBar()
        self._progress.setMaximumWidth(150)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        layout.addStretch()

        # Draw entries button
        self._draw_btn = QPushButton("📍 Draw on Chart")
        self._draw_btn.setEnabled(False)
        self._draw_btn.clicked.connect(self._on_draw_clicked)
        layout.addWidget(self._draw_btn)

        # Clear button
        self._clear_btn = QPushButton("🗑️ Clear Entries")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self._clear_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return widget

    def set_analyzing(self, analyzing: bool) -> None:
        """Update UI to show analysis in progress.

        Args:
            analyzing: True if analysis is running.
        """
        self._analyze_btn.setEnabled(not analyzing)
        self._progress.setVisible(analyzing)
        if analyzing:
            self._progress.setRange(0, 0)  # Indeterminate
        else:
            self._progress.setRange(0, 100)

    def set_result(self, result: AnalysisResult) -> None:
        """Update the popup with analysis results.

        Args:
            result: The analysis result to display.
        """
        self._result = result

        # Update regime
        regime_colors = {
            "trend_up": "#22c55e",
            "trend_down": "#ef4444",
            "range": "#f59e0b",
            "high_vol": "#a855f7",
            "squeeze": "#3b82f6",
            "no_trade": "#6b7280",
        }
        regime_text = result.regime.value.replace("_", " ").title()
        color = regime_colors.get(result.regime.value, "#888")
        self._regime_label.setText(f"Regime: {regime_text}")
        self._regime_label.setStyleSheet(
            f"font-weight: bold; font-size: 14pt; padding: 5px; color: {color};"
        )

        # Update signal counts
        self._signal_count_label.setText(
            f"Signals: {result.long_count} LONG / {result.short_count} SHORT"
        )
        self._signal_rate_label.setText(f"Rate: {result.signal_rate_per_hour:.1f}/h")

        # Update indicator set
        if result.active_set:
            self._set_name_label.setText(f"Active Set: {result.active_set.name}")
            self._score_label.setText(f"Score: {result.active_set.score:.3f}")
            self._update_params_table(result.active_set.parameters)

            # Show alternatives if available
            if result.alternative_sets:
                alt_names = [s.name for s in result.alternative_sets[:2]]
                self._alternatives_label.setText(f"Alternatives: {', '.join(alt_names)}")
                self._alternatives_label.setVisible(True)
            else:
                self._alternatives_label.setVisible(False)
        else:
            self._set_name_label.setText("Active Set: Default (no optimization)")
            self._score_label.setText("Score: --")
            self._params_table.setRowCount(0)
            self._alternatives_label.setVisible(False)

        # Update entries table
        self._update_entries_table(result.entries)

        # Enable draw button if we have entries
        self._draw_btn.setEnabled(len(result.entries) > 0)

        logger.info(
            "Analysis result displayed: %d entries, regime=%s",
            len(result.entries),
            result.regime.value,
        )

    def _update_params_table(self, params: dict) -> None:
        """Update the parameters table.

        Args:
            params: Dict of family -> {param: value}.
        """
        self._params_table.setRowCount(0)
        row = 0

        for family, family_params in params.items():
            if isinstance(family_params, dict):
                for param, value in family_params.items():
                    self._params_table.insertRow(row)
                    self._params_table.setItem(row, 0, QTableWidgetItem(family))
                    self._params_table.setItem(row, 1, QTableWidgetItem(param))
                    self._params_table.setItem(row, 2, QTableWidgetItem(str(value)))
                    row += 1
            else:
                self._params_table.insertRow(row)
                self._params_table.setItem(row, 0, QTableWidgetItem(family))
                self._params_table.setItem(row, 1, QTableWidgetItem("value"))
                self._params_table.setItem(row, 2, QTableWidgetItem(str(family_params)))
                row += 1

    def _update_entries_table(self, entries: list[EntryEvent]) -> None:
        """Update the entries table.

        Args:
            entries: List of entry events to display.
        """
        from datetime import datetime

        self._entries_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            # Time
            time_str = datetime.fromtimestamp(entry.timestamp).strftime(
                "%Y-%m-%d %H:%M"
            )
            time_item = QTableWidgetItem(time_str)
            self._entries_table.setItem(row, 0, time_item)

            # Side with color
            side_item = QTableWidgetItem(entry.side.value.upper())
            side_color = "#22c55e" if entry.side.value == "long" else "#ef4444"
            side_item.setForeground(
                self._entries_table.palette().text().color()
            )  # Will be overridden
            side_item.setData(Qt.ItemDataRole.ForegroundRole, side_color)
            self._entries_table.setItem(row, 1, side_item)

            # Price
            price_item = QTableWidgetItem(f"{entry.price:.2f}")
            self._entries_table.setItem(row, 2, price_item)

            # Confidence
            conf_item = QTableWidgetItem(f"{entry.confidence:.0%}")
            self._entries_table.setItem(row, 3, conf_item)

            # Reasons
            reasons_item = QTableWidgetItem(", ".join(entry.reason_tags))
            self._entries_table.setItem(row, 4, reasons_item)

    def _on_analyze_clicked(self) -> None:
        """Handle analyze button click."""
        self.set_analyzing(True)
        self.analyze_requested.emit()

    def _on_draw_clicked(self) -> None:
        """Handle draw on chart button click."""
        if self._result and self._result.entries:
            self.draw_entries_requested.emit(self._result.entries)

    def _on_clear_clicked(self) -> None:
        """Handle clear entries button click."""
        self.clear_entries_requested.emit()
