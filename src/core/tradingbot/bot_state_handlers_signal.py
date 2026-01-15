"""
Bot State Handlers Signal - SIGNAL State Processing (Signal Confirmation).

Refactored from bot_state_handlers.py.

Contains:
- process_signal: Signal confirmation and entry order creation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import BotAction, FeatureVector, SignalType, TradeSide
from .state_machine import BotTrigger

if TYPE_CHECKING:
    from .bot_state_handlers import BotStateHandlersMixin
    from .models import BotDecision


class BotStateHandlersSignal:
    """Helper for SIGNAL state processing."""

    def __init__(self, parent: BotStateHandlersMixin):
        self.parent = parent

    async def process_signal(self, features: FeatureVector) -> BotDecision | None:
        """Process SIGNAL state - confirm or expire signal.

        Args:
            features: Current feature vector

        Returns:
            BotDecision or None
        """
        if not self.parent._current_signal:
            self.parent._state_machine.trigger(BotTrigger.SIGNAL_EXPIRED)
            return None

        # Check signal still valid
        side = self.parent._current_signal.side
        new_score = self.parent._calculate_entry_score(features, side)

        if new_score < self.parent._get_entry_threshold() * 0.9:  # Allow some slack
            # Signal expired
            self.parent._current_signal = None
            self.parent._state_machine.trigger(BotTrigger.SIGNAL_EXPIRED)
            return self.parent._create_decision(
                BotAction.NO_TRADE, TradeSide.NONE, features, ["SIGNAL_EXPIRED"]
            )

        # Confirm signal and enter
        self.parent._current_signal.signal_type = SignalType.CONFIRMED
        self.parent._current_signal.score = new_score
        self.parent._state_machine.on_signal(self.parent._current_signal, confirmed=True)

        # Notify UI that signal is now confirmed
        if self.parent._on_signal:
            self.parent._on_signal(self.parent._current_signal)

        # Get initial stop price from signal BEFORE on_order callback
        # (on_order may call simulate_fill which clears _current_signal)
        initial_stop = self.parent._current_signal.stop_loss_price
        order_id = None

        self.parent._log_activity("DEBUG", f"ENTRY: initial_stop={initial_stop}")

        # Create entry order intent
        order = self.parent._create_entry_order(features, self.parent._current_signal)
        order_id = order.id

        if self.parent._on_order:
            self.parent._on_order(order)

        self.parent._log_activity(
            "DEBUG", f"Creating ENTER decision with stop_after={initial_stop}"
        )
        return self.parent._create_decision(
            BotAction.ENTER,
            side,
            features,
            ["SIGNAL_CONFIRMED", "ENTRY_ORDER_SENT"],
            stop_after=initial_stop,  # Initial stop price for chart display
            notes=f"Entry order: {order_id}, Initial SL: {initial_stop:.4f}",
        )
