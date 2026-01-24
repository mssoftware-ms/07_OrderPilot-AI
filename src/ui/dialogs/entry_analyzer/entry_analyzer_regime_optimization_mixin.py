"""Entry Analyzer - Regime Optimization Tab (Mixin).

Stufe-1: Regime-Optimierung - Tab 2/3
Provides UI for running regime optimization:
- Start/Stop buttons
- Progress bar with ETA
- Live updating top-5 results table
- Status messages
- TPE-based optimization using RegimeOptimizer
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon
from src.ui.threads.regime_optimization_thread import RegimeOptimizationThread

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RegimeOptimizationMixin:
    """Mixin for Regime Optimization tab in Entry Analyzer.

    Provides:
        - Start/Stop optimization controls
        - Progress tracking with ETA
        - Live top-5 results table
        - TPE-based optimization execution
    """

    # Type hints for parent class attributes
    _regime_opt_start_btn: QPushButton
    _regime_opt_stop_btn: QPushButton
    _regime_opt_progress_bar: QProgressBar
    _regime_opt_status_label: QLabel
    _regime_opt_eta_label: QLabel
    _regime_opt_top5_table: QTableWidget
    _regime_opt_thread: RegimeOptimizationThread | None
    _regime_opt_all_results: list[dict]
    _regime_opt_start_time: datetime | None

    def _setup_regime_optimization_tab(self, tab: QWidget) -> None:
        """Setup Regime Optimization tab with controls and live results.

        Args:
            tab: QWidget to populate
        """
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel("Regime Optimization (TPE)")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)

        description = QLabel(
            "Run TPE-based optimization to find optimal regime detection parameters. "
            "Progress and top-5 results are shown below."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(description)

        # Current Regime Score Display
        current_score_layout = QHBoxLayout()
        current_score_layout.addWidget(QLabel("Current Regime Score:"))
        self._regime_opt_current_score_label = QLabel("--")
        self._regime_opt_current_score_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #3b82f6;")
        self._regime_opt_current_score_label.setToolTip("Score of currently active regime configuration")
        current_score_layout.addWidget(self._regime_opt_current_score_label)
        current_score_layout.addStretch()

        refresh_score_btn = QPushButton(get_icon("refresh"), "Calculate Current Score")
        refresh_score_btn.setToolTip("Calculate score for currently active regime parameters")
        refresh_score_btn.clicked.connect(self._on_calculate_current_regime_score)
        current_score_layout.addWidget(refresh_score_btn)
        layout.addLayout(current_score_layout)

        # Control Buttons
        control_layout = QHBoxLayout()
        self._regime_opt_start_btn = QPushButton(get_icon("play_arrow"), "Start Optimization")
        self._regime_opt_start_btn.setProperty("class", "success")
        self._regime_opt_start_btn.clicked.connect(self._on_regime_opt_start)
        control_layout.addWidget(self._regime_opt_start_btn)

        self._regime_opt_stop_btn = QPushButton(get_icon("stop"), "Stop")
        self._regime_opt_stop_btn.setProperty("class", "danger")
        self._regime_opt_stop_btn.setEnabled(False)
        self._regime_opt_stop_btn.clicked.connect(self._on_regime_opt_stop)
        control_layout.addWidget(self._regime_opt_stop_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Progress Bar
        progress_layout = QVBoxLayout()
        progress_label = QLabel("Progress:")
        progress_layout.addWidget(progress_label)

        self._regime_opt_progress_bar = QProgressBar()
        self._regime_opt_progress_bar.setRange(0, 100)
        self._regime_opt_progress_bar.setValue(0)
        progress_layout.addWidget(self._regime_opt_progress_bar)

        layout.addLayout(progress_layout)

        # Status and ETA
        status_layout = QHBoxLayout()
        self._regime_opt_status_label = QLabel(
            "Ready. Configure parameters in 'Regime Setup' tab and click 'Start'."
        )
        self._regime_opt_status_label.setWordWrap(True)
        status_layout.addWidget(self._regime_opt_status_label, stretch=1)

        self._regime_opt_eta_label = QLabel("ETA: --")
        self._regime_opt_eta_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self._regime_opt_eta_label)

        layout.addLayout(status_layout)

        # Live Results Table (filtered by score)
        results_label = QLabel("Live Results (Score > 50 or Best 10):")
        results_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(results_label)

        self._regime_opt_top5_table = QTableWidget()
        self._regime_opt_top5_table.setColumnCount(13)
        self._regime_opt_top5_table.setHorizontalHeaderLabels(
            [
                "Rank",
                "Score",
                "ADX Period",
                "ADX Thresh",
                "SMA Fast",
                "SMA Slow",
                "RSI Period",
                "RSI Low",
                "RSI High",
                "BB Period",
                "BB Std Dev",
                "BB Width %",
                "Trial #",
            ]
        )
        # Make table sortable
        self._regime_opt_top5_table.setSortingEnabled(True)
        self._regime_opt_top5_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self._regime_opt_top5_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._regime_opt_top5_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._regime_opt_top5_table.setMinimumHeight(600)  # Increased from 200 to 600 (+200%)
        self._regime_opt_top5_table.setMaximumHeight(800)  # Allow scrolling beyond 600
        layout.addWidget(self._regime_opt_top5_table)

        layout.addStretch()

        # Selection Info
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("💡 Tip: Select a row, then click 'Apply Selected' or 'Save to History'"))
        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # Action Buttons
        action_layout = QHBoxLayout()

        # Export Button
        self._regime_opt_export_btn = QPushButton(get_icon("save"), "Export Results (JSON)")
        self._regime_opt_export_btn.setEnabled(False)
        self._regime_opt_export_btn.setToolTip("Export optimization results with parameter ranges to JSON file")
        self._regime_opt_export_btn.clicked.connect(self._on_regime_opt_export)
        action_layout.addWidget(self._regime_opt_export_btn)

        # Save Selected to History Button
        self._regime_opt_save_history_btn = QPushButton(get_icon("history"), "Save Selected to History")
        self._regime_opt_save_history_btn.setEnabled(False)
        self._regime_opt_save_history_btn.setToolTip(
            "Save selected result to optimization_results[] in JSON\n"
            "Keeps top 10 results in history for future reference"
        )
        self._regime_opt_save_history_btn.clicked.connect(self._on_save_selected_to_history)
        action_layout.addWidget(self._regime_opt_save_history_btn)

        # Save & Load in Regime Button
        self._regime_opt_apply_selected_btn = QPushButton(get_icon("check_circle"), "Save && Load in Regime")
        self._regime_opt_apply_selected_btn.setEnabled(False)
        self._regime_opt_apply_selected_btn.setProperty("class", "success")
        self._regime_opt_apply_selected_btn.setToolTip(
            "Save SELECTED result as new regime config file\n"
            "Updates indicator parameters and regime thresholds\n"
            "Clears tables and loads config in Regime tab"
        )
        self._regime_opt_apply_selected_btn.clicked.connect(self._on_apply_selected_to_regime_config)
        action_layout.addWidget(self._regime_opt_apply_selected_btn)

        action_layout.addStretch()

        # Continue Button
        self._regime_opt_continue_btn = QPushButton(get_icon("arrow_forward"), "View All Results →")
        self._regime_opt_continue_btn.setEnabled(False)
        self._regime_opt_continue_btn.clicked.connect(self._on_regime_opt_continue)
        action_layout.addWidget(self._regime_opt_continue_btn)
        layout.addLayout(action_layout)

        # Initialize state
        self._regime_opt_thread = None
        self._regime_opt_all_results = []
        self._regime_opt_start_time = None

    @pyqtSlot()
    def _on_regime_opt_start(self) -> None:
        """Start regime optimization."""
        # Get config from Regime Setup tab
        if not hasattr(self, "_regime_setup_config"):
            self._regime_opt_status_label.setText(
                "⚠️ Please configure parameters in 'Regime Setup' tab first!"
            )
            self._regime_opt_status_label.setStyleSheet("color: #f59e0b;")
            return

        # Get chart data
        if not hasattr(self, "_candles") or len(self._candles) == 0:
            self._regime_opt_status_label.setText(
                "⚠️ No chart data available. Please load chart first!"
            )
            self._regime_opt_status_label.setStyleSheet("color: #f59e0b;")
            return

        # Minimum 200 candles required for SMA(200) warmup period
        MIN_CANDLES_REQUIRED = 200
        candle_count = len(self._candles)
        if candle_count < MIN_CANDLES_REQUIRED:
            timeframe = getattr(self, "_current_timeframe", "5m")
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            required_hours = (timeframe_minutes * MIN_CANDLES_REQUIRED) / 60
            required_days = (timeframe_minutes * MIN_CANDLES_REQUIRED) / 1440

            if required_days >= 1:
                time_info = f"{required_days:.1f} Tage ({required_hours:.1f} Stunden)"
            else:
                time_info = f"{required_hours:.1f} Stunden"

            self._regime_opt_status_label.setText(
                f"⚠️ Analyse kann nicht ausgeführt werden!\n"
                f"Mindestens {MIN_CANDLES_REQUIRED} Kerzen benötigt (aktuell: {candle_count}).\n"
                f"Bei {timeframe} Kerzen: mindestens {time_info}.\n"
                f"Bitte Zeitraum ändern."
            )
            self._regime_opt_status_label.setStyleSheet("color: #ef4444;")
            logger.warning(
                f"Insufficient candles for analysis: {candle_count} < {MIN_CANDLES_REQUIRED}. "
                f"Timeframe: {timeframe}, required: {time_info}"
            )
            return

        logger.info(f"Starting regime optimization with TPE ({candle_count} candles)")

        # Convert candles to DataFrame
        import pandas as pd

        df = pd.DataFrame(self._candles)
        if "timestamp" in df.columns:
            df.set_index("timestamp", inplace=True)

        # Build param_grid from config
        param_grid = {}
        for param_name, param_config in self._regime_setup_config.items():
            if isinstance(param_config, dict) and "min" in param_config and "max" in param_config:
                # For TPE, we just pass min/max ranges, not all values
                min_val = param_config["min"]
                max_val = param_config["max"]

                # Handle float vs int parameters
                if isinstance(min_val, float) or isinstance(max_val, float):
                    # Float parameter: Create sample values with numpy linspace
                    import numpy as np
                    param_grid[param_name] = list(np.linspace(min_val, max_val, num=10))
                else:
                    # Integer parameter: Use range
                    param_grid[param_name] = list(range(min_val, max_val + 1))

        # Get config template path
        # Use default regime config from project
        # Path: src/ui/dialogs/entry_analyzer/this_file.py -> 5x parent = project root
        config_template_path = str(
            Path(__file__).parent.parent.parent.parent.parent / "config" / "regime_config_default.json"
        )

        # Get max_trials from UI
        max_trials = getattr(self, "_regime_setup_max_trials", None)
        if max_trials:
            max_trials_value = max_trials.value()
        else:
            max_trials_value = 150  # Default fallback

        # Create and start optimization thread
        self._regime_opt_thread = RegimeOptimizationThread(
            df=df,
            config_template_path=config_template_path,
            param_grid=param_grid,
            scope="entry",
            max_trials=max_trials_value
        )

        # Connect signals
        self._regime_opt_thread.progress.connect(self._on_regime_opt_progress)
        self._regime_opt_thread.result_ready.connect(self._on_regime_opt_result)
        self._regime_opt_thread.finished_with_results.connect(self._on_regime_opt_finished)
        self._regime_opt_thread.error.connect(self._on_regime_opt_error)

        # Update UI
        self._regime_opt_start_btn.setEnabled(False)
        self._regime_opt_stop_btn.setEnabled(True)
        self._regime_opt_status_label.setText("Optimization running...")
        self._regime_opt_status_label.setStyleSheet("")
        self._regime_opt_all_results = []
        self._regime_opt_top5_table.setRowCount(0)
        self._regime_opt_start_time = datetime.utcnow()

        # Show waiting dialog during entire optimization
        from src.ui.widgets import OptimizationWaitingDialog
        self._waiting_dialog = OptimizationWaitingDialog(self)
        self._waiting_dialog.set_status(f"Starte Optimierung mit {max_trials_value} Trials...")
        self._waiting_dialog.show()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Start thread
        self._regime_opt_thread.start()

    @pyqtSlot()
    def _on_regime_opt_stop(self) -> None:
        """Stop regime optimization gracefully."""
        if self._regime_opt_thread and self._regime_opt_thread.isRunning():
            logger.info("Requesting optimization stop")
            self._regime_opt_thread.request_stop()
            self._regime_opt_status_label.setText(
                "Stopping optimization... (finishing current trial)"
            )
            self._regime_opt_status_label.setStyleSheet("color: #f59e0b;")

            # Update waiting dialog
            if hasattr(self, "_waiting_dialog") and self._waiting_dialog and self._waiting_dialog.isVisible():
                self._waiting_dialog.set_status("Stoppe Optimierung...")

    @pyqtSlot(int, int, str)
    def _on_regime_opt_progress(self, current: int, total: int, message: str) -> None:
        """Handle progress update.

        Args:
            current: Current trial number
            total: Total trials
            message: Progress message
        """
        # Update progress bar
        progress_pct = int((current / total) * 100) if total > 0 else 0
        self._regime_opt_progress_bar.setValue(progress_pct)

        # Update status
        self._regime_opt_status_label.setText(f"Trial {current}/{total}: {message}")

        # Calculate ETA
        eta_text = "--"
        if self._regime_opt_start_time and current > 0:
            elapsed = (datetime.utcnow() - self._regime_opt_start_time).total_seconds()
            avg_per_trial = elapsed / current
            remaining_trials = total - current
            eta_seconds = int(avg_per_trial * remaining_trials)

            if eta_seconds < 60:
                eta_text = f"{eta_seconds}s"
            elif eta_seconds < 3600:
                eta_text = f"{eta_seconds // 60}m {eta_seconds % 60}s"
            else:
                hours = eta_seconds // 3600
                minutes = (eta_seconds % 3600) // 60
                eta_text = f"{hours}h {minutes}m"

            self._regime_opt_eta_label.setText(f"ETA: {eta_text}")

        # Update waiting dialog if open
        if hasattr(self, "_waiting_dialog") and self._waiting_dialog and self._waiting_dialog.isVisible():
            self._waiting_dialog.set_status(f"Trial {current}/{total} ({progress_pct}%) - ETA: {eta_text}")

    @pyqtSlot(dict)
    def _on_regime_opt_result(self, result: dict) -> None:
        """Handle individual optimization result.

        Args:
            result: Result dictionary from optimization
        """
        # Add to results list
        self._regime_opt_all_results.append(result)

        # Sort by score and update top-5 table
        self._regime_opt_all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        self._update_regime_opt_top5_table()

    @pyqtSlot(list)
    def _on_regime_opt_finished(self, results: list) -> None:
        """Handle optimization completion.

        Args:
            results: All optimization results
        """
        from PyQt6.QtWidgets import QApplication

        logger.info(f"Regime optimization complete: {len(results)} trials")

        # Ensure waiting dialog is visible (should already be open from start)
        if not hasattr(self, "_waiting_dialog") or not self._waiting_dialog:
            from src.ui.widgets import OptimizationWaitingDialog
            self._waiting_dialog = OptimizationWaitingDialog(self)
            self._waiting_dialog.show()

        self._waiting_dialog.set_status("Optimierung abgeschlossen - Verarbeite Ergebnisse...")
        QApplication.processEvents()

        # Update results
        self._regime_opt_all_results = results
        self._regime_opt_progress_bar.setValue(100)

        # Calculate elapsed time
        elapsed = (
            (datetime.utcnow() - self._regime_opt_start_time).total_seconds()
            if self._regime_opt_start_time
            else 0
        )
        elapsed_text = (
            f"{int(elapsed)}s" if elapsed < 60 else f"{int(elapsed / 60)}m {int(elapsed % 60)}s"
        )

        # Update status
        self._waiting_dialog.set_status("Ergebnisse werden sortiert...")
        QApplication.processEvents()

        # Update UI buttons
        self._regime_opt_start_btn.setEnabled(True)
        self._regime_opt_stop_btn.setEnabled(False)
        self._regime_opt_continue_btn.setEnabled(True)
        self._regime_opt_export_btn.setEnabled(True)
        self._regime_opt_save_history_btn.setEnabled(True)
        self._regime_opt_apply_selected_btn.setEnabled(True)

        self._regime_opt_status_label.setText(
            f"✅ Optimization complete! {len(results)} trials in {elapsed_text}. "
            f"Best score: {results[0]['score']:.1f}"
        )
        self._regime_opt_status_label.setStyleSheet("color: #22c55e;")
        self._regime_opt_eta_label.setText(f"Total: {elapsed_text}")

        # Update top-5 table with waiting dialog feedback
        self._waiting_dialog.set_status("Top-Ergebnisse werden geladen...")
        QApplication.processEvents()
        self._update_regime_opt_top5_table()

        # Enable Regime Results tab and populate it
        if hasattr(self, "_tabs"):
            for i in range(self._tabs.count()):
                if "Regime Results" in self._tabs.tabText(
                    i
                ) or "3. Regime Results" in self._tabs.tabText(i):
                    self._tabs.setTabEnabled(i, True)
                    break

        # Populate results table in Regime Results tab
        if hasattr(self, "_populate_regime_results_table"):
            self._waiting_dialog.set_status("Detaillierte Ergebnisse werden geladen...")
            QApplication.processEvents()
            self._populate_regime_results_table()

        # Close waiting dialog with short delay
        self._waiting_dialog.close_with_delay(800)

    @pyqtSlot(str)
    def _on_regime_opt_error(self, error_msg: str) -> None:
        """Handle optimization error.

        Args:
            error_msg: Error message
        """
        logger.error(f"Regime optimization error: {error_msg}")

        # Close waiting dialog if open
        if hasattr(self, "_waiting_dialog") and self._waiting_dialog:
            self._waiting_dialog.close()
            self._waiting_dialog = None

        # Update UI
        self._regime_opt_start_btn.setEnabled(True)
        self._regime_opt_stop_btn.setEnabled(False)
        self._regime_opt_status_label.setText(f"❌ Error: {error_msg}")
        self._regime_opt_status_label.setStyleSheet("color: #ef4444;")
        self._regime_opt_eta_label.setText("ETA: --")

    def _update_regime_opt_top5_table(self) -> None:
        """Update results table filtered by score > 50 (or best 10 if none)."""
        from PyQt6.QtWidgets import QApplication

        # Filter results: all with score > 50, or best 10 if none
        results_to_show = [r for r in self._regime_opt_all_results if r.get("score", 0) > 50]

        if not results_to_show:
            # No results over 50, show best 10
            results_to_show = self._regime_opt_all_results[:10]
            logger.info(f"No results with score > 50, showing best {len(results_to_show)} results")
        else:
            logger.info(f"Showing {len(results_to_show)} results with score > 50")

        # Disable visual updates and sorting while updating for better performance
        self._regime_opt_top5_table.setUpdatesEnabled(False)
        self._regime_opt_top5_table.setSortingEnabled(False)
        self._regime_opt_top5_table.setRowCount(len(results_to_show))

        for row, result in enumerate(results_to_show):
            # Process events every 5 rows to keep spinner animation smooth
            if row > 0 and row % 5 == 0:
                QApplication.processEvents()
                # Update waiting dialog with progress
                if hasattr(self, "_waiting_dialog") and self._waiting_dialog and self._waiting_dialog.isVisible():
                    progress = int((row / len(results_to_show)) * 100)
                    self._waiting_dialog.set_status(f"Top-Ergebnisse: {row}/{len(results_to_show)} ({progress}%)")
            params = result.get("params", {})
            score = result.get("score", 0)
            trial_num = result.get("trial_number", row + 1)

            # Debug logging to check params structure
            if row == 0:
                logger.debug(f"First result params type: {type(params)}, keys: {list(params.keys()) if isinstance(params, dict) else 'NOT A DICT'}")
                logger.debug(f"First result score: {score}, params sample: {str(params)[:200]}")

            # Column 0: Rank
            self._regime_opt_top5_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            # Column 1: Score
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_opt_top5_table.setItem(row, 1, score_item)

            # Column 2: ADX Period
            adx_period = params.get("adx_period", params.get("adx.period", "--"))
            self._regime_opt_top5_table.setItem(row, 2, QTableWidgetItem(str(adx_period)))

            # Column 3: ADX Threshold
            adx_thresh = params.get("adx_threshold", params.get("adx.threshold", "--"))
            self._regime_opt_top5_table.setItem(row, 3, QTableWidgetItem(str(adx_thresh)))

            # Column 4: SMA Fast
            sma_fast = params.get("sma_fast_period", params.get("sma_fast.period", "--"))
            self._regime_opt_top5_table.setItem(row, 4, QTableWidgetItem(str(sma_fast)))

            # Column 5: SMA Slow
            sma_slow = params.get("sma_slow_period", params.get("sma_slow.period", "--"))
            self._regime_opt_top5_table.setItem(row, 5, QTableWidgetItem(str(sma_slow)))

            # Column 6: RSI Period
            rsi_period = params.get("rsi_period", params.get("rsi.period", "--"))
            self._regime_opt_top5_table.setItem(row, 6, QTableWidgetItem(str(rsi_period)))

            # Column 7: RSI Sideways Low
            rsi_low = params.get("rsi_sideways_low", params.get("rsi.sideways_low", "--"))
            self._regime_opt_top5_table.setItem(row, 7, QTableWidgetItem(str(rsi_low)))

            # Column 8: RSI Sideways High
            rsi_high = params.get("rsi_sideways_high", params.get("rsi.sideways_high", "--"))
            self._regime_opt_top5_table.setItem(row, 8, QTableWidgetItem(str(rsi_high)))

            # Column 9: BB Period
            bb_period = params.get("bb_period", params.get("bb.period", "--"))
            self._regime_opt_top5_table.setItem(row, 9, QTableWidgetItem(str(bb_period)))

            # Column 10: BB Std Dev
            bb_std = params.get("bb_std_dev", params.get("bb.std_dev", "--"))
            self._regime_opt_top5_table.setItem(row, 10, QTableWidgetItem(str(bb_std)))

            # Column 11: BB Width Percentile
            bb_width = params.get("bb_width_percentile", params.get("bb.width_percentile", "--"))
            self._regime_opt_top5_table.setItem(row, 11, QTableWidgetItem(str(bb_width)))

            # Column 12: Trial Number
            trial_item = QTableWidgetItem(str(trial_num))
            trial_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_opt_top5_table.setItem(row, 12, trial_item)

        # Re-enable visual updates and sorting
        self._regime_opt_top5_table.setUpdatesEnabled(True)
        self._regime_opt_top5_table.setSortingEnabled(True)

        # Final UI update
        QApplication.processEvents()

    @pyqtSlot()
    def _on_regime_opt_export(self) -> None:
        """Export optimization results with parameter ranges to JSON."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json

        if not self._regime_opt_all_results:
            QMessageBox.warning(
                self,
                "No Results",
                "No optimization results available. Run optimization first."
            )
            return

        # Get default export directory
        # Path: src/ui/dialogs/entry_analyzer/this_file.py -> 5x parent = project root
        project_root = Path(__file__).parent.parent.parent.parent.parent
        default_dir = project_root / "03_JSON" / "Entry_Analyzer" / "Regime"
        default_dir.mkdir(parents=True, exist_ok=True)

        # Get symbol and timeframe for filename with timestamp
        symbol = getattr(self, "_current_symbol", "BTCUSDT")
        timeframe = getattr(self, "_current_timeframe", "5m")
        timestamp = datetime.utcnow().strftime("%y%m%d%H%M%S")
        default_filename = f"{timestamp}_regime_optimization_results_{symbol}_{timeframe}.json"

        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Regime Optimization Results",
            str(default_dir / default_filename),
            "JSON Files (*.json)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Get parameter ranges from Setup tab
            param_ranges = {}
            if hasattr(self, "_regime_setup_config"):
                param_ranges = self._regime_setup_config.copy()

            # Get max_trials
            max_trials = getattr(self, "_regime_setup_max_trials", None)
            max_trials_value = max_trials.value() if max_trials else 150

            # Issue #28: Get entry_params and evaluation_params from config if available
            entry_params = {}
            evaluation_params = {}
            if hasattr(self, "_regime_config") and self._regime_config:
                if hasattr(self._regime_config, "entry_params") and self._regime_config.entry_params:
                    entry_params = self._regime_config.entry_params
                if hasattr(self._regime_config, "evaluation_params") and self._regime_config.evaluation_params:
                    evaluation_params = self._regime_config.evaluation_params

            # Build export data
            export_data = {
                "version": "2.0",
                "meta": {
                    "stage": "regime_optimization",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "total_combinations": len(self._regime_opt_all_results),
                    "completed": len(self._regime_opt_all_results),
                    "method": "tpe_multivariate",
                    "max_trials": max_trials_value,
                },
                "parameter_ranges": param_ranges,
                "results": self._regime_opt_all_results,
            }

            # Issue #28: Include entry_params and evaluation_params if present
            if entry_params:
                export_data["entry_params"] = entry_params
            if evaluation_params:
                export_data["evaluation_params"] = evaluation_params

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(self._regime_opt_all_results)} results to {file_path}")

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(self._regime_opt_all_results)} results to:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export results:\n{str(e)}"
            )

    @pyqtSlot()
    def _on_regime_opt_continue(self) -> None:
        """Continue to Regime Results tab."""
        if hasattr(self, "_tabs"):
            # Find the Regime Results tab (next tab)
            current_index = self._tabs.currentIndex()
            next_index = current_index + 1
            if next_index < self._tabs.count():
                self._tabs.setTabEnabled(next_index, True)
                self._tabs.setCurrentIndex(next_index)

        logger.info("Continuing to Regime Results tab")

    @pyqtSlot()
    def _on_calculate_current_regime_score(self) -> None:
        """Calculate and display score for currently active regime configuration."""
        from PyQt6.QtWidgets import QMessageBox

        # Check if we have chart data
        if not hasattr(self, "_candles") or len(self._candles) == 0:
            QMessageBox.warning(
                self,
                "No Data",
                "No chart data available. Please load chart first!"
            )
            return

        # Minimum 200 candles required for SMA(200) warmup period
        MIN_CANDLES_REQUIRED = 200
        candle_count = len(self._candles)
        if candle_count < MIN_CANDLES_REQUIRED:
            timeframe = getattr(self, "_current_timeframe", "5m")
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            required_hours = (timeframe_minutes * MIN_CANDLES_REQUIRED) / 60
            required_days = (timeframe_minutes * MIN_CANDLES_REQUIRED) / 1440

            if required_days >= 1:
                time_info = f"{required_days:.1f} Tage ({required_hours:.1f} Stunden)"
            else:
                time_info = f"{required_hours:.1f} Stunden"

            QMessageBox.warning(
                self,
                "Unzureichende Daten",
                f"Analyse kann nicht ausgeführt werden!\n\n"
                f"Mindestens {MIN_CANDLES_REQUIRED} Kerzen benötigt.\n"
                f"Aktuell vorhanden: {candle_count} Kerzen.\n\n"
                f"Bei {timeframe} Kerzen benötigen Sie mindestens:\n"
                f"• {time_info}\n\n"
                f"Bitte Zeitraum im Chart ändern."
            )
            return

        try:
            # Get current regime config from main app
            # This would typically come from the active trading bot config
            # For now, we'll use default values or load from a config file
            from src.core.regime_optimizer import (
                RegimeOptimizer,
                AllParamRanges,
                ADXParamRanges,
                SMAParamRanges,
                RSIParamRanges,
                BBParamRanges,
                ParamRange,
                RegimeParams,
            )
            import pandas as pd

            # Convert candles to DataFrame
            df = pd.DataFrame(self._candles)
            if "timestamp" in df.columns:
                df.set_index("timestamp", inplace=True)

            # TODO: Load actual current regime params from config
            # For now, use default/standard values as example
            current_params = RegimeParams(
                adx_period=14,
                adx_threshold=25.0,
                sma_fast_period=50,
                sma_slow_period=200,
                rsi_period=14,
                rsi_sideways_low=40,
                rsi_sideways_high=60,
                bb_period=20,
                bb_std_dev=2.0,
                bb_width_percentile=30.0,
            )

            # Create minimal optimizer to calculate score
            param_ranges = AllParamRanges(
                adx=ADXParamRanges(
                    period=ParamRange(min=14, max=14, step=1),
                    threshold=ParamRange(min=25, max=25, step=1),
                ),
                sma_fast=SMAParamRanges(
                    period=ParamRange(min=50, max=50, step=1)
                ),
                sma_slow=SMAParamRanges(
                    period=ParamRange(min=200, max=200, step=1)
                ),
                rsi=RSIParamRanges(
                    period=ParamRange(min=14, max=14, step=1),
                    sideways_low=ParamRange(min=40, max=40, step=1),
                    sideways_high=ParamRange(min=60, max=60, step=1),
                ),
                bb=BBParamRanges(
                    period=ParamRange(min=20, max=20, step=1),
                    std_dev=ParamRange(min=2.0, max=2.0, step=0.1),
                    width_percentile=ParamRange(min=30, max=30, step=1),
                ),
            )

            # Create optimizer with default config (we only use it for score calculation,
            # not for running optimization, so config values don't matter)
            optimizer = RegimeOptimizer(
                data=df,
                param_ranges=param_ranges,
            )

            # Calculate indicators and metrics
            indicators = optimizer._calculate_indicators(current_params)
            regimes = optimizer._classify_regimes(current_params, indicators)
            metrics = optimizer._calculate_metrics(regimes, current_params)
            score = optimizer._calculate_composite_score(metrics)

            # Update label
            self._regime_opt_current_score_label.setText(f"{score:.2f}")
            self._regime_opt_current_score_label.setStyleSheet(
                f"font-weight: bold; font-size: 12pt; color: {'#22c55e' if score >= 75 else '#ef4444'};"
            )

            logger.info(f"Current regime score: {score:.2f}")

        except Exception as e:
            logger.error(f"Failed to calculate current regime score: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Calculation Failed",
                f"Failed to calculate score:\n{str(e)}"
            )

    @pyqtSlot()
    def _on_save_selected_to_history(self) -> None:
        """Save selected optimization result to optimization_results[] in JSON.

        Adds selected result to history without applying parameters.
        Keeps top 10 results in history.
        """
        from PyQt6.QtWidgets import QMessageBox
        import json

        try:
            # Get selected row from table
            selected_rows = self._regime_opt_top5_table.selectedItems()
            if not selected_rows:
                QMessageBox.warning(
                    self,
                    "No Selection",
                    "Please select a result row from the table first."
                )
                return

            # Get row index
            row = selected_rows[0].row()
            if row >= len(self._regime_opt_all_results):
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Selected row is out of range."
                )
                return

            selected_result = self._regime_opt_all_results[row]
            params = selected_result.get("params", {})
            score = selected_result.get("score", 0)
            metrics = selected_result.get("metrics", {})
            trial_number = selected_result.get("trial_number", row + 1)

            logger.info(f"Saving optimization result (score {score:.2f}) to history")

            # Load current JSON config
            config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")
            if not config_path.exists():
                QMessageBox.critical(
                    self,
                    "Config Not Found",
                    f"Regime config file not found:\n{config_path}"
                )
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Convert params to new v2.0 format (indicator.param: value)
            converted_params = self._convert_params_to_v2_format(params)

            # Create optimization result entry
            result_entry = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "score": float(score),
                "rank": row + 1,
                "params": converted_params,
                "metrics": metrics,
                "trial_number": trial_number,
                "optimization_config": {
                    "mode": "QUICK",
                    "max_trials": getattr(self, "_regime_setup_max_trials", None).value() if hasattr(self, "_regime_setup_max_trials") else 150,
                    "symbol": getattr(self, "_current_symbol", "UNKNOWN"),
                    "timeframe": getattr(self, "_current_timeframe", "5m")
                },
                "applied": False
            }

            # Add to optimization_results (insert at beginning)
            if "optimization_results" not in config_data:
                config_data["optimization_results"] = []

            config_data["optimization_results"].insert(0, result_entry)

            # Keep only top 10
            config_data["optimization_results"] = config_data["optimization_results"][:10]

            # Update metadata
            config_data["metadata"]["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            # Save updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully saved result to history: {config_path}")

            QMessageBox.information(
                self,
                "Saved to History",
                f"Successfully saved optimization result to history!\n\n"
                f"Score: {score:.2f}\n"
                f"Rank: {row + 1}\n"
                f"Trial: {trial_number}\n\n"
                f"Total in history: {len(config_data['optimization_results'])}/10"
            )

        except Exception as e:
            logger.error(f"Failed to save result to history: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save result to history:\n\n{str(e)}"
            )

    @pyqtSlot()
    def _on_apply_selected_to_regime_config(self) -> None:
        """Save & Load in Regime - Export selected result and load in Regime tab.

        Workflow:
        1. Load entry_analyzer_regime.json as base template
        2. Update indicator parameters and regime thresholds from selected result
        3. Save to new file: {timestamp}_regime_optimization_results_{symbol}_{timeframe}_Rank{rank}.json
        4. Clear both tables (Detected Regimes + Optimization Results)
        5. Load new file in Regime tab via Load Regime Config
        """
        from PyQt6.QtWidgets import QMessageBox
        import json

        try:
            # Get selected row from table
            selected_rows = self._regime_opt_top5_table.selectedItems()
            if not selected_rows:
                QMessageBox.warning(
                    self,
                    "No Selection",
                    "Please select a result row from the table first."
                )
                return

            # Get row index
            row = selected_rows[0].row()
            if row >= len(self._regime_opt_all_results):
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Selected row is out of range."
                )
                return

            selected_result = self._regime_opt_all_results[row]
            params = selected_result.get("params", {})
            score = selected_result.get("score", 0)
            rank = row + 1

            logger.info(f"Save & Load in Regime: Rank #{rank}, score {score:.2f}")

            # Build parameter summary dynamically
            param_summary = "\n".join([f"  {k}: {v}" for k, v in params.items()])

            # Get symbol and timeframe for filename
            symbol = getattr(self, "_current_symbol", "BTCUSDT")
            timeframe = getattr(self, "_current_timeframe", "5m")

            # Confirm with user
            reply = QMessageBox.question(
                self,
                "Save & Load in Regime",
                f"Save and load optimization result in Regime tab?\n\n"
                f"Rank: #{rank}\n"
                f"Score: {score:.2f}\n\n"
                f"Parameters:\n{param_summary}\n\n"
                f"This will:\n"
                f"1. Create new regime config (Rank #{rank})\n"
                f"2. Update indicator parameters\n"
                f"3. Update regime thresholds\n"
                f"4. Clear both tables\n"
                f"5. Load config in Regime tab",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Step 1: Load entry_analyzer_regime.json as base template
            # Path: src/ui/dialogs/entry_analyzer/this_file.py
            # Need 5x parent to reach project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            base_config_path = project_root / "03_JSON" / "Entry_Analyzer" / "Regime" / "entry_analyzer_regime.json"

            if not base_config_path.exists():
                QMessageBox.critical(
                    self,
                    "Base Config Not Found",
                    f"Base regime config file not found:\n{base_config_path}"
                )
                return

            with open(base_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Step 2: Update indicator parameters from selected result
            for param_key, param_value in params.items():
                if "." in param_key:
                    parts = param_key.split(".", 1)
                    if len(parts) == 2:
                        indicator_id, param_name = parts

                        # Skip regime thresholds (handled separately)
                        if indicator_id in ["BULL", "BEAR", "SIDEWAYS", "SIDEWAYS_OVERBOUGHT", "SIDEWAYS_OVERSOLD"]:
                            continue

                        # Find indicator in config
                        for indicator in config_data.get("indicators", []):
                            if indicator.get("id") == indicator_id:
                                if param_name in indicator.get("params", {}):
                                    # Preserve type (int vs float)
                                    current_value = indicator["params"][param_name]
                                    if isinstance(current_value, float):
                                        indicator["params"][param_name] = float(param_value)
                                    else:
                                        indicator["params"][param_name] = int(param_value)
                                    logger.debug(f"Updated {indicator_id}.{param_name} = {param_value}")
                                break

            # Step 3: Update regime thresholds
            for param_key, param_value in params.items():
                if "." in param_key:
                    parts = param_key.split(".", 1)
                    if len(parts) == 2:
                        regime_id, threshold_name = parts

                        if regime_id in ["BULL", "BEAR", "SIDEWAYS", "SIDEWAYS_OVERBOUGHT", "SIDEWAYS_OVERSOLD"]:
                            for regime in config_data.get("regimes", []):
                                if regime.get("id") == regime_id:
                                    self._update_regime_threshold(regime, threshold_name, param_value)
                                    logger.debug(f"Updated {regime_id}.{threshold_name} = {param_value}")
                                    break

            # Convert params to v2.0 format for storage
            converted_params = self._convert_params_to_v2_format(params)

            # Add to optimization_results with applied=True
            metrics = selected_result.get("metrics", {})
            trial_number = selected_result.get("trial_number", rank)

            max_trials = getattr(self, "_regime_setup_max_trials", None)
            max_trials_value = max_trials.value() if max_trials else 150

            result_entry = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "score": float(score),
                "rank": rank,
                "params": converted_params,
                "metrics": metrics,
                "trial_number": trial_number,
                "optimization_config": {
                    "mode": "QUICK",
                    "max_trials": max_trials_value,
                    "symbol": symbol,
                    "timeframe": timeframe
                },
                "applied": True
            }

            # Add to optimization_results (insert at beginning)
            if "optimization_results" not in config_data:
                config_data["optimization_results"] = []
            config_data["optimization_results"].insert(0, result_entry)
            config_data["optimization_results"] = config_data["optimization_results"][:10]

            # Update metadata
            config_data["metadata"]["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            config_data["metadata"]["notes"] = (
                f"Rank #{rank} optimization result applied on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC. "
                f"Score: {score:.2f}. Trial: {trial_number}"
            )

            # Step 4: Save to new file with Rank in filename
            export_dir = project_root / "03_JSON" / "Entry_Analyzer" / "Regime"
            logger.info(f"Export directory: {export_dir}")
            logger.info(f"Export directory exists: {export_dir.exists()}")
            export_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Export directory after mkdir: {export_dir.exists()}")

            timestamp = datetime.utcnow().strftime("%y%m%d%H%M%S")
            export_filename = f"{timestamp}_regime_optimization_results_{symbol}_{timeframe}_Rank{rank}.json"
            export_path = export_dir / export_filename
            logger.info(f"Attempting to save to: {export_path}")

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully saved regime config (Rank #{rank}) to: {export_path}")
            logger.info(f"File exists after save: {export_path.exists()}")

            # Step 5: Clear both tables
            if hasattr(self, "_detected_regimes_table"):
                self._detected_regimes_table.setRowCount(0)
                logger.info("Cleared Detected Regimes table")

            self._regime_opt_top5_table.setRowCount(0)
            logger.info("Cleared Optimization Results table")

            # Step 6: Load new file in Regime tab
            if hasattr(self, "_load_regime_config"):
                self._load_regime_config(export_path, show_error=True)
                logger.info(f"Loaded config in Regime tab: {export_path}")

            QMessageBox.information(
                self,
                "Success",
                f"Successfully saved and loaded regime config!\n\n"
                f"File: {export_filename}\n\n"
                f"Rank: #{rank}\n"
                f"Score: {score:.2f}\n\n"
                f"Config loaded in Regime tab."
            )

        except Exception as e:
            import traceback
            full_traceback = traceback.format_exc()
            logger.error(f"Failed to save & load regime config: {e}")
            logger.error(f"Full traceback:\n{full_traceback}")
            QMessageBox.critical(
                self,
                "Save & Load Failed",
                f"Failed to save & load regime config:\n\n{str(e)}\n\nDetails in log file."
            )

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes.

        Args:
            timeframe: Timeframe string like "1m", "5m", "15m", "1h", "4h", "1d"

        Returns:
            Number of minutes for one candle
        """
        timeframe = timeframe.lower().strip()

        # Parse number and unit
        if timeframe.endswith("m"):
            return int(timeframe[:-1])
        elif timeframe.endswith("h"):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith("d"):
            return int(timeframe[:-1]) * 1440
        elif timeframe.endswith("w"):
            return int(timeframe[:-1]) * 10080
        else:
            # Default to 5 minutes if unknown
            logger.warning(f"Unknown timeframe format: {timeframe}, defaulting to 5m")
            return 5

    def _convert_params_to_v2_format(self, params: dict) -> dict:
        """Convert flat optimizer parameters to v2.0 nested format.

        Args:
            params: Flat dict like {"adx_period": 14, "rsi_period": 12, ...}

        Returns:
            Nested dict like {"adx14.period": 14, "rsi14.period": 12, ...}
        """
        converted = {}

        # Known mappings from old flat format to new v2.0 format
        param_mappings = {
            "adx_period": "adx14.period",
            "adx_threshold": "BULL.adx_threshold",  # Will be duplicated for all regimes
            "rsi_period": "rsi14.period",
            "rsi_sideways_low": "SIDEWAYS.rsi_low",
            "rsi_sideways_high": "SIDEWAYS.rsi_high",
            "bb_period": "bb20.period",
            "bb_std_dev": "bb20.std_dev",
            "bb_width_percentile": "bb20.width_percentile",
            "sma_fast_period": "sma_fast.period",
            "sma_slow_period": "sma_slow.period",
            "macd_fast": "macd_12_26_9.fast",
            "macd_slow": "macd_12_26_9.slow",
            "macd_signal": "macd_12_26_9.signal",
        }

        for old_key, new_key in param_mappings.items():
            if old_key in params:
                converted[new_key] = params[old_key]

                # Special handling for shared thresholds
                if old_key == "adx_threshold":
                    # ADX threshold is used by BULL, BEAR, and all SIDEWAYS regimes
                    converted["BEAR.adx_threshold"] = params[old_key]
                    converted["SIDEWAYS.adx_threshold"] = params[old_key]
                    converted["SIDEWAYS_OVERBOUGHT.adx_threshold"] = params[old_key]
                    converted["SIDEWAYS_OVERSOLD.adx_threshold"] = params[old_key]

                elif old_key == "rsi_sideways_high":
                    # RSI high also used for SIDEWAYS_OVERBOUGHT
                    converted["SIDEWAYS_OVERBOUGHT.rsi_overbought"] = params[old_key]

                elif old_key == "rsi_sideways_low":
                    # RSI low also used for SIDEWAYS_OVERSOLD
                    converted["SIDEWAYS_OVERSOLD.rsi_oversold"] = params[old_key]

        # Pass through any already-converted params
        for key, value in params.items():
            if "." in key and key not in converted:
                converted[key] = value

        return converted

    def _update_regime_threshold(self, regime: dict, threshold_name: str, threshold_value: float) -> None:
        """Update regime threshold in conditions.

        Args:
            regime: Regime dict from JSON
            threshold_name: Name of threshold (e.g., "adx_threshold", "rsi_low")
            threshold_value: New threshold value
        """
        conditions = regime.get("conditions", {})

        # Map threshold names to condition updates
        if threshold_name == "adx_threshold":
            # Update ADX value threshold in conditions
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "adx14" and cond.get("op") in ["gt", "lt"]:
                        cond["right"]["value"] = int(threshold_value)

        elif threshold_name == "rsi_low":
            # Update RSI lower bound (SIDEWAYS regime)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi14" and cond.get("op") == "between":
                        cond["right"]["min"] = int(threshold_value)

        elif threshold_name == "rsi_high":
            # Update RSI upper bound (SIDEWAYS regime)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi14" and cond.get("op") == "between":
                        cond["right"]["max"] = int(threshold_value)

        elif threshold_name == "rsi_overbought":
            # Update RSI overbought threshold (SIDEWAYS_OVERBOUGHT)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi14" and cond.get("op") == "gt":
                        cond["right"]["value"] = int(threshold_value)

        elif threshold_name == "rsi_oversold":
            # Update RSI oversold threshold (SIDEWAYS_OVERSOLD)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi14" and cond.get("op") == "lt":
                        cond["right"]["value"] = int(threshold_value)
