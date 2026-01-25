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
        self._regime_opt_current_score_label.setToolTip(
            "RegimeScore (0-100) with 5 components:\n"
            "• Sep: Separability (30%)\n"
            "• Coh: Coherence (25%)\n"
            "• Fid: Fidelity (25%)\n"
            "• Bnd: Boundary (10%)\n"
            "• Cov: Coverage (10%)"
        )
        current_score_layout.addWidget(self._regime_opt_current_score_label)
        
        # Component details label (compact)
        self._regime_opt_components_label = QLabel("")
        self._regime_opt_components_label.setStyleSheet("color: #888; font-size: 9pt;")
        current_score_layout.addWidget(self._regime_opt_components_label)
        
        current_score_layout.addStretch()

        refresh_score_btn = QPushButton(get_icon("refresh"), "Calculate Current Score")
        refresh_score_btn.setToolTip("Calculate 5-component RegimeScore for currently active regime parameters")
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

        # Score component columns (5-component RegimeScore)
        score_components = ["Sep", "Coh", "Fid", "Bnd", "Cov"]

        # Build column headers: Rank, Total Score, Sep, Coh, Fid, Bnd, Cov, [Dynamic Params], Trial #
        headers = ["Rank", "Total"] + score_components + param_names + ["Trial #"]

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

            # Score Components (5 columns): Sep, Coh, Fid, Bnd, Cov
            component_keys = ["separability", "coherence", "fidelity", "boundary", "coverage_score"]
            for comp_key in component_keys:
                comp_value = metrics.get(comp_key, 0.0) if isinstance(metrics, dict) else 0.0
                # Convert 0-1 to 0-100 for display
                comp_pct = comp_value * 100
                comp_item = QTableWidgetItem(f"{comp_pct:.0f}")
                comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                comp_item.setToolTip(f"{comp_key}: {comp_value:.3f}")
                self._regime_opt_top5_table.setItem(row, col, comp_item)
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

            # Build current_params from JSON config
            current_params = RegimeParams(
                adx_period=int(get_param("adx", "period", 14)),
                adx_threshold=float(get_regime_threshold("BULL", "adx_threshold", 25.0)),
                sma_fast_period=int(get_param("sma_fast", "period", 50)),
                sma_slow_period=int(get_param("sma_slow", "period", 200)),
                rsi_period=int(get_param("rsi", "period", 14)),
                rsi_sideways_low=float(get_regime_threshold("SIDEWAYS", "rsi_low", 40)),
                rsi_sideways_high=float(get_regime_threshold("SIDEWAYS", "rsi_high", 60)),
                bb_period=int(get_param("bb", "period", 20)),
                bb_std_dev=float(get_param("bb", "std_dev", 2.0)),
                bb_width_percentile=float(get_param("bb", "width_percentile", 30.0)),
            )

            # Create param_ranges with SAME VALUES (for optimizer - single-value ranges)
            param_ranges = AllParamRanges(
                adx=ADXParamRanges(
                    period=ParamRange(
                        min=current_params.adx_period,
                        max=current_params.adx_period,
                        step=1
                    ),
                    threshold=ParamRange(
                        min=current_params.adx_threshold,
                        max=current_params.adx_threshold,
                        step=1
                    ),
                ),
                sma_fast=SMAParamRanges(
                    period=ParamRange(
                        min=current_params.sma_fast_period,
                        max=current_params.sma_fast_period,
                        step=1
                    )
                ),
                sma_slow=SMAParamRanges(
                    period=ParamRange(
                        min=current_params.sma_slow_period,
                        max=current_params.sma_slow_period,
                        step=1
                    )
                ),
                rsi=RSIParamRanges(
                    period=ParamRange(
                        min=current_params.rsi_period,
                        max=current_params.rsi_period,
                        step=1
                    ),
                    sideways_low=ParamRange(
                        min=current_params.rsi_sideways_low,
                        max=current_params.rsi_sideways_low,
                        step=1
                    ),
                    sideways_high=ParamRange(
                        min=current_params.rsi_sideways_high,
                        max=current_params.rsi_sideways_high,
                        step=1
                    ),
                ),
                bb=BBParamRanges(
                    period=ParamRange(
                        min=current_params.bb_period,
                        max=current_params.bb_period,
                        step=1
                    ),
                    std_dev=ParamRange(
                        min=current_params.bb_std_dev,
                        max=current_params.bb_std_dev,
                        step=0.1
                    ),
                    width_percentile=ParamRange(
                        min=current_params.bb_width_percentile,
                        max=current_params.bb_width_percentile,
                        step=1
                    ),
                ),
            )

            logger.info(
                f"Calculating score with params from JSON: "
                f"adx={current_params.adx_period}/{current_params.adx_threshold}, "
                f"rsi={current_params.rsi_period}, "
                f"bb={current_params.bb_period}/{current_params.bb_std_dev}"
            )

            # Create optimizer to classify regimes (we need the regimes Series)
            optimizer = RegimeOptimizer(
                data=df,
                param_ranges=param_ranges,
            )

            # Calculate indicators and classify regimes
            indicators = optimizer._calculate_indicators(current_params)
            regimes = optimizer._classify_regimes(current_params, indicators)
            
            # Convert regimes to Series for new scoring
            regimes_series = pd.Series(regimes, index=df.index)
            
            # Use new 5-component RegimeScore
            from src.core.scoring import calculate_regime_score, RegimeScoreConfig
            
            score_config = RegimeScoreConfig(
                warmup_bars=200,
                max_feature_lookback=max(
                    current_params.adx_period,
                    current_params.sma_slow_period,
                    current_params.rsi_period,
                    current_params.bb_period,
                ),
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
            
            # Update components label with breakdown
            sep = score_result.separability.normalized * 100
            coh = score_result.coherence.normalized * 100
            fid = score_result.fidelity.normalized * 100
            bnd = score_result.boundary.normalized * 100
            cov = score_result.coverage.normalized * 100
            
            if score_result.gates_passed:
                self._regime_opt_components_label.setText(
                    f"[Sep:{sep:.0f} Coh:{coh:.0f} Fid:{fid:.0f} Bnd:{bnd:.0f} Cov:{cov:.0f}]"
                )
            else:
                # Show gate failure reason
                failures = ", ".join(score_result.gate_failures[:2])
                self._regime_opt_components_label.setText(f"⚠️ {failures}")
                self._regime_opt_components_label.setStyleSheet("color: #ef4444; font-size: 9pt;")

            logger.info(
                f"Current regime score: {score:.2f} "
                f"(Sep:{sep:.1f} Coh:{coh:.1f} Fid:{fid:.1f} Bnd:{bnd:.1f} Cov:{cov:.1f})"
            )

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
                ],
                "entry_params": {
                    "min_score": 70,
                    "require_regime_match": True,
                    "max_signals_per_regime": 5
                },
                "evaluation_params": {
                    "lookback_periods": 200,
                    "min_regime_duration": 3,
                    "score_weights": {
                        "regime_distribution": 0.3,
                        "regime_stability": 0.3,
                        "indicator_quality": 0.4
                    }
                }
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
            params: Flat dict like {"adx_period": 14, "rsi_period": 12, ...}

        Returns:
            Nested dict like {"adx.period": 14, "rsi.period": 12, ...}
        """
        converted = {}

        # Known mappings from old flat format to new v2.0 format
        param_mappings = {
            "adx_period": "adx.period",
            "adx_threshold": "BULL.adx_threshold",  # Will be duplicated for all regimes
            "rsi_period": "rsi.period",
            "rsi_sideways_low": "SIDEWAYS.rsi_low",
            "rsi_sideways_high": "SIDEWAYS.rsi_high",
            "bb_period": "bb.period",
            "bb_std_dev": "bb.std_dev",
            "bb_width_percentile": "bb.width_percentile",
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

        Converts params like {"adx_period": 14, "rsi_period": 12} to:
        [
            {
                "name": "ADX1",
                "type": "ADX",
                "params": [{"name": "period", "value": 14, "range": {...}}]
            },
            ...
        ]

        Supports both underscore format (adx_period) and dot format (adx.period).

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of indicator dicts in v2.0 format
        """
        indicators_map = {}

        # Known indicator mappings (prefix -> name/type)
        indicator_info = {
            "adx": {"name": "STRENGTH_ADX", "type": "ADX"},
            "rsi": {"name": "MOMENTUM_RSI", "type": "RSI"},
            "bb": {"name": "VOLATILITY_BB", "type": "BB"},
            "sma_fast": {"name": "TREND_FILTER_FAST", "type": "SMA"},
            "sma_slow": {"name": "TREND_FILTER", "type": "SMA"},
        }

        # Mapping from flat param names to (indicator_id, param_name)
        param_mapping = {
            "adx_period": ("adx", "period"),
            "adx_threshold": ("adx", "threshold"),
            "rsi_period": ("rsi", "period"),
            "rsi_sideways_low": ("rsi", "sideways_low"),
            "rsi_sideways_high": ("rsi", "sideways_high"),
            "bb_period": ("bb", "period"),
            "bb_std_dev": ("bb", "std_dev"),
            "bb_width_percentile": ("bb", "width_percentile"),
            "sma_fast_period": ("sma_fast", "period"),
            "sma_slow_period": ("sma_slow", "period"),
        }

        # Default parameter ranges for common indicators
        param_ranges = {
            "period": {"min": 5, "max": 200, "step": 1},
            "threshold": {"min": 15, "max": 40, "step": 1},
            "std_dev": {"min": 1.5, "max": 3.0, "step": 0.1},
            "sideways_low": {"min": 30, "max": 50, "step": 1},
            "sideways_high": {"min": 50, "max": 70, "step": 1},
            "width_percentile": {"min": 10, "max": 50, "step": 5},
        }

        # Parse params and group by indicator
        for param_key, param_value in params.items():
            # Try direct mapping first (underscore format from optimizer)
            if param_key in param_mapping:
                indicator_id, param_name = param_mapping[param_key]
            # Try dot format (legacy)
            elif "." in param_key:
                parts = param_key.split(".", 1)
                if len(parts) != 2:
                    continue
                indicator_id, param_name = parts
                # Skip regime thresholds
                if indicator_id.isupper():
                    continue
            else:
                # Skip unknown params
                continue

            # Get indicator info
            if indicator_id not in indicator_info:
                logger.debug(f"Unknown indicator ID: {indicator_id}, skipping")
                continue

            info = indicator_info[indicator_id]

            # Initialize indicator entry if not exists
            if indicator_id not in indicators_map:
                indicators_map[indicator_id] = {
                    "name": info["name"],
                    "type": info["type"],
                    "params": []
                }

            # Add parameter
            param_entry = {
                "name": param_name,
                "value": int(param_value) if isinstance(param_value, (int, float)) and param_value == int(param_value) else round(float(param_value), 2)
            }

            # Add range if known
            if param_name in param_ranges:
                param_entry["range"] = param_ranges[param_name]

            indicators_map[indicator_id]["params"].append(param_entry)

        # Convert to list and sort by indicator name
        indicators = list(indicators_map.values())
        indicators.sort(key=lambda x: x["name"])

        logger.info(f"Built {len(indicators)} indicators from params: {[i['name'] for i in indicators]}")
        return indicators

    def _build_regimes_from_params(self, params: dict) -> list[dict]:
        """Build v2.0 regimes[] structure from optimization params.

        Converts optimizer params like {"adx_threshold": 25, "rsi_sideways_low": 40}
        to regime definitions with thresholds applied.

        The optimizer uses global thresholds, which we apply to standard regime types:
        - BULL: ADX > threshold, price > SMA
        - BEAR: ADX > threshold, price < SMA
        - SIDEWAYS: ADX < threshold, RSI in sideways range

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of regime dicts in v2.0 format
        """
        # Extract global thresholds from optimizer params
        adx_threshold = params.get("adx_threshold", 25)
        rsi_sideways_low = params.get("rsi_sideways_low", 40)
        rsi_sideways_high = params.get("rsi_sideways_high", 60)

        # Threshold ranges for v2.0 format
        threshold_ranges = {
            "adx_min": {"min": 15, "max": 50, "step": 1},
            "adx_max": {"min": 15, "max": 50, "step": 1},
            "rsi_min": {"min": 30, "max": 70, "step": 1},
            "rsi_max": {"min": 30, "max": 70, "step": 1},
        }

        # Build standard 3 regime types from global thresholds
        regimes = [
            {
                "id": "BULL",
                "name": "Bullischer Trend",
                "thresholds": [
                    {"name": "adx_min", "value": round(adx_threshold, 1), "range": threshold_ranges["adx_min"]},
                ],
                "priority": 90,
                "scope": "entry"
            },
            {
                "id": "BEAR",
                "name": "Bärischer Trend",
                "thresholds": [
                    {"name": "adx_min", "value": round(adx_threshold, 1), "range": threshold_ranges["adx_min"]},
                ],
                "priority": 85,
                "scope": "entry"
            },
            {
                "id": "SIDEWAYS",
                "name": "Seitwärts / Neutral",
                "thresholds": [
                    {"name": "adx_max", "value": round(adx_threshold, 1), "range": threshold_ranges["adx_max"]},
                    {"name": "rsi_min", "value": round(rsi_sideways_low, 1), "range": threshold_ranges["rsi_min"]},
                    {"name": "rsi_max", "value": round(rsi_sideways_high, 1), "range": threshold_ranges["rsi_max"]},
                ],
                "priority": 50,
                "scope": "entry"
            },
        ]

        logger.info(f"Built {len(regimes)} regimes from global thresholds: adx={adx_threshold:.1f}, rsi=[{rsi_sideways_low:.1f}, {rsi_sideways_high:.1f}]")
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
