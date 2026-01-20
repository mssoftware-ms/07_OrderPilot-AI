"""CEL (Common Expression Language) Engine for Trading Rules.

This module provides a CEL-based rule evaluation system for trading bot logic.
Supports custom trading functions and context building from market data.

Key Components:
- CELEngine: CEL expression compiler and evaluator
- RuleContextBuilder: Converts FeatureVector to CEL context
- RulePack: Pydantic models for rule packs
- Custom Functions: pctl, isnull, nz, coalesce

Example:
    from src.core.tradingbot.cel import CELEngine, RuleContextBuilder

    engine = CELEngine()
    context = RuleContextBuilder.build(features)
    result = engine.evaluate("rsi14.value < 30 && adx14.value > 25", context)
"""

from .engine import CELEngine
from .context import RuleContextBuilder
from .models import RulePack, Pack, Rule
from .executor import (
    RulePackExecutor,
    ExecutionResult,
    ExecutionSummary,
    enforce_monotonic_stop,
)

__all__ = [
    "CELEngine",
    "RuleContextBuilder",
    "RulePack",
    "Pack",
    "Rule",
    "RulePackExecutor",
    "ExecutionResult",
    "ExecutionSummary",
    "enforce_monotonic_stop",
]
