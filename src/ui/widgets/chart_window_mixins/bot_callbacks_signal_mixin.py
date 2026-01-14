from __future__ import annotations

import logging

from .bot_callbacks_signal_handling_mixin import BotCallbacksSignalHandlingMixin
from .bot_callbacks_position_lifecycle_mixin import BotCallbacksPositionLifecycleMixin
from .bot_callbacks_signal_utils_mixin import BotCallbacksSignalUtilsMixin

logger = logging.getLogger(__name__)


class BotCallbacksSignalMixin(
    BotCallbacksSignalHandlingMixin,
    BotCallbacksPositionLifecycleMixin,
    BotCallbacksSignalUtilsMixin,
):
    """Bot Callbacks Signal Mixin - Uses sub-mixin pattern for better modularity.

    Coordinates bot signal callbacks by combining:
    - Signal Handling: Signal callbacks and tracking
    - Position Lifecycle: Enter, exit, adjust callbacks
    - Signal Utils: Formatting and helper functions
    """
    pass
