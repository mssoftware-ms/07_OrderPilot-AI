from __future__ import annotations

import logging

from .bot_sltp_progressbar import SLTPProgressBar
from .bot_ui_signals_widgets_mixin import BotUISignalsWidgetsMixin
from .bot_ui_signals_actions_mixin import BotUISignalsActionsMixin
from .bot_ui_signals_chart_mixin import BotUISignalsChartMixin
from .bot_ui_signals_log_mixin import BotUISignalsLogMixin

logger = logging.getLogger(__name__)


class BotUISignalsMixin(
    BotUISignalsWidgetsMixin,
    BotUISignalsActionsMixin,
    BotUISignalsChartMixin,
    BotUISignalsLogMixin,
):
    """Bot UI Signals Tab - Uses sub-mixin pattern for better modularity.

    Coordinates signal display and position management by combining:
    - Widgets: UI creation (signals table, position info, status)
    - Actions: Signal and position actions (clear, sell)
    - Chart: Chart element drawing
    - Log: Bot log management and export

    Also exports SLTPProgressBar for convenience.
    """
    pass


# Re-export for backward compatibility
__all__ = ['BotUISignalsMixin', 'SLTPProgressBar']
