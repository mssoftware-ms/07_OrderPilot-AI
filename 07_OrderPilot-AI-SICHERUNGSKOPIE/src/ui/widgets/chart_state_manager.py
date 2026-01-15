"""Advanced Chart State Manager for OrderPilot-AI.

This module provides comprehensive state persistence for all chart types,
including zoom factors, indicator configurations, pane layouts, and row heights.
"""

import json
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QSettings, QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


@dataclass
class IndicatorState:
    """State of a single indicator."""
    type: str
    alias: str
    params: Dict[str, Any]
    visible: bool = True
    pane_index: int = 0
    row_height: float = 0.2  # Percentage of chart height


@dataclass
class PaneLayout:
    """Layout configuration for chart panes."""
    pane_count: int
    pane_heights: List[float]  # Relative heights (sum should be 1.0)
    splitter_positions: List[int] = None  # For PyQtGraph splitters


@dataclass
class ViewRange:
    """Visible range of the chart (zoom/pan state)."""
    x_min: float
    x_max: float
    y_min: float = None
    y_max: float = None
    logical_range_from: int = None  # For TradingView Lightweight Charts
    logical_range_to: int = None


@dataclass
class ChartState:
    """Complete chart state configuration."""
    symbol: str
    timeframe: str
    chart_type: str  # "tradingview", "pyqtgraph_advanced", "pyqtgraph_basic"
    theme: str = "dark"

    # View state
    view_range: ViewRange = None
    zoom_factor: float = 1.0

    # Layout
    pane_layout: PaneLayout = None

    # Indicators
    indicators: List[IndicatorState] = None

    # Window state
    window_geometry: bytes = None
    window_state: bytes = None

    # Additional settings
    show_volume: bool = True
    show_crosshair: bool = True
    auto_scale: bool = True
    drawings: List[dict] = None

    def __post_init__(self):
        if self.indicators is None:
            self.indicators = []
        if self.view_range is None:
            self.view_range = ViewRange(x_min=0, x_max=100)
        if self.pane_layout is None:
            self.pane_layout = PaneLayout(pane_count=1, pane_heights=[1.0])
        if self.drawings is None:
            self.drawings = []


class ChartStateManager(QObject):
    """Advanced state manager for chart persistence."""

    # Signals
    state_saved = pyqtSignal(str)  # symbol
    state_loaded = pyqtSignal(str, dict)  # symbol, state_dict

    def __init__(self, organization: str = "OrderPilot", application: str = "TradingApp"):
        """Initialize the state manager.

        Args:
            organization: Organization name for QSettings
            application: Application name for QSettings
        """
        super().__init__()
        self.settings = QSettings(organization, application)
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save_pending)
        self._auto_save_timer.setSingleShot(True)

        # Cache for pending saves (debouncing)
        self._pending_saves: Dict[str, ChartState] = {}
        self._auto_save_delay = 1000  # ms

        logger.info(f"ChartStateManager initialized with settings: {self.settings.fileName()}")

    def save_chart_state(self, symbol: str, chart_state: ChartState, auto_save: bool = False):
        """Save complete chart state to persistent storage.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTCUSD')
            chart_state: Complete chart state to save
            auto_save: If True, use debounced auto-save
        """
        try:
            if auto_save:
                # Debounced auto-save for frequent updates
                self._pending_saves[symbol] = chart_state
                self._auto_save_timer.start(self._auto_save_delay)
                return

            # Immediate save
            self._save_state_immediate(symbol, chart_state)

        except Exception as e:
            logger.error(f"Failed to save chart state for {symbol}: {e}")

    def load_chart_state(self, symbol: str, chart_type: str = None) -> Optional[ChartState]:
        """Load chart state from persistent storage.

        Args:
            symbol: Trading symbol
            chart_type: Optional chart type filter

        Returns:
            ChartState or None if not found
        """
        try:
            settings_key = f"charts/{self._sanitize_symbol(symbol)}"

            # Check if state exists
            if not self.settings.contains(f"{settings_key}/symbol"):
                logger.debug(f"No saved state found for symbol: {symbol}")
                return None

            # Load state components
            state_dict = {}

            # Basic properties
            state_dict['symbol'] = self.settings.value(f"{settings_key}/symbol", symbol)
            state_dict['timeframe'] = self.settings.value(f"{settings_key}/timeframe", "1D")
            state_dict['chart_type'] = self.settings.value(f"{settings_key}/chart_type", "tradingview")
            state_dict['theme'] = self.settings.value(f"{settings_key}/theme", "dark")
            state_dict['zoom_factor'] = self.settings.value(f"{settings_key}/zoom_factor", 1.0, type=float)

            # View range
            view_range_json = self.settings.value(f"{settings_key}/view_range")
            if view_range_json:
                view_range_dict = json.loads(view_range_json)
                state_dict['view_range'] = ViewRange(**view_range_dict)

            # Pane layout
            pane_layout_json = self.settings.value(f"{settings_key}/pane_layout")
            if pane_layout_json:
                pane_layout_dict = json.loads(pane_layout_json)
                state_dict['pane_layout'] = PaneLayout(**pane_layout_dict)

            # Indicators
            indicators_json = self.settings.value(f"{settings_key}/indicators")
            if indicators_json:
                indicators_list = json.loads(indicators_json)
                state_dict['indicators'] = [IndicatorState(**ind) for ind in indicators_list]

            # Window state
            state_dict['window_geometry'] = self.settings.value(f"{settings_key}/window_geometry")
            state_dict['window_state'] = self.settings.value(f"{settings_key}/window_state")

            # Boolean settings
            state_dict['show_volume'] = self.settings.value(f"{settings_key}/show_volume", True, type=bool)
            state_dict['show_crosshair'] = self.settings.value(f"{settings_key}/show_crosshair", True, type=bool)
            state_dict['auto_scale'] = self.settings.value(f"{settings_key}/auto_scale", True, type=bool)

            chart_state = ChartState(**state_dict)

            logger.info(f"Loaded chart state for {symbol}: {chart_state.chart_type}")
            self.state_loaded.emit(symbol, asdict(chart_state))

            return chart_state

        except Exception as e:
            logger.error(f"Failed to load chart state for {symbol}: {e}")
            return None

    def save_indicator_state(self, symbol: str, indicator: IndicatorState):
        """Save or update a single indicator state.

        Args:
            symbol: Trading symbol
            indicator: Indicator state to save
        """
        try:
            # Load existing state or create new
            chart_state = self.load_chart_state(symbol)
            if not chart_state:
                chart_state = ChartState(symbol=symbol, timeframe="1D", chart_type="tradingview")

            # Update or add indicator
            existing_indicator = None
            for i, ind in enumerate(chart_state.indicators):
                if ind.alias == indicator.alias:
                    existing_indicator = i
                    break

            if existing_indicator is not None:
                chart_state.indicators[existing_indicator] = indicator
            else:
                chart_state.indicators.append(indicator)

            self.save_chart_state(symbol, chart_state, auto_save=True)

        except Exception as e:
            logger.error(f"Failed to save indicator state for {symbol}: {e}")

    def save_view_range(self, symbol: str, view_range: ViewRange):
        """Save view range (zoom/pan state) for quick updates.

        Args:
            symbol: Trading symbol
            view_range: Current view range
        """
        try:
            chart_state = self.load_chart_state(symbol)
            if not chart_state:
                chart_state = ChartState(symbol=symbol, timeframe="1D", chart_type="tradingview")

            chart_state.view_range = view_range
            self.save_chart_state(symbol, chart_state, auto_save=True)

        except Exception as e:
            logger.error(f"Failed to save view range for {symbol}: {e}")

    def save_pane_layout(self, symbol: str, pane_layout: PaneLayout):
        """Save pane layout (row heights) for quick updates.

        Args:
            symbol: Trading symbol
            pane_layout: Current pane layout
        """
        try:
            chart_state = self.load_chart_state(symbol)
            if not chart_state:
                chart_state = ChartState(symbol=symbol, timeframe="1D", chart_type="tradingview")

            chart_state.pane_layout = pane_layout
            self.save_chart_state(symbol, chart_state, auto_save=True)

        except Exception as e:
            logger.error(f"Failed to save pane layout for {symbol}: {e}")

    def remove_chart_state(self, symbol: str):
        """Remove all saved state for a symbol.

        Args:
            symbol: Trading symbol to remove
        """
        try:
            settings_key = f"charts/{self._sanitize_symbol(symbol)}"
            self.settings.remove(settings_key)
            logger.info(f"Removed chart state for {symbol}")

        except Exception as e:
            logger.error(f"Failed to remove chart state for {symbol}: {e}")

    def list_saved_symbols(self) -> List[str]:
        """Get list of symbols with saved states.

        Returns:
            List of symbols that have saved chart states
        """
        try:
            self.settings.beginGroup("charts")
            symbols = self.settings.childGroups()
            self.settings.endGroup()

            # Reverse sanitization
            return [self._unsanitize_symbol(symbol) for symbol in symbols]

        except Exception as e:
            logger.error(f"Failed to list saved symbols: {e}")
            return []

    def clear_all_states(self):
        """Clear all saved chart states."""
        try:
            self.settings.remove("charts")
            logger.info("Cleared all chart states")

        except Exception as e:
            logger.error(f"Failed to clear all states: {e}")

    def _save_state_immediate(self, symbol: str, chart_state: ChartState):
        """Perform immediate save to QSettings."""
        settings_key = f"charts/{self._sanitize_symbol(symbol)}"

        # Basic properties
        self.settings.setValue(f"{settings_key}/symbol", chart_state.symbol)
        self.settings.setValue(f"{settings_key}/timeframe", chart_state.timeframe)
        self.settings.setValue(f"{settings_key}/chart_type", chart_state.chart_type)
        self.settings.setValue(f"{settings_key}/theme", chart_state.theme)
        self.settings.setValue(f"{settings_key}/zoom_factor", chart_state.zoom_factor)

        # View range
        if chart_state.view_range:
            view_range_json = json.dumps(asdict(chart_state.view_range))
            self.settings.setValue(f"{settings_key}/view_range", view_range_json)

        # Pane layout
        if chart_state.pane_layout:
            pane_layout_json = json.dumps(asdict(chart_state.pane_layout))
            self.settings.setValue(f"{settings_key}/pane_layout", pane_layout_json)

        # Indicators
        if chart_state.indicators:
            indicators_json = json.dumps([asdict(ind) for ind in chart_state.indicators])
            self.settings.setValue(f"{settings_key}/indicators", indicators_json)

        # Window state
        if chart_state.window_geometry:
            self.settings.setValue(f"{settings_key}/window_geometry", chart_state.window_geometry)
        if chart_state.window_state:
            self.settings.setValue(f"{settings_key}/window_state", chart_state.window_state)

        # Boolean settings
        self.settings.setValue(f"{settings_key}/show_volume", chart_state.show_volume)
        self.settings.setValue(f"{settings_key}/show_crosshair", chart_state.show_crosshair)
        self.settings.setValue(f"{settings_key}/auto_scale", chart_state.auto_scale)

        # Force sync to disk
        self.settings.sync()

        logger.debug(f"Saved chart state for {symbol}")
        self.state_saved.emit(symbol)

    def _auto_save_pending(self):
        """Process pending auto-saves."""
        for symbol, chart_state in self._pending_saves.items():
            self._save_state_immediate(symbol, chart_state)

        self._pending_saves.clear()

    def _sanitize_symbol(self, symbol: str) -> str:
        """Sanitize symbol for use as QSettings key."""
        # Replace characters that might cause issues in QSettings keys
        return symbol.replace("/", "_").replace(":", "_").replace("*", "_")

    def _unsanitize_symbol(self, sanitized: str) -> str:
        """Reverse symbol sanitization (basic approximation)."""
        # Note: This is lossy conversion, consider storing original mapping if needed
        return sanitized.replace("_", "/")


class TradingViewChartStateHelper:
    """Helper for TradingView Lightweight Charts state persistence."""

    @staticmethod
    def create_js_set_visible_range(range_dict: Dict[str, Any]) -> str:
        """Create JavaScript code to set visible range.

        Args:
            range_dict: Dict with 'from' and 'to' keys

        Returns:
            JavaScript code string
        """
        return f"""
        if (window.chartAPI && window.chartAPI.timeScale) {{
            window.chartAPI.timeScale().setVisibleLogicalRange({{
                from: {range_dict.get('logical_range_from', 0)},
                to: {range_dict.get('logical_range_to', 100)}
            }});
        }}
        """

    @staticmethod
    def create_js_get_visible_range() -> str:
        """Create JavaScript code to get visible range."""
        return """
        if (window.chartAPI && window.chartAPI.timeScale) {
            const range = window.chartAPI.timeScale().getVisibleLogicalRange();
            return range ? {
                logical_range_from: range.from,
                logical_range_to: range.to
            } : null;
        }
        return null;
        """

    @staticmethod
    def create_js_set_pane_layout(layout: PaneLayout) -> str:
        """Create JavaScript code to set pane layout.

        Args:
            layout: Pane layout configuration

        Returns:
            JavaScript code string
        """
        height_assignments = []
        for i, height in enumerate(layout.pane_heights):
            height_assignments.append(f"panes[{i}] && panes[{i}].setStretchFactor({height});")

        return f"""
        if (window.chartAPI && window.paneManager) {{
            const panes = window.paneManager.getPanes();
            {' '.join(height_assignments)}
        }}
        """

    @staticmethod
    def create_js_get_pane_layout() -> str:
        """Create JavaScript code to get current pane layout."""
        return """
        if (window.chartAPI && window.paneManager) {
            const panes = window.paneManager.getPanes();
            return {
                pane_count: panes.length,
                pane_heights: panes.map((pane, index) => pane.getStretchFactor ? pane.getStretchFactor() : (1.0 / panes.length))
            };
        }
        return null;
        """


class PyQtGraphChartStateHelper:
    """Helper for PyQtGraph chart state persistence."""

    @staticmethod
    def save_viewbox_state(viewbox) -> Dict[str, Any]:
        """Save PyQtGraph ViewBox state.

        Args:
            viewbox: PyQtGraph ViewBox instance

        Returns:
            State dictionary
        """
        try:
            if hasattr(viewbox, 'getState'):
                # Use built-in getState if available
                state = viewbox.getState()
                return {
                    'viewRange': state.get('viewRange'),
                    'autoRange': state.get('autoRange'),
                    'targetRange': state.get('targetRange'),
                }
            else:
                # Manual state extraction
                view_range = viewbox.viewRange()
                return {
                    'x_range': view_range[0],
                    'y_range': view_range[1],
                    'auto_range_x': viewbox.autoRangeEnabled()[0],
                    'auto_range_y': viewbox.autoRangeEnabled()[1],
                }

        except Exception as e:
            logger.warning(f"Failed to save PyQtGraph ViewBox state: {e}")
            return {}

    @staticmethod
    def restore_viewbox_state(viewbox, state_dict: Dict[str, Any]):
        """Restore PyQtGraph ViewBox state.

        Args:
            viewbox: PyQtGraph ViewBox instance
            state_dict: Saved state dictionary
        """
        try:
            if 'viewRange' in state_dict and hasattr(viewbox, 'setState'):
                # Use built-in setState if available
                viewbox.setState(state_dict)
            elif 'x_range' in state_dict and 'y_range' in state_dict:
                # Manual state restoration
                viewbox.setRange(
                    xRange=state_dict['x_range'],
                    yRange=state_dict['y_range'],
                    padding=0
                )

                # Restore auto-range settings
                if 'auto_range_x' in state_dict and 'auto_range_y' in state_dict:
                    viewbox.enableAutoRange(
                        x=state_dict['auto_range_x'],
                        y=state_dict['auto_range_y']
                    )

        except Exception as e:
            logger.warning(f"Failed to restore PyQtGraph ViewBox state: {e}")


# Global instance (singleton pattern)
_chart_state_manager = None

def get_chart_state_manager() -> ChartStateManager:
    """Get global chart state manager instance."""
    global _chart_state_manager
    if _chart_state_manager is None:
        _chart_state_manager = ChartStateManager()
    return _chart_state_manager
