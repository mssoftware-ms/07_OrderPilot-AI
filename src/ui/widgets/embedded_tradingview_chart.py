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

from .chart_mixins import (
    ToolbarMixin,
    IndicatorMixin,
    StreamingMixin,
    DataLoadingMixin,
    ChartStateMixin,
    BotOverlayMixin,
)
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
    ChartAIMarkingsMixin,  # AI-driven markings (must be early for method override)
    ChartMarkingMixin,
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

        # Setup UI
        self._setup_ui()

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
        """Draw a full-width rectangle between low/high prices."""
        color = color or "rgba(13,110,253,0.18)"
        label_js = label.replace("'", "\\'")
        js = (
            "if (window.chartAPI && window.chartAPI.addRectRange) {"
            f" window.chartAPI.addRectRange({low}, {high}, '{color}', '{label_js}');"
            " if (window.chartAPI.setVisibleRange) {"
            "   window.chartAPI.setVisibleRange(window.chartAPI.getVisibleRange && window.chartAPI.getVisibleRange());"
            " }"
            "}"
        )
        try:
            self._execute_js(js)
        except Exception as exc:
            logger.debug("add_rect_range JS failed: %s", exc)

    def add_horizontal_line(self, price: float, label: str = "", color: str | None = None) -> None:
        """Draw a horizontal line at given price."""
        color = color or "#0d6efd"
        label_js = label.replace("'", "\\'")
        js = (
            "if (window.chartAPI && window.chartAPI.addHorizontalLine) {"
            f" window.chartAPI.addHorizontalLine({price}, '{color}', '{label_js}');"
            " if (window.chartAPI.setVisibleRange) {"
            "   window.chartAPI.setVisibleRange(window.chartAPI.getVisibleRange && window.chartAPI.getVisibleRange());"
            " }"
            "}"
        )
        try:
            self._execute_js(js)
        except Exception as exc:
            logger.debug("add_horizontal_line JS failed: %s", exc)

    def resizeEvent(self, event):
        """Keep JS chart canvas in sync with Qt resize events (docks, chat, splitter)."""
        super().resizeEvent(event)
        try:
            # request_chart_resize is provided by EmbeddedTradingViewChartViewMixin
            self.request_chart_resize()
        except Exception as exc:
            logger.debug("resizeEvent chart resize failed: %s", exc)
