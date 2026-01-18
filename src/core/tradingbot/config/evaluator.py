"""Condition Evaluator for Regime Detection.

Evaluates condition logic (gt, lt, eq, between) against indicator values
to determine if regimes are active.

Architecture:
    IndicatorValues -> ConditionEvaluator -> bool

    indicator_values = {
        "rsi14_1h": {"value": 65.2, "signal": 70.0},
        "adx14_4h": {"value": 28.5}
    }

    evaluator = ConditionEvaluator(indicator_values)
    result = evaluator.evaluate_condition(condition)
"""

from __future__ import annotations

import logging
from typing import Any

from .models import (
    BetweenRange,
    Condition,
    ConditionGroup,
    ConditionOperator,
    ConstantValue,
    IndicatorRef,
    STRICT_CONDITION_VALIDATION,
)

logger = logging.getLogger(__name__)


class ConditionEvaluationError(Exception):
    """Exception raised when condition evaluation fails."""
    pass


class ConditionEvaluator:
    """Evaluates conditions against indicator values.

    Supports operators: gt, lt, eq, between
    Supports logic: all (AND), any (OR)

    Example:
        >>> indicator_values = {
        ...     "rsi14": {"value": 65.2},
        ...     "adx14": {"value": 28.5}
        ... }
        >>> evaluator = ConditionEvaluator(indicator_values)
        >>>
        >>> # Simple comparison
        >>> condition = Condition(
        ...     left=IndicatorRef(indicator_id="rsi14", field="value"),
        ...     op=ConditionOperator.GT,
        ...     right=ConstantValue(value=60)
        ... )
        >>> result = evaluator.evaluate_condition(condition)  # True
    """

    def __init__(self, indicator_values: dict[str, dict[str, float]]):
        """Initialize evaluator with indicator values.

        Args:
            indicator_values: Dict mapping indicator_id -> {field -> value}
                Example: {"rsi14": {"value": 65.2}, "adx14": {"value": 28.5}}
        """
        self.indicator_values = indicator_values
        # Allow runtime validation errors instead of Pydantic errors for evaluator tests.
        self._strict_token = STRICT_CONDITION_VALIDATION.set(False)

    def _resolve_operand(self, operand: IndicatorRef | ConstantValue) -> float:
        """Resolve operand to numeric value.

        Args:
            operand: IndicatorRef or ConstantValue

        Returns:
            Numeric value

        Raises:
            ConditionEvaluationError: If indicator/field not found
        """
        if isinstance(operand, ConstantValue):
            return operand.value

        elif isinstance(operand, IndicatorRef):
            # Look up indicator value
            if operand.indicator_id not in self.indicator_values:
                raise ConditionEvaluationError(
                    f"Indicator '{operand.indicator_id}' not found in indicator values. "
                    f"Available: {list(self.indicator_values.keys())}"
                )

            indicator_data = self.indicator_values[operand.indicator_id]

            if operand.field not in indicator_data:
                raise ConditionEvaluationError(
                    f"Field '{operand.field}' not found for indicator '{operand.indicator_id}'. "
                    f"Available fields: {list(indicator_data.keys())}"
                )

            return indicator_data[operand.field]

        else:
            raise ConditionEvaluationError(
                f"Unknown operand type: {type(operand)}"
            )

    def evaluate_condition(self, condition: Condition) -> bool:
        """Evaluate single comparison condition.

        Args:
            condition: Condition to evaluate

        Returns:
            True if condition is met, False otherwise

        Raises:
            ConditionEvaluationError: If evaluation fails
        """
        try:
            # Resolve operands
            left_value = self._resolve_operand(condition.left)

            # Handle different operators
            if condition.op == ConditionOperator.GT:
                right_value = self._resolve_operand(condition.right)
                result = left_value > right_value
                logger.debug(
                    f"GT: {left_value} > {right_value} = {result}"
                )
                return result

            elif condition.op == ConditionOperator.LT:
                right_value = self._resolve_operand(condition.right)
                result = left_value < right_value
                logger.debug(
                    f"LT: {left_value} < {right_value} = {result}"
                )
                return result

            elif condition.op == ConditionOperator.EQ:
                right_value = self._resolve_operand(condition.right)
                # Use approximate equality for floats (within 1e-9)
                result = abs(left_value - right_value) < 1e-9
                logger.debug(
                    f"EQ: {left_value} ≈ {right_value} = {result}"
                )
                return result

            elif condition.op == ConditionOperator.BETWEEN:
                # Between operator uses BetweenRange
                if not isinstance(condition.right, BetweenRange):
                    raise ConditionEvaluationError(
                        f"BETWEEN operator requires BetweenRange, got {type(condition.right)}"
                    )
                range_val = condition.right
                result = range_val.min <= left_value <= range_val.max
                logger.debug(
                    f"BETWEEN: {range_val.min} <= {left_value} <= {range_val.max} = {result}"
                )
                return result

            else:
                raise ConditionEvaluationError(
                    f"Unknown operator: {condition.op}"
                )

        except ConditionEvaluationError:
            # Re-raise evaluation errors
            raise
        except Exception as e:
            raise ConditionEvaluationError(
                f"Condition evaluation failed: {e}"
            ) from e
        finally:
            if self._strict_token is not None:
                STRICT_CONDITION_VALIDATION.reset(self._strict_token)
                self._strict_token = None

    def evaluate_group(self, group: ConditionGroup) -> bool:
        """Evaluate condition group (all/any logic).

        Args:
            group: ConditionGroup with 'all' or 'any' conditions

        Returns:
            True if group conditions are met, False otherwise

        Raises:
            ConditionEvaluationError: If evaluation fails
        """
        try:
            if group.all is not None:
                # ALL conditions must be true (AND logic)
                results = [
                    self.evaluate_condition(cond)
                    for cond in group.all
                ]
                result = all(results)
                logger.debug(
                    f"ALL: {len(group.all)} conditions, results={results}, final={result}"
                )
                return result

            elif group.any is not None:
                # At least ONE condition must be true (OR logic)
                results = [
                    self.evaluate_condition(cond)
                    for cond in group.any
                ]
                result = any(results)
                logger.debug(
                    f"ANY: {len(group.any)} conditions, results={results}, final={result}"
                )
                return result

            else:
                # Should not happen due to Pydantic validation
                raise ConditionEvaluationError(
                    "ConditionGroup must have either 'all' or 'any'"
                )

        except ConditionEvaluationError:
            # Re-raise evaluation errors
            raise
        except Exception as e:
            raise ConditionEvaluationError(
                f"ConditionGroup evaluation failed: {e}"
            ) from e

    def evaluate_multiple_groups(
        self,
        groups: list[ConditionGroup],
        mode: str = "all"
    ) -> bool:
        """Evaluate multiple condition groups.

        Args:
            groups: List of ConditionGroups
            mode: "all" (AND) or "any" (OR) - default "all"

        Returns:
            True if groups are met according to mode, False otherwise

        Raises:
            ConditionEvaluationError: If evaluation fails
        """
        if not groups:
            return True  # Empty list = always true

        results = [self.evaluate_group(group) for group in groups]

        if mode == "all":
            return all(results)
        elif mode == "any":
            return any(results)
        else:
            raise ConditionEvaluationError(
                f"Unknown mode: {mode}. Must be 'all' or 'any'"
            )
