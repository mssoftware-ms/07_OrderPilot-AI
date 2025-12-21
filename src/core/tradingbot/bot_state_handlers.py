"""State Processing Mixin for BotController.

Provides state machine processing methods:
- _process_state: Main state dispatcher
- _process_flat: Entry signal detection
- _process_signal: Signal confirmation
- _process_manage: Position management
- _handle_stop_hit: Stop-loss handling
- _handle_exit_signal: Exit signal handling
- _check_exit_signals: Exit condition checking
- _check_strategy_selection: Daily strategy selection
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .models import (
    BotAction,
    BotDecision,
    FeatureVector,
    SignalType,
    TradeSide,
)
from .state_machine import BotState, BotTrigger

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BotStateHandlersMixin:
    """Mixin providing state processing methods.

    Expected attributes from BotController:
        config: FullBotConfig
        symbol: str
        _running: bool
        _state_machine: BotStateMachine
        _regime: RegimeState
        _active_strategy: StrategyProfile | None
        _current_signal: Signal | None
        _position: PositionState | None
        _trades_today: int
        _daily_pnl: float
        _consecutive_losses: int
        _bar_count: int
        _trading_blocked: bool
        _last_block_reasons: list[str]
        _last_strategy_selection_date: datetime | None
        _strategy_selector: StrategySelector
        _strategy_catalog: StrategyCatalog
        _log_activity: Callable[[str, str], None]
        _on_signal: Callable[[Signal], None] | None
        _on_order: Callable[[OrderIntent], None] | None
        _on_trading_blocked: Callable[[list[str]], None] | None
        _on_macd_signal: Callable[[str, float], None] | None
        can_trade: property
    """

    async def _process_state(
        self,
        features: FeatureVector,
        bar: dict[str, Any]
    ) -> BotDecision | None:
        """Process current state and generate decision.

        Args:
            features: Current feature vector
            bar: Current bar data

        Returns:
            BotDecision or None
        """
        state = self._state_machine.state

        # Log state for debugging
        self._log_activity(
            "STATE",
            f"Processing state: {state.value} | Position: {self._position is not None} | "
            f"Bar: O={bar.get('open', 0):.2f} H={bar.get('high', 0):.2f} L={bar.get('low', 0):.2f} C={bar.get('close', 0):.2f}"
        )

        if state == BotState.FLAT:
            return await self._process_flat(features)

        elif state == BotState.SIGNAL:
            return await self._process_signal(features)

        elif state == BotState.ENTERED:
            # Waiting for fill - check timeout
            self._log_activity("DEBUG", "State ENTERED - waiting for fill, no stop check!")
            return None

        elif state == BotState.MANAGE:
            return await self._process_manage(features, bar)

        elif state == BotState.EXITED:
            # Reset for next trade
            self._state_machine.trigger(BotTrigger.RESET)
            return None

        return None

    async def _check_strategy_selection(self, features: FeatureVector) -> None:
        """Check if strategy selection is needed (daily or forced).

        Args:
            features: Current feature vector
        """
        now = datetime.utcnow()

        # Check if new day or forced reselection
        needs_selection = (
            self._active_strategy is None or
            self._last_strategy_selection_date is None or
            now.date() > self._last_strategy_selection_date.date()
        )

        if not needs_selection:
            return

        # Select best strategy for current regime
        try:
            result = self._strategy_selector.select_strategy(
                regime=self._regime,
                symbol=self.symbol
            )

            if result.selected_strategy:
                # Look up StrategyProfile from catalog (result.selected_strategy is a string name)
                strategy_def = self._strategy_catalog.get_strategy(result.selected_strategy)
                if strategy_def:
                    self._active_strategy = strategy_def.profile
                    self._last_strategy_selection_date = now

                    self._log_activity(
                        "STRATEGY",
                        f"Tagesstrategie gewaehlt: {self._active_strategy.name} | "
                        f"Score: {result.strategy_scores.get(result.selected_strategy, 0):.2f} | "
                        f"Regime: {self._regime.regime.value}"
                    )
                else:
                    self._log_activity(
                        "ERROR",
                        f"Strategie '{result.selected_strategy}' nicht im Katalog gefunden"
                    )

        except Exception as e:
            self._log_activity("ERROR", f"Strategie-Auswahl fehlgeschlagen: {e}")
            # Fallback to first available strategy
            strategies = self._strategy_catalog.get_all_strategies()
            if strategies:
                # strategies[0] is StrategyDefinition, need .profile for StrategyProfile
                self._active_strategy = strategies[0].profile
                self._log_activity(
                    "STRATEGY",
                    f"Fallback-Strategie: {self._active_strategy.name}"
                )

    async def _process_flat(self, features: FeatureVector) -> BotDecision | None:
        """Process FLAT state - look for entry signals.

        Args:
            features: Current feature vector

        Returns:
            BotDecision or None
        """
        if not self.can_trade:
            # Log why we can't trade for debugging
            reasons = []
            if not self._running:
                reasons.append("Bot nicht gestartet")
            if self._state_machine.is_paused():
                reasons.append("Bot pausiert")
            if self._state_machine.is_error():
                reasons.append("Bot im Fehlerzustand")
            # Only check restrictions if not disabled
            if not self.config.bot.disable_restrictions:
                if self._trades_today >= self.config.risk.max_trades_per_day:
                    reasons.append(f"Max Trades erreicht ({self._trades_today}/{self.config.risk.max_trades_per_day})")
                account_value = 10000.0
                daily_pnl_pct = (self._daily_pnl / account_value) * 100
                if daily_pnl_pct <= -self.config.risk.max_daily_loss_pct:
                    reasons.append(f"Tagesverlust-Limit ({daily_pnl_pct:.2f}%)")
                if self._consecutive_losses >= self.config.risk.loss_streak_cooldown:
                    reasons.append(f"Verlustserie ({self._consecutive_losses} in Folge)")

            # Only notify once when trading becomes blocked (not every bar)
            if not self._trading_blocked or reasons != self._last_block_reasons:
                self._trading_blocked = True
                self._last_block_reasons = reasons.copy()
                self._log_activity("BLOCKED", f"Trading blockiert: {', '.join(reasons) if reasons else 'unknown'}")

                # Trigger popup callback
                if self._on_trading_blocked and reasons:
                    try:
                        self._on_trading_blocked(reasons)
                    except Exception as e:
                        logger.error(f"Trading blocked callback error: {e}")

            return None

        # Reset block tracking when trading is possible again
        if self._trading_blocked:
            self._trading_blocked = False
            self._last_block_reasons = []
            self._log_activity("UNBLOCKED", "Trading wieder moeglich")

        # Calculate entry score
        long_score = self._calculate_entry_score(features, TradeSide.LONG)
        short_score = self._calculate_entry_score(features, TradeSide.SHORT)
        threshold = self._get_entry_threshold()

        # Log scores for transparency
        self._log_activity(
            "SCORE",
            f"Long: {long_score:.3f} | Short: {short_score:.3f} | Threshold: {threshold:.3f}"
        )

        # Get best signal
        if long_score > short_score and long_score >= threshold:
            side = TradeSide.LONG
            score = long_score
        elif short_score > long_score and short_score >= threshold:
            side = TradeSide.SHORT
            score = short_score
        else:
            # No valid signal
            return self._create_decision(
                BotAction.NO_TRADE,
                TradeSide.NONE,
                features,
                ["SCORE_BELOW_THRESHOLD"]
            )

        # Optional pattern validation BEFORE signal creation (warn-only)
        if self.config.bot.use_pattern_check:
            pattern_ok, pattern_reason = await self._pattern_gate(features, side)
            if not pattern_ok and pattern_reason:
                self._log_activity("PATTERN_WARN", pattern_reason)

        # Create signal
        signal = self._create_signal(features, side, score)
        self._current_signal = signal

        self._log_activity(
            "SIGNAL",
            f"{side.value.upper()} Signal generiert | Score: {score:.3f} | "
            f"Entry: {signal.entry_price:.2f} | SL: {signal.stop_loss_price:.2f}"
        )

        if self._on_signal:
            self._on_signal(signal)

        # Transition to SIGNAL state
        self._state_machine.on_signal(signal, confirmed=False)

        return self._create_decision(
            BotAction.NO_TRADE,  # Signal detected, not entry yet
            side,
            features,
            ["SIGNAL_DETECTED"],
            notes=f"Signal {signal.id}: {side.value} score={score:.2f}"
        )

    async def _process_signal(self, features: FeatureVector) -> BotDecision | None:
        """Process SIGNAL state - confirm or expire signal.

        Args:
            features: Current feature vector

        Returns:
            BotDecision or None
        """
        if not self._current_signal:
            self._state_machine.trigger(BotTrigger.SIGNAL_EXPIRED)
            return None

        # Check signal still valid
        side = self._current_signal.side
        new_score = self._calculate_entry_score(features, side)

        if new_score < self._get_entry_threshold() * 0.9:  # Allow some slack
            # Signal expired
            self._current_signal = None
            self._state_machine.trigger(BotTrigger.SIGNAL_EXPIRED)
            return self._create_decision(
                BotAction.NO_TRADE,
                TradeSide.NONE,
                features,
                ["SIGNAL_EXPIRED"]
            )

        # Confirm signal and enter
        self._current_signal.signal_type = SignalType.CONFIRMED
        self._current_signal.score = new_score
        self._state_machine.on_signal(self._current_signal, confirmed=True)

        # Notify UI that signal is now confirmed
        if self._on_signal:
            self._on_signal(self._current_signal)

        # Get initial stop price from signal BEFORE on_order callback
        # (on_order may call simulate_fill which clears _current_signal)
        initial_stop = self._current_signal.stop_loss_price
        order_id = None

        self._log_activity("DEBUG", f"ENTRY: initial_stop={initial_stop}")

        # Create entry order intent
        order = self._create_entry_order(features, self._current_signal)
        order_id = order.id

        if self._on_order:
            self._on_order(order)

        self._log_activity("DEBUG", f"Creating ENTER decision with stop_after={initial_stop}")
        return self._create_decision(
            BotAction.ENTER,
            side,
            features,
            ["SIGNAL_CONFIRMED", "ENTRY_ORDER_SENT"],
            stop_after=initial_stop,  # Initial stop price for chart display
            notes=f"Entry order: {order_id}, Initial SL: {initial_stop:.4f}"
        )

    async def _process_manage(
        self,
        features: FeatureVector,
        bar: dict[str, Any]
    ) -> BotDecision | None:
        """Process MANAGE state - manage open position.

        Args:
            features: Current feature vector
            bar: Current bar data

        Returns:
            BotDecision or None
        """
        if not self._position:
            logger.error("MANAGE state but no position")
            self._state_machine.error("No position in MANAGE state")
            return None

        close_price = bar.get("close", features.close)
        low_price = bar.get("low", close_price)
        high_price = bar.get("high", close_price)

        # Update position with close price for P&L calculation
        self._position.update_price(close_price)
        self._position.bars_held += 1

        # Check stop hit using the EXTREME price of the candle (LOW for LONG, HIGH for SHORT)
        # This is critical: a candle's low might breach the stop even if close doesn't
        stop_price = self._position.trailing.current_stop_price
        initial_stop = self._position.trailing.initial_stop_price
        stop_hit = False

        # Log stop check details
        side_str = self._position.side.value.upper()
        self._log_activity(
            "STOP_CHECK",
            f"Side={side_str} | Stop={stop_price:.2f} (Initial={initial_stop:.2f}) | "
            f"Candle: H={high_price:.2f} L={low_price:.2f} C={close_price:.2f}"
        )

        if self._position.side == TradeSide.LONG:
            # For LONG: check if LOW breached stop
            if low_price <= stop_price:
                stop_hit = True
                self._log_activity(
                    "STOP",
                    f"🛑 Stop-Loss getroffen! LOW={low_price:.2f} <= Stop={stop_price:.2f} "
                    f"(Close={close_price:.2f})"
                )
        else:
            # For SHORT: check if HIGH breached stop
            if high_price >= stop_price:
                stop_hit = True
                self._log_activity(
                    "STOP",
                    f"🛑 Stop-Loss getroffen! HIGH={high_price:.2f} >= Stop={stop_price:.2f} "
                    f"(Close={close_price:.2f})"
                )

        if stop_hit:
            return await self._handle_stop_hit(features)

        # Check exit signals
        exit_signal = self._check_exit_signals(features)
        if exit_signal:
            return await self._handle_exit_signal(features, exit_signal)

        # Update trailing stop
        new_stop = self._calculate_trailing_stop(features, self._position)
        self._log_activity("DEBUG", f"_calculate_trailing_stop returned: {new_stop}")
        if new_stop:
            old_stop = self._position.trailing.current_stop_price
            is_long = self._position.side == TradeSide.LONG
            self._log_activity(
                "DEBUG",
                f"Calling update_stop: new={new_stop:.4f}, old={old_stop:.4f}, is_long={is_long}"
            )
            updated = self._position.trailing.update_stop(
                new_stop,
                self._bar_count,
                datetime.utcnow(),
                is_long=is_long
            )
            self._log_activity("DEBUG", f"update_stop returned: {updated}")

            if updated:
                self._state_machine.trigger(BotTrigger.STOP_UPDATED)
                return self._create_decision(
                    BotAction.ADJUST_STOP,
                    self._position.side,
                    features,
                    ["TRAILING_STOP_UPDATED"],
                    stop_before=old_stop,
                    stop_after=new_stop
                )

        # Hold position
        return self._create_decision(
            BotAction.HOLD,
            self._position.side,
            features,
            ["POSITION_HELD"]
        )

    async def _handle_stop_hit(self, features: FeatureVector) -> BotDecision:
        """Handle stop-loss hit.

        Args:
            features: Current feature vector

        Returns:
            BotDecision
        """
        self._state_machine.on_stop_hit(features.close)

        pnl = self._position.unrealized_pnl if self._position else 0
        self._daily_pnl += pnl

        if pnl < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        self._trades_today += 1
        side = self._position.side if self._position else TradeSide.NONE

        # Determine if this was initial stop (SL) or trailing stop (TS)
        # Trailing stop is active if the stop was moved from initial position
        is_trailing_stop = False
        if self._position and self._position.trailing:
            initial_stop = self._position.trailing.initial_stop_price
            current_stop = self._position.trailing.current_stop_price
            # If stop was moved (trailing activated), it's a TS exit
            if abs(current_stop - initial_stop) > 0.0001:
                is_trailing_stop = True

        self._position = None

        reason_codes = ["TRAILING_STOP_HIT", "POSITION_CLOSED"] if is_trailing_stop else ["STOP_HIT", "POSITION_CLOSED"]
        stop_type = "Trailing Stop" if is_trailing_stop else "Stop Loss"

        return self._create_decision(
            BotAction.EXIT,
            side,
            features,
            reason_codes,
            notes=f"{stop_type} hit, P&L: {pnl:.2f}"
        )

    async def _handle_exit_signal(
        self,
        features: FeatureVector,
        reason: str
    ) -> BotDecision:
        """Handle exit signal.

        Args:
            features: Current feature vector
            reason: Exit reason

        Returns:
            BotDecision
        """
        self._state_machine.on_exit_signal(reason)

        pnl = self._position.unrealized_pnl if self._position else 0
        self._daily_pnl += pnl

        if pnl < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        self._trades_today += 1
        side = self._position.side if self._position else TradeSide.NONE
        self._position = None

        return self._create_decision(
            BotAction.EXIT,
            side,
            features,
            [reason.upper(), "POSITION_CLOSED"],
            notes=f"P&L: {pnl:.2f}"
        )

    # ==================== Exit Signals ====================

    def _check_exit_signals(self, features: FeatureVector) -> str | None:
        """Check for exit signals.

        Args:
            features: Current features

        Returns:
            Exit reason or None
        """
        if not self._position:
            return None

        # Momentum reversal
        if features.rsi_14 is not None:
            if self._position.side == TradeSide.LONG and features.rsi_14 > 80:
                return "RSI_EXTREME_OVERBOUGHT"
            elif self._position.side == TradeSide.SHORT and features.rsi_14 < 20:
                return "RSI_EXTREME_OVERSOLD"

        # MACD cross - always detect and notify, but optionally don't exit
        if features.macd is not None and features.macd_signal is not None:
            macd_signal_type = None

            if self._position.side == TradeSide.LONG:
                if features.macd < features.macd_signal and features.macd_hist and features.macd_hist < 0:
                    macd_signal_type = "MACD_BEARISH_CROSS"
            else:  # SHORT position
                if features.macd > features.macd_signal and features.macd_hist and features.macd_hist > 0:
                    macd_signal_type = "MACD_BULLISH_CROSS"

            if macd_signal_type:
                # Always notify for chart marker (even if exit is disabled)
                if self._on_macd_signal:
                    try:
                        self._on_macd_signal(macd_signal_type, features.close)
                    except Exception as e:
                        logger.error(f"MACD signal callback error: {e}")

                self._log_activity(
                    "MACD",
                    f"{macd_signal_type} erkannt @ {features.close:.2f} | "
                    f"Exit: {'DEAKTIVIERT' if self.config.bot.disable_macd_exit else 'AKTIV'}"
                )

                # Only trigger exit if MACD exit is enabled
                if not self.config.bot.disable_macd_exit:
                    return macd_signal_type

        return None
