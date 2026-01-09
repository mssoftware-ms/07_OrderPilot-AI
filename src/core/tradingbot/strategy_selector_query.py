"""
Strategy Selector Query - Query Methods for Current Selection & Strategy Info.

Refactored from strategy_selector.py.

Contains:
- get_current_selection: Get current selection result
- get_current_strategy: Get current strategy definition
- is_trading_allowed: Check if trading is allowed
- get_applicable_strategies: Get applicable strategies for regime
- get_strategy_info: Get detailed strategy info
- get_regime_strategies: Get strategy mapping per regime
- suggest_strategy: Quick strategy suggestion
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import RegimeState, RegimeType
    from .strategy_catalog import StrategyDefinition
    from .strategy_selector import StrategySelector
    from .strategy_selector_models import SelectionResult

logger = logging.getLogger(__name__)


class StrategySelectorQuery:
    """Helper for query methods."""

    def __init__(self, parent: StrategySelector):
        self.parent = parent

    def get_current_selection(self) -> SelectionResult | None:
        """Get current strategy selection.

        Returns:
            Current selection or None
        """
        return self.parent._current_selection

    def get_current_strategy(self) -> StrategyDefinition | None:
        """Get current selected strategy definition.

        Returns:
            StrategyDefinition or None
        """
        if (
            not self.parent._current_selection
            or not self.parent._current_selection.selected_strategy
        ):
            return None
        return self.parent.catalog.get_strategy(
            self.parent._current_selection.selected_strategy
        )

    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed with current selection.

        Returns:
            True if a strategy is selected
        """
        return (
            self.parent._current_selection is not None
            and self.parent._current_selection.selected_strategy is not None
        )

    def get_applicable_strategies(self, regime: RegimeState) -> list[str]:
        """Get strategies applicable for regime.

        Args:
            regime: Market regime

        Returns:
            List of strategy names
        """
        strategies = self.parent.catalog.get_strategies_for_regime(regime)
        return [s.profile.name for s in strategies]

    def get_strategy_info(self, strategy_name: str) -> dict | None:
        """Get detailed info about a strategy.

        Args:
            strategy_name: Strategy name

        Returns:
            Strategy info dict or None
        """
        strategy = self.parent.catalog.get_strategy(strategy_name)
        if not strategy:
            return None

        trades = self.parent._trade_history.get(strategy_name, [])
        metrics = (
            self.parent.evaluator.calculate_metrics(trades) if trades else None
        )

        return {
            "name": strategy.profile.name,
            "type": strategy.strategy_type.value,
            "description": strategy.profile.description,
            "applicable_regimes": [r.value for r in strategy.profile.regimes],
            "applicable_volatility": [v.value for v in strategy.profile.volatility_levels],
            "entry_threshold": strategy.min_entry_score,
            "trailing_mode": strategy.trailing_mode.value,
            "stop_loss_pct": strategy.stop_loss_pct,
            "historical_trades": len(trades),
            "metrics": (
                {
                    "profit_factor": metrics.profit_factor if metrics else None,
                    "win_rate": metrics.win_rate if metrics else None,
                    "max_drawdown_pct": metrics.max_drawdown_pct if metrics else None,
                    "expectancy": metrics.expectancy if metrics else None,
                }
                if metrics
                else None
            ),
        }

    def get_regime_strategies(self) -> dict[str, list[str]]:
        """Get strategy mapping per regime.

        Returns:
            Dict mapping regime to applicable strategies
        """
        from .models import RegimeState, RegimeType

        mapping = {}
        for regime_type in RegimeType:
            # Create dummy regime state
            dummy_regime = RegimeState(regime=regime_type)
            strategies = self.parent.catalog.get_strategies_for_regime(dummy_regime)
            mapping[regime_type.value] = [s.profile.name for s in strategies]
        return mapping

    def suggest_strategy(self, regime: RegimeState) -> str | None:
        """Quick suggestion without full evaluation.

        Args:
            regime: Current regime

        Returns:
            Suggested strategy name or None
        """
        candidates = self.parent.catalog.get_strategies_for_regime(regime)

        if not candidates:
            return self.parent._guards.DEFAULT_FALLBACK.get(regime.regime.value)

        # Return highest-rated by historical performance
        best = None
        best_pf = 0

        for strategy in candidates:
            trades = self.parent._trade_history.get(strategy.profile.name, [])
            if trades:
                metrics = self.parent.evaluator.calculate_metrics(trades)
                if metrics.profit_factor > best_pf:
                    best_pf = metrics.profit_factor
                    best = strategy.profile.name

        return best or candidates[0].profile.name
