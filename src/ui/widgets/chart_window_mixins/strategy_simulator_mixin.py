"""Strategy Simulator Mixin for ChartWindow.

Provides the Strategy Simulator tab for backtesting the 5 base strategies
with configurable parameters and automated optimization.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.core.simulator import SimulationResult, OptimizationRun

logger = logging.getLogger(__name__)


class SimulationWorker(QThread):
    """Worker thread for running simulations."""

    finished = pyqtSignal(object)  # SimulationResult or OptimizationRun
    progress = pyqtSignal(int, int, float)  # current, total, best_score
    error = pyqtSignal(str)

    def __init__(
        self,
        data,
        symbol: str,
        strategy_name: str,
        parameters: dict,
        mode: str,
        opt_trials: int = 50,
    ):
        super().__init__()
        self.data = data
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.parameters = parameters
        self.mode = mode  # "manual", "grid", "bayesian"
        self.opt_trials = opt_trials
        self._cancelled = False
        self._optimizer = None  # type: ignore[var-annotated]

    def cancel(self):
        """Cancel running simulation."""
        self._cancelled = True
        if self._optimizer and hasattr(self._optimizer, "cancel"):
            try:
                self._optimizer.cancel()
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Optimizer cancel failed: %s", exc)

    def run(self):
        """Run simulation in separate thread."""
        try:
            from src.core.simulator import (
                StrategyName,
                StrategySimulator,
                OptimizationConfig,
                BayesianOptimizer,
                GridSearchOptimizer,
            )

            strategy = StrategyName(self.strategy_name)

            if self.mode == "manual":
                # Single simulation - needs event loop for async run_simulation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    simulator = StrategySimulator(self.data, self.symbol)
                    result = loop.run_until_complete(
                        simulator.run_simulation(
                            strategy_name=strategy,
                            parameters=self.parameters,
                        )
                    )
                    self.finished.emit(result)
                finally:
                    loop.close()

            elif self.mode in ("grid", "bayesian"):
                # Optimization - optimizers are synchronous and manage their own event loops
                config = OptimizationConfig(
                    strategy_name=strategy,
                    objective_metric="sharpe_ratio",
                    direction="maximize",
                    n_trials=self.opt_trials,
                )

                def progress_cb(current, total, best):
                    self.progress.emit(current, total, best)

                if self.mode == "bayesian":
                    optimizer = BayesianOptimizer(self.data, self.symbol, config)
                else:
                    optimizer = GridSearchOptimizer(self.data, self.symbol, config)

                # Keep reference so we can cancel from UI thread
                self._optimizer = optimizer

                # Optimizers are now synchronous
                result = optimizer.optimize(progress_callback=progress_cb)
                self.finished.emit(result)

        except Exception as e:
            logger.error("Simulation failed: %s", e, exc_info=True)
            self.error.emit(str(e))
        finally:
            self._optimizer = None


class StrategySimulatorMixin:
    """Mixin providing Strategy Simulator tab for ChartWindow."""

    # Storage for simulation results
    _simulation_results: list = []
    _table_row_results: list = []  # Maps table row index to SimulationResult or None
    _last_optimization_run: object = None
    _current_worker: SimulationWorker | None = None

    def _create_strategy_simulator_tab(self) -> QWidget:
        """Create the Strategy Simulator tab widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Splitter for controls and results
        splitter = QSplitter()

        # Left: Controls
        controls = self._create_simulator_controls()
        controls.setMaximumWidth(280)
        controls.setMinimumWidth(220)
        splitter.addWidget(controls)

        # Right: Results
        results = self._create_simulator_results()
        splitter.addWidget(results)

        splitter.setSizes([280, 600])
        layout.addWidget(splitter)

        # Initialize
        self._simulation_results = []
        self._table_row_results = []
        self._last_optimization_run = None
        self._on_simulator_strategy_changed(0)

        return widget

    def _create_simulator_controls(self) -> QWidget:
        """Create control panel (strategy selection, parameters, buttons)."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        # Strategy Selection Group
        strategy_group = QGroupBox("Strategy")
        strategy_layout = QVBoxLayout(strategy_group)

        self.simulator_strategy_combo = QComboBox()
        self.simulator_strategy_combo.addItems([
            "Breakout",
            "Momentum",
            "Mean Reversion",
            "Trend Following",
            "Scalping",
        ])
        self.simulator_strategy_combo.currentIndexChanged.connect(
            self._on_simulator_strategy_changed
        )
        strategy_layout.addWidget(self.simulator_strategy_combo)
        layout.addWidget(strategy_group)

        # Parameters Group (dynamic based on strategy)
        self.simulator_params_group = QGroupBox("Parameters")
        params_main_layout = QVBoxLayout(self.simulator_params_group)
        self.simulator_params_layout = QFormLayout()
        self._simulator_param_widgets: dict[str, QWidget] = {}
        params_main_layout.addLayout(self.simulator_params_layout)

        # Parameter action buttons (two rows for better fit)
        params_btn_row1 = QHBoxLayout()
        params_btn_row1.setSpacing(4)

        self.simulator_reset_params_btn = QPushButton("Reset")
        self.simulator_reset_params_btn.setToolTip("Parameter auf Standardwerte zurücksetzen")
        self.simulator_reset_params_btn.clicked.connect(self._on_reset_simulator_params)
        params_btn_row1.addWidget(self.simulator_reset_params_btn)

        self.simulator_save_to_bot_btn = QPushButton("Save")
        self.simulator_save_to_bot_btn.setToolTip("Parameter für produktiven Bot speichern")
        self.simulator_save_to_bot_btn.clicked.connect(self._on_save_params_to_bot)
        params_btn_row1.addWidget(self.simulator_save_to_bot_btn)

        self.simulator_load_from_bot_btn = QPushButton("Load")
        self.simulator_load_from_bot_btn.setToolTip("Gespeicherte Parameter laden")
        self.simulator_load_from_bot_btn.clicked.connect(self._on_load_params_from_bot)
        params_btn_row1.addWidget(self.simulator_load_from_bot_btn)

        params_main_layout.addLayout(params_btn_row1)

        layout.addWidget(self.simulator_params_group)

        # Optimization Mode Group
        opt_group = QGroupBox("Mode")
        opt_layout = QVBoxLayout(opt_group)

        self.simulator_opt_mode_group = QButtonGroup()
        self.simulator_opt_manual = QRadioButton("Manual (Single Run)")
        self.simulator_opt_grid = QRadioButton("Grid Search")
        self.simulator_opt_bayesian = QRadioButton("Bayesian Optimization")
        self.simulator_opt_manual.setChecked(True)

        self.simulator_opt_mode_group.addButton(self.simulator_opt_manual, 0)
        self.simulator_opt_mode_group.addButton(self.simulator_opt_grid, 1)
        self.simulator_opt_mode_group.addButton(self.simulator_opt_bayesian, 2)

        opt_layout.addWidget(self.simulator_opt_manual)
        opt_layout.addWidget(self.simulator_opt_grid)
        opt_layout.addWidget(self.simulator_opt_bayesian)

        # Trials spinner
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Trials:"))
        self.simulator_opt_trials_spin = QSpinBox()
        self.simulator_opt_trials_spin.setRange(10, 500)
        self.simulator_opt_trials_spin.setValue(50)
        trials_layout.addWidget(self.simulator_opt_trials_spin)
        opt_layout.addLayout(trials_layout)

        layout.addWidget(opt_group)

        # Action Buttons
        buttons_layout = QHBoxLayout()

        self.simulator_run_btn = QPushButton("Run")
        self.simulator_run_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        self.simulator_run_btn.clicked.connect(self._on_run_simulation)
        buttons_layout.addWidget(self.simulator_run_btn)

        self.simulator_stop_btn = QPushButton("Stop")
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_stop_btn.clicked.connect(self._on_stop_simulation)
        buttons_layout.addWidget(self.simulator_stop_btn)

        layout.addLayout(buttons_layout)

        # Progress
        self.simulator_progress = QProgressBar()
        self.simulator_progress.setVisible(False)
        layout.addWidget(self.simulator_progress)

        # Status label
        self.simulator_status_label = QLabel("")
        self.simulator_status_label.setWordWrap(True)
        layout.addWidget(self.simulator_status_label)

        layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        return widget

    def _create_simulator_results(self) -> QWidget:
        """Create results panel (table + export)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Results Table
        self.simulator_results_table = QTableWidget()
        self.simulator_results_table.setColumnCount(9)
        self.simulator_results_table.setHorizontalHeaderLabels([
            "Strategy",
            "Trades",
            "Win %",
            "PF",
            "P&L €",
            "P&L %",
            "DD %",
            "Score",
            "Parameters",
        ])
        # Set column resize modes - last column (Parameters) gets extra space
        header = self.simulator_results_table.horizontalHeader()
        for i in range(8):  # First 8 columns: fixed width
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Parameters column: stretches to fill remaining space
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.simulator_results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.simulator_results_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.simulator_results_table.itemSelectionChanged.connect(
            self._on_simulator_result_selected
        )
        layout.addWidget(self.simulator_results_table)

        # Buttons row
        buttons_layout = QHBoxLayout()

        self.simulator_show_markers_btn = QPushButton("Show Entry/Exit")
        self.simulator_show_markers_btn.clicked.connect(self._on_show_simulation_markers)
        self.simulator_show_markers_btn.setEnabled(False)
        buttons_layout.addWidget(self.simulator_show_markers_btn)

        self.simulator_clear_markers_btn = QPushButton("Clear Markers")
        self.simulator_clear_markers_btn.clicked.connect(self._on_clear_simulation_markers)
        buttons_layout.addWidget(self.simulator_clear_markers_btn)

        self.simulator_export_btn = QPushButton("Export Excel")
        self.simulator_export_btn.clicked.connect(self._on_export_simulation_xlsx)
        self.simulator_export_btn.setEnabled(False)
        buttons_layout.addWidget(self.simulator_export_btn)

        self.simulator_clear_results_btn = QPushButton("Clear All")
        self.simulator_clear_results_btn.clicked.connect(self._on_clear_simulation_results)
        buttons_layout.addWidget(self.simulator_clear_results_btn)

        layout.addLayout(buttons_layout)

        return widget

    def _on_simulator_strategy_changed(self, index: int) -> None:
        """Update parameter widgets when strategy changes."""
        from src.core.simulator import StrategyName, get_strategy_parameters

        strategy_map = {
            0: StrategyName.BREAKOUT,
            1: StrategyName.MOMENTUM,
            2: StrategyName.MEAN_REVERSION,
            3: StrategyName.TREND_FOLLOWING,
            4: StrategyName.SCALPING,
        }
        strategy = strategy_map.get(index, StrategyName.BREAKOUT)
        self._populate_simulator_parameter_widgets(strategy)

    def _populate_simulator_parameter_widgets(self, strategy) -> None:
        """Create parameter input widgets for selected strategy."""
        from src.core.simulator import get_strategy_parameters

        # Clear existing
        while self.simulator_params_layout.count():
            item = self.simulator_params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._simulator_param_widgets.clear()

        # Get parameter definitions
        param_config = get_strategy_parameters(strategy)

        for param_def in param_config.parameters:
            if param_def.param_type == "int":
                widget = QSpinBox()
                widget.setRange(
                    param_def.min_value or 0,
                    param_def.max_value or 100,
                )
                widget.setValue(param_def.default)
                if param_def.step:
                    widget.setSingleStep(param_def.step)
            elif param_def.param_type == "float":
                widget = QDoubleSpinBox()
                widget.setRange(
                    param_def.min_value or 0.0,
                    param_def.max_value or 100.0,
                )
                widget.setValue(param_def.default)
                if param_def.step:
                    widget.setSingleStep(param_def.step)
                widget.setDecimals(3)
            else:
                continue  # Skip bool for now

            widget.setToolTip(param_def.description)
            self._simulator_param_widgets[param_def.name] = widget
            self.simulator_params_layout.addRow(
                f"{param_def.display_name}:", widget
            )

    def _get_simulator_parameters(self) -> dict[str, Any]:
        """Get current parameter values from widgets."""
        params = {}
        for name, widget in self._simulator_param_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                params[name] = widget.value()
        return params

    def _on_reset_simulator_params(self) -> None:
        """Reset all parameter widgets to their default values."""
        from src.core.simulator import StrategyName, get_strategy_parameters

        strategy_map = {
            0: StrategyName.BREAKOUT,
            1: StrategyName.MOMENTUM,
            2: StrategyName.MEAN_REVERSION,
            3: StrategyName.TREND_FOLLOWING,
            4: StrategyName.SCALPING,
        }
        strategy = strategy_map.get(
            self.simulator_strategy_combo.currentIndex(), StrategyName.BREAKOUT
        )
        param_config = get_strategy_parameters(strategy)

        for param_def in param_config.parameters:
            widget = self._simulator_param_widgets.get(param_def.name)
            if widget and isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(param_def.default)

        self.simulator_status_label.setText("Parameters reset to default")

    def _on_save_params_to_bot(self) -> None:
        """Save current parameters for production bot use."""
        from src.core.simulator import save_strategy_params

        strategy_name = self._get_simulator_strategy_name()
        params = self._get_simulator_parameters()

        # Get symbol from current chart if available
        symbol = None
        if hasattr(self, "current_symbol"):
            symbol = self.current_symbol

        try:
            filepath = save_strategy_params(
                strategy_name=strategy_name,
                params=params,
                symbol=symbol,
            )
            self.simulator_status_label.setText(f"Parameters saved: {strategy_name}")
            QMessageBox.information(
                self,
                "Parameters Saved",
                f"Strategy parameters saved for production bot.\n\n"
                f"Strategy: {strategy_name}\n"
                f"File: {filepath}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save parameters: {e}")

    def _on_load_params_from_bot(self) -> None:
        """Load saved parameters from production bot config."""
        from src.core.simulator import load_strategy_params, get_params_metadata

        strategy_name = self._get_simulator_strategy_name()

        params = load_strategy_params(strategy_name)

        if params is None:
            QMessageBox.warning(
                self,
                "No Saved Parameters",
                f"No saved parameters found for strategy: {strategy_name}\n\n"
                "Use 'Save to Bot' to save optimized parameters first.",
            )
            return

        # Apply loaded parameters to widgets
        for param_name, value in params.items():
            widget = self._simulator_param_widgets.get(param_name)
            if widget and isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)

        # Show metadata info
        metadata = get_params_metadata(strategy_name)
        info_text = f"Loaded parameters for {strategy_name}"
        if metadata:
            if metadata.get("saved_at"):
                info_text += f"\nSaved: {metadata['saved_at'][:19]}"
            if metadata.get("symbol"):
                info_text += f"\nOptimized for: {metadata['symbol']}"

        self.simulator_status_label.setText(f"Parameters loaded: {strategy_name}")
        QMessageBox.information(self, "Parameters Loaded", info_text)

    def _get_simulator_strategy_name(self) -> str:
        """Get currently selected strategy name."""
        strategy_map = {
            0: "breakout",
            1: "momentum",
            2: "mean_reversion",
            3: "trend_following",
            4: "scalping",
        }
        return strategy_map.get(
            self.simulator_strategy_combo.currentIndex(), "breakout"
        )

    def _on_run_simulation(self) -> None:
        """Run simulation with current settings."""
        # Get chart data
        if not hasattr(self, "chart_widget"):
            QMessageBox.warning(
                self, "Error", "No chart widget available"
            )
            return

        # Try to get DataFrame from chart
        # The DataLoadingMixin stores data as self.data on the chart_widget
        data = None
        if hasattr(self.chart_widget, "data") and self.chart_widget.data is not None:
            data = self.chart_widget.data
        elif hasattr(self.chart_widget, "get_dataframe"):
            data = self.chart_widget.get_dataframe()
        elif hasattr(self.chart_widget, "_df"):
            data = self.chart_widget._df

        if data is None or (hasattr(data, "empty") and data.empty):
            QMessageBox.warning(
                self, "Error", "No chart data available. Load a chart first."
            )
            return

        # Get symbol from chart_widget or ChartWindow
        symbol = getattr(self, "symbol", "UNKNOWN")
        if hasattr(self.chart_widget, "current_symbol") and self.chart_widget.current_symbol:
            symbol = self.chart_widget.current_symbol
        elif hasattr(self.chart_widget, "symbol"):
            symbol = self.chart_widget.symbol

        # Get current parameters
        params = self._get_simulator_parameters()
        strategy_name = self._get_simulator_strategy_name()

        # Determine mode
        mode_id = self.simulator_opt_mode_group.checkedId()
        mode_map = {0: "manual", 1: "grid", 2: "bayesian"}
        mode = mode_map.get(mode_id, "manual")

        # Disable UI
        self.simulator_run_btn.setEnabled(False)
        self.simulator_stop_btn.setEnabled(True)
        self.simulator_progress.setVisible(True)
        self.simulator_progress.setValue(0)
        self.simulator_status_label.setText("Running simulation...")

        # Log simulation start
        self._log_simulator_to_ki(
            "START",
            f"Running {mode} simulation: {strategy_name}, "
            f"data rows: {len(data)}, symbol: {symbol}"
        )

        # Create worker
        self._current_worker = SimulationWorker(
            data=data,
            symbol=symbol,
            strategy_name=strategy_name,
            parameters=params,
            mode=mode,
            opt_trials=self.simulator_opt_trials_spin.value(),
        )
        self._current_worker.finished.connect(self._on_simulation_finished)
        self._current_worker.progress.connect(self._on_simulation_progress)
        self._current_worker.error.connect(self._on_simulation_error)
        self._current_worker.start()

    def _on_stop_simulation(self) -> None:
        """Stop running simulation."""
        if self._current_worker:
            # Signal cancellation; keep reference so thread can exit cleanly
            self._current_worker.cancel()
            self.simulator_status_label.setText("Stopping...")

    def _on_simulation_progress(self, current: int, total: int, best: float) -> None:
        """Update progress bar."""
        pct = int((current / total) * 100) if total > 0 else 0
        self.simulator_progress.setValue(pct)
        self.simulator_status_label.setText(
            f"Trial {current}/{total} | Best: {best:.4f}"
        )

    def _on_simulation_finished(self, result) -> None:
        """Handle simulation completion."""
        from src.core.simulator import SimulationResult, OptimizationRun

        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)

        if isinstance(result, SimulationResult):
            self._simulation_results.append(result)
            self._add_result_to_table(result)
            status_msg = (
                f"Completed: {result.total_trades} trades, "
                f"P&L: {result.total_pnl:.2f}"
            )
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)

        elif isinstance(result, OptimizationRun):
            self._last_optimization_run = result

            # Check for errors
            if result.errors:
                for error in result.errors[:5]:  # Log first 5 errors
                    self._log_simulator_to_ki("ERROR", error)
                if len(result.errors) > 5:
                    self._log_simulator_to_ki(
                        "ERROR", f"... and {len(result.errors) - 5} more errors"
                    )

            # Check if any trials completed
            if result.total_trials == 0:
                error_msg = "No optimization trials completed successfully."
                if result.errors:
                    error_msg += f" First error: {result.errors[0]}"
                self.simulator_status_label.setText(f"Error: {error_msg}")
                self._log_simulator_to_ki("ERROR", error_msg)
                QMessageBox.warning(
                    self, "Optimization Warning",
                    f"No trials completed.\n\n"
                    f"Check KI Logs for error details."
                )
            else:
                # Add best result
                if result.best_result:
                    self._simulation_results.append(result.best_result)
                    self._add_result_to_table(result.best_result)
                # Add top trials
                for trial in result.get_top_n_trials(10):
                    # Create pseudo-result for table
                    self._add_trial_to_table(trial, result.strategy_name)

                status_msg = (
                    f"Optimization complete: {result.total_trials} trials, "
                    f"Best score: {result.best_score:.4f}"
                )
                if result.errors:
                    status_msg += f" ({len(result.errors)} failed)"
                self.simulator_status_label.setText(status_msg)
                self._log_simulator_to_ki("OK", status_msg)

        self.simulator_export_btn.setEnabled(bool(self._simulation_results))
        # Ensure thread is fully stopped before dropping reference
        self._cleanup_simulation_worker(wait_ms=200)

    def _on_simulation_error(self, error_msg: str) -> None:
        """Handle simulation error."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)
        self.simulator_status_label.setText(f"Error: {error_msg}")

        # Log to KI Logs
        self._log_simulator_to_ki("ERROR", f"Simulation failed: {error_msg}")

        QMessageBox.critical(self, "Simulation Error", error_msg)
        self._cleanup_simulation_worker(wait_ms=200)

    def _cleanup_simulation_worker(self, wait_ms: int = 0, cancel: bool = False) -> None:
        """Safely stop and dispose the simulation worker thread.

        Args:
            wait_ms: How long to wait for the thread to finish. 0 = no wait.
            cancel: Whether to request cancellation first.
        """
        worker = self._current_worker
        if not worker:
            return

        if cancel:
            worker.cancel()

        finished = not worker.isRunning()
        if wait_ms and not finished:
            finished = worker.wait(wait_ms)

        if finished:
            worker.deleteLater()
            self._current_worker = None
        else:
            logger.warning("Simulation worker still running after %d ms", wait_ms)

    def _log_simulator_to_ki(self, entry_type: str, message: str) -> None:
        """Log simulator messages to KI Logs tab.

        Uses _add_ki_log_entry from BotDisplayManagerMixin if available.
        """
        prefixed_msg = f"[Simulator] {message}"
        if hasattr(self, '_add_ki_log_entry'):
            self._add_ki_log_entry(entry_type, prefixed_msg)
        else:
            # Fallback to standard logging
            logger.info(f"[{entry_type}] {prefixed_msg}")

    def _calculate_score(self, result) -> int:
        """Calculate performance score from -1000 to +1000.

        Based on P&L% where:
        - +100% profit = +1000 score
        - -100% loss = -1000 score
        """
        pnl_pct = result.total_pnl_pct
        # Clamp to -100% to +100% range, then scale to -1000 to +1000
        score = int(max(-1000, min(1000, pnl_pct * 10)))
        return score

    def _add_result_to_table(self, result) -> None:
        """Add simulation result to results table."""
        row = self.simulator_results_table.rowCount()
        self.simulator_results_table.insertRow(row)

        # Track result for this row (for Show Entry/Exit)
        self._table_row_results.append(result)

        # Format parameters (ALL parameters)
        params_full = ", ".join(
            f"{k}={v}" for k, v in result.parameters.items()
        )

        # Calculate score (-1000 to +1000)
        score = self._calculate_score(result)

        items = [
            result.strategy_name,
            str(result.total_trades),
            f"{result.win_rate * 100:.1f}",
            f"{result.profit_factor:.2f}",
            f"{result.total_pnl:.2f}",  # P&L in Euro (based on 1000€ trades)
            f"{result.total_pnl_pct:.2f}",  # P&L % of invested capital
            f"{result.max_drawdown_pct:.1f}",
            str(score),  # Score instead of Sharpe
            params_full,
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.simulator_results_table.setItem(row, col, item)

            # Color P&L column
            if col == 4:  # P&L € column
                try:
                    pnl = float(value)
                    if pnl > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif pnl < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass

            # Color Score column
            if col == 7:  # Score column
                try:
                    sc = int(value)
                    if sc > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif sc < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass

    def _add_trial_to_table(self, trial, strategy_name: str) -> None:
        """Add optimization trial to results table (no detailed trade data)."""
        row = self.simulator_results_table.rowCount()
        self.simulator_results_table.insertRow(row)

        # No detailed result for trials (only metrics summary)
        self._table_row_results.append(None)

        # Format ALL parameters
        params_full = ", ".join(
            f"{k}={v}" for k, v in trial.parameters.items()
        )

        metrics = trial.metrics
        pnl_pct = metrics.get("total_pnl_pct", 0)

        # Calculate score from P&L% (-1000 to +1000)
        score = int(max(-1000, min(1000, pnl_pct * 10)))

        # P&L in Euro (assuming 1000€ initial capital, pnl_pct is already percentage)
        pnl_euro = pnl_pct * 10  # 1% of 1000€ = 10€

        items = [
            strategy_name,
            str(int(metrics.get("total_trades", 0))),
            f"{metrics.get('win_rate', 0) * 100:.1f}",
            f"{metrics.get('profit_factor', 0):.2f}",
            f"{pnl_euro:.2f}",  # P&L in Euro
            f"{pnl_pct:.2f}",  # P&L %
            f"{metrics.get('max_drawdown_pct', 0):.1f}",
            str(score),  # Score instead of Sharpe
            params_full,
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.simulator_results_table.setItem(row, col, item)

            # Color P&L column
            if col == 4:
                try:
                    pnl = float(value)
                    if pnl > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif pnl < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass

            # Color Score column
            if col == 7:
                try:
                    sc = int(value)
                    if sc > 0:
                        item.setBackground(Qt.GlobalColor.green)
                    elif sc < 0:
                        item.setBackground(Qt.GlobalColor.red)
                except ValueError:
                    pass

    def _on_simulator_result_selected(self) -> None:
        """Handle result selection in table."""
        selected = self.simulator_results_table.selectedItems()
        self.simulator_show_markers_btn.setEnabled(bool(selected))

    def _on_show_simulation_markers(self) -> None:
        """Show entry/exit markers on chart for selected result."""
        selected = self.simulator_results_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        if row >= len(self._table_row_results) or self._table_row_results[row] is None:
            QMessageBox.warning(
                self, "Warning",
                "Keine Detail-Daten für diese Zeile verfügbar.\n\n"
                "Optimization-Trials haben nur Metriken, keine Trade-Details.\n"
                "Nur die 'Best Result'-Zeile hat vollständige Trade-Daten."
            )
            return

        result = self._table_row_results[row]

        # Get chart and clear existing markers
        if hasattr(self, "chart_widget"):
            # Clear previous simulation markers
            if hasattr(self.chart_widget, "clear_bot_markers"):
                self.chart_widget.clear_bot_markers()

            # Add entry/exit points
            for trade in result.trades:
                side = trade.side

                # Entry marker
                if hasattr(self.chart_widget, "add_entry_confirmed"):
                    self.chart_widget.add_entry_confirmed(
                        int(trade.entry_time.timestamp()),
                        trade.entry_price,
                        side,
                        score=0,
                    )

                # Exit marker
                if hasattr(self.chart_widget, "add_exit_marker"):
                    self.chart_widget.add_exit_marker(
                        int(trade.exit_time.timestamp()),
                        trade.exit_price,
                        side,
                        trade.exit_reason,
                    )

            self.simulator_status_label.setText(
                f"Showing {len(result.trades)} trades on chart"
            )

    def _on_clear_simulation_markers(self) -> None:
        """Clear simulation markers from chart."""
        if hasattr(self, "chart_widget") and hasattr(
            self.chart_widget, "clear_bot_markers"
        ):
            self.chart_widget.clear_bot_markers()
            self.simulator_status_label.setText("Markers cleared")

    def _on_export_simulation_xlsx(self) -> None:
        """Export results to Excel file."""
        # Check if table has data (even if _simulation_results is empty)
        table_row_count = self.simulator_results_table.rowCount()
        if table_row_count == 0 and not self._simulation_results:
            QMessageBox.warning(self, "Warning", "No results to export")
            return

        default_name = f"strategy_simulation_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Simulation Results",
            default_name,
            "Excel Files (*.xlsx)",
        )
        if not filepath:
            return

        try:
            from src.core.simulator import export_simulation_results

            # Extract table data from UI
            ui_table_data = self._extract_table_data()

            saved_path = export_simulation_results(
                results=self._simulation_results,
                filepath=filepath,
                optimization_run=self._last_optimization_run,
                ui_table_data=ui_table_data,
            )
            QMessageBox.information(
                self,
                "Export Complete",
                f"Results exported to:\n{saved_path}",
            )
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"openpyxl is required for Excel export.\n\n{e}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _extract_table_data(self) -> list[list[str]]:
        """Extract all data from the results table.

        Returns:
            List of rows, each row is a list of cell values.
        """
        table = self.simulator_results_table
        row_count = table.rowCount()
        col_count = table.columnCount()

        table_data = []
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = table.item(row, col)
                value = item.text() if item else ""
                row_data.append(value)
            table_data.append(row_data)

        return table_data

    def _on_clear_simulation_results(self) -> None:
        """Clear all simulation results."""
        self._simulation_results.clear()
        self._table_row_results.clear()
        self._last_optimization_run = None
        self.simulator_results_table.setRowCount(0)
        self.simulator_export_btn.setEnabled(False)
        self.simulator_show_markers_btn.setEnabled(False)
        self.simulator_status_label.setText("Results cleared")
