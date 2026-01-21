"""Strategy Evaluator - Robustness Validation.

Refactored from strategy_evaluator.py monolith.

Module 2/6 of strategy_evaluator.py split.

Contains:
- Robustness validation against gate criteria
"""

from __future__ import annotations

from .evaluator_types import (
    PerformanceMetrics,
    RobustnessGate,
    RobustnessReport,
    WalkForwardResult,
)


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

    def validate_strategy_robustness(
        self,
        walk_forward_result: WalkForwardResult,
        min_trades: int = 30,
        max_drawdown_threshold: float = 20.0,
        min_sharpe: float = 1.0,
        max_degradation_pct: float = 30.0
    ) -> RobustnessReport:
        """Validate strategy robustness using walk-forward results.

        Args:
            walk_forward_result: Walk-forward analysis result
            min_trades: Minimum total trades required
            max_drawdown_threshold: Maximum allowed drawdown %
            min_sharpe: Minimum Sharpe ratio required
            max_degradation_pct: Maximum allowed OOS degradation %

        Returns:
            RobustnessReport with validation results
        """
        # Extract metrics
        is_metrics = walk_forward_result.in_sample_metrics
        oos_metrics = walk_forward_result.out_of_sample_metrics

        # Calculate combined metrics
        total_trades = is_metrics.total_trades + oos_metrics.total_trades
        max_drawdown_pct = max(
            abs(is_metrics.max_drawdown_pct),
            abs(oos_metrics.max_drawdown_pct)
        )

        # Calculate average Sharpe ratio from rolling OOS periods (more accurate)
        # Use rolling_sharpe list from walk_forward_result
        if walk_forward_result.rolling_sharpe:
            # Filter out 0.0 values (means no Sharpe calculated)
            valid_sharpe = [s for s in walk_forward_result.rolling_sharpe if s != 0.0]
            avg_sharpe_ratio = sum(valid_sharpe) / len(valid_sharpe) if valid_sharpe else 0.0
        elif oos_metrics.sharpe_ratio is not None:
            avg_sharpe_ratio = oos_metrics.sharpe_ratio
        elif is_metrics.sharpe_ratio is not None:
            avg_sharpe_ratio = is_metrics.sharpe_ratio
        else:
            avg_sharpe_ratio = 0.0

        # Get degradation percentage
        degradation_pct = walk_forward_result.get_degradation_pct()

        # Validate criteria
        min_trades_met = total_trades >= min_trades
        max_drawdown_met = max_drawdown_pct <= max_drawdown_threshold
        min_sharpe_met = avg_sharpe_ratio >= min_sharpe
        degradation_acceptable = abs(degradation_pct) <= max_degradation_pct

        # Collect failures and warnings
        failures = []
        warnings = []

        if not min_trades_met:
            failures.append(
                f"Insufficient trades: {total_trades} < {min_trades} required"
            )

        if not max_drawdown_met:
            failures.append(
                f"Excessive drawdown: {max_drawdown_pct:.1f}% > {max_drawdown_threshold:.1f}% threshold"
            )

        if not min_sharpe_met:
            failures.append(
                f"Low Sharpe ratio: {avg_sharpe_ratio:.2f} < {min_sharpe:.2f} minimum"
            )

        if not degradation_acceptable:
            failures.append(
                f"High OOS degradation: {degradation_pct:.1f}% > {max_degradation_pct:.1f}% threshold"
            )

        # Check for warnings
        if oos_metrics.total_trades < 10:
            warnings.append(
                f"Low OOS trade count ({oos_metrics.total_trades}) - results may not be statistically significant"
            )

        if oos_metrics.win_rate < 0.3:
            warnings.append(
                f"Low OOS win rate ({oos_metrics.win_rate:.1%}) - strategy may struggle in live trading"
            )

        if walk_forward_result.periods_passed < walk_forward_result.periods_evaluated * 0.5:
            warnings.append(
                f"Only {walk_forward_result.periods_passed}/{walk_forward_result.periods_evaluated} periods passed validation"
            )

        # Determine overall robustness
        is_robust = (
            min_trades_met and
            max_drawdown_met and
            min_sharpe_met and
            degradation_acceptable
        )

        return RobustnessReport(
            strategy_name=walk_forward_result.strategy_name,
            walk_forward_result=walk_forward_result,
            min_trades_met=min_trades_met,
            max_drawdown_met=max_drawdown_met,
            min_sharpe_met=min_sharpe_met,
            degradation_acceptable=degradation_acceptable,
            total_trades=total_trades,
            max_drawdown_pct=max_drawdown_pct,
            avg_sharpe_ratio=avg_sharpe_ratio,
            degradation_pct=degradation_pct,
            is_robust=is_robust,
            failures=failures,
            warnings=warnings,
        )
