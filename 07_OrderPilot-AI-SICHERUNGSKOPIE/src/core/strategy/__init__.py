"""Strategy Module for OrderPilot-AI.

Provides models and utilities for defining, compiling, and executing
trading strategies in a declarative manner.
"""

from .compiler import (
    CompilationError,
    ConditionEvaluator,
    IndicatorFactory,
    StrategyCompiler,
)
from .definition import (
    ComparisonOperator,
    Condition,
    EntryExitLogic,
    IndicatorConfig,
    IndicatorType,
    LogicGroup,
    LogicOperator,
    RiskManagement,
    StrategyDefinition,
)

__all__ = [
    # Enums
    "IndicatorType",
    "ComparisonOperator",
    "LogicOperator",
    # Models
    "IndicatorConfig",
    "Condition",
    "LogicGroup",
    "RiskManagement",
    "StrategyDefinition",
    # Type Aliases
    "EntryExitLogic",
    # Compiler
    "StrategyCompiler",
    "IndicatorFactory",
    "ConditionEvaluator",
    "CompilationError",
]
