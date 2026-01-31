"""CEL Engine - Common Expression Language for trading rules.

This package provides a CEL (Common Expression Language) engine for evaluating
trading rules and conditions with custom functions.

Main Components:
- CELEngine: Core expression evaluation engine
- CELFunctions: Custom trading functions (90+ functions across 7 phases)
- CELContextHelper: Helper for context value resolution
- get_cel_engine(): Singleton factory for default engine instance

Usage:
    >>> from src.core.tradingbot import CELEngine, get_cel_engine
    >>>
    >>> # Create engine instance
    >>> engine = CELEngine()
    >>> context = {"price": 100, "threshold": 95}
    >>> result = engine.evaluate("price > threshold", context)
    >>>
    >>> # Or use singleton
    >>> engine = get_cel_engine()

Backward Compatibility:
    The original monolithic cel_engine.py has been split into:
    - cel_engine_core.py: Main CELEngine class
    - cel_engine_functions.py: All custom CEL functions
    - cel_engine_utils.py: Helper utilities

    All imports from the original module still work through this __init__.py
"""

from .cel_engine_core import CELEngine
from .cel_engine_utils import get_cel_engine, reset_cel_engine, CELContextHelper
from .cel_engine_functions import CELFunctions
# Issue #61: Export all config classes needed by UI
from .config import (
    BotConfig,
    FullBotConfig,
    KIMode,
    MarketType,
    RiskConfig,
    TrailingMode,
)

__all__ = [
    'CELEngine',
    'CELFunctions',
    'CELContextHelper',
    'get_cel_engine',
    'reset_cel_engine',
    'BotConfig',
    'FullBotConfig',
    'KIMode',
    'MarketType',
    'RiskConfig',
    'TrailingMode',
]
