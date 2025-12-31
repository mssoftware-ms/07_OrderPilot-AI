"""Strategy Simulator Package.

Provides configurable strategy simulation and parameter optimization
for the 5 base strategies: Breakout, Momentum, Mean Reversion,
Trend Following, and Scalping.
"""

from .strategy_params import (
    StrategyName,
    ParameterDefinition,
    StrategyParameterConfig,
    get_strategy_parameters,
    get_default_parameters,
    STRATEGY_PARAMETER_REGISTRY,
)
from .result_types import (
    TradeRecord,
    SimulationResult,
    OptimizationRun,
    OptimizationTrial,
)
from .simulation_engine import (
    SimulationConfig,
    StrategySimulator,
)
from .optimization_bayesian import (
    OptimizationConfig,
    BayesianOptimizer,
    GridSearchOptimizer,
)
from .excel_export import (
    StrategySimulatorExport,
    export_simulation_results,
)
from .strategy_persistence import (
    save_strategy_params,
    save_strategy_params_to_path,
    load_strategy_params,
    get_all_saved_strategies,
    delete_strategy_params,
    get_params_metadata,
)

__all__ = [
    # Strategy Parameters
    "StrategyName",
    "ParameterDefinition",
    "StrategyParameterConfig",
    "get_strategy_parameters",
    "get_default_parameters",
    "STRATEGY_PARAMETER_REGISTRY",
    # Result Types
    "TradeRecord",
    "SimulationResult",
    "OptimizationRun",
    "OptimizationTrial",
    # Simulation
    "SimulationConfig",
    "StrategySimulator",
    # Optimization
    "OptimizationConfig",
    "BayesianOptimizer",
    "GridSearchOptimizer",
    # Export
    "StrategySimulatorExport",
    "export_simulation_results",
    # Persistence
    "save_strategy_params",
    "save_strategy_params_to_path",
    "load_strategy_params",
    "get_all_saved_strategies",
    "delete_strategy_params",
    "get_params_metadata",
]
