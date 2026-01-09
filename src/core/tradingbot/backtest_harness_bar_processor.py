"""Backtest Harness Bar Processor - Bar Processing and State Machine.

Refactored from backtest_harness.py.

Contains:
- process_bar: Process single bar with feature calculation and regime detection
- _process_flat_state: Look for entry signals when no position
- _process_signal_state: Confirm or expire pending signals
- _process_manage_state: Manage open position (trailing stop, exit signals)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import FeatureVector, RegimeState, Signal, TradeSide

if TYPE_CHECKING:
    from .backtest_harness import BacktestHarness

logger = logging.getLogger(__name__)


class BacktestHarnessBarProcessor:
    """Helper for bar processing and state machine."""

    def __init__(self, parent: "BacktestHarness"):
        self.parent = parent

    def process_bar(self, bar_idx: int) -> None:
        """Process a single bar.

        Args:
            bar_idx: Bar index in data
        """
        # Calculate features
        data_slice = self.parent._data.iloc[:bar_idx + 1]
        features = self.parent._feature_engine.calculate_features(
            data_slice,
            self.parent.backtest_config.symbol,
            self.parent._state.current_time
        )

        if features is None:
            return

        self.parent._state.features = features

        # Classify regime
        regime = self.parent._regime_engine.classify(features)
        self.parent._state.regime = regime

        # Check no-trade filter
        filter_result = self.parent._no_trade_filter.check(
            features, regime, self.parent._state.current_time
        )

        # State-dependent processing
        if self.parent._state.position and self.parent._state.position.is_open:
            self._process_manage_state(features, regime)
        elif self.parent._state.pending_signal:
            self._process_signal_state(features, regime, filter_result.can_trade)
        else:
            if filter_result.can_trade:
                self._process_flat_state(features, regime)

    def _process_flat_state(
        self,
        features: FeatureVector,
        regime: RegimeState
    ) -> None:
        """Process bar in FLAT state (look for entries)."""
        # Get current strategy
        strategy = self.parent._strategy_selector.get_current_strategy(regime)
        if not strategy:
            return

        # Score entry for both sides
        for side in [TradeSide.LONG, TradeSide.SHORT]:
            score_result = self.parent._entry_scorer.calculate_score(
                features, side, regime, strategy
            )

            if score_result.meets_threshold:
                # Create signal
                signal = Signal(
                    symbol=self.parent.backtest_config.symbol,
                    side=side,
                    entry_price=features.close,
                    stop_loss_price=self.parent._helpers.calculate_initial_stop(
                        features, side, regime
                    ),
                    score=score_result.score,
                    timestamp=self.parent._state.current_time
                )
                self.parent._state.pending_signal = signal
                self.parent._state.signals_generated += 1
                break

    def _process_signal_state(
        self,
        features: FeatureVector,
        regime: RegimeState,
        can_trade: bool
    ) -> None:
        """Process bar in SIGNAL state (confirm or expire)."""
        signal = self.parent._state.pending_signal
        if not signal:
            return

        # Simple confirmation: next bar also favorable
        strategy = self.parent._strategy_selector.get_current_strategy(regime)
        if strategy and can_trade:
            score_result = self.parent._entry_scorer.calculate_score(
                features, signal.side, regime, strategy
            )

            if score_result.meets_threshold:
                # Confirmed - execute entry
                self.parent._execution.execute_entry(signal, features)
                self.parent._state.signals_confirmed += 1

        # Clear signal either way
        self.parent._state.pending_signal = None

    def _process_manage_state(
        self,
        features: FeatureVector,
        regime: RegimeState
    ) -> None:
        """Process bar in MANAGE state (trailing stop, exit signals)."""
        position = self.parent._state.position
        if not position:
            return

        bar = self.parent._state.current_bar

        # Update position tracking
        position.bars_held += 1
        current_price = features.close

        # Check stop hit
        if position.side == TradeSide.LONG:
            if bar["low"] <= position.trailing.current_stop_price:
                self.parent._execution.close_position("STOP_HIT", position.trailing.current_stop_price)
                return
            # Update MFE/MAE
            position.max_favorable_excursion = max(
                position.max_favorable_excursion,
                (bar["high"] - position.entry_price) / position.entry_price
            )
            position.max_adverse_excursion = max(
                position.max_adverse_excursion,
                (position.entry_price - bar["low"]) / position.entry_price
            )
        else:  # SHORT
            if bar["high"] >= position.trailing.current_stop_price:
                self.parent._execution.close_position("STOP_HIT", position.trailing.current_stop_price)
                return
            position.max_favorable_excursion = max(
                position.max_favorable_excursion,
                (position.entry_price - bar["low"]) / position.entry_price
            )
            position.max_adverse_excursion = max(
                position.max_adverse_excursion,
                (bar["high"] - position.entry_price) / position.entry_price
            )

        # Check exit signals
        strategy = self.parent._strategy_selector.get_current_strategy(regime)
        exit_result = self.parent._exit_checker.check_exit(
            features, position, regime, self.parent._state.regime, strategy
        )

        if exit_result.should_exit:
            self.parent._execution.close_position(exit_result.reason.value, current_price)
            return

        # Update trailing stop
        trailing_result = self.parent._trailing_manager.calculate_trailing_stop(
            features, position, regime, bar
        )

        if trailing_result.should_update:
            position.trailing.update_stop(
                trailing_result.new_stop,
                self.parent._state.bar_count,
                self.parent._state.current_time,
                is_long=position.side == TradeSide.LONG
            )
