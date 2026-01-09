"""
Bot State Handlers Flat - FLAT State Processing (Entry Signal Detection).

Refactored from bot_state_handlers.py.

Contains:
- process_flat: Main FLAT state processor
- check_strategy_selection: Daily strategy selection
- Trade blocking helpers
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from .models import BotAction, FeatureVector, SignalType, TradeSide

if TYPE_CHECKING:
    from .bot_state_handlers import BotStateHandlersMixin
    from .models import BotDecision

logger = logging.getLogger(__name__)


class BotStateHandlersFlat:
    """Helper for FLAT state processing."""

    def __init__(self, parent: BotStateHandlersMixin):
        self.parent = parent

    async def process_flat(self, features: FeatureVector) -> BotDecision | None:
        """Process FLAT state - look for entry signals.

        Args:
            features: Current feature vector

        Returns:
            BotDecision or None
        """
        if not self.parent.can_trade:
            reasons = self._get_trade_block_reasons()
            self._handle_trade_blocked(reasons)
            return None

        # Reset block tracking when trading is possible again
        self._reset_trade_blocked()

        # Calculate entry score
        long_score = self.parent._calculate_entry_score(features, TradeSide.LONG)
        short_score = self.parent._calculate_entry_score(features, TradeSide.SHORT)
        threshold = self.parent._get_entry_threshold()

        # Log scores for transparency
        self.parent._log_activity(
            "SCORE",
            f"Long: {long_score:.3f} | Short: {short_score:.3f} | Threshold: {threshold:.3f}",
        )

        # Get best signal
        side, score = self._select_entry_signal(long_score, short_score, threshold)
        if side is None:
            return self.parent._create_decision(
                BotAction.NO_TRADE,
                TradeSide.NONE,
                features,
                ["SCORE_BELOW_THRESHOLD"],
            )

        # Optional pattern validation BEFORE signal creation (warn-only)
        if self.parent.config.bot.use_pattern_check:
            pattern_ok, pattern_reason = await self.parent._pattern_gate(features, side)
            if not pattern_ok and pattern_reason:
                self.parent._log_activity("PATTERN_WARN", pattern_reason)

        # Create signal
        signal = self.parent._create_signal(features, side, score)
        self.parent._current_signal = signal

        self.parent._log_activity(
            "SIGNAL",
            f"{side.value.upper()} Signal generiert | Score: {score:.3f} | "
            f"Entry: {signal.entry_price:.2f} | SL: {signal.stop_loss_price:.2f}",
        )

        if self.parent._on_signal:
            self.parent._on_signal(signal)

        # Transition to SIGNAL state
        self.parent._state_machine.on_signal(signal, confirmed=False)

        return self.parent._create_decision(
            BotAction.NO_TRADE,  # Signal detected, not entry yet
            side,
            features,
            ["SIGNAL_DETECTED"],
            notes=f"Signal {signal.id}: {side.value} score={score:.2f}",
        )

    async def check_strategy_selection(self, features: FeatureVector) -> None:
        """Check if strategy selection is needed (daily or forced).

        Args:
            features: Current feature vector
        """
        now = datetime.utcnow()

        # Check if new day or forced reselection
        needs_selection = (
            self.parent._active_strategy is None
            or self.parent._last_strategy_selection_date is None
            or now.date() > self.parent._last_strategy_selection_date.date()
        )

        if not needs_selection:
            return

        # Select best strategy for current regime
        try:
            result = self.parent._strategy_selector.select_strategy(
                regime=self.parent._regime, symbol=self.parent.symbol
            )

            if result.selected_strategy:
                # Look up StrategyProfile from catalog (result.selected_strategy is a string name)
                strategy_def = self.parent._strategy_catalog.get_strategy(
                    result.selected_strategy
                )
                if strategy_def:
                    self.parent._active_strategy = strategy_def.profile
                    self.parent._last_strategy_selection_date = now

                    self.parent._log_activity(
                        "STRATEGY",
                        f"Tagesstrategie gewaehlt: {self.parent._active_strategy.name} | "
                        f"Score: {result.strategy_scores.get(result.selected_strategy, 0):.2f} | "
                        f"Regime: {self.parent._regime.regime.value}",
                    )
                else:
                    self.parent._log_activity(
                        "ERROR",
                        f"Strategie '{result.selected_strategy}' nicht im Katalog gefunden",
                    )

        except Exception as e:
            self.parent._log_activity("ERROR", f"Strategie-Auswahl fehlgeschlagen: {e}")
            # Fallback to first available strategy
            strategies = self.parent._strategy_catalog.get_all_strategies()
            if strategies:
                # strategies[0] is StrategyDefinition, need .profile for StrategyProfile
                self.parent._active_strategy = strategies[0].profile
                self.parent._log_activity(
                    "STRATEGY", f"Fallback-Strategie: {self.parent._active_strategy.name}"
                )

    def _get_trade_block_reasons(self) -> list[str]:
        """Get reasons why trading is blocked."""
        reasons: list[str] = []
        if not self.parent._running:
            reasons.append("Bot nicht gestartet")
        if self.parent._state_machine.is_paused():
            reasons.append("Bot pausiert")
        if self.parent._state_machine.is_error():
            reasons.append("Bot im Fehlerzustand")
        if not self.parent.config.bot.disable_restrictions:
            if self.parent._trades_today >= self.parent.config.risk.max_trades_per_day:
                reasons.append(
                    f"Max Trades erreicht ({self.parent._trades_today}/{self.parent.config.risk.max_trades_per_day})"
                )
            account_value = 10000.0
            daily_pnl_pct = (self.parent._daily_pnl / account_value) * 100
            if daily_pnl_pct <= -self.parent.config.risk.max_daily_loss_pct:
                reasons.append(f"Tagesverlust-Limit ({daily_pnl_pct:.2f}%)")
            if (
                self.parent._consecutive_losses
                >= self.parent.config.risk.loss_streak_cooldown
            ):
                reasons.append(
                    f"Verlustserie ({self.parent._consecutive_losses} in Folge)"
                )
        return reasons

    def _handle_trade_blocked(self, reasons: list[str]) -> None:
        """Handle trade blocking."""
        if (
            self.parent._trading_blocked
            and reasons == self.parent._last_block_reasons
        ):
            return
        self.parent._trading_blocked = True
        self.parent._last_block_reasons = reasons.copy()
        self.parent._log_activity(
            "BLOCKED",
            f"Trading blockiert: {', '.join(reasons) if reasons else 'unknown'}",
        )

        if self.parent._on_trading_blocked and reasons:
            try:
                self.parent._on_trading_blocked(reasons)
            except Exception as e:
                logger.error(f"Trading blocked callback error: {e}")

    def _reset_trade_blocked(self) -> None:
        """Reset trade blocking state."""
        if not self.parent._trading_blocked:
            return
        self.parent._trading_blocked = False
        self.parent._last_block_reasons = []
        self.parent._log_activity("UNBLOCKED", "Trading wieder moeglich")

    def _select_entry_signal(
        self, long_score: float, short_score: float, threshold: float
    ) -> tuple[TradeSide | None, float]:
        """Select best entry signal."""
        if long_score > short_score and long_score >= threshold:
            return TradeSide.LONG, long_score
        if short_score > long_score and short_score >= threshold:
            return TradeSide.SHORT, short_score
        return None, 0.0
