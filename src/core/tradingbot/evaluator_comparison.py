"""Strategy Evaluator - Strategy Comparison.

Refactored from strategy_evaluator.py monolith.

Module 6/6 of strategy_evaluator.py split.

Contains:
- Strategy ranking by composite score
"""

from __future__ import annotations

from .evaluator_types import WalkForwardResult


class EvaluatorComparison:
    """Helper für StrategyEvaluator strategy comparison."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyEvaluator Instanz
        """
        self.parent = parent

    def compare_strategies(
        self,
        results: list[WalkForwardResult]
    ) -> list[tuple[str, float]]:
        """Rank strategies by composite score.

        Args:
            results: Walk-forward results for strategies

        Returns:
            List of (strategy_name, score) sorted by score descending
        """
        scores = []

        for result in results:
            if not result.is_robust:
                scores.append((result.strategy_name, 0.0))
                continue

            # Composite score components
            pf_score = min(result.in_sample_metrics.profit_factor / 2.0, 1.0)
            wr_score = result.in_sample_metrics.win_rate
            dd_score = 1 - (abs(result.in_sample_metrics.max_drawdown_pct) / 20.0)
            dd_score = max(0, min(1, dd_score))
            robust_score = result.robustness_score

            # OOS bonus/penalty
            oos_bonus = 0.0
            if result.out_of_sample_metrics.total_trades > 0:
                if result.out_of_sample_metrics.profit_factor >= 1.0:
                    oos_bonus = 0.2
                elif result.out_of_sample_metrics.net_profit > 0:
                    oos_bonus = 0.1

            # Weighted composite
            composite = (
                pf_score * 0.30 +
                wr_score * 0.20 +
                dd_score * 0.20 +
                robust_score * 0.20 +
                oos_bonus * 0.10
            )

            scores.append((result.strategy_name, composite))

        return sorted(scores, key=lambda x: x[1], reverse=True)
