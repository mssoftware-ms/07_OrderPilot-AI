"""Chart Marking Mixin for EmbeddedTradingViewChart (REFACTORED).

Provides a unified API for all chart marking functionality:
- Entry arrows (Long/Short)
- Support/Resistance zones
- Structure break markers (BoS/CHoCH)
- Stop-loss lines with risk display

Module 6/6 of chart_marking_mixin.py split - Main Orchestrator
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from ..lines import StopLossLineManager
from ..markers import EntryMarkerManager, StructureMarkerManager
from ..models import Direction, StructureBreakType, ZoneType
from ..zones import ZoneManager
from .chart_marking_entry_methods import ChartMarkingEntryMethods
from .chart_marking_internal import ChartMarkingInternal
from .chart_marking_line_methods import ChartMarkingLineMethods
from .chart_marking_structure_methods import ChartMarkingStructureMethods
from .chart_marking_zone_methods import ChartMarkingZoneMethods

if TYPE_CHECKING:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

logger = logging.getLogger(__name__)


class ChartMarkingMixin:
    """Mixin that adds chart marking capabilities to EmbeddedTradingViewChart (REFACTORED).

    This mixin provides methods for adding, updating, and removing various
    chart markings. It manages the internal state and communicates with
    the JavaScript chart via QWebChannel.

    Usage:
        class EmbeddedTradingViewChart(ChartMarkingMixin, QWidget):
            def __init__(self):
                super().__init__()
                self._init_chart_marking()

            # Now you can use:
            # self.add_long_entry(timestamp, price, "Long Entry")
            # self.add_support_zone(start, end, top, bottom, "Support")
    """

    # These attributes should be defined by the parent class
    web_view: "QWebEngineView"

    def _init_chart_marking(self) -> None:
        """Initialize chart marking components. Call from __init__."""
        self._entry_markers = EntryMarkerManager(on_update=self._on_markers_changed)
        self._structure_markers = StructureMarkerManager(on_update=self._on_markers_changed)
        self._zones = ZoneManager(on_update=self._on_zones_changed)
        self._sl_lines = StopLossLineManager(on_update=self._on_lines_changed)

        # Composition pattern - Helper-Klassen
        self._entry_methods = ChartMarkingEntryMethods(parent=self)
        self._structure_methods = ChartMarkingStructureMethods(parent=self)
        self._zone_methods = ChartMarkingZoneMethods(parent=self)
        self._line_methods = ChartMarkingLineMethods(parent=self)
        self._internal = ChartMarkingInternal(parent=self)

        logger.debug("Chart marking system initialized")

    # =========================================================================
    # Entry Markers (delegiert an ChartMarkingEntryMethods)
    # =========================================================================

    def add_entry_marker(self, marker_id: Optional[str], timestamp: int | datetime, price: float, direction: Direction | str, text: str = "", tooltip: str = "", score: Optional[float] = None) -> str:
        """Add an entry marker (arrow)."""
        return self._entry_methods.add_entry_marker(marker_id, timestamp, price, direction, text, tooltip, score)

    def add_long_entry(self, timestamp: int | datetime, price: float, text: str = "Long Entry", marker_id: Optional[str] = None, score: Optional[float] = None) -> str:
        """Add a long entry marker."""
        return self._entry_methods.add_long_entry(timestamp, price, text, marker_id, score)

    def add_short_entry(self, timestamp: int | datetime, price: float, text: str = "Short Entry", marker_id: Optional[str] = None, score: Optional[float] = None) -> str:
        """Add a short entry marker."""
        return self._entry_methods.add_short_entry(timestamp, price, text, marker_id, score)

    def remove_entry_marker(self, marker_id: str) -> bool:
        """Remove an entry marker."""
        return self._entry_methods.remove_entry_marker(marker_id)

    def clear_entry_markers(self) -> None:
        """Remove all entry markers."""
        self._entry_methods.clear_entry_markers()

    # =========================================================================
    # Structure Break Markers (delegiert an ChartMarkingStructureMethods)
    # =========================================================================

    def add_structure_break(self, marker_id: Optional[str], timestamp: int | datetime, price: float, break_type: StructureBreakType | str, direction: Direction | str, text: str = "") -> str:
        """Add a structure break marker."""
        return self._structure_methods.add_structure_break(marker_id, timestamp, price, break_type, direction, text)

    def add_bos(self, timestamp: int | datetime, price: float, is_bullish: bool = True, marker_id: Optional[str] = None, text: str = "BoS") -> str:
        """Add a Break of Structure marker."""
        return self._structure_methods.add_bos(timestamp, price, is_bullish, marker_id, text)

    def add_choch(self, timestamp: int | datetime, price: float, is_bullish: bool = True, marker_id: Optional[str] = None, text: str = "CHoCH") -> str:
        """Add a Change of Character marker."""
        return self._structure_methods.add_choch(timestamp, price, is_bullish, marker_id, text)

    def add_msb(self, timestamp: int | datetime, price: float, is_bullish: bool = True, marker_id: Optional[str] = None, text: str = "MSB") -> str:
        """Add a Market Structure Break marker."""
        return self._structure_methods.add_msb(timestamp, price, is_bullish, marker_id, text)

    def remove_structure_break(self, marker_id: str) -> bool:
        """Remove a structure break marker."""
        return self._structure_methods.remove_structure_break(marker_id)

    def clear_structure_breaks(self) -> None:
        """Remove all structure break markers."""
        self._structure_methods.clear_structure_breaks()

    def clear_structure_breaks_by_type(self, break_type: StructureBreakType | str) -> int:
        """Remove all structure breaks of a specific type."""
        return self._structure_methods.clear_structure_breaks_by_type(break_type)

    # =========================================================================
    # Zones (delegiert an ChartMarkingZoneMethods)
    # =========================================================================

    def add_zone(self, zone_id: Optional[str], zone_type: ZoneType | str, start_time: int | datetime, end_time: int | datetime, top_price: float, bottom_price: float, opacity: float = 0.3, label: str = "", color: Optional[str] = None) -> str:
        """Add a support/resistance zone."""
        return self._zone_methods.add_zone(zone_id, zone_type, start_time, end_time, top_price, bottom_price, opacity, label, color)

    def add_support_zone(self, start_time: int | datetime, end_time: int | datetime, top_price: float, bottom_price: float, label: str = "Support", zone_id: Optional[str] = None, opacity: float = 0.3) -> str:
        """Add a support zone."""
        return self._zone_methods.add_support_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)

    def add_resistance_zone(self, start_time: int | datetime, end_time: int | datetime, top_price: float, bottom_price: float, label: str = "Resistance", zone_id: Optional[str] = None, opacity: float = 0.3) -> str:
        """Add a resistance zone."""
        return self._zone_methods.add_resistance_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)

    def add_demand_zone(self, start_time: int | datetime, end_time: int | datetime, top_price: float, bottom_price: float, label: str = "Demand", zone_id: Optional[str] = None, opacity: float = 0.3) -> str:
        """Add a demand zone."""
        return self._zone_methods.add_demand_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)

    def add_supply_zone(self, start_time: int | datetime, end_time: int | datetime, top_price: float, bottom_price: float, label: str = "Supply", zone_id: Optional[str] = None, opacity: float = 0.3) -> str:
        """Add a supply zone."""
        return self._zone_methods.add_supply_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)

    def update_zone(self, zone_id: str, start_time: Optional[int | datetime] = None, end_time: Optional[int | datetime] = None, top_price: Optional[float] = None, bottom_price: Optional[float] = None) -> bool:
        """Update a zone's dimensions."""
        return self._zone_methods.update_zone(zone_id, start_time, end_time, top_price, bottom_price)

    def extend_zone(self, zone_id: str, new_end_time: int | datetime) -> bool:
        """Extend a zone's end time."""
        return self._zone_methods.extend_zone(zone_id, new_end_time)

    def remove_zone(self, zone_id: str) -> bool:
        """Remove a zone."""
        return self._zone_methods.remove_zone(zone_id)

    def clear_zones(self) -> None:
        """Remove all zones."""
        self._zone_methods.clear_zones()

    def clear_zones_by_type(self, zone_type: ZoneType | str) -> int:
        """Remove all zones of a specific type."""
        return self._zone_methods.clear_zones_by_type(zone_type)

    # =========================================================================
    # Stop-Loss Lines (delegiert an ChartMarkingLineMethods)
    # =========================================================================

    def add_line(self, line_id: str, price: float, color: str, label: str = "", line_style: str = "solid", show_risk: bool = False) -> str:
        """Add a generic horizontal line."""
        return self._line_methods.add_line(line_id, price, color, label, line_style, show_risk)

    def add_stop_loss_line(self, line_id: str, price: float, entry_price: Optional[float] = None, is_long: bool = True, label: str = "SL", show_risk: bool = True) -> str:
        """Add a stop-loss line."""
        return self._line_methods.add_stop_loss_line(line_id, price, entry_price, is_long, label, show_risk)

    def add_take_profit_line(self, line_id: str, price: float, entry_price: Optional[float] = None, is_long: bool = True, label: str = "TP") -> str:
        """Add a take-profit line."""
        return self._line_methods.add_take_profit_line(line_id, price, entry_price, is_long, label)

    def add_entry_line(self, line_id: str, price: float, is_long: bool = True, label: str = "Entry") -> str:
        """Add an entry price line."""
        return self._line_methods.add_entry_line(line_id, price, is_long, label)

    def add_trailing_stop_line(self, line_id: str, price: float, entry_price: Optional[float] = None, is_long: bool = True, label: str = "TSL") -> str:
        """Add a trailing stop line."""
        return self._line_methods.add_trailing_stop_line(line_id, price, entry_price, is_long, label)

    def update_stop_loss_line(self, line_id: str, price: Optional[float] = None, entry_price: Optional[float] = None) -> bool:
        """Update a stop-loss line's price levels."""
        return self._line_methods.update_stop_loss_line(line_id, price, entry_price)

    def update_trailing_stop(self, line_id: str, new_price: float) -> bool:
        """Update a trailing stop price."""
        return self._line_methods.update_trailing_stop(line_id, new_price)

    def remove_stop_loss_line(self, line_id: str) -> bool:
        """Remove a stop-loss line."""
        return self._line_methods.remove_stop_loss_line(line_id)

    def clear_stop_loss_lines(self) -> None:
        """Remove all stop-loss lines."""
        self._line_methods.clear_stop_loss_lines()

    # =========================================================================
    # State Management (delegiert an ChartMarkingInternal)
    # =========================================================================

    def get_marking_state(self) -> dict[str, Any]:
        """Get complete marking state for persistence."""
        return self._internal.get_marking_state()

    def restore_marking_state(self, state: dict[str, Any]) -> None:
        """Restore marking state from persistence."""
        self._internal.restore_marking_state(state)

    def clear_all_markings(self) -> None:
        """Remove all markings from the chart."""
        self._internal.clear_all_markings()

    # =========================================================================
    # JavaScript Communication (Private)
    # =========================================================================

    def _on_markers_changed(self) -> None:
        """Called when entry or structure markers change."""
        self._internal.on_markers_changed()

    def _on_zones_changed(self) -> None:
        """Called when zones change."""
        self._internal.on_zones_changed()

    def _on_lines_changed(self) -> None:
        """Called when stop-loss lines change."""
        self._internal.on_lines_changed()

    # =========================================================================
    # Properties for Direct Access (delegiert an ChartMarkingInternal)
    # =========================================================================

    @property
    def entry_marker_count(self) -> int:
        """Number of entry markers."""
        return self._internal.entry_marker_count

    @property
    def structure_marker_count(self) -> int:
        """Number of structure break markers."""
        return self._internal.structure_marker_count

    @property
    def zone_count(self) -> int:
        """Number of zones."""
        return self._internal.zone_count

    @property
    def stop_loss_line_count(self) -> int:
        """Number of stop-loss lines."""
        return self._internal.stop_loss_line_count

    @property
    def total_marking_count(self) -> int:
        """Total number of all markings."""
        return self._internal.total_marking_count


__all__ = ["ChartMarkingMixin"]
