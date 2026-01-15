"""
Bot State Handlers Exit - Exit Handling (Stop Loss & Exit Signals).

Refactored from bot_state_handlers.py.

Contains:
- handle_stop_hit: Stop-loss hit processing
- handle_exit_signal: Exit signal processing
- check_exit_signals: Exit condition checking (RSI + MACD)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import BotAction, FeatureVector, TradeSide

if TYPE_CHECKING:
    from .bot_state_handlers import BotStateHandlersMixin
    from .models import BotDecision

logger = logging.getLogger(__name__)


class BotStateHandlersExit:
    """Helper for exit handling."""

    def __init__(self, parent: BotStateHandlersMixin):
        self.parent = parent

    async def handle_stop_hit(self, features: FeatureVector) -> BotDecision:
        """Handle stop-loss hit.

        Args:
            features: Current feature vector

        Returns:
            BotDecision
        """
        self.parent._state_machine.on_stop_hit(features.close)

        pnl = self.parent._position.unrealized_pnl if self.parent._position else 0
        self.parent._daily_pnl += pnl

        if pnl < 0:
            self.parent._consecutive_losses += 1
        else:
            self.parent._consecutive_losses = 0

        self.parent._trades_today += 1
        side = self.parent._position.side if self.parent._position else TradeSide.NONE

        # Determine if this was initial stop (SL) or trailing stop (TS)
        # Trailing stop is active if the stop was moved from initial position
        is_trailing_stop = False
        if self.parent._position and self.parent._position.trailing:
            initial_stop = self.parent._position.trailing.initial_stop_price
            current_stop = self.parent._position.trailing.current_stop_price
            # If stop was moved (trailing activated), it's a TS exit
            if abs(current_stop - initial_stop) > 0.0001:
                is_trailing_stop = True

        self.parent._position = None

        reason_codes = (
            ["TRAILING_STOP_HIT", "POSITION_CLOSED"]
            if is_trailing_stop
            else ["STOP_HIT", "POSITION_CLOSED"]
        )
        stop_type = "Trailing Stop" if is_trailing_stop else "Stop Loss"

        return self.parent._create_decision(
            BotAction.EXIT, side, features, reason_codes, notes=f"{stop_type} hit, P&L: {pnl:.2f}"
        )

    async def handle_exit_signal(self, features: FeatureVector, reason: str) -> BotDecision:
        """Handle exit signal.

        Args:
            features: Current feature vector
            reason: Exit reason

        Returns:
            BotDecision
        """
        self.parent._state_machine.on_exit_signal(reason)

        pnl = self.parent._position.unrealized_pnl if self.parent._position else 0
        self.parent._daily_pnl += pnl

        if pnl < 0:
            self.parent._consecutive_losses += 1
        else:
            self.parent._consecutive_losses = 0

        self.parent._trades_today += 1
        side = self.parent._position.side if self.parent._position else TradeSide.NONE
        self.parent._position = None

        return self.parent._create_decision(
            BotAction.EXIT,
            side,
            features,
            [reason.upper(), "POSITION_CLOSED"],
            notes=f"P&L: {pnl:.2f}",
        )

    # ==================== Exit Signals ====================

    def check_exit_signals(self, features: FeatureVector) -> str | None:
        """Check for exit signals.

        Args:
            features: Current features

        Returns:
            Exit reason or None
        """
        if not self.parent._position:
            return None

        rsi_exit = self._check_rsi_exit(features)
        if rsi_exit:
            return rsi_exit

        return self._check_macd_exit(features)

    def _check_rsi_exit(self, features: FeatureVector) -> str | None:
        """Check RSI extreme exit conditions."""
        if features.rsi_14 is None or not self.parent._position:
            return None
        if self.parent._position.side == TradeSide.LONG and features.rsi_14 > 80:
            return "RSI_EXTREME_OVERBOUGHT"
        if self.parent._position.side == TradeSide.SHORT and features.rsi_14 < 20:
            return "RSI_EXTREME_OVERSOLD"
        return None

    def _check_macd_exit(self, features: FeatureVector) -> str | None:
        """Check MACD crossover exit conditions."""
        if (
            features.macd is None
            or features.macd_signal is None
            or not self.parent._position
        ):
            return None

        macd_signal_type = None
        if self.parent._position.side == TradeSide.LONG:
            if (
                features.macd < features.macd_signal
                and features.macd_hist
                and features.macd_hist < 0
            ):
                macd_signal_type = "MACD_BEARISH_CROSS"
        else:
            if (
                features.macd > features.macd_signal
                and features.macd_hist
                and features.macd_hist > 0
            ):
                macd_signal_type = "MACD_BULLISH_CROSS"

        if not macd_signal_type:
            return None

        if self.parent._on_macd_signal:
            try:
                self.parent._on_macd_signal(macd_signal_type, features.close)
            except Exception as e:
                logger.error(f"MACD signal callback error: {e}")

        self.parent._log_activity(
            "MACD",
            f"{macd_signal_type} erkannt @ {features.close:.2f} | "
            f"Exit: {'DEAKTIVIERT' if self.parent.config.bot.disable_macd_exit else 'AKTIV'}",
        )

        if not self.parent.config.bot.disable_macd_exit:
            return macd_signal_type
        return None
