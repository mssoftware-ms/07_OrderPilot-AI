"""CEL Engine Core - Main CEL expression evaluation engine.

This module contains the core CELEngine class responsible for:
- CEL program compilation and caching
- Expression evaluation with context
- Type conversion between Python and CEL types
- Integration with custom trading functions

Part of the CEL (Common Expression Language) engine refactoring.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

try:
    import celpy
    from celpy import Environment
    CEL_AVAILABLE = True
except ImportError:
    CEL_AVAILABLE = False
    celpy = None
    Environment = None

from .cel_engine_functions import CELFunctions

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

        # Create function container with reference to this engine
        self._func_container = CELFunctions(engine_instance=self)

        # Custom functions dictionary for celpy
        self.custom_functions = self._build_custom_functions()
        self._last_context: dict[str, Any] = {}

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
        funcs = self._func_container
        return {
            # Statistical functions
            'pctl': funcs._func_pctl,
            'crossover': funcs._func_crossover,

            # Null handling
            'isnull': funcs._func_isnull,
            'nz': funcs._func_nz,
            'coalesce': funcs._func_coalesce,

            # Math functions (Phase 1.1)
            'clamp': funcs._func_clamp,
            'pct_change': funcs._func_pct_change,
            'pct_from_level': funcs._func_pct_from_level,
            'level_at_pct': funcs._func_level_at_pct,
            'retracement': funcs._func_retracement,
            'extension': funcs._func_extension,

            # Status functions (Phase 1.2)
            'is_trade_open': funcs._func_is_trade_open,
            'is_long': funcs._func_is_long,
            'is_short': funcs._func_is_short,
            'is_bullish_signal': funcs._func_is_bullish_signal,
            'is_bearish_signal': funcs._func_is_bearish_signal,
            'in_regime': funcs._func_in_regime,

            # Price functions (Phase 1.3)
            'stop_hit_long': funcs._func_stop_hit_long,
            'stop_hit_short': funcs._func_stop_hit_short,
            'tp_hit': funcs._func_tp_hit,
            'price_above_ema': funcs._func_price_above_ema,
            'price_below_ema': funcs._func_price_below_ema,
            'price_above_level': funcs._func_price_above_level,
            'price_below_level': funcs._func_price_below_level,

            # Time functions (Phase 1.4)
            'now': funcs._func_now,
            'timestamp': funcs._func_timestamp,
            'bar_age': funcs._func_bar_age,
            'bars_since': funcs._func_bars_since,
            'is_new_day': funcs._func_is_new_day,
            'is_new_hour': funcs._func_is_new_hour,

            # String functions (Phase 1.5)
            'type': funcs._func_type,
            'string': funcs._func_string,
            'int': funcs._func_int,
            'double': funcs._func_double,
            'bool': funcs._func_bool,
            'contains': funcs._func_contains,
            'startsWith': funcs._func_starts_with,
            'endsWith': funcs._func_ends_with,
            'toLowerCase': funcs._func_to_lower_case,
            'toUpperCase': funcs._func_to_upper_case,
            'substring': funcs._func_substring,
            'split': funcs._func_split,
            'join': funcs._func_join,

            # Array functions (Phase 1.6)
            'size': funcs._func_size,
            'length': funcs._func_size,  # Alias
            'has': funcs._func_has,
            'all': funcs._func_all,
            'any': funcs._func_any,
            'map': funcs._func_map,
            'filter': funcs._func_filter,
            'sum': funcs._func_sum,
            'avg': funcs._func_avg,
            'average': funcs._func_avg,  # Alias
            'first': funcs._func_first,
            'last': funcs._func_last,
            'indexOf': funcs._func_index_of,
            'slice': funcs._func_slice,
            'distinct': funcs._func_distinct,
            'sort': funcs._func_sort,
            'reverse': funcs._func_reverse,

            # Additional Math functions
            'floor': funcs._func_floor,
            'ceil': funcs._func_ceil,
            'round': funcs._func_round,
            'sqrt': funcs._func_sqrt,
            'pow': funcs._func_pow,
            'exp': funcs._func_exp,

            # Additional Time functions
            'is_new_week': funcs._func_is_new_week,
            'is_new_month': funcs._func_is_new_month,

            # Additional Price functions
            'highest': funcs._func_highest,
            'lowest': funcs._func_lowest,
            'sma': funcs._func_sma,

            # Regime functions (Phase 1.7)
            'last_closed_regime': funcs._func_last_closed_regime,
            'trigger_regime_analysis': funcs._func_trigger_regime_analysis,
            'new_regime_detected': funcs._func_new_regime_detected,

            # Pattern functions (Candlestick & Chart Patterns)
            'pin_bar_bullish': funcs._func_pin_bar_bullish,
            'pin_bar_bearish': funcs._func_pin_bar_bearish,
            'inside_bar': funcs._func_inside_bar,
            'inverted_hammer': funcs._func_inverted_hammer,
            'bull_flag': funcs._func_bull_flag,
            'bear_flag': funcs._func_bear_flag,
            'cup_and_handle': funcs._func_cup_and_handle,
            'double_bottom': funcs._func_double_bottom,
            'double_top': funcs._func_double_top,
            'ascending_triangle': funcs._func_ascending_triangle,
            'descending_triangle': funcs._func_descending_triangle,

            # Breakout functions
            'breakout_above': funcs._func_breakout_above,
            'breakdown_below': funcs._func_breakdown_below,
            'false_breakout': funcs._func_false_breakout,
            'break_of_structure': funcs._func_break_of_structure,

            # Smart Money Concepts (SMC)
            'liquidity_swept': funcs._func_liquidity_swept,
            'fvg_exists': funcs._func_fvg_exists,
            'order_block_retest': funcs._func_order_block_retest,
            'harmonic_pattern_detected': funcs._func_harmonic_pattern_detected,

            # Built-ins
            'abs': abs,
            'min': min,
            'max': max,
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
            # Store last context for context-aware helper functions
            self._last_context = context or {}

            # Debug: Log context keys
            print(f"[CEL] evaluate() called, context keys: {list(context.keys())}", flush=True)
            print(f"[CEL] chart_window in context: {'chart_window' in context}", flush=True)
            if 'chart_window' in context:
                print(f"[CEL] chart_window type: {type(context['chart_window']).__name__}", flush=True)

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
    def evaluate_with_sources(
        self,
        expression: str,
        chart_window=None,
        bot_config=None,
        project_vars_path=None,
        indicators: dict[str, Any] | None = None,
        regime: dict[str, Any] | None = None,
        default: Any = None,
        context_builder=None,
    ) -> Any:
        """Evaluate CEL expression with automatic context building from multiple sources.

        This method provides a high-level API for evaluating expressions with
        variables from chart data, bot configuration, and project variables.
        Automatically builds the context using CELContextBuilder.

        Args:
            expression: CEL expression to evaluate
            chart_window: ChartWindow instance for chart.* variables (optional)
            bot_config: BotConfig instance for bot.* variables (optional)
            project_vars_path: Path to .cel_variables.json for project variables (optional)
            indicators: Dictionary of indicator values for indicators.* namespace (optional)
            regime: Dictionary of regime values for regime.* namespace (optional)
            default: Default value if evaluation fails (optional)
            context_builder: Custom CELContextBuilder instance (creates default if None)

        Returns:
            Evaluation result (bool, int, float, str, list, dict, or None)

        Raises:
            ValueError: If expression is invalid
            RuntimeError: If evaluation fails unexpectedly

        Examples:
            >>> from src.core.tradingbot.cel_engine import CELEngine
            >>> from src.core.variables import CELContextBuilder
            >>>
            >>> cel = CELEngine()
            >>>
            >>> # Evaluate with all sources
            >>> result = cel.evaluate_with_sources(
            ...     expression="chart.price > project.entry_min_price and bot.leverage == 10",
            ...     chart_window=chart_window,
            ...     bot_config=bot_config,
            ...     project_vars_path="project/.cel_variables.json"
            ... )
            >>>
            >>> # Evaluate with minimal sources
            >>> result = cel.evaluate_with_sources(
            ...     expression="bot.paper_mode == true",
            ...     bot_config=bot_config
            ... )
            >>>
            >>> # Evaluate with indicators and regime
            >>> result = cel.evaluate_with_sources(
            ...     expression="indicators.rsi > 70 and regime.current == 'overbought'",
            ...     indicators={"rsi": 75.0},
            ...     regime={"current": "overbought"}
            ... )

        Note:
            This method uses lazy imports to avoid circular dependencies.
            CELContextBuilder is imported only when needed.
        """
        # Lazy import to avoid circular dependency
        if context_builder is None:
            from src.core.variables import CELContextBuilder
            context_builder = CELContextBuilder()

        # Build context from all sources
        context = context_builder.build(
            chart_window=chart_window,
            bot_config=bot_config,
            project_vars_path=project_vars_path,
            indicators=indicators,
            regime=regime,
            include_empty_namespaces=False,  # Only include available data
        )

        # Evaluate using standard evaluate() method
        return self.evaluate(expression, context, default=default)

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

