"""
Bot State Handlers Manage - MANAGE State Processing (Position Management).

Refactored from bot_state_handlers.py.

Contains:
- process_manage: Position management and stop/exit checks
- Bar price extraction and position updates
- Stop hit detection
- Trailing stop updates
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .models import BotAction, FeatureVector, TradeSide
from .state_machine import BotTrigger

if TYPE_CHECKING:
    from .bot_state_handlers import BotStateHandlersMixin
    from .models import BotDecision

logger = logging.getLogger(__name__)


class BotStateHandlersManage:
    """Helper for MANAGE state processing."""

    def __init__(self, parent: BotStateHandlersMixin):
        self.parent = parent

    async def process_manage(
        self, features: FeatureVector, bar: dict[str, Any]
    ) -> BotDecision | None:
        """Process MANAGE state - manage open position.

        Args:
            features: Current feature vector
            bar: Current bar data

        Returns:
            BotDecision or None
        """
        if not self.parent._position:
            logger.error("MANAGE state but no position")
            self.parent._state_machine.error("No position in MANAGE state")
            return None

        close_price, low_price, high_price = self._extract_bar_prices(bar, features)
        self._update_position_price(close_price)

        # Check stop hit using the EXTREME price of the candle (LOW for LONG, HIGH for SHORT)
        # This is critical: a candle's low might breach the stop even if close doesn't
        if self._check_stop_hit(close_price, low_price, high_price):
            return await self.parent._exit.handle_stop_hit(features)

        # Check exit signals
        exit_signal = self.parent._exit.check_exit_signals(features)
        if exit_signal:
            return await self.parent._exit.handle_exit_signal(features, exit_signal)

        # Update trailing stop
        decision = self._maybe_update_trailing_stop(features)
        if decision:
            return decision

        # Hold position
        return self.parent._create_decision(
            BotAction.HOLD, self.parent._position.side, features, ["POSITION_HELD"]
        )

    def _extract_bar_prices(
        self, bar: dict[str, Any], features: FeatureVector
    ) -> tuple[float, float, float]:
        """Extract close, low, high prices from bar."""
        close_price = bar.get("close", features.close)
        low_price = bar.get("low", close_price)
        high_price = bar.get("high", close_price)
        return close_price, low_price, high_price

    def _update_position_price(self, close_price: float) -> None:
        """Update position with current price."""
        self.parent._position.update_price(close_price)
        self.parent._position.bars_held += 1

    def _check_stop_hit(
        self, close_price: float, low_price: float, high_price: float
    ) -> bool:
        """Check if stop loss was hit using candle extremes."""
        stop_price = self.parent._position.trailing.current_stop_price
        initial_stop = self.parent._position.trailing.initial_stop_price

        side_str = self.parent._position.side.value.upper()
        self.parent._log_activity(
            "STOP_CHECK",
            f"Side={side_str} | Stop={stop_price:.2f} (Initial={initial_stop:.2f}) | "
            f"Candle: H={high_price:.2f} L={low_price:.2f} C={close_price:.2f}",
        )

        if self.parent._position.side == TradeSide.LONG:
            if low_price <= stop_price:
                self.parent._log_activity(
                    "STOP",
                    f"🛑 Stop-Loss getroffen! LOW={low_price:.2f} <= Stop={stop_price:.2f} "
                    f"(Close={close_price:.2f})",
                )
                return True
        else:
            if high_price >= stop_price:
                self.parent._log_activity(
                    "STOP",
                    f"🛑 Stop-Loss getroffen! HIGH={high_price:.2f} >= Stop={stop_price:.2f} "
                    f"(Close={close_price:.2f})",
                )
                return True
        return False

    def _maybe_update_trailing_stop(
        self, features: FeatureVector
    ) -> BotDecision | None:
        """Check and update trailing stop if needed."""
        new_stop = self.parent._calculate_trailing_stop(features, self.parent._position)
        self.parent._log_activity("DEBUG", f"_calculate_trailing_stop returned: {new_stop}")
        if not new_stop:
            return None
        old_stop = self.parent._position.trailing.current_stop_price
        is_long = self.parent._position.side == TradeSide.LONG
        self.parent._log_activity(
            "DEBUG",
            f"Calling update_stop: new={new_stop:.4f}, old={old_stop:.4f}, is_long={is_long}",
        )
        updated = self.parent._position.trailing.update_stop(
            new_stop,
            self.parent._bar_count,
            datetime.utcnow(),
            is_long=is_long,
        )
        self.parent._log_activity("DEBUG", f"update_stop returned: {updated}")

        if updated:
            self.parent._state_machine.trigger(BotTrigger.STOP_UPDATED)
            return self.parent._create_decision(
                BotAction.ADJUST_STOP,
                self.parent._position.side,
                features,
                ["TRAILING_STOP_UPDATED"],
                stop_before=old_stop,
                stop_after=new_stop,
            )
        return None
