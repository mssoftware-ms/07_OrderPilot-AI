"""Chart State Integration Mixin for OrderPilot-AI Chart Widgets.

This module provides mixins and integration utilities to add comprehensive
state persistence to existing chart widgets without breaking their current functionality.
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget

from .chart_state_manager import (
    ChartStateManager, ChartState, IndicatorState, ViewRange, PaneLayout,
    TradingViewChartStateHelper, PyQtGraphChartStateHelper,
    get_chart_state_manager
)

logger = logging.getLogger(__name__)


class TradingViewChartStateMixin:
    """Mixin for TradingView Lightweight Charts state persistence.

    Add this mixin to your EmbeddedTradingViewChart class to get automatic
    state persistence functionality.
    """

    # Additional signals for state management
    chart_state_saved = pyqtSignal(str)  # symbol
    chart_state_loaded = pyqtSignal(str, dict)  # symbol, state

    def __init_chart_state__(self):
        """Initialize chart state management. Call this in your chart's __init__."""
        self.state_manager = get_chart_state_manager()
        self._auto_save_enabled = True
        self._state_save_timer = QTimer()
        self._state_save_timer.setSingleShot(True)
        self._state_save_timer.timeout.connect(self._save_current_state)

        # Track state changes for debounced saving
        self._pending_state_save = False
        self._last_saved_state = None

        # Connect to state manager signals
        self.state_manager.state_saved.connect(self._on_state_saved)
        self.state_manager.state_loaded.connect(self._on_state_loaded)

        logger.debug("TradingView chart state management initialized")

    def save_chart_state_now(self, include_window_state: bool = True):
        """Immediately save current chart state.

        Args:
            include_window_state: Whether to include window geometry/state
        """
        try:
            if not hasattr(self, 'current_symbol') or not self.current_symbol:
                logger.debug("No symbol set, skipping state save")
                return

            # Get current chart state via JavaScript
            self._get_chart_state_async(lambda state: self._save_chart_state_callback(
                state, include_window_state
            ))

        except Exception as e:
            logger.error(f"Failed to save chart state: {e}")

    def load_chart_state_now(self) -> bool:
        """Load saved chart state for current symbol.

        Returns:
            True if state was loaded, False if no saved state found
        """
        try:
            if not hasattr(self, 'current_symbol') or not self.current_symbol:
                logger.debug("No symbol set, skipping state load")
                return False

            # Load state from manager
            chart_state = self.state_manager.load_chart_state(
                self.current_symbol,
                chart_type="tradingview"
            )

            if not chart_state:
                logger.debug(f"No saved state found for {self.current_symbol}")
                return False

            # Apply state to chart
            self._apply_chart_state(chart_state)
            return True

        except Exception as e:
            logger.error(f"Failed to load chart state: {e}")
            return False

    def enable_auto_save_state(self, enabled: bool = True):
        """Enable or disable automatic state saving.

        Args:
            enabled: Whether to enable auto-save
        """
        self._auto_save_enabled = enabled
        logger.info(f"Chart state auto-save: {'enabled' if enabled else 'disabled'}")

    def clear_saved_state(self):
        """Clear saved state for current symbol."""
        if hasattr(self, 'current_symbol') and self.current_symbol:
            self.state_manager.remove_chart_state(self.current_symbol)
            logger.info(f"Cleared saved state for {self.current_symbol}")

    def _schedule_state_save(self, delay_ms: int = 2000):
        """Schedule a debounced state save.

        Args:
            delay_ms: Delay in milliseconds before saving
        """
        if not self._auto_save_enabled:
            return

        self._pending_state_save = True
        self._state_save_timer.start(delay_ms)

    def _save_current_state(self):
        """Internal method to save current state (called by timer)."""
        if self._pending_state_save:
            self.save_chart_state_now(include_window_state=False)
            self._pending_state_save = False

    def _get_chart_state_async(self, callback: Callable[[Dict[str, Any]], None]):
        """Get current chart state asynchronously via JavaScript.

        Args:
            callback: Function to call with state data
        """
        js_code = """
        (function() {
            try {
                if (!window.chartAPI || !window.chartAPI.getChartState) {
                    return { error: 'Chart API not ready' };
                }

                const state = window.chartAPI.getChartState();
                return state || { error: 'No state returned' };
            } catch (e) {
                return { error: e.message };
            }
        })();
        """

        def handle_result(result):
            if isinstance(result, dict) and 'error' not in result:
                callback(result)
            else:
                logger.warning(f"Failed to get chart state: {result}")
                callback({})

        # Execute JavaScript and handle result
        if hasattr(self, 'web_view') and hasattr(self.web_view, 'page'):
            self.web_view.page().runJavaScript(js_code, handle_result)

    def _save_chart_state_callback(self, js_state: Dict[str, Any], include_window: bool):
        """Callback to save chart state after getting JavaScript state.

        Args:
            js_state: State data from JavaScript
            include_window: Whether to include window state
        """
        try:
            # Convert JavaScript state to ChartState object
            chart_state = self._convert_js_to_chart_state(js_state, include_window)

            # Save to state manager
            self.state_manager.save_chart_state(
                self.current_symbol,
                chart_state,
                auto_save=True
            )

            logger.debug(f"Saved chart state for {self.current_symbol}")

        except Exception as e:
            logger.error(f"Failed in save chart state callback: {e}")

    def _convert_js_to_chart_state(self, js_state: Dict[str, Any], include_window: bool) -> ChartState:
        """Convert JavaScript chart state to ChartState object.

        Args:
            js_state: State from JavaScript
            include_window: Whether to include window state

        Returns:
            ChartState object
        """
        # Create view range from JavaScript visible range
        view_range = None
        if 'visibleRange' in js_state and js_state['visibleRange']:
            vr = js_state['visibleRange']
            view_range = ViewRange(
                x_min=0, x_max=100,  # Placeholder values
                logical_range_from=vr.get('from', 0),
                logical_range_to=vr.get('to', 100)
            )

        # Create pane layout from JavaScript pane data
        pane_layout = None
        if 'paneLayout' in js_state and js_state['paneLayout']:
            pl = js_state['paneLayout']
            pane_layout = PaneLayout(
                pane_count=pl.get('pane_count', 1),
                pane_heights=pl.get('pane_heights', [1.0])
            )

        # Extract indicator information
        indicators = []
        if 'activeSeries' in js_state:
            # Convert active overlays to indicator states
            for overlay_name in js_state['activeSeries'].get('overlays', []):
                if hasattr(self, 'active_indicator_params') and overlay_name in self.active_indicator_params:
                    indicator = IndicatorState(
                        type=overlay_name,
                        alias=overlay_name,
                        params=self.active_indicator_params.get(overlay_name, {}),
                        visible=True,
                        pane_index=0  # Overlays are on main pane
                    )
                    indicators.append(indicator)

            # Convert panel indicators
            for panel_name in js_state['activeSeries'].get('panels', []):
                if hasattr(self, 'active_indicator_params') and panel_name in self.active_indicator_params:
                    indicator = IndicatorState(
                        type=panel_name,
                        alias=panel_name,
                        params=self.active_indicator_params.get(panel_name, {}),
                        visible=True,
                        pane_index=1  # Separate pane
                    )
                    indicators.append(indicator)

        # Get window state if requested
        window_geometry = None
        window_state = None
        if include_window and hasattr(self, 'window') and self.window():
            window_geometry = self.window().saveGeometry()
            if hasattr(self.window(), 'saveState'):
                window_state = self.window().saveState()

        # Create complete chart state
        chart_state = ChartState(
            symbol=getattr(self, 'current_symbol', 'UNKNOWN'),
            timeframe=getattr(self, 'current_timeframe', '1D'),
            chart_type="tradingview",
            theme=getattr(self, 'current_theme', 'dark'),
            view_range=view_range,
            pane_layout=pane_layout,
            indicators=indicators,
            window_geometry=window_geometry,
            window_state=window_state,
            show_volume=getattr(self, 'show_volume', True),
            show_crosshair=True,
            auto_scale=True
        )

        return chart_state

    def _apply_chart_state(self, chart_state: ChartState):
        """Apply loaded chart state to the chart.

        Args:
            chart_state: State to apply
        """
        try:
            # Apply basic settings
            if hasattr(self, 'current_timeframe'):
                self.current_timeframe = chart_state.timeframe

            # Apply window state
            if chart_state.window_geometry and hasattr(self, 'window') and self.window():
                self.window().restoreGeometry(chart_state.window_geometry)

            if chart_state.window_state and hasattr(self, 'window') and self.window():
                if hasattr(self.window(), 'restoreState'):
                    self.window().restoreState(chart_state.window_state)

            # Apply indicators
            if chart_state.indicators:
                self._apply_indicators(chart_state.indicators)

            # Apply view range and pane layout via JavaScript
            self._apply_chart_state_js(chart_state)

            logger.info(f"Applied chart state for {chart_state.symbol}")
            self.chart_state_loaded.emit(chart_state.symbol, chart_state.__dict__)

        except Exception as e:
            logger.error(f"Failed to apply chart state: {e}")

    def _apply_indicators(self, indicators: list):
        """Apply indicator states to the chart.

        Args:
            indicators: List of IndicatorState objects
        """
        try:
            for indicator in indicators:
                if hasattr(self, 'active_indicators'):
                    self.active_indicators[indicator.alias] = indicator.visible

                if hasattr(self, 'active_indicator_params'):
                    self.active_indicator_params[indicator.alias] = indicator.params

                # Trigger indicator loading if chart is ready
                if hasattr(self, 'chart_initialized') and self.chart_initialized:
                    self._load_indicator_async(indicator)

        except Exception as e:
            logger.error(f"Failed to apply indicators: {e}")

    def _apply_chart_state_js(self, chart_state: ChartState):
        """Apply chart state via JavaScript.

        Args:
            chart_state: Chart state to apply
        """
        try:
            # Prepare state object for JavaScript
            js_state = {}

            if chart_state.view_range:
                js_state['visibleRange'] = {
                    'from': chart_state.view_range.logical_range_from,
                    'to': chart_state.view_range.logical_range_to
                }

            if chart_state.pane_layout:
                js_state['paneLayout'] = {
                    'pane_count': chart_state.pane_layout.pane_count,
                    'pane_heights': chart_state.pane_layout.pane_heights
                }

            # Generate JavaScript code to apply state
            js_code = f"""
            (function() {{
                try {{
                    if (!window.chartAPI || !window.chartAPI.setChartState) {{
                        console.warn('Chart API not ready for state restoration');
                        return false;
                    }}

                    const state = {json.dumps(js_state)};
                    return window.chartAPI.setChartState(state);
                }} catch (e) {{
                    console.error('Error applying chart state:', e);
                    return false;
                }}
            }})();
            """

            # Execute with delay to ensure chart is ready
            QTimer.singleShot(1000, lambda: self._execute_js_if_ready(js_code))

        except Exception as e:
            logger.error(f"Failed to prepare JavaScript state application: {e}")

    def _execute_js_if_ready(self, js_code: str):
        """Execute JavaScript code if chart is ready.

        Args:
            js_code: JavaScript code to execute
        """
        if hasattr(self, 'web_view') and hasattr(self.web_view, 'page'):
            self.web_view.page().runJavaScript(js_code)

    def _load_indicator_async(self, indicator: IndicatorState):
        """Load a single indicator asynchronously.

        Args:
            indicator: Indicator to load
        """
        try:
            # This would trigger your existing indicator loading mechanism
            if hasattr(self, '_add_indicator_to_chart'):
                self._add_indicator_to_chart(indicator.type, indicator.params)

        except Exception as e:
            logger.error(f"Failed to load indicator {indicator.alias}: {e}")

    def _on_state_saved(self, symbol: str):
        """Handle state saved signal from manager."""
        if symbol == getattr(self, 'current_symbol', None):
            self.chart_state_saved.emit(symbol)

    def _on_state_loaded(self, symbol: str, state_dict: Dict[str, Any]):
        """Handle state loaded signal from manager."""
        if symbol == getattr(self, 'current_symbol', None):
            self.chart_state_loaded.emit(symbol, state_dict)

    # Event handlers to trigger auto-save
    def _on_zoom_changed(self):
        """Call this when zoom changes to trigger auto-save."""
        self._schedule_state_save(delay_ms=1500)

    def _on_pan_changed(self):
        """Call this when pan changes to trigger auto-save."""
        self._schedule_state_save(delay_ms=1500)

    def _on_indicator_changed(self):
        """Call this when indicators change to trigger auto-save."""
        self._schedule_state_save(delay_ms=500)

    def _on_pane_layout_changed(self):
        """Call this when pane layout changes to trigger auto-save."""
        self._schedule_state_save(delay_ms=1000)


class PyQtGraphChartStateMixin:
    """Mixin for PyQtGraph chart state persistence."""

    def __init_chart_state__(self):
        """Initialize chart state management for PyQtGraph."""
        self.state_manager = get_chart_state_manager()
        self._auto_save_enabled = True

    def save_chart_state_now(self):
        """Save current PyQtGraph chart state."""
        try:
            if not hasattr(self, 'current_symbol') or not self.current_symbol:
                return

            # Get viewbox state
            viewbox_state = {}
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'plotItem'):
                viewbox = self.chart_widget.plotItem.vb
                viewbox_state = PyQtGraphChartStateHelper.save_viewbox_state(viewbox)

            # Create view range
            view_range = ViewRange(
                x_min=viewbox_state.get('x_range', [0, 100])[0],
                x_max=viewbox_state.get('x_range', [0, 100])[1],
                y_min=viewbox_state.get('y_range', [0, 100])[0] if 'y_range' in viewbox_state else None,
                y_max=viewbox_state.get('y_range', [0, 100])[1] if 'y_range' in viewbox_state else None,
            )

            # Create chart state
            chart_state = ChartState(
                symbol=self.current_symbol,
                timeframe=getattr(self, 'current_timeframe', '1D'),
                chart_type="pyqtgraph",
                view_range=view_range,
                # Add indicators if available
                indicators=self._get_pyqtgraph_indicators() if hasattr(self, '_get_pyqtgraph_indicators') else []
            )

            self.state_manager.save_chart_state(self.current_symbol, chart_state)

        except Exception as e:
            logger.error(f"Failed to save PyQtGraph chart state: {e}")

    def load_chart_state_now(self) -> bool:
        """Load saved PyQtGraph chart state."""
        try:
            if not hasattr(self, 'current_symbol') or not self.current_symbol:
                return False

            chart_state = self.state_manager.load_chart_state(
                self.current_symbol,
                chart_type="pyqtgraph"
            )

            if not chart_state:
                return False

            # Apply viewbox state
            if hasattr(self, 'chart_widget') and chart_state.view_range:
                viewbox = self.chart_widget.plotItem.vb
                state_dict = {
                    'x_range': [chart_state.view_range.x_min, chart_state.view_range.x_max]
                }
                if chart_state.view_range.y_min is not None and chart_state.view_range.y_max is not None:
                    state_dict['y_range'] = [chart_state.view_range.y_min, chart_state.view_range.y_max]

                PyQtGraphChartStateHelper.restore_viewbox_state(viewbox, state_dict)

            return True

        except Exception as e:
            logger.error(f"Failed to load PyQtGraph chart state: {e}")
            return False


def install_chart_state_persistence(chart_widget, chart_type: str = "auto"):
    """Install state persistence on an existing chart widget.

    Args:
        chart_widget: Chart widget to enhance
        chart_type: Type of chart ("tradingview", "pyqtgraph", or "auto")

    Returns:
        Enhanced chart widget
    """
    if chart_type == "auto":
        # Auto-detect chart type
        if hasattr(chart_widget, 'web_view'):
            chart_type = "tradingview"
        elif hasattr(chart_widget, 'chart_widget'):
            chart_type = "pyqtgraph"
        else:
            logger.warning("Could not auto-detect chart type")
            return chart_widget

    try:
        if chart_type == "tradingview":
            # Add TradingView mixin
            if not hasattr(chart_widget, '__init_chart_state__'):
                chart_widget.__class__ = type(
                    chart_widget.__class__.__name__ + 'WithState',
                    (TradingViewChartStateMixin, chart_widget.__class__),
                    {}
                )
                chart_widget.__init_chart_state__()

        elif chart_type == "pyqtgraph":
            # Add PyQtGraph mixin
            if not hasattr(chart_widget, '__init_chart_state__'):
                chart_widget.__class__ = type(
                    chart_widget.__class__.__name__ + 'WithState',
                    (PyQtGraphChartStateMixin, chart_widget.__class__),
                    {}
                )
                chart_widget.__init_chart_state__()

        logger.info(f"Installed {chart_type} state persistence on chart widget")

    except Exception as e:
        logger.error(f"Failed to install state persistence: {e}")

    return chart_widget