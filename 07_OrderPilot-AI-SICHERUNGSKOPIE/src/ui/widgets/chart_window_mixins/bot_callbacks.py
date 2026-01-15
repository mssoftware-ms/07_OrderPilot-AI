from __future__ import annotations

from .bot_callbacks_candle_mixin import BotCallbacksCandleMixin
from .bot_callbacks_lifecycle_mixin import BotCallbacksLifecycleMixin
from .bot_callbacks_log_order_mixin import BotCallbacksLogOrderMixin
from .bot_callbacks_signal_mixin import BotCallbacksSignalMixin


class BotCallbacksMixin(
    BotCallbacksLifecycleMixin,
    BotCallbacksSignalMixin,
    BotCallbacksLogOrderMixin,
    BotCallbacksCandleMixin,
):
    """Mixin providing bot callback handlers."""
