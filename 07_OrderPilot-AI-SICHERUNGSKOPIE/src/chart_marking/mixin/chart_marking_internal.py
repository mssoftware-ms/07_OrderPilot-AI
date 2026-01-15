"""Chart Marking Mixin - Internal State & JS Communication.

Refactored from chart_marking_mixin.py monolith.

Module 5/6 of chart_marking_mixin.py split.

Contains:
- State management (get/restore/clear)
- JavaScript communication callbacks
- Update methods for chart sync
- Properties for counts
"""

from __future__ import annotations

import json
import logging
from typing import Any

from PyQt6.QtCore import Q_ARG, QMetaObject, QThread, Qt, pyqtSlot

logger = logging.getLogger(__name__)


class ChartMarkingInternal:
    """Helper für ChartMarkingMixin internal state & JS communication."""

    def __init__(self, parent):
        """
        Args:
            parent: ChartMarkingMixin Instanz
        """
        self.parent = parent

    # =========================================================================
    # State Management
    # =========================================================================

    def get_marking_state(self) -> dict[str, Any]:
        """Get complete marking state for persistence."""
        return {
            "entry_markers": self.parent._entry_markers.to_state(),
            "structure_markers": self.parent._structure_markers.to_state(),
            "zones": self.parent._zones.to_state(),
            "stop_loss_lines": self.parent._sl_lines.to_state(),
        }

    def restore_marking_state(self, state: dict[str, Any]) -> None:
        """Restore marking state from persistence."""
        if "entry_markers" in state:
            self.parent._entry_markers.restore_state(state["entry_markers"])
        if "structure_markers" in state:
            self.parent._structure_markers.restore_state(state["structure_markers"])
        if "zones" in state:
            self.parent._zones.restore_state(state["zones"])
        if "stop_loss_lines" in state:
            self.parent._sl_lines.restore_state(state["stop_loss_lines"])

        logger.info("Chart marking state restored")

    def clear_all_markings(self) -> None:
        """Remove all markings from the chart."""
        self.parent._entry_markers.clear()
        self.parent._structure_markers.clear()
        self.parent._zones.clear()
        self.parent._sl_lines.clear()
        logger.info("All chart markings cleared")

    # =========================================================================
    # JavaScript Communication (Private)
    # =========================================================================

    def on_markers_changed(self) -> None:
        """Called when entry or structure markers change."""
        self._update_chart_markers()

    def on_zones_changed(self) -> None:
        """Called when zones change."""
        self._update_chart_zones()

    def on_lines_changed(self) -> None:
        """Called when stop-loss lines change."""
        self._update_chart_lines()

    def _update_chart_markers(self) -> None:
        """Update all markers on the chart."""
        # Combine entry and structure markers
        markers = (
            self.parent._entry_markers.get_chart_markers() +
            self.parent._structure_markers.get_chart_markers()
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
        for zone_data in self.parent._zones.get_chart_zones():
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
        # Issue #46: Fixed parameter order to match JavaScript signature
        # JavaScript: addHorizontalLine(price, color, label, lineStyle, customId)
        for line_data in self.parent._sl_lines.get_chart_lines():
            # Escape label to prevent JavaScript injection
            safe_label = line_data['title'].replace("'", "\\'").replace('"', '\\"')
            js_code = (
                f"window.chartAPI.addHorizontalLine("
                f"{line_data['price']}, "
                f"'{line_data['color']}', "
                f"'{safe_label}', "  # Label is 3rd parameter (was 6th!)
                f"{line_data['lineStyle']}, "  # lineStyle is 4th parameter (was 3rd)
                f"'{line_data['id']}'"  # customId is 5th parameter (use line ID)
                f");"
            )
            self._execute_js(js_code)

    @pyqtSlot(str)
    def _execute_js(self, js_code: str) -> None:
        """Execute JavaScript in the chart web view (thread-safe)."""
        # If another mixin provides robust JS queuing, delegate to it.
        try:
            return super(self.parent.__class__, self.parent)._execute_js(js_code)  # type: ignore[misc]
        except AttributeError:
            pass

        # If chart not ready, queue it if possible
        def _queue_pending():
            if hasattr(self.parent, "pending_js_commands"):
                self.parent.pending_js_commands.append(js_code)
                logger.debug("Queued JS (chart not ready): %s", js_code[:120])
                return True
            return False

        if not hasattr(self.parent, "web_view") or not self.parent.web_view:
            if not _queue_pending():
                logger.warning("Cannot execute JS: web_view not available")
            return

        # Check thread safety
        if QThread.currentThread() != self.parent.thread():
            QMetaObject.invokeMethod(
                self.parent,
                "_execute_js",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, js_code),
            )
            return

        try:
            self.parent.web_view.page().runJavaScript(js_code)
        except Exception as exc:
            logger.error("runJavaScript failed: %s", exc)

    # =========================================================================
    # Properties for Direct Access
    # =========================================================================

    @property
    def entry_marker_count(self) -> int:
        """Number of entry markers."""
        return len(self.parent._entry_markers)

    @property
    def structure_marker_count(self) -> int:
        """Number of structure break markers."""
        return len(self.parent._structure_markers)

    @property
    def zone_count(self) -> int:
        """Number of zones."""
        return len(self.parent._zones)

    @property
    def stop_loss_line_count(self) -> int:
        """Number of stop-loss lines."""
        return len(self.parent._sl_lines)

    @property
    def total_marking_count(self) -> int:
        """Total number of all markings."""
        return (
            self.entry_marker_count +
            self.structure_marker_count +
            self.zone_count +
            self.stop_loss_line_count
        )
