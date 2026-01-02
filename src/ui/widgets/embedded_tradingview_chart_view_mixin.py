from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

class EmbeddedTradingViewChartViewMixin:
    """EmbeddedTradingViewChartViewMixin extracted from EmbeddedTradingViewChart."""
    def zoom_to_fit_all(self):
        """Zoom to full data range and normalize pane heights.

        - Fits time + price scale using chartAPI.fitContent()
        - Rescales pane stretch factors so the price pane stays dominant
        """
        # Snapshot current view for undo
        self._execute_js("window.chartAPI.rememberViewState();")

        # Always attempt a fit (queued if not ready)
        def _do_fit():
            self._execute_js("window.chartAPI.fitContent();")

        if not (self.page_loaded and self.chart_initialized):
            logger.info("Zoom-to-fit queued: chart not ready yet")
            _do_fit()
            return

        def _apply_layout(layout: dict):
            try:
                layout = layout or {}
                indicator_ids = [k for k in layout.keys() if k != "price"]

                if indicator_ids:
                    # Keep price pane dominant, indicators equal + reasonable height
                    price_weight = 5
                    indicator_weight = 1
                    new_layout = {"price": price_weight}
                    for pid in indicator_ids:
                        new_layout[pid] = indicator_weight
                    self.set_pane_layout(new_layout)
                else:
                    # Ensure at least a healthy price pane height
                    self.set_pane_layout({"price": 5})
            finally:
                _do_fit()

        # Fetch current panes to know which indicator panes exist
        self.get_pane_layout(_apply_layout)
    def zoom_back_to_previous_view(self) -> bool:
        """Restore the previous zoom/layout state (one-step undo).

        Returns:
            True if a previous state existed and was applied, else False.
        """
        if not (self.page_loaded and self.chart_initialized):
            logger.info("Zoom-back skipped: chart not ready")
            return False

        def _on_result(success):
            logger.info("Zoom-back executed, success=%s", success)

        self.web_view.page().runJavaScript("window.chartAPI.restoreLastView();", _on_result)
        # Fire-and-forget; assume success if state existed
        return True

    def request_chart_resize(self) -> None:
        """Force the JS chart to match the current Qt container size.

        Useful after dock/undock or when the chat panel is shown/hidden.
        Safe to call even before the chart is ready; the JS call is queued.
        """
        resize_script = """
            (() => {
                if (window.chartAPI && typeof window.chartAPI.resizeToContainer === 'function') {
                    return window.chartAPI.resizeToContainer();
                }
                return false;
            })();
        """
        try:
            self._execute_js(resize_script)
        except Exception as exc:
            logger.debug("Chart resize request failed: %s", exc)
