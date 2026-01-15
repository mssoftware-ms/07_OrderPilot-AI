from __future__ import annotations

import logging

from PyQt6.QtCore import QTimer, QUrl

logger = logging.getLogger(__name__)

class EmbeddedTradingViewChartLoadingMixin:
    """EmbeddedTradingViewChartLoadingMixin extracted from EmbeddedTradingViewChart."""
    def _on_page_loaded(self, success: bool):
        """Handle page load completion."""
        if success:
            self.page_loaded = True
            logger.info("Chart page loaded successfully")
            self._start_chart_ready_poll()
        else:
            logger.error("Chart page failed to load")
    def _start_chart_ready_poll(self):
        """Poll inside the WebEngine until window.chartAPI exists."""
        if self.chart_ready_timer:
            self.chart_ready_timer.stop()

        self.chart_ready_timer = QTimer(self)
        self.chart_ready_timer.setInterval(150)
        self.chart_ready_timer.timeout.connect(self._poll_chart_ready)
        self.chart_ready_timer.start()
    def _poll_chart_ready(self):
        if not self.page_loaded:
            return

        self.web_view.page().runJavaScript(
            "typeof window.chartAPI !== 'undefined' && typeof window.chartAPI.setData === 'function';",
            self._on_chart_ready_result
        )
    def _on_chart_ready_result(self, ready: bool):
        if not ready:
            return

        if self.chart_ready_timer:
            self.chart_ready_timer.stop()
            self.chart_ready_timer = None

        self.chart_initialized = True
        logger.info("chartAPI is ready")

        self._flush_pending_js()
        if self.pending_data_load is not None:
            logger.info("Loading pending data after chart initialization")
            self.load_data(self.pending_data_load)
            self.pending_data_load = None

        if hasattr(self, '_pending_indicator_update') and self._pending_indicator_update:
            logger.info("Updating pending indicators after chart initialization")
            self._pending_indicator_update = False
            self._update_indicators()
