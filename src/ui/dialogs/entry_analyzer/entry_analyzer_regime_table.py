"""DEPRECATED: Entry Analyzer - Regime Table Tab (Mixin).

⚠️ THIS MODULE IS DEPRECATED AND WILL BE REMOVED IN v3.0 ⚠️

This module uses Grid Search (303,750 combinations, ~9 hours runtime).
Use the new RegimeOptimizationMixin with Optuna TPE instead:
- 150 trials, ~2 minutes runtime
- 270x faster
- Better results via Bayesian optimization

New modules to use:
- RegimeSetupMixin (Tab "1. Regime Setup")
- RegimeOptimizationMixin (Tab "2. Regime Optimization")
- RegimeResultsMixin (Tab "3. Regime Results")

Deprecated features:
- Grid search over parameter combinations
- Manual parameter range configuration
- Single-threaded optimization

Date: 2026-01-24
Replacement: entry_analyzer_regime_optimization_mixin.py
"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGroupBox,
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


class RegimeTableMixin:
    """DEPRECATED: Mixin for Regime Table tab in Entry Analyzer.

    ⚠️ THIS CLASS IS DEPRECATED - Use RegimeOptimizationMixin instead ⚠️

    Deprecated functionality:
        - Parameter range configuration → Use RegimeSetupMixin
        - Regime optimization (grid search) → Use RegimeOptimizationMixin with TPE
        - Results table → Use RegimeResultsMixin

    Performance comparison:
        - Grid Search: 303,750 combinations, ~9 hours
        - Optuna TPE: 150 trials, ~2 minutes (270x faster)
        - Results table with sorting
        - Draw to chart functionality
        - Excel export
    """

    # Type hints for parent class attributes
    _regime_table_tab: QWidget
    _regime_opt_param_grid: Dict[str, tuple[QComboBox, QSpinBox, QSpinBox]]
    _regime_opt_optimize_btn: QPushButton
    _regime_opt_progress: QProgressBar
    _regime_opt_status_label: QLabel
    _regime_opt_results_table: QTableWidget
    _regime_opt_draw_btn: QPushButton
    _regime_opt_export_btn: QPushButton
    _regime_optimization_thread: RegimeOptimizationThread | None
    _regime_optimization_results: List[Dict[str, Any]]

    def _setup_regime_table_tab(self, tab: QWidget) -> None:
        """DEPRECATED: Setup Regime Table tab with parameter grid and results.

        ⚠️ WARNING: This tab uses slow Grid Search (303,750 combinations, ~9 hours).
        Switch to new tabs for 270x speedup:
        - Tab "1. Regime Setup" (RegimeSetupMixin)
        - Tab "2. Regime Optimization" (RegimeOptimizationMixin with TPE)
        - Tab "3. Regime Results" (RegimeResultsMixin)

        Args:
            tab: QWidget to populate
        """
        warnings.warn(
            "RegimeTableMixin is deprecated. "
            "Use RegimeOptimizationMixin with Optuna TPE for 270x speedup.",
            DeprecationWarning,
            stacklevel=2,
        )
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel("Regime Parameter Optimization")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)

        # Parameter Grid Configuration
        param_group = self._create_param_grid_group()
        layout.addWidget(param_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self._regime_opt_optimize_btn = QPushButton(get_icon("play_arrow"), "Start Optimization")
        self._regime_opt_optimize_btn.clicked.connect(self._on_regime_optimization_start)
        control_layout.addWidget(self._regime_opt_optimize_btn)

        control_layout.addStretch()

        self._regime_opt_progress = QProgressBar()
        self._regime_opt_progress.setVisible(False)
        control_layout.addWidget(self._regime_opt_progress, stretch=1)

        layout.addLayout(control_layout)

        # Status label
        self._regime_opt_status_label = QLabel(
            "Ready. Configure parameters and click 'Start Optimization'."
        )
        self._regime_opt_status_label.setWordWrap(True)
        layout.addWidget(self._regime_opt_status_label)

        # Results table
        results_layout = QVBoxLayout()

        results_header = QHBoxLayout()
        results_label = QLabel("Optimization Results:")
        results_label.setStyleSheet("font-weight: bold;")
        results_header.addWidget(results_label)
        results_header.addStretch()

        self._regime_opt_draw_btn = QPushButton(get_icon("show_chart"), "Draw Selected to Chart")
        self._regime_opt_draw_btn.setEnabled(False)
        self._regime_opt_draw_btn.clicked.connect(self._on_regime_draw_selected)
        results_header.addWidget(self._regime_opt_draw_btn)

        self._regime_opt_export_btn = QPushButton(get_icon("download"), "Export to Excel")
        self._regime_opt_export_btn.setEnabled(False)
        self._regime_opt_export_btn.clicked.connect(self._on_regime_export_excel)
        results_header.addWidget(self._regime_opt_export_btn)

        results_layout.addLayout(results_header)

        self._regime_opt_results_table = QTableWidget()
        self._regime_opt_results_table.setColumnCount(10)
        self._regime_opt_results_table.setHorizontalHeaderLabels(
            [
                "Rank",
                "Score",
                "ADX Period",
                "ADX Threshold",
                "RSI Period",
                "RSI Oversold",
                "RSI Overbought",
                "Regime Count",
                "Avg Duration",
                "Switches",
            ]
        )
        self._regime_opt_results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._regime_opt_results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._regime_opt_results_table.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        self._regime_opt_results_table.setSortingEnabled(True)
        results_layout.addWidget(self._regime_opt_results_table, stretch=1)

        layout.addLayout(results_layout, stretch=1)

        # Initialize state
        self._regime_optimization_thread = None
        self._regime_optimization_results = []

    def _create_param_grid_group(self) -> QGroupBox:
        """Create parameter grid configuration group.

        Returns:
            QGroupBox with parameter range controls
        """
        group = QGroupBox("Parameter Ranges")
        layout = QVBoxLayout(group)

        # Initialize param grid dict
        self._regime_opt_param_grid = {}

        # ADX Period
        adx_period_layout = QHBoxLayout()
        adx_period_layout.addWidget(QLabel("ADX Period:"))
        adx_period_preset = QComboBox()
        adx_period_preset.addItems(["10-14-20", "7-14-21", "12-16-20", "Custom"])
        adx_period_preset.currentTextChanged.connect(
            lambda text: self._on_param_preset_changed("adx_period", text)
        )
        adx_period_layout.addWidget(adx_period_preset)
        adx_period_min = QSpinBox()
        adx_period_min.setRange(3, 50)
        adx_period_min.setValue(10)
        adx_period_layout.addWidget(QLabel("Min:"))
        adx_period_layout.addWidget(adx_period_min)
        adx_period_max = QSpinBox()
        adx_period_max.setRange(3, 50)
        adx_period_max.setValue(20)
        adx_period_layout.addWidget(QLabel("Max:"))
        adx_period_layout.addWidget(adx_period_max)
        adx_period_layout.addStretch()
        layout.addLayout(adx_period_layout)
        self._regime_opt_param_grid["adx_period"] = (
            adx_period_preset,
            adx_period_min,
            adx_period_max,
        )

        # ADX Threshold
        adx_thresh_layout = QHBoxLayout()
        adx_thresh_layout.addWidget(QLabel("ADX Threshold:"))
        adx_thresh_preset = QComboBox()
        adx_thresh_preset.addItems(["17-25-40", "20-30-50", "15-25-35", "Custom"])
        adx_thresh_preset.currentTextChanged.connect(
            lambda text: self._on_param_preset_changed("adx_threshold", text)
        )
        adx_thresh_layout.addWidget(adx_thresh_preset)
        adx_thresh_min = QSpinBox()
        adx_thresh_min.setRange(10, 70)
        adx_thresh_min.setValue(17)
        adx_thresh_layout.addWidget(QLabel("Min:"))
        adx_thresh_layout.addWidget(adx_thresh_min)
        adx_thresh_max = QSpinBox()
        adx_thresh_max.setRange(10, 70)
        adx_thresh_max.setValue(40)
        adx_thresh_layout.addWidget(QLabel("Max:"))
        adx_thresh_layout.addWidget(adx_thresh_max)
        adx_thresh_layout.addStretch()
        layout.addLayout(adx_thresh_layout)
        self._regime_opt_param_grid["adx_threshold"] = (
            adx_thresh_preset,
            adx_thresh_min,
            adx_thresh_max,
        )

        # RSI Period
        rsi_period_layout = QHBoxLayout()
        rsi_period_layout.addWidget(QLabel("RSI Period:"))
        rsi_period_preset = QComboBox()
        rsi_period_preset.addItems(["9-14-21", "7-14-18", "10-15-20", "Custom"])
        rsi_period_preset.currentTextChanged.connect(
            lambda text: self._on_param_preset_changed("rsi_period", text)
        )
        rsi_period_layout.addWidget(rsi_period_preset)
        rsi_period_min = QSpinBox()
        rsi_period_min.setRange(5, 30)
        rsi_period_min.setValue(9)
        rsi_period_layout.addWidget(QLabel("Min:"))
        rsi_period_layout.addWidget(rsi_period_min)
        rsi_period_max = QSpinBox()
        rsi_period_max.setRange(5, 30)
        rsi_period_max.setValue(21)
        rsi_period_layout.addWidget(QLabel("Max:"))
        rsi_period_layout.addWidget(rsi_period_max)
        rsi_period_layout.addStretch()
        layout.addLayout(rsi_period_layout)
        self._regime_opt_param_grid["rsi_period"] = (
            rsi_period_preset,
            rsi_period_min,
            rsi_period_max,
        )

        # RSI Oversold
        rsi_oversold_layout = QHBoxLayout()
        rsi_oversold_layout.addWidget(QLabel("RSI Oversold:"))
        rsi_oversold_preset = QComboBox()
        rsi_oversold_preset.addItems(["20-30", "25-35", "15-25", "Custom"])
        rsi_oversold_preset.currentTextChanged.connect(
            lambda text: self._on_param_preset_changed("rsi_oversold", text)
        )
        rsi_oversold_layout.addWidget(rsi_oversold_preset)
        rsi_oversold_min = QSpinBox()
        rsi_oversold_min.setRange(10, 50)
        rsi_oversold_min.setValue(20)
        rsi_oversold_layout.addWidget(QLabel("Min:"))
        rsi_oversold_layout.addWidget(rsi_oversold_min)
        rsi_oversold_max = QSpinBox()
        rsi_oversold_max.setRange(10, 50)
        rsi_oversold_max.setValue(30)
        rsi_oversold_layout.addWidget(QLabel("Max:"))
        rsi_oversold_layout.addWidget(rsi_oversold_max)
        rsi_oversold_layout.addStretch()
        layout.addLayout(rsi_oversold_layout)
        self._regime_opt_param_grid["rsi_oversold"] = (
            rsi_oversold_preset,
            rsi_oversold_min,
            rsi_oversold_max,
        )

        # RSI Overbought
        rsi_overbought_layout = QHBoxLayout()
        rsi_overbought_layout.addWidget(QLabel("RSI Overbought:"))
        rsi_overbought_preset = QComboBox()
        rsi_overbought_preset.addItems(["70-80", "65-75", "75-85", "Custom"])
        rsi_overbought_preset.currentTextChanged.connect(
            lambda text: self._on_param_preset_changed("rsi_overbought", text)
        )
        rsi_overbought_layout.addWidget(rsi_overbought_preset)
        rsi_overbought_min = QSpinBox()
        rsi_overbought_min.setRange(50, 90)
        rsi_overbought_min.setValue(70)
        rsi_overbought_layout.addWidget(QLabel("Min:"))
        rsi_overbought_layout.addWidget(rsi_overbought_min)
        rsi_overbought_max = QSpinBox()
        rsi_overbought_max.setRange(50, 90)
        rsi_overbought_max.setValue(80)
        rsi_overbought_layout.addWidget(QLabel("Max:"))
        rsi_overbought_layout.addWidget(rsi_overbought_max)
        rsi_overbought_layout.addStretch()
        layout.addLayout(rsi_overbought_layout)
        self._regime_opt_param_grid["rsi_overbought"] = (
            rsi_overbought_preset,
            rsi_overbought_min,
            rsi_overbought_max,
        )

        return group

    def _on_param_preset_changed(self, param_name: str, preset: str):
        """Handle preset selection change.

        Args:
            param_name: Parameter identifier
            preset: Selected preset string
        """
        if preset == "Custom":
            return

        _, min_spin, max_spin = self._regime_opt_param_grid[param_name]

        # Parse preset (format: "min-max" or "min-mid-max")
        parts = preset.split("-")
        if len(parts) >= 2:
            min_val = int(parts[0])
            max_val = int(parts[-1])
            min_spin.setValue(min_val)
            max_spin.setValue(max_val)

    def auto_select_parameter_ranges_for_regime(self, regime_type: str) -> None:
        """Automatically select parameter range presets based on detected regime.

        Issue #8: Auto-select parameter ranges when regime is detected.

        Args:
            regime_type: Detected regime type (trend_up, trend_down, range, etc.)
        """
        logger.info(f"AUTO-SELECT CALLED: regime_type={regime_type}")

        if not hasattr(self, "_regime_opt_param_grid") or not self._regime_opt_param_grid:
            logger.warning("Regime parameter grid not initialized")
            # Visual feedback: Show warning in status label
            if hasattr(self, "_regime_opt_status_label"):
                self._regime_opt_status_label.setText(
                    "⚠ Parameter grid not yet initialized. Open the Reg. Table tab first."
                )
                self._regime_opt_status_label.setStyleSheet("color: orange;")
            return

        # Mapping: regime_type -> preset selections
        # Optimized for each market condition
        regime_presets = {
            "trend_up": {
                "adx_period": "12-16-20",  # Longer periods for trend confirmation
                "adx_threshold": "20-30-50",  # Higher threshold for strong trends
                "rsi_period": "10-15-20",  # Standard RSI periods
                "rsi_oversold": "25-35",  # Less aggressive oversold
                "rsi_overbought": "65-75",  # Less aggressive overbought
            },
            "trend_down": {
                "adx_period": "12-16-20",
                "adx_threshold": "20-30-50",
                "rsi_period": "10-15-20",
                "rsi_oversold": "25-35",
                "rsi_overbought": "65-75",
            },
            "range": {
                "adx_period": "7-14-21",  # Shorter periods for range detection
                "adx_threshold": "15-25-35",  # Lower threshold for weak trend
                "rsi_period": "7-14-18",  # Faster RSI for range
                "rsi_oversold": "20-30",  # More aggressive levels
                "rsi_overbought": "70-80",
            },
            "high_vol": {
                "adx_period": "10-14-20",  # Medium periods
                "adx_threshold": "17-25-40",  # Standard threshold
                "rsi_period": "9-14-21",  # Standard RSI
                "rsi_oversold": "15-25",  # Extreme oversold for high vol
                "rsi_overbought": "75-85",  # Extreme overbought for high vol
            },
            "squeeze": {
                "adx_period": "10-14-20",  # Medium periods
                "adx_threshold": "15-25-35",  # Lower threshold (squeeze = low ADX)
                "rsi_period": "9-14-21",  # Standard RSI
                "rsi_oversold": "25-35",  # Conservative levels
                "rsi_overbought": "65-75",
            },
            "no_trade": {
                "adx_period": "10-14-20",  # Medium periods
                "adx_threshold": "17-25-40",  # Standard threshold
                "rsi_period": "9-14-21",  # Standard RSI
                "rsi_oversold": "20-30",  # Standard levels
                "rsi_overbought": "70-80",
            },
        }

        # Get presets for this regime type
        presets = regime_presets.get(regime_type)
        if not presets:
            logger.warning(f"No parameter presets defined for regime: {regime_type}")
            return

        # Apply presets to UI
        try:
            for param_name, preset_value in presets.items():
                if param_name in self._regime_opt_param_grid:
                    combo, min_spin, max_spin = self._regime_opt_param_grid[param_name]

                    # Find and select preset in combo box
                    index = combo.findText(preset_value)
                    if index >= 0:
                        combo.setCurrentIndex(index)
                        # _on_param_preset_changed will be called automatically
                        logger.debug(f"Set {param_name} preset to {preset_value}")
                    else:
                        logger.warning(f"Preset {preset_value} not found for {param_name}")

            logger.info(f"Auto-selected parameter ranges for regime: {regime_type}")

            # Visual feedback: Update status label if it exists
            if hasattr(self, "_regime_opt_status_label"):
                self._regime_opt_status_label.setText(
                    f"✓ Auto-selected parameter ranges for {regime_type.replace('_', ' ').title()}"
                )
                self._regime_opt_status_label.setStyleSheet("color: green; font-weight: bold;")

        except Exception as e:
            logger.error(f"Failed to auto-select parameter ranges: {e}", exc_info=True)
            # Visual feedback: Show error in status label
            if hasattr(self, "_regime_opt_status_label"):
                self._regime_opt_status_label.setText(
                    f"⚠ Failed to auto-select parameter ranges: {e}"
                )
                self._regime_opt_status_label.setStyleSheet("color: red;")

    def _on_regime_optimization_start(self):
        """Start regime parameter optimization."""
        try:
            # Get chart data
            if not hasattr(self, "_candles") or not self._candles:
                QMessageBox.warning(self, "No Data", "Please load chart data first.")
                return

            # Convert candles to DataFrame
            import pandas as pd

            df = pd.DataFrame(self._candles)

            # Handle different time column names (timestamp vs time)
            time_col = None
            if "timestamp" in df.columns:
                time_col = "timestamp"
            elif "time" in df.columns:
                time_col = "time"
            else:
                raise ValueError(
                    f"No time column found in candles. Available columns: {list(df.columns)}"
                )

            # Convert to datetime and set as index
            df["time"] = pd.to_datetime(df[time_col], unit="s")
            df.set_index("time", inplace=True)

            # Get parameter grid
            param_grid = {}
            for param_name, (_, min_spin, max_spin) in self._regime_opt_param_grid.items():
                min_val = min_spin.value()
                max_val = max_spin.value()

                # Generate range
                if param_name in ["adx_period", "rsi_period"]:
                    step = 3  # Step size for periods
                elif param_name in ["adx_threshold", "rsi_oversold", "rsi_overbought"]:
                    step = 5  # Step size for thresholds
                else:
                    step = 1

                values = list(range(min_val, max_val + 1, step))
                param_grid[param_name] = values

            # Count total combinations
            total = 1
            for values in param_grid.values():
                total *= len(values)

            # Confirm with user
            reply = QMessageBox.question(
                self,
                "Confirm Optimization",
                f"This will test {total} parameter combinations.\n\n"
                f"Estimated time: {total * 0.5:.0f}-{total * 1:.0f} seconds\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Get config path
            config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")
            if not config_path.exists():
                QMessageBox.critical(
                    self, "Config Not Found", f"Regime config not found: {config_path}"
                )
                return

            # Clear previous results
            self._regime_opt_results_table.setRowCount(0)
            self._regime_optimization_results = []

            # Disable button
            self._regime_opt_optimize_btn.setEnabled(False)
            self._regime_opt_progress.setVisible(True)
            self._regime_opt_progress.setValue(0)
            self._regime_opt_status_label.setText(
                f"Starting optimization ({total} combinations)..."
            )

            # Create and start optimization thread
            self._regime_optimization_thread = RegimeOptimizationThread(
                df=df, config_template_path=str(config_path), param_grid=param_grid, scope="entry"
            )

            self._regime_optimization_thread.progress.connect(self._on_regime_optimization_progress)
            self._regime_optimization_thread.result_ready.connect(
                self._on_regime_optimization_result
            )
            self._regime_optimization_thread.finished_with_results.connect(
                self._on_regime_optimization_finished
            )
            self._regime_optimization_thread.error.connect(self._on_regime_optimization_error)

            self._regime_optimization_thread.start()

        except Exception as e:
            logger.error(f"Failed to start regime optimization: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to start optimization: {str(e)}")

    def _on_regime_optimization_progress(self, current: int, total: int, message: str):
        """Handle optimization progress update.

        Args:
            current: Current combination index
            total: Total combinations
            message: Progress message
        """
        progress_pct = int((current / total) * 100)
        self._regime_opt_progress.setValue(progress_pct)
        self._regime_opt_status_label.setText(f"{message} ({current}/{total} - {progress_pct}%)")

    def _on_regime_optimization_result(self, result: Dict[str, Any]):
        """Handle single optimization result.

        Args:
            result: Result dictionary
        """
        # Add result to internal list
        self._regime_optimization_results.append(result)

        # Add row to table
        row = self._regime_opt_results_table.rowCount()
        self._regime_opt_results_table.insertRow(row)

        # Extract parameters
        params = result["params"]
        metrics = result["metrics"]

        # Populate columns
        self._regime_opt_results_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))  # Rank
        self._regime_opt_results_table.setItem(row, 1, QTableWidgetItem(str(result["score"])))
        self._regime_opt_results_table.setItem(
            row, 2, QTableWidgetItem(str(params.get("adx_period", "N/A")))
        )
        self._regime_opt_results_table.setItem(
            row, 3, QTableWidgetItem(str(params.get("adx_threshold", "N/A")))
        )
        self._regime_opt_results_table.setItem(
            row, 4, QTableWidgetItem(str(params.get("rsi_period", "N/A")))
        )
        self._regime_opt_results_table.setItem(
            row, 5, QTableWidgetItem(str(params.get("rsi_oversold", "N/A")))
        )
        self._regime_opt_results_table.setItem(
            row, 6, QTableWidgetItem(str(params.get("rsi_overbought", "N/A")))
        )
        self._regime_opt_results_table.setItem(
            row, 7, QTableWidgetItem(str(metrics["regime_count"]))
        )
        self._regime_opt_results_table.setItem(
            row, 8, QTableWidgetItem(f"{metrics['avg_duration']:.1f}")
        )
        self._regime_opt_results_table.setItem(
            row, 9, QTableWidgetItem(str(metrics["switch_count"]))
        )

        # Store result in row data
        self._regime_opt_results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, result)

    def _on_regime_optimization_finished(self, results: List[Dict[str, Any]]):
        """Handle optimization completion.

        Args:
            results: All optimization results (sorted by score)
        """
        self._regime_opt_optimize_btn.setEnabled(True)
        self._regime_opt_progress.setVisible(False)
        summary_text = ""
        if self._regime_optimization_thread:
            summary_text = getattr(self._regime_optimization_thread, "timing_summary_text", "")

        status_text = (
            f"Optimization complete! {len(results)} combinations tested. "
            "Select rows and click 'Draw Selected to Chart' to visualize."
        )
        if summary_text:
            status_text = f"{status_text}\n{summary_text}"

        self._regime_opt_status_label.setText(status_text)

        # Enable buttons
        self._regime_opt_draw_btn.setEnabled(True)
        self._regime_opt_export_btn.setEnabled(True)

        logger.info(f"Regime optimization complete: {len(results)} results")

    def _on_regime_optimization_error(self, error_msg: str):
        """Handle optimization error.

        Args:
            error_msg: Error message
        """
        self._regime_opt_optimize_btn.setEnabled(True)
        self._regime_opt_progress.setVisible(False)
        self._regime_opt_status_label.setText(f"Error: {error_msg}")

        QMessageBox.critical(self, "Optimization Error", error_msg)

    def _on_regime_draw_selected(self):
        """Draw selected regime configurations to chart."""
        selected_rows = set([item.row() for item in self._regime_opt_results_table.selectedItems()])

        if not selected_rows:
            QMessageBox.information(
                self, "No Selection", "Please select one or more rows to draw on the chart."
            )
            return

        # Get regime histories for selected rows
        regime_histories = []
        for row in sorted(selected_rows):
            result_item = self._regime_opt_results_table.item(row, 0)
            result = result_item.data(Qt.ItemDataRole.UserRole)
            if result:
                regime_histories.append(result["regime_history"])

        # Emit signal to draw regime lines
        # Flatten all regime histories into one list
        all_regimes = []
        for history in regime_histories:
            all_regimes.extend(history)

        if all_regimes:
            self.draw_regime_lines_requested.emit(all_regimes)
            self._regime_opt_status_label.setText(
                f"Drew {len(all_regimes)} regime periods from {len(selected_rows)} configuration(s) to chart."
            )
            logger.info(f"Drew {len(all_regimes)} regime periods to chart")

    def _on_regime_export_excel(self):
        """Export optimization results to Excel."""
        if not self._regime_optimization_results:
            QMessageBox.information(self, "No Results", "No optimization results to export.")
            return

        # Ask user for file path
        default_filename = f"regime_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", default_filename, "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            import pandas as pd

            # Prepare data for export
            export_data = []
            for idx, result in enumerate(self._regime_optimization_results, start=1):
                params = result["params"]
                metrics = result["metrics"]

                row = {
                    "Rank": idx,
                    "Score": result["score"],
                    "ADX Period": params.get("adx_period", "N/A"),
                    "ADX Threshold": params.get("adx_threshold", "N/A"),
                    "RSI Period": params.get("rsi_period", "N/A"),
                    "RSI Oversold": params.get("rsi_oversold", "N/A"),
                    "RSI Overbought": params.get("rsi_overbought", "N/A"),
                    "Regime Count": metrics["regime_count"],
                    "Avg Duration (bars)": f"{metrics['avg_duration']:.2f}",
                    "Switch Count": metrics["switch_count"],
                    "Stability Score": f"{metrics['stability_score']:.3f}",
                    "Coverage (%)": f"{metrics['coverage']:.2f}",
                }
                export_data.append(row)

            # Create DataFrame
            df = pd.DataFrame(export_data)

            # Export to Excel
            df.to_excel(file_path, index=False, sheet_name="Regime Optimization")

            QMessageBox.information(self, "Export Successful", f"Results exported to:\n{file_path}")

            logger.info(f"Exported regime optimization results to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Failed", f"Failed to export to Excel:\n{str(e)}")
