from __future__ import annotations

import logging

from .strategy_simulator_execution_mixin import StrategySimulatorExecutionMixin
from .strategy_simulator_data_mixin import StrategySimulatorDataMixin
from .strategy_simulator_settings_mixin import StrategySimulatorSettingsMixin
from .strategy_simulator_results_mixin import StrategySimulatorResultsMixin
from .strategy_simulator_ui_callbacks_mixin import StrategySimulatorUICallbacksMixin

logger = logging.getLogger(__name__)


class StrategySimulatorRunMixin(
    StrategySimulatorExecutionMixin,
    StrategySimulatorDataMixin,
    StrategySimulatorSettingsMixin,
    StrategySimulatorResultsMixin,
    StrategySimulatorUICallbacksMixin,
):
    """StrategySimulatorRunMixin - Uses sub-mixin pattern for better modularity.

    Coordinates strategy simulation execution by combining:
    - Execution: Running simulations and worker management
    - Data: Chart data access and filtering
    - Settings: UI widget value collection
    - Results: Result handling and optimization
    - UI Callbacks: Progress updates and UI state management
    """
    pass
