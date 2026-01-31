"""Toolbar Mixin Row 1 - Timeframe, Period, Indicators, Primary Actions.

REFACTORED: This module now uses composition pattern.
Original 827 LOC split into 3 focused mixins:
- toolbar_row1_setup_mixin.py (~300 LOC) - Widget creation, layout
- toolbar_row1_events_mixin.py (~250 LOC) - Event handlers, signals
- toolbar_row1_actions_mixin.py (~250 LOC) - Action methods, toolbar ops

Architecture:
- MRO: Actions → Events → Setup
- 100% backward compatible
- Clean separation of concerns

Reference: bot_ui_signals_mixin.py split (commit c3d2aec)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize

from src.ui.widgets.chart_mixins.toolbar_row1.toolbar_row1_actions_mixin import ToolbarRow1ActionsMixin
from src.ui.widgets.chart_mixins.toolbar_row1.toolbar_row1_events_mixin import ToolbarRow1EventsMixin
from src.ui.widgets.chart_mixins.toolbar_row1.toolbar_row1_setup_mixin import ToolbarRow1SetupMixin

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarMixinRow1(
    ToolbarRow1ActionsMixin,
    ToolbarRow1EventsMixin,
    ToolbarRow1SetupMixin,
):
    """Row 1 toolbar composite mixin (timeframe, period, indicators, primary actions).

    This is a composite class that inherits from:
    - ToolbarRow1ActionsMixin: Action methods (zoom, load, indicators)
    - ToolbarRow1EventsMixin: Event handlers (broker, watchlist, strategy)
    - ToolbarRow1SetupMixin: Widget creation and layout

    MRO Chain: Actions → Events → Setup

    All methods are inherited from the specialized mixins:
    - Setup: build_toolbar_row1, add_broker_mirror_controls, add_watchlist_toggle,
             add_timeframe_selector, add_period_selector, add_indicators_menu,
             _build_indicator_tree, add_primary_actions
    - Events: _on_broker_connect_clicked, _on_broker_connected_event,
              _on_broker_disconnected_event, _update_broker_ui_state,
              _toggle_watchlist, _on_strategy_settings_clicked
    - Actions: on_zoom_all, on_zoom_back, on_load_chart, on_refresh,
               on_indicator_add, on_indicator_remove, on_reset_indicators,
               refresh_active_indicator_menu, prompt_custom_period,
               prompt_generic_params
    """

    # Class constants (from Setup mixin)
    BUTTON_HEIGHT = 32
    ICON_SIZE = QSize(20, 20)

    def __init__(self, parent):
        """Initialize toolbar row 1 mixin.

        Args:
            parent: Parent widget (EmbeddedTradingViewChart)
        """
        self.parent = parent
        logger.debug("ToolbarMixinRow1 initialized (refactored composite)")
