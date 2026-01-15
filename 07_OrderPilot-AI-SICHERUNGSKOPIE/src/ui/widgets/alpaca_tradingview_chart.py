"""Alpaca-only TradingView Chart Widget.

CRITICAL: This chart is ONLY for Alpaca (Stock + Crypto).
NO Bitunix code allowed here!
"""

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
    DataLoadingMixin,
    ChartStateMixin,
    BotOverlayMixin,
    LevelZonesMixin,
)
from .chart_mixins.alpaca_streaming_mixin import AlpacaStreamingMixin
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


class AlpacaTradingViewChart(
    ChartAIMarkingsMixin,  # AI-driven markings (must be early for method override)
    ChartMarkingMixin,
    LevelZonesMixin,  # Phase 5.5: Level zones support
    BotOverlayMixin,
    ToolbarMixin,
    IndicatorMixin,
    AlpacaStreamingMixin,  # ← ALPACA ONLY STREAMING
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
    """Alpaca-only TradingView Lightweight Charts widget.

    This chart is specifically designed for Alpaca data (Stock + Crypto).
    Uses AlpacaStreamingMixin with 5% bad tick filter.
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

    # Phase 5.5: Toolbar button signals
    levels_detect_requested = pyqtSignal()  # Request level detection
    level_type_toggled = pyqtSignal(str, bool)  # (level_type, checked)
    context_inspector_requested = pyqtSignal()  # Open context inspector
    context_copy_json_requested = pyqtSignal()  # Copy context as JSON
    context_copy_prompt_requested = pyqtSignal()  # Copy context as AI prompt
    context_export_file_requested = pyqtSignal()  # Export context to file
    context_refresh_requested = pyqtSignal()  # Refresh context
    # Phase 5.7: Level interaction signals
    level_target_suggested = pyqtSignal(str, float)  # (target_type, price) - for Set TP/SL

    def __init__(self, history_manager=None):
        """Initialize Alpaca chart widget.

        Args:
            history_manager: HistoryManager instance for data loading
        """
        super().__init__()

        self.history_manager = history_manager
        self.data: Optional[pd.DataFrame] = None
        self.current_symbol: Optional[str] = None
        self.current_timeframe: str = '1H'
        self.bridge = None
        self.pending_bars = deque(maxlen=100)
        self.live_streaming_enabled = False
        self.web_view = None

        # Indicator state
        self.indicator_states: Dict[str, bool] = {
            'SMA': False,
            'EMA': False,
            'RSI': False,
            'MACD': False,
            'BollingerBands': False
        }
        self.indicator_configs: Dict[str, dict] = {}
        self.indicator_engine = IndicatorEngine()
        self.cached_indicators: Dict[str, pd.Series | pd.DataFrame] = {}

        # Initialize UI components
        self._setup_ui()

        # Setup event connections
        self._setup_streaming()

        # Initialize bot overlay state
        self._bot_overlay_data = {}
        self._bot_price_line_id = None

        # Phase 5.7: Initialize level zones and click handling
        self._setup_level_zones()

        logger.info("✅ AlpacaTradingViewChart initialized (Alpaca-only)")

    def _setup_streaming(self):
        """Connect market data event bus signals to chart slots."""
        # Connect to event bus for streaming data
        event_bus.on(EventType.MARKET_DATA_TICK, self._on_market_tick)
        event_bus.on(EventType.MARKET_BAR, self._on_market_bar)
        logger.info("📡 Alpaca chart: Event bus streaming connected")

    def __del__(self):
        """Cleanup event bus connections."""
        try:
            event_bus.off(EventType.MARKET_DATA_TICK, self._on_market_tick)
            event_bus.off(EventType.MARKET_BAR, self._on_market_bar)
        except Exception:
            pass
