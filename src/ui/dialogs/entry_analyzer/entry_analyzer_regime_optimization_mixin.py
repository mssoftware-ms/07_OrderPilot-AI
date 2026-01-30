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
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
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
    _regime_opt_max_trials: QSpinBox
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

        # Header with help button
        header_layout = QHBoxLayout()
        header = QLabel("Regime Optimization (TPE)")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        # Help button for RegimeScore
        help_btn = QPushButton(get_icon("help"), "")
        help_btn.setToolTip("Open RegimeScore Help")
        help_btn.setFixedSize(28, 28)
        help_btn.clicked.connect(self._on_regime_score_help_clicked)
        header_layout.addWidget(help_btn)
        layout.addLayout(header_layout)

        # Current Regime Score Display
        current_score_layout = QHBoxLayout()
        current_score_layout.addWidget(QLabel("Current Regime Score:"))
        self._regime_opt_current_score_label = QLabel("--")
        self._regime_opt_current_score_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #3b82f6;")
        self._regime_opt_current_score_label.setToolTip(
            "RegimeScore (0-100): Measures quality of regime detection"
        )
        current_score_layout.addWidget(self._regime_opt_current_score_label)

        # Component details label (compact)
        self._regime_opt_components_label = QLabel("")
        self._regime_opt_components_label.setStyleSheet("color: #888; font-size: 9pt;")
        current_score_layout.addWidget(self._regime_opt_components_label)

        current_score_layout.addStretch()

        refresh_score_btn = QPushButton(get_icon("refresh"), "Calculate Current Score")
        refresh_score_btn.setToolTip("Calculate RegimeScore for currently active regime parameters")
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

        # Max Trials SpinBox
        control_layout.addSpacing(20)
        control_layout.addWidget(QLabel("Max Trials:"))
        self._regime_opt_max_trials = QSpinBox()
        self._regime_opt_max_trials.setRange(10, 9999)
        self._regime_opt_max_trials.setValue(150)
        self._regime_opt_max_trials.setSingleStep(10)
        self._regime_opt_max_trials.setToolTip("Maximum number of optimization trials (10-9999)")
        self._regime_opt_max_trials.setMinimumWidth(100)
        control_layout.addWidget(self._regime_opt_max_trials)

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
        # Dynamic columns - will be set when first result arrives
        # Initial headers: Rank, Score, Trial # (parameters added dynamically)
        self._regime_opt_top5_table.setColumnCount(3)
        self._regime_opt_top5_table.setHorizontalHeaderLabels(
            ["Rank", "Score", "Trial #"]
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

        # Draw on Chart Button
        self._regime_opt_draw_btn = QPushButton(get_icon("show_chart"), "Draw on Chart")
        self._regime_opt_draw_btn.setEnabled(False)
        self._regime_opt_draw_btn.setToolTip(
            "Draw selected regime periods on chart\n"
            "Clears all existing regime lines first"
        )
        self._regime_opt_draw_btn.clicked.connect(self._on_regime_opt_draw_selected)
        action_layout.addWidget(self._regime_opt_draw_btn)

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
        max_trials = getattr(self, "_regime_opt_max_trials", None)
        if max_trials:
            max_trials_value = max_trials.value()
        else:
            max_trials_value = 150  # Default fallback

        # Get JSON config for per-regime threshold evaluation
        # This enables JSON-based regime classification with per-regime thresholds
        # instead of the simplified 3-regime global threshold model
        json_config = None
        if hasattr(self, "_regime_config") and self._regime_config:
            # Convert Pydantic model to dict if needed
            if hasattr(self._regime_config, "model_dump"):
                json_config = self._regime_config.model_dump()
            elif hasattr(self._regime_config, "dict"):
                json_config = self._regime_config.dict()
            elif isinstance(self._regime_config, dict):
                json_config = self._regime_config
            else:
                logger.warning(
                    "Could not convert _regime_config to dict, using legacy mode"
                )

            if json_config:
                logger.info("Using JSON-based regime evaluation with per-regime thresholds")

        # Create and start optimization thread
        self._regime_opt_thread = RegimeOptimizationThread(
            df=df,
            config_template_path=config_template_path,
            param_grid=param_grid,
            scope="entry",
            max_trials=max_trials_value,
            json_config=json_config
        )

        # Connect signals
        self._regime_opt_thread.progress.connect(self._on_regime_opt_progress)
        # NOTE: result_ready signal removed - was causing 150x table rebuilds
        # self._regime_opt_thread.result_ready.connect(self._on_regime_opt_result)
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

        DEPRECATED: This method caused 150x table rebuilds (once per result).
        Now we only update the table once at the end via _on_regime_opt_finished.

        Args:
            result: Result dictionary from optimization
        """
        # DEPRECATED - Signal connection removed to prevent performance issues
        pass

    @pyqtSlot(list)
    def _on_regime_opt_finished(self, results: list) -> None:
        """Handle optimization completion.

        Args:
            results: All optimization results
        """
        from PyQt6.QtWidgets import QApplication

        try:
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
            self._regime_opt_draw_btn.setEnabled(True)

            # Get best score safely
            best_score = 0
            if results and len(results) > 0:
                best_score = results[0].get('score', 0)

            self._regime_opt_status_label.setText(
                f"✅ Optimization complete! {len(results)} trials in {elapsed_text}. "
                f"Best score: {best_score:.1f}"
            )
            self._regime_opt_status_label.setStyleSheet("color: #22c55e;")
            self._regime_opt_eta_label.setText(f"Total: {elapsed_text}")

            # Update top-5 table with waiting dialog feedback
            self._waiting_dialog.set_status("Top-Ergebnisse werden geladen...")
            QApplication.processEvents()

            try:
                self._update_regime_opt_top5_table()
            except Exception as e:
                logger.error(f"Failed to update top5 table: {e}", exc_info=True)
                self._regime_opt_status_label.setText(
                    f"⚠️ Optimization complete but table update failed: {str(e)}"
                )

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

                try:
                    self._populate_regime_results_table()
                except Exception as e:
                    logger.error(f"Failed to populate regime results table: {e}", exc_info=True)

            # Close waiting dialog with short delay
            self._waiting_dialog.close_with_delay(800)

        except Exception as e:
            logger.error(f"Critical error in _on_regime_opt_finished: {e}", exc_info=True)

            # Close waiting dialog if open
            if hasattr(self, "_waiting_dialog") and self._waiting_dialog:
                self._waiting_dialog.close()

            # Show error to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Optimization Error",
                f"Failed to process optimization results:\n{str(e)}\n\nCheck logs for details."
            )

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
        """Update results table filtered by score > 50 (or best 10 if none).

        DYNAMIC column generation - NO hardcoded parameter names!
        Generates columns based on parameters in the first result.
        """
        from PyQt6.QtWidgets import QApplication

        # Filter results: all with score > 50, or best 10 if none
        results_to_show = [r for r in self._regime_opt_all_results if r.get("score", 0) > 50]

        if not results_to_show:
            # No results over 50, show best 10
            results_to_show = self._regime_opt_all_results[:10]
            logger.info(f"No results with score > 50, showing best {len(results_to_show)} results")
        else:
            logger.info(f"Showing {len(results_to_show)} results with score > 50")

        if not results_to_show:
            logger.warning("No results to display in top5 table")
            return

        # DYNAMIC COLUMN GENERATION: Get parameter names from first result
        first_result = results_to_show[0]
        params_dict = first_result.get("params", {})
        metrics_dict = first_result.get("metrics", {})

        # Sort parameter names for consistent column order
        param_names = sorted(params_dict.keys())

        # Build column headers: Rank, Total Score, [Dynamic Params], Trial #
        # Note: Score components (Sep, Coh, Fid, Bnd, Cov) removed - legacy scoring system
        headers = ["Rank", "Total"] + param_names + ["Trial #"]

        # Update table structure
        self._regime_opt_top5_table.setColumnCount(len(headers))
        self._regime_opt_top5_table.setHorizontalHeaderLabels(headers)

        # Configure header resize modes
        header = self._regime_opt_top5_table.horizontalHeader()
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        logger.info(f"Dynamic table: {len(headers)} columns ({len(param_names)} parameters)")

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
            metrics = result.get("metrics", {})
            score = result.get("score", 0)
            trial_num = result.get("trial_number", row + 1)

            # Find original index in _regime_opt_all_results
            original_index = self._regime_opt_all_results.index(result) if result in self._regime_opt_all_results else row

            col = 0

            # Column 0: Rank (display rank, but store original index in UserRole)
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_item.setData(Qt.ItemDataRole.UserRole, original_index)  # Store original index for correct retrieval
            self._regime_opt_top5_table.setItem(row, col, rank_item)
            col += 1

            # Column 1: Total Score
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Color-code score
            if score >= 75:
                score_item.setForeground(Qt.GlobalColor.darkGreen)
            elif score >= 50:
                score_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                score_item.setForeground(Qt.GlobalColor.darkRed)
            self._regime_opt_top5_table.setItem(row, col, score_item)
            col += 1

            # Dynamic Parameter Columns
            for param_name in param_names:
                param_value = params.get(param_name, "--")
                # Format value based on type
                if isinstance(param_value, float):
                    value_str = f"{param_value:.2f}"
                else:
                    value_str = str(param_value)

                param_item = QTableWidgetItem(value_str)
                param_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_opt_top5_table.setItem(row, col, param_item)
                col += 1

            # Last Column: Trial Number
            trial_item = QTableWidgetItem(str(trial_num))
            trial_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_opt_top5_table.setItem(row, col, trial_item)

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
            max_trials = getattr(self, "_regime_opt_max_trials", None)
            max_trials_value = max_trials.value() if max_trials else 150

            # Build export data
            # NOTE: entry_params and evaluation_params are NOT included -
            #       Only entry_expression is used for Trading Bot execution.
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
                RSIParamRanges,
                ATRParamRanges,
                ParamRange,
                RegimeParams,
            )
            import pandas as pd

            # Convert candles to DataFrame
            df = pd.DataFrame(self._candles)
            if "timestamp" in df.columns:
                df.set_index("timestamp", inplace=True)

            # Load ACTUAL params from JSON config (NO HARDCODED VALUES!)
            if not hasattr(self, "_regime_config") or self._regime_config is None:
                raise ValueError(
                    "No regime config loaded! Please load a JSON config in the 'Regime' tab first."
                )

            config = self._regime_config

            # Get optimized params from optimization_results if available
            optimized_params = {}
            opt_results = []
            if isinstance(config, dict):
                opt_results = config.get("optimization_results", [])
            elif hasattr(config, "optimization_results"):
                opt_results = config.optimization_results or []

            if opt_results:
                applied = [r for r in opt_results if r.get("applied", False)]
                if applied:
                    optimized_params = applied[-1].get("params", {})
                else:
                    optimized_params = opt_results[0].get("params", {})

            # Helper to get param value (optimized or base)
            def get_param(indicator_id: str, param_name: str, default: Any) -> Any:
                # Try optimized first
                opt_key = f"{indicator_id}.{param_name}"
                if opt_key in optimized_params:
                    return optimized_params[opt_key]

                # Also try underscore format (from optimizer)
                underscore_key = f"{indicator_id}_{param_name}"
                if underscore_key in optimized_params:
                    return optimized_params[underscore_key]

                # Fallback to indicators from config (dict or object)
                indicators = config.get("indicators", []) if isinstance(config, dict) else getattr(config, "indicators", [])

                # Also check optimization_results[0].indicators for v2 format
                if not indicators and isinstance(config, dict):
                    opt_results = config.get("optimization_results", [])
                    if opt_results:
                        indicators = opt_results[0].get("indicators", [])

                for ind in indicators:
                    ind_id = ind.get("id") or ind.get("name", "") if isinstance(ind, dict) else getattr(ind, "id", getattr(ind, "name", ""))
                    # Match by id or name (handle both v1 and v2 naming)
                    if ind_id.lower().replace("_", "") == indicator_id.lower().replace("_", "") or indicator_id.lower() in ind_id.lower():
                        if isinstance(ind, dict):
                            params = ind.get("params", {})
                            # v2 format: params is a list of {name, value}
                            if isinstance(params, list):
                                for p in params:
                                    if p.get("name") == param_name:
                                        return p.get("value", default)
                            else:
                                return params.get(param_name, default)
                        else:
                            return getattr(ind, "params", {}).get(param_name, default)

                return default

            # Helper for regime thresholds
            def get_regime_threshold(regime_id: str, threshold_name: str, default: Any) -> Any:
                opt_key = f"{regime_id}.{threshold_name}"
                if opt_key in optimized_params:
                    return optimized_params[opt_key]

                # Get regimes from config (dict or object)
                regimes = config.get("regimes", []) if isinstance(config, dict) else getattr(config, "regimes", [])

                # Also check optimization_results[0].regimes for v2 format
                if not regimes and isinstance(config, dict):
                    opt_results = config.get("optimization_results", [])
                    if opt_results:
                        regimes = opt_results[0].get("regimes", [])

                for regime in regimes:
                    r_id = regime.get("id", "") if isinstance(regime, dict) else getattr(regime, "id", "")
                    if r_id == regime_id:
                        if isinstance(regime, dict):
                            # v2 format: thresholds is a list of {name, value}
                            thresholds = regime.get("thresholds", [])
                            for t in thresholds:
                                if t.get("name") == threshold_name:
                                    return t.get("value", default)
                            # Also check direct keys for backwards compatibility
                            return regime.get(threshold_name, default)
                        else:
                            return getattr(regime, threshold_name, default)

                return default

            # Build current_params from JSON config (ADX/DI-based like original regime_engine)
            current_params = RegimeParams(
                adx_period=int(get_param("adx", "period", 14)),
                adx_trending_threshold=float(get_regime_threshold("BULL", "adx_min", 25.0)),
                adx_weak_threshold=float(get_regime_threshold("SIDEWAYS", "adx_max", 20.0)),
                di_diff_threshold=float(get_param("adx", "di_diff_threshold", 5.0)),
                rsi_period=int(get_param("rsi", "period", 14)),
                rsi_strong_bull=float(get_regime_threshold("BULL", "rsi_strong_bull", 55.0)),
                rsi_strong_bear=float(get_regime_threshold("BEAR", "rsi_strong_bear", 45.0)),
                atr_period=int(get_param("atr", "period", 14)),
                strong_move_pct=float(get_param("atr", "strong_move_pct", 1.5)),
                extreme_move_pct=float(get_param("atr", "extreme_move_pct", 3.0)),
            )

            # Create param_ranges with SAME VALUES (for optimizer - single-value ranges)
            param_ranges = AllParamRanges(
                adx=ADXParamRanges(
                    period=ParamRange(
                        min=current_params.adx_period,
                        max=current_params.adx_period,
                        step=1
                    ),
                    trending_threshold=ParamRange(
                        min=current_params.adx_trending_threshold,
                        max=current_params.adx_trending_threshold,
                        step=1
                    ),
                    weak_threshold=ParamRange(
                        min=current_params.adx_weak_threshold,
                        max=current_params.adx_weak_threshold,
                        step=1
                    ),
                    di_diff_threshold=ParamRange(
                        min=current_params.di_diff_threshold,
                        max=current_params.di_diff_threshold,
                        step=1
                    ),
                ),
                rsi=RSIParamRanges(
                    period=ParamRange(
                        min=current_params.rsi_period,
                        max=current_params.rsi_period,
                        step=1
                    ),
                    strong_bull=ParamRange(
                        min=current_params.rsi_strong_bull,
                        max=current_params.rsi_strong_bull,
                        step=1
                    ),
                    strong_bear=ParamRange(
                        min=current_params.rsi_strong_bear,
                        max=current_params.rsi_strong_bear,
                        step=1
                    ),
                ),
                atr=ATRParamRanges(
                    period=ParamRange(
                        min=current_params.atr_period,
                        max=current_params.atr_period,
                        step=1
                    ),
                    strong_move_pct=ParamRange(
                        min=current_params.strong_move_pct,
                        max=current_params.strong_move_pct,
                        step=0.1
                    ),
                    extreme_move_pct=ParamRange(
                        min=current_params.extreme_move_pct,
                        max=current_params.extreme_move_pct,
                        step=0.5
                    ),
                ),
            )

            logger.info(
                f"Calculating score with params from JSON: "
                f"adx={current_params.adx_period}/{current_params.adx_trending_threshold}/{current_params.adx_weak_threshold}, "
                f"di_diff={current_params.di_diff_threshold}, "
                f"rsi={current_params.rsi_period}"
            )

            # Get JSON config for per-regime threshold evaluation
            json_config_dict = None
            if isinstance(config, dict):
                json_config_dict = config
            elif hasattr(config, "model_dump"):
                json_config_dict = config.model_dump()
            elif hasattr(config, "dict"):
                json_config_dict = config.dict()

            # Create optimizer to classify regimes (we need the regimes Series)
            optimizer = RegimeOptimizer(
                data=df,
                param_ranges=param_ranges,
                json_config=json_config_dict
            )

            # Calculate indicators and classify regimes
            # Use JSON mode if config has optimization_results with regimes
            if json_config_dict and "optimization_results" in json_config_dict:
                logger.info("Using JSON-based regime classification for current score")
                indicators = optimizer._calculate_json_indicators(current_params)
                regimes = optimizer._classify_regimes_json(current_params, indicators)
            else:
                logger.info("Using legacy regime classification for current score")
                indicators = optimizer._calculate_indicators(current_params)
                regimes = optimizer._classify_regimes(current_params, indicators)

            # Convert regimes to Series for new scoring
            regimes_series = pd.Series(regimes, index=df.index)

            # Use new 5-component RegimeScore
            from src.core.scoring import calculate_regime_score, RegimeScoreConfig

            data_len = len(df)
            score_config = RegimeScoreConfig(
                warmup_bars=min(200, max(50, data_len // 10)),
                max_feature_lookback=max(
                    current_params.adx_period,
                    current_params.rsi_period,
                    current_params.atr_period,
                ),
                # Relaxed gates for scalping/high-frequency data
                min_segments=max(3, data_len // 200),
                min_avg_duration=2,
                max_switch_rate_per_1000=500,  # High switch rates are normal for scalping
                min_unique_labels=2,
                min_bars_for_scoring=max(30, data_len // 10),
            )
            score_result = calculate_regime_score(
                data=df,
                regimes=regimes_series,
                config=score_config,
            )

            score = score_result.total_score

            # Update main score label
            self._regime_opt_current_score_label.setText(f"{score:.1f}")

            # Color based on score and gate status
            if not score_result.gates_passed:
                color = "#ef4444"  # Red for gate failure
            elif score >= 75:
                color = "#22c55e"  # Green for good
            elif score >= 50:
                color = "#f59e0b"  # Orange for medium
            else:
                color = "#ef4444"  # Red for poor

            self._regime_opt_current_score_label.setStyleSheet(
                f"font-weight: bold; font-size: 12pt; color: {color};"
            )

            # Update components label with status
            if score_result.gates_passed:
                self._regime_opt_components_label.setText("✓ Valid")
                self._regime_opt_components_label.setStyleSheet("color: #22c55e; font-size: 9pt;")
            else:
                # Show gate failure reason
                failures = ", ".join(score_result.gate_failures[:2])
                self._regime_opt_components_label.setText(f"⚠️ {failures}")
                self._regime_opt_components_label.setStyleSheet("color: #ef4444; font-size: 9pt;")

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

            # Get row index and retrieve original index from UserRole
            row = selected_rows[0].row()
            rank_item = self._regime_opt_top5_table.item(row, 0)  # Rank column stores original index

            if rank_item is None:
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Could not retrieve selection data."
                )
                return

            # Get original index from UserRole (stored during table population)
            original_index = rank_item.data(Qt.ItemDataRole.UserRole)
            if original_index is None:
                # Fallback to row index if UserRole not set (backwards compatibility)
                original_index = row

            if original_index >= len(self._regime_opt_all_results):
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Selected row is out of range."
                )
                return

            selected_result = self._regime_opt_all_results[original_index]
            params = selected_result.get("params", {})
            score = selected_result.get("score", 0)
            metrics = selected_result.get("metrics", {})
            trial_number = selected_result.get("trial_number", original_index + 1)
            rank = row + 1  # Visual rank for display

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
                "rank": rank,
                "params": converted_params,
                "metrics": metrics,
                "trial_number": trial_number,
                "optimization_config": {
                    "mode": "QUICK",
                    "max_trials": getattr(self, "_regime_opt_max_trials", None).value() if hasattr(self, "_regime_opt_max_trials") else 150,
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
                f"Rank: #{rank}\n"
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

        Builds pure v2.0 format from scratch (no v1.0 base config).

        Workflow:
        1. Build v2.0 config from optimization result
        2. Build indicators[] from flattened params
        3. Build regimes[] from regime threshold params
        4. Save to new file using RegimeConfigLoaderV2
        5. Clear both tables
        6. Load new config in Regime tab
        """
        from PyQt6.QtWidgets import QMessageBox
        from datetime import datetime
        from src.core.tradingbot.config.regime_loader_v2 import RegimeConfigLoaderV2

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

            # Get row index and retrieve original index from UserRole
            row = selected_rows[0].row()
            rank_item = self._regime_opt_top5_table.item(row, 0)  # Rank column stores original index

            if rank_item is None:
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Could not retrieve selection data."
                )
                return

            # Get original index from UserRole (stored during table population)
            original_index = rank_item.data(Qt.ItemDataRole.UserRole)
            if original_index is None:
                # Fallback to row index if UserRole not set (backwards compatibility)
                original_index = row

            if original_index >= len(self._regime_opt_all_results):
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Selected row is out of range."
                )
                return

            selected_result = self._regime_opt_all_results[original_index]
            params = selected_result.get("params", {})
            score = selected_result.get("score", 0)
            rank = row + 1  # Display rank (visual position in table)

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
                f"4. Load config in Regime tab",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Step 1: Build indicators[] from flattened params
            indicators = self._build_indicators_from_params(params)

            # Step 2: Build regimes[] from regime threshold params
            regimes = self._build_regimes_from_params(params)

            # Step 3: Build v2.0 config structure
            trial_number = selected_result.get("trial_number", rank)
            metrics = selected_result.get("metrics", {})
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            config_data = {
                "schema_version": "2.0.0",
                "metadata": {
                    "author": "OrderPilot-AI",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "tags": [symbol, timeframe, "regime", "optimization"],
                    "notes": (
                        f"Rank #{rank} optimization result applied on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC. "
                        f"Score: {score:.2f}. Trial: {trial_number}"
                    ),
                    "trading_style": "Daytrading",  # Default, can be customized
                    "description": f"Optimized regime configuration for {symbol} {timeframe} with {len(indicators)} indicators and {len(regimes)} regimes."
                },
                "optimization_results": [
                    {
                        "timestamp": timestamp,
                        "score": float(score),
                        "trial_number": trial_number,
                        "applied": True,
                        "indicators": indicators,
                        "regimes": regimes
                    }
                ]
                # NOTE: entry_params and evaluation_params are NOT included -
                #       Only entry_expression is used for Trading Bot execution.
            }

            # Step 4: Save to new file with validation
            project_root = Path(__file__).parent.parent.parent.parent.parent
            export_dir = project_root / "03_JSON" / "Entry_Analyzer" / "Regime"
            export_dir.mkdir(parents=True, exist_ok=True)

            timestamp_str = datetime.utcnow().strftime("%y%m%d%H%M%S")
            export_filename = f"{timestamp_str}_regime_optimization_results_{symbol}_{timeframe}_#{rank}.json"
            export_path = export_dir / export_filename

            logger.info(f"Saving v2.0 config to: {export_path}")

            # Use RegimeConfigLoaderV2 for validation and save
            loader = RegimeConfigLoaderV2()
            loader.save_config(config_data, export_path, indent=2, validate=True)

            logger.info(f"Successfully saved v2.0 regime config (Rank #{rank}) to: {export_path}")

            # Step 5: Clear detected regimes table (will be repopulated with new config)
            # NOTE: Keep optimization results table - results are valuable for reference
            if hasattr(self, "_detected_regimes_table"):
                self._detected_regimes_table.setRowCount(0)
                logger.info("Cleared Detected Regimes table (will repopulate with new config)")

            # Step 6: Load new file in Regime tab
            if hasattr(self, "_load_regime_config"):
                self._load_regime_config(export_path, show_error=True)
                logger.info(f"Loaded config in Regime tab: {export_path}")

            QMessageBox.information(
                self,
                "Success",
                f"Successfully saved and loaded v2.0 regime config!\n\n"
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
            params: Flat dict like {"adx_period": 14, "adx_trending_threshold": 25, ...}

        Returns:
            Nested dict like {"adx.period": 14, "BULL.adx_min": 25, ...}
        """
        converted = {}

        # Known mappings from ADX/DI-based flat format to v2.0 format
        param_mappings = {
            # ADX indicator parameters
            "adx_period": "adx.period",
            "di_diff_threshold": "adx.di_diff_threshold",
            # Regime thresholds
            "adx_trending_threshold": "BULL.adx_min",  # Trending threshold for BULL/BEAR
            "adx_weak_threshold": "SIDEWAYS.adx_max",  # Weak threshold for SIDEWAYS
            # RSI parameters
            "rsi_period": "rsi.period",
            "rsi_strong_bull": "BULL.rsi_strong_bull",
            "rsi_strong_bear": "BEAR.rsi_strong_bear",
            # ATR parameters
            "atr_period": "atr.period",
            "strong_move_pct": "atr.strong_move_pct",
            "extreme_move_pct": "atr.extreme_move_pct",
        }

        for old_key, new_key in param_mappings.items():
            if old_key in params:
                converted[new_key] = params[old_key]

                # Special handling for shared thresholds
                if old_key == "adx_trending_threshold":
                    # Trending threshold is used by both BULL and BEAR
                    converted["BEAR.adx_min"] = params[old_key]

                elif old_key == "di_diff_threshold":
                    # DI difference used by both BULL and BEAR
                    converted["BULL.di_diff_min"] = params[old_key]
                    converted["BEAR.di_diff_min"] = params[old_key]

                elif old_key == "extreme_move_pct":
                    # Extreme move threshold shared
                    converted["BULL.extreme_move_pct"] = params[old_key]
                    converted["BEAR.extreme_move_pct"] = params[old_key]

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
                    if left.get("indicator_id") == "adx" and cond.get("op") in ["gt", "lt"]:
                        cond["right"]["value"] = int(threshold_value)

        elif threshold_name == "rsi_low":
            # Update RSI lower bound (SIDEWAYS regime)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "between":
                        cond["right"]["min"] = int(threshold_value)

        elif threshold_name == "rsi_high":
            # Update RSI upper bound (SIDEWAYS regime)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "between":
                        cond["right"]["max"] = int(threshold_value)

        elif threshold_name == "rsi_overbought":
            # Update RSI overbought threshold (SIDEWAYS_OVERBOUGHT)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "gt":
                        cond["right"]["value"] = int(threshold_value)

        elif threshold_name == "rsi_oversold":
            # Update RSI oversold threshold (SIDEWAYS_OVERSOLD)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "lt":
                        cond["right"]["value"] = int(threshold_value)

    def _build_indicators_from_params(self, params: dict) -> list[dict]:
        """Build v2.0 indicators[] structure from flattened params.

        Uses the original JSON indicators (if loaded) and updates param values
        with optimized params. This preserves all indicator types (including
        custom ones like CHANDELIER, ADX_LEAF_WEST, etc.).

        Param formats supported:
        - Flat: "adx_period", "rsi_period"
        - JSON dot-notation: "MOMENTUM_RSI.period", "STRENGTH_ADX.trending_threshold"

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of indicator dicts in v2.0 format
        """
        import copy

        # Try to get original indicators from loaded JSON config
        original_indicators = None
        if hasattr(self, "_regime_config") and self._regime_config:
            try:
                # Get indicators from optimization_results[0].indicators
                if hasattr(self._regime_config, "optimization_results"):
                    opt_results = self._regime_config.optimization_results
                    if opt_results and len(opt_results) > 0:
                        if hasattr(opt_results[0], "indicators"):
                            original_indicators = opt_results[0].indicators
                        elif isinstance(opt_results[0], dict):
                            original_indicators = opt_results[0].get("indicators", [])
                elif isinstance(self._regime_config, dict):
                    opt_results = self._regime_config.get("optimization_results", [])
                    if opt_results and len(opt_results) > 0:
                        original_indicators = opt_results[0].get("indicators", [])
            except Exception as e:
                logger.warning(f"Could not extract indicators from config: {e}")

        if original_indicators:
            # Use original indicators and update param values from params
            indicators = []
            for ind_data in original_indicators:
                # Deep copy to avoid modifying original
                if hasattr(ind_data, "model_dump"):
                    indicator = ind_data.model_dump()
                elif hasattr(ind_data, "dict"):
                    indicator = ind_data.dict()
                else:
                    indicator = copy.deepcopy(ind_data) if isinstance(ind_data, dict) else {}

                ind_name = indicator.get("name", "")
                ind_type = indicator.get("type", "")

                # Update params with optimized values
                if "params" in indicator and isinstance(indicator["params"], list):
                    for param in indicator["params"]:
                        if not isinstance(param, dict):
                            continue
                        param_name = param.get("name", "")

                        # Try JSON dot-notation first: "INDICATOR_NAME.param_name"
                        json_key = f"{ind_name}.{param_name}"
                        if json_key in params:
                            param["value"] = self._format_param_value(params[json_key])
                            continue

                        # Try flat format mapping
                        flat_value = self._get_flat_param_for_indicator(
                            params, ind_name, ind_type, param_name
                        )
                        if flat_value is not None:
                            param["value"] = self._format_param_value(flat_value)

                indicators.append(indicator)

            logger.info(
                f"Built {len(indicators)} indicators from original JSON config: "
                f"{[i.get('name', '?') for i in indicators]}"
            )
            return indicators

        # Fallback: Build default indicator structure if no JSON loaded
        logger.warning("No JSON indicators found, building default indicator structure")
        return self._build_default_indicators_from_params(params)

    def _format_param_value(self, value: float | int) -> int | float:
        """Format parameter value (int if whole number, else float)."""
        if isinstance(value, float) and value == int(value):
            return int(value)
        if isinstance(value, float):
            return round(value, 2)
        return value

    def _get_flat_param_for_indicator(
        self, params: dict, ind_name: str, ind_type: str, param_name: str
    ) -> float | None:
        """Map flat optimizer params to indicator param names.

        Args:
            params: Flat params dict
            ind_name: Indicator name (e.g., "STRENGTH_ADX")
            ind_type: Indicator type (e.g., "ADX")
            param_name: Parameter name (e.g., "period")

        Returns:
            Parameter value or None if not found
        """
        # Build possible flat key names based on indicator type
        type_lower = ind_type.lower() if ind_type else ""

        # Direct mappings
        flat_keys = [
            f"{type_lower}_{param_name}",  # e.g., "adx_period"
            param_name,  # Direct match
        ]

        for key in flat_keys:
            if key in params:
                return params[key]

        return None

    def _build_default_indicators_from_params(self, params: dict) -> list[dict]:
        """Build default indicator structure when no JSON is loaded.

        Fallback method for backwards compatibility.

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of indicator dicts in v2.0 format
        """
        indicators_map = {}

        indicator_info = {
            "adx": {"name": "STRENGTH_ADX", "type": "ADX"},
            "rsi": {"name": "MOMENTUM_RSI", "type": "RSI"},
            "atr": {"name": "VOLATILITY_ATR", "type": "ATR"},
        }

        param_mapping = {
            "adx_period": ("adx", "period"),
            "adx_trending_threshold": ("adx", "trending_threshold"),
            "adx_weak_threshold": ("adx", "weak_threshold"),
            "di_diff_threshold": ("adx", "di_diff_threshold"),
            "rsi_period": ("rsi", "period"),
            "rsi_strong_bull": ("rsi", "strong_bull"),
            "rsi_strong_bear": ("rsi", "strong_bear"),
            "atr_period": ("atr", "period"),
            "strong_move_pct": ("atr", "strong_move_pct"),
            "extreme_move_pct": ("atr", "extreme_move_pct"),
        }

        param_ranges = {
            "period": {"min": 5, "max": 50, "step": 1},
            "trending_threshold": {"min": 20, "max": 40, "step": 1},
            "weak_threshold": {"min": 15, "max": 25, "step": 1},
            "di_diff_threshold": {"min": 3, "max": 15, "step": 1},
            "strong_bull": {"min": 50, "max": 70, "step": 1},
            "strong_bear": {"min": 30, "max": 50, "step": 1},
            "strong_move_pct": {"min": 0.5, "max": 3.0, "step": 0.1},
            "extreme_move_pct": {"min": 2.0, "max": 5.0, "step": 0.5},
        }

        for param_key, param_value in params.items():
            if param_key in param_mapping:
                indicator_id, param_name = param_mapping[param_key]
            elif "." in param_key:
                parts = param_key.split(".", 1)
                if len(parts) != 2:
                    continue
                indicator_id, param_name = parts
                if indicator_id.isupper():
                    continue
            else:
                continue

            if indicator_id not in indicator_info:
                continue

            info = indicator_info[indicator_id]

            if indicator_id not in indicators_map:
                indicators_map[indicator_id] = {
                    "name": info["name"],
                    "type": info["type"],
                    "params": []
                }

            param_entry = {
                "name": param_name,
                "value": self._format_param_value(param_value)
            }

            if param_name in param_ranges:
                param_entry["range"] = param_ranges[param_name]

            indicators_map[indicator_id]["params"].append(param_entry)

        indicators = list(indicators_map.values())
        indicators.sort(key=lambda x: x["name"])

        logger.info(f"Built {len(indicators)} default indicators: {[i['name'] for i in indicators]}")
        return indicators

    def _build_regimes_from_params(self, params: dict) -> list[dict]:
        """Build v2.0 regimes[] structure from optimization params.

        Uses the original JSON regimes (if loaded) and updates threshold values
        with optimized params. This preserves all regime IDs (including custom
        ones like STRONG_BULL, STRONG_BEAR, STRONG_SIDEWAYS).

        Param formats supported:
        - Flat: "adx_trending_threshold", "di_diff_threshold"
        - JSON dot-notation: "STRONG_BULL.adx_min", "BEAR.di_diff_min"

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of regime dicts in v2.0 format
        """
        import copy

        # Try to get original regimes from loaded JSON config
        original_regimes = None
        if hasattr(self, "_regime_config") and self._regime_config:
            try:
                # Get regimes from optimization_results[0].regimes
                if hasattr(self._regime_config, "optimization_results"):
                    opt_results = self._regime_config.optimization_results
                    if opt_results and len(opt_results) > 0:
                        if hasattr(opt_results[0], "regimes"):
                            original_regimes = opt_results[0].regimes
                        elif isinstance(opt_results[0], dict):
                            original_regimes = opt_results[0].get("regimes", [])
                elif isinstance(self._regime_config, dict):
                    opt_results = self._regime_config.get("optimization_results", [])
                    if opt_results and len(opt_results) > 0:
                        original_regimes = opt_results[0].get("regimes", [])
            except Exception as e:
                logger.warning(f"Could not extract regimes from config: {e}")

        if original_regimes:
            # Use original regimes and update threshold values from params
            regimes = []
            for regime_data in original_regimes:
                # Deep copy to avoid modifying original
                if hasattr(regime_data, "model_dump"):
                    regime = regime_data.model_dump()
                elif hasattr(regime_data, "dict"):
                    regime = regime_data.dict()
                else:
                    regime = copy.deepcopy(regime_data) if isinstance(regime_data, dict) else {"id": str(regime_data)}

                regime_id = regime.get("id", "").upper()

                # Update thresholds with optimized values
                if "thresholds" in regime and isinstance(regime["thresholds"], list):
                    for thresh in regime["thresholds"]:
                        if not isinstance(thresh, dict):
                            continue
                        thresh_name = thresh.get("name", "")

                        # Try JSON dot-notation first: "REGIME_ID.threshold_name"
                        json_key = f"{regime_id}.{thresh_name}"
                        if json_key in params:
                            thresh["value"] = self._round_value(params[json_key])
                            continue

                        # Try flat format mapping
                        flat_value = self._get_flat_param_for_threshold(
                            params, regime_id, thresh_name
                        )
                        if flat_value is not None:
                            thresh["value"] = self._round_value(flat_value)

                regimes.append(regime)

            logger.info(
                f"Built {len(regimes)} regimes from original JSON config with updated thresholds"
            )
            return regimes

        # Fallback: Build default 3-regime structure if no JSON loaded
        logger.warning("No JSON regimes found, building default 3-regime structure")
        return self._build_default_regimes_from_params(params)

    def _round_value(self, value: float | int) -> float:
        """Round value appropriately based on magnitude."""
        if isinstance(value, int):
            return float(value)
        if abs(value) >= 10:
            return round(value, 1)
        return round(value, 2)

    def _get_flat_param_for_threshold(
        self, params: dict, regime_id: str, thresh_name: str
    ) -> float | None:
        """Map flat optimizer params to regime threshold names.

        Args:
            params: Flat params dict
            regime_id: Regime ID (e.g., "BULL", "STRONG_BULL")
            thresh_name: Threshold name (e.g., "adx_min", "di_diff_min")

        Returns:
            Parameter value or None if not found
        """
        # Direct mappings from optimizer params to threshold names
        mapping = {
            "adx_min": "adx_trending_threshold",
            "adx_max": "adx_weak_threshold",
            "di_diff_min": "di_diff_threshold",
            "rsi_strong_bull": "rsi_strong_bull",
            "rsi_strong_bear": "rsi_strong_bear",
            "strong_move_pct": "strong_move_pct",
            "extreme_move_pct": "extreme_move_pct",
        }

        if thresh_name in mapping:
            flat_key = mapping[thresh_name]
            if flat_key in params:
                return params[flat_key]

        return None

    def _build_default_regimes_from_params(self, params: dict) -> list[dict]:
        """Build default 3-regime structure when no JSON is loaded.

        Fallback method for backwards compatibility.

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of 3 regime dicts (BULL, BEAR, SIDEWAYS)
        """
        adx_trending = params.get("adx_trending_threshold", 25)
        adx_weak = params.get("adx_weak_threshold", 20)
        di_diff = params.get("di_diff_threshold", 5)
        rsi_strong_bull = params.get("rsi_strong_bull", 55)
        rsi_strong_bear = params.get("rsi_strong_bear", 45)
        extreme_move_pct = params.get("extreme_move_pct", 3.0)

        threshold_ranges = {
            "adx_min": {"min": 15, "max": 40, "step": 1},
            "adx_max": {"min": 15, "max": 30, "step": 1},
            "di_diff_min": {"min": 3, "max": 15, "step": 1},
            "rsi_strong_bull": {"min": 50, "max": 70, "step": 1},
            "rsi_strong_bear": {"min": 30, "max": 50, "step": 1},
            "extreme_move_pct": {"min": 2.0, "max": 5.0, "step": 0.5},
        }

        regimes = [
            {
                "id": "BULL",
                "name": "Bullischer Trend",
                "thresholds": [
                    {"name": "adx_min", "value": round(adx_trending, 1), "range": threshold_ranges["adx_min"]},
                    {"name": "di_diff_min", "value": round(di_diff, 1), "range": threshold_ranges["di_diff_min"]},
                    {"name": "rsi_strong_bull", "value": round(rsi_strong_bull, 1), "range": threshold_ranges["rsi_strong_bull"]},
                    {"name": "extreme_move_pct", "value": round(extreme_move_pct, 2), "range": threshold_ranges["extreme_move_pct"]},
                ],
                "priority": 90,
                "scope": "entry"
            },
            {
                "id": "BEAR",
                "name": "Bärischer Trend",
                "thresholds": [
                    {"name": "adx_min", "value": round(adx_trending, 1), "range": threshold_ranges["adx_min"]},
                    {"name": "di_diff_min", "value": round(di_diff, 1), "range": threshold_ranges["di_diff_min"]},
                    {"name": "rsi_strong_bear", "value": round(rsi_strong_bear, 1), "range": threshold_ranges["rsi_strong_bear"]},
                    {"name": "extreme_move_pct", "value": round(extreme_move_pct, 2), "range": threshold_ranges["extreme_move_pct"]},
                ],
                "priority": 85,
                "scope": "entry"
            },
            {
                "id": "SIDEWAYS",
                "name": "Seitwärts / Range",
                "thresholds": [
                    {"name": "adx_max", "value": round(adx_weak, 1), "range": threshold_ranges["adx_max"]},
                ],
                "priority": 50,
                "scope": "entry"
            },
        ]

        logger.info(
            f"Built default 3 regimes: adx_trending={adx_trending:.1f}, "
            f"adx_weak={adx_weak:.1f}, di_diff={di_diff:.1f}"
        )
        return regimes

    @pyqtSlot()
    def _on_regime_score_help_clicked(self) -> None:
        """Open RegimeScore help file in browser."""
        help_path = Path(__file__).parent.parent.parent.parent.parent / "help" / "regime_score_help.html"
        if help_path.exists():
            webbrowser.open(help_path.as_uri())
            logger.info(f"Opened help file: {help_path}")
        else:
            QMessageBox.warning(
                self,
                "Help Not Found",
                f"Help file not found at:\n{help_path}\n\n"
                "Please ensure the help file exists.",
            )

    @pyqtSlot()
    def _on_regime_opt_draw_selected(self) -> None:
        """Draw selected optimization result's regime periods on chart.

        Clears all existing regime lines first, then draws the new ones.
        """
        # Get selected row from table
        selected_rows = self._regime_opt_top5_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a result row from the table first."
            )
            return

        # Get row index and retrieve original index from UserRole
        row = selected_rows[0].row()
        rank_item = self._regime_opt_top5_table.item(row, 0)

        if rank_item is None:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Could not retrieve selection data."
            )
            return

        # Get original index from UserRole
        original_index = rank_item.data(Qt.ItemDataRole.UserRole)
        if original_index is None:
            original_index = row

        if original_index >= len(self._regime_opt_all_results):
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Selected row is out of range."
            )
            return

        selected_result = self._regime_opt_all_results[original_index]
        regime_history = selected_result.get("regime_history", [])

        if not regime_history:
            QMessageBox.warning(
                self,
                "No Regime Data",
                "Selected result has no regime history to draw.\n\n"
                "The optimization may not have saved regime periods."
            )
            return

        # Emit signal to draw regime lines on chart (clears existing lines automatically)
        if hasattr(self, "draw_regime_lines_requested"):
            self.draw_regime_lines_requested.emit(regime_history)
            rank = row + 1
            score = selected_result.get("score", 0)
            logger.info(f"Drawing {len(regime_history)} regime periods from Rank #{rank} (score: {score:.1f})")

            QMessageBox.information(
                self,
                "Regime Lines Drawn",
                f"Drew {len(regime_history)} regime periods on chart.\n\n"
                f"Rank: #{rank}\n"
                f"Score: {score:.1f}"
            )
        else:
            QMessageBox.warning(
                self,
                "Signal Not Connected",
                "Chart drawing signal is not connected.\n"
                "Cannot draw regime lines."
            )
