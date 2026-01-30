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
from datetime import datetime
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
        return {
            # Statistical functions
            'pctl': self._func_pctl,
            'crossover': self._func_crossover,

            # Null handling
            'isnull': self._func_isnull,
            'nz': self._func_nz,
            'coalesce': self._func_coalesce,

            # Math functions (Phase 1.1)
            'clamp': self._func_clamp,
            'pct_change': self._func_pct_change,
            'pct_from_level': self._func_pct_from_level,
            'level_at_pct': self._func_level_at_pct,
            'retracement': self._func_retracement,
            'extension': self._func_extension,

            # Status functions (Phase 1.2)
            'is_trade_open': self._func_is_trade_open,
            'is_long': self._func_is_long,
            'is_short': self._func_is_short,
            'is_bullish_signal': self._func_is_bullish_signal,
            'is_bearish_signal': self._func_is_bearish_signal,
            'in_regime': self._func_in_regime,

            # Price functions (Phase 1.3)
            'stop_hit_long': self._func_stop_hit_long,
            'stop_hit_short': self._func_stop_hit_short,
            'tp_hit': self._func_tp_hit,
            'price_above_ema': self._func_price_above_ema,
            'price_below_ema': self._func_price_below_ema,
            'price_above_level': self._func_price_above_level,
            'price_below_level': self._func_price_below_level,

            # Time functions (Phase 1.4)
            'now': self._func_now,
            'timestamp': self._func_timestamp,
            'bar_age': self._func_bar_age,
            'bars_since': self._func_bars_since,
            'is_new_day': self._func_is_new_day,
            'is_new_hour': self._func_is_new_hour,

            # String functions (Phase 1.5)
            'type': self._func_type,
            'string': self._func_string,
            'int': self._func_int,
            'double': self._func_double,
            'bool': self._func_bool,
            'contains': self._func_contains,
            'startsWith': self._func_starts_with,
            'endsWith': self._func_ends_with,
            'toLowerCase': self._func_to_lower_case,
            'toUpperCase': self._func_to_upper_case,
            'substring': self._func_substring,
            'split': self._func_split,
            'join': self._func_join,

            # Array functions (Phase 1.6)
            'size': self._func_size,
            'length': self._func_size,  # Alias
            'has': self._func_has,
            'all': self._func_all,
            'any': self._func_any,
            'map': self._func_map,
            'filter': self._func_filter,
            'sum': self._func_sum,
            'avg': self._func_avg,
            'average': self._func_avg,  # Alias
            'first': self._func_first,
            'last': self._func_last,
            'indexOf': self._func_index_of,
            'slice': self._func_slice,
            'distinct': self._func_distinct,
            'sort': self._func_sort,
            'reverse': self._func_reverse,

            # Additional Math functions
            'floor': self._func_floor,
            'ceil': self._func_ceil,
            'round': self._func_round,
            'sqrt': self._func_sqrt,
            'pow': self._func_pow,
            'exp': self._func_exp,

            # Additional Time functions
            'is_new_week': self._func_is_new_week,
            'is_new_month': self._func_is_new_month,

            # Additional Price functions
            'highest': self._func_highest,
            'lowest': self._func_lowest,
            'sma': self._func_sma,

            # Regime functions (Phase 1.7)
            'last_closed_regime': self._func_last_closed_regime,
            'trigger_regime_analysis': self._func_trigger_regime_analysis,
            'new_regime_detected': self._func_new_regime_detected,

            # Pattern functions (Candlestick & Chart Patterns)
            'pin_bar_bullish': self._func_pin_bar_bullish,
            'pin_bar_bearish': self._func_pin_bar_bearish,
            'inside_bar': self._func_inside_bar,
            'inverted_hammer': self._func_inverted_hammer,
            'bull_flag': self._func_bull_flag,
            'bear_flag': self._func_bear_flag,
            'cup_and_handle': self._func_cup_and_handle,
            'double_bottom': self._func_double_bottom,
            'double_top': self._func_double_top,
            'ascending_triangle': self._func_ascending_triangle,
            'descending_triangle': self._func_descending_triangle,

            # Breakout functions
            'breakout_above': self._func_breakout_above,
            'breakdown_below': self._func_breakdown_below,
            'false_breakout': self._func_false_breakout,
            'break_of_structure': self._func_break_of_structure,

            # Smart Money Concepts (SMC)
            'liquidity_swept': self._func_liquidity_swept,
            'fvg_exists': self._func_fvg_exists,
            'order_block_retest': self._func_order_block_retest,
            'harmonic_pattern_detected': self._func_harmonic_pattern_detected,

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
    # Phase 1.1: Mathematical & Trading Functions
    # ========================================================================

    @staticmethod
    def _func_clamp(value: float, min_val: float, max_val: float) -> float:
        """Constrain value between min and max.

        Args:
            value: Value to clamp
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            Clamped value

        Example:
            >>> clamp(15, 10, 20)
            15
            >>> clamp(5, 10, 20)
            10
            >>> clamp(25, 10, 20)
            20
        """
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")
        return max(min_val, min(value, max_val))

    @staticmethod
    def _func_pct_change(old: float, new: float) -> float:
        """Calculate percentage change from old to new value.

        Args:
            old: Old value
            new: New value

        Returns:
            Percentage change (e.g., 10.5 for 10.5% increase)

        Example:
            >>> pct_change(100, 110)
            10.0
            >>> pct_change(100, 90)
            -10.0
        """
        if old == 0:
            # Avoid division by zero: return 0 if both are 0, else 100% change
            return 0.0 if new == 0 else (100.0 if new > 0 else -100.0)
        return ((new - old) / abs(old)) * 100.0

    @staticmethod
    def _func_pct_from_level(price: float, level: float) -> float:
        """Calculate percentage distance from price to level.

        Args:
            price: Current price
            level: Reference level

        Returns:
            Absolute percentage distance

        Example:
            >>> pct_from_level(110, 100)
            10.0
            >>> pct_from_level(90, 100)
            10.0
        """
        if level == 0:
            return 0.0
        return abs((price - level) / level) * 100.0

    @staticmethod
    def _func_level_at_pct(entry: float, pct: float, side: str) -> float:
        """Calculate price level at percentage distance from entry.

        Args:
            entry: Entry price
            pct: Percentage distance (positive number, e.g., 2.0 for 2%)
            side: Trade side ('long' or 'short')

        Returns:
            Price level

        Example:
            >>> level_at_pct(100, 2.0, 'long')  # Stop loss 2% below
            98.0
            >>> level_at_pct(100, 2.0, 'short')  # Stop loss 2% above
            102.0
        """
        if side.lower() == 'long':
            # Long: level below entry (stop loss)
            return entry * (1 - pct / 100.0)
        elif side.lower() == 'short':
            # Short: level above entry (stop loss)
            return entry * (1 + pct / 100.0)
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'long' or 'short'")

    @staticmethod
    def _func_retracement(from_price: float, to_price: float, pct: float) -> float:
        """Calculate Fibonacci retracement level.

        Args:
            from_price: Starting price (swing low for uptrend, high for downtrend)
            to_price: Ending price (swing high for uptrend, low for downtrend)
            pct: Retracement percentage (e.g., 38.2, 50, 61.8)

        Returns:
            Retracement level price

        Example:
            >>> retracement(100, 200, 50)  # 50% retracement
            150.0
            >>> retracement(200, 100, 61.8)  # 61.8% retracement down
            138.2
        """
        return from_price + (to_price - from_price) * (pct / 100.0)

    @staticmethod
    def _func_extension(from_price: float, to_price: float, pct: float) -> float:
        """Calculate Fibonacci extension level.

        Args:
            from_price: Starting price
            to_price: Ending price
            pct: Extension percentage (e.g., 127.2, 161.8, 261.8)

        Returns:
            Extension level price

        Example:
            >>> extension(100, 200, 161.8)  # 161.8% extension
            361.8
        """
        move = to_price - from_price
        return to_price + move * (pct / 100.0)

    # ========================================================================
    # Phase 1.2: Status Functions
    # ========================================================================

    @staticmethod
    def _func_is_trade_open(trade: dict) -> bool:
        """Check if a trade is currently open.

        Args:
            trade: Trade context dict with 'is_open' or 'status' field

        Returns:
            True if trade is open

        Example:
            >>> is_trade_open({"is_open": True})
            True
            >>> is_trade_open({"status": "open"})
            True
        """
        if isinstance(trade, dict):
            # Check 'is_open' field first
            if 'is_open' in trade:
                return bool(trade['is_open'])
            # Fallback: check 'status' field
            if 'status' in trade:
                return str(trade['status']).lower() in ('open', 'active')
        return False

    @staticmethod
    def _func_is_long(trade: dict) -> bool:
        """Check if current trade is LONG.

        Args:
            trade: Trade context dict with 'side' field

        Returns:
            True if trade side is LONG

        Example:
            >>> is_long({"side": "long"})
            True
            >>> is_long({"side": "short"})
            False
        """
        if isinstance(trade, dict) and 'side' in trade:
            return str(trade['side']).lower() == 'long'
        return False

    @staticmethod
    def _func_is_short(trade: dict) -> bool:
        """Check if current trade is SHORT.

        Args:
            trade: Trade context dict with 'side' field

        Returns:
            True if trade side is SHORT

        Example:
            >>> is_short({"side": "short"})
            True
            >>> is_short({"side": "long"})
            False
        """
        if isinstance(trade, dict) and 'side' in trade:
            return str(trade['side']).lower() == 'short'
        return False

    @staticmethod
    def _func_is_bullish_signal(strategy: dict) -> bool:
        """Check if strategy has bullish bias.

        Args:
            strategy: Strategy context dict with 'signal' or 'bias' field

        Returns:
            True if bullish signal active

        Example:
            >>> is_bullish_signal({"signal": "bullish"})
            True
            >>> is_bullish_signal({"bias": "long"})
            True
        """
        if isinstance(strategy, dict):
            # Check 'signal' field
            if 'signal' in strategy:
                return str(strategy['signal']).lower() in ('bullish', 'buy', 'long')
            # Check 'bias' field
            if 'bias' in strategy:
                return str(strategy['bias']).lower() in ('bullish', 'long', 'up')
        return False

    @staticmethod
    def _func_is_bearish_signal(strategy: dict) -> bool:
        """Check if strategy has bearish bias.

        Args:
            strategy: Strategy context dict with 'signal' or 'bias' field

        Returns:
            True if bearish signal active

        Example:
            >>> is_bearish_signal({"signal": "bearish"})
            True
            >>> is_bearish_signal({"bias": "short"})
            True
        """
        if isinstance(strategy, dict):
            # Check 'signal' field
            if 'signal' in strategy:
                return str(strategy['signal']).lower() in ('bearish', 'sell', 'short')
            # Check 'bias' field
            if 'bias' in strategy:
                return str(strategy['bias']).lower() in ('bearish', 'short', 'down')
        return False

    @staticmethod
    def _func_in_regime(regime: str | list, regime_id: str) -> bool:
        """Check if currently in specified regime.

        Args:
            regime: Current regime (string ID or list of active regime IDs)
            regime_id: Regime ID to check

        Returns:
            True if in specified regime

        Example:
            >>> in_regime("trending_strong", "trending_strong")
            True
            >>> in_regime(["trending", "high_vol"], "trending")
            True
        """
        if isinstance(regime, str):
            return regime == regime_id
        elif isinstance(regime, list):
            return regime_id in regime
        return False

    # ========================================================================
    # Phase 1.3: Price Functions
    # ========================================================================

    @staticmethod
    def _func_stop_hit_long(trade: dict, current_price: float) -> bool:
        """Check if long stop loss was hit.

        Args:
            trade: Trade context with 'stop_price' or 'stop_loss' field
            current_price: Current market price

        Returns:
            True if stop was hit (price <= stop)

        Example:
            >>> stop_hit_long({"stop_price": 100}, 99)
            True
            >>> stop_hit_long({"stop_price": 100}, 101)
            False
        """
        if not isinstance(trade, dict):
            return False

        stop_price = trade.get('stop_price') or trade.get('stop_loss')
        if stop_price is None:
            return False

        return current_price <= float(stop_price)

    @staticmethod
    def _func_stop_hit_short(trade: dict, current_price: float) -> bool:
        """Check if short stop loss was hit.

        Args:
            trade: Trade context with 'stop_price' or 'stop_loss' field
            current_price: Current market price

        Returns:
            True if stop was hit (price >= stop)

        Example:
            >>> stop_hit_short({"stop_price": 100}, 101)
            True
            >>> stop_hit_short({"stop_price": 100}, 99)
            False
        """
        if not isinstance(trade, dict):
            return False

        stop_price = trade.get('stop_price') or trade.get('stop_loss')
        if stop_price is None:
            return False

        return current_price >= float(stop_price)

    @staticmethod
    def _func_tp_hit(trade: dict, current_price: float) -> bool:
        """Check if take profit was hit.

        Args:
            trade: Trade context with 'tp_price', 'take_profit', and 'side' fields
            current_price: Current market price

        Returns:
            True if take profit was hit

        Example:
            >>> tp_hit({"tp_price": 110, "side": "long"}, 111)
            True
            >>> tp_hit({"tp_price": 90, "side": "short"}, 89)
            True
        """
        if not isinstance(trade, dict):
            return False

        tp_price = trade.get('tp_price') or trade.get('take_profit')
        if tp_price is None:
            return False

        side = trade.get('side', '').lower()
        tp_price = float(tp_price)

        if side == 'long':
            return current_price >= tp_price
        elif side == 'short':
            return current_price <= tp_price
        else:
            # Unknown side, check both directions
            return current_price >= tp_price or current_price <= tp_price

    @staticmethod
    def _func_price_above_ema(price: float, ema: float) -> bool:
        """Check if price is above EMA.

        Args:
            price: Current price
            ema: EMA value

        Returns:
            True if price > EMA

        Example:
            >>> price_above_ema(105, 100)
            True
            >>> price_above_ema(95, 100)
            False
        """
        return price > ema

    @staticmethod
    def _func_price_below_ema(price: float, ema: float) -> bool:
        """Check if price is below EMA.

        Args:
            price: Current price
            ema: EMA value

        Returns:
            True if price < EMA

        Example:
            >>> price_below_ema(95, 100)
            True
            >>> price_below_ema(105, 100)
            False
        """
        return price < ema

    @staticmethod
    def _func_price_above_level(price: float, level: float) -> bool:
        """Check if price is above specified level.

        Args:
            price: Current price
            level: Price level (support/resistance)

        Returns:
            True if price > level

        Example:
            >>> price_above_level(105, 100)
            True
        """
        return price > level

    @staticmethod
    def _func_price_below_level(price: float, level: float) -> bool:
        """Check if price is below specified level.

        Args:
            price: Current price
            level: Price level (support/resistance)

        Returns:
            True if price < level

        Example:
            >>> price_below_level(95, 100)
            True
        """
        return price < level

    # ========================================================================
    # Phase 1.4: Time Functions
    # ========================================================================

    @staticmethod
    def _func_now() -> int:
        """Get current Unix timestamp in seconds.

        Returns:
            Current timestamp (seconds since epoch)

        Example:
            >>> now()  # e.g., 1706356800
            1706356800
        """
        return int(datetime.now().timestamp())

    @staticmethod
    def _func_timestamp(dt: str | datetime | int) -> int:
        """Convert datetime to Unix timestamp.

        Args:
            dt: Datetime (ISO string, datetime object, or timestamp)

        Returns:
            Unix timestamp in seconds

        Example:
            >>> timestamp("2024-01-27T12:00:00")
            1706356800
            >>> timestamp(1706356800)
            1706356800
        """
        if isinstance(dt, int):
            return dt
        elif isinstance(dt, datetime):
            return int(dt.timestamp())
        elif isinstance(dt, str):
            # Parse ISO format datetime string
            try:
                parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return int(parsed.timestamp())
            except ValueError:
                # Fallback: try common formats
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        parsed = datetime.strptime(dt, fmt)
                        return int(parsed.timestamp())
                    except ValueError:
                        continue
                raise ValueError(f"Cannot parse datetime: {dt}")
        else:
            raise TypeError(f"Invalid type for timestamp: {type(dt)}")

    @staticmethod
    def _func_bar_age(bar_time: int | str | datetime) -> int:
        """Calculate age of bar in seconds.

        Args:
            bar_time: Bar timestamp (Unix seconds, ISO string, or datetime)

        Returns:
            Age in seconds

        Example:
            >>> bar_age(1706356800)  # If now is 1706356900
            100
        """
        bar_ts = CELEngine._func_timestamp(bar_time)
        now_ts = CELEngine._func_now()
        return now_ts - bar_ts

    @staticmethod
    def _func_bars_since(trade: dict, current_bar: int) -> int:
        """Calculate number of bars since trade entry.

        Args:
            trade: Trade context with 'entry_bar' or 'bars_in_trade' field
            current_bar: Current bar index

        Returns:
            Number of bars since entry

        Example:
            >>> bars_since({"entry_bar": 100}, 105)
            5
            >>> bars_since({"bars_in_trade": 10}, 0)
            10
        """
        if not isinstance(trade, dict):
            return 0

        # Check if already calculated
        if 'bars_in_trade' in trade:
            return int(trade['bars_in_trade'])

        # Calculate from entry bar
        entry_bar = trade.get('entry_bar')
        if entry_bar is not None:
            return current_bar - int(entry_bar)

        return 0

    @staticmethod
    def _func_is_new_day(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if current time is a new day compared to previous.

        Args:
            prev_time: Previous timestamp
            curr_time: Current timestamp

        Returns:
            True if day changed

        Example:
            >>> is_new_day("2024-01-27T23:59:59", "2024-01-28T00:00:01")
            True
            >>> is_new_day("2024-01-27T10:00:00", "2024-01-27T14:00:00")
            False
        """
        prev_ts = CELEngine._func_timestamp(prev_time)
        curr_ts = CELEngine._func_timestamp(curr_time)

        prev_dt = datetime.fromtimestamp(prev_ts)
        curr_dt = datetime.fromtimestamp(curr_ts)

        return prev_dt.date() != curr_dt.date()

    @staticmethod
    def _func_is_new_hour(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if current time is a new hour compared to previous.

        Args:
            prev_time: Previous timestamp
            curr_time: Current timestamp

        Returns:
            True if hour changed

        Example:
            >>> is_new_hour("2024-01-27T10:59:59", "2024-01-27T11:00:01")
            True
            >>> is_new_hour("2024-01-27T10:00:00", "2024-01-27T10:30:00")
            False
        """
        prev_ts = CELEngine._func_timestamp(prev_time)
        curr_ts = CELEngine._func_timestamp(curr_time)

        prev_dt = datetime.fromtimestamp(prev_ts)
        curr_dt = datetime.fromtimestamp(curr_ts)

        return prev_dt.hour != curr_dt.hour or prev_dt.date() != curr_dt.date()

    # ========================================================================
    # Phase 1.5: String & Type Functions
    # ========================================================================

    @staticmethod
    def _func_type(value: Any) -> str:
        """Get type name of value.

        Args:
            value: Any value

        Returns:
            Type name (string)

        Example:
            >>> type(42)
            'int'
            >>> type("hello")
            'str'
        """
        return type(value).__name__

    @staticmethod
    def _func_string(value: Any) -> str:
        """Convert value to string.

        Args:
            value: Any value

        Returns:
            String representation

        Example:
            >>> string(42)
            '42'
            >>> string(True)
            'True'
        """
        return str(value)

    @staticmethod
    def _func_int(value: Any) -> int:
        """Convert value to integer.

        Args:
            value: Numeric value or string

        Returns:
            Integer value

        Example:
            >>> int("42")
            42
            >>> int(42.7)
            42
        """
        return int(float(value))  # Handle both int and float strings

    @staticmethod
    def _func_double(value: Any) -> float:
        """Convert value to float (double).

        Args:
            value: Numeric value or string

        Returns:
            Float value

        Example:
            >>> double("42.5")
            42.5
            >>> double(42)
            42.0
        """
        return float(value)

    @staticmethod
    def _func_bool(value: Any) -> bool:
        """Convert value to boolean.

        Args:
            value: Any value

        Returns:
            Boolean value

        Example:
            >>> bool("true")
            True
            >>> bool(0)
            False
        """
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    @staticmethod
    def _func_contains(haystack: str, needle: str) -> bool:
        """Check if string contains substring.

        Args:
            haystack: String to search in
            needle: Substring to search for

        Returns:
            True if found

        Example:
            >>> contains("hello world", "world")
            True
            >>> contains("hello world", "xyz")
            False
        """
        return needle in haystack

    @staticmethod
    def _func_starts_with(text: str, prefix: str) -> bool:
        """Check if string starts with prefix.

        Args:
            text: String to check
            prefix: Prefix to match

        Returns:
            True if starts with prefix

        Example:
            >>> startsWith("hello world", "hello")
            True
        """
        return text.startswith(prefix)

    @staticmethod
    def _func_ends_with(text: str, suffix: str) -> bool:
        """Check if string ends with suffix.

        Args:
            text: String to check
            suffix: Suffix to match

        Returns:
            True if ends with suffix

        Example:
            >>> endsWith("hello world", "world")
            True
        """
        return text.endswith(suffix)

    @staticmethod
    def _func_to_lower_case(text: str) -> str:
        """Convert string to lowercase.

        Args:
            text: String to convert

        Returns:
            Lowercase string

        Example:
            >>> toLowerCase("HELLO World")
            'hello world'
        """
        return text.lower()

    @staticmethod
    def _func_to_upper_case(text: str) -> str:
        """Convert string to uppercase.

        Args:
            text: String to convert

        Returns:
            Uppercase string

        Example:
            >>> toUpperCase("hello World")
            'HELLO WORLD'
        """
        return text.upper()

    @staticmethod
    def _func_substring(text: str, start: int, end: int | None = None) -> str:
        """Extract substring.

        Args:
            text: String to extract from
            start: Start index (inclusive)
            end: End index (exclusive), None = to end

        Returns:
            Substring

        Example:
            >>> substring("hello world", 0, 5)
            'hello'
            >>> substring("hello world", 6)
            'world'
        """
        if end is None:
            return text[start:]
        return text[start:end]

    @staticmethod
    def _func_split(text: str, delimiter: str) -> list[str]:
        """Split string by delimiter.

        Args:
            text: String to split
            delimiter: Delimiter string

        Returns:
            List of parts

        Example:
            >>> split("a,b,c", ",")
            ['a', 'b', 'c']
        """
        return text.split(delimiter)

    @staticmethod
    def _func_join(parts: list, delimiter: str) -> str:
        """Join list of strings with delimiter.

        Args:
            parts: List of strings
            delimiter: Delimiter to join with

        Returns:
            Joined string

        Example:
            >>> join(['a', 'b', 'c'], ",")
            'a,b,c'
        """
        return delimiter.join(str(p) for p in parts)

    # ========================================================================
    # Phase 1.6: Array Functions
    # ========================================================================

    @staticmethod
    def _func_size(array: list | dict) -> int:
        """Get size/length of array or map.

        Args:
            array: List or dict

        Returns:
            Number of elements

        Example:
            >>> size([1, 2, 3])
            3
            >>> size({"a": 1, "b": 2})
            2
        """
        return len(array)

    @staticmethod
    def _func_has(array: list, element: Any) -> bool:
        """Check if array contains element.

        Args:
            array: List to search
            element: Element to find

        Returns:
            True if element in array

        Example:
            >>> has([1, 2, 3], 2)
            True
            >>> has([1, 2, 3], 5)
            False
        """
        return element in array

    @staticmethod
    def _func_all(array: list, condition: Any = None) -> bool:
        """Check if all elements match condition (or are truthy).

        Args:
            array: List to check
            condition: Condition function (not supported in CEL, checks truthiness)

        Returns:
            True if all elements are truthy

        Example:
            >>> all([True, True, True])
            True
            >>> all([True, False, True])
            False
        """
        # Note: CEL doesn't support lambda functions, so we check truthiness
        return all(array)

    @staticmethod
    def _func_any(array: list, condition: Any = None) -> bool:
        """Check if any element matches condition (or is truthy).

        Args:
            array: List to check
            condition: Condition function (not supported in CEL, checks truthiness)

        Returns:
            True if any element is truthy

        Example:
            >>> any([False, False, True])
            True
            >>> any([False, False, False])
            False
        """
        # Note: CEL doesn't support lambda functions, so we check truthiness
        return any(array)

    @staticmethod
    def _func_map(array: list, transform: Any) -> list:
        """Map function over array (limited support without lambdas).

        Args:
            array: List to map over
            transform: Transform function (not fully supported in CEL)

        Returns:
            Transformed list

        Note:
            CEL doesn't support lambda functions, so this is limited.
            Returns original array.

        Example:
            >>> map([1, 2, 3], lambda x: x * 2)  # Not supported in CEL
            [1, 2, 3]
        """
        # Note: Without lambda support, return original array
        # This is a placeholder for future CEL macro support
        return array

    @staticmethod
    def _func_filter(array: list, condition: Any) -> list:
        """Filter array by condition (limited support without lambdas).

        Args:
            array: List to filter
            condition: Filter condition (not fully supported in CEL)

        Returns:
            Filtered list

        Note:
            CEL doesn't support lambda functions, so this is limited.
            Returns original array.

        Example:
            >>> filter([1, 2, 3, 4], lambda x: x > 2)  # Not supported in CEL
            [1, 2, 3, 4]
        """
        # Note: Without lambda support, return original array
        # This is a placeholder for future CEL macro support
        return array

    @staticmethod
    def _func_sum(array: list) -> float:
        """Calculate sum of array elements.

        Args:
            array: List of numbers

        Returns:
            Sum of all elements

        Example:
            >>> sum([1, 2, 3, 4])
            10.0
        """
        return sum(float(x) for x in array if x is not None)

    @staticmethod
    def _func_avg(array: list) -> float:
        """Calculate average of array elements.

        Args:
            array: List of numbers

        Returns:
            Average value

        Example:
            >>> avg([1, 2, 3, 4])
            2.5
        """
        if not array:
            return 0.0
        values = [float(x) for x in array if x is not None]
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _func_first(array: list) -> Any:
        """Get first element of array.

        Args:
            array: List

        Returns:
            First element or None if empty

        Example:
            >>> first([1, 2, 3])
            1
        """
        return array[0] if array else None

    @staticmethod
    def _func_last(array: list) -> Any:
        """Get last element of array.

        Args:
            array: List

        Returns:
            Last element or None if empty

        Example:
            >>> last([1, 2, 3])
            3
        """
        return array[-1] if array else None

    @staticmethod
    def _func_index_of(array: list, element: Any) -> int:
        """Find index of element in array.

        Args:
            array: List to search
            element: Element to find

        Returns:
            Index of element, or -1 if not found

        Example:
            >>> indexOf([1, 2, 3], 2)
            1
            >>> indexOf([1, 2, 3], 5)
            -1
        """
        try:
            return array.index(element)
        except ValueError:
            return -1

    @staticmethod
    def _func_slice(array: list, start: int, end: int | None = None) -> list:
        """Slice array.

        Args:
            array: List to slice
            start: Start index (inclusive)
            end: End index (exclusive), None = to end

        Returns:
            Sliced list

        Example:
            >>> slice([1, 2, 3, 4, 5], 1, 3)
            [2, 3]
            >>> slice([1, 2, 3, 4, 5], 2)
            [3, 4, 5]
        """
        if end is None:
            return array[start:]
        return array[start:end]

    @staticmethod
    def _func_distinct(array: list) -> list:
        """Get distinct/unique elements from array.

        Args:
            array: List with potential duplicates

        Returns:
            List with unique elements (order preserved)

        Example:
            >>> distinct([1, 2, 2, 3, 1, 4])
            [1, 2, 3, 4]
        """
        # Preserve order while removing duplicates
        seen = set()
        result = []
        for item in array:
            # Handle unhashable types
            try:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            except TypeError:
                # Unhashable type (e.g., dict, list), always include
                result.append(item)
        return result

    @staticmethod
    def _func_sort(array: list, reverse: bool = False) -> list:
        """Sort array.

        Args:
            array: List to sort
            reverse: Sort in descending order

        Returns:
            Sorted list

        Example:
            >>> sort([3, 1, 4, 1, 5])
            [1, 1, 3, 4, 5]
            >>> sort([3, 1, 4], True)
            [4, 3, 1]
        """
        return sorted(array, reverse=reverse)

    @staticmethod
    def _func_reverse(array: list) -> list:
        """Reverse array.

        Args:
            array: List to reverse

        Returns:
            Reversed list

        Example:
            >>> reverse([1, 2, 3])
            [3, 2, 1]
        """
        return list(reversed(array))

    # ========================================================================
    # Additional Math Functions (Phase 1 Completion)
    # ========================================================================

    @staticmethod
    def _func_floor(value: float) -> float:
        """Round down to nearest integer.

        Args:
            value: Number to floor

        Returns:
            Floored value

        Example:
            >>> floor(3.7)
            3.0
            >>> floor(-3.2)
            -4.0
        """
        import math
        return math.floor(value)

    @staticmethod
    def _func_ceil(value: float) -> float:
        """Round up to nearest integer.

        Args:
            value: Number to ceil

        Returns:
            Ceiled value

        Example:
            >>> ceil(3.2)
            4.0
            >>> ceil(-3.7)
            -3.0
        """
        import math
        return math.ceil(value)

    @staticmethod
    def _func_round(value: float, decimals: int = 0) -> float:
        """Round to N decimal places.

        Args:
            value: Number to round
            decimals: Number of decimal places (default: 0)

        Returns:
            Rounded value

        Example:
            >>> round(3.14159, 2)
            3.14
            >>> round(3.7, 0)
            4.0
        """
        return round(value, decimals)

    @staticmethod
    def _func_sqrt(value: float) -> float:
        """Calculate square root.

        Args:
            value: Number to take square root of

        Returns:
            Square root

        Raises:
            ValueError: If value is negative

        Example:
            >>> sqrt(16.0)
            4.0
            >>> sqrt(2.0)
            1.414...
        """
        import math
        if value < 0:
            raise ValueError(f"Cannot take square root of negative number: {value}")
        return math.sqrt(value)

    @staticmethod
    def _func_pow(base: float, exponent: float) -> float:
        """Calculate base raised to exponent power.

        Args:
            base: Base number
            exponent: Exponent

        Returns:
            base^exponent

        Example:
            >>> pow(2.0, 3.0)
            8.0
            >>> pow(5.0, 2.0)
            25.0
        """
        return pow(base, exponent)

    @staticmethod
    def _func_exp(value: float) -> float:
        """Calculate e raised to power of value (e^x).

        Args:
            value: Exponent

        Returns:
            e^value

        Example:
            >>> exp(0.0)
            1.0
            >>> exp(1.0)
            2.718...
        """
        import math
        return math.exp(value)

    # ========================================================================
    # Additional Time Functions (Phase 1 Completion)
    # ========================================================================

    @staticmethod
    def _func_is_new_week(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if new week started between two timestamps.

        Args:
            prev_time: Previous timestamp (Unix seconds, ISO string, or datetime)
            curr_time: Current timestamp (Unix seconds, ISO string, or datetime)

        Returns:
            True if new week started (Monday transition)

        Example:
            >>> is_new_week(prev_sunday, curr_monday)
            True
            >>> is_new_week(monday_morning, monday_evening)
            False
        """
        def to_datetime(val: int | str | datetime) -> datetime:
            """Convert timestamp to datetime."""
            if isinstance(val, datetime):
                return val
            elif isinstance(val, int):
                return datetime.fromtimestamp(val)
            else:  # String
                return datetime.fromisoformat(val)

        prev_dt = to_datetime(prev_time)
        curr_dt = to_datetime(curr_time)

        # Check if week changed (ISO week number)
        return prev_dt.isocalendar()[1] != curr_dt.isocalendar()[1]

    @staticmethod
    def _func_is_new_month(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if new month started between two timestamps.

        Args:
            prev_time: Previous timestamp (Unix seconds, ISO string, or datetime)
            curr_time: Current timestamp (Unix seconds, ISO string, or datetime)

        Returns:
            True if new month started

        Example:
            >>> is_new_month(jan_31, feb_01)
            True
            >>> is_new_month(jan_15, jan_20)
            False
        """
        def to_datetime(val: int | str | datetime) -> datetime:
            """Convert timestamp to datetime."""
            if isinstance(val, datetime):
                return val
            elif isinstance(val, int):
                return datetime.fromtimestamp(val)
            else:  # String
                return datetime.fromisoformat(val)

        prev_dt = to_datetime(prev_time)
        curr_dt = to_datetime(curr_time)

        # Check if month changed
        return prev_dt.month != curr_dt.month or prev_dt.year != curr_dt.year

    # ========================================================================
    # Additional Price Functions (Phase 1 Completion)
    # ========================================================================

    @staticmethod
    def _func_highest(series: list | pd.Series, period: int) -> float:
        """Get highest value over period.

        Args:
            series: Price series (list or pandas Series)
            period: Lookback period

        Returns:
            Highest value in last N periods

        Example:
            >>> highest([100, 105, 110, 108, 112], 5)
            112.0
            >>> highest([100, 105, 110], 2)
            110.0
        """
        if isinstance(series, pd.Series):
            series = series.tolist()

        # Take last N periods
        data = series[-period:] if len(series) >= period else series

        return max(data) if data else 0.0

    @staticmethod
    def _func_lowest(series: list | pd.Series, period: int) -> float:
        """Get lowest value over period.

        Args:
            series: Price series (list or pandas Series)
            period: Lookback period

        Returns:
            Lowest value in last N periods

        Example:
            >>> lowest([100, 95, 90, 92, 88], 5)
            88.0
            >>> lowest([100, 95, 90], 2)
            90.0
        """
        if isinstance(series, pd.Series):
            series = series.tolist()

        # Take last N periods
        data = series[-period:] if len(series) >= period else series

        return min(data) if data else 0.0

    @staticmethod
    def _func_sma(series: list | pd.Series, period: int) -> float:
        """Calculate Simple Moving Average.

        Args:
            series: Price series (list or pandas Series)
            period: SMA period

        Returns:
            Simple moving average of last N periods

        Example:
            >>> sma([100, 102, 104, 106, 108], 5)
            104.0
            >>> sma([10, 20, 30], 2)
            25.0
        """
        if isinstance(series, pd.Series):
            series = series.tolist()

        # Take last N periods
        data = series[-period:] if len(series) >= period else series

        if not data:
            return 0.0

        return sum(data) / len(data)

    # ========================================================================
    # Phase 1.7: Regime Functions
    # ========================================================================

    def _func_trigger_regime_analysis(self) -> bool:
        """Trigger regime analysis on visible chart range.

        This function:
        1. Gets chart window reference from context
        2. Calls trigger_regime_update() on the chart to analyze visible range
        3. Returns true if successful, false otherwise

        Returns:
            True if regime analysis was triggered successfully

        Example:
            >>> # In CEL expression (run before entry check):
            >>> trigger_regime_analysis() && last_closed_regime() == 'EXTREME_BULL'
            True

            >>> # Ensure regime data is fresh before trade decision
            >>> trigger_regime_analysis() && !is_trade_open(trade) && in_regime('TREND_UP')
            True

        Note:
            This function requires the context to have:
            - 'chart_window' reference with trigger_regime_update() method

            If chart_window is not available, logs a warning and returns False.
        """
        try:
            ctx = self._last_context or {}

            # Debug: Log context
            print(f"[CEL] trigger_regime_analysis: _last_context keys: {list(ctx.keys())}", flush=True)
            print(f"[CEL] trigger_regime_analysis: chart_window in ctx: {'chart_window' in ctx}", flush=True)

            # Get chart window reference from context
            if 'chart_window' not in ctx:
                logger.warning("❌ trigger_regime_analysis: No chart_window in context!")
                print("[CEL] ❌ trigger_regime_analysis: No chart_window in context!", flush=True)
                print(f"[CEL] ❌ Available keys: {list(ctx.keys())}", flush=True)
                return False

            chart_window = ctx['chart_window']
            print(f"[CEL] ✅ chart_window found: {type(chart_window).__name__}", flush=True)

            # Check if regime update is available (from RegimeDisplayMixin)
            if not hasattr(chart_window, 'trigger_regime_update'):
                logger.warning("❌ trigger_regime_analysis: Chart window has no trigger_regime_update method")
                print("[CEL] ❌ Chart window has no trigger_regime_update method", flush=True)
                return False

            # Trigger regime analysis (with immediate execution, no debounce, force=True)
            # force=True bypasses hash check to ensure detection always runs
            print("[CEL] 🔄 Triggering regime_update(debounce_ms=0, force=True)...", flush=True)
            chart_window.trigger_regime_update(debounce_ms=0, force=True)

            logger.info("✅ Regime analysis triggered successfully")
            print("[CEL] ✅ Regime analysis triggered successfully", flush=True)
            return True

        except Exception as e:
            logger.error(f"❌ Error triggering regime analysis: {e}", exc_info=True)
            print(f"[CEL] ❌ Error: {e}", flush=True)
            return False

    def _func_last_closed_regime(self) -> str:
        """Get regime of the last closed candle.

        Returns:
            Regime string (e.g., 'STRONG_BULL', 'BULL', 'SIDEWAYS', 'BEAR', 'STRONG_BEAR')
            Returns 'UNKNOWN' if data is not available.

        Priority order for reading regime:
        1. chart_window._last_closed_regime (set by trigger_regime_analysis())
        2. last_closed_candle.regime from context
        3. chart_data[-2].regime from context
        4. prev_regime from context
        5. 'UNKNOWN' as fallback

        Example:
            >>> # In CEL expression:
            >>> trigger_regime_analysis() && last_closed_regime() == 'STRONG_BULL'
            True
        """
        ctx = self._last_context or {}

        # Priority 1: Read from ChartWindow (set by trigger_regime_analysis())
        # This is the most up-to-date value after regime analysis runs
        # Note: RegimeDisplayMixin stores this in _last_regime_name
        if 'chart_window' in ctx:
            chart_window = ctx['chart_window']
            if hasattr(chart_window, '_last_regime_name'):
                regime = getattr(chart_window, '_last_regime_name', None)
                if regime and regime != 'UNKNOWN':
                    logger.debug(f"last_closed_regime: Read '{regime}' from chart_window._last_regime_name")
                    return str(regime)

        # Priority 2: Try to get from last_closed_candle object
        if 'last_closed_candle' in ctx:
            candle = ctx['last_closed_candle']
            if isinstance(candle, dict) and 'regime' in candle:
                regime = candle['regime']
                logger.debug(f"last_closed_regime: Read '{regime}' from last_closed_candle")
                return str(regime)

        # Priority 3: try to get from chart_data history
        if 'chart_data' in ctx:
            chart_data = ctx['chart_data']
            if isinstance(chart_data, list) and len(chart_data) >= 2:
                # Last closed candle is at index -2 (current candle at -1)
                last_closed = chart_data[-2]
                if isinstance(last_closed, dict) and 'regime' in last_closed:
                    regime = last_closed['regime']
                    logger.debug(f"last_closed_regime: Read '{regime}' from chart_data[-2]")
                    return str(regime)

        # Priority 4: check for prev_regime field
        if 'prev_regime' in ctx:
            regime = ctx['prev_regime']
            logger.debug(f"last_closed_regime: Read '{regime}' from prev_regime")
            return str(regime)

        # Default: unknown
        logger.warning("last_closed_regime: No regime data found, returning 'UNKNOWN'")
        return 'UNKNOWN'

    def _func_new_regime_detected(self) -> bool:
        """Check if a new regime was detected on the last closed candle.

        This function compares the previous regime with the current regime
        to detect regime changes (transitions).

        Returns:
            True if regime changed compared to previous candle,
            False if no change or data unavailable.

        Example:
            >>> # In CEL expression - only enter on regime change:
            >>> trigger_regime_analysis() && new_regime_detected() && last_closed_regime() == 'STRONG_BULL'
            True

            >>> # Enter on any STRONG_BULL, even without regime change:
            >>> trigger_regime_analysis() && last_closed_regime() == 'STRONG_BULL'
            True
        """
        ctx = self._last_context or {}

        # Get previous regime from context
        prev_regime = ctx.get('prev_regime', 'UNKNOWN')

        # Get current regime (uses the same priority logic)
        current_regime = self._func_last_closed_regime()

        # Detect change
        if prev_regime == 'UNKNOWN' or current_regime == 'UNKNOWN':
            # Can't detect change if either is unknown
            return False

        is_new = prev_regime != current_regime
        if is_new:
            logger.info(f"new_regime_detected: Regime changed from '{prev_regime}' to '{current_regime}'")

        return is_new

    # ========================================================================
    # Pattern / Breakout / SMC Helpers
    # ========================================================================

    def _get_context_value(self, key: str) -> Any:
        """Resolve a value from the last evaluation context.

        Supports both flat keys (e.g., "pattern.pin_bar_bullish")
        and nested dicts (e.g., context["pattern"]["pin_bar_bullish"]).
        """
        ctx = self._last_context or {}
        if key in ctx:
            return ctx.get(key)
        if "." in key:
            namespace, sub = key.split(".", 1)
            container = ctx.get(namespace)
            if isinstance(container, dict):
                return container.get(sub)
        return None

    def _context_flag(self, *keys: str) -> bool:
        """Return boolean flag for the first available key."""
        for key in keys:
            value = self._get_context_value(key)
            if value is not None:
                return bool(value)
        return False

    # Pattern functions
    def _func_pin_bar_bullish(self) -> bool:
        return self._context_flag(
            "pattern.pin_bar_bullish", "patterns.pin_bar_bullish", "pin_bar_bullish",
            "pattern.pin_bar", "patterns.pin_bar", "pin_bar"
        )

    def _func_pin_bar_bearish(self) -> bool:
        return self._context_flag(
            "pattern.pin_bar_bearish", "patterns.pin_bar_bearish", "pin_bar_bearish",
            "pattern.pin_bar", "patterns.pin_bar", "pin_bar"
        )

    def _func_inside_bar(self) -> bool:
        return self._context_flag("pattern.inside_bar", "patterns.inside_bar", "inside_bar")

    def _func_inverted_hammer(self) -> bool:
        return self._context_flag("pattern.inverted_hammer", "patterns.inverted_hammer", "inverted_hammer")

    def _func_bull_flag(self) -> bool:
        return self._context_flag("pattern.bull_flag", "patterns.bull_flag", "bull_flag")

    def _func_bear_flag(self) -> bool:
        return self._context_flag("pattern.bear_flag", "patterns.bear_flag", "bear_flag")

    def _func_cup_and_handle(self) -> bool:
        return self._context_flag("pattern.cup_and_handle", "patterns.cup_and_handle", "cup_and_handle")

    def _func_double_bottom(self) -> bool:
        return self._context_flag("pattern.double_bottom", "patterns.double_bottom", "double_bottom")

    def _func_double_top(self) -> bool:
        return self._context_flag("pattern.double_top", "patterns.double_top", "double_top")

    def _func_ascending_triangle(self) -> bool:
        return self._context_flag("pattern.ascending_triangle", "patterns.ascending_triangle", "ascending_triangle")

    def _func_descending_triangle(self) -> bool:
        return self._context_flag("pattern.descending_triangle", "patterns.descending_triangle", "descending_triangle")

    # Breakout functions
    def _func_breakout_above(self) -> bool:
        return self._context_flag("breakout.breakout_above", "pattern.breakout_above", "breakout_above")

    def _func_breakdown_below(self) -> bool:
        return self._context_flag("breakout.breakdown_below", "pattern.breakdown_below", "breakdown_below")

    def _func_false_breakout(self) -> bool:
        return self._context_flag("breakout.false_breakout", "pattern.false_breakout", "false_breakout")

    def _func_break_of_structure(self) -> bool:
        return self._context_flag("breakout.break_of_structure", "pattern.break_of_structure", "break_of_structure")

    # Smart Money Concepts
    def _func_liquidity_swept(self) -> bool:
        return self._context_flag("smc.liquidity_swept", "pattern.liquidity_swept", "liquidity_swept")

    def _func_fvg_exists(self) -> bool:
        return self._context_flag("smc.fvg_exists", "pattern.fvg_exists", "fvg_exists")

    def _func_order_block_retest(self) -> bool:
        return self._context_flag("smc.order_block_retest", "pattern.order_block_retest", "order_block_retest")

    def _func_harmonic_pattern_detected(self) -> bool:
        return self._context_flag(
            "smc.harmonic_pattern_detected", "pattern.harmonic_pattern_detected", "harmonic_pattern_detected"
        )

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
