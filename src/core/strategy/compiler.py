"""Strategy Compiler for converting declarative strategies to Backtrader.

Compiles StrategyDefinition (YAML/JSON) into executable Backtrader strategies.
Handles indicator instantiation, condition evaluation, and signal generation.

Example:
    >>> from src.core.strategy.definition import StrategyDefinition
    >>> from src.core.strategy.compiler import StrategyCompiler
    >>>
    >>> # Load strategy from YAML
    >>> with open("strategies/sma_crossover.yaml") as f:
    ...     strategy_def = StrategyDefinition.from_yaml(f.read())
    >>>
    >>> # Compile to Backtrader strategy class
    >>> compiler = StrategyCompiler()
    >>> strategy_class = compiler.compile(strategy_def)
    >>>
    >>> # Use in Cerebro
    >>> cerebro.addstrategy(strategy_class)
"""

from __future__ import annotations

import logging
from typing import Any, Callable

import backtrader as bt

from .definition import (
    Condition,
    ComparisonOperator,
    IndicatorConfig,
    IndicatorType,
    LogicGroup,
    LogicOperator,
    StrategyDefinition,
)

logger = logging.getLogger(__name__)


class CompilationError(Exception):
    """Exception raised when strategy compilation fails."""
    pass


class IndicatorFactory:
    """Factory for creating Backtrader indicators from IndicatorConfig.

    Maps IndicatorType enum to Backtrader indicator classes.
    """

    # Mapping: IndicatorType -> Backtrader Indicator Class
    # Note: Some indicators require custom implementation if not available in Backtrader
    INDICATOR_MAP: dict[IndicatorType, type[bt.Indicator]] = {
        # Moving Averages
        IndicatorType.SMA: bt.indicators.SimpleMovingAverage,
        IndicatorType.EMA: bt.indicators.ExponentialMovingAverage,
        IndicatorType.WMA: bt.indicators.WeightedMovingAverage,
        IndicatorType.DEMA: bt.indicators.DoubleExponentialMovingAverage,
        IndicatorType.TEMA: bt.indicators.TripleExponentialMovingAverage,

        # Momentum Indicators
        IndicatorType.RSI: bt.indicators.RelativeStrengthIndex,
        IndicatorType.MACD: bt.indicators.MACD,
        IndicatorType.STOCH: bt.indicators.Stochastic,
        IndicatorType.CCI: bt.indicators.CommodityChannelIndex,
        IndicatorType.MOM: bt.indicators.Momentum,
        IndicatorType.ROC: bt.indicators.RateOfChange,

        # Volatility Indicators
        IndicatorType.ATR: bt.indicators.AverageTrueRange,
        IndicatorType.BBANDS: bt.indicators.BollingerBands,
        IndicatorType.STDDEV: bt.indicators.StandardDeviation,

        # Volume Indicators
        # Note: OBV, VWAP, AD, CMF not available in standard Backtrader
        # These would need custom implementation
        # IndicatorType.OBV: bt.indicators.OnBalanceVolume,  # Not available
        # IndicatorType.VWAP: bt.indicators.VWAP,  # Not available
        # IndicatorType.AD: bt.indicators.AccumulationDistribution,  # Not available
        # IndicatorType.CMF: bt.indicators.ChaikinMoneyFlow,  # Not available

        # Trend Indicators
        IndicatorType.ADX: bt.indicators.AverageDirectionalMovementIndex,
        IndicatorType.AROON: bt.indicators.AroonIndicator,
        IndicatorType.PSAR: bt.indicators.ParabolicSAR,

        # Other indicators not in standard Backtrader:
        # IndicatorType.KC: Keltner Channels
        # IndicatorType.PIVOT: Pivot Points
        # IndicatorType.VWMA: Volume Weighted Moving Average
        # IndicatorType.SUPERTREND: SuperTrend
    }

    # Indicators that require full OHLCV data feed, not just a single line
    FULL_DATA_INDICATORS = {
        IndicatorType.ATR,
        IndicatorType.BBANDS,
        IndicatorType.STOCH,
        IndicatorType.PSAR,
    }

    @classmethod
    def create_indicator(
        cls,
        config: IndicatorConfig,
        data: bt.DataBase
    ) -> bt.Indicator:
        """Create Backtrader indicator from configuration.

        Args:
            config: Indicator configuration
            data: Backtrader data feed

        Returns:
            Instantiated Backtrader indicator

        Raises:
            CompilationError: If indicator type is not supported
        """
        indicator_class = cls.INDICATOR_MAP.get(config.type)

        if indicator_class is None:
            raise CompilationError(
                f"Unsupported indicator type: {config.type}. "
                f"Supported types: {list(cls.INDICATOR_MAP.keys())}"
            )

        try:
            # Create indicator with params
            # Most BT indicators accept 'period' param; map to indicator-specific names
            params = cls._normalize_params(config.type, config.params)

            logger.debug(
                f"Creating indicator: {config.alias} = {config.type}({params})"
            )

            # Some indicators need full OHLCV data, others just need a single line
            if config.type in cls.FULL_DATA_INDICATORS:
                # Pass full data feed (ATR, BBANDS, STOCH, etc.)
                return indicator_class(data, **params)
            else:
                # Get specific data source line (default: close)
                if config.source == "close":
                    source = data.close
                elif config.source == "open":
                    source = data.open
                elif config.source == "high":
                    source = data.high
                elif config.source == "low":
                    source = data.low
                elif config.source == "volume":
                    source = data.volume
                else:
                    raise CompilationError(
                        f"Unknown data source: {config.source}. "
                        f"Valid sources: close, open, high, low, volume"
                    )

                return indicator_class(source, **params)

        except Exception as e:
            raise CompilationError(
                f"Failed to create indicator {config.alias} ({config.type}): {e}"
            ) from e

    @classmethod
    def _normalize_params(
        cls,
        indicator_type: IndicatorType,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """Normalize parameter names for different indicators.

        Args:
            indicator_type: Type of indicator
            params: Raw parameters from config

        Returns:
            Normalized parameters for Backtrader
        """
        normalized = {}

        # Handle indicator-specific parameter mappings
        if indicator_type == IndicatorType.MACD:
            # MACD uses period_me1, period_me2, period_signal
            normalized["period_me1"] = params.get("fast", 12)
            normalized["period_me2"] = params.get("slow", 26)
            normalized["period_signal"] = params.get("signal", 9)

        elif indicator_type == IndicatorType.BBANDS:
            # Bollinger Bands uses period, devfactor
            normalized["period"] = params.get("period", 20)
            if "deviation" in params:
                normalized["devfactor"] = params.get("deviation")
            else:
                normalized["devfactor"] = params.get("devfactor", 2.0)

        elif indicator_type == IndicatorType.STOCH:
            # Stochastic uses period, period_dfast, period_dslow
            normalized["period"] = params.get("k_period", params.get("period", 14))
            normalized["period_dfast"] = params.get("d_period", 3)

        else:
            # Default: most indicators use 'period'
            # Just pass through the params
            normalized = params.copy()

        # Backtrader typically expects lowercase param names
        return normalized


class ConditionEvaluator:
    """Evaluates Condition and LogicGroup expressions.

    Recursively evaluates nested logic groups and handles special operators
    like crosses_above, crosses_below, inside, outside.
    """

    def __init__(self, strategy: bt.Strategy):
        """Initialize evaluator.

        Args:
            strategy: Backtrader strategy instance (for accessing indicators)
        """
        self.strategy = strategy
        self._previous_values: dict[str, float] = {}

    def evaluate(self, logic: Condition | LogicGroup) -> bool:
        """Evaluate condition or logic group.

        Args:
            logic: Condition or LogicGroup to evaluate

        Returns:
            Boolean result of evaluation
        """
        if isinstance(logic, Condition):
            return self._evaluate_condition(logic)
        elif isinstance(logic, LogicGroup):
            return self._evaluate_logic_group(logic)
        else:
            raise CompilationError(f"Unknown logic type: {type(logic)}")

    def _evaluate_condition(self, cond: Condition) -> bool:
        """Evaluate a single condition.

        Args:
            cond: Condition to evaluate

        Returns:
            Boolean result
        """
        # Resolve operands
        left_value = self._resolve_operand(cond.left)

        # Handle range operators (inside, outside)
        if cond.operator in (ComparisonOperator.INSIDE, ComparisonOperator.OUTSIDE):
            if not isinstance(cond.right, list) or len(cond.right) != 2:
                raise CompilationError(
                    f"Operator {cond.operator} requires list[low, high] as right operand"
                )
            low, high = cond.right

            if cond.operator == ComparisonOperator.INSIDE:
                return low <= left_value <= high
            else:  # OUTSIDE
                return left_value < low or left_value > high

        # For non-range operators, resolve right operand
        right_value = self._resolve_operand(cond.right)

        # Handle comparison operators
        if cond.operator == ComparisonOperator.GT:
            return left_value > right_value
        elif cond.operator == ComparisonOperator.GTE:
            return left_value >= right_value
        elif cond.operator == ComparisonOperator.LT:
            return left_value < right_value
        elif cond.operator == ComparisonOperator.LTE:
            return left_value <= right_value
        elif cond.operator == ComparisonOperator.EQ:
            return abs(left_value - right_value) < 1e-9  # Float equality
        elif cond.operator == ComparisonOperator.NEQ:
            return abs(left_value - right_value) >= 1e-9

        # Handle cross operators (require previous value tracking)
        elif cond.operator == ComparisonOperator.CROSSES_ABOVE:
            return self._check_cross_above(cond.left, left_value, right_value)
        elif cond.operator == ComparisonOperator.CROSSES_BELOW:
            return self._check_cross_below(cond.left, left_value, right_value)
        elif cond.operator == ComparisonOperator.CROSSES:
            return (
                self._check_cross_above(cond.left, left_value, right_value) or
                self._check_cross_below(cond.left, left_value, right_value)
            )

        else:
            raise CompilationError(f"Unknown operator: {cond.operator}")

    def _evaluate_logic_group(self, group: LogicGroup) -> bool:
        """Evaluate a logic group (AND, OR, NOT).

        Args:
            group: LogicGroup to evaluate

        Returns:
            Boolean result
        """
        results = [self.evaluate(cond) for cond in group.conditions]

        if group.operator == LogicOperator.AND:
            return all(results)
        elif group.operator == LogicOperator.OR:
            return any(results)
        elif group.operator == LogicOperator.NOT:
            return not results[0]  # NOT has exactly 1 condition
        else:
            raise CompilationError(f"Unknown logic operator: {group.operator}")

    def _resolve_operand(self, operand: str | float) -> float:
        """Resolve operand to a numeric value.

        Args:
            operand: Indicator alias or numeric literal

        Returns:
            Numeric value

        Raises:
            CompilationError: If operand cannot be resolved
        """
        # Numeric literal
        if isinstance(operand, (int, float)):
            return float(operand)

        # String: check if numeric
        if isinstance(operand, str):
            try:
                return float(operand)
            except ValueError:
                pass

        # Indicator alias or data field
        if operand == "close":
            return self.strategy.data.close[0]
        elif operand == "open":
            return self.strategy.data.open[0]
        elif operand == "high":
            return self.strategy.data.high[0]
        elif operand == "low":
            return self.strategy.data.low[0]
        elif operand == "volume":
            return self.strategy.data.volume[0]

        # Check indicators
        if hasattr(self.strategy, f"ind_{operand}"):
            indicator = getattr(self.strategy, f"ind_{operand}")

            # Handle MACD (returns multiple lines)
            if isinstance(indicator, bt.indicators.MACD):
                return indicator.macd[0]  # Use MACD line by default

            # Handle Bollinger Bands (returns multiple lines)
            elif isinstance(indicator, bt.indicators.BollingerBands):
                return indicator.mid[0]  # Use middle band by default

            # Handle Stochastic (returns multiple lines)
            elif isinstance(indicator, bt.indicators.Stochastic):
                return indicator.percK[0]  # Use %K by default

            # Most indicators return single line
            else:
                return indicator[0]

        raise CompilationError(
            f"Cannot resolve operand: {operand}. "
            f"Not a number, data field, or known indicator alias."
        )

    def _check_cross_above(
        self,
        key: str | float,
        current_left: float,
        current_right: float
    ) -> bool:
        """Check if left crossed above right.

        Args:
            key: Unique key for tracking (usually left operand)
            current_left: Current left value
            current_right: Current right value

        Returns:
            True if crossed above, False otherwise
        """
        key_str = str(key)
        cross_key = f"{key_str}_cross_above"

        # Need previous values
        prev_left = self._previous_values.get(f"{key_str}_left")
        prev_right = self._previous_values.get(f"{key_str}_right")

        # Update current values
        self._previous_values[f"{key_str}_left"] = current_left
        self._previous_values[f"{key_str}_right"] = current_right

        # First bar: no previous values
        if prev_left is None or prev_right is None:
            return False

        # Check cross: was below, now above
        return prev_left <= prev_right and current_left > current_right

    def _check_cross_below(
        self,
        key: str | float,
        current_left: float,
        current_right: float
    ) -> bool:
        """Check if left crossed below right.

        Args:
            key: Unique key for tracking (usually left operand)
            current_left: Current left value
            current_right: Current right value

        Returns:
            True if crossed below, False otherwise
        """
        key_str = str(key)

        # Need previous values
        prev_left = self._previous_values.get(f"{key_str}_left")
        prev_right = self._previous_values.get(f"{key_str}_right")

        # Update current values
        self._previous_values[f"{key_str}_left"] = current_left
        self._previous_values[f"{key_str}_right"] = current_right

        # First bar: no previous values
        if prev_left is None or prev_right is None:
            return False

        # Check cross: was above, now below
        return prev_left >= prev_right and current_left < current_right


class StrategyCompiler:
    """Compiles StrategyDefinition into executable Backtrader strategies.

    Creates a dynamic Backtrader Strategy class at runtime based on the
    declarative strategy definition.

    Example:
        >>> compiler = StrategyCompiler()
        >>> strategy_class = compiler.compile(strategy_definition)
        >>> cerebro.addstrategy(strategy_class)
    """

    def compile(self, definition: StrategyDefinition) -> type[bt.Strategy]:
        """Compile strategy definition to Backtrader Strategy class.

        Args:
            definition: Validated strategy definition

        Returns:
            Backtrader Strategy class (not instance)

        Raises:
            CompilationError: If compilation fails
        """
        logger.info(f"Compiling strategy: {definition.name} v{definition.version}")

        # Validate definition
        try:
            # Pydantic validation already happened during parsing
            pass
        except Exception as e:
            raise CompilationError(f"Invalid strategy definition: {e}") from e

        # Create dynamic strategy class
        strategy_class = self._create_strategy_class(definition)

        logger.info(
            f"✓ Strategy compiled: {definition.name} "
            f"({len(definition.indicators)} indicators)"
        )

        return strategy_class

    def _create_strategy_class(
        self,
        definition: StrategyDefinition
    ) -> type[bt.Strategy]:
        """Create dynamic Backtrader Strategy class.

        Args:
            definition: Strategy definition

        Returns:
            Strategy class configured with definition
        """
        # Import here to avoid circular imports
        from .compiled_strategy import CompiledStrategy

        # Create a dynamic class that wraps CompiledStrategy with the definition
        class DynamicCompiledStrategy(CompiledStrategy):
            """Strategy class with embedded definition."""

            def __init__(self):
                """Initialize with the compiled definition."""
                super().__init__(definition)

        # Set metadata
        DynamicCompiledStrategy.__strategy_name__ = definition.name
        DynamicCompiledStrategy.__strategy_version__ = definition.version

        return DynamicCompiledStrategy
