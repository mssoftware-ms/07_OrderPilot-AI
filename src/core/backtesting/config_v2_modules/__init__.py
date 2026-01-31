"""Backtesting Configuration V2 - Modular Structure

This package provides the BacktestConfigV2 configuration system split
into logical modules for better maintainability.

Modules:
- base: Enums and optimizable parameter types
- entry: Entry score configuration and triggers
- exit: Exit management configuration
- optimization: Optimization, risk, and execution settings
- main: Main BacktestConfigV2 aggregator class

For backward compatibility, you can import from the top level:
    from src.core.backtesting.config_v2 import BacktestConfigV2

For new code, import from this package:
    from src.core.backtesting.config_v2_modules import BacktestConfigV2
"""

# Re-export all public classes for convenience
from .base import (
    # Enums
    AssetClass,
    DirectionBias,
    OptimizationMethod,
    ScenarioType,
    SlippageMethod,
    StopLossType,
    StrategyType,
    TakeProfitType,
    TargetMetric,
    TrailingType,
    WeightPresetName,
    # Optimizable types
    OptimizableFloat,
    OptimizableInt,
)
from .entry import (
    DEFAULT_WEIGHT_PRESETS,
    BreakoutTrigger,
    EntryScoreGates,
    EntryScoreSection,
    EntryTriggersSection,
    IndicatorParams,
    MetaSection,
    PullbackTrigger,
    SfpTrigger,
    StrategyProfileSection,
    WeightPreset,
)
from .exit import (
    ExitManagementSection,
    PartialTPConfig,
    StopLossConfig,
    TakeProfitConfig,
    TimeStopConfig,
    TrailingStopConfig,
)
from .main import BacktestConfigV2
from .optimization import (
    Conditional,
    ConstraintsSection,
    ExecutionSimulationSection,
    OptimizationSection,
    ParameterGroup,
    RiskLeverageSection,
    WalkForwardSection,
)

__all__ = [
    # Main config
    "BacktestConfigV2",
    # Enums
    "AssetClass",
    "DirectionBias",
    "OptimizationMethod",
    "ScenarioType",
    "SlippageMethod",
    "StopLossType",
    "StrategyType",
    "TakeProfitType",
    "TargetMetric",
    "TrailingType",
    "WeightPresetName",
    # Optimizable types
    "OptimizableFloat",
    "OptimizableInt",
    # Entry
    "DEFAULT_WEIGHT_PRESETS",
    "BreakoutTrigger",
    "EntryScoreGates",
    "EntryScoreSection",
    "EntryTriggersSection",
    "IndicatorParams",
    "MetaSection",
    "PullbackTrigger",
    "SfpTrigger",
    "StrategyProfileSection",
    "WeightPreset",
    # Exit
    "ExitManagementSection",
    "PartialTPConfig",
    "StopLossConfig",
    "TakeProfitConfig",
    "TimeStopConfig",
    "TrailingStopConfig",
    # Optimization
    "Conditional",
    "ConstraintsSection",
    "ExecutionSimulationSection",
    "OptimizationSection",
    "ParameterGroup",
    "RiskLeverageSection",
    "WalkForwardSection",
]
