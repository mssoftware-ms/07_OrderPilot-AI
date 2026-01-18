"""JSON Configuration System for Regime-Based Trading Strategies.

This module provides:
- Pydantic models for JSON strategy configuration
- Config loading and validation against JSON Schema
- Condition evaluation system
- Regime detection
- Strategy routing

Architecture:
    models.py -> Core Pydantic models (Indicators, Regimes, Strategies, etc.)
    loader.py -> ConfigLoader (loads + validates JSON files)
    evaluator.py -> ConditionEvaluator (evaluates condition logic)
    detector.py -> RegimeDetector (detects active regimes)
    router.py -> StrategyRouter (routes regimes to strategy sets)
"""

from .detector import ActiveRegime, RegimeDetector
from .evaluator import ConditionEvaluationError, ConditionEvaluator
from .loader import ConfigLoader, ConfigLoadError
from .models import (
    # Enums
    ConditionOperator,
    IndicatorType,
    RegimeScope,

    # Core Models
    IndicatorDefinition,
    IndicatorRef,
    ConstantValue,
    BetweenRange,
    Condition,
    ConditionGroup,
    RegimeDefinition,
    RiskSettings,
    StrategyDefinition as JSONStrategyDefinition,
    StrategyReference,
    StrategySetDefinition,
    RoutingMatch,
    RoutingRule,

    # Root Config
    TradingBotConfig,
)

__all__ = [
    # Loader
    "ConfigLoader",
    "ConfigLoadError",

    # Evaluator
    "ConditionEvaluator",
    "ConditionEvaluationError",

    # Detector
    "RegimeDetector",
    "ActiveRegime",

    # Enums
    "ConditionOperator",
    "IndicatorType",
    "RegimeScope",

    # Models
    "IndicatorDefinition",
    "IndicatorRef",
    "ConstantValue",
    "BetweenRange",
    "Condition",
    "ConditionGroup",
    "RegimeDefinition",
    "RiskSettings",
    "JSONStrategyDefinition",
    "StrategyReference",
    "StrategySetDefinition",
    "RoutingMatch",
    "RoutingRule",
    "TradingBotConfig",
]
