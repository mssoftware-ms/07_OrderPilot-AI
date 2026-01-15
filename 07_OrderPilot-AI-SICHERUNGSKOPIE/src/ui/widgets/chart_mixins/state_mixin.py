"""State Mixin for EmbeddedTradingViewChart.

Contains state management methods (get/set visible range, pane layout, chart state).
"""

import json
import logging

logger = logging.getLogger(__name__)


class ChartStateMixin:
    """Mixin providing state management for EmbeddedTradingViewChart."""

    def get_visible_range(self, callback):
        """Asynchronously get the current visible logical range.

        Args:
            callback: Function to call with the result (dict/None)
        """
        if self.page_loaded and self.chart_initialized:
            self.web_view.page().runJavaScript(
                "window.chartAPI.getVisibleRange();",
                callback
            )
        else:
            callback(None)

    def set_visible_range(self, range_data: dict):
        """Restore visible logical range.

        Args:
            range_data: Dictionary with 'from' and 'to' logical indices
        """
        if not range_data:
            logger.warning("⚠️ set_visible_range called with empty range_data")
            return

        logger.info(f"📐 set_visible_range called with: {range_data}")
        logger.info(f"   Chart state: page_loaded={self.page_loaded}, chart_initialized={self.chart_initialized}")

        json_range = json.dumps(range_data)
        js_command = f"window.chartAPI.setVisibleRange({json_range});"

        # Execute with callback to verify result
        def _on_result(success):
            if success:
                logger.info(f"✅ setVisibleRange succeeded")
            else:
                logger.warning(f"⚠️ setVisibleRange returned false or failed")

        if self.page_loaded and self.chart_initialized:
            logger.info(f"🔧 Executing setVisibleRange JS directly")
            self.web_view.page().runJavaScript(js_command, _on_result)
        else:
            logger.warning(f"⚠️ Chart not ready, queueing setVisibleRange command")
            self._execute_js(js_command)

    def get_pane_layout(self, callback):
        """Asynchronously get the current pane layout (stretch factors).

        Args:
            callback: Function to call with the result (dict)
        """
        logger.info(f"🔍 get_pane_layout called (page_loaded={self.page_loaded}, chart_initialized={self.chart_initialized})")

        if self.page_loaded and self.chart_initialized:
            logger.info("✅ Chart ready, requesting pane layout from JavaScript...")

            def _on_result(result):
                logger.info(f"📥 JavaScript returned pane layout: type={type(result)}, value={result}")
                callback(result)

            self.web_view.page().runJavaScript(
                "window.chartAPI.getPaneLayout();",
                _on_result
            )
        else:
            logger.warning("⚠️ Cannot get pane layout: chart not initialized")
            callback({})

    def set_pane_layout(self, layout: dict):
        """Restore pane layout (stretch factors).

        Args:
            layout: Dictionary mapping pane IDs to stretch factors
        """
        if not layout:
            logger.warning("⚠️ set_pane_layout: No layout provided")
            return

        logger.info(f"📐 set_pane_layout called with: {layout}")
        json_layout = json.dumps(layout)
        js_command = f"window.chartAPI.setPaneLayout({json_layout});"
        logger.info(f"🔧 Executing JS: {js_command}")

        # Execute with callback to verify result
        def _on_result(success):
            if success:
                logger.info(f"✅ setPaneLayout succeeded: {success}")
            else:
                logger.warning(f"⚠️ setPaneLayout failed or returned false")

        if self.page_loaded and self.chart_initialized:
            self.web_view.page().runJavaScript(js_command, _on_result)
        else:
            logger.warning("⚠️ Chart not ready, queueing setPaneLayout command")
            self._execute_js(js_command)

    def get_chart_state(self, callback):
        """Get comprehensive chart state including panes, zoom, and indicators.

        Args:
            callback: Function to call with the complete state dict
        """
        if self.page_loaded and self.chart_initialized:
            logger.info("🔍 Requesting complete chart state from JavaScript")
            self.web_view.page().runJavaScript(
                "window.chartAPI.getChartState();",
                callback
            )
        else:
            logger.warning("⚠️ Cannot get chart state: chart not initialized")
            callback({})

    def set_chart_state(self, state: dict):
        """Restore comprehensive chart state.

        Args:
            state: State dictionary from get_chart_state()
        """
        if not state:
            logger.warning("⚠️ set_chart_state: No state provided")
            return

        logger.info(f"📊 set_chart_state called with keys: {list(state.keys())}")
        json_state = json.dumps(state)
        js_command = f"window.chartAPI.setChartState({json_state});"

        def _on_result(success):
            if success:
                logger.info(f"✅ Chart state restoration succeeded")
            else:
                logger.warning(f"⚠️ Chart state restoration failed")

        if self.page_loaded and self.chart_initialized:
            self.web_view.page().runJavaScript(js_command, _on_result)
        else:
            logger.warning("⚠️ Chart not ready, queueing setChartState command")
            self._execute_js(js_command)
