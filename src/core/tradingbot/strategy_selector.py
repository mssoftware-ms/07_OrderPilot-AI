"""
Strategy Selector for Tradingbot (REFACTORED).

REFACTORED: Split into focused helper modules using composition pattern.

Handles daily strategy selection based on market regime,
historical performance, and walk-forward validation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

# Import models and helpers
from .models import RegimeState
from .strategy_catalog import StrategyCatalog
from .strategy_evaluator import StrategyEvaluator, TradeResult
from .strategy_selector_guards import StrategySelectorGuards
from .strategy_selector_history import StrategySelectorHistory
from .strategy_selector_models import SelectionResult, SelectionSnapshot
from .strategy_selector_query import StrategySelectorQuery
from .strategy_selector_selection import StrategySelectorSelection

# Re-export models for backward compatibility
__all__ = ["StrategySelector", "SelectionResult", "SelectionSnapshot"]

logger = logging.getLogger(__name__)


class StrategySelector:
    """Daily strategy selector (REFACTORED).

    Selects the best strategy for current market conditions
    using walk-forward validation and regime matching.

    Delegiert spezifische Aufgaben an Helper-Klassen.
    """

    def __init__(
        self,
        catalog: StrategyCatalog | None = None,
        evaluator: StrategyEvaluator | None = None,
        snapshot_dir: Path | str | None = None,
        allow_intraday_switch: bool = False,
        require_regime_flip_for_switch: bool = True,
    ):
        """Initialize strategy selector.

        Args:
            catalog: Strategy catalog (creates default if None)
            evaluator: Strategy evaluator (creates default if None)
            snapshot_dir: Directory for selection snapshots
            allow_intraday_switch: Allow strategy switch within day
            require_regime_flip_for_switch: Only switch on significant regime change
        """
        self.catalog = catalog or StrategyCatalog()
        self.evaluator = evaluator or StrategyEvaluator()

        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else None
        if self.snapshot_dir:
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        self.allow_intraday_switch = allow_intraday_switch
        self.require_regime_flip_for_switch = require_regime_flip_for_switch

        # Current selection state
        self._current_selection: SelectionResult | None = None
        self._selection_date: datetime | None = None
        self._last_regime: RegimeState | None = None

        # Trade history cache (for walk-forward)
        self._trade_history: dict[str, list[TradeResult]] = {}

        # Create helpers (composition pattern)
        self._selection = StrategySelectorSelection(self)
        self._guards = StrategySelectorGuards(self)
        self._history = StrategySelectorHistory(self)
        self._query = StrategySelectorQuery(self)

        logger.info(
            f"StrategySelector initialized "
            f"(intraday_switch={allow_intraday_switch}, "
            f"require_flip={require_regime_flip_for_switch})"
        )

    def select_strategy(
        self, regime: RegimeState, symbol: str, force: bool = False
    ) -> SelectionResult:
        """Select best strategy for current conditions.

        Args:
            regime: Current market regime
            symbol: Trading symbol
            force: Force re-selection even if locked

        Returns:
            SelectionResult with selected strategy
        """
        # Guard: Check if we should re-select
        if not force and not self._guards.should_reselect(regime, datetime.utcnow()):
            if self._current_selection:
                return self._current_selection

        logger.info(
            f"Selecting strategy for {symbol} "
            f"(regime={regime.regime.value}, vol={regime.volatility.value})"
        )

        # Get candidates
        candidates = self.catalog.get_strategies_for_regime(regime)
        if not candidates:
            return self._guards.create_fallback_result(
                regime, "No strategies applicable for current regime"
            )

        # Evaluate and filter (delegiert)
        evaluated = self._selection.evaluate_candidates(candidates)
        robust = self._selection.filter_robust_strategies(evaluated)

        if not robust:
            return self._guards.create_fallback_result(
                regime, "No strategies passed robustness validation"
            )

        # Select best (delegiert)
        result = self._selection.select_best_strategy(robust, regime, candidates, symbol)
        return (
            result
            if result
            else self._guards.create_fallback_result(regime, "Selection logic error")
        )

    # ==================== Trade History Management (Delegiert) ====================

    def record_trade(self, strategy_name: str, trade: TradeResult) -> None:
        """Record a trade result for strategy evaluation (delegiert)."""
        return self._history.record_trade(strategy_name, trade)

    def load_trade_history(self, strategy_name: str, trades: list[TradeResult]) -> None:
        """Load historical trades for a strategy (delegiert)."""
        return self._history.load_trade_history(strategy_name, trades)

    def get_trade_history(self, strategy_name: str) -> list[TradeResult]:
        """Get trade history for a strategy (delegiert)."""
        return self._history.get_trade_history(strategy_name)

    # ==================== Query Methods (Delegiert) ====================

    def get_current_selection(self) -> SelectionResult | None:
        """Get current strategy selection (delegiert)."""
        return self._query.get_current_selection()

    def get_current_strategy(self):
        """Get current selected strategy definition (delegiert)."""
        return self._query.get_current_strategy()

    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed with current selection (delegiert)."""
        return self._query.is_trading_allowed()

    def get_applicable_strategies(self, regime: RegimeState) -> list[str]:
        """Get strategies applicable for regime (delegiert)."""
        return self._query.get_applicable_strategies(regime)

    def get_strategy_info(self, strategy_name: str) -> dict | None:
        """Get detailed info about a strategy (delegiert)."""
        return self._query.get_strategy_info(strategy_name)

    def get_regime_strategies(self) -> dict[str, list[str]]:
        """Get strategy mapping per regime (delegiert)."""
        return self._query.get_regime_strategies()

    def suggest_strategy(self, regime: RegimeState) -> str | None:
        """Quick suggestion without full evaluation (delegiert)."""
        return self._query.suggest_strategy(regime)
