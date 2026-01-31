"""CEL Engine - Backward Compatibility Wrapper.

This module provides backward compatibility for code importing from the original
monolithic cel_engine.py file.

DEPRECATED: This wrapper is provided for backward compatibility only.
New code should import from:
- cel_engine_core (CELEngine class)
- cel_engine_functions (CELFunctions)
- cel_engine_utils (get_cel_engine, CELContextHelper)

Or use the package-level imports:
    from src.core.tradingbot import CELEngine, get_cel_engine
"""

# Re-export all public APIs from new structure
from .cel_engine_core import CELEngine
from .cel_engine_functions import CELFunctions
from .cel_engine_utils import (
    get_cel_engine,
    reset_cel_engine,
    CELContextHelper,
)

# Export all symbols for compatibility
__all__ = [
    'CELEngine',
    'CELFunctions',
    'CELContextHelper',
    'get_cel_engine',
    'reset_cel_engine',
]
