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
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
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
)

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
                        mouseWheel: false,
                        pressedMouseMove: true,
                        horzTouchDrag: true,
                        vertTouchDrag: true,
                    },
                    handleScale: {
                        axisPressedMouseMove: { time: true, price: true },
                        mouseWheel: true,
                        pinch: true,
                    },
                    autoSize: true,
                });

                const overlaySeries = {};
                const panelMap = {};
                const panelMainSeries = {};
                const panelExtraSeries = {};

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
                    const paneApi = chart.addPane();
                    if (paneApi.setStretchFactor) paneApi.setStretchFactor(1);
                    panelMap[panelId] = paneApi;
                    return paneApi;
                }

                function removePane(panelId) {
                    const paneApi = panelMap[panelId];
                    if (!paneApi) return false;
                    if (paneApi === pricePaneApi) return false;

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

                // Global flag to suppress fitContent during state restoration
                let suppressFitContent = false;

                window.chartAPI = {
                    // Set data with optional skipFit parameter
                    setData: (data, skipFit = false) => {
                        try {
                            priceSeries.setData(data);
                            if (!skipFit && !suppressFitContent) {
                                refitPriceScale();
                            } else {
                                console.log('setData: skipping fitContent (skipFit=' + skipFit + ', suppressFitContent=' + suppressFitContent + ')');
                            }
                        } catch(e){ console.error(e); }
                    },

                    // Suppress fitContent calls during state restoration
                    setSuppressFitContent: (suppress) => {
                        suppressFitContent = suppress;
                        console.log('suppressFitContent set to:', suppress);
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
                            if (panelMap[panelId] !== undefined) {
                                const existingPane = panelMap[panelId];
                                const existingIndex = typeof existingPane?.paneIndex === 'function' ? existingPane.paneIndex() : -1;
                                if (existingIndex >= 0) return true;
                                delete panelMap[panelId];
                            }
                            const paneApi = addPane(panelId);
                            const paneIndex = paneApi.paneIndex();
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
                            let paneApi = panelMap[panelId];
                            if (paneApi && (typeof paneApi.paneIndex !== 'function' || paneApi.paneIndex() < 0)) {
                                delete panelMap[panelId];
                                paneApi = undefined;
                            }
                            paneApi = paneApi || addPane(panelId);
                            let paneIndex = paneApi.paneIndex();
                            if (paneIndex < 0) {
                                paneApi = addPane(panelId);
                                paneIndex = paneApi.paneIndex();
                            }
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

                    fitContent: () => {
                        try {
                            if (!suppressFitContent) {
                                refitPriceScale();
                            } else {
                                console.log('fitContent: suppressed');
                            }
                        } catch(e){ console.error(e); }
                    },
                    resetPriceScale: () => { try { refitPriceScale(); } catch(e){ console.error(e); } },

                    addTradeMarkers: (markers) => {
                        try {
                            if (!Array.isArray(markers)) return false;
                            priceSeries.setMarkers(markers);
                            return true;
                        } catch(e){ console.error(e); return false; }
                    },

                    clearMarkers: () => {
                        try { priceSeries.setMarkers([]); return true; }
                        catch(e){ console.error(e); return false; }
                    },

                    updateBar: (bar) => {
                        try {
                            if (!bar || typeof bar !== 'object') return false;
                            priceSeries.update(bar);
                            return true;
                        } catch(e){ console.error(e); return false; }
                    },

                    getVisibleRange: () => {
                        try { return chart.timeScale().getVisibleLogicalRange(); }
                        catch(e) { console.error(e); return null; }
                    },

                    setVisibleRange: (range) => {
                        try {
                            if (!range) return false;
                            chart.timeScale().setVisibleLogicalRange(range);
                            return true;
                        } catch(e) { console.error(e); return false; }
                    },

                    getPaneLayout: () => {
                        try {
                            const layout = {};
                            const allPanes = chart.panes();
                            const factors = {};
                            if (allPanes.length > 0 && typeof allPanes[0].getStretchFactor === 'function') {
                                factors['price'] = allPanes[0].getStretchFactor();
                            }
                            for (const [id, paneApi] of Object.entries(panelMap)) {
                                if (paneApi && typeof paneApi.getStretchFactor === 'function') {
                                    factors[id] = paneApi.getStretchFactor();
                                }
                            }
                            let total = 0;
                            for (const factor of Object.values(factors)) { total += factor; }
                            if (total > 0) {
                                for (const [id, factor] of Object.entries(factors)) {
                                    layout[id] = Math.round((factor / total) * 100);
                                }
                            }
                            return layout;
                        } catch(e) { console.error(e); return {}; }
                    },

                    setPaneLayout: (layout) => {
                        try {
                            if (!layout || Object.keys(layout).length === 0) return false;
                            let restored = 0;
                            const allPanes = chart.panes();
                            if (layout['price'] !== undefined && allPanes.length > 0) {
                                const pricePane = allPanes[0];
                                if (typeof pricePane.setStretchFactor === 'function') {
                                    pricePane.setStretchFactor(layout['price']);
                                    restored++;
                                }
                            }
                            for (const [id, percentValue] of Object.entries(layout)) {
                                if (id === 'price') continue;
                                const paneApi = panelMap[id];
                                if (paneApi && typeof paneApi.setStretchFactor === 'function') {
                                    paneApi.setStretchFactor(percentValue);
                                    restored++;
                                }
                            }
                            setTimeout(() => {
                                try {
                                    chart.applyOptions({});
                                    const container = document.getElementById('chart-container');
                                    if (container) {
                                        chart.resize(container.clientWidth, container.clientHeight);
                                    }
                                    // REMOVED: fitContent() was resetting zoom after pane layout restoration
                                    // The visible range should be preserved, only pane heights change
                                } catch(e) {}
                            }, 100);
                            return restored > 0;
                        } catch(e) { console.error(e); return false; }
                    },

                    getChartState: () => {
                        try {
                            const visibleRange = chart.timeScale().getVisibleLogicalRange();
                            const paneLayout = window.chartAPI.getPaneLayout();
                            return {
                                version: '1.0.0',
                                timestamp: Date.now(),
                                visibleRange: visibleRange,
                                paneLayout: paneLayout,
                                activeSeries: {
                                    overlays: Object.keys(overlaySeries),
                                    panels: Object.keys(panelMap)
                                },
                                chartOptions: { autoSize: true }
                            };
                        } catch(e) { console.error(e); return {}; }
                    },

                    setChartState: (state) => {
                        try {
                            if (!state || !state.version) return false;
                            let restored = 0;
                            if (state.visibleRange) {
                                try { window.chartAPI.setVisibleRange(state.visibleRange); restored++; }
                                catch(e) {}
                            }
                            if (state.paneLayout) {
                                setTimeout(() => {
                                    try { window.chartAPI.setPaneLayout(state.paneLayout); }
                                    catch(e) {}
                                }, 500);
                                restored++;
                            }
                            return restored > 0;
                        } catch(e) { console.error(e); return false; }
                    },

                    clear: () => {
                        try {
                            priceSeries.setData([]);
                            priceSeries.setMarkers([]);
                            Object.values(overlaySeries).forEach(s => chart.removeSeries(s));
                            Object.keys(overlaySeries).forEach(k => delete overlaySeries[k]);
                            Object.keys(panelMap).forEach(pid => removePane(pid));
                        } catch(e){ console.error(e); }
                    }
                };

                document.getElementById('status').textContent = 'Ready - waiting for data...';
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


class EmbeddedTradingViewChart(
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

        # Setup UI
        self._setup_ui()

        # Subscribe to events
        event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)
        event_bus.subscribe(EventType.MARKET_TICK, self._on_market_tick)
        event_bus.subscribe(EventType.MARKET_DATA_TICK, self._on_market_tick)

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

        # Toolbar (from ToolbarMixin)
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
