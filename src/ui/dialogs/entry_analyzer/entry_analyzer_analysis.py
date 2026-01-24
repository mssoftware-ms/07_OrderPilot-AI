"""Entry Analyzer - Analysis & Validation Mixin.

This mixin handles visible chart analysis and entry signal validation:
- Analysis tab UI with indicator set display and entry table
- Validation tab UI with k-fold cross-validation
- Event handlers for analyze, draw, clear, validate actions
- Results display and table updates

Extracted from: entry_analyzer_popup.py (lines 918-933, 973-1011, 1207-1251, 1315-1370)
Date: 2026-01-21
LOC: ~208
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Import icon provider (Issue #12)
from src.ui.icons import get_icon

if TYPE_CHECKING:
    from PyQt6.QtCore import QThread

    from src.core.tradingbot.entry_events import EntryEvent

logger = logging.getLogger(__name__)


class AnalysisMixin:
    """Analysis and validation functionality.

    This mixin provides:
    - Analysis tab with indicator set display and entry signals table
    - Validation tab with k-fold cross-validation results
    - Event handlers for analyze/draw/clear/validate actions
    - Table updates for parameters and entries

    Attributes (defined in parent class):
        # Analysis Tab UI
        _set_name_label: QLabel
        _params_table: QTableWidget
        _score_label: QLabel
        _alternatives_label: QLabel
        _filter_checkbox: QCheckBox
        _filter_stats_label: QLabel
        _entries_table: QTableWidget

        # Validation Tab UI
        _validate_btn: QPushButton
        _val_progress: QProgressBar
        _val_status_label: QLabel
        _val_summary: QLabel
        _folds_table: QTableWidget

        # Workers
        _validation_worker: QThread | None

        # Data
        _result: AnalysisResult | None
        _validation_result: Any | None
        _candles: list[dict] | None
        _symbol: str | None
        _timeframe: str | None

        # Signals
        analyze_requested: pyqtSignal
        draw_entries_requested: pyqtSignal
        clear_entries_requested: pyqtSignal
    """

    # Type hints for attributes used from parent class
    _set_name_label: QLabel
    _params_table: QTableWidget
    _score_label: QLabel
    _alternatives_label: QLabel
    _filter_checkbox: QCheckBox
    _filter_stats_label: QLabel
    _entries_table: QTableWidget
    _validate_btn: QPushButton
    _val_progress: QProgressBar
    _val_status_label: QLabel
    _val_summary: QLabel
    _folds_table: QTableWidget
    _validation_worker: QThread | None
    _result: Any | None
    _validation_result: Any | None
    _candles: list[dict] | None
    _symbol: str | None
    _timeframe: str | None
    analyze_requested: pyqtSignal
    draw_entries_requested: pyqtSignal
    clear_entries_requested: pyqtSignal

    def _setup_analysis_tab(self, tab: QWidget) -> None:
        """Setup Analysis tab with indicator set and entry table.

        Original: entry_analyzer_popup.py:918-933

        Layout:
        - Top: Indicator Set info (optimized parameters, score)
        - Bottom: Entry table (time, side, price, confidence, reasons)
        """
        layout = QVBoxLayout(tab)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Indicator Set info
        indicator_group = self._create_indicator_group()
        splitter.addWidget(indicator_group)

        # Bottom: Entry table
        entries_group = self._create_entries_group()
        splitter.addWidget(entries_group)

        splitter.setSizes([200, 300])
        layout.addWidget(splitter)

    def _setup_validation_tab(self, tab: QWidget) -> None:
        """Setup Validation tab with k-fold cross-validation results.

        Original: entry_analyzer_popup.py:973-1011

        Features:
        - Validation action button (Run Validation)
        - Progress bar and status label
        - Validation summary (OOS score, win rate, train/test ratio)
        - Folds table (6 columns: Fold, Train Score, Test Score, Ratio, OOS WR, Overfit)
        """
        layout = QVBoxLayout(tab)

        # Validation action row (Issue #12: Material Design icon + theme color)
        action_row = QHBoxLayout()
        self._validate_btn = QPushButton(" Run Validation")
        self._validate_btn.setIcon(get_icon("check_circle"))
        self._validate_btn.setProperty("class", "success")  # Use theme success color
        self._validate_btn.clicked.connect(self._on_validate_clicked)
        action_row.addWidget(self._validate_btn)

        self._val_progress = QProgressBar()
        self._val_progress.setMaximumWidth(150)
        self._val_progress.setVisible(False)
        action_row.addWidget(self._val_progress)

        self._val_status_label = QLabel("Ready")
        self._val_status_label.setProperty("class", "status-label")  # Issue #12: Use theme
        action_row.addWidget(self._val_status_label)
        action_row.addStretch()
        layout.addLayout(action_row)

        # Validation summary
        self._val_summary = QLabel("No validation results yet")
        self._val_summary.setStyleSheet("font-size: 12pt; padding: 10px;")
        layout.addWidget(self._val_summary)

        # Folds table
        self._folds_table = QTableWidget()
        self._folds_table.setColumnCount(6)
        self._folds_table.setHorizontalHeaderLabels(
            ["Fold", "Train Score", "Test Score", "Ratio", "OOS WR", "Overfit"]
        )
        self._folds_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._folds_table)

    def _create_indicator_group(self) -> QGroupBox:
        """Create Indicator Set info group box.

        Original: entry_analyzer_popup.py:1012-1037

        Contains:
        - Set name label (Active Set)
        - Parameters table (3 columns: Family, Parameter, Value)
        - Score label
        - Alternatives label (hidden by default)
        """
        group = QGroupBox("Optimized Indicator Set")  # Issue #12: Removed emoji
        layout = QVBoxLayout(group)

        self._set_name_label = QLabel("Active Set: --")
        self._set_name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._set_name_label)

        self._params_table = QTableWidget()
        self._params_table.setColumnCount(3)
        self._params_table.setHorizontalHeaderLabels(["Family", "Parameter", "Value"])
        self._params_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._params_table.setMaximumHeight(150)
        layout.addWidget(self._params_table)

        self._score_label = QLabel("Score: --")
        layout.addWidget(self._score_label)

        self._alternatives_label = QLabel("Alternatives: --")
        self._alternatives_label.setStyleSheet("color: #888; font-size: 10pt;")
        self._alternatives_label.setVisible(False)
        layout.addWidget(self._alternatives_label)

        return group

    def _create_entries_group(self) -> QGroupBox:
        """Create Detected Entries group box.

        Original: entry_analyzer_popup.py:1039-1070

        Contains:
        - Filter checkbox (Apply Trade Filters)
        - Filter stats label
        - Entries table (5 columns: Time, Side, Price, Confidence, Reasons)
        """
        group = QGroupBox("Detected Entries")  # Issue #12: Removed emoji
        layout = QVBoxLayout(group)

        # Filter toggle
        filter_row = QHBoxLayout()
        self._filter_checkbox = QCheckBox("Apply Trade Filters (no-trade zones)")
        self._filter_checkbox.setChecked(False)
        self._filter_checkbox.setToolTip(
            "Filter out entries during volatility spikes, low volume, etc."
        )
        filter_row.addWidget(self._filter_checkbox)
        self._filter_stats_label = QLabel("")
        self._filter_stats_label.setStyleSheet("color: #888;")
        filter_row.addWidget(self._filter_stats_label)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self._entries_table = QTableWidget()
        self._entries_table.setColumnCount(5)
        self._entries_table.setHorizontalHeaderLabels(
            ["Time", "Side", "Price", "Confidence", "Reasons"]
        )
        self._entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._entries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._entries_table)

        return group

    def _update_params_table(self, params: dict) -> None:
        """Update parameters table with indicator parameters.

        Original: entry_analyzer_popup.py:1207-1224

        Args:
            params: Dictionary of indicator families with their parameters
                   Format: {family_name: {param_name: value}}
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
        """Update entries table with detected entry signals.

        Original: entry_analyzer_popup.py:1226-1240

        Args:
            entries: List of EntryEvent objects with timestamp, side, price, confidence, reason_tags
        """
        self._entries_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            time_str = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M")
            self._entries_table.setItem(row, 0, QTableWidgetItem(time_str))

            side_item = QTableWidgetItem(entry.side.value.upper())
            self._entries_table.setItem(row, 1, side_item)

            self._entries_table.setItem(row, 2, QTableWidgetItem(f"{entry.price:.2f}"))
            self._entries_table.setItem(row, 3, QTableWidgetItem(f"{entry.confidence:.0%}"))

            reasons_item = QTableWidgetItem(", ".join(entry.reason_tags))
            self._entries_table.setItem(row, 4, reasons_item)

    def _on_analyze_clicked(self) -> None:
        """Handle analyze button click.

        Original: entry_analyzer_popup.py:1242-1244

        Emits analyze_requested signal and sets analyzing state.
        """
        self.set_analyzing(True)
        self.analyze_requested.emit()

    def _on_draw_clicked(self) -> None:
        """Handle draw entries button click.

        Original: entry_analyzer_popup.py:1246-1248

        Emits draw_entries_requested signal with detected entries.
        """
        if self._result and self._result.entries:
            self.draw_entries_requested.emit(self._result.entries)

    def _on_clear_clicked(self) -> None:
        """Handle clear entries button click.

        Original: entry_analyzer_popup.py:1250-1251

        Emits clear_entries_requested signal to remove entry markers from chart.
        """
        self.clear_entries_requested.emit()

    def _on_validate_clicked(self) -> None:
        """Handle validate button click.

        Original: entry_analyzer_popup.py:1315-1332

        Starts k-fold cross-validation with ValidationWorker:
        - Checks for analysis result and candle data
        - Disables validate button
        - Shows progress bar
        - Creates ValidationWorker thread
        - Connects finished/error signals
        """
        if not self._result or not self._candles:
            QMessageBox.warning(
                self, "No Data", "Run analysis first and ensure candle data is available"
            )
            return

        self._validate_btn.setEnabled(False)
        self._val_progress.setVisible(True)
        self._val_progress.setRange(0, 0)
        self._val_status_label.setText("Running validation...")

        from src.ui.dialogs.entry_analyzer.entry_analyzer_workers import (
            ValidationWorker,
        )

        self._validation_worker = ValidationWorker(
            analysis=self._result,
            candles=self._candles,
            parent=self,
        )
        self._validation_worker.finished.connect(self._on_validation_finished)
        self._validation_worker.error.connect(self._on_validation_error)
        self._validation_worker.start()

    def _on_validation_finished(self, result: Any) -> None:
        """Handle validation completion.

        Original: entry_analyzer_popup.py:1334-1364

        Displays:
        - Validation status (PASSED/FAILED)
        - OOS score, win rate, train/test ratio
        - Total OOS trades
        - Failure reasons (if any)
        - Folds table with per-fold metrics
        """
        self._validation_result = result
        self._val_progress.setVisible(False)
        self._validate_btn.setEnabled(True)

        status = "✅ PASSED" if result.is_valid else "❌ FAILED"
        self._val_status_label.setText(status)

        summary = (
            f"**Status:** {status}\n"
            f"**OOS Score:** {result.avg_test_score:.3f}\n"
            f"**OOS Win Rate:** {result.oos_win_rate:.1%}\n"
            f"**Train/Test Ratio:** {result.avg_train_test_ratio:.2f}\n"
            f"**Total OOS Trades:** {result.total_oos_trades}"
        )
        if result.failure_reasons:
            summary += f"\n**Issues:** {', '.join(result.failure_reasons)}"
        self._val_summary.setText(summary)

        # Update folds table
        self._folds_table.setRowCount(len(result.folds))
        for row, fold in enumerate(result.folds):
            self._folds_table.setItem(row, 0, QTableWidgetItem(str(fold.fold_idx)))
            self._folds_table.setItem(row, 1, QTableWidgetItem(f"{fold.train_score:.3f}"))
            self._folds_table.setItem(row, 2, QTableWidgetItem(f"{fold.test_score:.3f}"))
            self._folds_table.setItem(row, 3, QTableWidgetItem(f"{fold.train_test_ratio:.2f}"))
            self._folds_table.setItem(row, 4, QTableWidgetItem(f"{fold.test_win_rate:.1%}"))
            overfit = "Yes" if fold.is_overfit else "No"
            self._folds_table.setItem(row, 5, QTableWidgetItem(overfit))

        logger.info("Validation complete: %s", "passed" if result.is_valid else "failed")

    def _on_validation_error(self, error_msg: str) -> None:
        """Handle validation error.

        Original: entry_analyzer_popup.py:1366-1370

        Displays error message and re-enables validate button.
        """
        self._val_progress.setVisible(False)
        self._validate_btn.setEnabled(True)
        self._val_status_label.setText("Error")
        self._val_summary.setText(f"❌ Validation Error: {error_msg}")
        logger.error("Validation error: %s", error_msg)

    # Public API methods (implemented in main class)
    def set_analyzing(self, analyzing: bool) -> None:
        """Set analyzing state.

        This method is implemented in the main class.
        """
        raise NotImplementedError("This method is implemented in the main class")
