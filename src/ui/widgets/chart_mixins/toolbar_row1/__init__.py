"""Toolbar Row 1 Module - Backward Compatibility Re-exports.

This module provides backward compatibility for the refactored toolbar_mixin_row1.
All existing imports will continue to work unchanged.

Example:
    from src.ui.widgets.chart_mixins.toolbar_mixin_row1 import ToolbarMixinRow1

Structure:
- toolbar_row1_setup_mixin.py: Widget creation and layout (~300 LOC)
- toolbar_row1_events_mixin.py: Event handlers and signals (~250 LOC)
- toolbar_row1_actions_mixin.py: Action methods and operations (~250 LOC)

The composite ToolbarMixinRow1 class is available at the parent level.
"""

from src.ui.widgets.chart_mixins.toolbar_row1.toolbar_row1_actions_mixin import ToolbarRow1ActionsMixin
from src.ui.widgets.chart_mixins.toolbar_row1.toolbar_row1_events_mixin import ToolbarRow1EventsMixin
from src.ui.widgets.chart_mixins.toolbar_row1.toolbar_row1_setup_mixin import ToolbarRow1SetupMixin

__all__ = [
    "ToolbarRow1SetupMixin",
    "ToolbarRow1EventsMixin",
    "ToolbarRow1ActionsMixin",
]
