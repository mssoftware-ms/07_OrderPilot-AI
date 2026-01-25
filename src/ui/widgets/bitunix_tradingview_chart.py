"""Bitunix-only TradingView Chart Widget.

CRITICAL: This chart is ONLY for Bitunix.
NO Alpaca code allowed here!
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
from .chart_mixins.bitunix_streaming_mixin import BitunixStreamingMixin
from .chart_mixins.entry_analyzer_mixin import EntryAnalyzerMixin
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


class BitunixTradingViewChart(
    ChartAIMarkingsMixin,  # AI-driven markings (must be early for method override)
    ChartMarkingMixin,
    LevelZonesMixin,  # Phase 5.5: Level zones support
    EntryAnalyzerMixin,  # Phase 4: Entry Analyzer popup + regime filter
    BotOverlayMixin,
    ToolbarMixin,
    IndicatorMixin,
    BitunixStreamingMixin,  # ← BITUNIX ONLY STREAMING
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
    """Bitunix-only TradingView Lightweight Charts widget.

    This chart is specifically designed for Bitunix data.
    Uses BitunixStreamingMixin WITHOUT bad tick filter (ticks are already filtered in provider).
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
        """Initialize Bitunix chart widget.

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

        # Regime display updates (Issue #13)
        self._last_regime_hash = ""
        self._setup_regime_updates()

        # Setup event connections
        self._setup_streaming()

        # Initialize bot overlay state
        self._bot_overlay_data = {}
        self._bot_price_line_id = None

        # Phase 5.7: Initialize level zones and click handling
        self._setup_level_zones()

        logger.info("✅ BitunixTradingViewChart initialized (Bitunix-only)")

    def _setup_regime_updates(self) -> None:
        """Connect regime updates to data load and candle close events."""
        try:
            if hasattr(self, "data_loaded"):
                self.data_loaded.connect(self._update_regime_from_data)
            if hasattr(self, "candle_closed"):
                self.candle_closed.connect(self._on_candle_closed_for_regime)
        except Exception as exc:
            logger.warning(f"Failed to setup regime updates: {exc}")

    def _on_candle_closed_for_regime(
        self,
        prev_open: float,
        prev_high: float,
        prev_low: float,
        prev_close: float,
        new_open: float,
    ) -> None:
        """Update regime after a candle closes."""
        self._update_regime_from_data()

    def _get_regime_candles(self, max_bars: int = 300) -> list[dict]:
        """Build candle list from current chart data for regime detection."""
        data = getattr(self, "data", None)
        if data is None or not hasattr(data, "iterrows"):
            return []

        try:
            from src.ui.widgets.chart_mixins.data_loading_utils import (
                get_local_timezone_offset_seconds,
            )
        except Exception:
            return []

        candles = []
        local_offset = get_local_timezone_offset_seconds()
        has_time_column = "time" in data.columns

        for idx, row in data.tail(max_bars).iterrows():
            if has_time_column:
                timestamp = int(row.get("time", 0))
            else:
                timestamp = 0
                if hasattr(idx, "timestamp"):
                    timestamp = int(idx.timestamp()) + local_offset
                elif isinstance(idx, (int, float)):
                    timestamp = int(idx)

            candles.append(
                {
                    "timestamp": timestamp,
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)),
                }
            )

        return candles

    def _update_regime_from_data(self) -> None:
        """Detect and display the latest regime based on chart data."""
        try:
            candles = self._get_regime_candles()
            if not candles:
                if hasattr(self, "update_regime_badge"):
                    self.update_regime_badge("UNKNOWN")
                return

            close_hash = str(hash(tuple(c["close"] for c in candles[-5:])))
            if close_hash == self._last_regime_hash:
                return
            self._last_regime_hash = close_hash

            from src.analysis.entry_signals.entry_signal_engine import (
                OptimParams,
                calculate_features,
                detect_regime,
            )

            params = OptimParams()
            features = calculate_features(candles, params)
            regime = detect_regime(features, params)
            regime_str = regime.value if hasattr(regime, "value") else str(regime)

            if hasattr(self, "update_regime_badge"):
                self.update_regime_badge(regime_str)
        except Exception as exc:
            logger.error(f"Failed to update regime from data: {exc}", exc_info=True)
            if hasattr(self, "update_regime_badge"):
                self.update_regime_badge("UNKNOWN")

    def _setup_streaming(self):
        """Connect market data event bus signals to chart slots."""
        # Connect to event bus for streaming data
        event_bus.on(EventType.MARKET_DATA_TICK, self._on_market_tick)
        event_bus.on(EventType.MARKET_BAR, self._on_market_bar)
        logger.info("📡 Bitunix chart: Event bus streaming connected")

    def __del__(self):
        """Cleanup event bus connections."""
        try:
            event_bus.off(EventType.MARKET_DATA_TICK, self._on_market_tick)
            event_bus.off(EventType.MARKET_BAR, self._on_market_bar)
        except Exception:
            pass
