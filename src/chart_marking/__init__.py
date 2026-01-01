"""Chart Marking System for OrderPilot-AI.

Provides unified chart marking functionality:
- Entry arrows (Long/Short)
- Support/Resistance zones
- Structure break markers (BoS/CHoCH)
- Stop-loss lines with risk display
- Multi-chart/multi-monitor support

Usage:
    # The ChartMarkingMixin is added to EmbeddedTradingViewChart
    # Access via chart widget:
    chart_widget.add_long_entry(timestamp, price, "Long Entry")
    chart_widget.add_support_zone(start, end, top, bottom, "Support")
    chart_widget.add_bos(timestamp, price, is_bullish=True)
    chart_widget.add_stop_loss_line("sl_1", price, entry_price)
"""

from .constants import Colors, LineStyles, MarkerSizes
from .lines import StopLossLineManager
from .markers import EntryMarkerManager, StructureMarkerManager
from .mixin import ChartMarkingMixin
from .models import (
    ChartConfig,
    Direction,
    EntryMarker,
    LineStyle,
    MarkerPosition,
    MarkerShape,
    MultiChartLayout,
    StopLossLine,
    StructureBreakMarker,
    StructureBreakType,
    Zone,
    ZoneType,
)
from .zones import ZoneManager
from .zones.zone_primitive_js import get_zone_javascript

# Multi-chart support
from .multi_chart import (
    CrosshairSyncManager,
    LayoutManager,
    MultiMonitorChartManager,
)

__all__ = [
    # Mixin
    "ChartMarkingMixin",
    # Enums
    "MarkerShape",
    "MarkerPosition",
    "Direction",
    "ZoneType",
    "StructureBreakType",
    "LineStyle",
    # Data classes
    "EntryMarker",
    "Zone",
    "StructureBreakMarker",
    "StopLossLine",
    "ChartConfig",
    "MultiChartLayout",
    # Managers
    "EntryMarkerManager",
    "StructureMarkerManager",
    "ZoneManager",
    "StopLossLineManager",
    # Constants
    "Colors",
    "LineStyles",
    "MarkerSizes",
    # JavaScript
    "get_zone_javascript",
    # Multi-chart
    "LayoutManager",
    "CrosshairSyncManager",
    "MultiMonitorChartManager",
]

__version__ = "1.0.0"
