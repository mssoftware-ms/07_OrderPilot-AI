"""Chart Marking Mixin for EmbeddedTradingViewChart.

Provides a unified API for all chart marking functionality:
- Entry arrows (Long/Short)
- Support/Resistance zones
- Structure break markers (BoS/CHoCH)
- Stop-loss lines with risk display
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from PyQt6.QtCore import QMetaObject, Qt, QThread, Q_ARG, pyqtSlot

from ..lines import StopLossLineManager
from ..markers import EntryMarkerManager, StructureMarkerManager
from ..models import Direction, StructureBreakType, ZoneType
from ..zones import ZoneManager

if TYPE_CHECKING:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

logger = logging.getLogger(__name__)


class ChartMarkingMixin:
    """Mixin that adds chart marking capabilities to EmbeddedTradingViewChart.

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
        logger.debug("Chart marking system initialized")

    # =========================================================================
    # Entry Markers
    # =========================================================================

    def add_entry_marker(
        self,
        marker_id: Optional[str],
        timestamp: int | datetime,
        price: float,
        direction: Direction | str,
        text: str = "",
        tooltip: str = "",
        score: Optional[float] = None,
    ) -> str:
        """Add an entry marker (arrow).

        Args:
            marker_id: Unique identifier (auto-generated if None)
            timestamp: Bar timestamp
            price: Entry price level
            direction: "long"/"short" or Direction enum
            text: Display text
            tooltip: Hover tooltip
            score: Optional signal score

        Returns:
            Marker ID
        """
        return self._entry_markers.add(
            marker_id, timestamp, price, direction, text, tooltip, score
        )

    def add_long_entry(
        self,
        timestamp: int | datetime,
        price: float,
        text: str = "Long Entry",
        marker_id: Optional[str] = None,
        score: Optional[float] = None,
    ) -> str:
        """Add a long entry marker (convenience method)."""
        return self._entry_markers.add_long(timestamp, price, text, marker_id, score)

    def add_short_entry(
        self,
        timestamp: int | datetime,
        price: float,
        text: str = "Short Entry",
        marker_id: Optional[str] = None,
        score: Optional[float] = None,
    ) -> str:
        """Add a short entry marker (convenience method)."""
        return self._entry_markers.add_short(timestamp, price, text, marker_id, score)

    def remove_entry_marker(self, marker_id: str) -> bool:
        """Remove an entry marker."""
        return self._entry_markers.remove(marker_id)

    def clear_entry_markers(self) -> None:
        """Remove all entry markers."""
        self._entry_markers.clear()

    # =========================================================================
    # Structure Break Markers (BoS/CHoCH)
    # =========================================================================

    def add_structure_break(
        self,
        marker_id: Optional[str],
        timestamp: int | datetime,
        price: float,
        break_type: StructureBreakType | str,
        direction: Direction | str,
        text: str = "",
    ) -> str:
        """Add a structure break marker.

        Args:
            marker_id: Unique identifier (auto-generated if None)
            timestamp: Break timestamp
            price: Break price level
            break_type: "BoS", "CHoCH", or "MSB"
            direction: "bullish"/"bearish"
            text: Display text

        Returns:
            Marker ID
        """
        return self._structure_markers.add(
            marker_id, timestamp, price, break_type, direction, text
        )

    def add_bos(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "BoS",
    ) -> str:
        """Add a Break of Structure marker (convenience method)."""
        return self._structure_markers.add_bos(timestamp, price, is_bullish, marker_id, text)

    def add_choch(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "CHoCH",
    ) -> str:
        """Add a Change of Character marker (convenience method)."""
        return self._structure_markers.add_choch(timestamp, price, is_bullish, marker_id, text)

    def add_msb(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "MSB",
    ) -> str:
        """Add a Market Structure Break marker (convenience method)."""
        return self._structure_markers.add_msb(timestamp, price, is_bullish, marker_id, text)

    def remove_structure_break(self, marker_id: str) -> bool:
        """Remove a structure break marker."""
        return self._structure_markers.remove(marker_id)

    def clear_structure_breaks(self) -> None:
        """Remove all structure break markers."""
        self._structure_markers.clear()

    def clear_structure_breaks_by_type(self, break_type: StructureBreakType | str) -> int:
        """Remove all structure breaks of a specific type."""
        return self._structure_markers.clear_by_type(break_type)

    # =========================================================================
    # Zones (Support/Resistance)
    # =========================================================================

    def add_zone(
        self,
        zone_id: Optional[str],
        zone_type: ZoneType | str,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        opacity: float = 0.3,
        label: str = "",
        color: Optional[str] = None,
    ) -> str:
        """Add a support/resistance zone.

        Args:
            zone_id: Unique identifier (auto-generated if None)
            zone_type: Type (support/resistance/demand/supply)
            start_time: Zone start timestamp
            end_time: Zone end timestamp
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            opacity: Fill opacity (0-1)
            label: Zone label text
            color: Optional custom fill color

        Returns:
            Zone ID
        """
        logger.debug(f"ChartMarkingMixin.add_zone called: {label} ({zone_type}) [{bottom_price}-{top_price}]")
        return self._zones.add(
            zone_id, zone_type, start_time, end_time,
            top_price, bottom_price, opacity, label, color
        )

    def add_support_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Support",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a support zone (convenience method)."""
        return self._zones.add_support(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def add_resistance_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Resistance",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a resistance zone (convenience method)."""
        return self._zones.add_resistance(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def add_demand_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Demand",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a demand zone (convenience method)."""
        return self._zones.add_demand(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def add_supply_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Supply",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a supply zone (convenience method)."""
        return self._zones.add_supply(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def update_zone(
        self,
        zone_id: str,
        start_time: Optional[int | datetime] = None,
        end_time: Optional[int | datetime] = None,
        top_price: Optional[float] = None,
        bottom_price: Optional[float] = None,
    ) -> bool:
        """Update a zone's dimensions."""
        return self._zones.update(zone_id, start_time, end_time, top_price, bottom_price)

    def extend_zone(self, zone_id: str, new_end_time: int | datetime) -> bool:
        """Extend a zone's end time."""
        return self._zones.extend_zone(zone_id, new_end_time)

    def remove_zone(self, zone_id: str) -> bool:
        """Remove a zone."""
        return self._zones.remove(zone_id)

    def clear_zones(self) -> None:
        """Remove all zones."""
        self._zones.clear()

    def clear_zones_by_type(self, zone_type: ZoneType | str) -> int:
        """Remove all zones of a specific type."""
        return self._zones.clear_by_type(zone_type)

    # =========================================================================
    # Stop-Loss Lines
    # =========================================================================

    def add_line(
        self,
        line_id: str,
        price: float,
        color: str,
        label: str = "",
        line_style: str = "solid",
        show_risk: bool = False,
    ) -> str:
        """Add a generic horizontal line.

        Args:
            line_id: Unique identifier
            price: Price level
            color: Line color
            label: Line label
            line_style: "solid", "dashed", or "dotted"
            show_risk: Whether to show risk (requires entry price, defaults to False)

        Returns:
            Line ID
        """
        from ..models import Direction
        return self._sl_lines.add(
            line_id, price, None, Direction.LONG,
            color, line_style, label, show_risk
        )

    def add_stop_loss_line(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "SL",
        show_risk: bool = True,
    ) -> str:
        """Add a stop-loss line with optional risk display.

        Args:
            line_id: Unique identifier
            price: Stop-loss price level
            entry_price: Entry price for risk calculation
            is_long: True for long position
            label: Line label
            show_risk: Whether to show risk percentage

        Returns:
            Line ID
        """
        from ..constants import Colors
        from ..models import LineStyle

        direction = Direction.LONG if is_long else Direction.SHORT
        return self._sl_lines.add(
            line_id, price, entry_price, direction,
            Colors.STOP_LOSS, LineStyle.DASHED, label, show_risk
        )

    def add_take_profit_line(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "TP",
    ) -> str:
        """Add a take-profit line (convenience method)."""
        return self._sl_lines.add_take_profit(line_id, price, entry_price, is_long, label)

    def add_entry_line(
        self,
        line_id: str,
        price: float,
        is_long: bool = True,
        label: str = "Entry",
    ) -> str:
        """Add an entry price line (convenience method)."""
        return self._sl_lines.add_entry_line(line_id, price, is_long, label)

    def add_trailing_stop_line(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "TSL",
    ) -> str:
        """Add a trailing stop line (convenience method)."""
        return self._sl_lines.add_trailing_stop(line_id, price, entry_price, is_long, label)

    def update_stop_loss_line(
        self,
        line_id: str,
        price: Optional[float] = None,
        entry_price: Optional[float] = None,
    ) -> bool:
        """Update a stop-loss line's price levels."""
        return self._sl_lines.update(line_id, price, entry_price)

    def update_trailing_stop(self, line_id: str, new_price: float) -> bool:
        """Update a trailing stop price."""
        return self._sl_lines.update_trailing_stop(line_id, new_price)

    def remove_stop_loss_line(self, line_id: str) -> bool:
        """Remove a stop-loss line."""
        return self._sl_lines.remove(line_id)

    def clear_stop_loss_lines(self) -> None:
        """Remove all stop-loss lines."""
        self._sl_lines.clear()

    # =========================================================================
    # State Management
    # =========================================================================

    def get_marking_state(self) -> dict[str, Any]:
        """Get complete marking state for persistence.

        Returns:
            Dictionary with all marker/zone/line states
        """
        return {
            "entry_markers": self._entry_markers.to_state(),
            "structure_markers": self._structure_markers.to_state(),
            "zones": self._zones.to_state(),
            "stop_loss_lines": self._sl_lines.to_state(),
        }

    def restore_marking_state(self, state: dict[str, Any]) -> None:
        """Restore marking state from persistence.

        Args:
            state: State dictionary from get_marking_state()
        """
        if "entry_markers" in state:
            self._entry_markers.restore_state(state["entry_markers"])
        if "structure_markers" in state:
            self._structure_markers.restore_state(state["structure_markers"])
        if "zones" in state:
            self._zones.restore_state(state["zones"])
        if "stop_loss_lines" in state:
            self._sl_lines.restore_state(state["stop_loss_lines"])

        logger.info("Chart marking state restored")

    def clear_all_markings(self) -> None:
        """Remove all markings from the chart."""
        self._entry_markers.clear()
        self._structure_markers.clear()
        self._zones.clear()
        self._sl_lines.clear()
        logger.info("All chart markings cleared")

    # =========================================================================
    # JavaScript Communication (Private)
    # =========================================================================

    def _on_markers_changed(self) -> None:
        """Called when entry or structure markers change."""
        self._update_chart_markers()

    def _on_zones_changed(self) -> None:
        """Called when zones change."""
        self._update_chart_zones()

    def _on_lines_changed(self) -> None:
        """Called when stop-loss lines change."""
        self._update_chart_lines()

    def _update_chart_markers(self) -> None:
        """Update all markers on the chart."""
        # Combine entry and structure markers
        markers = (
            self._entry_markers.get_chart_markers() +
            self._structure_markers.get_chart_markers()
        )
        markers.sort(key=lambda m: m["time"])

        js_code = f"window.chartAPI.addTradeMarkers({json.dumps(markers)});"
        self._execute_js(js_code)

    def _update_chart_zones(self) -> None:
        """Update all zones on the chart."""
        # First clear existing zones
        logger.info("ChartMarkingMixin: clearing zones on chart")
        self._execute_js("window.chartAPI.clearZones();")

        # Add each zone
        for zone_data in self._zones.get_chart_zones():
            logger.info(
                "ChartMarkingMixin: addZone id=%s range=%s-%s prices=%.2f-%.2f",
                zone_data["id"],
                zone_data["startTime"],
                zone_data["endTime"],
                zone_data["bottomPrice"],
                zone_data["topPrice"],
            )
            js_code = (
                f"window.chartAPI.addZone("
                f"'{zone_data['id']}', "
                f"{zone_data['startTime']}, "
                f"{zone_data['endTime']}, "
                f"{zone_data['topPrice']}, "
                f"{zone_data['bottomPrice']}, "
                f"'{zone_data['fillColor']}', "
                f"{zone_data.get('opacity', 0.3)}, "
                f"'{zone_data['label']}'"
                f");"
            )
            self._execute_js(js_code)

    def _update_chart_lines(self) -> None:
        """Update all horizontal lines on the chart."""
        # Remove all horizontal lines using the dedicated clearLines API
        self._execute_js("window.chartAPI?.clearLines();")
        logger.debug("Cleared all horizontal lines from chart")

        # Add each line
        for line_data in self._sl_lines.get_chart_lines():
            js_code = (
                f"window.chartAPI.addHorizontalLine("
                f"{line_data['price']}, "
                f"'{line_data['color']}', "
                f"{line_data['lineStyle']}, "
                f"{line_data['lineWidth']}, "
                f"{str(line_data['axisLabelVisible']).lower()}, "
                f"'{line_data['title']}'"
                f");"
            )
            self._execute_js(js_code)

    @pyqtSlot(str)
    def _execute_js(self, js_code: str) -> None:
        """Execute JavaScript in the chart web view (thread-safe).

        Args:
            js_code: JavaScript code to execute
        """
        # If another mixin provides robust JS queuing, delegate to it.
        try:
            return super()._execute_js(js_code)  # type: ignore[misc]
        except AttributeError:
            pass

        # If chart not ready, queue it if possible
        def _queue_pending():
            if hasattr(self, "pending_js_commands"):
                self.pending_js_commands.append(js_code)
                logger.debug("Queued JS (chart not ready): %s", js_code[:120])
                return True
            return False

        if not hasattr(self, "web_view") or not self.web_view:
            if not _queue_pending():
                logger.warning("Cannot execute JS: web_view not available")
            return

        # Check thread safety
        if QThread.currentThread() != self.thread():
            QMetaObject.invokeMethod(
                self,
                "_execute_js",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, js_code),
            )
            return

        try:
            self.web_view.page().runJavaScript(js_code)
        except Exception as exc:
            logger.error("runJavaScript failed: %s", exc)

    # =========================================================================
    # Properties for Direct Access
    # =========================================================================

    @property
    def entry_marker_count(self) -> int:
        """Number of entry markers."""
        return len(self._entry_markers)

    @property
    def structure_marker_count(self) -> int:
        """Number of structure break markers."""
        return len(self._structure_markers)

    @property
    def zone_count(self) -> int:
        """Number of zones."""
        return len(self._zones)

    @property
    def stop_loss_line_count(self) -> int:
        """Number of stop-loss lines."""
        return len(self._sl_lines)

    @property
    def total_marking_count(self) -> int:
        """Total number of all markings."""
        return (
            self.entry_marker_count +
            self.structure_marker_count +
            self.zone_count +
            self.stop_loss_line_count
        )
