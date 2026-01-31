"""Compounding component (engine + UI panel).

Refactored to use mixin pattern:
- CompoundingUISetupMixin: UI widget creation
- CompoundingUIEventsMixin: Event handlers & exports
- CompoundingUIPlotsMixin: Chart rendering
- CompoundingPanel: Main widget (composes all mixins)
"""

from .calculator import DayResult, MonthKpis, Params, SolveStatus, simulate, solve_daily_profit_pct_for_target
from .ui import CompoundingPanel
from .compounding_ui_setup import CompoundingUISetupMixin, MplCanvas, FUTURES_FEES_BY_VIP, MODERN_COLORS
from .compounding_ui_events import CompoundingUIEventsMixin
from .compounding_ui_plots import CompoundingUIPlotsMixin

__all__ = [
    # Calculator engine
    "Params",
    "DayResult",
    "MonthKpis",
    "SolveStatus",
    "simulate",
    "solve_daily_profit_pct_for_target",
    # Main UI widget
    "CompoundingPanel",
    # Mixins (for advanced usage)
    "CompoundingUISetupMixin",
    "CompoundingUIEventsMixin",
    "CompoundingUIPlotsMixin",
    # Shared components
    "MplCanvas",
    "FUTURES_FEES_BY_VIP",
    "MODERN_COLORS",
]
