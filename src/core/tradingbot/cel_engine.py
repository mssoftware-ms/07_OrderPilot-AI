"""CEL (Common Expression Language) Engine for Rule Evaluation.

Provides safe, non-Turing complete expression evaluation for trading rules.
Includes custom functions for technical analysis (pctl, crossover, isnull, etc.).

Based on:
- CEL Spec: https://github.com/google/cel-spec/blob/master/doc/langdef.md
- Python CEL: https://pypi.org/project/cel-python/
- Documentation: 01_Projectplan/Strategien_Workflow_json/CEL_Rules_Doku_TradingBot_Analyzer.md
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

try:
    import celpy
    from celpy import Environment, Runner
    CEL_AVAILABLE = True
except ImportError:
    CEL_AVAILABLE = False
    celpy = None
    Environment = None
    Runner = None

logger = logging.getLogger(__name__)


class CELEngine:
    """CEL expression engine with custom trading functions.

    Features:
    - Compilation caching for performance
    - Custom functions: pctl, crossover, isnull, nz, coalesce
    - Safe evaluation with bounded execution
    - Type-safe context handling

    Example:
        >>> engine = CELEngine()
        >>> context = {"atrp": 0.6, "cfg": {"min_atrp_pct": 0.2}}
        >>> result = engine.evaluate("atrp > cfg.min_atrp_pct", context)
        >>> print(result)  # True
    """

    def __init__(self, enable_cache: bool = True, cache_size: int = 128):
        """Initialize CEL engine.

        Args:
            enable_cache: Enable compilation caching for performance
            cache_size: LRU cache size for compiled expressions
        """
        if not CEL_AVAILABLE:
            raise ImportError(
                "cel-python (celpy) is not installed. "
                "Install with: pip install cel-python"
            )

        self.enable_cache = enable_cache
        self.cache_size = cache_size

        # Create CEL environment
        self.env = celpy.Environment()

        # Custom functions dictionary for celpy
        self.custom_functions = self._build_custom_functions()

        # Cache for compiled programs (AST + functions)
        if enable_cache:
            self._get_program = lru_cache(maxsize=cache_size)(self._create_program)
        else:
            self._get_program = self._create_program

        logger.info(f"CELEngine initialized (cache={'enabled' if enable_cache else 'disabled'})")

    def _build_custom_functions(self) -> dict[str, Any]:
        """Build dictionary of custom functions for CEL.

        Returns:
            Dictionary mapping function names to implementations
        """
        return {
            'pctl': self._func_pctl,
            'crossover': self._func_crossover,
            'isnull': self._func_isnull,
            'nz': self._func_nz,
            'coalesce': self._func_coalesce,
            'abs': abs,  # Built-in
            'min': min,  # Built-in
            'max': max,  # Built-in
        }

    def _create_program(self, expression: str) -> Any:
        """Compile CEL expression and create program (internal, may be cached).

        Args:
            expression: CEL expression string

        Returns:
            Compiled CEL program ready for evaluation

        Raises:
            ValueError: If expression syntax is invalid
        """
        try:
            # Compile expression to AST
            ast = self.env.compile(expression)
            # Create program with custom functions
            program = self.env.program(ast, functions=self.custom_functions)
            return program
        except Exception as e:
            raise ValueError(f"CEL compilation failed: {e}") from e

    def evaluate(
        self,
        expression: str,
        context: dict[str, Any],
        default: Any = None
    ) -> Any:
        """Evaluate CEL expression with context.

        Args:
            expression: CEL expression to evaluate
            context: Variable context (must be JSON-serializable types)
            default: Default value if evaluation fails

        Returns:
            Evaluation result (bool, int, float, str, list, dict, or None)

        Raises:
            ValueError: If expression is invalid
            RuntimeError: If evaluation fails unexpectedly
        """
        try:
            # Get compiled program (cached if enabled)
            program = self._get_program(expression)

            # Convert context to celpy types for proper operator support
            cel_context = self._to_cel_types(context)

            # Evaluate with context
            result = program.evaluate(cel_context)

            # Convert celpy types back to Python native types
            return self._to_python_type(result)

        except ValueError:
            # Re-raise compilation errors
            raise
        except Exception as e:
            logger.warning(f"CEL evaluation failed: {e}, returning default={default}")
            if default is not None:
                return default
            raise RuntimeError(f"CEL evaluation failed: {e}") from e

    @staticmethod
    def _to_cel_types(context: dict[str, Any]) -> dict[str, Any]:
        """Convert Python native types to celpy types recursively.

        Args:
            context: Dictionary with Python native types

        Returns:
            Dictionary with celpy types
        """
        import celpy.celtypes as ct

        def convert_value(value: Any) -> Any:
            """Convert a single value to celpy type."""
            if value is None:
                return None
            elif isinstance(value, bool):
                # IMPORTANT: Must check bool before int (bool is subclass of int)
                return ct.BoolType(value)
            elif isinstance(value, int):
                return ct.IntType(value)
            elif isinstance(value, float):
                return ct.DoubleType(value)
            elif isinstance(value, str):
                return ct.StringType(value)
            elif isinstance(value, bytes):
                return ct.BytesType(value)
            elif isinstance(value, list):
                return ct.ListType([convert_value(item) for item in value])
            elif isinstance(value, dict):
                return ct.MapType({
                    ct.StringType(str(k)): convert_value(v)
                    for k, v in value.items()
                })
            else:
                # Already a celpy type or unknown type - leave as is
                return value

        return {key: convert_value(val) for key, val in context.items()}

    @staticmethod
    def _to_python_type(value: Any) -> Any:
        """Convert celpy types to Python native types.

        Args:
            value: celpy type or Python native type

        Returns:
            Python native type (bool, int, float, str, list, dict, None)
        """
        if value is None:
            return None

        # Import celpy types
        import celpy.celtypes as ct

        # Convert celpy types to Python native types
        if isinstance(value, ct.BoolType):
            return bool(value)
        elif isinstance(value, ct.IntType):
            return int(value)
        elif isinstance(value, ct.UintType):
            return int(value)
        elif isinstance(value, ct.DoubleType):
            return float(value)
        elif isinstance(value, ct.StringType):
            return str(value)
        elif isinstance(value, ct.BytesType):
            return bytes(value)
        elif isinstance(value, ct.ListType):
            return [CELEngine._to_python_type(item) for item in value]
        elif isinstance(value, ct.MapType):
            return {
                CELEngine._to_python_type(k): CELEngine._to_python_type(v)
                for k, v in value.items()
            }
        else:
            # Already a Python native type or unknown type
            return value


    # ========================================================================
    # Custom Trading Functions
    # ========================================================================

    @staticmethod
    def _func_pctl(series: list | pd.Series, percentile: float, window: int | None = None) -> float:
        """Calculate percentile of a series.

        Args:
            series: Data series (list or Series)
            percentile: Percentile rank (0-100)
            window: Rolling window size (None = use all data)

        Returns:
            Percentile value

        Example:
            >>> pctl([10, 20, 30, 40, 50], 50)  # Median
            30.0
        """
        if isinstance(series, pd.Series):
            data = series.values
        elif isinstance(series, list):
            data = np.array(series)
        else:
            data = np.array([series])

        # Use window if specified
        if window is not None and len(data) > window:
            data = data[-window:]

        # Filter out NaN/None
        data = data[~pd.isna(data)]

        if len(data) == 0:
            return 0.0

        return float(np.percentile(data, percentile))

    @staticmethod
    def _func_crossover(series1: float | list, series2: float | list) -> bool:
        """Check if series1 crossed above series2 (bullish crossover).

        Args:
            series1: Current and previous values [current, previous]
            series2: Current and previous values [current, previous]

        Returns:
            True if series1 crossed above series2

        Example:
            >>> crossover([10, 8], [9, 9])  # 8 < 9, 10 > 9 => crossover
            True
        """
        # Handle scalar vs list inputs
        if isinstance(series1, (int, float)):
            # If scalar, assume no crossover (need history)
            return False
        if isinstance(series2, (int, float)):
            s2_curr = s2_prev = series2
        else:
            s2_curr, s2_prev = series2[0], series2[1] if len(series2) > 1 else series2[0]

        s1_curr, s1_prev = series1[0], series1[1] if len(series1) > 1 else series1[0]

        # Crossover: was below, now above
        return s1_prev <= s2_prev and s1_curr > s2_curr

    @staticmethod
    def _func_isnull(value: Any) -> bool:
        """Check if value is null/None/NaN.

        Args:
            value: Value to check

        Returns:
            True if value is null/None/NaN

        Example:
            >>> isnull(None)
            True
            >>> isnull(float('nan'))
            True
        """
        if value is None:
            return True
        if isinstance(value, float) and np.isnan(value):
            return True
        return False

    @staticmethod
    def _func_nz(value: Any, default: Any = 0) -> Any:
        """Return default if value is null, otherwise return value.

        Args:
            value: Value to check
            default: Default value if null

        Returns:
            value if not null, else default

        Example:
            >>> nz(None, 100)
            100
            >>> nz(42, 100)
            42
        """
        if CELEngine._func_isnull(value):
            return default
        return value

    @staticmethod
    def _func_coalesce(*args) -> Any:
        """Return first non-null value from arguments.

        Args:
            *args: Values to check in order

        Returns:
            First non-null value, or None if all null

        Example:
            >>> coalesce(None, None, 42, 100)
            42
        """
        for arg in args:
            if not CELEngine._func_isnull(arg):
                return arg
        return None

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def clear_cache(self) -> None:
        """Clear program compilation cache."""
        if self.enable_cache and hasattr(self._get_program, 'cache_clear'):
            self._get_program.cache_clear()
            logger.info("CEL program cache cleared")

    def get_cache_info(self) -> dict[str, int] | None:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, size, maxsize (or None if caching disabled)
        """
        if self.enable_cache and hasattr(self._get_program, 'cache_info'):
            info = self._get_program.cache_info()
            return {
                'hits': info.hits,
                'misses': info.misses,
                'size': info.currsize,
                'maxsize': info.maxsize
            }
        return None

    def validate_expression(self, expression: str) -> tuple[bool, str | None]:
        """Validate CEL expression syntax.

        Args:
            expression: CEL expression to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self._get_program(expression)
            return True, None
        except ValueError as e:
            return False, str(e)


# Singleton instance for convenience
_default_engine: CELEngine | None = None


def get_cel_engine() -> CELEngine:
    """Get or create default CEL engine instance.

    Returns:
        Default CELEngine instance (singleton)
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = CELEngine()
    return _default_engine
