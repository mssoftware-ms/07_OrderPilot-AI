from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

class EmbeddedTradingViewChartJSMixin:
    """EmbeddedTradingViewChartJSMixin extracted from EmbeddedTradingViewChart."""
    def _execute_js(self, script: str):
        """Execute JavaScript in the web view, queueing until chart is ready."""
        if self.page_loaded and self.chart_initialized:
            # Avoid logging high-frequency data updates like updatePanelData
            if ('Indicator' in script or 'Panel' in script or 'createPanel' in script) and 'updatePanelData' not in script:
                logger.info(f"🔧 Executing JS (indicator): {script[:100]}...")
            self.web_view.page().runJavaScript(script)
        else:
            self.pending_js_commands.append(script)
            if not self.page_loaded:
                logger.warning(f"❌ Page not loaded yet, queueing JS: {script[:50]}...")
            else:
                logger.warning(f"❌ Chart not initialized yet, queueing JS: {script[:50]}...")
    def _flush_pending_js(self):
        """Run any JS commands that were queued before chart initialization completed."""
        if not (self.page_loaded and self.chart_initialized):
            return
        while self.pending_js_commands:
            script = self.pending_js_commands.pop(0)
            self.web_view.page().runJavaScript(script)
