from __future__ import annotations

from .bot_ui_control_mixin import BotUIControlMixin
from .bot_ui_ki_logs_mixin import BotUIKILogsMixin
from .bot_ui_signals_mixin import BotUISignalsMixin
from .bot_ui_strategy_mixin import BotUIStrategyMixin


class BotUIPanelsMixin(
    BotUIControlMixin,
    BotUIStrategyMixin,
    BotUISignalsMixin,
    BotUIKILogsMixin,
):
    """Mixin providing bot panel tab creation methods."""
