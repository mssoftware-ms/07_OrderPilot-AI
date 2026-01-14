"""
Backtesting Configuration Package

For backwards compatibility, all classes are re-exported here.
"""

# Enums
from .enums import (
    StrategyType,
    WeightPresetName,
    DirectionBias,
    ScenarioType,
    AssetClass,
    StopLossType,
    TakeProfitType,
    TrailingType,
    SlippageMethod,
    OptimizationMethod,
    TargetMetric,
)

# Optimizable Types
from .optimizable import OptimizableFloat, OptimizableInt, WeightPreset

# Indicators
from .indicators import MetaSection, IndicatorParams

# Entry
from .entry import (
    StrategyProfileSection,
    EntryScoreGates,
    EntryScoreSection,
    BreakoutTrigger,
    PullbackTrigger,
    SfpTrigger,
    EntryTriggersSection,
)

# Exit
from .exit import (
    StopLossConfig,
    TakeProfitConfig,
    TrailingStopConfig,
    PartialTPConfig,
    TimeStopConfig,
    ExitManagementSection,
)

# Risk
from .risk import RiskLeverageSection, ExecutionSimulationSection

# Optimization
from .optimization import (
    OptimizationSection,
    WalkForwardSection,
    ParameterGroup,
    Conditional,
    ConstraintsSection,
)

# Main
from .main import BacktestConfigV2

__all__ = [
    # Enums
    "StrategyType",
    "WeightPresetName",
    "DirectionBias",
    "ScenarioType",
    "AssetClass",
    "StopLossType",
    "TakeProfitType",
    "TrailingType",
    "SlippageMethod",
    "OptimizationMethod",
    "TargetMetric",
    # Optimizable
    "OptimizableFloat",
    "OptimizableInt",
    "WeightPreset",
    # Indicators
    "MetaSection",
    "IndicatorParams",
    # Entry
    "StrategyProfileSection",
    "EntryScoreGates",
    "EntryScoreSection",
    "BreakoutTrigger",
    "PullbackTrigger",
    "SfpTrigger",
    "EntryTriggersSection",
    # Exit
    "StopLossConfig",
    "TakeProfitConfig",
    "TrailingStopConfig",
    "PartialTPConfig",
    "TimeStopConfig",
    "ExitManagementSection",
    # Risk
    "RiskLeverageSection",
    "ExecutionSimulationSection",
    # Optimization
    "OptimizationSection",
    "WalkForwardSection",
    "ParameterGroup",
    "Conditional",
    "ConstraintsSection",
    # Main
    "BacktestConfigV2",
]
