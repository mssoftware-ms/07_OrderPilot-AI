"""Entry Analyzer - Indicator Optimization V2 Mixin (Stage 2).

Handles Indicator Optimization Execution for Stage 2:
- Per-regime optimization (uses only regime-specific bars)
- Per-signal-type optimization (entry_long, entry_short, exit_long, exit_short)
- Progress tracking with 4 separate progress bars
- Live results table with real-time updates
- Worker thread management (IndicatorOptimizationWorkerV2)

Date: 2026-01-24
Stage: 2 (Indicator Optimization)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon

if TYPE_CHECKING:
    from PyQt6.QtCore import QThread

logger = logging.getLogger(__name__)


class IndicatorOptimizationV2Mixin:
    """Stage 2: Indicator Optimization Execution for regime-specific signals.

    Provides:
    - Start/Stop optimization per regime
    - 4 separate progress bars (one per signal type)
    - Live results table with real-time updates
    - IndicatorOptimizationWorkerV2 thread management
    - Result filtering and sorting

    Attributes (defined in parent):
        _ind_v2_start_btn: QPushButton - Start optimization button
        _ind_v2_stop_btn: QPushButton - Stop optimization button
        _ind_v2_signal_progress: dict[str, QProgressBar] - Progress per signal type
        _ind_v2_live_results_table: QTableWidget - Live results display
        _ind_v2_worker: QThread - Optimization worker thread
        _ind_v2_optimization_results: dict - Results per signal type
    """

    # Type hints for parent attributes
    _ind_v2_regime_combo: QComboBox
    _ind_v2_signal_types: dict[str, QCheckBox]
    _ind_v2_indicator_checkboxes: dict[str, QCheckBox]
    _ind_v2_param_widgets: dict
    _regime_bar_indices: dict[str, list[int]]
    _ind_v2_start_btn: QPushButton
    _ind_v2_stop_btn: QPushButton
    _ind_v2_signal_progress: dict[str, QProgressBar]
    _ind_v2_live_results_table: QTableWidget
    _ind_v2_worker: QThread | None
    _ind_v2_optimization_results: dict
    _candles: list[dict]
    _symbol: str
    _timeframe: str

    def _setup_indicator_optimization_v2_tab(self, tab: QWidget) -> None:
        """Setup Indicator Optimization V2 tab (Stage 2).

        Creates:
        - Start/Stop buttons
        - 4 progress bars (one per signal type)
        - Live results table
        - Status labels
        """
        layout = QVBoxLayout(tab)

        # ===== Control Buttons =====
        control_layout = QHBoxLayout()

        self._ind_v2_start_btn = QPushButton(" Start Optimization")
        self._ind_v2_start_btn.setIcon(get_icon("play_arrow"))
        self._ind_v2_start_btn.setProperty("class", "success")
        self._ind_v2_start_btn.clicked.connect(self._on_start_indicator_v2_optimization)
        control_layout.addWidget(self._ind_v2_start_btn)

        self._ind_v2_stop_btn = QPushButton(" Stop")
        self._ind_v2_stop_btn.setIcon(get_icon("stop"))
        self._ind_v2_stop_btn.setProperty("class", "danger")
        self._ind_v2_stop_btn.setEnabled(False)
        self._ind_v2_stop_btn.clicked.connect(self._on_stop_indicator_v2_optimization)
        control_layout.addWidget(self._ind_v2_stop_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # ===== Progress Group =====
        progress_group = QGroupBox("Optimization Progress (Per Signal Type)")
        progress_layout = QFormLayout(progress_group)

        self._ind_v2_signal_progress = {}
        signal_labels = {
            "entry_long": "Entry Long:",
            "entry_short": "Entry Short:",
            "exit_long": "Exit Long:",
            "exit_short": "Exit Short:",
        }

        for signal_type, label in signal_labels.items():
            progress_bar = QProgressBar()
            progress_bar.setFormat("%p% (%v/%m)")
            progress_bar.setTextVisible(True)
            self._ind_v2_signal_progress[signal_type] = progress_bar
            progress_layout.addRow(label, progress_bar)

        layout.addWidget(progress_group)

        # ===== Live Results Table =====
        results_label = QLabel("<b>Live Results (Auto-Updated)</b>")
        layout.addWidget(results_label)

        self._ind_v2_live_results_table = QTableWidget()
        self._ind_v2_live_results_table.setColumnCount(8)
        self._ind_v2_live_results_table.setHorizontalHeaderLabels(
            [
                "Signal Type",
                "Indicator",
                "Score",
                "Win Rate",
                "Profit Factor",
                "Sharpe",
                "Trades",
                "Parameters",
            ]
        )

        # Table configuration
        header = self._ind_v2_live_results_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self._ind_v2_live_results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._ind_v2_live_results_table.setAlternatingRowColors(True)
        self._ind_v2_live_results_table.setSortingEnabled(True)

        layout.addWidget(self._ind_v2_live_results_table)

        # Initialize state
        self._ind_v2_worker = None
        self._ind_v2_optimization_results = {}

    def _on_start_indicator_v2_optimization(self) -> None:
        """Handle start optimization button click.

        Validates:
        - Regime selected and has bar indices
        - At least one signal type enabled
        - At least one indicator selected
        - Chart data available

        Starts:
        - IndicatorOptimizationWorkerV2 thread
        """
        # Get selected regime
        regime = self._ind_v2_regime_combo.currentText()

        # Validate regime has bar indices
        if regime not in self._regime_bar_indices:
            QMessageBox.warning(
                self,
                "No Regime Data",
                f"No bar indices loaded for {regime} regime.\n\n"
                "Please load optimized_regime_*.json from Stage 1 first.",
            )
            return

        bar_indices = self._regime_bar_indices[regime]
        if not bar_indices:
            QMessageBox.warning(
                self,
                "Empty Regime",
                f"{regime} regime has no bars.\n\n" "Cannot optimize with empty dataset.",
            )
            return

        # Get enabled signal types
        enabled_signal_types = [
            signal_type
            for signal_type, checkbox in self._ind_v2_signal_types.items()
            if checkbox.isChecked()
        ]

        if not enabled_signal_types:
            QMessageBox.warning(
                self,
                "No Signal Types",
                "Please select at least one signal type to optimize.",
            )
            return

        # Get selected indicators
        selected_indicators = [
            ind_id for ind_id, cb in self._ind_v2_indicator_checkboxes.items() if cb.isChecked()
        ]

        if not selected_indicators:
            QMessageBox.warning(
                self,
                "No Indicators",
                "Please select at least one indicator to optimize.",
            )
            return

        # Get parameter ranges
        param_ranges = {}
        for indicator_id, params in self._ind_v2_param_widgets.items():
            param_ranges[indicator_id] = {}
            for param_name, widgets in params.items():
                param_ranges[indicator_id][param_name] = {
                    "min": widgets["min"].value(),
                    "max": widgets["max"].value(),
                    "step": widgets["step"].value(),
                }

        # Validate chart data
        if not self._candles:
            QMessageBox.warning(
                self,
                "No Chart Data",
                "No chart data available.\n\n" "Please load chart data before optimization.",
            )
            return

        # Create worker configuration
        config = {
            "regime": regime,
            "bar_indices": bar_indices,
            "signal_types": enabled_signal_types,
            "indicators": selected_indicators,
            "param_ranges": param_ranges,
            "symbol": self._symbol,
            "timeframe": self._timeframe,
            "candles": self._candles,
        }

        # Create and start worker thread
        from src.ui.dialogs.entry_analyzer.entry_analyzer_indicator_worker import (
            IndicatorOptimizationWorkerV2,
        )

        self._ind_v2_worker = IndicatorOptimizationWorkerV2(config, parent=self)

        # Connect signals
        self._ind_v2_worker.progress.connect(self._on_indicator_v2_progress)
        self._ind_v2_worker.result_ready.connect(self._on_indicator_v2_result)
        self._ind_v2_worker.finished.connect(self._on_indicator_v2_finished)
        self._ind_v2_worker.error.connect(self._on_indicator_v2_error)

        # Reset progress bars
        for signal_type, progress_bar in self._ind_v2_signal_progress.items():
            if signal_type in enabled_signal_types:
                progress_bar.setMaximum(100)
                progress_bar.setValue(0)
            else:
                progress_bar.setMaximum(100)
                progress_bar.setValue(0)
                progress_bar.setEnabled(False)

        # Clear results table
        self._ind_v2_live_results_table.setRowCount(0)
        self._ind_v2_optimization_results = {}

        # Update UI state
        self._ind_v2_start_btn.setEnabled(False)
        self._ind_v2_stop_btn.setEnabled(True)

        # Start worker
        self._ind_v2_worker.start()
        logger.info(
            f"Started Stage 2 optimization for {regime} regime with "
            f"{len(enabled_signal_types)} signal types and "
            f"{len(selected_indicators)} indicators"
        )

    def _on_stop_indicator_v2_optimization(self) -> None:
        """Handle stop optimization button click.

        Requests worker thread to stop gracefully.
        """
        if self._ind_v2_worker and self._ind_v2_worker.isRunning():
            self._ind_v2_worker.stop()
            logger.info("Requested Stage 2 optimization stop")

    def _on_indicator_v2_progress(
        self, signal_type: str, current: int, total: int, best_score: float
    ) -> None:
        """Handle optimization progress update.

        Args:
            signal_type: Signal type being optimized
            current: Current trial number
            total: Total trials
            best_score: Best score found so far
        """
        if signal_type in self._ind_v2_signal_progress:
            progress_bar = self._ind_v2_signal_progress[signal_type]
            progress_bar.setMaximum(total)
            progress_bar.setValue(current)
            progress_bar.setFormat(f"%p% - Best: {best_score:.1f}")

    def _on_indicator_v2_result(self, signal_type: str, result: dict) -> None:
        """Handle individual optimization result (live update).

        Args:
            signal_type: Signal type (entry_long, entry_short, etc.)
            result: Optimization result dictionary
        """
        # Add to results storage
        if signal_type not in self._ind_v2_optimization_results:
            self._ind_v2_optimization_results[signal_type] = []

        self._ind_v2_optimization_results[signal_type].append(result)

        # Update live results table (add row)
        row = self._ind_v2_live_results_table.rowCount()
        self._ind_v2_live_results_table.insertRow(row)

        # Signal Type
        self._ind_v2_live_results_table.setItem(
            row, 0, QTableWidgetItem(signal_type.replace("_", " ").title())
        )

        # Indicator
        self._ind_v2_live_results_table.setItem(
            row, 1, QTableWidgetItem(result.get("indicator", "N/A"))
        )

        # Score (color-coded)
        score = result.get("score", 0.0)
        score_item = QTableWidgetItem(f"{score:.1f}")
        score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if score >= 70:
            score_item.setBackground(Qt.GlobalColor.green)
        elif score >= 50:
            score_item.setBackground(Qt.GlobalColor.yellow)
        else:
            score_item.setBackground(Qt.GlobalColor.red)
        self._ind_v2_live_results_table.setItem(row, 2, score_item)

        # Win Rate
        win_rate = result.get("win_rate", 0.0)
        self._ind_v2_live_results_table.setItem(row, 3, QTableWidgetItem(f"{win_rate:.1%}"))

        # Profit Factor
        profit_factor = result.get("profit_factor", 0.0)
        self._ind_v2_live_results_table.setItem(row, 4, QTableWidgetItem(f"{profit_factor:.2f}"))

        # Sharpe Ratio
        sharpe = result.get("sharpe_ratio", 0.0)
        self._ind_v2_live_results_table.setItem(row, 5, QTableWidgetItem(f"{sharpe:.2f}"))

        # Trades
        trades = result.get("trades", 0)
        self._ind_v2_live_results_table.setItem(row, 6, QTableWidgetItem(str(trades)))

        # Parameters
        params = result.get("params", {})
        params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
        self._ind_v2_live_results_table.setItem(row, 7, QTableWidgetItem(params_str))

        # Auto-scroll to bottom
        self._ind_v2_live_results_table.scrollToBottom()

    def _on_indicator_v2_finished(self, all_results: dict) -> None:
        """Handle optimization completion.

        Args:
            all_results: Dictionary of results per signal type
        """
        # Update UI state
        self._ind_v2_start_btn.setEnabled(True)
        self._ind_v2_stop_btn.setEnabled(False)

        # Set all progress bars to 100%
        for signal_type, progress_bar in self._ind_v2_signal_progress.items():
            if signal_type in all_results:
                progress_bar.setValue(progress_bar.maximum())

        # Calculate summary
        total_results = sum(len(results) for results in all_results.values())
        best_overall = None
        best_score = 0.0

        for signal_type, results in all_results.items():
            if results:
                best_in_type = max(results, key=lambda r: r.get("score", 0.0))
                if best_in_type.get("score", 0.0) > best_score:
                    best_score = best_in_type["score"]
                    best_overall = (signal_type, best_in_type)

        # Show completion message
        regime = self._ind_v2_regime_combo.currentText()
        msg = (
            f"Stage 2 Optimization Complete!\n\n"
            f"Regime: {regime}\n"
            f"Total Results: {total_results}\n"
        )

        if best_overall:
            signal_type, best_result = best_overall
            msg += (
                f"\nBest Result:\n"
                f"• Signal Type: {signal_type.replace('_', ' ').title()}\n"
                f"• Indicator: {best_result.get('indicator', 'N/A')}\n"
                f"• Score: {best_result.get('score', 0.0):.1f}\n"
                f"• Win Rate: {best_result.get('win_rate', 0.0):.1%}\n"
                f"• Profit Factor: {best_result.get('profit_factor', 0.0):.2f}"
            )

        QMessageBox.information(self, "Optimization Complete", msg)
        logger.info(f"Stage 2 optimization completed with {total_results} total results")

    def _on_indicator_v2_error(self, error_message: str) -> None:
        """Handle optimization error.

        Args:
            error_message: Error description
        """
        # Update UI state
        self._ind_v2_start_btn.setEnabled(True)
        self._ind_v2_stop_btn.setEnabled(False)

        # Show error
        QMessageBox.critical(
            self,
            "Optimization Error",
            f"An error occurred during optimization:\n\n{error_message}",
        )
        logger.error(f"Stage 2 optimization error: {error_message}")
