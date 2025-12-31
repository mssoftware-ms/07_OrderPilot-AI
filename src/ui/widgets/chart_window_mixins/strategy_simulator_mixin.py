<<<<<<< HEAD
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
    QCheckBox,
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
    QPlainTextEdit,
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
    partial_result = pyqtSignal(object)  # Intermediate result for batch runs
    progress = pyqtSignal(int, int, float)  # current, total, best_score
    strategy_started = pyqtSignal(int, int, str, str)  # index, total, strategy_name, side
    error = pyqtSignal(str)

    def __init__(
        self,
        data,
        symbol: str,
        strategy_name: str,
        parameters: dict,
        mode: str,
        opt_trials: int = 50,
        objective_metric: str = "score",
        entry_only: bool = False,
        entry_lookahead_mode: str = "session_end",
        entry_lookahead_bars: int | None = None,
    ):
        super().__init__()
        self.data = data
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.parameters = parameters
        self.mode = mode  # "manual", "grid", "bayesian"
        self.opt_trials = opt_trials
        self.objective_metric = objective_metric
        self.entry_only = entry_only
        self.entry_lookahead_mode = entry_lookahead_mode
        self.entry_lookahead_bars = entry_lookahead_bars
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
                get_default_parameters,
                load_strategy_params,
                filter_entry_only_params,
            )

            is_all = self.strategy_name == "all"
            strategies = list(StrategyName) if is_all else [StrategyName(self.strategy_name)]
            sides = ["long", "short"] if self.entry_only else ["long"]
            total_runs = len(strategies) * len(sides)

            if self.mode == "manual":
                # Single or batch simulation - needs event loop for async run_simulation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results: list[object] = []
                try:
                    simulator = StrategySimulator(self.data, self.symbol)
                    run_index = 0
                    for strategy in strategies:
                        for side in sides:
                            if self._cancelled:
                                break
                            run_index += 1
                            self.strategy_started.emit(run_index, total_runs, strategy.value, side)
                            if is_all:
                                params = load_strategy_params(strategy.value) or get_default_parameters(strategy)
                            else:
                                params = self.parameters
                            if self.entry_only:
                                params = filter_entry_only_params(strategy, params)
                            result = loop.run_until_complete(
                                simulator.run_simulation(
                                    strategy_name=strategy,
                                    parameters=params,
                                    entry_only=self.entry_only,
                                    entry_side=side,
                                    entry_lookahead_mode=self.entry_lookahead_mode,
                                    entry_lookahead_bars=self.entry_lookahead_bars,
                                )
                            )
                            results.append(result)
                            if is_all:
                                self.partial_result.emit(result)
                        if self._cancelled:
                            break
                finally:
                    loop.close()

                if is_all:
                    self.finished.emit({"batch_done": True, "count": len(results)})
                else:
                    if len(results) == 1:
                        self.finished.emit(results[0])
                    else:
                        self.finished.emit(results)

            elif self.mode in ("grid", "bayesian"):
                # Optimization - optimizers are synchronous and manage their own event loops
                results: list[object] = []
                run_index = 0

                def progress_cb(current, total, best):
                    self.progress.emit(current, total, best)

                for strategy in strategies:
                    for side in sides:
                        if self._cancelled:
                            break

                        run_index += 1
                        self.strategy_started.emit(run_index, total_runs, strategy.value, side)
                        objective_metric = "entry_score" if self.entry_only else self.objective_metric
                        config = OptimizationConfig(
                            strategy_name=strategy,
                            objective_metric=objective_metric,
                            direction="maximize",
                            n_trials=self.opt_trials,
                            entry_only=self.entry_only,
                            entry_side=side,
                            entry_lookahead_mode=self.entry_lookahead_mode,
                            entry_lookahead_bars=self.entry_lookahead_bars,
                        )

                        if self.mode == "bayesian":
                            optimizer = BayesianOptimizer(self.data, self.symbol, config)
                        else:
                            optimizer = GridSearchOptimizer(self.data, self.symbol, config)

                        # Keep reference so we can cancel from UI thread
                        self._optimizer = optimizer

                        # Optimizers are now synchronous
                        if self.mode == "grid":
                            result = optimizer.optimize(
                                progress_callback=progress_cb,
                                max_combinations=self.opt_trials,
                            )
                        else:
                            result = optimizer.optimize(progress_callback=progress_cb)
                        results.append(result)
                        if is_all:
                            self.partial_result.emit(result)
                    if self._cancelled:
                        break

                if is_all:
                    self.finished.emit({"batch_done": True, "count": len(results)})
                else:
                    if len(results) == 1:
                        self.finished.emit(results[0])
                    else:
                        self.finished.emit(results)

        except Exception as e:
            logger.error("Simulation failed: %s", e, exc_info=True)
            self.error.emit(str(e))
        finally:
            self._optimizer = None


class StrategySimulatorMixin:
    """Mixin providing Strategy Simulator tab for ChartWindow."""

    # Storage for simulation results
    _simulation_results: list = []
    _last_optimization_run: object = None
    _current_worker: SimulationWorker | None = None
    _current_sim_strategy_name: str | None = None
    _current_sim_strategy_index: int | None = None
    _current_sim_strategy_total: int | None = None
    _current_sim_strategy_side: str | None = None
    _current_simulation_mode: str | None = None
    _current_objective_metric: str | None = None
    _current_entry_only: bool = False
    _all_run_active: bool = False
    _all_run_restore_index: int | None = None
    _entry_marker_min_score: float = 50.0
    _simulator_splitter: QSplitter | None = None  # Splitter for save/restore

    def _create_strategy_simulator_tab(self) -> QWidget:
        """Create the Strategy Simulator tab widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Splitter for controls and results
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent collapse
        splitter.setHandleWidth(6)  # Make handle visible and draggable
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555;
            }
            QSplitter::handle:hover {
                background-color: #777;
            }
            QSplitter::handle:pressed {
                background-color: #999;
            }
        """)

        # Left: Controls (20% wider: 336*1.2=403, 264*1.2=317)
        controls = self._create_simulator_controls()
        controls.setMaximumWidth(600)  # Allow wider for drag
        controls.setMinimumWidth(320)  # 20% wider minimum
        splitter.addWidget(controls)

        # Right: Results
        results = self._create_simulator_results()
        splitter.addWidget(results)

        # Store reference for state save/restore
        self._simulator_splitter = splitter

        # Set initial sizes (20% wider: 403px for controls)
        splitter.setSizes([403, 600])

        # Restore saved splitter state if available
        self._restore_simulator_splitter_state()

        layout.addWidget(splitter)

        # Initialize
        self._simulation_results = []
        self._last_optimization_run = None
        self._current_sim_strategy_name = None
        self._current_sim_strategy_index = None
        self._current_sim_strategy_total = None
        self._current_sim_strategy_side = None
        self._current_simulation_mode = None
        self._current_objective_metric = None
        self._current_entry_only = False
        self._all_run_active = False
        self._all_run_restore_index = None
        self._on_simulator_strategy_changed(0)
        self._on_entry_lookahead_changed()

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
            "Bollinger Squeeze",
            "Trend Pullback",
            "Opening Range",
            "Regime Hybrid",
            "ALL",
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

        # Optimization target
        objective_layout = QHBoxLayout()
        objective_layout.addWidget(QLabel("Optimize:"))
        self.simulator_opt_metric_combo = QComboBox()
        self.simulator_opt_metric_combo.addItem("Score (P&L)", "score")
        self.simulator_opt_metric_combo.addItem("Entry Score", "entry_score")
        self.simulator_opt_metric_combo.addItem("P&L %", "total_pnl_pct")
        self.simulator_opt_metric_combo.addItem("Profit Factor", "profit_factor")
        self.simulator_opt_metric_combo.addItem("Sharpe Ratio", "sharpe_ratio")
        self.simulator_opt_metric_combo.addItem("Win Rate", "win_rate")
        self.simulator_opt_metric_combo.addItem("Max Drawdown", "max_drawdown_pct")
        objective_layout.addWidget(self.simulator_opt_metric_combo)
        opt_layout.addLayout(objective_layout)

        self.simulator_entry_only_checkbox = QCheckBox("Entry Only (Long+Short)")
        self.simulator_entry_only_checkbox.setToolTip(
            "Simuliert nur Einstiege (Lookahead über Einstellung unten)."
        )
        self.simulator_entry_only_checkbox.toggled.connect(self._on_entry_only_toggled)
        opt_layout.addWidget(self.simulator_entry_only_checkbox)

        entry_lookahead_layout = QHBoxLayout()
        entry_lookahead_layout.addWidget(QLabel("Entry Lookahead:"))
        self.simulator_entry_lookahead_combo = QComboBox()
        self.simulator_entry_lookahead_combo.addItem(
            "Session End (Equities 22:00 CET)", "session_end"
        )
        self.simulator_entry_lookahead_combo.addItem(
            "Until Counter-Signal", "counter_signal"
        )
        self.simulator_entry_lookahead_combo.addItem("Fixed Bars", "fixed_bars")
        self.simulator_entry_lookahead_combo.currentIndexChanged.connect(
            self._on_entry_lookahead_changed
        )
        entry_lookahead_layout.addWidget(self.simulator_entry_lookahead_combo)
        opt_layout.addLayout(entry_lookahead_layout)

        entry_lookahead_bars_layout = QHBoxLayout()
        entry_lookahead_bars_layout.addWidget(QLabel("Lookahead Bars:"))
        self.simulator_entry_lookahead_bars = QSpinBox()
        self.simulator_entry_lookahead_bars.setRange(1, 10000)
        self.simulator_entry_lookahead_bars.setValue(30)
        self.simulator_entry_lookahead_bars.setToolTip(
            "Nur aktiv bei Fixed Bars"
        )
        entry_lookahead_bars_layout.addWidget(self.simulator_entry_lookahead_bars)
        opt_layout.addLayout(entry_lookahead_bars_layout)

        # Trials spinner
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Trials:"))
        self.simulator_opt_trials_spin = QSpinBox()
        self.simulator_opt_trials_spin.setRange(10, 2_147_483_647)
        self.simulator_opt_trials_spin.setValue(50)
        trials_layout.addWidget(self.simulator_opt_trials_spin)
        opt_layout.addLayout(trials_layout)

        self.simulator_trials_hint_label = QLabel("")
        self.simulator_trials_hint_label.setWordWrap(True)
        opt_layout.addWidget(self.simulator_trials_hint_label)

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

        self.simulator_log_view = QPlainTextEdit()
        self.simulator_log_view.setReadOnly(True)
        self.simulator_log_view.setMaximumBlockCount(500)
        self.simulator_log_view.setPlaceholderText("Simulation log...")
        layout.addWidget(self.simulator_log_view)

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
        self.simulator_results_table.setColumnCount(10)
        self.simulator_results_table.setHorizontalHeaderLabels([
            "Strategy",
            "Trades",
            "Win %",
            "PF",
            "P&L €",
            "P&L %",
            "DD %",
            "Score",
            "Objective",
            "Parameters",
        ])
        # Set column resize modes - last column (Parameters) gets extra space
        header = self.simulator_results_table.horizontalHeader()
        for i in range(9):  # First 9 columns: fixed width
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Parameters column: stretches to fill remaining space
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        self.simulator_results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.simulator_results_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.simulator_results_table.itemSelectionChanged.connect(
            self._on_simulator_result_selected
        )
        self.simulator_results_table.setSortingEnabled(True)
        header.setSortIndicatorShown(True)
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

        self.simulator_show_entry_points_checkbox = QCheckBox("View Points")
        self.simulator_show_entry_points_checkbox.setToolTip(
            "Entry-Only: zeigt Entry-Punkte der ausgewählten Zeile"
        )
        self.simulator_show_entry_points_checkbox.toggled.connect(
            self._on_toggle_entry_points
        )
        buttons_layout.addWidget(self.simulator_show_entry_points_checkbox)

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
        from src.core.simulator import StrategyName

        if self._is_all_strategy_selected() and not self._all_run_active:
            self.simulator_params_group.setEnabled(False)
            self._update_trials_hint(None)
            return

        self.simulator_params_group.setEnabled(True)
        strategy_map = {
            0: StrategyName.BREAKOUT,
            1: StrategyName.MOMENTUM,
            2: StrategyName.MEAN_REVERSION,
            3: StrategyName.TREND_FOLLOWING,
            4: StrategyName.SCALPING,
            5: StrategyName.BOLLINGER_SQUEEZE,
            6: StrategyName.TREND_PULLBACK,
            7: StrategyName.OPENING_RANGE,
            8: StrategyName.REGIME_HYBRID,
        }
        strategy = strategy_map.get(index, StrategyName.BREAKOUT)
        self._populate_simulator_parameter_widgets(strategy)
        self._update_trials_hint(strategy)

        if self._all_run_active:
            self.simulator_params_group.setEnabled(False)

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

    def _apply_params_to_widgets(self, params: dict[str, Any]) -> None:
        """Apply parameter values to the current widgets."""
        for param_name, value in params.items():
            widget = self._simulator_param_widgets.get(param_name)
            if widget and isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)

    def _estimate_grid_combinations(self, strategy) -> int:
        """Estimate grid combinations using the same coarse steps as grid search."""
        from src.core.simulator import get_strategy_parameters

        param_config = get_strategy_parameters(strategy)
        total = 1
        for param_def in param_config.parameters:
            values = self._get_grid_values_for_param(param_def)
            total *= len(values)
        return total

    def _get_grid_values_for_param(self, param_def) -> list[Any]:
        if param_def.param_type == "bool":
            return [True, False]

        if param_def.min_value is None or param_def.max_value is None:
            return [param_def.default]

        step = param_def.step or (1 if param_def.param_type == "int" else 0.1)
        grid_step = step * 2
        values = []
        current = param_def.min_value
        while current <= param_def.max_value:
            if param_def.param_type == "int":
                values.append(int(current))
            else:
                values.append(round(current, 4))
            current += grid_step

        for value in (param_def.min_value, param_def.max_value, param_def.default):
            if value not in values:
                values.append(value)
        return sorted(values)

    def _update_trials_hint(self, strategy) -> None:
        """Update suggested trials label."""
        if strategy is None:
            self.simulator_trials_hint_label.setText(
                "Suggested Trials: per-strategy (ALL)"
            )
            self.simulator_opt_trials_spin.setToolTip(
                "Suggested Trials: per-strategy (ALL)"
            )
            return
        try:
            total = self._estimate_grid_combinations(strategy)
            suggested = min(total, 1000)
            self.simulator_trials_hint_label.setText(
                f"Suggested Trials (grid): {suggested} / {total} combos"
            )
            self.simulator_opt_trials_spin.setToolTip(
                f"Suggested (grid): {suggested} of {total} combos"
            )
        except Exception:
            self.simulator_trials_hint_label.setText("")

    def _get_selected_objective_metric(self) -> str:
        """Get selected optimization objective metric."""
        if self._is_entry_only_selected():
            return "entry_score"
        if hasattr(self, "simulator_opt_metric_combo"):
            data = self.simulator_opt_metric_combo.currentData()
            if data:
                return str(data)
        return "score"

    def _get_objective_label(self, metric: str) -> str:
        labels = {
            "score": "Score",
            "entry_score": "Entry Score",
            "total_pnl_pct": "P&L %",
            "profit_factor": "PF",
            "sharpe_ratio": "Sharpe",
            "win_rate": "Win %",
            "max_drawdown_pct": "Max DD",
        }
        return labels.get(metric, metric)

    def _is_entry_only_selected(self) -> bool:
        return bool(
            hasattr(self, "simulator_entry_only_checkbox")
            and self.simulator_entry_only_checkbox.isChecked()
        )

    def _on_entry_only_toggled(self, checked: bool) -> None:
        if not hasattr(self, "simulator_opt_metric_combo"):
            return
        if checked:
            idx = self.simulator_opt_metric_combo.findData("entry_score")
            if idx >= 0:
                self.simulator_opt_metric_combo.setCurrentIndex(idx)
            self.simulator_opt_metric_combo.setEnabled(False)
        else:
            self.simulator_opt_metric_combo.setEnabled(True)
        self._on_entry_lookahead_changed()

    def _on_entry_lookahead_changed(self) -> None:
        if not hasattr(self, "simulator_entry_lookahead_combo"):
            return
        enabled = self._is_entry_only_selected()
        mode = self.simulator_entry_lookahead_combo.currentData()
        is_fixed = mode == "fixed_bars"
        self.simulator_entry_lookahead_combo.setEnabled(enabled)
        if hasattr(self, "simulator_entry_lookahead_bars"):
            self.simulator_entry_lookahead_bars.setEnabled(enabled and is_fixed)

    def _get_entry_lookahead_mode(self) -> str:
        if not hasattr(self, "simulator_entry_lookahead_combo"):
            return "session_end"
        data = self.simulator_entry_lookahead_combo.currentData()
        return data or "session_end"

    def _get_entry_lookahead_bars(self) -> int | None:
        if not hasattr(self, "simulator_entry_lookahead_bars"):
            return None
        if self._get_entry_lookahead_mode() != "fixed_bars":
            return None
        return int(self.simulator_entry_lookahead_bars.value())

    def _append_simulator_log(self, message: str) -> None:
        if not hasattr(self, "simulator_log_view"):
            return
        if message:
            self.simulator_log_view.appendPlainText(message)

    def _format_entry_points(self, points: list[tuple] | None) -> str:
        if not points:
            return ""
        formatted = []
        for item in points:
            if len(item) == 3:
                price, ts, _score = item
            else:
                price, ts = item
            formatted.append(f"{price:.3f}/{ts.strftime('%H:%M:%S')}")
        return ";".join(formatted)

    def _normalize_param_value(self, value: Any) -> Any:
        if isinstance(value, float):
            return round(value, 8)
        if isinstance(value, (list, tuple)):
            return tuple(self._normalize_param_value(v) for v in value)
        if isinstance(value, dict):
            return tuple(
                (k, self._normalize_param_value(v))
                for k, v in sorted(value.items())
            )
        return value

    def _make_param_fingerprint(
        self,
        strategy_name: str,
        params: dict[str, Any],
        entry_side: str | None = None,
    ) -> tuple:
        items = tuple(
            (k, self._normalize_param_value(v))
            for k, v in sorted(params.items())
        )
        return (strategy_name, entry_side or "", items)

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

        if self._is_all_strategy_selected():
            self.simulator_status_label.setText(
                "ALL selected: parameters are not used for batch runs"
            )
            return

        strategy_map = {
            0: StrategyName.BREAKOUT,
            1: StrategyName.MOMENTUM,
            2: StrategyName.MEAN_REVERSION,
            3: StrategyName.TREND_FOLLOWING,
            4: StrategyName.SCALPING,
            5: StrategyName.BOLLINGER_SQUEEZE,
            6: StrategyName.TREND_PULLBACK,
            7: StrategyName.OPENING_RANGE,
            8: StrategyName.REGIME_HYBRID,
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
        from src.core.simulator import save_strategy_params_to_path

        strategy_name = self._get_simulator_strategy_name()
        params = self._get_simulator_parameters()

        # Get symbol from current chart if available
        symbol = None
        if hasattr(self, "current_symbol"):
            symbol = self.current_symbol

        default_dir = Path("config/strategy_params")
        default_name = f"{strategy_name}_params.json"
        default_path = default_dir / default_name
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Strategy Parameters",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )
        if not filepath:
            return

        path = Path(filepath)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        try:
            saved_path = save_strategy_params_to_path(
                filepath=path,
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
                f"File: {saved_path}",
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
        if self._is_all_strategy_selected():
            return "all"

        strategy_map = {
            0: "breakout",
            1: "momentum",
            2: "mean_reversion",
            3: "trend_following",
            4: "scalping",
            5: "bollinger_squeeze",
            6: "trend_pullback",
            7: "opening_range",
            8: "regime_hybrid",
        }
        return strategy_map.get(
            self.simulator_strategy_combo.currentIndex(), "breakout"
        )

    def _get_strategy_index_by_name(self, strategy_name: str) -> int | None:
        """Get combo index for a strategy name."""
        strategy_map = {
            "breakout": 0,
            "momentum": 1,
            "mean_reversion": 2,
            "trend_following": 3,
            "scalping": 4,
            "bollinger_squeeze": 5,
            "trend_pullback": 6,
            "opening_range": 7,
            "regime_hybrid": 8,
        }
        return strategy_map.get(strategy_name)

    def _is_all_strategy_selected(self) -> bool:
        """Check if ALL is selected in strategy dropdown."""
        return self.simulator_strategy_combo.currentText().strip().upper() == "ALL"

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
        entry_only = self._is_entry_only_selected()
        entry_lookahead_mode = self._get_entry_lookahead_mode()
        entry_lookahead_bars = self._get_entry_lookahead_bars()
        objective_metric = "entry_score" if entry_only else self._get_selected_objective_metric()
        self._current_objective_metric = objective_metric
        self._current_entry_only = entry_only

        if hasattr(self, "simulator_log_view"):
            self.simulator_log_view.clear()

        if self._is_all_strategy_selected():
            self._all_run_active = True
            self._all_run_restore_index = self.simulator_strategy_combo.currentIndex()
            self.simulator_params_group.setEnabled(False)
            self.simulator_strategy_combo.setEnabled(False)

        # Determine mode
        mode_id = self.simulator_opt_mode_group.checkedId()
        mode_map = {0: "manual", 1: "grid", 2: "bayesian"}
        mode = mode_map.get(mode_id, "manual")
        self._current_simulation_mode = mode
        if entry_only and mode == "manual" and self.simulator_opt_trials_spin.value() > 1:
            self._append_simulator_log(
                "Entry-Only: Manual ignores trials. Switch to Grid/Bayesian to use trials."
            )

        # Disable UI
        self.simulator_run_btn.setEnabled(False)
        self.simulator_stop_btn.setEnabled(True)
        self.simulator_progress.setVisible(True)
        self.simulator_progress.setValue(0)
        self.simulator_status_label.setText("Running simulation...")

        objective_label = self._get_objective_label(objective_metric)
        entry_label = "entry-only" if entry_only else "full"
        side_label = "long+short" if entry_only else "long"

        # Log simulation start
        self._log_simulator_to_ki(
            "START",
            f"Running {mode} simulation: {strategy_name}, "
            f"mode: {entry_label} ({side_label}), objective: {objective_label}, "
            f"lookahead: {entry_lookahead_mode}, "
            f"trials: {self.simulator_opt_trials_spin.value()}, "
            f"data rows: {len(data)}, symbol: {symbol}"
        )
        self._append_simulator_log(
            f"START | {mode} | {strategy_name} | {entry_label} ({side_label}) | "
            f"{objective_label} | lookahead={entry_lookahead_mode} | "
            f"trials={self.simulator_opt_trials_spin.value()}"
        )

        # Create worker
        self._current_worker = SimulationWorker(
            data=data,
            symbol=symbol,
            strategy_name=strategy_name,
            parameters=params,
            mode=mode,
            opt_trials=self.simulator_opt_trials_spin.value(),
            objective_metric=objective_metric,
            entry_only=entry_only,
            entry_lookahead_mode=entry_lookahead_mode,
            entry_lookahead_bars=entry_lookahead_bars,
        )
        self._current_worker.finished.connect(self._on_simulation_finished)
        self._current_worker.partial_result.connect(self._on_simulation_partial_result)
        self._current_worker.progress.connect(self._on_simulation_progress)
        self._current_worker.strategy_started.connect(self._on_simulation_strategy_started)
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
        strategy_prefix = ""
        if self._current_sim_strategy_name:
            index = self._current_sim_strategy_index or 1
            total_strategies = self._current_sim_strategy_total or 1
            display_name = self._get_strategy_display_name(self._current_sim_strategy_name)
            if self._current_entry_only and self._current_sim_strategy_side:
                side_label = self._current_sim_strategy_side.upper()
                strategy_prefix = f"{index}/{total_strategies} {display_name} {side_label} | "
            else:
                strategy_prefix = f"{index}/{total_strategies} {display_name} | "
        objective_label = self._get_objective_label(self._current_objective_metric or "score")
        self.simulator_status_label.setText(
            f"{strategy_prefix}Trial {current}/{total} | Best {objective_label}: {best:.4f}"
        )
        log_prefix = strategy_prefix.replace(" | ", " ").strip()
        self._append_simulator_log(
            f"{log_prefix}Trial {current}/{total} | Best {objective_label}: {best:.4f}".strip()
        )

    def _on_simulation_finished(self, result) -> None:
        """Handle simulation completion."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)
        self._finalize_all_run()

        if isinstance(result, dict) and result.get("batch_done"):
            count = result.get("count", 0)
            label = "runs" if self._current_entry_only else "strategies"
            status_msg = f"Completed batch run: {count} {label}"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
            self._append_simulator_log(status_msg)
            self._append_simulator_log(status_msg)
        elif isinstance(result, list):
            for item in result:
                self._handle_simulation_result(item)

            label = "runs" if self._current_entry_only else "strategies"
            status_msg = f"Completed batch run: {len(result)} {label}"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
        else:
            self._handle_simulation_result(result)

        self.simulator_export_btn.setEnabled(bool(self._simulation_results))
        # Ensure thread is fully stopped before dropping reference
        self._cleanup_simulation_worker(wait_ms=200)

    def _handle_simulation_result(self, result) -> None:
        """Handle a single simulation or optimization result."""
        from src.core.simulator import SimulationResult, OptimizationRun

        if isinstance(result, SimulationResult):
            self._simulation_results.append(result)
            if result.entry_only:
                objective_label = self._get_objective_label("entry_score")
            elif self._current_simulation_mode == "manual":
                objective_label = "Manual"
            else:
                objective_label = self._get_objective_label(self._current_objective_metric or "score")
            self._add_result_to_table(result, objective_label=objective_label)
            if result.entry_only:
                entry_score = result.entry_score or 0.0
                status_msg = (
                    f"Entry-Only: {result.entry_count} entries, "
                    f"Score: {entry_score:.1f}"
                )
            else:
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
                seen_params: set[tuple] = set()
                if result.best_result:
                    self._simulation_results.append(result.best_result)
                    objective_label = self._get_objective_label(result.objective_metric)
                    self._add_result_to_table(
                        result.best_result,
                        objective_label=objective_label,
                        entry_side=result.entry_side,
                    )
                    best_side = (
                        result.best_result.entry_side
                        if getattr(result.best_result, "entry_only", False)
                        else None
                    )
                    seen_params.add(
                        self._make_param_fingerprint(
                            result.strategy_name,
                            result.best_result.parameters,
                            best_side,
                        )
                    )
                # Add top trials
                for trial in result.get_top_n_trials(10):
                    # Create pseudo-result for table
                    objective_label = self._get_objective_label(result.objective_metric)
                    trial_side = trial.entry_side if result.entry_only else None
                    fingerprint = self._make_param_fingerprint(
                        result.strategy_name, trial.parameters, trial_side
                    )
                    if fingerprint in seen_params:
                        continue
                    seen_params.add(fingerprint)
                    self._add_trial_to_table(
                        trial,
                        result.strategy_name,
                        objective_label=objective_label,
                        entry_side=result.entry_side,
                    )

                status_msg = (
                    f"Optimization complete: {result.total_trials} trials, "
                    f"Best score: {result.best_score:.4f}"
                )
                if result.entry_only:
                    status_msg += f" ({result.entry_side.upper()})"
                if result.errors:
                    status_msg += f" ({len(result.errors)} failed)"
                self.simulator_status_label.setText(status_msg)
                self._log_simulator_to_ki("OK", status_msg)
                self._append_simulator_log(status_msg)

    def _on_simulation_error(self, error_msg: str) -> None:
        """Handle simulation error."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)
        self.simulator_status_label.setText(f"Error: {error_msg}")
        self._append_simulator_log(f"ERROR: {error_msg}")
        self._finalize_all_run()

        # Log to KI Logs
        self._log_simulator_to_ki("ERROR", f"Simulation failed: {error_msg}")

        QMessageBox.critical(self, "Simulation Error", error_msg)
        self._cleanup_simulation_worker(wait_ms=200)

    def _on_simulation_partial_result(self, result) -> None:
        """Handle partial results for batch runs."""
        self._handle_simulation_result(result)

    def _on_simulation_strategy_started(
        self,
        index: int,
        total: int,
        strategy_name: str,
        side: str,
    ) -> None:
        """Update UI when a strategy run starts."""
        self._current_sim_strategy_name = strategy_name
        self._current_sim_strategy_index = index
        self._current_sim_strategy_total = total
        self._current_sim_strategy_side = side
        if self._all_run_active:
            combo_index = self._get_strategy_index_by_name(strategy_name)
            if combo_index is not None:
                self.simulator_strategy_combo.setCurrentIndex(combo_index)
            try:
                from src.core.simulator import StrategyName, get_default_parameters, load_strategy_params

                strategy_enum = StrategyName(strategy_name)
                saved_params = load_strategy_params(strategy_name)
                seed_params = saved_params or get_default_parameters(strategy_enum)
                self._apply_params_to_widgets(seed_params)
                seed_source = "saved" if saved_params else "default"
                self._append_simulator_log(
                    f"Seed params: {seed_source} ({strategy_name})"
                )
            except Exception:
                pass
        display_name = self._get_strategy_display_name(strategy_name)
        mode = self._current_simulation_mode or "manual"
        side_label = ""
        if self._current_entry_only and side:
            side_label = f" {side.upper()}"
        status_msg = f"Running {index}/{total}: {display_name}{side_label} ({mode})"
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("INFO", status_msg)
        self._append_simulator_log(status_msg)

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

    def _finalize_all_run(self) -> None:
        """Restore UI state after ALL batch runs."""
        if not self._all_run_active:
            return
        self._all_run_active = False
        self.simulator_strategy_combo.setEnabled(True)
        if self._all_run_restore_index is not None:
            self.simulator_strategy_combo.setCurrentIndex(self._all_run_restore_index)
        self._all_run_restore_index = None
        self.simulator_params_group.setEnabled(not self._is_all_strategy_selected())

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
        if getattr(result, "entry_only", False):
            entry_score = result.entry_score or 0.0
            return int(round(entry_score))
        pnl_pct = result.total_pnl_pct
        # Clamp to -100% to +100% range, then scale to -1000 to +1000
        score = int(max(-1000, min(1000, pnl_pct * 10)))
        return score

    def _add_result_to_table(
        self,
        result,
        objective_label: str | None = None,
        entry_side: str | None = None,
    ) -> None:
        """Add simulation result to results table."""
        table = self.simulator_results_table
        was_sorting = table.isSortingEnabled()
        if was_sorting:
            table.setSortingEnabled(False)

        row = table.rowCount()
        table.insertRow(row)

        # Format parameters (ALL parameters)
        params_full = ", ".join(
            f"{k}={v}" for k, v in result.parameters.items()
        )

        # Calculate score (-1000 to +1000)
        score = self._calculate_score(result)

        if objective_label is None:
            if getattr(result, "entry_only", False):
                objective_label = self._get_objective_label("entry_score")
            elif self._current_simulation_mode == "manual":
                objective_label = "Manual"
            else:
                objective_label = self._get_objective_label(self._current_objective_metric or "score")

        if getattr(result, "entry_only", False):
            ls_value = entry_side or getattr(result, "entry_side", None) or "long"
            entry_points = getattr(result, "entry_points", None)
            entry_display = self._format_entry_points(entry_points)
            if not entry_display:
                entry_price = getattr(result, "entry_best_price", None)
                entry_time = getattr(result, "entry_best_time", None)
                if entry_price is not None and entry_time is not None:
                    entry_display = f"{entry_price:.3f}/{entry_time.strftime('%H:%M:%S')}"
            prefix_items = [f"LS={ls_value}"]
            if entry_display:
                prefix_items.append(f"EP={entry_display}")
            prefix = ", ".join(prefix_items)
            params_full = f"{prefix}, {params_full}" if params_full else prefix

        items = [
            result.strategy_name,
            str(result.total_trades),
            f"{result.win_rate * 100:.1f}",
            f"{result.profit_factor:.2f}",
            f"{result.total_pnl:.2f}",  # P&L in Euro (based on 1000€ trades)
            f"{result.total_pnl_pct:.2f}",  # P&L % of invested capital
            f"{result.max_drawdown_pct:.1f}",
            str(score),  # Score instead of Sharpe
            objective_label,
            params_full,
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(str(value))
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, result)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

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

        if was_sorting:
            table.setSortingEnabled(True)

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

    def _add_trial_to_table(
        self,
        trial,
        strategy_name: str,
        objective_label: str | None = None,
        entry_side: str | None = None,
    ) -> None:
        """Add optimization trial to results table (no detailed trade data)."""
        table = self.simulator_results_table
        was_sorting = table.isSortingEnabled()
        if was_sorting:
            table.setSortingEnabled(False)

        row = table.rowCount()
        table.insertRow(row)

        # Format ALL parameters
        params_full = ", ".join(
            f"{k}={v}" for k, v in trial.parameters.items()
        )

        metrics = trial.metrics
        pnl_pct = metrics.get("total_pnl_pct", 0)

        # Calculate score from P&L% (-1000 to +1000)
        entry_score = metrics.get("entry_score")
        if entry_score is not None:
            score = int(round(entry_score))
        else:
            score = int(max(-1000, min(1000, pnl_pct * 10)))

        if objective_label is None:
            objective_label = self._get_objective_label(self._current_objective_metric or "score")

        ls_value = entry_side or "long"
        entry_display = ""
        if entry_score is not None:
            entry_points = metrics.get("entry_points")
            if entry_points:
                entry_display = str(entry_points)
            else:
                entry_price = metrics.get("entry_best_price")
                entry_time = metrics.get("entry_best_time")
                if entry_price is not None and entry_time:
                    try:
                        entry_display = f"{float(entry_price):.3f}/{entry_time}"
                    except (TypeError, ValueError):
                        entry_display = f"{entry_price}/{entry_time}"
            prefix_items = [f"LS={ls_value}"]
            if entry_display:
                prefix_items.append(f"EP={entry_display}")
            prefix = ", ".join(prefix_items)
            params_full = f"{prefix}, {params_full}" if params_full else prefix

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
            objective_label,
            params_full,
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(str(value))
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, None)
                item.setData(Qt.ItemDataRole.UserRole + 1, trial)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

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

        if was_sorting:
            table.setSortingEnabled(True)

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
        if not selected:
            self.simulator_show_markers_btn.setEnabled(False)
            if hasattr(self, "simulator_show_entry_points_checkbox"):
                if self.simulator_show_entry_points_checkbox.isChecked():
                    self._update_entry_points_from_selection()
            return

        row = selected[0].row()
        result = self._get_result_from_row(row)
        self.simulator_show_markers_btn.setEnabled(result is not None)
        if hasattr(self, "simulator_show_entry_points_checkbox"):
            if self.simulator_show_entry_points_checkbox.isChecked():
                self._update_entry_points_from_selection()

    def _on_toggle_entry_points(self, checked: bool) -> None:
        if not hasattr(self, "chart_widget"):
            return
        if checked:
            self._update_entry_points_from_selection()
        else:
            if hasattr(self.chart_widget, "clear_bot_markers"):
                self.chart_widget.clear_bot_markers()

    def _update_entry_points_from_selection(self) -> None:
        """Show entry-only points for the selected row (if available)."""
        if not hasattr(self, "chart_widget"):
            return
        selected = self.simulator_results_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        result = self._get_result_from_row(row)
        entry_points = []
        side = "long"
        default_score = 0.0
        if result and getattr(result, "entry_only", False):
            entry_points = getattr(result, "entry_points", None) or []
            side = getattr(result, "entry_side", "long")
            default_score = float(result.entry_score or 0.0)
        else:
            trial = self._get_trial_from_row(row)
            if trial and getattr(trial, "entry_points", None):
                entry_points = getattr(trial, "entry_points") or []
                side = getattr(trial, "entry_side", "long")
                try:
                    default_score = float(trial.score)
                except Exception:
                    default_score = 0.0

        if not entry_points:
            if hasattr(self.chart_widget, "clear_bot_markers"):
                self.chart_widget.clear_bot_markers()
            self.simulator_status_label.setText("No entry-only data for selected row")
            return

        if hasattr(self.chart_widget, "clear_bot_markers"):
            self.chart_widget.clear_bot_markers()

        min_score = getattr(self, "_entry_marker_min_score", 50.0)
        shown = 0
        if hasattr(self.chart_widget, "add_entry_confirmed"):
            for item in entry_points:
                if len(item) == 3:
                    price, ts, entry_score = item
                else:
                    price, ts = item
                    entry_score = default_score
                try:
                    score_val = float(entry_score)
                except Exception:
                    score_val = 0.0
                if score_val < min_score:
                    continue
                self.chart_widget.add_entry_confirmed(ts, float(price), side, score_val)
                shown += 1

        if shown == 0:
            self.simulator_status_label.setText(
                f"No entry points with score >= {min_score:.0f}"
            )

        # Zoom / refresh view if supported
        if hasattr(self.chart_widget, "zoom_to_fit_all"):
            try:
                self.chart_widget.zoom_to_fit_all()
            except Exception:
                pass
        elif hasattr(self.chart_widget, "zoom_to_fit"):
            try:
                self.chart_widget.zoom_to_fit()
            except Exception:
                pass

    def _on_show_simulation_markers(self) -> None:
        """Show entry/exit markers on chart for selected result."""
        selected = self.simulator_results_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        result = self._get_result_from_row(row)
        if result is None:
            QMessageBox.warning(
                self, "Warning",
                "Keine Detail-Daten für diese Zeile verfügbar.\n\n"
                "Optimization-Trials haben nur Metriken, keine Trade-Details.\n"
                "Nur die 'Best Result'-Zeile hat vollständige Trade-Daten."
            )
            return

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
        self._last_optimization_run = None
        self.simulator_results_table.setRowCount(0)
        self.simulator_export_btn.setEnabled(False)
        self.simulator_show_markers_btn.setEnabled(False)
        self.simulator_status_label.setText("Results cleared")

    def _get_result_from_row(self, row: int) -> object | None:
        """Get the SimulationResult stored on the row, if any."""
        item = self.simulator_results_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _get_trial_from_row(self, row: int) -> object | None:
        """Get OptimizationTrial stored on the row, if any."""
        item = self.simulator_results_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole + 1)

    def _get_strategy_display_name(self, strategy_name: str) -> str:
        """Get display name for a strategy."""
        from src.core.simulator import StrategyName

        try:
            return StrategyName.display_names().get(strategy_name, strategy_name)
        except Exception:
            return strategy_name

    def _restore_simulator_splitter_state(self) -> None:
        """Restore the Strategy Simulator splitter state from settings."""
        if not hasattr(self, 'settings') or not hasattr(self, '_simulator_splitter'):
            return

        try:
            splitter_state = self.settings.value("StrategySimulator/splitterState")
            if splitter_state:
                self._simulator_splitter.restoreState(splitter_state)
                logger.debug("Restored Strategy Simulator splitter state")
        except Exception as e:
            logger.debug(f"Could not restore splitter state: {e}")

    def _save_simulator_splitter_state(self) -> None:
        """Save the Strategy Simulator splitter state to settings."""
        if not hasattr(self, 'settings') or not hasattr(self, '_simulator_splitter'):
            return

        try:
            self.settings.setValue(
                "StrategySimulator/splitterState",
                self._simulator_splitter.saveState()
            )
            logger.debug("Saved Strategy Simulator splitter state")
        except Exception as e:
            logger.debug(f"Could not save splitter state: {e}")
=======
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
    partial_result = pyqtSignal(object)  # Intermediate result for batch runs
    progress = pyqtSignal(int, int, float)  # current, total, best_score
    strategy_started = pyqtSignal(int, int, str)  # index, total, strategy_name
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
                get_default_parameters,
            )

            is_all = self.strategy_name == "all"
            strategies = list(StrategyName) if is_all else [StrategyName(self.strategy_name)]

            if self.mode == "manual":
                # Single or batch simulation - needs event loop for async run_simulation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results: list[object] = []
                try:
                    simulator = StrategySimulator(self.data, self.symbol)
                    for idx, strategy in enumerate(strategies, start=1):
                        if self._cancelled:
                            break
                        self.strategy_started.emit(idx, len(strategies), strategy.value)
                        params = (
                            get_default_parameters(strategy)
                            if is_all
                            else self.parameters
                        )
                        result = loop.run_until_complete(
                            simulator.run_simulation(
                                strategy_name=strategy,
                                parameters=params,
                            )
                        )
                        results.append(result)
                        if is_all:
                            self.partial_result.emit(result)
                finally:
                    loop.close()

                if is_all:
                    self.finished.emit({"batch_done": True, "count": len(results)})
                else:
                    self.finished.emit(results[0] if results else [])

            elif self.mode in ("grid", "bayesian"):
                # Optimization - optimizers are synchronous and manage their own event loops
                results: list[object] = []

                def progress_cb(current, total, best):
                    self.progress.emit(current, total, best)

                for idx, strategy in enumerate(strategies, start=1):
                    if self._cancelled:
                        break

                    self.strategy_started.emit(idx, len(strategies), strategy.value)
                    config = OptimizationConfig(
                        strategy_name=strategy,
                        objective_metric="sharpe_ratio",
                        direction="maximize",
                        n_trials=self.opt_trials,
                    )

                    if self.mode == "bayesian":
                        optimizer = BayesianOptimizer(self.data, self.symbol, config)
                    else:
                        optimizer = GridSearchOptimizer(self.data, self.symbol, config)

                    # Keep reference so we can cancel from UI thread
                    self._optimizer = optimizer

                    # Optimizers are now synchronous
                    if self.mode == "grid":
                        result = optimizer.optimize(
                            progress_callback=progress_cb,
                            max_combinations=self.opt_trials,
                        )
                    else:
                        result = optimizer.optimize(progress_callback=progress_cb)
                    results.append(result)
                    if is_all:
                        self.partial_result.emit(result)

                if is_all:
                    self.finished.emit({"batch_done": True, "count": len(results)})
                else:
                    self.finished.emit(results[0] if results else [])

        except Exception as e:
            logger.error("Simulation failed: %s", e, exc_info=True)
            self.error.emit(str(e))
        finally:
            self._optimizer = None


class StrategySimulatorMixin:
    """Mixin providing Strategy Simulator tab for ChartWindow."""

    # Storage for simulation results
    _simulation_results: list = []
    _last_optimization_run: object = None
    _current_worker: SimulationWorker | None = None
    _current_sim_strategy_name: str | None = None
    _current_sim_strategy_index: int | None = None
    _current_sim_strategy_total: int | None = None
    _current_simulation_mode: str | None = None

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
        self._last_optimization_run = None
        self._current_sim_strategy_name = None
        self._current_sim_strategy_index = None
        self._current_sim_strategy_total = None
        self._current_simulation_mode = None
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
            "Bollinger Squeeze",
            "Trend Pullback",
            "Opening Range",
            "Regime Hybrid",
            "ALL",
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
        self.simulator_opt_trials_spin.setRange(10, 2_147_483_647)
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
        self.simulator_results_table.setSortingEnabled(True)
        header.setSortIndicatorShown(True)
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
        from src.core.simulator import StrategyName

        if self._is_all_strategy_selected():
            self.simulator_params_group.setEnabled(False)
            return

        self.simulator_params_group.setEnabled(True)
        strategy_map = {
            0: StrategyName.BREAKOUT,
            1: StrategyName.MOMENTUM,
            2: StrategyName.MEAN_REVERSION,
            3: StrategyName.TREND_FOLLOWING,
            4: StrategyName.SCALPING,
            5: StrategyName.BOLLINGER_SQUEEZE,
            6: StrategyName.TREND_PULLBACK,
            7: StrategyName.OPENING_RANGE,
            8: StrategyName.REGIME_HYBRID,
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

        if self._is_all_strategy_selected():
            self.simulator_status_label.setText(
                "ALL selected: parameters are not used for batch runs"
            )
            return

        strategy_map = {
            0: StrategyName.BREAKOUT,
            1: StrategyName.MOMENTUM,
            2: StrategyName.MEAN_REVERSION,
            3: StrategyName.TREND_FOLLOWING,
            4: StrategyName.SCALPING,
            5: StrategyName.BOLLINGER_SQUEEZE,
            6: StrategyName.TREND_PULLBACK,
            7: StrategyName.OPENING_RANGE,
            8: StrategyName.REGIME_HYBRID,
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
        from src.core.simulator import save_strategy_params_to_path

        strategy_name = self._get_simulator_strategy_name()
        params = self._get_simulator_parameters()

        # Get symbol from current chart if available
        symbol = None
        if hasattr(self, "current_symbol"):
            symbol = self.current_symbol

        default_dir = Path("config/strategy_params")
        default_name = f"{strategy_name}_params.json"
        default_path = default_dir / default_name
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Strategy Parameters",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )
        if not filepath:
            return

        path = Path(filepath)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        try:
            saved_path = save_strategy_params_to_path(
                filepath=path,
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
                f"File: {saved_path}",
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
        if self._is_all_strategy_selected():
            return "all"

        strategy_map = {
            0: "breakout",
            1: "momentum",
            2: "mean_reversion",
            3: "trend_following",
            4: "scalping",
            5: "bollinger_squeeze",
            6: "trend_pullback",
            7: "opening_range",
            8: "regime_hybrid",
        }
        return strategy_map.get(
            self.simulator_strategy_combo.currentIndex(), "breakout"
        )

    def _is_all_strategy_selected(self) -> bool:
        """Check if ALL is selected in strategy dropdown."""
        return self.simulator_strategy_combo.currentText().strip().upper() == "ALL"

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
        self._current_simulation_mode = mode

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
        self._current_worker.partial_result.connect(self._on_simulation_partial_result)
        self._current_worker.progress.connect(self._on_simulation_progress)
        self._current_worker.strategy_started.connect(self._on_simulation_strategy_started)
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
        strategy_prefix = ""
        if self._current_sim_strategy_name:
            index = self._current_sim_strategy_index or 1
            total_strategies = self._current_sim_strategy_total or 1
            display_name = self._get_strategy_display_name(self._current_sim_strategy_name)
            strategy_prefix = f"{index}/{total_strategies} {display_name} | "
        self.simulator_status_label.setText(
            f"{strategy_prefix}Trial {current}/{total} | Best: {best:.4f}"
        )

    def _on_simulation_finished(self, result) -> None:
        """Handle simulation completion."""
        self.simulator_run_btn.setEnabled(True)
        self.simulator_stop_btn.setEnabled(False)
        self.simulator_progress.setVisible(False)

        if isinstance(result, dict) and result.get("batch_done"):
            count = result.get("count", 0)
            status_msg = f"Completed batch run: {count} strategies"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
        elif isinstance(result, list):
            for item in result:
                self._handle_simulation_result(item)

            status_msg = f"Completed batch run: {len(result)} strategies"
            self.simulator_status_label.setText(status_msg)
            self._log_simulator_to_ki("OK", status_msg)
        else:
            self._handle_simulation_result(result)

        self.simulator_export_btn.setEnabled(bool(self._simulation_results))
        # Ensure thread is fully stopped before dropping reference
        self._cleanup_simulation_worker(wait_ms=200)

    def _handle_simulation_result(self, result) -> None:
        """Handle a single simulation or optimization result."""
        from src.core.simulator import SimulationResult, OptimizationRun

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

    def _on_simulation_partial_result(self, result) -> None:
        """Handle partial results for batch runs."""
        self._handle_simulation_result(result)

    def _on_simulation_strategy_started(self, index: int, total: int, strategy_name: str) -> None:
        """Update UI when a strategy run starts."""
        self._current_sim_strategy_name = strategy_name
        self._current_sim_strategy_index = index
        self._current_sim_strategy_total = total
        display_name = self._get_strategy_display_name(strategy_name)
        mode = self._current_simulation_mode or "manual"
        status_msg = f"Running {index}/{total}: {display_name} ({mode})"
        self.simulator_status_label.setText(status_msg)
        self._log_simulator_to_ki("INFO", status_msg)

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
        table = self.simulator_results_table
        was_sorting = table.isSortingEnabled()
        if was_sorting:
            table.setSortingEnabled(False)

        row = table.rowCount()
        table.insertRow(row)

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
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, result)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

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

        if was_sorting:
            table.setSortingEnabled(True)

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
        table = self.simulator_results_table
        was_sorting = table.isSortingEnabled()
        if was_sorting:
            table.setSortingEnabled(False)

        row = table.rowCount()
        table.insertRow(row)

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
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, None)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

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

        if was_sorting:
            table.setSortingEnabled(True)

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
        if not selected:
            self.simulator_show_markers_btn.setEnabled(False)
            return

        row = selected[0].row()
        result = self._get_result_from_row(row)
        self.simulator_show_markers_btn.setEnabled(result is not None)

    def _on_show_simulation_markers(self) -> None:
        """Show entry/exit markers on chart for selected result."""
        selected = self.simulator_results_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        result = self._get_result_from_row(row)
        if result is None:
            QMessageBox.warning(
                self, "Warning",
                "Keine Detail-Daten für diese Zeile verfügbar.\n\n"
                "Optimization-Trials haben nur Metriken, keine Trade-Details.\n"
                "Nur die 'Best Result'-Zeile hat vollständige Trade-Daten."
            )
            return

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
        self._last_optimization_run = None
        self.simulator_results_table.setRowCount(0)
        self.simulator_export_btn.setEnabled(False)
        self.simulator_show_markers_btn.setEnabled(False)
        self.simulator_status_label.setText("Results cleared")

    def _get_result_from_row(self, row: int) -> object | None:
        """Get the SimulationResult stored on the row, if any."""
        item = self.simulator_results_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _get_strategy_display_name(self, strategy_name: str) -> str:
        """Get display name for a strategy."""
        from src.core.simulator import StrategyName

        try:
            return StrategyName.display_names().get(strategy_name, strategy_name)
        except Exception:
            return strategy_name
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268
