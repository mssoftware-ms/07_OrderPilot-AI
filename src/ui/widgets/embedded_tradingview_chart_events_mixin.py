from __future__ import annotations

import logging


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
