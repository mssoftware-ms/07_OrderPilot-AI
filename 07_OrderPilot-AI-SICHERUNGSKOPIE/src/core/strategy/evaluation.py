"""Condition Evaluation Engine.

This module provides condition evaluation functionality for trading strategies,
including logical operators and comparison operations.
"""

import logging
import re
from typing import Any, Dict, Optional

import backtrader as bt

from .definition import (
    Condition, LogicGroup,
    ComparisonOperator, LogicOperator
)
from .compiler import CompilationError

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """Evaluates trading strategy conditions."""

    def __init__(self, strategy: bt.Strategy):
        """Initialize evaluator with strategy context.

        Args:
            strategy: Backtrader strategy instance
        """
        self.strategy = strategy
        self._previous_values: Dict[str, float] = {}

    def evaluate(self, condition: Condition) -> bool:
        """Evaluate a condition.

        Args:
            condition: Condition to evaluate

        Returns:
            Boolean result of evaluation

        Raises:
            CompilationError: If evaluation fails
        """
        try:
            if isinstance(condition, Condition):
                return self._evaluate_comparison(condition)
            elif isinstance(condition, LogicGroup):
                return self._evaluate_logic_group(condition)
            else:
                raise CompilationError(f"Unknown condition type: {type(condition)}")

        except Exception as e:
            raise CompilationError(f"Condition evaluation failed: {e}") from e

    def _evaluate_comparison(self, cond: Condition) -> bool:
        """Evaluate a comparison condition.

        Args:
            cond: Comparison condition to evaluate

        Returns:
            Boolean result
        """
        left_value = self._resolve_operand(cond.left)
        right_value = self._resolve_operand(cond.right)

        return self._apply_comparison_operator(cond.operator, left_value, right_value, cond.left)

    def _apply_comparison_operator(
        self,
        operator: ComparisonOperator,
        left_value: float,
        right_value: float,
        left_operand: str
    ) -> bool:
        """Apply comparison operator to values."""
        result = self._apply_basic_operator(operator, left_value, right_value)
        if result is not None:
            return result
        return self._apply_cross_operator(operator, left_operand, left_value, right_value)

    def _apply_basic_operator(
        self,
        operator: ComparisonOperator,
        left_value: float,
        right_value: float,
    ) -> bool | None:
        if operator == ComparisonOperator.GT:
            return left_value > right_value
        if operator == ComparisonOperator.GTE:
            return left_value >= right_value
        if operator == ComparisonOperator.LT:
            return left_value < right_value
        if operator == ComparisonOperator.LTE:
            return left_value <= right_value
        if operator == ComparisonOperator.EQ:
            return abs(left_value - right_value) < 1e-9
        if operator == ComparisonOperator.NEQ:
            return abs(left_value - right_value) >= 1e-9
        return None

    def _apply_cross_operator(
        self,
        operator: ComparisonOperator,
        left_operand: str,
        left_value: float,
        right_value: float,
    ) -> bool:
        if operator == ComparisonOperator.CROSSES_ABOVE:
            return self._check_cross_above(left_operand, left_value, right_value)
        if operator == ComparisonOperator.CROSSES_BELOW:
            return self._check_cross_below(left_operand, left_value, right_value)
        if operator == ComparisonOperator.CROSSES:
            return (
                self._check_cross_above(left_operand, left_value, right_value)
                or self._check_cross_below(left_operand, left_value, right_value)
            )
        raise CompilationError(f"Unknown operator: {operator}")

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
            if self._is_numeric_string(operand):
                return float(operand)

            # Simple formula support (e.g., "sma_base + (2 * atr)")
            if any(ch in operand for ch in "+-*/()"):
                return self._evaluate_expression(operand)

            # Check data fields
            data_value = self._resolve_data_field(operand)
            if data_value is not None:
                return data_value

            # Check indicators
            indicator_value = self._resolve_indicator(operand)
            if indicator_value is not None:
                return indicator_value

        raise CompilationError(
            f"Cannot resolve operand: {operand}. "
            f"Not a number, data field, or known indicator alias."
        )

    def _is_numeric_string(self, value: str) -> bool:
        """Check if string represents a number."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _resolve_data_field(self, operand: str) -> Optional[float]:
        """Resolve data field (close, open, high, low, volume)."""
        data_fields = {
            "close": self.strategy.data.close[0],
            "open": self.strategy.data.open[0],
            "high": self.strategy.data.high[0],
            "low": self.strategy.data.low[0],
            "volume": self.strategy.data.volume[0],
        }
        return data_fields.get(operand)

    def _resolve_indicator(self, operand: str) -> Optional[float]:
        """Resolve indicator value by alias."""
        alias = operand
        attr = None
        if "." in operand:
            alias, attr = operand.split(".", 1)

        if hasattr(self.strategy, f"ind_{alias}"):
            indicator = getattr(self.strategy, f"ind_{alias}")

            # Handle multi-line indicators
            if isinstance(indicator, bt.indicators.MACD):
                if attr == "histogram":
                    return indicator.histo[0]
                if attr == "signal":
                    return indicator.signal[0]
                return indicator.macd[0]  # Use MACD line by default
            elif isinstance(indicator, bt.indicators.BollingerBands):
                if attr == "upper":
                    return indicator.top[0]
                if attr == "lower":
                    return indicator.bot[0]
                if attr == "middle":
                    return indicator.mid[0]
                return indicator.mid[0]  # Use middle band by default
            elif isinstance(indicator, bt.indicators.Stochastic):
                return indicator.percK[0]  # Use %K by default
            else:
                if attr and hasattr(indicator, attr):
                    return getattr(indicator, attr)[0]
                # Most indicators return single line
                return indicator[0]

        return None

    def _evaluate_expression(self, expr: str) -> float:
        """Evaluate a simple indicator/math expression."""
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_\\.]*", expr)
        resolved = {}
        for token in tokens:
            if token in resolved:
                continue
            resolved[token] = self._resolve_operand(token)

        safe_expr = expr
        for token, value in resolved.items():
            safe_expr = re.sub(rf"\\b{re.escape(token)}\\b", str(value), safe_expr)

        return float(eval(safe_expr, {"__builtins__": {}}, {}))

    def _check_cross_above(self, operand: str, current_value: float, threshold: float) -> bool:
        """Check if operand crossed above threshold.

        Args:
            operand: Operand key for tracking
            current_value: Current value
            threshold: Threshold value

        Returns:
            True if crossed above
        """
        previous_value = self._get_previous_value(operand)
        self._update_previous_value(operand, current_value)

        if previous_value is None:
            return False

        return previous_value <= threshold < current_value

    def _check_cross_below(self, operand: str, current_value: float, threshold: float) -> bool:
        """Check if operand crossed below threshold.

        Args:
            operand: Operand key for tracking
            current_value: Current value
            threshold: Threshold value

        Returns:
            True if crossed below
        """
        previous_value = self._get_previous_value(operand)
        self._update_previous_value(operand, current_value)

        if previous_value is None:
            return False

        return previous_value >= threshold > current_value

    def _get_previous_value(self, operand: str) -> Optional[float]:
        """Get previous value for operand."""
        return self._previous_values.get(operand)

    def _update_previous_value(self, operand: str, value: float):
        """Update previous value for operand."""
        self._previous_values[operand] = value
