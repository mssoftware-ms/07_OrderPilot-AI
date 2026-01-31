"""Regime Optimization - Event Handlers Mixin.

Handles optimization lifecycle events and signal processing.

Agent: CODER-013
Task: 3.1.3 - Split regime_optimization_mixin
File: 2/5 - Events (375 LOC target)
"""

from __future__ import annotations

import logging
import webbrowser
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.ui.threads.regime_optimization_thread import RegimeOptimizationThread

logger = logging.getLogger(__name__)


class RegimeOptimizationEventsMixin:
    """Event handlers for optimization lifecycle.

    Handles:
        - Start/stop optimization
        - Progress updates with ETA
        - Completion handling
        - Error handling
        - Tab navigation
        - Help system
    """

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
                    param_grid[param_name] = list(np.linspace(min_val, max_val, num=10))
                else:
                    # Integer parameter: Use range
                    param_grid[param_name] = list(range(min_val, max_val + 1))

        # Get config template path
        # Use default regime config from project
        # Path: src/ui/dialogs/entry_analyzer/this_file.py -> 5x parent = project root
        config_template_path = str(
            Path(__file__).parent.parent.parent.parent.parent.parent
            / "config"
            / "regime_config_default.json"
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
                logger.warning("Could not convert _regime_config to dict, using legacy mode")

            if json_config:
                logger.info("Using JSON-based regime evaluation with per-regime thresholds")

        # Create and start optimization thread
        self._regime_opt_thread = RegimeOptimizationThread(
            df=df,
            config_template_path=config_template_path,
            param_grid=param_grid,
            scope="entry",
            max_trials=max_trials_value,
            json_config=json_config,
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
            if (
                hasattr(self, "_waiting_dialog")
                and self._waiting_dialog
                and self._waiting_dialog.isVisible()
            ):
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
        if (
            hasattr(self, "_waiting_dialog")
            and self._waiting_dialog
            and self._waiting_dialog.isVisible()
        ):
            self._waiting_dialog.set_status(
                f"Trial {current}/{total} ({progress_pct}%) - ETA: {eta_text}"
            )

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
                best_score = results[0].get("score", 0)

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
            QMessageBox.critical(
                self,
                "Optimization Error",
                f"Failed to process optimization results:\n{str(e)}\n\nCheck logs for details.",
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
    def _on_regime_score_help_clicked(self) -> None:
        """Open RegimeScore help file in browser."""
        help_path = (
            Path(__file__).parent.parent.parent.parent.parent.parent
            / "help"
            / "regime_score_help.html"
        )
        if help_path.exists():
            webbrowser.open(help_path.as_uri())
            logger.info(f"Opened help file: {help_path}")
        else:
            QMessageBox.warning(
                self,
                "Help Not Found",
                f"Help file not found at:\n{help_path}\n\n" "Please ensure the help file exists.",
            )
