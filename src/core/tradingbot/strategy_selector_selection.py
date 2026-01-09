"""
Strategy Selector Selection - Main Selection Logic.

Refactored from strategy_selector.py.

Contains:
- Main selection logic (evaluation, filtering, ranking)
- _evaluate_candidates: Walk-forward evaluation
- _filter_robust_strategies: Robustness filtering
- _select_best_strategy: Best strategy selection
- _rank_and_select_best: Ranking-based selection
- _select_first_applicable: Fallback first-applicable selection
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import RegimeState
    from .strategy_catalog import StrategyDefinition
    from .strategy_evaluator import WalkForwardResult
    from .strategy_selector import StrategySelector
    from .strategy_selector_models import SelectionResult

logger = logging.getLogger(__name__)


class StrategySelectorSelection:
    """Helper for main selection logic."""

    def __init__(self, parent: StrategySelector):
        self.parent = parent

    def evaluate_candidates(self, candidates: list) -> list[tuple]:
        """Evaluate each candidate strategy with walk-forward analysis."""
        evaluated = []
        for strategy in candidates:
            trades = self.parent._trade_history.get(strategy.profile.name, [])
            if trades:
                wf_result = self.parent.evaluator.run_walk_forward(strategy, trades)
                evaluated.append((strategy, wf_result))
            else:
                evaluated.append((strategy, None))
        return evaluated

    def filter_robust_strategies(self, evaluated: list[tuple]) -> list[tuple]:
        """Filter to strategies that pass robustness validation."""
        return [(s, r) for s, r in evaluated if r is None or r.is_robust]

    def select_best_strategy(
        self,
        robust: list[tuple],
        regime: RegimeState,
        candidates: list,
        symbol: str,
    ) -> SelectionResult | None:
        """Select best strategy from robust list."""
        # Try ranking approach first
        if any(r for _, r in robust if r is not None):
            result = self._rank_and_select_best(robust, regime, candidates)
            if result:
                self.parent._guards.save_selection(result, symbol)
                return result

        # Fallback: use first applicable
        return self._select_first_applicable(robust, regime, candidates, symbol)

    def _rank_and_select_best(
        self, robust: list[tuple], regime: RegimeState, candidates: list
    ) -> SelectionResult | None:
        """Rank strategies and select best."""
        wf_results = [r for _, r in robust if r is not None]
        rankings = self.parent.evaluator.compare_strategies(wf_results)

        # Find best that's in our robust list
        for strategy_name, score in rankings:
            for strategy, wf_result in robust:
                if strategy.profile.name == strategy_name:
                    return self.parent._guards.create_selection_result(
                        strategy,
                        regime,
                        wf_result,
                        {name: sc for name, sc in rankings},
                        len(candidates),
                        len(robust),
                    )
        return None

    def _select_first_applicable(
        self,
        robust: list[tuple],
        regime: RegimeState,
        candidates: list,
        symbol: str,
    ) -> SelectionResult:
        """Select first applicable strategy (no historical data)."""
        strategy, _ = robust[0]
        result = self.parent._guards.create_selection_result(
            strategy,
            regime,
            None,
            {strategy.profile.name: 0.5},
            len(candidates),
            len(robust),
        )
        self.parent._guards.save_selection(result, symbol)
        return result
