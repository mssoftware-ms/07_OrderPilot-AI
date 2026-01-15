"""
Bot State Handlers Dispatcher - Main State Machine Dispatcher.

Refactored from bot_state_handlers.py.

Contains:
- _process_state: Main state dispatcher routing to specific state processors
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import FeatureVector
from .state_machine import BotState, BotTrigger

if TYPE_CHECKING:
    from .bot_state_handlers import BotStateHandlersMixin
    from .models import BotDecision


class BotStateHandlersDispatcher:
    """Helper for main state dispatching."""

    def __init__(self, parent: BotStateHandlersMixin):
        self.parent = parent

    async def process_state(
        self, features: FeatureVector, bar: dict[str, Any]
    ) -> BotDecision | None:
        """Process current state and generate decision.

        Args:
            features: Current feature vector
            bar: Current bar data

        Returns:
            BotDecision or None
        """
        state = self.parent._state_machine.state

        # Log state for debugging
        self.parent._log_activity(
            "STATE",
            f"Processing state: {state.value} | Position: {self.parent._position is not None} | "
            f"Bar: O={bar.get('open', 0):.2f} H={bar.get('high', 0):.2f} L={bar.get('low', 0):.2f} C={bar.get('close', 0):.2f}",
        )

        if state == BotState.FLAT:
            return await self.parent._flat.process_flat(features)

        elif state == BotState.SIGNAL:
            return await self.parent._signal.process_signal(features)

        elif state == BotState.ENTERED:
            # Waiting for fill - check timeout
            self.parent._log_activity(
                "DEBUG", "State ENTERED - waiting for fill, no stop check!"
            )
            return None

        elif state == BotState.MANAGE:
            return await self.parent._manage.process_manage(features, bar)

        elif state == BotState.EXITED:
            # Reset for next trade
            self.parent._state_machine.trigger(BotTrigger.RESET)
            return None

        return None
