"""Embedded TradingView Lightweight Charts Widget.

This module provides a fully embedded trading chart using TradingView's Lightweight Charts
library rendered directly in a Qt WebEngine view (Chromium-based).

REFACTORED: Extracted mixins to meet 600 LOC limit.
- ToolbarMixin: Toolbar creation
- IndicatorMixin: Indicator calculation and updates
- StreamingMixin: Live streaming and market events
- DataLoadingMixin: Data loading (load_data, load_symbol)
- ChartStateMixin: State management (visible range, pane layout)
"""

import logging
from collections import deque
from typing import Optional, Dict, List

import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtCore import QObject
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logging.warning("PyQt6-WebEngine not installed. Chart widget will not work.")

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
from .chart_js_template import CHART_HTML_TEMPLATE

logger = logging.getLogger(__name__)


class ChartBridge(QObject):
    """Bridge object for JavaScript to Python communication.

    Allows JavaScript in the chart to call Python methods, e.g., when
    a stop line is dragged to a new position.
    """

    # Signal emitted when a stop line is moved
    stop_line_moved = pyqtSignal(str, float)  # (line_id, new_price)

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(str, float)
    def onStopLineMoved(self, line_id: str, new_price: float):
        """Called from JavaScript when a stop line is dragged.

        Args:
            line_id: ID of the line ("initial_stop", "trailing_stop", "entry_line")
            new_price: New price level after drag
        """
        logger.info(f"[ChartBridge] Stop line moved: {line_id} -> {new_price:.2f}")
        self.stop_line_moved.emit(line_id, new_price)


class EmbeddedTradingViewChart(
    BotOverlayMixin,
    ToolbarMixin,
    IndicatorMixin,
    StreamingMixin,
    DataLoadingMixin,
    ChartStateMixin,
    QWidget
):
    """Embedded TradingView Lightweight Charts widget.

    Features:
    - Fully embedded in Qt application (no external windows)
    - Chromium-based WebEngine rendering
    - Professional TradingView appearance
    - Real-time updates
    - Technical indicators support
    """

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
        self.active_indicators: Dict[str, bool] = {}
        self.active_indicator_params: Dict[str, dict] = {}
        self.live_streaming_enabled = False

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

    def _on_market_tick_event(self, event):
        """Event bus callback - emit signal for thread-safe handling."""
        # This may be called from background thread, so emit signal
        self._tick_received.emit(event)

    def _on_market_bar_event(self, event):
        """Event bus callback - emit signal for thread-safe handling."""
        # This may be called from background thread, so emit signal
        self._bar_received.emit(event)

    @pyqtSlot(object)
    def _handle_tick_main_thread(self, event):
        """Handle tick in main thread (thread-safe)."""
        self._on_market_tick(event)

    @pyqtSlot(object)
    def _handle_bar_main_thread(self, event):
        """Handle bar in main thread (thread-safe)."""
        self._on_market_bar(event)

    def _show_error_ui(self):
        """Show error message if WebEngine not available."""
        layout = QVBoxLayout(self)
        error_label = QLabel(
            "⚠️ PyQt6-WebEngine not installed\n\n"
            "Run: pip install PyQt6-WebEngine"
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14pt;")
        layout.addWidget(error_label)

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar (from ToolbarMixin)
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Web view for chart
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_page_loaded)
        self.web_view.setHtml(CHART_HTML_TEMPLATE)
        layout.addWidget(self.web_view, stretch=1)

        # Setup WebChannel for JavaScript to Python communication
        self._chart_bridge = ChartBridge(self)
        self._chart_bridge.stop_line_moved.connect(self._on_bridge_stop_line_moved)
        self._web_channel = QWebChannel(self.web_view.page())
        self._web_channel.registerObject("pyBridge", self._chart_bridge)
        self.web_view.page().setWebChannel(self._web_channel)

        # Info panel
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Select a symbol to begin")
        self.info_label.setStyleSheet("color: #aaa; font-family: monospace; padding: 5px;")
        info_layout.addWidget(self.info_label)
        layout.addLayout(info_layout)

    def _execute_js(self, script: str):
        """Execute JavaScript in the web view, queueing until chart is ready."""
        if self.page_loaded and self.chart_initialized:
            if 'Indicator' in script or 'Panel' in script or 'createPanel' in script:
                logger.info(f"🔧 Executing JS (indicator): {script[:100]}...")
            self.web_view.page().runJavaScript(script)
        else:
            self.pending_js_commands.append(script)
            if not self.page_loaded:
                logger.warning(f"❌ Page not loaded yet, queueing JS: {script[:50]}...")
            else:
                logger.warning(f"❌ Chart not initialized yet, queueing JS: {script[:50]}...")

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

    def _flush_pending_js(self):
        """Run any JS commands that were queued before chart initialization completed."""
        if not (self.page_loaded and self.chart_initialized):
            return
        while self.pending_js_commands:
            script = self.pending_js_commands.pop(0)
            self.web_view.page().runJavaScript(script)

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

    def _on_bridge_stop_line_moved(self, line_id: str, new_price: float):
        """Handle stop line moved event from JavaScript bridge.

        Re-emits the signal so it can be caught by the chart window.
        """
        logger.info(f"Chart line moved: {line_id} -> {new_price:.4f}")
        self.stop_line_moved.emit(line_id, new_price)
