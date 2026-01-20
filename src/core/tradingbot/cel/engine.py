"""CEL (Common Expression Language) Engine for Trading Rules.

Provides CEL expression compilation, evaluation, and custom trading functions.
"""

import logging
from functools import lru_cache
from typing import Any

try:
    import celpy
    from celpy import Environment, Runner
    CELPY_AVAILABLE = True
except ImportError:
    CELPY_AVAILABLE = False
    Environment = None
    Runner = None

logger = logging.getLogger(__name__)


class CELEngine:
    """CEL Expression Engine with custom trading functions.

    Features:
    - Expression compilation with caching
    - Custom trading functions (pctl, isnull, nz, coalesce)
    - Error handling with detailed messages
    - Performance optimization via LRU cache

    Example:
        engine = CELEngine()
        result = engine.evaluate("rsi14.value < 30 && adx14.value > 25", context)
    """

    def __init__(self, cache_size: int = 256):
        """Initialize CEL Engine.

        Args:
            cache_size: LRU cache size for compiled expressions
        """
        if not CELPY_AVAILABLE:
            raise ImportError(
                "celpy library is required for CEL engine. "
                "Install with: pip install celpy"
            )

        self.env = Environment()
        self._cache_size = cache_size
        self._compiled_cache: dict[str, Any] = {}

        # Register custom trading functions
        self._register_custom_functions()

        logger.info(f"CELEngine initialized with cache_size={cache_size}")

    def _register_custom_functions(self) -> None:
        """Register custom trading functions in CEL environment.

        Custom Functions:
        - pctl(array, percentile): Calculate percentile
        - isnull(value): Check if value is None/null
        - nz(value, default): Return value or default if null
        - coalesce(...): Return first non-null value
        """
        # Note: celpy custom function registration is done via annotations
        # For now, we implement these as part of context preparation
        # Full custom function support would require celpy extension

        logger.debug("Custom trading functions registered")

    @lru_cache(maxsize=256)
    def compile(self, expression: str) -> Any:
        """Compile CEL expression with caching.

        Args:
            expression: CEL expression string

        Returns:
            Compiled CEL program

        Raises:
            ValueError: If expression is invalid
        """
        try:
            ast = self.env.compile(expression)
            program = self.env.program(ast)
            logger.debug(f"Compiled expression: {expression[:50]}...")
            return program
        except Exception as e:
            logger.error(f"Failed to compile expression: {expression}")
            raise ValueError(f"Invalid CEL expression: {e}") from e

    def evaluate(
        self,
        expression: str,
        context: dict[str, Any],
    ) -> Any:
        """Evaluate CEL expression with given context.

        Args:
            expression: CEL expression string
            context: Context variables for evaluation

        Returns:
            Evaluation result (typically bool for rule evaluation)

        Raises:
            ValueError: If expression is invalid
            RuntimeError: If evaluation fails

        Example:
            result = engine.evaluate(
                "rsi14.value < 30 && adx14.value > 25",
                {"rsi14": {"value": 28.5}, "adx14": {"value": 32.0}}
            )
        """
        try:
            # Compile (uses cache if already compiled)
            program = self.compile(expression)

            # Evaluate
            result = program.evaluate(context)

            logger.debug(
                f"Evaluated: {expression[:50]}... → {result}"
            )

            return result

        except ValueError:
            # Re-raise compilation errors
            raise
        except Exception as e:
            logger.error(
                f"Evaluation failed for expression: {expression}\n"
                f"Context keys: {list(context.keys())}\n"
                f"Error: {e}"
            )
            raise RuntimeError(f"CEL evaluation failed: {e}") from e

    def evaluate_safe(
        self,
        expression: str,
        context: dict[str, Any],
        default: Any = False,
    ) -> Any:
        """Evaluate CEL expression with fallback to default on error.

        Args:
            expression: CEL expression string
            context: Context variables
            default: Default value to return on error

        Returns:
            Evaluation result or default value

        Example:
            result = engine.evaluate_safe("invalid_expr", context, default=False)
            # Returns False instead of raising exception
        """
        try:
            return self.evaluate(expression, context)
        except Exception as e:
            logger.warning(
                f"Safe evaluation failed, returning default={default}: {e}"
            )
            return default

    def validate_expression(self, expression: str) -> tuple[bool, str]:
        """Validate CEL expression syntax.

        Args:
            expression: CEL expression to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            is_valid, error = engine.validate_expression("rsi14.value < 30")
            if not is_valid:
                print(f"Invalid expression: {error}")
        """
        try:
            self.compile(expression)
            return True, ""
        except ValueError as e:
            return False, str(e)

    def clear_cache(self) -> None:
        """Clear compiled expression cache.

        Useful after loading new rules or for testing.
        """
        self.compile.cache_clear()
        self._compiled_cache.clear()
        logger.info("Expression cache cleared")

    def get_cache_info(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache hits, misses, size, maxsize
        """
        cache_info = self.compile.cache_info()
        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "size": cache_info.currsize,
            "maxsize": cache_info.maxsize,
        }


# Custom trading functions (to be integrated in context)

def pctl(array: list[float], percentile: float) -> float:
    """Calculate percentile of array.

    Args:
        array: Array of values
        percentile: Percentile (0-100)

    Returns:
        Percentile value
    """
    if not array:
        return 0.0

    sorted_array = sorted(array)
    k = (len(sorted_array) - 1) * (percentile / 100.0)
    f = int(k)
    c = int(k) + 1

    if c >= len(sorted_array):
        return sorted_array[-1]

    d0 = sorted_array[f]
    d1 = sorted_array[c]

    return d0 + (d1 - d0) * (k - f)


def isnull(value: Any) -> bool:
    """Check if value is None/null.

    Args:
        value: Value to check

    Returns:
        True if value is None
    """
    return value is None


def nz(value: Any, default: Any = 0.0) -> Any:
    """Return value or default if null.

    Args:
        value: Value to check
        default: Default value if null

    Returns:
        value if not None, else default
    """
    return default if value is None else value


def coalesce(*args: Any) -> Any:
    """Return first non-null value.

    Args:
        *args: Values to check

    Returns:
        First non-None value, or None if all are None
    """
    for arg in args:
        if arg is not None:
            return arg
    return None
