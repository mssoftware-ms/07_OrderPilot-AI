"""JSON Configuration System for Regime-Based Trading Strategies.

This module provides:
- Pydantic models for JSON strategy configuration
- Config loading and validation against JSON Schema
- Condition evaluation system
- Regime detection
- Strategy routing
- Strategy set execution with parameter overrides

Architecture:
    models.py -> Core Pydantic models (Indicators, Regimes, Strategies, etc.)
    loader.py -> ConfigLoader (loads + validates JSON files)
    evaluator.py -> ConditionEvaluator (evaluates condition logic)
    detector.py -> RegimeDetector (detects active regimes)
    router.py -> StrategyRouter (routes regimes to strategy sets)
    executor.py -> StrategySetExecutor (executes with parameter overrides)
"""

from .detector import ActiveRegime, RegimeDetector
from .evaluator import ConditionEvaluationError, ConditionEvaluator
from .executor import ExecutionContext, StrategySetExecutor
from .loader import ConfigLoader, ConfigLoadError
from .router import MatchedStrategySet, StrategyRouter
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

# Legacy runtime config models live in src/core/tradingbot/config.py, but the
# package name "config" shadows that module. Load it explicitly to preserve
# backwards compatibility for imports like `from src.core.tradingbot import BotConfig`.
from importlib import util
from pathlib import Path

_legacy_config_path = Path(__file__).resolve().parent.parent / "config.py"
_legacy_spec = util.spec_from_file_location(
    "src.core.tradingbot._legacy_config", _legacy_config_path
)
if _legacy_spec and _legacy_spec.loader:
    _legacy_config = util.module_from_spec(_legacy_spec)
    _legacy_spec.loader.exec_module(_legacy_config)
else:
    _legacy_config = None

if _legacy_config is not None:
    BotConfig = _legacy_config.BotConfig
    FullBotConfig = _legacy_config.FullBotConfig
    KIMode = _legacy_config.KIMode
    LLMPolicyConfig = _legacy_config.LLMPolicyConfig
    MarketType = _legacy_config.MarketType
    RiskConfig = _legacy_config.RiskConfig
    TrailingMode = _legacy_config.TrailingMode
    TradingEnvironment = _legacy_config.TradingEnvironment

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

    # Router
    "StrategyRouter",
    "MatchedStrategySet",

    # Executor
    "StrategySetExecutor",
    "ExecutionContext",

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
    # Legacy runtime config (compatibility)
    "BotConfig",
    "FullBotConfig",
    "KIMode",
    "LLMPolicyConfig",
    "MarketType",
    "RiskConfig",
    "TrailingMode",
    "TradingEnvironment",
]
