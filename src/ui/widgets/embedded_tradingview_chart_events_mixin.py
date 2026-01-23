from __future__ import annotations

import logging

from PyQt6.QtWidgets import QInputDialog

logger = logging.getLogger(__name__)

class EmbeddedTradingViewChartEventsMixin:
    """EmbeddedTradingViewChartEventsMixin extracted from EmbeddedTradingViewChart."""
    def _on_market_tick_event(self, event):
        """Event bus callback - emit signal for thread-safe handling."""
        # This may be called from background thread, so emit signal
        self._tick_received.emit(event)
    def _on_market_bar_event(self, event):
        """Event bus callback - emit signal for thread-safe handling."""
        # This may be called from background thread, so emit signal
        self._bar_received.emit(event)
    def _handle_tick_main_thread(self, event):
        """Handle tick in main thread (thread-safe)."""
        self._on_market_tick(event)
    def _handle_bar_main_thread(self, event):
        """Handle bar in main thread (thread-safe)."""
        self._on_market_bar(event)
    def _on_bridge_stop_line_moved(self, line_id: str, new_price: float):
        """Handle stop line moved event from JavaScript bridge.

        Re-emits the signal so it can be caught by the chart window.
        """
        logger.info(f"Chart line moved: {line_id} -> {new_price:.4f}")
        self.stop_line_moved.emit(line_id, new_price)

    def _on_bridge_zone_deleted(self, zone_id: str):
        """Handle zone deletion from JavaScript delete tool.

        This is called when the user deletes a zone using the chart's
        delete tool (clicking on a zone with the trash tool selected).
        We need to sync this deletion back to the Python ZoneManager.
        """
        logger.info(f"Zone deleted via JS delete tool: {zone_id}")
        # Remove from Python manager (without triggering JS update since JS already removed it)
        if hasattr(self, "_zones") and zone_id in self._zones:
            # Directly remove from internal dict without callback to avoid re-clearing JS
            del self._zones._zones[zone_id]
            logger.info(f"Zone {zone_id} removed from Python manager")

    def _on_line_draw_requested(self, line_id: str, price: float, color: str, line_type: str):
        """Handle line draw request from JavaScript (Issue #24).

        Shows a label input dialog and creates the line with the label.

        Args:
            line_id: Unique ID for the line
            price: Price level for the line
            color: Line color (hex)
            line_type: Type of line ('green' or 'red')
        """
        logger.info(f"Line draw requested: {line_id} @ {price:.4f} ({line_type})")

        # Show dialog to get label
        line_type_text = "Grüne Linie" if line_type == "green" else "Rote Linie"
        label, ok = QInputDialog.getText(
            self,
            f"{line_type_text} - Beschriftung",
            f"Bezeichnung für Linie bei {price:.4f}:",
            text=""
        )

        if ok:
            # Create line via JavaScript with the label
            label_escaped = label.replace("'", "\\'").replace('"', '\\"')
            js_code = f"window.chartAPI?.addHorizontalLine({price}, '{color}', '{label_escaped}', 'solid', '{line_id}');"
            self._execute_js(js_code)
            logger.info(f"Line created with label: '{label}' @ {price:.4f}")
        else:
            # User cancelled - create line without label (fallback)
            js_code = f"window.chartAPI?.addHorizontalLine({price}, '{color}', '', 'solid', '{line_id}');"
            self._execute_js(js_code)
            logger.info(f"Line created without label @ {price:.4f} (user cancelled dialog)")

    def _on_vline_draw_requested(self, line_id: str, timestamp: float, color: str):
        """Handle vertical line draw request from JavaScript.

        Shows a label input dialog and creates the line with the label.

        Args:
            line_id: Unique ID for the line
            timestamp: Unix timestamp for the line
            color: Line color (hex)
        """
        from datetime import datetime, timezone
        dt_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Vertical line draw requested: {line_id} @ {dt_str}")

        # Show dialog to get label
        label, ok = QInputDialog.getText(
            self,
            "Vertikale Linie - Beschriftung",
            f"Bezeichnung für Linie am {dt_str} (UTC):",
            text=""
        )

        if ok:
            # Create line via JavaScript with the label
            label_escaped = label.replace("'", "\\'").replace('"', '\\"')
            js_code = f"window.chartAPI?.addVerticalLine({timestamp}, '{color}', '{label_escaped}', 'solid', '{line_id}');"
            self._execute_js(js_code)
            logger.info(f"Vertical line created with label: '{label}' @ {dt_str}")
        else:
            # User cancelled - create line without label (fallback)
            js_code = f"window.chartAPI?.addVerticalLine({timestamp}, '{color}', '', 'solid', '{line_id}');"
            self._execute_js(js_code)
            logger.info(f"Vertical line created without label @ {dt_str} (user cancelled dialog)")
