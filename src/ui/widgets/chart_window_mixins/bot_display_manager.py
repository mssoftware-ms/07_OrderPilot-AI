from __future__ import annotations

from .bot_display_logging_mixin import BotDisplayLoggingMixin
from .bot_display_metrics_mixin import BotDisplayMetricsMixin
from .bot_display_position_mixin import BotDisplayPositionMixin
from .bot_display_selection_mixin import BotDisplaySelectionMixin
from .bot_display_signals_mixin import BotDisplaySignalsMixin


class BotDisplayManagerMixin(
    BotDisplaySelectionMixin,
    BotDisplayPositionMixin,
    BotDisplaySignalsMixin,
    BotDisplayLoggingMixin,
    BotDisplayMetricsMixin,
):
    """Mixin providing bot display update methods."""
