"""Strategy Config - Condition Evaluation Engine.

Refactored from strategy_config.py monolith.

Module 3/4 of strategy_config.py split.

Contains:
- evaluate_condition: Main evaluation dispatcher
- _eval_regime: Regime-based conditions
- _eval_comparison: Indicator comparisons
- _eval_range: Range-based conditions
- _eval_threshold: Threshold conditions
- _get_value: Value extraction helper
- _compare: Comparison operator helper
"""

from __future__ import annotations

import logging

import pandas as pd

from .strategy_config_dataclasses import ConditionRule

logger = logging.getLogger(__name__)


class StrategyConfigEvaluation:
    """Helper für StrategyConfig condition evaluation."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyConfig Instanz
        """
        self.parent = parent

    def evaluate_condition(
        self, condition: ConditionRule, data: pd.Series, regime: str | None = None
    ) -> tuple[bool, str]:
        """
        Evaluiert eine einzelne Bedingung.

        Args:
            condition: Die zu evaluierende Bedingung
            data: Aktuelle Marktdaten (letzte Zeile des DataFrame)
            regime: Aktuelles Market Regime

        Returns:
            Tuple (condition_met, description)
        """
        if not condition.enabled:
            return False, "Condition disabled"

        rule = condition.rule

        try:
            if condition.condition_type == "regime":
                return self._eval_regime(rule, regime)

            elif condition.condition_type == "indicator_comparison":
                return self._eval_comparison(rule, data)

            elif condition.condition_type == "indicator_range":
                return self._eval_range(rule, data)

            elif condition.condition_type == "indicator_threshold":
                return self._eval_threshold(rule, data)

            else:
                logger.warning(f"Unknown condition type: {condition.condition_type}")
                return False, f"Unknown type: {condition.condition_type}"

        except Exception as e:
            logger.error(f"Error evaluating condition {condition.id}: {e}")
            return False, f"Error: {str(e)}"

    def _eval_regime(
        self, rule: dict, regime: str | None
    ) -> tuple[bool, str]:
        """Evaluiert Regime-Bedingung."""
        if regime is None:
            return True, "No regime data"

        not_in = rule.get("not_in", [])
        must_be = rule.get("must_be", [])

        regime_upper = regime.upper()

        if not_in:
            for forbidden in not_in:
                if forbidden.upper() in regime_upper:
                    return False, f"Regime {regime} is forbidden"
            return True, f"Regime {regime} is acceptable"

        if must_be:
            for required in must_be:
                if required.upper() in regime_upper:
                    return True, f"Regime {regime} matches requirement"
            return False, f"Regime {regime} doesn't match requirements"

        return True, "No regime constraints"

    def _eval_comparison(
        self, rule: dict, data: pd.Series
    ) -> tuple[bool, str]:
        """Evaluiert Vergleichs-Bedingung."""
        conditions = rule.get("conditions", [])
        logic = rule.get("logic", "AND")

        results = []
        details = []

        for cond in conditions:
            left_name = cond.get("left", "")
            operator = cond.get("operator", "")
            right_name = cond.get("right", "")

            left_val = self._get_value(left_name, data)
            right_val = self._get_value(right_name, data)

            if left_val is None or right_val is None:
                results.append(False)
                details.append(f"{left_name} or {right_name} not available")
                continue

            result = self._compare(left_val, operator, right_val)
            results.append(result)
            details.append(
                f"{left_name}({left_val:.2f}) {operator} {right_name}({right_val:.2f}) = {result}"
            )

        if logic == "AND":
            final = all(results)
        elif logic == "OR":
            final = any(results)
        else:
            final = all(results)

        return final, "; ".join(details)

    def _eval_range(
        self, rule: dict, data: pd.Series
    ) -> tuple[bool, str]:
        """Evaluiert Bereichs-Bedingung."""
        indicator = rule.get("indicator", "")
        min_val = rule.get("min", float("-inf"))
        max_val = rule.get("max", float("inf"))

        value = self._get_value(indicator, data)

        if value is None:
            return False, f"{indicator} not available"

        in_range = min_val <= value <= max_val
        return in_range, f"{indicator}={value:.2f} (range: {min_val}-{max_val})"

    def _eval_threshold(
        self, rule: dict, data: pd.Series
    ) -> tuple[bool, str]:
        """Evaluiert Schwellwert-Bedingung."""
        indicator = rule.get("indicator", "")
        operator = rule.get("operator", ">")
        threshold = rule.get("threshold", 0)

        value = self._get_value(indicator, data)

        if value is None:
            return False, f"{indicator} not available"

        result = self._compare(value, operator, threshold)
        return result, f"{indicator}={value:.2f} {operator} {threshold}"

    def _get_value(self, name: str, data: pd.Series) -> float | None:
        """Holt Wert aus Daten (mit verschiedenen Namenskonventionen)."""
        if name == "price":
            return data.get("close")

        # Versuche verschiedene Namenskonventionen
        variations = [
            name,
            name.lower(),
            name.upper(),
            name.replace("_", ""),
            f"{name}_14",  # z.B. rsi -> rsi_14
            f"{name.upper()}_14",
        ]

        for var in variations:
            val = data.get(var)
            if val is not None:
                return float(val)

        return None

    def _compare(self, left: float, operator: str, right: float) -> bool:
        """Führt Vergleich durch."""
        ops = {
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: abs(a - b) < 0.0001,
            "!=": lambda a, b: abs(a - b) >= 0.0001,
        }
        return ops.get(operator, lambda a, b: False)(left, right)
