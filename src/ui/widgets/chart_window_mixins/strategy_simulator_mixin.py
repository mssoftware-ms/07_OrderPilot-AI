from __future__ import annotations

from PyQt6.QtWidgets import QSplitter

from .strategy_simulator_params_mixin import StrategySimulatorParamsMixin
from .strategy_simulator_results_mixin import StrategySimulatorResultsMixin
from .strategy_simulator_run_mixin import StrategySimulatorRunMixin
from .strategy_simulator_ui_mixin import StrategySimulatorUIMixin
from .strategy_simulator_worker import SimulationWorker


class StrategySimulatorMixin(
    StrategySimulatorUIMixin,
    StrategySimulatorParamsMixin,
    StrategySimulatorRunMixin,
    StrategySimulatorResultsMixin,
):
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
