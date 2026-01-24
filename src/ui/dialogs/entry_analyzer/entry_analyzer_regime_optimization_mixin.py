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

        # Live Top-5 Results Table
        results_label = QLabel("Live Top-5 Results:")
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
        self._regime_opt_top5_table.setMaximumHeight(200)
        layout.addWidget(self._regime_opt_top5_table)

        layout.addStretch()

        # Action Buttons
        action_layout = QHBoxLayout()

        # Export Button
        self._regime_opt_export_btn = QPushButton(get_icon("save"), "Export Results (JSON)")
        self._regime_opt_export_btn.setEnabled(False)
        self._regime_opt_export_btn.setToolTip("Export optimization results with parameter ranges to JSON file")
        self._regime_opt_export_btn.clicked.connect(self._on_regime_opt_export)
        action_layout.addWidget(self._regime_opt_export_btn)

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

        logger.info("Starting regime optimization with TPE")

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
        config_template_path = str(
            Path(__file__).parent.parent.parent.parent / "config" / "regime_config_default.json"
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
        logger.info(f"Regime optimization complete: {len(results)} trials")

        # Update results
        self._regime_opt_all_results = results

        # Update UI
        self._regime_opt_start_btn.setEnabled(True)
        self._regime_opt_stop_btn.setEnabled(False)
        self._regime_opt_continue_btn.setEnabled(True)
        self._regime_opt_export_btn.setEnabled(True)
        self._regime_opt_progress_bar.setValue(100)

        elapsed = (
            (datetime.utcnow() - self._regime_opt_start_time).total_seconds()
            if self._regime_opt_start_time
            else 0
        )
        elapsed_text = (
            f"{int(elapsed)}s" if elapsed < 60 else f"{int(elapsed / 60)}m {int(elapsed % 60)}s"
        )

        self._regime_opt_status_label.setText(
            f"✅ Optimization complete! {len(results)} trials in {elapsed_text}. "
            f"Best score: {results[0]['score']:.1f}"
        )
        self._regime_opt_status_label.setStyleSheet("color: #22c55e;")
        self._regime_opt_eta_label.setText(f"Total: {elapsed_text}")

        # Update top-5 table
        self._update_regime_opt_top5_table()

        # Enable Regime Results tab and populate it
        if hasattr(self, "_tabs"):
            # Find Regime Results tab (should be tab 4)
            for i in range(self._tabs.count()):
                if "Regime Results" in self._tabs.tabText(
                    i
                ) or "3. Regime Results" in self._tabs.tabText(i):
                    self._tabs.setTabEnabled(i, True)
                    break

        # Populate results table in Regime Results tab
        if hasattr(self, "_populate_regime_results_table"):
            self._populate_regime_results_table()

    @pyqtSlot(str)
    def _on_regime_opt_error(self, error_msg: str) -> None:
        """Handle optimization error.

        Args:
            error_msg: Error message
        """
        logger.error(f"Regime optimization error: {error_msg}")

        # Update UI
        self._regime_opt_start_btn.setEnabled(True)
        self._regime_opt_stop_btn.setEnabled(False)
        self._regime_opt_status_label.setText(f"❌ Error: {error_msg}")
        self._regime_opt_status_label.setStyleSheet("color: #ef4444;")
        self._regime_opt_eta_label.setText("ETA: --")

    def _update_regime_opt_top5_table(self) -> None:
        """Update top-5 results table with all 13 parameters."""
        # Get top 5 results
        top5 = self._regime_opt_all_results[:5]

        # Disable sorting while updating
        self._regime_opt_top5_table.setSortingEnabled(False)
        self._regime_opt_top5_table.setRowCount(len(top5))

        for row, result in enumerate(top5):
            params = result.get("params", {})
            score = result.get("score", 0)
            trial_num = result.get("trial_number", row + 1)

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

            # Highlight best result (row 0)
            if row == 0:
                for col in range(13):
                    item = self._regime_opt_top5_table.item(row, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.green)

        # Re-enable sorting
        self._regime_opt_top5_table.setSortingEnabled(True)

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
        project_root = Path(__file__).parent.parent.parent.parent
        default_dir = project_root / "03_JSON" / "Entry_Analyzer"
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

            from src.core.regime_optimizer import OptimizationConfig
            optimizer = RegimeOptimizer(
                data=df,
                param_ranges=param_ranges,
                config=OptimizationConfig(max_trials=1)
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
