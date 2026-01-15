"""Strategy Evaluator - Robustness Validation.

Refactored from strategy_evaluator.py monolith.

Module 2/6 of strategy_evaluator.py split.

Contains:
- Robustness validation against gate criteria
"""

from __future__ import annotations

from .evaluator_types import PerformanceMetrics, RobustnessGate


class EvaluatorValidation:
    """Helper für StrategyEvaluator robustness validation."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyEvaluator Instanz
        """
        self.parent = parent

    def validate_robustness(
        self,
        metrics: PerformanceMetrics,
        gate: RobustnessGate | None = None
    ) -> tuple[bool, list[str]]:
        """Validate metrics against robustness criteria.

        Args:
            metrics: Performance metrics to validate
            gate: Custom robustness gate (uses default if None)

        Returns:
            (is_robust, list of failure reasons)
        """
        gate = gate or self.parent.robustness_gate
        failures = []

        if metrics.total_trades < gate.min_trades:
            failures.append(
                f"Insufficient trades: {metrics.total_trades} < {gate.min_trades}"
            )

        if metrics.profit_factor < gate.min_profit_factor:
            failures.append(
                f"Low profit factor: {metrics.profit_factor:.2f} < {gate.min_profit_factor}"
            )

        if abs(metrics.max_drawdown_pct) > gate.max_drawdown_pct:
            failures.append(
                f"High drawdown: {abs(metrics.max_drawdown_pct):.1f}% > {gate.max_drawdown_pct}%"
            )

        if metrics.win_rate < gate.min_win_rate:
            failures.append(
                f"Low win rate: {metrics.win_rate:.1%} < {gate.min_win_rate:.1%}"
            )

        if metrics.expectancy < gate.min_expectancy:
            failures.append(
                f"Low expectancy: {metrics.expectancy:.2f} < {gate.min_expectancy}"
            )

        return len(failures) == 0, failures
