"""Embedded TradingView Lightweight Charts Widget."""

from __future__ import annotations

import logging
from collections import deque
from typing import Optional, Dict, List

import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logging.warning("PyQt6-WebEngine not installed. Chart widget will not work.")

from src.chart_marking import ChartMarkingMixin
from src.common.event_bus import EventType, event_bus
from src.core.indicators.engine import IndicatorEngine
from src.core.market_data.types import AssetClass, DataSource

from .chart_mixins import (
    ToolbarMixin,
    IndicatorMixin,
    StreamingMixin,
    DataLoadingMixin,
    ChartStateMixin,
    BotOverlayMixin,
    LevelZonesMixin,
)
from .chart_mixins.entry_analyzer_mixin import EntryAnalyzerMixin
from .chart_mixins.heatmap_mixin import HeatmapMixin
from .chart_js_template import get_chart_html_template
from .embedded_tradingview_bridge import ChartBridge
from .embedded_tradingview_chart_events_mixin import EmbeddedTradingViewChartEventsMixin
from .embedded_tradingview_chart_js_mixin import EmbeddedTradingViewChartJSMixin
from .embedded_tradingview_chart_loading_mixin import EmbeddedTradingViewChartLoadingMixin
from .embedded_tradingview_chart_marking_mixin import EmbeddedTradingViewChartMarkingMixin
from .embedded_tradingview_chart_ui_mixin import EmbeddedTradingViewChartUIMixin
from .embedded_tradingview_chart_view_mixin import EmbeddedTradingViewChartViewMixin
from .chart_ai_markings_mixin import ChartAIMarkingsMixin

logger = logging.getLogger(__name__)


class EmbeddedTradingViewChart(
    EntryAnalyzerMixin,  # Entry Analyzer popup integration
    ChartAIMarkingsMixin,  # AI-driven markings (must be early for method override)
    ChartMarkingMixin,
    HeatmapMixin,  # Liquidation Heatmap integration
    LevelZonesMixin,  # Phase 5.5: Level zones support
    BotOverlayMixin,
    ToolbarMixin,
    IndicatorMixin,
    StreamingMixin,
    DataLoadingMixin,
    ChartStateMixin,
    EmbeddedTradingViewChartUIMixin,
    EmbeddedTradingViewChartMarkingMixin,
    EmbeddedTradingViewChartJSMixin,
    EmbeddedTradingViewChartViewMixin,
    EmbeddedTradingViewChartLoadingMixin,
    EmbeddedTradingViewChartEventsMixin,
    QWidget,
):
    """Embedded TradingView Lightweight Charts widget."""

    # Signals
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)
    data_loaded = pyqtSignal()
    indicator_toggled = pyqtSignal(str, bool, dict)
    # Thread-safe signals for streaming updates (called from background threads)
    _tick_received = pyqtSignal(object)
    _bar_received = pyqtSignal(object)
    # Chart trading signals - emitted when user drags lines in chart
    stop_line_moved = pyqtSignal(str, float)  # (line_id, new_price)
    # Candle closed signal - emitted when a new candle starts (previous candle closed)
    candle_closed = pyqtSignal(float, float, float, float, float)  # (prev_open, prev_high, prev_low, prev_close, new_open)
    # Tick price signal - emitted on every valid tick for real-time P&L updates
    tick_price_updated = pyqtSignal(float)  # (current_price)

    def __init__(self, history_manager=None):
        """Initialize embedded chart widget.

        Args:
            history_manager: HistoryManager instance for loading data
        """
        super().__init__()

        if not WEBENGINE_AVAILABLE:
            logger.error("PyQt6-WebEngine not installed!")
            self._show_error_ui()
            return

        self.history_manager = history_manager
        self.indicator_engine = IndicatorEngine()

        # Data storage
        self.current_symbol = "AAPL"
        self.current_timeframe = "1T"
        self.current_period = "1D"
        self.current_data_provider: Optional[str] = None
        self.current_asset_class: Optional[AssetClass] = None
        self.current_data_source: Optional[DataSource] = None
        self.data: Optional[pd.DataFrame] = None
        self.volume_data: list = []
        self.active_indicators: Dict[str, dict] = {}
        self.active_indicator_params: Dict[str, dict] = {}
        self.live_streaming_enabled = False
        self._indicator_counter = 0
        self._pending_indicator_instances: list = []

        # State restoration queue
        self._pending_state_restoration = None
        self._indicators_loaded = False
        self._restoring_state = False  # Flag to prevent fitContent() during restoration
        self._skip_fit_content = False  # Flag to skip fitContent() on data load

        # Page load state
        self.page_loaded = False
        self.chart_initialized = False
        self.pending_data_load: Optional[pd.DataFrame] = None
        self.pending_js_commands: List[str] = []
        self.chart_ready_timer: Optional[QTimer] = None

        # Update batching for performance
        self.pending_bars = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_pending_updates)
        self.update_timer.setInterval(1000)

        # Indicator update lock to prevent race conditions
        self._updating_indicators = False

        # Initialize bot overlay (from BotOverlayMixin)
        self._init_bot_overlay()

        # Initialize chart marking (from ChartMarkingMixin)
        self._init_chart_marking()

        # Initialize Entry Analyzer (from EntryAnalyzerMixin)
        self._init_entry_analyzer()

        # Initialize data loading (from DataLoadingMixin) - CRITICAL: Must be called before _setup_ui
        self._setup_data_loading()

        # Setup UI
        self._setup_ui()

        # Initialize level zones (from LevelZonesMixin)
        self._setup_level_zones()

        # Connect thread-safe signals to handlers (runs in main thread)
        self._tick_received.connect(self._handle_tick_main_thread)
        self._bar_received.connect(self._handle_bar_main_thread)

        # Subscribe to events - these emit signals for thread safety
        event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar_event)
        event_bus.subscribe(EventType.MARKET_TICK, self._on_market_tick_event)
        event_bus.subscribe(EventType.MARKET_DATA_TICK, self._on_market_tick_event)

        logger.info("EmbeddedTradingViewChart initialized")

    # Public helper to add a full-width price range (used by chat evaluation popup)
    def add_rect_range(self, low: float, high: float, label: str = "", color: str | None = None) -> None:
        """Draw a full-width rectangle between low/high prices.
        
        Refactored to use ChartMarkingMixin for state tracking.
        """
        color = color or "rgba(13,110,253,0.18)"
        label = label or "Range"
        
        # Calculate time range (wide range to simulate full width)
        import time
        now = int(time.time())
        start_time = now - 365 * 24 * 3600  # 1 year back
        end_time = now + 365 * 24 * 3600    # 1 year forward
        
        # Try to use data range if available
        if self.data is not None and not self.data.empty and 'time' in self.data.columns:
            try:
                start_time = int(self.data['time'].iloc[0])
                end_time = int(self.data['time'].iloc[-1]) + 30 * 24 * 3600 # +1 month
            except Exception:
                pass

        try:
            if hasattr(self, "add_zone"):
                logger.info(
                    "add_rect_range -> add_zone (AI mixin) prices %.2f-%.2f label=%s color=%s",
                    min(high, low),
                    max(high, low),
                    label,
                    color,
                )
                # ChartAIMarkingsMixin.add_zone signature:
                # add_zone(start_time, end_time, top_price, bottom_price, fill_color, border_color, label)
                # Ensure color fallbacks are set
                fill_color = color or "rgba(13,110,253,0.18)"
                border_color = "#0d6efd"

                self.add_zone(
                    start_time,
                    end_time,
                    max(high, low),
                    min(high, low),
                    fill_color,
                    border_color,
                    label,
                )
            # Fallback: also draw via JS primitive so user sees it immediately
            if hasattr(self, "web_view") and self.web_view:
                js = (
                    "window.chartAPI && window.chartAPI.addRectRange && "
                    f"window.chartAPI.addRectRange({min(high, low)}, {max(high, low)}, '{fill_color}', '{label}');"
                )
                logger.info("add_rect_range -> JS addRectRange")
                self.web_view.page().runJavaScript(js)
            else:
                logger.warning("add_zone not available")
                
        except Exception as exc:
            logger.error("add_rect_range failed: %s", exc)

    def add_horizontal_line(self, price: float, label: str = "", color: str | None = None) -> None:
        """Draw a horizontal line at given price.
        
        Refactored to use ChartMarkingMixin for state tracking.
        """
        color = color or "#0d6efd"
        import time
        line_id = f"line_{int(price)}_{int(time.time()*1000)}"
        
        try:
            if hasattr(self, "add_line"):
                self.add_line(
                    line_id=line_id,
                    price=price,
                    color=color,
                    label=label,
                    line_style="solid",
                    show_risk=False
                )
            else:
                 logger.warning("add_line not available")
        except Exception as exc:
            logger.error("add_horizontal_line failed: %s", exc)

    def refresh_chart_colors(self) -> None:
        """Refresh chart colors and background image from QSettings (Issues #34, #35, #37, #39, #40).

        Calls JavaScript updateColors() and updateBackgroundImage() to apply without reloading HTML.
        Issue #40: Also reloads volume data with updated colors.
        Issue #39: Updates candle border radius.
        """
        try:
            from PyQt6.QtCore import QSettings
            from pathlib import Path
            from .chart_js_template import get_chart_colors_config

            settings = QSettings("OrderPilot", "TradingApp")
            colors = get_chart_colors_config()

            # Update colors and sync window._customCandleColors for rounded candles overlay
            js_code = f"""
            window._customCandleColors = {{ upColor: '{colors["upColor"]}', downColor: '{colors["downColor"]}' }};
            if (window.chartAPI && window.chartAPI.updateColors) {{
                window.chartAPI.updateColors({{
                    background: '{colors["background"]}',
                    upColor: '{colors["upColor"]}',
                    downColor: '{colors["downColor"]}',
                    wickUpColor: '{colors["wickUpColor"]}',
                    wickDownColor: '{colors["wickDownColor"]}'
                }});
            }}
            """

            # Update background image
            bg_image_path = settings.value("chart_background_image", "")
            bg_opacity = settings.value("chart_background_image_opacity", 30, type=int)

            if bg_image_path:
                # Convert Windows path to file:/// URL for WebView
                image_path = Path(bg_image_path).as_posix()
                file_url = f"file:///{image_path}"
                js_code += f"""
                if (window.chartAPI && window.chartAPI.updateBackgroundImage) {{
                    window.chartAPI.updateBackgroundImage('{file_url}', {bg_opacity});
                }}
                """
            else:
                # Remove background image
                js_code += """
                if (window.chartAPI && window.chartAPI.updateBackgroundImage) {
                    window.chartAPI.updateBackgroundImage(null, 0);
                }
                """

            # Issue #39: Update candle border radius
            border_radius = settings.value("chart_candle_border_radius", 0, type=int)
            js_code += f"""
            if (window.chartAPI && window.chartAPI.updateCandleBorderRadius) {{
                window.chartAPI.updateCandleBorderRadius({border_radius});
            }}
            """

            if hasattr(self, "web_view") and self.web_view:
                self.web_view.page().runJavaScript(js_code)
                logger.info(f"Chart colors, background, and border radius refreshed: {colors}, bg={bg_image_path}, radius={border_radius}")

                # Issue #40: Reload volume data with new colors
                self._reload_volume_with_new_colors()
            else:
                logger.warning("Cannot refresh colors: web_view not available")
        except Exception as exc:
            logger.error(f"refresh_chart_colors failed: {exc}")

    def _reload_volume_with_new_colors(self) -> None:
        """Reload volume panel with updated colors (Issue #40)."""
        try:
            # Only reload if we have data
            if not hasattr(self, 'data') or self.data is None or self.data.empty:
                logger.debug("No data available to reload volume")
                return

            # Rebuild volume data with new colors
            from .chart_mixins.data_loading_series import DataLoadingSeries
            series_helper = DataLoadingSeries(self)
            _, volume_data = series_helper.build_chart_series(self.data)

            if volume_data:
                # Remove old volume panel
                self._execute_js("window.chartAPI.removePanel('volume');")

                # Create new volume panel with updated colors
                from .chart_mixins.data_loading_series import _get_volume_colors
                vol_colors = _get_volume_colors()

                import json
                self._execute_js(
                    f"window.chartAPI.createPanel('volume', 'Volume', 'histogram', '{vol_colors['bullish']}', null, null);"
                )
                volume_json = json.dumps(volume_data)
                self._execute_js(f"window.chartAPI.setPanelData('volume', {volume_json});")

                logger.info(f"Volume panel reloaded with new colors: {vol_colors}")
        except Exception as exc:
            logger.error(f"_reload_volume_with_new_colors failed: {exc}")

    def resizeEvent(self, event):
        """Keep JS chart canvas in sync with Qt resize events (docks, chat, splitter)."""
        super().resizeEvent(event)
        try:
            # request_chart_resize is provided by EmbeddedTradingViewChartViewMixin
            self.request_chart_resize()
        except Exception as exc:
            logger.debug("resizeEvent chart resize failed: %s", exc)
