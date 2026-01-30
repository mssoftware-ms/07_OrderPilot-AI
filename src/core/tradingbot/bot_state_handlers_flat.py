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

from .models import BotAction, DirectionalBias, FeatureVector, SignalType, TradeSide

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

        # ===== JSON ENTRY MODE CHECK =====
        # If JSON Entry Mode is active, use JsonEntryScorer instead of normal scoring
        if self.parent._json_entry_mode and self.parent._json_entry_scorer:
            return await self._process_json_entry(features)

        # ===== NORMAL ENTRY MODE (default) =====
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

        # CEL RulePack Integration (Phase 4) - Risk + Entry Packs
        # Check risk and entry rules BEFORE creating signal
        allowed, reason, summary = self.parent._evaluate_rules(
            features,
            pack_types=["risk", "entry"]
        )

        if not allowed:
            # Entry blocked by rules
            self.parent._log_activity(
                "BLOCKED",
                f"Entry blockiert durch RulePack: {reason}"
            )
            logger.info(f"Entry blocked by RulePack: {reason}")
            return self.parent._create_decision(
                BotAction.NO_TRADE,
                side,
                features,
                ["BLOCKED_BY_CEL_RULES"],
                notes=f"RulePack block: {reason}"
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
        """Check and update daily bias for daytrading mode.

        NOTE: Fixed daily strategy selection is DISABLED.
        Instead, calculates directional bias (long/short/neutral) from market regime.
        Strategies change dynamically with market conditions.

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

        # Select strategy and calculate daily bias
        try:
            result = self.parent._strategy_selector.select_strategy(
                regime=self.parent._regime, symbol=self.parent.symbol
            )

            # Calculate daily bias from market regime
            daily_bias = self._calculate_daily_bias(features)
            bias_confidence = self._calculate_bias_confidence(features)

            # Update bias in selection result
            result.daily_bias = daily_bias
            result.bias_confidence = bias_confidence
            result.bias_override_threshold = self.parent.config.bot.bias_override_threshold

            self.parent._last_strategy_selection_date = now

            # Log bias instead of fixed strategy
            self.parent._log_activity(
                "BIAS",
                f"Tages-Bias: {daily_bias.value.upper()} | "
                f"Konfidenz: {bias_confidence:.1%} | "
                f"Override ab: {result.bias_override_threshold:.0%} | "
                f"Regime: {self.parent._regime.regime.value}",
            )

            # Still select a strategy (but not locked - changes with regime)
            if result.selected_strategy:
                strategy_def = self.parent._strategy_catalog.get_strategy(
                    result.selected_strategy
                )
                if strategy_def:
                    self.parent._active_strategy = strategy_def.profile
                    self.parent._log_activity(
                        "STRATEGY",
                        f"Aktuelle Strategie: {self.parent._active_strategy.name} "
                        f"(wechselt mit Marktsituation)",
                    )

        except Exception as e:
            self.parent._log_activity("ERROR", f"Bias/Strategie-Auswahl fehlgeschlagen: {e}")
            # Fallback to first available strategy
            strategies = self.parent._strategy_catalog.get_all_strategies()
            if strategies:
                self.parent._active_strategy = strategies[0].profile
                self.parent._log_activity(
                    "STRATEGY", f"Fallback-Strategie: {self.parent._active_strategy.name}"
                )

    def _calculate_daily_bias(self, features: FeatureVector) -> DirectionalBias:
        """Calculate daily directional bias from market indicators.

        Uses:
        - Market regime (trend direction)
        - Moving average alignment
        - Price vs SMAs

        Returns:
            DirectionalBias (LONG, SHORT, or NEUTRAL)
        """
        regime = self.parent._regime

        # Primary: Use regime direction
        from .models import RegimeType

        if regime.regime == RegimeType.TREND_UP:
            # Uptrend regime -> LONG bias
            return DirectionalBias.LONG
        elif regime.regime == RegimeType.TREND_DOWN:
            # Downtrend regime -> SHORT bias
            return DirectionalBias.SHORT
        elif regime.regime == RegimeType.RANGE:
            # Range-bound -> NEUTRAL (trade both directions)
            return DirectionalBias.NEUTRAL

        # Unknown regime: try to determine from MAs
        if features.sma_20 and features.sma_50:
            if features.sma_20 > features.sma_50 and features.close > features.sma_20:
                return DirectionalBias.LONG
            elif features.sma_20 < features.sma_50 and features.close < features.sma_20:
                return DirectionalBias.SHORT

        return DirectionalBias.NEUTRAL

    def _calculate_bias_confidence(self, features: FeatureVector) -> float:
        """Calculate confidence in daily bias.

        Higher confidence when:
        - Strong ADX (trending market)
        - Clear MA separation
        - Regime confidence is high

        Returns:
            Confidence score (0.0 - 1.0)
        """
        confidence = 0.5  # Base confidence

        regime = self.parent._regime

        # Regime confidence component (0-0.3)
        if regime.regime_confidence:
            confidence += regime.regime_confidence * 0.3

        # ADX component (0-0.2): strong trend = higher confidence
        if features.adx is not None:
            if features.adx > 30:
                confidence += 0.2
            elif features.adx > 20:
                confidence += 0.1

        # MA alignment component (0-0.1)
        if features.sma_20 and features.sma_50:
            ma_separation = abs(features.sma_20 - features.sma_50) / features.sma_50
            if ma_separation > 0.02:  # 2% separation
                confidence += 0.1

        return min(confidence, 1.0)

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
        """Select best entry signal considering daily bias.

        Daytrading mode: Signal direction can be influenced by daily bias.
        - If bias is LONG: prefer long trades, but allow short if score > override threshold
        - If bias is SHORT: prefer short trades, but allow long if score > override threshold
        - If bias is NEUTRAL: select best signal regardless of direction

        Strong signals (above bias_override_threshold) can trade against daily bias.
        """
        # Get daily bias and override threshold
        selection = self.parent._strategy_selector.get_current_selection()
        daily_bias = selection.daily_bias if selection else DirectionalBias.NEUTRAL
        bias_override = self.parent.config.bot.bias_override_threshold

        # Determine if signals meet minimum threshold
        long_valid = long_score >= threshold
        short_valid = short_score >= threshold

        if not long_valid and not short_valid:
            return None, 0.0

        # NEUTRAL bias: simply select best signal (original logic)
        if daily_bias == DirectionalBias.NEUTRAL:
            if long_score > short_score and long_valid:
                return TradeSide.LONG, long_score
            if short_score > long_score and short_valid:
                return TradeSide.SHORT, short_score
            return None, 0.0

        # LONG bias: prefer long, allow short only if score >= override threshold
        if daily_bias == DirectionalBias.LONG:
            if long_valid:
                # Always take a valid long signal when bias is LONG
                self.parent._log_activity(
                    "BIAS", f"Tagestrend LONG -> Long-Signal bevorzugt (Score: {long_score:.3f})"
                )
                return TradeSide.LONG, long_score
            if short_valid and short_score >= bias_override:
                # Allow short against bias if score is very high
                self.parent._log_activity(
                    "BIAS",
                    f"Short-Signal ueberschreibt LONG-Bias (Score: {short_score:.3f} >= {bias_override:.0%})"
                )
                return TradeSide.SHORT, short_score
            # Short signal not strong enough to override LONG bias
            self.parent._log_activity(
                "BIAS",
                f"Short-Signal ignoriert (Score {short_score:.3f} < {bias_override:.0%} Override-Threshold)"
            )
            return None, 0.0

        # SHORT bias: prefer short, allow long only if score >= override threshold
        if daily_bias == DirectionalBias.SHORT:
            if short_valid:
                # Always take a valid short signal when bias is SHORT
                self.parent._log_activity(
                    "BIAS", f"Tagestrend SHORT -> Short-Signal bevorzugt (Score: {short_score:.3f})"
                )
                return TradeSide.SHORT, short_score
            if long_valid and long_score >= bias_override:
                # Allow long against bias if score is very high
                self.parent._log_activity(
                    "BIAS",
                    f"Long-Signal ueberschreibt SHORT-Bias (Score: {long_score:.3f} >= {bias_override:.0%})"
                )
                return TradeSide.LONG, long_score
            # Long signal not strong enough to override SHORT bias
            self.parent._log_activity(
                "BIAS",
                f"Long-Signal ignoriert (Score {long_score:.3f} < {bias_override:.0%} Override-Threshold)"
            )
            return None, 0.0

        # Fallback to best signal
        if long_score > short_score and long_valid:
            return TradeSide.LONG, long_score
        if short_valid:
            return TradeSide.SHORT, short_score
        return None, 0.0

    async def _process_json_entry(self, features: FeatureVector) -> BotDecision | None:
        """Process JSON Entry Mode - evaluate CEL entry_expression.

        Called when JSON Entry Mode is active. Uses JsonEntryScorer to evaluate
        the CEL entry_expression from Regime JSON instead of normal scoring.

        NOTE: Only evaluates on candle-close events, not on every tick.

        Args:
            features: Current feature vector

        Returns:
            BotDecision or None
        """
        # IMPORTANT: Only evaluate CEL expression on candle-close events
        # Skip tick-by-tick updates to avoid redundant evaluations
        if not features.is_candle_close:
            return None  # Not a candle-close event - skip CEL evaluation
        
        logger.info("JSON Entry Mode: Evaluating CEL entry_expression...")

        # Get current regime state
        regime_state = self.parent._regime

        # Get previous regime (for last_closed_regime() function)
        prev_regime = getattr(self.parent, '_prev_regime_name', None)

        # Get chart window reference (for trigger_regime_analysis() in CEL)
        chart_window = getattr(self.parent, '_chart_window', None)
        
        logger.info(f"JSON Entry: chart_window = {type(chart_window).__name__ if chart_window else 'None'}")
        print(f"[JSON_ENTRY] chart_window = {type(chart_window).__name__ if chart_window else 'None'}", flush=True)

        # Evaluate Long Entry
        should_enter_long, long_score, long_reasons = self.parent._json_entry_scorer.should_enter_long(
            features=features,
            regime=regime_state,
            chart_window=chart_window,
            prev_regime=prev_regime
        )

        # Evaluate Short Entry
        should_enter_short, short_score, short_reasons = self.parent._json_entry_scorer.should_enter_short(
            features=features,
            regime=regime_state,
            chart_window=chart_window,
            prev_regime=prev_regime
        )

        # Log evaluation results
        self.parent._log_activity(
            "JSON_ENTRY",
            f"CEL Evaluation | Long: {should_enter_long} (Score: {long_score:.2f}) | "
            f"Short: {should_enter_short} (Score: {short_score:.2f})"
        )

        logger.info(
            f"JSON Entry CEL evaluation: "
            f"Long={should_enter_long} ({long_score:.2f}), "
            f"Short={should_enter_short} ({short_score:.2f})"
        )

        # Determine entry side
        side = None
        score = 0.0
        reasons = []

        if should_enter_long and should_enter_short:
            # Both signals - take the stronger one
            if long_score >= short_score:
                side = TradeSide.LONG
                score = long_score
                reasons = long_reasons
                logger.info("JSON Entry: LONG signal (stronger than Short)")
            else:
                side = TradeSide.SHORT
                score = short_score
                reasons = short_reasons
                logger.info("JSON Entry: SHORT signal (stronger than Long)")
        elif should_enter_long:
            side = TradeSide.LONG
            score = long_score
            reasons = long_reasons
            logger.info("JSON Entry: LONG signal")
        elif should_enter_short:
            side = TradeSide.SHORT
            score = short_score
            reasons = short_reasons
            logger.info("JSON Entry: SHORT signal")
        else:
            # No entry signal
            logger.info("JSON Entry: No entry signal (CEL expression not satisfied)")
            return self.parent._create_decision(
                BotAction.NO_TRADE,
                TradeSide.NONE,
                features,
                ["JSON_ENTRY_NO_MATCH"],
                notes=f"CEL expression not satisfied"
            )

        # CEL RulePack Integration (optional - check risk/entry rules)
        allowed, reason, summary = self.parent._evaluate_rules(
            features,
            pack_types=["risk", "entry"]
        )

        if not allowed:
            self.parent._log_activity(
                "BLOCKED",
                f"JSON Entry blockiert durch RulePack: {reason}"
            )
            logger.info(f"JSON Entry blocked by RulePack: {reason}")
            return self.parent._create_decision(
                BotAction.NO_TRADE,
                side,
                features,
                ["BLOCKED_BY_CEL_RULES"],
                notes=f"RulePack block: {reason}"
            )

        # Create signal
        signal = self.parent._create_signal(features, side, score)
        self.parent._current_signal = signal

        # Log reasons from CEL evaluation
        reasons_str = ", ".join(reasons) if reasons else "CEL expression satisfied"

        self.parent._log_activity(
            "JSON_ENTRY",
            f"{side.value.upper()} Signal generiert (JSON Entry) | "
            f"Score: {score:.2f} | Entry: {signal.entry_price:.2f} | "
            f"SL: {signal.stop_loss_price:.2f} | Reasons: {reasons_str}"
        )

        # Send signal to UI (triggers _on_bot_signal callback)
        if self.parent._on_signal:
            self.parent._on_signal(signal)

        # Transition to SIGNAL state
        self.parent._state_machine.on_signal(signal, confirmed=False)

        return self.parent._create_decision(
            BotAction.NO_TRADE,  # Signal detected, not entry yet
            side,
            features,
            ["JSON_ENTRY_SIGNAL_DETECTED"],
            notes=f"JSON Entry Signal {signal.id}: {side.value} score={score:.2f}, reasons={reasons_str}",
        )
