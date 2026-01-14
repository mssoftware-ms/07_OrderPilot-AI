"""
Strategy Selector Guards - Reselection Guards & Result Creation.

Refactored from strategy_selector.py.

Contains:
- should_reselect: Check if reselection is needed
- create_selection_result: Create SelectionResult with lock
- create_fallback_result: Create fallback result
- save_selection: Persist selection snapshot
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .strategy_selector_models import SelectionResult, SelectionSnapshot

if TYPE_CHECKING:
    from .models import RegimeState, RegimeType
    from .strategy_catalog import StrategyDefinition
    from .strategy_evaluator import WalkForwardResult
    from .strategy_selector import StrategySelector

logger = logging.getLogger(__name__)


class StrategySelectorGuards:
    """Helper for reselection guards and result creation."""

    # Fallback strategy per regime when no strategy passes validation
    DEFAULT_FALLBACK = {
        "TREND_UP": "trend_following_conservative",
        "TREND_DOWN": "trend_following_conservative",
        "RANGE": "mean_reversion_bb",
        "UNKNOWN": None,  # No trading in unknown regime
    }

    def __init__(self, parent: StrategySelector):
        self.parent = parent

    def should_reselect(self, regime: RegimeState, now: datetime) -> bool:
        """Check if we should re-select strategy."""
        from .models import RegimeType, VolatilityLevel

        # First selection
        if self.parent._current_selection is None:
            return True

        # Check lock
        if self.parent._current_selection.locked_until:
            if now < self.parent._current_selection.locked_until:
                return False

        # Daily selection - new day
        if self.parent._selection_date:
            if now.date() > self.parent._selection_date.date():
                return True

        # Intraday switch allowed?
        if not self.parent.allow_intraday_switch:
            return False

        # Regime flip check
        if self.parent.require_regime_flip_for_switch and self.parent._last_regime:
            # Only re-select on significant regime change
            prev = self.parent._last_regime
            significant_change = (
                (prev.is_trending and not regime.is_trending)
                or (not prev.is_trending and regime.is_trending)
                or (
                    prev.regime != regime.regime
                    and prev.regime != RegimeType.UNKNOWN
                    and regime.regime != RegimeType.UNKNOWN
                )
                or (
                    prev.volatility == VolatilityLevel.EXTREME
                    and regime.volatility != VolatilityLevel.EXTREME
                )
            )
            return significant_change

        return False

    def create_selection_result(
        self,
        strategy: StrategyDefinition,
        regime: RegimeState,
        wf_result: WalkForwardResult | None,
        scores: dict[str, float],
        candidates_count: int,
        passed_count: int,
    ) -> SelectionResult:
        """Create selection result."""
        # Calculate lock until (15 minutes from now for faster market adaptation)
        # Changed from daily lock (23:59:59) to 15-minute intervals to better
        # respond to intraday market condition changes
        now = datetime.utcnow()
        lock_until = now + timedelta(minutes=15)

        result = SelectionResult(
            selected_strategy=strategy.profile.name,
            regime=regime.regime,
            volatility=regime.volatility,
            candidates_evaluated=candidates_count,
            candidates_passed=passed_count,
            strategy_scores=scores,
            locked_until=lock_until,
        )

        if wf_result:
            result.wf_result = {
                "in_sample_pf": wf_result.in_sample_metrics.profit_factor,
                "in_sample_wr": wf_result.in_sample_metrics.win_rate,
                "oos_pf": wf_result.out_of_sample_metrics.profit_factor,
                "robustness_score": wf_result.robustness_score,
            }

        # Update state
        self.parent._current_selection = result
        self.parent._selection_date = now
        self.parent._last_regime = regime

        logger.info(
            f"Selected strategy: {strategy.profile.name} "
            f"(score={scores.get(strategy.profile.name, 0):.3f})"
        )

        return result

    def create_fallback_result(self, regime: RegimeState, reason: str) -> SelectionResult:
        """Create fallback selection result."""
        fallback = self.DEFAULT_FALLBACK.get(regime.regime.value)

        result = SelectionResult(
            selected_strategy=fallback,
            fallback_used=True,
            fallback_reason=reason,
            regime=regime.regime,
            volatility=regime.volatility,
        )

        self.parent._current_selection = result
        self.parent._selection_date = datetime.utcnow()
        self.parent._last_regime = regime

        logger.warning(f"Using fallback strategy: {fallback} (reason: {reason})")

        return result

    def save_selection(self, result: SelectionResult, symbol: str) -> None:
        """Save selection snapshot."""
        if not self.parent.snapshot_dir:
            return

        snapshot = SelectionSnapshot(
            selection_date=result.selection_date,
            symbol=symbol,
            selected_strategy=result.selected_strategy or "none",
            regime=result.regime.value,
            volatility=result.volatility.value,
            in_sample_pf=(
                result.wf_result.get("in_sample_pf", 0) if result.wf_result else 0
            ),
            in_sample_wr=(
                result.wf_result.get("in_sample_wr", 0) if result.wf_result else 0
            ),
            oos_pf=result.wf_result.get("oos_pf") if result.wf_result else None,
            composite_score=(
                result.strategy_scores.get(result.selected_strategy, 0)
                if result.selected_strategy
                else 0
            ),
            robustness_score=(
                result.wf_result.get("robustness_score", 0) if result.wf_result else 0
            ),
            training_window_days=self.parent.evaluator.walk_forward_config.training_window_days,
            test_window_days=self.parent.evaluator.walk_forward_config.test_window_days,
        )

        filename = f"{symbol}_{result.selection_date.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.parent.snapshot_dir / filename

        with open(filepath, "w") as f:
            f.write(snapshot.model_dump_json(indent=2))

        logger.debug(f"Saved selection snapshot: {filepath}")
