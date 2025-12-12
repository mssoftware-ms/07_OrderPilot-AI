"""Embedded TradingView Lightweight Charts Widget.

This module provides a fully embedded trading chart using TradingView's Lightweight Charts
library rendered directly in a Qt WebEngine view (Chromium-based).
"""

import json
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QPushButton,
    QToolBar,
    QMenu,
)
from PyQt6.QtGui import QAction

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logging.warning("PyQt6-WebEngine not installed. Chart widget will not work.")

from src.common.event_bus import Event, EventType, event_bus
from src.core.indicators.engine import IndicatorConfig, IndicatorEngine, IndicatorType

logger = logging.getLogger(__name__)


# HTML template for TradingView Lightweight Charts
CHART_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://unpkg.com/lightweight-charts@5.0.9/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background: #0a0a0a;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        #chart-container { width: 100vw; height: 100vh; position: relative; }
        #status { position: absolute; top: 10px; left: 10px; color: #00ff00; font-size: 12px; font-family: monospace; z-index: 1000; }
    </style>
</head>
<body>
    <div id="chart-container">
        <div id="status">Initializing chart...</div>
    </div>
    <script>
        const { createChart, CrosshairMode, LineStyle, LineSeries, HistogramSeries, CandlestickSeries } = LightweightCharts;

        function initializeChart() {
            try {
                const container = document.getElementById('chart-container');
                const scaleMargins = { top: 0.15, bottom: 0.15 };
                const chart = createChart(container, {
                    layout: {
                        background: { type: 'solid', color: '#0a0a0a' },
                        textColor: '#d1d4dc',
                        panes: { separatorColor: '#2a2a2a', separatorHoverColor: '#3a3a3a', enableResize: true },
                    },
                    grid: {
                        vertLines: { color: 'rgba(70, 70, 70, 0.35)' },
                        horzLines: { color: 'rgba(70, 70, 70, 0.35)' },
                    },
                    crosshair: { mode: CrosshairMode.Normal },
                    rightPriceScale: {
                        borderColor: '#485c7b',
                        minimumWidth: 60,
                        autoScale: true,
                        scaleMargins
                    },
                    timeScale: { timeVisible: true, secondsVisible: false, borderColor: '#485c7b' },
                    handleScroll: {
                        mouseWheel: false,             // Disable mouse wheel for scrolling, use it for zooming instead
                        pressedMouseMove: true,        // Drag to pan horizontally and vertically
                        horzTouchDrag: true,
                        vertTouchDrag: true,
                    },
                    handleScale: {
                        axisPressedMouseMove: { time: true, price: true }, // Drag axes to scale
                        mouseWheel: true,              // Mouse wheel to zoom time scale
                        pinch: true,                   // Pinch to zoom
                    },
                    autoSize: true,
                });

                const overlaySeries = {};
                const panelMap = {};          // panelId -> paneApi
                const panelMainSeries = {};   // panelId -> series
                const panelExtraSeries = {};  // panelId_key -> series

                // Price pane with higher stretch factor
                const pricePaneApi = chart.panes()[0];
                if (pricePaneApi?.setStretchFactor) pricePaneApi.setStretchFactor(4);

                const rightScale = chart.priceScale('right');

                function refitPriceScale() {
                    rightScale.applyOptions({ autoScale: true, scaleMargins });
                    chart.timeScale().fitContent();
                    setTimeout(() => {
                        rightScale.applyOptions({ autoScale: false, scaleMargins });
                    }, 0);
                }

                const priceSeries = chart.addSeries(CandlestickSeries, {
                    upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350'
                }, pricePaneApi.paneIndex());

                function addPane(panelId) {
                    if (panelMap[panelId] !== undefined) return panelMap[panelId];
                    const paneApi = chart.addPane(); // appended at bottom
                    if (paneApi.setStretchFactor) paneApi.setStretchFactor(1); // compact indicator pane
                    panelMap[panelId] = paneApi;
                    return paneApi;
                }

                function removePane(panelId) {
                    const paneApi = panelMap[panelId];
                    if (!paneApi) return false;
                    if (paneApi === pricePaneApi) return false; // never remove price pane

                    if (panelMainSeries[panelId]) {
                        chart.removeSeries(panelMainSeries[panelId]);
                        delete panelMainSeries[panelId];
                    }
                    Object.keys(panelExtraSeries).filter(k => k.startsWith(panelId + '_')).forEach(k => {
                        chart.removeSeries(panelExtraSeries[k]);
                        delete panelExtraSeries[k];
                    });

                    chart.removePane(paneApi.paneIndex());
                    delete panelMap[panelId];
                    return true;
                }

                window.chartAPI = {
                    setData: (data) => {
                        try {
                            priceSeries.setData(data);
                            refitPriceScale();
                        } catch(e){ console.error(e); }
                    },
                    updateCandle: (c) => { try { priceSeries.update(c); } catch(e){ console.error(e); } },
                    setVolumeData: () => console.warn('setVolumeData is deprecated'),
                    updateVolume: () => console.warn('updateVolume is deprecated'),

                    addIndicator: (name, color) => {
                        try {
                            const s = chart.addSeries(LineSeries, {
                                color,
                                lineWidth: 2,
                                title: name,
                                priceLineVisible: true,
                                lastValueVisible: true,
                            }, 0);
                            // Label on price scale
                            s.createPriceLine({ price: 0, color, lineWidth: 1, lineStyle: LineStyle.Dotted, axisLabelVisible: true, title: name });
                            overlaySeries[name] = s;
                            return true;
                        }
                        catch(e){ console.error(e); return false; }
                    },
                    removeIndicator: (name) => {
                        try { if (!overlaySeries[name]) return false; chart.removeSeries(overlaySeries[name]); delete overlaySeries[name]; return true; }
                        catch(e){ console.error(e); return false; }
                    },
                    setIndicatorData: (name, data) => { try { if (!overlaySeries[name]) return false; overlaySeries[name].setData(data); return true; } catch(e){ console.error(e); return false; } },
                    updateIndicator: (name, point) => { try { if (!overlaySeries[name]) return false; overlaySeries[name].update(point); return true; } catch(e){ console.error(e); return false; } },

                    createPanel: (panelId, displayName, type, color, min, max) => {
                        try {
                            console.log(`📊 createPanel called: panelId='${panelId}', exists=${panelMap[panelId] !== undefined}`);
                            if (panelMap[panelId] !== undefined) {
                                // A stale pane reference (paneIndex === -1) can remain after rapid remove/add.
                                const existingPane = panelMap[panelId];
                                const existingIndex = typeof existingPane?.paneIndex === 'function' ? existingPane.paneIndex() : -1;
                                if (existingIndex >= 0) {
                                    console.log(`  ⚠️ Panel '${panelId}' already exists at index ${existingIndex}, skipping creation`);
                                    return true;
                                }
                                console.warn(`  ⚠️ Panel '${panelId}' map entry is stale (index=${existingIndex}), recreating`);
                                delete panelMap[panelId];
                            }
                            console.log(`  ✓ Creating new panel '${panelId}'`);
                            const paneApi = addPane(panelId);
                            const paneIndex = paneApi.paneIndex();
                            console.log(`  ✓ Pane index: ${paneIndex}`);
                            let series;
                            if (type === 'histogram') {
                                series = chart.addSeries(HistogramSeries, {
                                    base: 0,
                                    color,
                                    priceScaleId: 'right',
                                    priceFormat: { type: 'price', precision: 4, minMove: 0.0001 },
                                    title: displayName,
                                }, paneIndex);
                            } else {
                                const opts = { color, lineWidth: 2, title: displayName, priceScaleId: 'right' };
                                if (min !== null && max !== null) {
                                    opts.autoscaleInfoProvider = () => ({ priceRange: { minValue: min, maxValue: max } });
                                }
                                series = chart.addSeries(LineSeries, opts, paneIndex);
                            }
                            panelMainSeries[panelId] = series;
                            return true;
                        } catch(e){ console.error(e); return false; }
                    },

                    removePanel: (panelId) => { try { return removePane(panelId); } catch(e){ console.error(e); return false; } },

                    setPanelData: (panelId, data) => { try { const s = panelMainSeries[panelId]; if (!s) return false; s.setData(data); return true; } catch(e){ console.error(e); return false; } },
                    updatePanelData: (panelId, point) => { try { const s = panelMainSeries[panelId]; if (!s) return false; s.update(point); return true; } catch(e){ console.error(e); return false; } },

                    addPanelSeries: (panelId, seriesKey, type, color, data) => {
                        try {
                            console.log(`📈 addPanelSeries called: panelId='${panelId}', seriesKey='${seriesKey}', panelExists=${panelMap[panelId] !== undefined}`);
                            // Get or create pane. If an old paneApi survives with paneIndex -1 (after removal),
                            // drop it and recreate to avoid "Index should be greater or equal to 0" assertions.
                            let paneApi = panelMap[panelId];
                            if (paneApi && (typeof paneApi.paneIndex !== 'function' || paneApi.paneIndex() < 0)) {
                                console.warn(`  ⚠️ Stale paneApi for '${panelId}' (index=${paneApi.paneIndex?.()}); recreating pane`);
                                delete panelMap[panelId];
                                paneApi = undefined;
                            }
                            paneApi = paneApi || addPane(panelId);
                            let paneIndex = paneApi.paneIndex();
                            if (paneIndex < 0) {
                                console.warn(`  ⚠️ paneIndex for '${panelId}' is ${paneIndex}, forcing fresh pane creation`);
                                paneApi = addPane(panelId);
                                paneIndex = paneApi.paneIndex();
                            }
                            console.log(`  ✓ Using pane index: ${paneIndex}`);
                            const seriesOpts = type === 'histogram'
                                ? { base: 0, color, priceScaleId: 'right', priceFormat: { type: 'price', precision: 4, minMove: 0.0001 }, title: seriesKey.toUpperCase() }
                                : { color, lineWidth: 2, title: seriesKey.toUpperCase(), priceScaleId: 'right' };
                            const s = type === 'histogram'
                                ? chart.addSeries(HistogramSeries, seriesOpts, paneIndex)
                                : chart.addSeries(LineSeries, seriesOpts, paneIndex);
                            const key = panelId + '_' + seriesKey;
                            panelExtraSeries[key] = s;
                            if (data) s.setData(data);
                            return true;
                        } catch(e){ console.error(e); return false; }
                    },

                    setPanelSeriesData: (panelId, seriesKey, data) => { try { const s = panelExtraSeries[panelId + '_' + seriesKey]; if (!s) return false; s.setData(data); return true; } catch(e){ console.error(e); return false; } },

                    addPanelPriceLine: (panelId, price, color, lineStyle, title) => {
                        try {
                            const s = panelMainSeries[panelId];
                            if (!s) return false;
                            let style = LineStyle.Dashed;
                            if (lineStyle === 'solid') style = LineStyle.Solid; else if (lineStyle === 'dotted') style = LineStyle.Dotted;
                            s.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title: title || '' });
                            return true;
                        } catch(e){ console.error(e); return false; }
                    },

                    fitContent: () => { try { refitPriceScale(); } catch(e){ console.error(e); } },
                    resetPriceScale: () => { try { refitPriceScale(); } catch(e){ console.error(e); } },

                    // Add trade markers (Entry/Exit points) to chart
                    addTradeMarkers: (markers) => {
                        try {
                            if (!Array.isArray(markers)) {
                                console.error('addTradeMarkers: markers must be an array');
                                return false;
                            }
                            priceSeries.setMarkers(markers);
                            console.log(`Added ${markers.length} trade markers to chart`);
                            return true;
                        } catch(e){
                            console.error('Error adding trade markers:', e);
                            return false;
                        }
                    },

                    // Clear all markers from chart
                    clearMarkers: () => {
                        try {
                            priceSeries.setMarkers([]);
                            return true;
                        } catch(e){
                            console.error('Error clearing markers:', e);
                            return false;
                        }
                    },

                    // Update chart with new real-time bar
                    updateBar: (bar) => {
                        try {
                            if (!bar || typeof bar !== 'object') {
                                console.error('updateBar: bar must be an object');
                                return false;
                            }
                            // TradingView Lightweight Charts: update() adds or updates the last bar
                            priceSeries.update(bar);
                            console.log(`Updated chart with real-time bar: ${new Date(bar.time * 1000).toISOString()}`);
                            return true;
                        } catch(e){
                            console.error('Error updating bar:', e);
                            return false;
                        }
                    },

                    clear: () => {
                        try {
                            priceSeries.setData([]);
                            priceSeries.setMarkers([]);  // Also clear markers
                            Object.values(overlaySeries).forEach(s => chart.removeSeries(s));
                            Object.keys(overlaySeries).forEach(k => delete overlaySeries[k]);
                            Object.keys(panelMap).forEach(pid => removePane(pid));
                        } catch(e){ console.error(e); }
                    }
                };

                document.getElementById('status').textContent = 'Ready - waiting for data...';
                console.log('Chart initialized with v5 panes');
            } catch (error) {
                console.error('CRITICAL INIT ERROR:', error);
                document.getElementById('status').textContent = 'ERROR: ' + error.message;
                document.getElementById('status').style.color = '#ff0000';
            }
        }

        setTimeout(initializeChart, 50);
    </script>
</body>
</html>
"""


class EmbeddedTradingViewChart(QWidget):
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
    data_loaded = pyqtSignal()  # Emitted when chart data is loaded
    indicator_toggled = pyqtSignal(str, bool, dict)  # (indicator_id, enabled, config)

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
        self.current_period = "1D"  # Time range to load (Intraday, 1W, 1M, etc.)
        self.current_data_provider: Optional[str] = None
        self.data: Optional[pd.DataFrame] = None
        self.volume_data: list = []  # Volume data for external dock widgets
        self.active_indicators: Dict[str, bool] = {}
        self.live_streaming_enabled = False

        # Page load state
        self.page_loaded = False
        self.chart_initialized = False  # Set to True once chartAPI is ready in JS
        self.pending_data_load: Optional[pd.DataFrame] = None
        self.pending_js_commands: List[str] = []
        self.chart_ready_timer: Optional[QTimer] = None

        # Update batching for performance
        self.pending_bars = deque(maxlen=100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_pending_updates)
        self.update_timer.setInterval(1000)  # Batch updates every 1 second

        # Indicator update lock to prevent race conditions
        self._updating_indicators = False

        # Setup UI
        self._setup_ui()

        # Subscribe to events
        event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)
        event_bus.subscribe(EventType.MARKET_TICK, self._on_market_tick)  # Legacy market ticks
        event_bus.subscribe(EventType.MARKET_DATA_TICK, self._on_market_tick)  # Alpaca/stream ticks

        logger.info("EmbeddedTradingViewChart initialized")

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

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Web view for chart
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_page_loaded)
        self.web_view.setHtml(CHART_HTML_TEMPLATE)
        layout.addWidget(self.web_view, stretch=1)

        # Info panel
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Select a symbol to begin")
        self.info_label.setStyleSheet("color: #aaa; font-family: monospace; padding: 5px;")
        info_layout.addWidget(self.info_label)
        layout.addLayout(info_layout)

    def _create_toolbar(self) -> QToolBar:
        """Create chart toolbar."""
        toolbar = QToolBar()

        # Symbol selector
        toolbar.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        # Add crypto symbols with separator
        self.symbol_combo.addItems([
            "BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD",  # Crypto
            "───────",  # Visual separator
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ"  # Stocks
        ])
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self._on_symbol_change)
        toolbar.addWidget(self.symbol_combo)

        toolbar.addSeparator()

        # Candle size selector (renamed from Zeitrahmen to Kerzen)
        toolbar.addWidget(QLabel("Kerzen:"))
        self.timeframe_combo = QComboBox()
        # Add items with display labels and internal values
        timeframes = [
            ("1 Minute", "1T"),
            ("5 Minuten", "5T"),
            ("15 Minuten", "15T"),
            ("30 Minuten", "30T"),
            ("1 Stunde", "1H"),
            ("4 Stunden", "4H"),
            ("1 Tag", "1D")
        ]
        for display, value in timeframes:
            self.timeframe_combo.addItem(display, value)

        # Set current based on internal value
        index = self.timeframe_combo.findData(self.current_timeframe)
        if index >= 0:
            self.timeframe_combo.setCurrentIndex(index)

        self.timeframe_combo.currentIndexChanged.connect(
            lambda idx: self._on_timeframe_change(self.timeframe_combo.itemData(idx))
        )
        toolbar.addWidget(self.timeframe_combo)

        toolbar.addSeparator()

        # Time period selector (how far back to load)
        toolbar.addWidget(QLabel("Zeitraum:"))
        self.period_combo = QComboBox()
        # Add time periods with display labels and lookback days
        periods = [
            ("Intraday", "1D", 1),      # Today only
            ("2 Tage", "2D", 2),        # Last 2 days
            ("5 Tage", "5D", 5),        # Last week
            ("1 Woche", "1W", 7),       # 1 week
            ("2 Wochen", "2W", 14),     # 2 weeks
            ("1 Monat", "1M", 30),      # 1 month
            ("3 Monate", "3M", 90),     # 3 months
            ("6 Monate", "6M", 180),    # 6 months
            ("1 Jahr", "1Y", 365),      # 1 year
        ]
        for display, value, days in periods:
            self.period_combo.addItem(display, value)

        # Set current based on internal value
        index = self.period_combo.findData(self.current_period)
        if index >= 0:
            self.period_combo.setCurrentIndex(index)

        self.period_combo.currentIndexChanged.connect(
            lambda idx: self._on_period_change(self.period_combo.itemData(idx))
        )
        toolbar.addWidget(self.period_combo)

        toolbar.addSeparator()

        # Indicators dropdown menu with checkboxes
        toolbar.addWidget(QLabel("Indikatoren:"))

        self.indicators_button = QPushButton("📊 Indikatoren")
        self.indicators_button.setToolTip("Wähle Indikatoren zur Anzeige")
        self.indicators_menu = QMenu(self)

        # Available indicators (matching Strategy Tab)
        self.indicator_actions = {}
        indicators = [
            ("SMA", "SMA (Simple Moving Average)", "#FFA500"),
            ("EMA", "EMA (Exponential Moving Average)", "#00FFFF"),
            ("RSI", "RSI (Relative Strength Index)", "#FF00FF"),
            ("MACD", "MACD", "#00FF00"),
            ("BB", "Bollinger Bands", "#FFFF00"),
            ("ATR", "ATR (Average True Range)", "#FF0000"),
            ("STOCH", "Stochastic Oscillator", "#0000FF"),
            ("ADX", "ADX (Average Directional Index)", "#FF6600"),
            ("CCI", "CCI (Commodity Channel Index)", "#9933FF"),
            ("MFI", "MFI (Money Flow Index)", "#33FF99"),
        ]

        for ind_id, ind_name, color in indicators:
            action = QAction(ind_name, self)
            action.setCheckable(True)
            action.setData({"id": ind_id, "color": color})
            action.triggered.connect(lambda _checked, a=action: self._on_indicator_toggled(a))
            self.indicators_menu.addAction(action)
            self.indicator_actions[ind_id] = action

        self.indicators_button.setMenu(self.indicators_menu)
        self.indicators_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #fff;
            }
            QPushButton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: right center;
            }
        """)
        toolbar.addWidget(self.indicators_button)

        toolbar.addSeparator()

        # Load data button
        self.load_button = QPushButton("📊 Load Chart")
        self.load_button.clicked.connect(self._on_load_chart)
        self.load_button.setStyleSheet("font-weight: bold; padding: 5px 15px;")
        toolbar.addWidget(self.load_button)

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._on_refresh)
        toolbar.addWidget(self.refresh_button)

        toolbar.addSeparator()

        # Live streaming toggle
        self.live_stream_button = QPushButton("🔴 Live")
        self.live_stream_button.setCheckable(True)
        self.live_stream_button.setToolTip("Toggle real-time streaming (WebSocket)")
        self.live_stream_button.clicked.connect(self._toggle_live_stream)
        self.live_stream_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #fff;
            }
        """)
        toolbar.addWidget(self.live_stream_button)

        # ===== PANEL TOGGLE BUTTON (right after Live button) =====
        self.toggle_panel_button = QPushButton("▼ Panel")
        self.toggle_panel_button.setCheckable(True)
        self.toggle_panel_button.setChecked(True)  # Panel initially visible
        self.toggle_panel_button.setToolTip("Show/Hide bottom panel (Strategy, Backtest, Optimize)")
        self.toggle_panel_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #FFA500;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #FFA500;
                color: #000;
            }
        """)
        # Signal will be emitted to parent ChartWindow
        toolbar.addWidget(self.toggle_panel_button)

        toolbar.addSeparator()

        # Market status
        self.market_status_label = QLabel("Ready")
        self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
        toolbar.addWidget(self.market_status_label)

        return toolbar

    def _execute_js(self, script: str):
        """Execute JavaScript in the web view, queueing until chart is ready."""
        if self.page_loaded and self.chart_initialized:
            # Log indicator-related JS calls
            if 'Indicator' in script or 'Panel' in script or 'createPanel' in script:
                logger.info(f"🔧 Executing JS (indicator): {script[:100]}...")
            self.web_view.page().runJavaScript(script)
        else:
            # Queue command until both page load and chart initialization are done
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

    def _on_page_loaded(self, success: bool):
        """Handle page load completion."""
        if success:
            self.page_loaded = True
            logger.info("Chart page loaded successfully")

            # Start polling until chartAPI is present inside the WebView
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

        # Ask JS if chartAPI is ready
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

        # Flush queued JS and pending data load
        self._flush_pending_js()
        if self.pending_data_load is not None:
            logger.info("Loading pending data after chart initialization")
            self.load_data(self.pending_data_load)
            self.pending_data_load = None

        # Update indicators if pending
        if hasattr(self, '_pending_indicator_update') and self._pending_indicator_update:
            logger.info("Updating pending indicators after chart initialization")
            self._pending_indicator_update = False
            self._update_indicators()

    def load_data(self, data: pd.DataFrame):
        """Load market data into chart.

        Args:
            data: OHLCV DataFrame with DatetimeIndex
        """
        # Wait for page + chart initialization before setting data
        if not (self.page_loaded and self.chart_initialized):
            logger.info("Chart not ready yet, deferring data load")
            self.pending_data_load = data
            return

        try:
            self.data = data

            # Prepare candlestick data
            candle_data = []
            volume_data = []

            for timestamp, row in data.iterrows():
                # Skip invalid data
                if any(pd.isna(x) for x in [row['open'], row['high'], row['low'], row['close']]):
                    continue

                unix_time = int(timestamp.timestamp())

                candle_data.append({
                    'time': unix_time,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                })

                volume_data.append({
                    'time': unix_time,
                    'value': float(row.get('volume', 0)),
                    'color': '#26a69a' if row['close'] >= row['open'] else '#ef5350'
                })

            # Send candlestick data to chart
            candle_json = json.dumps(candle_data)
            self._execute_js(f"window.chartAPI.setData({candle_json});")

            # Store volume data for external dock widgets
            self.volume_data = volume_data

            # Fit chart
            self._execute_js("window.chartAPI.fitContent();")

            # Update indicators (will be handled by dock widgets)
            self._update_indicators()

            # Update UI
            first_date = data.index[0].strftime('%Y-%m-%d %H:%M')
            last_date = data.index[-1].strftime('%Y-%m-%d %H:%M')
            self.info_label.setText(
                f"Loaded {len(candle_data)} bars | "
                f"From: {first_date} | To: {last_date}"
            )
            self.market_status_label.setText("✓ Chart Loaded")
            self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

            # Start update timer for real-time data
            if not self.update_timer.isActive():
                self.update_timer.start()

            logger.info(f"Loaded {len(candle_data)} bars into embedded chart")

            # Emit signal that data was loaded (for dock widgets)
            self.data_loaded.emit()

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

    def _get_indicator_configs(self):
        """Get indicator configuration dictionaries.

        Returns:
            Tuple of (overlay_configs, oscillator_configs)
        """
        overlay_configs = {
            "SMA": (IndicatorType.SMA, {'period': 20}, "SMA(20)", None, None),
            "EMA": (IndicatorType.EMA, {'period': 20}, "EMA(20)", None, None),
            "BB": (IndicatorType.BB, {'period': 20, 'std': 2}, "BB(20,2)", None, None),
        }

        oscillator_configs = {
            "RSI": (IndicatorType.RSI, {'period': 14}, "RSI(14)", 0, 100),
            "MACD": (IndicatorType.MACD, {'fast': 12, 'slow': 26, 'signal': 9}, "MACD(12,26,9)", None, None),
            "STOCH": (IndicatorType.STOCH, {'k_period': 14, 'd_period': 3}, "STOCH(14,3)", 0, 100),
            "ATR": (IndicatorType.ATR, {'period': 14}, "ATR(14)", 0, None),
            "ADX": (IndicatorType.ADX, {'period': 14}, "ADX(14)", 0, 100),
            "CCI": (IndicatorType.CCI, {'period': 20}, "CCI(20)", -100, 100),
            "MFI": (IndicatorType.MFI, {'period': 14}, "MFI(14)", 0, 100),
        }

        return overlay_configs, oscillator_configs

    def _convert_macd_data_to_chart_format(self, result):
        """Convert MACD indicator result to chart format.

        Args:
            result: IndicatorResult with DataFrame values

        Returns:
            Dict with 'macd', 'signal', 'histogram' keys
        """
        col_names = result.values.columns.tolist()
        logger.info(f"MACD columns: {col_names}")

        # Find columns (check histogram and signal first to avoid false matches)
        macd_col = signal_col = hist_col = None
        for col in col_names:
            col_lower = col.lower()
            if 'macdh' in col_lower or 'hist' in col_lower:
                hist_col = col
            elif 'macds' in col_lower or 'signal' in col_lower:
                signal_col = col
            elif 'macd' in col_lower:
                macd_col = col

        macd_series = result.values[macd_col] if macd_col else None
        signal_series = result.values[signal_col] if signal_col else None
        hist_series = result.values[hist_col] if hist_col else None

        logger.info(f"MACD column mapping: macd={macd_col}, signal={signal_col}, hist={hist_col}")

        # Convert each series to chart format
        macd_data = [
            {'time': int(ts.timestamp()), 'value': float(val)}
            for ts, val in zip(self.data.index, macd_series.values if macd_series is not None else [])
            if not pd.isna(val)
        ]

        signal_data = [
            {'time': int(ts.timestamp()), 'value': float(val)}
            for ts, val in zip(self.data.index, signal_series.values if signal_series is not None else [])
            if not pd.isna(val)
        ]

        hist_data = [
            {
                'time': int(ts.timestamp()),
                'value': float(val),
                'color': '#26a69a' if float(val) >= 0 else '#ef5350'
            }
            for ts, val in zip(self.data.index, hist_series.values if hist_series is not None else [])
            if not pd.isna(val)
        ]

        logger.info(f"MACD data prepared: macd={len(macd_data)} points, signal={len(signal_data)} points, histogram={len(hist_data)} points")

        return {
            'macd': macd_data,
            'signal': signal_data,
            'histogram': hist_data
        }

    def _convert_multi_series_data_to_chart_format(self, result, ind_id):
        """Convert multi-series indicator result to chart format.

        Args:
            result: IndicatorResult with DataFrame values
            ind_id: Indicator ID string

        Returns:
            List of time/value dicts
        """
        col_names = result.values.columns.tolist()

        # Determine which column to use
        if 'k' in col_names:
            main_col = 'k'
        elif any('STOCHk' in col for col in col_names):
            main_col = [col for col in col_names if 'STOCHk' in col][0]
        elif 'middle' in col_names:  # Bollinger Bands
            main_col = 'middle'
        elif any('BBM' in col for col in col_names):  # pandas_ta BB middle
            main_col = [col for col in col_names if 'BBM' in col][0]
        else:
            main_col = col_names[0]  # Fallback to first column

        series_data = result.values[main_col]
        logger.info(f"Using column '{main_col}' from multi-series indicator {ind_id}")

        return [
            {'time': int(ts.timestamp()), 'value': float(val)}
            for ts, val in zip(self.data.index, series_data.values)
            if not pd.isna(val)
        ]

    def _convert_single_series_data_to_chart_format(self, result):
        """Convert single-series indicator result to chart format.

        Args:
            result: IndicatorResult with Series values

        Returns:
            List of time/value dicts
        """
        return [
            {'time': int(ts.timestamp()), 'value': float(val)}
            for ts, val in zip(self.data.index, result.values.values)
            if not pd.isna(val)
        ]

    def _create_overlay_indicator(self, display_name, color):
        """Create overlay indicator on price chart.

        Args:
            display_name: Display name for the indicator
            color: Color string for the indicator
        """
        self._execute_js(f"window.chartAPI.addIndicator('{display_name}', '{color}');")

    def _create_oscillator_panel(self, ind_id, display_name, color, min_val, max_val):
        """Create oscillator panel with indicator-specific reference lines.

        Args:
            ind_id: Indicator ID string
            display_name: Display name for the panel
            color: Color string for the indicator
            min_val: Minimum value for y-axis (or None)
            max_val: Maximum value for y-axis (or None)
        """
        panel_id = ind_id.lower()

        # DON'T remove existing panels - causes pane index shifting issues
        # Just create if not exists, JavaScript will check if it already exists

        if ind_id == "MACD":
            # MACD: Create panel with histogram
            logger.info(f"  📊 Creating MACD panel with ID '{panel_id}'")
            self._execute_js(
                f"window.chartAPI.createPanel('{panel_id}', '{display_name}', 'histogram', '#26a69a', null, null);"
            )
            self._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'macd', 'line', '#2962FF', null);")
            self._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'signal', 'line', '#FF6D00', null);")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'solid', '0');")
            logger.info(f"  ✓ MACD panel JavaScript calls completed")
        else:
            # Other oscillators
            js_min = 'null' if min_val is None else str(min_val)
            js_max = 'null' if max_val is None else str(max_val)
            self._execute_js(
                f"window.chartAPI.createPanel('{panel_id}', '{display_name}', 'line', '{color}', {js_min}, {js_max});"
            )
            self._add_oscillator_reference_lines(ind_id, panel_id)

        logger.info(f"Created panel for {ind_id}")

    def _add_oscillator_reference_lines(self, ind_id, panel_id):
        """Add indicator-specific reference lines to oscillator panel.

        Args:
            ind_id: Indicator ID string
            panel_id: Panel ID string
        """
        if ind_id == "RSI":
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 30, '#FF0000', 'dashed', 'Oversold');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 70, '#00FF00', 'dashed', 'Overbought');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 50, '#888888', 'dotted', 'Neutral');")
        elif ind_id == "STOCH":
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 20, '#FF0000', 'dashed', 'Oversold');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 80, '#00FF00', 'dashed', 'Overbought');")
        elif ind_id == "CCI":
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', -100, '#FF0000', 'dashed', '-100');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 100, '#00FF00', 'dashed', '+100');")
            self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'dotted', '0');")

    def _update_overlay_data(self, display_name, ind_data):
        """Update overlay indicator data on price chart.

        Args:
            display_name: Display name of the indicator
            ind_data: List of time/value dicts
        """
        ind_json = json.dumps(ind_data)
        self._execute_js(f"window.chartAPI.setIndicatorData('{display_name}', {ind_json});")

    def _update_oscillator_data(self, ind_id, ind_data):
        """Update oscillator panel data.

        Args:
            ind_id: Indicator ID string
            ind_data: Either list of time/value dicts or dict with multiple series
        """
        panel_id = ind_id.lower()

        if isinstance(ind_data, dict) and ind_id == "MACD":
            # MACD: Set data for all 3 series
            macd_json = json.dumps(ind_data['macd'])
            signal_json = json.dumps(ind_data['signal'])
            hist_json = json.dumps(ind_data['histogram'])

            logger.info(f"  📈 Setting MACD data: histogram={len(ind_data['histogram'])} points, macd={len(ind_data['macd'])} points, signal={len(ind_data['signal'])} points")
            self._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {hist_json});")
            self._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'macd', {macd_json});")
            self._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'signal', {signal_json});")
            logger.info(f"  ✓ MACD data set complete")
        else:
            # Regular oscillator - single series
            ind_json = json.dumps(ind_data)
            self._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {ind_json});")

    def _remove_indicator_from_chart(self, ind_id, display_name, is_overlay):
        """Remove indicator from chart.

        Args:
            ind_id: Indicator ID string
            display_name: Display name of the indicator
            is_overlay: True if overlay indicator, False if oscillator
        """
        if is_overlay:
            self._execute_js(f"window.chartAPI.removeIndicator('{display_name}');")
        else:
            panel_id = ind_id.lower()
            self._execute_js(f"window.chartAPI.removePanel('{panel_id}');")
            logger.info(f"Removed panel for {ind_id}")

    def _update_indicators(self):
        """Update technical indicators on chart."""
        logger.info("🔧 _update_indicators called")

        if self.data is None:
            logger.warning("❌ Cannot update indicators: chart data not loaded yet")
            return

        if not (self.page_loaded and self.chart_initialized):
            logger.warning("❌ Cannot update indicators: chart not fully initialized yet (page_loaded=%s, chart_initialized=%s)",
                          self.page_loaded, self.chart_initialized)
            # Mark that we need to update indicators once chart is ready
            self._pending_indicator_update = True
            return

        # Prevent concurrent execution with real-time updates
        if self._updating_indicators:
            logger.warning("⏸️ Indicator update already in progress, skipping...")
            return

        logger.info("✓ Chart ready, processing indicators...")

        try:
            self._updating_indicators = True
            overlay_configs, oscillator_configs = self._get_indicator_configs()

            # Process each indicator
            for ind_id, action in self.indicator_actions.items():
                is_checked = action.isChecked()
                if is_checked:
                    logger.info(f"  → Processing checked indicator: {ind_id}")
                indicator_data = action.data()
                color = indicator_data["color"]

                # Determine if overlay or oscillator
                is_overlay = ind_id in overlay_configs
                is_oscillator = ind_id in oscillator_configs

                # Skip if not implemented
                if not is_overlay and not is_oscillator:
                    if is_checked and ind_id not in self.active_indicators:
                        logger.warning(f"Indicator {ind_id} not yet implemented")
                    continue

                # Get configuration
                if is_overlay:
                    ind_type, params, display_name, _, _ = overlay_configs[ind_id]
                else:
                    ind_type, params, display_name, min_val, max_val = oscillator_configs[ind_id]

                if is_checked:
                    try:
                        # Calculate indicator
                        logger.info(f"  → Calculating {ind_id} with params: {params}")
                        config = IndicatorConfig(indicator_type=ind_type, params=params)
                        result = self.indicator_engine.calculate(self.data, config)
                        logger.info(f"  ✓ Calculated {ind_id}, values shape: {result.values.shape if hasattr(result.values, 'shape') else len(result.values)}")

                        # Convert to chart format based on data type
                        if isinstance(result.values, pd.DataFrame) and ind_id == "MACD":
                            ind_data = self._convert_macd_data_to_chart_format(result)
                        elif isinstance(result.values, pd.DataFrame):
                            ind_data = self._convert_multi_series_data_to_chart_format(result, ind_id)
                        else:
                            ind_data = self._convert_single_series_data_to_chart_format(result)
                        logger.info(f"  ✓ Converted {ind_id} to chart format, {len(ind_data)} data points")

                        # Create indicator/panel if not exists, or recreate if needed
                        should_create = ind_id not in self.active_indicators

                        if should_create:
                            logger.info(f"  → Creating new {'overlay' if is_overlay else 'panel'} for {ind_id}")
                            if is_overlay:
                                self._create_overlay_indicator(display_name, color)
                            else:
                                self._create_oscillator_panel(ind_id, display_name, color, min_val, max_val)
                            self.active_indicators[ind_id] = True
                            logger.info(f"  ✓ Created and activated {ind_id}")
                        else:
                            logger.info(f"  → {ind_id} already exists, updating data only")

                        # Update data
                        if is_overlay:
                            self._update_overlay_data(display_name, ind_data)
                        else:
                            self._update_oscillator_data(ind_id, ind_data)
                        logger.info(f"  ✓ Updated data for {ind_id}")

                    except Exception as ind_error:
                        logger.error(f"  ❌ Error processing indicator {ind_id}: {ind_error}", exc_info=True)

                elif ind_id in self.active_indicators:
                    # Remove indicator if unchecked - FIXED: This elif must be at same level as if is_checked!
                    logger.info(f"  → Removing {ind_id} from chart (is_overlay={is_overlay})")
                    self._remove_indicator_from_chart(ind_id, display_name, is_overlay)
                    del self.active_indicators[ind_id]
                    logger.info(f"  ✓ Removed {ind_id} from active indicators. Remaining: {list(self.active_indicators.keys())}")

        except Exception as e:
            logger.error(f"Error updating indicators: {e}", exc_info=True)
        finally:
            self._updating_indicators = False

    def _update_indicators_realtime(self, candle: dict):
        """Update indicators in real-time with new candle data.

        Args:
            candle: New candle dict with time, open, high, low, close
        """
        if self.data is None or not self.active_indicators:
            return  # No data or no active indicators

        if not (self.page_loaded and self.chart_initialized):
            return  # Chart not ready

        # Skip if full indicator update is running
        if self._updating_indicators:
            return

        try:
            # Update the last row of the DataFrame with new candle data
            # Create a new row from the candle
            new_row = pd.DataFrame([{
                'time': pd.Timestamp.fromtimestamp(candle['time'], tz='UTC'),
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close']
            }])
            new_row.set_index('time', inplace=True)

            # Check if this timestamp already exists (update) or is new (append)
            if new_row.index[0] in self.data.index:
                # Update existing row
                self.data.loc[new_row.index[0]] = new_row.iloc[0]
            else:
                # Append new row
                self.data = pd.concat([self.data, new_row])

            # Get indicator configs
            overlay_configs, oscillator_configs = self._get_indicator_configs()

            # Update each active indicator
            for ind_id in self.active_indicators:
                # Determine if overlay or oscillator
                is_overlay = ind_id in overlay_configs
                is_oscillator = ind_id in oscillator_configs

                if not is_overlay and not is_oscillator:
                    continue

                # Get configuration
                if is_overlay:
                    ind_type, params, display_name, _, _ = overlay_configs[ind_id]
                else:
                    ind_type, params, display_name, min_val, max_val = oscillator_configs[ind_id]

                # Recalculate indicator
                config = IndicatorConfig(indicator_type=ind_type, params=params)
                result = self.indicator_engine.calculate(self.data, config)

                # Get the last value(s)
                if isinstance(result.values, pd.DataFrame):
                    # Multi-series indicator (MACD, Stoch)
                    if ind_id == "MACD":
                        last_idx = result.values.index[-1]
                        hist_val = float(result.values.loc[last_idx, 'MACDh_12_26_9'])
                        time_unix = int(last_idx.timestamp())

                        # Update only the MACD histogram for real-time
                        # (MACD and Signal lines are too slow for tick-by-tick updates)
                        panel_id = ind_id.lower()
                        hist_point = json.dumps({'time': time_unix, 'value': hist_val})
                        self._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {hist_point});")
                    else:
                        # Other multi-series indicators (Stoch, etc.)
                        last_idx = result.values.index[-1]
                        time_unix = int(last_idx.timestamp())

                        # Use first column as main value
                        main_val = float(result.values.iloc[-1, 0])
                        point = json.dumps({'time': time_unix, 'value': main_val})

                        if is_overlay:
                            self._execute_js(f"window.chartAPI.updateIndicator('{display_name}', {point});")
                        else:
                            panel_id = ind_id.lower()
                            self._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {point});")
                else:
                    # Single-series indicator (RSI, EMA, SMA, etc.)
                    last_idx = result.values.index[-1]
                    value = float(result.values.iloc[-1])
                    time_unix = int(last_idx.timestamp())

                    point = json.dumps({'time': time_unix, 'value': value})

                    if is_overlay:
                        self._execute_js(f"window.chartAPI.updateIndicator('{display_name}', {point});")
                    else:
                        panel_id = ind_id.lower()
                        self._execute_js(f"window.chartAPI.updatePanelData('{panel_id}', {point});")

        except Exception as e:
            logger.error(f"Error updating indicators in real-time: {e}", exc_info=True)

    def _update_indicators_button_badge(self):
        """Update indicators button to show count of active indicators."""
        active_count = sum(1 for action in self.indicator_actions.values() if action.isChecked())

        if active_count > 0:
            self.indicators_button.setText(f"📊 Indikatoren ({active_count})")
            self.indicators_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B00;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #FF8C00;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #FF8C00;
                }
                QPushButton::menu-indicator {
                    subcontrol-origin: padding;
                    subcontrol-position: right center;
                }
            """)
        else:
            self.indicators_button.setText("📊 Indikatoren")
            self.indicators_button.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #aaa;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    color: #fff;
                }
                QPushButton::menu-indicator {
                    subcontrol-origin: padding;
                    subcontrol-position: right center;
                }
            """)

    def _on_indicator_toggled(self, action: QAction):
        """Handle indicator toggle from dropdown menu.

        Args:
            action: The QAction that was toggled
        """
        indicator_data = action.data()
        indicator_id = indicator_data["id"]
        is_checked = action.isChecked()

        logger.info(f"🔄 Indicator {indicator_id} {'enabled' if is_checked else 'disabled'} (currently active: {list(self.active_indicators.keys())})")

        # Update indicators display
        self._update_indicators()

        # Update button style to show how many indicators are active
        self._update_indicators_button_badge()

        logger.info(f"✓ Toggle complete. Active indicators: {list(self.active_indicators.keys())}")

    @pyqtSlot(object)
    def _on_market_bar(self, event: Event):
        """Handle market bar event."""
        try:
            bar_data = event.data
            if bar_data.get('symbol') != self.current_symbol:
                return

            # Add to pending updates (batched processing)
            self.pending_bars.append(bar_data)

        except Exception as e:
            logger.error(f"Error handling market bar: {e}")

    @pyqtSlot(object)
    def _on_market_tick(self, event: Event):
        """Handle market tick event - update current candle in real-time."""
        try:
            tick_data = event.data
            if tick_data.get('symbol') != self.current_symbol:
                return

            # Update price in info label
            price = tick_data.get('price', 0)
            volume = tick_data.get('volume', tick_data.get('size', 0))

            if not price:
                logger.warning(f"Received tick for {self.current_symbol} but no price data")
                return

            self.info_label.setText(f"Last: ${price:.2f}")
            logger.info(f"📊 Live tick: {self.current_symbol} @ ${price:.2f}")

            # --- Time Handling Fix ---
            # Use timestamp from event, NOT system time
            ts = tick_data.get('timestamp')
            if ts is None:
                ts = event.timestamp

            if ts is None:
                ts = datetime.now(timezone.utc)

            # Ensure ts is datetime and UTC
            if isinstance(ts, str):
                try:
                    ts = pd.to_datetime(ts).to_pydatetime()
                except Exception:
                    ts = datetime.now(timezone.utc)
            elif isinstance(ts, (int, float)):
                ts = datetime.fromtimestamp(ts, tz=timezone.utc)

            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            current_tick_time = int(ts.timestamp())
            current_minute_start = current_tick_time - (current_tick_time % 60)

            # DEBUG LOGGING
            logger.info(f"LIVE TICK DEBUG: Raw TS: {tick_data.get('timestamp')} | Resolved TS: {ts} | TickUnix: {current_tick_time} | MinStart: {current_minute_start}")

            # Update current candle in real-time (Stock3 style)
            if not hasattr(self, '_current_candle_time'):
                # Initialize with current minute boundary from DATA
                self._current_candle_time = current_minute_start
                self._current_candle_open = price
                self._current_candle_high = price
                self._current_candle_low = price
                self._current_candle_volume = 0

            # Check if we need a new candle (new minute)
            if current_minute_start > self._current_candle_time:
                # New candle - reset
                self._current_candle_time = current_minute_start
                self._current_candle_open = price
                self._current_candle_high = price
                self._current_candle_low = price
                self._current_candle_volume = 0
            else:
                # Same candle - update high/low
                self._current_candle_high = max(self._current_candle_high, price)
                self._current_candle_low = min(self._current_candle_low, price)

            # Accumulate volume
            if volume:
                self._current_candle_volume += volume

            # Create candle update
            candle = {
                'time': self._current_candle_time,
                'open': float(self._current_candle_open),
                'high': float(self._current_candle_high),
                'low': float(self._current_candle_low),
                'close': float(price),
            }

            volume_bar = {
                'time': self._current_candle_time,
                'value': float(self._current_candle_volume),
                'color': '#26a69a' if price >= self._current_candle_open else '#ef5350'
            }

            # Update chart immediately (like Stock3!)
            candle_json = json.dumps(candle)
            volume_json = json.dumps(volume_bar)

            self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
            self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

            # ✅ FIX: Update indicators in real-time
            self._update_indicators_realtime(candle)

        except Exception as e:
            logger.error(f"Error handling market tick: {e}", exc_info=True)

    def _process_pending_updates(self):
        """Process pending bar updates (batched for performance)."""
        if not self.pending_bars:
            return

        try:
            # Process all pending bars
            while self.pending_bars:
                bar_data = self.pending_bars.popleft()

                ts_raw = bar_data.get('timestamp', datetime.now())
                # Robust parsing: handle str/np datetime/pandas Timestamp
                try:
                    if isinstance(ts_raw, str):
                        ts_parsed = pd.to_datetime(ts_raw)
                        ts_value = ts_parsed.to_pydatetime() if hasattr(ts_parsed, "to_pydatetime") else datetime.now()
                    elif hasattr(ts_raw, "to_pydatetime"):
                        ts_value = ts_raw.to_pydatetime()
                    else:
                        ts_value = ts_raw
                    unix_time = int(pd.Timestamp(ts_value).timestamp())
                except Exception:
                    unix_time = int(datetime.now().timestamp())

                candle = {
                    'time': unix_time,
                    'open': float(bar_data.get('open', 0)),
                    'high': float(bar_data.get('high', 0)),
                    'low': float(bar_data.get('low', 0)),
                    'close': float(bar_data.get('close', 0)),
                }

                volume = {
                    'time': unix_time,
                    'value': float(bar_data.get('volume', 0)),
                    'color': '#26a69a' if candle['close'] >= candle['open'] else '#ef5350'
                }

                # Update chart
                candle_json = json.dumps(candle)
                volume_json = json.dumps(volume)

                self._execute_js(f"window.chartAPI.updateCandle({candle_json});")
                self._execute_js(f"window.chartAPI.updatePanelData('volume', {volume_json});")

        except Exception as e:
            logger.error(f"Error processing updates: {e}", exc_info=True)

    def _on_symbol_change(self, symbol: str):
        """Handle symbol change."""
        # Ignore separator line
        if symbol == "───────" or not symbol.strip():
            # Revert to previous symbol
            self.symbol_combo.setCurrentText(self.current_symbol)
            return

        self.current_symbol = symbol
        self.symbol_changed.emit(symbol)
        logger.info(f"Symbol changed to: {symbol}")

    def _on_timeframe_change(self, timeframe: str):
        """Handle timeframe (candle size) change."""
        self.current_timeframe = timeframe
        self.timeframe_changed.emit(timeframe)
        logger.info(f"Candle size changed to: {timeframe}")

    def _on_period_change(self, period: str):
        """Handle time period change."""
        self.current_period = period
        logger.info(f"Time period changed to: {period}")

    def _on_load_chart(self):
        """Load chart data for current symbol."""
        import asyncio

        # Get or create event loop compatible with Qt
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Try qasync loop if available
            try:
                from qasync import QEventLoop
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    loop = QEventLoop(app)
                    asyncio.set_event_loop(loop)
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except ImportError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        # Create and schedule the task
        asyncio.create_task(self.load_symbol(self.current_symbol, self.current_data_provider))

    def _on_refresh(self):
        """Refresh current chart."""
        if self.data is not None:
            self.load_data(self.data)
        else:
            self._on_load_chart()

    def _toggle_live_stream(self):
        """Toggle live streaming on/off."""
        import asyncio

        # Get current button state
        is_checked = self.live_stream_button.isChecked()

        logger.info(f"🔄 Live stream toggle clicked: button_checked={is_checked}, current_enabled={self.live_streaming_enabled}")

        # Update enabled flag
        self.live_streaming_enabled = is_checked

        if self.live_streaming_enabled:
            # Start live stream
            logger.info(f"Starting live stream for {self.current_symbol}...")

            # Get or create event loop compatible with Qt
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Try qasync loop if available
                try:
                    from qasync import QEventLoop
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        loop = QEventLoop(app)
                        asyncio.set_event_loop(loop)
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except ImportError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

            asyncio.create_task(self._start_live_stream())

            # Update button style
            self.live_stream_button.setStyleSheet("""
                QPushButton {
                    background-color: #00FF00;
                    color: black;
                    border: 2px solid #00AA00;
                    border-radius: 3px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #00CC00;
                }
            """)
            self.live_stream_button.setText("🟢 Live")
            self.market_status_label.setText("🔴 Streaming...")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")

        else:
            # Stop live stream
            logger.info("Stopping live stream...")

            # Get or create event loop compatible with Qt
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Try qasync loop if available
                try:
                    from qasync import QEventLoop
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        loop = QEventLoop(app)
                        asyncio.set_event_loop(loop)
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except ImportError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

            asyncio.create_task(self._stop_live_stream())

            # Reset button style
            self.live_stream_button.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #aaa;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    color: #fff;
                }
            """)
            self.live_stream_button.setText("🔴 Live")
            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")

    async def _start_live_stream(self):
        """Start live streaming for current symbol."""
        if not self.history_manager:
            logger.warning("No history manager available")
            self.market_status_label.setText("⚠ No data source")
            return

        if not self.current_symbol:
            logger.warning("No symbol selected")
            self.market_status_label.setText("⚠ No symbol")
            return

        try:
            # Detect if crypto symbol (contains "/" like BTC/USD)
            is_crypto = "/" in self.current_symbol

            # Start appropriate real-time stream via HistoryManager
            if is_crypto:
                success = await self.history_manager.start_crypto_realtime_stream([self.current_symbol])
                logger.info(f"✓ Live crypto stream started for {self.current_symbol}")
            else:
                success = await self.history_manager.start_realtime_stream([self.current_symbol])
                logger.info(f"✓ Live stock stream started for {self.current_symbol}")

            if success:
                asset_type = "Crypto" if is_crypto else "Stock"
                self.market_status_label.setText(f"🟢 Live ({asset_type}): {self.current_symbol}")
                self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")
            else:
                logger.error("Failed to start live stream")
                self.market_status_label.setText("⚠ Stream failed")
                self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
                # Uncheck button
                self.live_stream_button.setChecked(False)
                self._toggle_live_stream()

        except Exception as e:
            logger.error(f"Error starting live stream: {e}")
            self.market_status_label.setText(f"⚠ Error: {str(e)[:20]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
            # Uncheck button
            self.live_stream_button.setChecked(False)
            self._toggle_live_stream()

    async def _stop_live_stream(self):
        """Stop live streaming for this symbol."""
        if not self.history_manager or not self.current_symbol:
            return

        try:
            # Unsubscribe only this symbol (don't stop entire stream)
            is_crypto = "/" in self.current_symbol

            if is_crypto:
                # Unsubscribe from crypto stream
                if hasattr(self.history_manager, 'crypto_stream_client') and self.history_manager.crypto_stream_client:
                    await self.history_manager.crypto_stream_client.unsubscribe([self.current_symbol])
                    logger.info(f"✓ Unsubscribed {self.current_symbol} from crypto stream")
            else:
                # Unsubscribe from stock stream
                if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                    await self.history_manager.stream_client.unsubscribe([self.current_symbol])
                    logger.info(f"✓ Unsubscribed {self.current_symbol} from stock stream")

            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")

        except Exception as e:
            logger.error(f"Error unsubscribing {self.current_symbol} from stream: {e}")

    async def refresh_data(self):
        """Public method to refresh chart data (called by main app)."""
        if self.current_symbol:
            await self.load_symbol(self.current_symbol, self.current_data_provider)
        else:
            logger.warning("No symbol loaded to refresh")

    async def load_symbol(self, symbol: str, data_provider: Optional[str] = None):
        """Load symbol data and display chart.

        Args:
            symbol: Trading symbol
            data_provider: Data provider (alpaca, yahoo, etc.)
        """
        try:
            if not self.history_manager:
                logger.warning("No history manager available")
                self.market_status_label.setText("⚠ No data source")
                return

            self.current_symbol = symbol
            self.current_data_provider = data_provider
            self.symbol_combo.setCurrentText(symbol)

            self.market_status_label.setText(f"Loading {symbol}...")
            self.market_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")

            # Import required classes
            from datetime import timedelta, datetime
            import pytz
            from src.core.market_data.history_provider import DataRequest, DataSource, Timeframe
            from src.core.market_data.types import AssetClass

            # Detect asset class from symbol
            # Crypto symbols contain "/" (e.g., BTC/USD, ETH/USD)
            # Stock symbols don't (e.g., AAPL, MSFT)
            asset_class = AssetClass.CRYPTO if "/" in symbol else AssetClass.STOCK

            # Map timeframe
            timeframe_map = {
                "1T": Timeframe.MINUTE_1,
                "5T": Timeframe.MINUTE_5,
                "15T": Timeframe.MINUTE_15,
                "30T": Timeframe.MINUTE_30,
                "1H": Timeframe.HOUR_1,
                "4H": Timeframe.HOUR_4,
                "1D": Timeframe.DAY_1,
            }
            timeframe = timeframe_map.get(self.current_timeframe, Timeframe.MINUTE_1)

            # Map provider (single Alpaca option auto-selects crypto vs stocks)
            provider_source = None
            if data_provider:
                if data_provider == "alpaca":
                    provider_source = (
                        DataSource.ALPACA_CRYPTO
                        if asset_class == AssetClass.CRYPTO
                        else DataSource.ALPACA
                    )
                else:
                    provider_map = {
                        "database": DataSource.DATABASE,
                        "yahoo": DataSource.YAHOO,
                        "alpha_vantage": DataSource.ALPHA_VANTAGE,
                        "ibkr": DataSource.IBKR,
                        "finnhub": DataSource.FINNHUB,
                    }
                    provider_source = provider_map.get(data_provider)
            else:
                # Default: Use appropriate Alpaca provider based on asset class
                if asset_class == AssetClass.CRYPTO:
                    provider_source = DataSource.ALPACA_CRYPTO
                    logger.info("No provider specified, using Alpaca Crypto for live data")
                else:
                    provider_source = DataSource.ALPACA
                    logger.info("No provider specified, using Alpaca for live data")

            # Determine lookback period based on selected time period
            period_to_days = {
                "1D": 1,      # Intraday (today)
                "2D": 2,      # 2 days
                "5D": 5,      # 5 days
                "1W": 7,      # 1 week
                "2W": 14,     # 2 weeks
                "1M": 30,     # 1 month
                "3M": 90,     # 3 months
                "6M": 180,    # 6 months
                "1Y": 365,    # 1 year
            }
            lookback_days = period_to_days.get(self.current_period, 30)  # Default: 1 month

            # --- Timezone-aware date calculation ---
            ny_tz = pytz.timezone('America/New_York')
            now_ny = datetime.now(ny_tz)
            end_date = now_ny

            # CRITICAL: Crypto trades 24/7, stocks have market hours
            use_previous_trading_day = False

            if asset_class == AssetClass.CRYPTO:
                # Crypto: Always use current time, no market hours restrictions
                start_date = end_date - timedelta(days=lookback_days)
                logger.info(f"Crypto asset: Using current time (24/7 trading)")
            else:
                # Stocks: Apply market hours logic
                # Market hours: 9:30 AM - 4:00 PM EST
                market_open_hour = 9
                market_open_minute = 30

                # Adjust end_date for weekends AND pre-market hours
                weekday = end_date.weekday()  # Monday=0, Sunday=6
                current_hour = end_date.hour
                current_minute = end_date.minute
                is_before_market_open = (current_hour < market_open_hour or
                                        (current_hour == market_open_hour and current_minute < market_open_minute))

                if weekday == 5:  # Saturday
                    end_date = end_date - timedelta(days=1)
                    use_previous_trading_day = True
                    logger.info("Weekend detected (Saturday), using Friday's data")
                elif weekday == 6:  # Sunday
                    end_date = end_date - timedelta(days=2)
                    use_previous_trading_day = True
                    logger.info("Weekend detected (Sunday), using Friday's data")
                elif weekday == 0 and is_before_market_open:  # Monday before market open
                    end_date = end_date - timedelta(days=3)  # Go back to Friday
                    use_previous_trading_day = True
                    logger.info(f"Monday pre-market ({current_hour:02d}:{current_minute:02d} EST), using Friday's data")
                elif weekday < 5 and is_before_market_open:  # Tuesday-Friday before market open
                    end_date = end_date - timedelta(days=1)  # Go back to previous day
                    use_previous_trading_day = True
                    logger.info(f"Pre-market hours ({current_hour:02d}:{current_minute:02d} EST), using previous trading day")

                # For intraday during non-trading periods, fetch the entire last trading day
                if self.current_period == "1D" and use_previous_trading_day:
                    # Set a specific window for the last trading day in New York time
                    last_trading_day = end_date.date()
                    start_date = ny_tz.localize(datetime.combine(last_trading_day, datetime.min.time())).replace(hour=4, minute=0)
                    end_date = ny_tz.localize(datetime.combine(last_trading_day, datetime.max.time())).replace(hour=20, minute=0)
                    logger.info(f"Intraday non-trading period: fetching data for {last_trading_day} (4:00 - 20:00 EST)")
                else:
                    # Standard lookback calculation
                    start_date = end_date - timedelta(days=lookback_days)

            logger.info(f"Loading {symbol} - Candles: {self.current_timeframe}, Period: {self.current_period} ({lookback_days} days)")
            logger.info(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')} to {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")


            # Fetch data
            request = DataRequest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                asset_class=asset_class,  # Important: Set asset class for proper routing
                source=provider_source
            )

            # CRITICAL DEBUG: Log the actual date range being requested
            logger.info(f"📅 Requesting data: {symbol}")
            logger.info(f"   Start: {start_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"   End:   {end_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"   Asset: {asset_class.value}, Source: {provider_source.value if provider_source else 'auto'}")

            bars, source_used = await self.history_manager.fetch_data(request)

            # Log fetched data range
            if bars:
                first_bar = bars[0].timestamp
                last_bar = bars[-1].timestamp
                logger.info(f"📊 Fetched {len(bars)} bars from {source_used}")
                logger.info(f"   First bar: {first_bar.strftime('%Y-%m-%d %H:%M:%S') if hasattr(first_bar, 'strftime') else first_bar}")
                logger.info(f"   Last bar:  {last_bar.strftime('%Y-%m-%d %H:%M:%S') if hasattr(last_bar, 'strftime') else last_bar}")

            if not bars:
                logger.warning(f"No data for {symbol}")
                self.market_status_label.setText(f"⚠ No data for {symbol}")
                return

            # Convert to DataFrame
            data_dict = {
                'timestamp': [bar.timestamp for bar in bars],
                'open': [float(bar.open) for bar in bars],
                'high': [float(bar.high) for bar in bars],
                'low': [float(bar.low) for bar in bars],
                'close': [float(bar.close) for bar in bars],
                'volume': [bar.volume for bar in bars]
            }

            df = pd.DataFrame(data_dict)
            df.set_index('timestamp', inplace=True)

            # Load into chart
            self.load_data(df)

            # Update status with data source info (only if not live streaming)
            if not self.live_streaming_enabled:
                self.market_status_label.setText(f"✓ Loaded from {source_used}")
                self.market_status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")

            logger.info(f"Loaded {len(bars)} bars for {symbol} from {source_used}")

            # Restart live stream if enabled (with proper cleanup)
            if self.live_streaming_enabled:
                logger.info(f"Restarting live stream for symbol: {symbol}")
                # CRITICAL: Stop existing stream first to prevent deadlock
                await self._stop_live_stream()
                # Small delay to ensure cleanup completes
                import asyncio
                await asyncio.sleep(0.5)
                # Now start new stream
                await self._start_live_stream()

        except Exception as e:
            logger.error(f"Error loading symbol: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
