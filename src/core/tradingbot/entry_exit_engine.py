"""Entry/Exit Engine for Tradingbot.

Handles trailing stop management and coordinates entry scoring
and exit signal checking through specialized components.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- entry_scorer.py: EntryScorer class
- exit_checker.py: ExitSignalChecker class
- entry_exit_engine.py: EntryExitEngine + TrailingStopManager (this file)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from .config import TrailingMode
from .entry_scorer import EntryScorer, EntryScoreResult
from .exit_checker import ExitSignalChecker, ExitSignalResult, ExitReason
from .models import (
    FeatureVector,
    PositionState,
    RegimeState,
    Signal,
    TradeSide,
    TrailingState,
)

logger = logging.getLogger(__name__)


@dataclass
class TrailingStopResult:
    """Result of trailing stop calculation."""
    new_stop: float | None = None
    reason: str = ""
    distance_pct: float = 0.0

class TrailingStopManager:
    """Manages trailing stop updates for positions."""

    def __init__(
        self,
        min_step_pct: float = 0.1,
        update_cooldown_bars: int = 3,
        activation_pct: float = 0.0
    ):
        """Initialize trailing stop manager.

        Args:
            min_step_pct: Minimum step size as percentage
            update_cooldown_bars: Bars between updates
            activation_pct: Minimum profit % before trailing activates
        """
        self.min_step_pct = min_step_pct
        self.update_cooldown_bars = update_cooldown_bars
        self.activation_pct = activation_pct

    def calculate_trailing_stop(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState,
        current_bar: int
    ) -> TrailingStopResult:
        """Calculate new trailing stop price.

        Trailing stop is only activated when position is in profit.
        Until then, the initial stop loss remains active.

        Args:
            features: Current features
            position: Current position
            regime: Current regime
            current_bar: Current bar index

        Returns:
            TrailingStopResult with new stop price if applicable
        """
        # Only activate trailing when position reaches activation threshold
        # Until then, the initial stop loss protects against losses
        entry_price = position.entry_price
        current_price = features.close

        if position.side == TradeSide.LONG:
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100

        if profit_pct < self.activation_pct:
            # Position not yet at activation threshold - keep initial stop loss
            return TrailingStopResult()

        # Check cooldown
        bars_since_update = current_bar - position.trailing.last_update_bar
        if bars_since_update < self.update_cooldown_bars:
            return TrailingStopResult()

        mode = position.trailing.mode

        if mode == TrailingMode.PCT:
            return self._trailing_pct(features, position, regime)
        elif mode == TrailingMode.ATR:
            return self._trailing_atr(features, position, regime)
        elif mode == TrailingMode.SWING:
            return self._trailing_swing(features, position)

        return TrailingStopResult()

    def _trailing_pct(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState
    ) -> TrailingStopResult:
        """Percentage-based trailing stop."""
        # Base distance
        distance_pct = 2.0  # 2% default

        # Adjust by volatility
        if regime.volatility == VolatilityLevel.HIGH:
            distance_pct *= 1.3
        elif regime.volatility == VolatilityLevel.EXTREME:
            distance_pct *= 1.5
        elif regime.volatility == VolatilityLevel.LOW:
            distance_pct *= 0.8

        if position.side == TradeSide.LONG:
            new_stop = position.trailing.highest_price * (1 - distance_pct / 100)
            if new_stop > position.trailing.current_stop_price:
                step_pct = ((new_stop - position.trailing.current_stop_price) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="PCT trailing update",
                        distance_pct=distance_pct
                    )
        else:
            new_stop = position.trailing.lowest_price * (1 + distance_pct / 100)
            if new_stop < position.trailing.current_stop_price:
                step_pct = ((position.trailing.current_stop_price - new_stop) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="PCT trailing update",
                        distance_pct=distance_pct
                    )

        return TrailingStopResult()

    def _trailing_atr(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState
    ) -> TrailingStopResult:
        """ATR-based trailing stop."""
        if features.atr_14 is None:
            return TrailingStopResult()

        # Base ATR multiple
        atr_multiple = 2.0

        # Adjust by regime
        if regime.is_trending:
            atr_multiple *= 1.2  # Wider in trends
        if regime.volatility == VolatilityLevel.HIGH:
            atr_multiple *= 1.3
        elif regime.volatility == VolatilityLevel.EXTREME:
            atr_multiple *= 1.5
        elif regime.volatility == VolatilityLevel.LOW:
            atr_multiple *= 0.8

        distance = features.atr_14 * atr_multiple

        if position.side == TradeSide.LONG:
            new_stop = position.trailing.highest_price - distance
            if new_stop > position.trailing.current_stop_price:
                step_pct = ((new_stop - position.trailing.current_stop_price) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason=f"ATR trailing ({atr_multiple:.1f}x ATR)",
                        distance_pct=(distance / features.close) * 100
                    )
        else:
            new_stop = position.trailing.lowest_price + distance
            if new_stop < position.trailing.current_stop_price:
                step_pct = ((position.trailing.current_stop_price - new_stop) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason=f"ATR trailing ({atr_multiple:.1f}x ATR)",
                        distance_pct=(distance / features.close) * 100
                    )

        return TrailingStopResult()

    def _trailing_swing(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> TrailingStopResult:
        """Swing/structure-based trailing stop using BB."""
        if features.bb_lower is None or features.bb_upper is None:
            return TrailingStopResult()

        buffer = features.atr_14 * 0.3 if features.atr_14 else features.close * 0.003

        if position.side == TradeSide.LONG:
            # Use BB lower as support
            new_stop = features.bb_lower - buffer
            if new_stop > position.trailing.current_stop_price:
                step_pct = ((new_stop - position.trailing.current_stop_price) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="Swing trailing (BB support)",
                        distance_pct=((features.close - new_stop) / features.close) * 100
                    )
        else:
            # Use BB upper as resistance
            new_stop = features.bb_upper + buffer
            if new_stop < position.trailing.current_stop_price:
                step_pct = ((position.trailing.current_stop_price - new_stop) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="Swing trailing (BB resistance)",
                        distance_pct=((new_stop - features.close) / features.close) * 100
                    )

        return TrailingStopResult()

class EntryExitEngine:
    """Unified engine for entry/exit decisions.

    Combines entry scoring, exit signal checking, and trailing stop
    management into a single interface.
    """

    def __init__(
        self,
        entry_scorer: EntryScorer | None = None,
        exit_checker: ExitSignalChecker | None = None,
        trailing_manager: TrailingStopManager | None = None
    ):
        """Initialize entry/exit engine.

        Args:
            entry_scorer: Entry score calculator
            exit_checker: Exit signal checker
            trailing_manager: Trailing stop manager
        """
        self.entry_scorer = entry_scorer or EntryScorer()
        self.exit_checker = exit_checker or ExitSignalChecker()
        self.trailing_manager = trailing_manager or TrailingStopManager()

        logger.info("EntryExitEngine initialized")

    def evaluate_entry(
        self,
        features: FeatureVector,
        regime: RegimeState,
        strategy: "StrategyDefinition | None" = None
    ) -> tuple[EntryScoreResult, EntryScoreResult]:
        """Evaluate entry scores for both sides.

        Args:
            features: Current features
            regime: Current regime
            strategy: Optional strategy

        Returns:
            (long_score, short_score)
        """
        long_score = self.entry_scorer.calculate_score(
            features, TradeSide.LONG, regime, strategy
        )
        short_score = self.entry_scorer.calculate_score(
            features, TradeSide.SHORT, regime, strategy
        )
        return long_score, short_score

    def check_exit(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState,
        previous_regime: RegimeState | None = None,
        strategy: "StrategyDefinition | None" = None
    ) -> ExitSignalResult:
        """Check for exit signals.

        Args:
            features: Current features
            position: Current position
            regime: Current regime
            previous_regime: Previous regime
            strategy: Optional strategy

        Returns:
            ExitSignalResult
        """
        return self.exit_checker.check_exit(
            features, position, regime, previous_regime, strategy
        )

    def update_trailing_stop(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState,
        current_bar: int
    ) -> TrailingStopResult:
        """Update trailing stop.

        Args:
            features: Current features
            position: Current position
            regime: Current regime
            current_bar: Current bar index

        Returns:
            TrailingStopResult
        """
        return self.trailing_manager.calculate_trailing_stop(
            features, position, regime, current_bar
        )
