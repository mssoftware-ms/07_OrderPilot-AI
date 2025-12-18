"""TradingView Lightweight Charts HTML/JavaScript Template.

This module contains the HTML template with embedded JavaScript for the
TradingView Lightweight Charts widget. Separated from the main Python
module to comply with the 600 LOC rule for Python files.

The template includes:
- Chart initialization with candlestick series
- Drawing tools (horizontal lines, trend lines, rays, percent rectangles)
- Panel management for indicators
- Drag-and-drop support for stop lines
- WebChannel bridge for Python communication

Note: This file contains a large string constant with HTML/JavaScript,
not Python code, so LOC rules for Python code don't apply.
"""

# HTML template for TradingView Lightweight Charts
# This is extracted from embedded_tradingview_chart.py to reduce file size.
#
# The template provides:
# - Professional chart appearance
# - Drawing toolbar with multiple tools
# - Price panels for indicators
# - Drag support for stop lines (with Python callback)
# - Chart state management (visible range, pane layout)

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
        #main-container { display: flex; width: 100vw; height: 100vh; }
        #drawing-toolbar {
            width: 36px;
            background: #1a1a1a;
            border-right: 1px solid #333;
            display: flex;
            flex-direction: column;
            padding: 4px 0;
            z-index: 1000;
        }
        .tool-btn {
            width: 32px;
            height: 32px;
            margin: 2px auto;
            border: none;
            border-radius: 4px;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        .tool-btn:hover { background: #333; }
        .tool-btn.active { background: #2962ff; }
        .tool-btn svg { width: 18px; height: 18px; }
        .tool-separator { height: 1px; background: #333; margin: 6px 4px; }
        #chart-container { flex: 1; height: 100vh; position: relative; }
        #status { position: absolute; top: 10px; left: 10px; color: #00ff00; font-size: 12px; font-family: monospace; z-index: 1000; }
    </style>
</head>
<body>
    <div id="main-container">
        <div id="drawing-toolbar">
            <button class="tool-btn active" id="tool-pointer" title="Auswahl (Esc)">
                <svg viewBox="0 0 24 24" fill="#aaa"><path d="M13.64 21.97C13.14 22.21 12.54 22 12.31 21.5L10.13 16.76L7.62 18.78C7.45 18.92 7.24 19 7 19C6.45 19 6 18.55 6 18V3C6 2.45 6.45 2 7 2C7.24 2 7.47 2.09 7.64 2.23L19.14 11.74C19.64 12.12 19.5 12.91 18.91 13.09L14.62 14.38L16.8 19.12C17.04 19.62 16.83 20.22 16.33 20.46L13.64 21.97Z"/></svg>
            </button>
            <div class="tool-separator"></div>
            <button class="tool-btn" id="tool-hline-green" title="Horizontale Linie (Grün)">
                <svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12" stroke="#26a69a" stroke-width="3"/></svg>
            </button>
            <button class="tool-btn" id="tool-hline-red" title="Horizontale Linie (Rot)">
                <svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12" stroke="#ef5350" stroke-width="3"/></svg>
            </button>
            <button class="tool-btn" id="tool-trendline" title="Trendlinie">
                <svg viewBox="0 0 24 24"><line x1="4" y1="18" x2="20" y2="6" stroke="#ffeb3b" stroke-width="2"/></svg>
            </button>
            <button class="tool-btn" id="tool-ray" title="Strahl">
                <svg viewBox="0 0 24 24"><line x1="4" y1="16" x2="20" y2="8" stroke="#9c27b0" stroke-width="2"/><circle cx="4" cy="16" r="3" fill="#9c27b0"/></svg>
            </button>
            <button class="tool-btn" id="tool-percent-rect" title="Prozent-Rechteck (% Differenz)">
                <svg viewBox="0 0 24 24"><rect x="4" y="6" width="16" height="12" fill="rgba(38,166,154,0.3)" stroke="#26a69a" stroke-width="1.5"/><text x="12" y="14" text-anchor="middle" fill="#26a69a" font-size="8" font-weight="bold">%</text></svg>
            </button>
            <div class="tool-separator"></div>
            <button class="tool-btn" id="tool-delete" title="Löschen (Del)">
                <svg viewBox="0 0 24 24" fill="#ef5350"><path d="M19 4h-3.5l-1-1h-5l-1 1H5v2h14M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12z"/></svg>
            </button>
            <button class="tool-btn" id="tool-clear-all" title="Alle löschen">
                <svg viewBox="0 0 24 24" fill="#ff9800"><path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/></svg>
            </button>
        </div>
        <div id="chart-container">
            <div id="status">Initializing chart...</div>
        </div>
    </div>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        const { createChart, CrosshairMode, LineStyle, LineSeries, HistogramSeries, CandlestickSeries, createSeriesMarkers } = LightweightCharts;

        // Global reference to Python bridge (set up after QWebChannel connects)
        let pyBridge = null;

        // Initialize QWebChannel for Python communication
        function initQtBridge() {
            if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined' && qt.webChannelTransport) {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    pyBridge = channel.objects.pyBridge;
                    console.log('QWebChannel connected, pyBridge available:', !!pyBridge);
                });
            } else {
                console.log('QWebChannel not available (running outside Qt?)');
            }
        }

        // Initialize bridge on load
        setTimeout(initQtBridge, 100);

        function initializeChart() {
            try {
                const container = document.getElementById('chart-container');
                const scaleMargins = { top: 0.15, bottom: 0.15 };
                // Get timezone offset for local time display (e.g., CET = +1, CEST = +2)
                const getLocalTimezoneOffsetHours = () => {
                    const now = new Date();
                    return -now.getTimezoneOffset() / 60;  // Offset in hours (positive for east of UTC)
                };
                const tzOffsetHours = getLocalTimezoneOffsetHours();
                console.log('Local timezone offset: UTC+' + tzOffsetHours);

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
                    timeScale: {
                        timeVisible: true,
                        secondsVisible: false,
                        borderColor: '#485c7b',
                        // Shift displayed time by local timezone offset
                        shiftVisibleRangeOnNewBar: true,
                    },
                    localization: {
                        locale: 'de-DE',
                        // Timestamps are already shifted to local time in Python,
                        // so we use UTC methods to display them directly without double conversion
                        timeFormatter: (timestamp) => {
                            const date = new Date(timestamp * 1000);
                            const hours = String(date.getUTCHours()).padStart(2, '0');
                            const minutes = String(date.getUTCMinutes()).padStart(2, '0');
                            return `${hours}:${minutes}`;
                        },
                        dateFormatter: (timestamp) => {
                            const date = new Date(timestamp * 1000);
                            const day = String(date.getUTCDate()).padStart(2, '0');
                            const month = String(date.getUTCMonth() + 1).padStart(2, '0');
                            const year = date.getUTCFullYear();
                            return `${day}.${month}.${year}`;
                        },
                    },
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

                // Markers primitive holder (v5 API)
                let seriesMarkers = null;

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
                    updateCandle: (c) => {
                        try {
                            // Track last update time to avoid "Cannot update oldest data" errors
                            if (window._lastCandleTime && c.time < window._lastCandleTime) {
                                return false;
                            }
                            priceSeries.update(c);
                            window._lastCandleTime = c.time;
                            return true;
                        } catch(e){
                            if (e.message && e.message.includes('oldest data')) return false;
                            console.error(e);
                            return false;
                        }
                    },
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
                                zOrder: -10,  // Render behind drawings
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
                    updatePanelData: (panelId, point) => {
                        try {
                            const s = panelMainSeries[panelId];
                            if (!s) return false;
                            // Track last update time to avoid "Cannot update oldest data" errors
                            const timeKey = '_lastTime_' + panelId;
                            if (window[timeKey] && point.time < window[timeKey]) {
                                // Skip older data silently
                                return false;
                            }
                            s.update(point);
                            window[timeKey] = point.time;
                            return true;
                        } catch(e){
                            // Silently ignore "Cannot update oldest data" errors
                            if (e.message && e.message.includes('oldest data')) return false;
                            console.error(e);
                            return false;
                        }
                    },

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
                    updatePanelSeriesData: (panelId, seriesKey, point) => { try { const s = panelExtraSeries[panelId + '_' + seriesKey]; if (!s) return false; s.update(point); return true; } catch(e){ console.error(e); return false; } },

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
                            // Use v5 createSeriesMarkers API
                            if (seriesMarkers) {
                                // Update existing markers primitive
                                seriesMarkers.setMarkers(markers);
                            } else if (markers.length > 0) {
                                // Create new markers primitive
                                seriesMarkers = createSeriesMarkers(priceSeries, markers);
                            }
                            console.log('Added ' + markers.length + ' trade markers');
                            return true;
                        } catch(e){ console.error('addTradeMarkers error:', e); return false; }
                    },

                    clearMarkers: () => {
                        try {
                            if (seriesMarkers) {
                                seriesMarkers.setMarkers([]);
                            }
                            console.log('Cleared markers');
                            return true;
                        }
                        catch(e){ console.error('clearMarkers error:', e); return false; }
                    },

                    updateBar: (bar) => {
                        try {
                            if (!bar || typeof bar !== 'object') return false;
                            // Track last update time to avoid "Cannot update oldest data" errors
                            if (window._lastBarTime && bar.time < window._lastBarTime) {
                                return false;
                            }
                            priceSeries.update(bar);
                            window._lastBarTime = bar.time;
                            return true;
                        } catch(e){
                            if (e.message && e.message.includes('oldest data')) return false;
                            console.error(e);
                            return false;
                        }
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
                            // Clear markers using v5 API
                            if (seriesMarkers) {
                                seriesMarkers.destroy();
                                seriesMarkers = null;
                            }
                            Object.values(overlaySeries).forEach(s => chart.removeSeries(s));
                            Object.keys(overlaySeries).forEach(k => delete overlaySeries[k]);
                            Object.keys(panelMap).forEach(pid => removePane(pid));
                        } catch(e){ console.error(e); }
                    }
                };

                // ==================== DRAWING TOOLS ====================

                // Drawing state
                let currentTool = 'pointer';
                let drawingPoints = [];
                let previewPrimitive = null;
                const drawings = []; // All drawn primitives
                let selectedDrawing = null;

                // Drawing primitive classes
                class HorizontalLinePrimitive {
                    constructor(price, color, id, label = '', lineStyle = 'solid') {
                        this.price = price;
                        this.color = color;
                        this.id = id;
                        this.label = label;
                        this.lineStyle = lineStyle;
                        this.type = 'hline';
                        this._paneViews = [new HorizontalLinePaneView(this)];
                    }
                    updateAllViews() { this._paneViews.forEach(v => v.update()); }
                    paneViews() { return this._paneViews; }
                }

                class HorizontalLinePaneView {
                    constructor(source) { this._source = source; this._y = null; }
                    update() { this._y = priceSeries.priceToCoordinate(this._source.price); }
                    renderer() { return new HorizontalLineRenderer(this._y, this._source.color, this._source.label, this._source.lineStyle); }
                }

                class HorizontalLineRenderer {
                    constructor(y, color, label = '', lineStyle = 'solid') {
                        this._y = y;
                        this._color = color;
                        this._label = label;
                        this._lineStyle = lineStyle;
                    }
                    draw(target) {
                        target.useBitmapCoordinateSpace(scope => {
                            if (this._y === null) return;
                            const ctx = scope.context;
                            const yScaled = Math.round(this._y * scope.verticalPixelRatio);

                            // Draw line
                            ctx.strokeStyle = this._color;
                            ctx.lineWidth = 2;
                            if (this._lineStyle === 'dashed') {
                                ctx.setLineDash([8, 4]);
                            } else if (this._lineStyle === 'dotted') {
                                ctx.setLineDash([2, 2]);
                            } else {
                                ctx.setLineDash([]);
                            }
                            ctx.beginPath();
                            ctx.moveTo(0, yScaled);
                            ctx.lineTo(scope.bitmapSize.width, yScaled);
                            ctx.stroke();
                            ctx.setLineDash([]);

                            // Draw label if provided
                            if (this._label) {
                                const fontSize = 11 * scope.verticalPixelRatio;
                                ctx.font = `bold ${fontSize}px Arial`;
                                const textWidth = ctx.measureText(this._label).width;
                                const padding = 4 * scope.verticalPixelRatio;
                                const labelX = scope.bitmapSize.width - textWidth - padding * 3;
                                const labelY = yScaled - padding;

                                // Background
                                ctx.fillStyle = this._color;
                                ctx.fillRect(labelX - padding, labelY - fontSize, textWidth + padding * 2, fontSize + padding);

                                // Text
                                ctx.fillStyle = '#ffffff';
                                ctx.fillText(this._label, labelX, labelY - padding/2);
                            }
                        });
                    }
                }

                class TrendLinePrimitive {
                    constructor(p1, p2, color, id) {
                        this.p1 = p1; this.p2 = p2; this.color = color; this.id = id;
                        this.type = 'trendline';
                        this._paneViews = [new TrendLinePaneView(this)];
                    }
                    updateAllViews() { this._paneViews.forEach(v => v.update()); }
                    paneViews() { return this._paneViews; }
                }

                class TrendLinePaneView {
                    constructor(source) { this._source = source; this._p1 = {x:null,y:null}; this._p2 = {x:null,y:null}; }
                    update() {
                        const ts = chart.timeScale();
                        this._p1 = { x: ts.timeToCoordinate(this._source.p1.time), y: priceSeries.priceToCoordinate(this._source.p1.price) };
                        this._p2 = { x: ts.timeToCoordinate(this._source.p2.time), y: priceSeries.priceToCoordinate(this._source.p2.price) };
                    }
                    renderer() { return new TrendLineRenderer(this._p1, this._p2, this._source.color); }
                }

                class TrendLineRenderer {
                    constructor(p1, p2, color) { this._p1 = p1; this._p2 = p2; this._color = color; }
                    draw(target) {
                        target.useBitmapCoordinateSpace(scope => {
                            if (this._p1.x === null || this._p1.y === null || this._p2.x === null || this._p2.y === null) return;
                            const ctx = scope.context;
                            const x1 = Math.round(this._p1.x * scope.horizontalPixelRatio);
                            const y1 = Math.round(this._p1.y * scope.verticalPixelRatio);
                            const x2 = Math.round(this._p2.x * scope.horizontalPixelRatio);
                            const y2 = Math.round(this._p2.y * scope.verticalPixelRatio);
                            ctx.strokeStyle = this._color;
                            ctx.lineWidth = 2;
                            ctx.beginPath();
                            ctx.moveTo(x1, y1);
                            ctx.lineTo(x2, y2);
                            ctx.stroke();
                            // Draw endpoints
                            ctx.fillStyle = this._color;
                            ctx.beginPath(); ctx.arc(x1, y1, 4, 0, 2*Math.PI); ctx.fill();
                            ctx.beginPath(); ctx.arc(x2, y2, 4, 0, 2*Math.PI); ctx.fill();
                        });
                    }
                }

                class RayPrimitive {
                    constructor(p1, p2, color, id) {
                        this.p1 = p1; this.p2 = p2; this.color = color; this.id = id;
                        this.type = 'ray';
                        this._paneViews = [new RayPaneView(this)];
                    }
                    updateAllViews() { this._paneViews.forEach(v => v.update()); }
                    paneViews() { return this._paneViews; }
                }

                class RayPaneView {
                    constructor(source) { this._source = source; this._p1 = {x:null,y:null}; this._p2 = {x:null,y:null}; }
                    update() {
                        const ts = chart.timeScale();
                        this._p1 = { x: ts.timeToCoordinate(this._source.p1.time), y: priceSeries.priceToCoordinate(this._source.p1.price) };
                        this._p2 = { x: ts.timeToCoordinate(this._source.p2.time), y: priceSeries.priceToCoordinate(this._source.p2.price) };
                    }
                    renderer() { return new RayRenderer(this._p1, this._p2, this._source.color); }
                }

                class RayRenderer {
                    constructor(p1, p2, color) { this._p1 = p1; this._p2 = p2; this._color = color; }
                    draw(target) {
                        target.useBitmapCoordinateSpace(scope => {
                            if (this._p1.x === null || this._p1.y === null || this._p2.x === null || this._p2.y === null) return;
                            const ctx = scope.context;
                            const x1 = Math.round(this._p1.x * scope.horizontalPixelRatio);
                            const y1 = Math.round(this._p1.y * scope.verticalPixelRatio);
                            const x2 = Math.round(this._p2.x * scope.horizontalPixelRatio);
                            const y2 = Math.round(this._p2.y * scope.verticalPixelRatio);
                            // Extend line to edge of chart
                            const dx = x2 - x1; const dy = y2 - y1;
                            const len = Math.sqrt(dx*dx + dy*dy);
                            if (len === 0) return;
                            const extendX = x1 + (dx/len) * scope.bitmapSize.width * 2;
                            const extendY = y1 + (dy/len) * scope.bitmapSize.width * 2;
                            ctx.strokeStyle = this._color;
                            ctx.lineWidth = 2;
                            ctx.beginPath();
                            ctx.moveTo(x1, y1);
                            ctx.lineTo(extendX, extendY);
                            ctx.stroke();
                            // Draw start point
                            ctx.fillStyle = this._color;
                            ctx.beginPath(); ctx.arc(x1, y1, 5, 0, 2*Math.PI); ctx.fill();
                        });
                    }
                }

                // ==================== PERCENT RECTANGLE TOOL ====================
                class PercentRectPrimitive {
                    constructor(p1, p2, id) {
                        this.p1 = p1;  // First point: reference price (100%)
                        this.p2 = p2;  // Second point: comparison price
                        this.id = id;
                        this.type = 'percent-rect';
                        this.updatePercent();
                        this._paneViews = [new PercentRectPaneView(this)];
                    }
                    updatePercent() {
                        // Calculate percent difference based on current p1 and p2
                        this.percentDiff = ((this.p2.price - this.p1.price) / this.p1.price) * 100;
                        // Color: green for positive, red for negative
                        this.color = this.percentDiff >= 0 ? 'rgba(38, 166, 154, 0.3)' : 'rgba(239, 83, 80, 0.3)';
                        this.borderColor = this.percentDiff >= 0 ? '#26a69a' : '#ef5350';
                    }
                    updateAllViews() { this._paneViews.forEach(v => v.update()); }
                    paneViews() { return this._paneViews; }
                }

                class PercentRectPaneView {
                    constructor(source) {
                        this._source = source;
                        this._p1 = {x:null,y:null};
                        this._p2 = {x:null,y:null};
                    }
                    update() {
                        const ts = chart.timeScale();
                        this._p1 = {
                            x: ts.timeToCoordinate(this._source.p1.time),
                            y: priceSeries.priceToCoordinate(this._source.p1.price)
                        };
                        this._p2 = {
                            x: ts.timeToCoordinate(this._source.p2.time),
                            y: priceSeries.priceToCoordinate(this._source.p2.price)
                        };
                    }
                    renderer() {
                        return new PercentRectRenderer(
                            this._p1, this._p2,
                            this._source.color, this._source.borderColor,
                            this._source.percentDiff, this._source.p1.price, this._source.p2.price
                        );
                    }
                }

                class PercentRectRenderer {
                    constructor(p1, p2, fillColor, borderColor, percentDiff, price1, price2) {
                        this._p1 = p1;
                        this._p2 = p2;
                        this._fillColor = fillColor;
                        this._borderColor = borderColor;
                        this._percentDiff = percentDiff;
                        this._price1 = price1;
                        this._price2 = price2;
                    }
                    draw(target) {
                        target.useBitmapCoordinateSpace(scope => {
                            if (this._p1.x === null || this._p1.y === null ||
                                this._p2.x === null || this._p2.y === null) return;
                            const ctx = scope.context;
                            const x1 = Math.round(this._p1.x * scope.horizontalPixelRatio);
                            const y1 = Math.round(this._p1.y * scope.verticalPixelRatio);
                            const x2 = Math.round(this._p2.x * scope.horizontalPixelRatio);
                            const y2 = Math.round(this._p2.y * scope.verticalPixelRatio);

                            // Draw filled rectangle
                            ctx.fillStyle = this._fillColor;
                            ctx.fillRect(Math.min(x1, x2), Math.min(y1, y2),
                                        Math.abs(x2 - x1), Math.abs(y2 - y1));

                            // Draw border
                            ctx.strokeStyle = this._borderColor;
                            ctx.lineWidth = 2;
                            ctx.strokeRect(Math.min(x1, x2), Math.min(y1, y2),
                                          Math.abs(x2 - x1), Math.abs(y2 - y1));

                            // Draw percentage label in the center
                            const centerX = (x1 + x2) / 2;
                            const centerY = (y1 + y2) / 2;
                            const sign = this._percentDiff >= 0 ? '+' : '';
                            const labelText = `${sign}${this._percentDiff.toFixed(2)}%`;

                            const fontSize = 14 * scope.verticalPixelRatio;
                            ctx.font = `bold ${fontSize}px Arial`;
                            const textWidth = ctx.measureText(labelText).width;
                            const padding = 6 * scope.verticalPixelRatio;

                            // Background for label
                            ctx.fillStyle = this._borderColor;
                            ctx.fillRect(centerX - textWidth/2 - padding, centerY - fontSize/2 - padding/2,
                                        textWidth + padding*2, fontSize + padding);

                            // Label text
                            ctx.fillStyle = '#ffffff';
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillText(labelText, centerX, centerY);

                            // Draw price labels at corners
                            const smallFontSize = 10 * scope.verticalPixelRatio;
                            ctx.font = `${smallFontSize}px Arial`;
                            ctx.fillStyle = this._borderColor;

                            // Start price (100%)
                            const price1Text = `${this._price1.toFixed(2)} (100%)`;
                            ctx.textAlign = 'left';
                            ctx.fillText(price1Text, Math.min(x1, x2) + 4, y1 + (y1 < y2 ? smallFontSize + 2 : -4));

                            // End price
                            const price2Text = `${this._price2.toFixed(2)}`;
                            ctx.fillText(price2Text, Math.min(x1, x2) + 4, y2 + (y2 < y1 ? smallFontSize + 2 : -4));

                            // Draw corner points
                            ctx.fillStyle = this._borderColor;
                            ctx.beginPath(); ctx.arc(x1, y1, 4, 0, 2*Math.PI); ctx.fill();
                            ctx.beginPath(); ctx.arc(x2, y2, 4, 0, 2*Math.PI); ctx.fill();
                        });
                    }
                }

                // Generate unique ID
                let drawingIdCounter = 0;
                const genId = () => 'drawing_' + (++drawingIdCounter);

                // Crosshair mode management
                let savedCrosshairMode = CrosshairMode.Normal;
                function disableCrosshairMagnet() {
                    savedCrosshairMode = CrosshairMode.Normal;
                    chart.applyOptions({ crosshair: { mode: CrosshairMode.Hidden } });
                }
                function restoreCrosshairMode() {
                    chart.applyOptions({ crosshair: { mode: savedCrosshairMode } });
                }

                // Drag state for drawings
                let isDragging = false;
                let dragTarget = null;      // { drawing, handle: 'line'|'p1'|'p2' }
                let dragStartY = 0;
                let dragStartX = 0;

                // Y-Pan state for price axis scrolling
                let isYPanning = false;
                let yPanStartY = 0;
                let yPanStartRange = null;

                // Tool selection
                function selectTool(toolId) {
                    // Restore crosshair when switching away from drawing tools
                    if (currentTool !== 'pointer' && toolId === 'pointer') {
                        restoreCrosshairMode();
                    }
                    // Disable crosshair for drawing tools
                    if (toolId !== 'pointer' && toolId !== 'delete') {
                        disableCrosshairMagnet();
                    }
                    currentTool = toolId;
                    drawingPoints = [];
                    removePreview();
                    document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
                    const btn = document.getElementById('tool-' + toolId);
                    if (btn) btn.classList.add('active');
                    container.style.cursor = toolId === 'pointer' ? 'default' : 'crosshair';
                }

                function removePreview() {
                    if (previewPrimitive) {
                        priceSeries.detachPrimitive(previewPrimitive);
                        previewPrimitive = null;
                    }
                }

                function removeDrawing(drawing) {
                    priceSeries.detachPrimitive(drawing);
                    const idx = drawings.indexOf(drawing);
                    if (idx > -1) drawings.splice(idx, 1);
                }

                function clearAllDrawings() {
                    drawings.forEach(d => priceSeries.detachPrimitive(d));
                    drawings.length = 0;
                    selectedDrawing = null;
                }

                // Hit detection for drag handles
                function findDragTarget(x, y) {
                    const threshold = 10;
                    for (const d of drawings) {
                        if (d.type === 'hline') {
                            const lineY = priceSeries.priceToCoordinate(d.price);
                            if (lineY !== null && Math.abs(y - lineY) < threshold) {
                                return { drawing: d, handle: 'line' };
                            }
                        } else if (d.type === 'trendline' || d.type === 'ray') {
                            const ts = chart.timeScale();
                            const x1 = ts.timeToCoordinate(d.p1.time);
                            const y1 = priceSeries.priceToCoordinate(d.p1.price);
                            const x2 = ts.timeToCoordinate(d.p2.time);
                            const y2 = priceSeries.priceToCoordinate(d.p2.price);
                            if (x1 !== null && y1 !== null) {
                                // Check P1 handle
                                if (Math.sqrt((x-x1)*(x-x1) + (y-y1)*(y-y1)) < threshold) {
                                    return { drawing: d, handle: 'p1' };
                                }
                            }
                            if (x2 !== null && y2 !== null) {
                                // Check P2 handle
                                if (Math.sqrt((x-x2)*(x-x2) + (y-y2)*(y-y2)) < threshold) {
                                    return { drawing: d, handle: 'p2' };
                                }
                            }
                            // Check line itself for whole-line drag
                            if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                                const dist = pointToSegmentDist(x, y, x1, y1, x2, y2);
                                if (dist < threshold) {
                                    return { drawing: d, handle: 'line' };
                                }
                            }
                        } else if (d.type === 'percent-rect') {
                            // Hit detection for percent rectangle corners
                            const ts = chart.timeScale();
                            const x1 = ts.timeToCoordinate(d.p1.time);
                            const y1 = priceSeries.priceToCoordinate(d.p1.price);
                            const x2 = ts.timeToCoordinate(d.p2.time);
                            const y2 = priceSeries.priceToCoordinate(d.p2.price);
                            if (x1 !== null && y1 !== null) {
                                // Check P1 handle (top-left or start point)
                                if (Math.sqrt((x-x1)*(x-x1) + (y-y1)*(y-y1)) < threshold) {
                                    return { drawing: d, handle: 'p1' };
                                }
                            }
                            if (x2 !== null && y2 !== null) {
                                // Check P2 handle (bottom-right or end point)
                                if (Math.sqrt((x-x2)*(x-x2) + (y-y2)*(y-y2)) < threshold) {
                                    return { drawing: d, handle: 'p2' };
                                }
                            }
                            // Check if inside rectangle for whole-rect drag
                            if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                                const minX = Math.min(x1, x2);
                                const maxX = Math.max(x1, x2);
                                const minY = Math.min(y1, y2);
                                const maxY = Math.max(y1, y2);
                                if (x >= minX && x <= maxX && y >= minY && y <= maxY) {
                                    return { drawing: d, handle: 'rect' };
                                }
                            }
                        }
                    }
                    return null;
                }

                // Mouse event handlers for dragging
                container.addEventListener('mousedown', e => {
                    if (currentTool !== 'pointer') return;
                    const rect = container.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    const target = findDragTarget(x, y);
                    if (target) {
                        // Drawing drag
                        isDragging = true;
                        dragTarget = target;
                        dragStartX = x;
                        dragStartY = y;
                        container.style.cursor = 'grabbing';
                        e.preventDefault();
                        e.stopPropagation();
                    } else if (e.button === 0) {
                        // Left click without drawing target - enable Y-panning
                        // First disable autoScale to allow manual Y control
                        try {
                            rightScale.applyOptions({ autoScale: false });
                            // Try to get visible price range (may not exist in all versions)
                            const range = typeof rightScale.getVisiblePriceRange === 'function'
                                ? rightScale.getVisiblePriceRange()
                                : null;
                            if (range) {
                                isYPanning = true;
                                yPanStartY = y;
                                yPanStartRange = { from: range.from, to: range.to };
                            }
                        } catch (err) {
                            console.warn('Y-panning not available:', err.message);
                        }
                    }
                }, true);

                container.addEventListener('mousemove', e => {
                    // Handle Y-panning (when no drawing is being dragged)
                    if (isYPanning && yPanStartRange) {
                        const rect = container.getBoundingClientRect();
                        const y = e.clientY - rect.top;
                        const dy = y - yPanStartY;

                        // Convert pixel movement to price movement
                        const chartHeight = rect.height;
                        const priceRange = yPanStartRange.to - yPanStartRange.from;
                        const pricePerPixel = priceRange / chartHeight;
                        const priceDelta = dy * pricePerPixel;

                        // Apply new range (move in same direction as mouse)
                        const newFrom = yPanStartRange.from + priceDelta;
                        const newTo = yPanStartRange.to + priceDelta;
                        try {
                            if (typeof rightScale.setVisiblePriceRange === 'function') {
                                rightScale.setVisiblePriceRange({ from: newFrom, to: newTo });
                            }
                        } catch (err) {
                            console.warn('setVisiblePriceRange failed:', err.message);
                        }
                        return;
                    }

                    if (!isDragging || !dragTarget) {
                        // Update cursor on hover
                        if (currentTool === 'pointer') {
                            const rect = container.getBoundingClientRect();
                            const x = e.clientX - rect.left;
                            const y = e.clientY - rect.top;
                            const target = findDragTarget(x, y);
                            if (target) {
                                if (target.handle === 'p1' || target.handle === 'p2') {
                                    container.style.cursor = 'move';
                                } else if (target.drawing.type === 'hline') {
                                    container.style.cursor = 'ns-resize';
                                } else if (target.drawing.type === 'percent-rect' && target.handle === 'rect') {
                                    container.style.cursor = 'grab';
                                } else {
                                    container.style.cursor = 'grab';
                                }
                            } else {
                                container.style.cursor = 'default';
                            }
                        }
                        return;
                    }
                    const rect = container.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    const d = dragTarget.drawing;
                    const ts = chart.timeScale();

                    if (d.type === 'hline') {
                        // Move horizontal line in Y only
                        const newPrice = priceSeries.coordinateToPrice(y);
                        if (newPrice !== null) {
                            d.price = newPrice;
                            d.updateAllViews();
                            chart.timeScale().applyOptions({}); // Force redraw
                        }
                    } else if (d.type === 'trendline' || d.type === 'ray') {
                        const newPrice = priceSeries.coordinateToPrice(y);
                        const newTime = ts.coordinateToTime(x);
                        if (newPrice !== null && newTime !== null) {
                            if (dragTarget.handle === 'p1') {
                                d.p1 = { time: newTime, price: newPrice };
                            } else if (dragTarget.handle === 'p2') {
                                d.p2 = { time: newTime, price: newPrice };
                            } else if (dragTarget.handle === 'line') {
                                // Move whole line
                                const dx = x - dragStartX;
                                const dy = y - dragStartY;
                                const x1 = ts.timeToCoordinate(d.p1.time);
                                const y1 = priceSeries.priceToCoordinate(d.p1.price);
                                const x2 = ts.timeToCoordinate(d.p2.time);
                                const y2 = priceSeries.priceToCoordinate(d.p2.price);
                                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                                    const newTime1 = ts.coordinateToTime(x1 + dx);
                                    const newPrice1 = priceSeries.coordinateToPrice(y1 + dy);
                                    const newTime2 = ts.coordinateToTime(x2 + dx);
                                    const newPrice2 = priceSeries.coordinateToPrice(y2 + dy);
                                    if (newTime1 && newPrice1 && newTime2 && newPrice2) {
                                        d.p1 = { time: newTime1, price: newPrice1 };
                                        d.p2 = { time: newTime2, price: newPrice2 };
                                        dragStartX = x;
                                        dragStartY = y;
                                    }
                                }
                            }
                            d.updateAllViews();
                            chart.timeScale().applyOptions({}); // Force redraw
                        }
                    } else if (d.type === 'percent-rect') {
                        // Drag handling for percent rectangle
                        const newPrice = priceSeries.coordinateToPrice(y);
                        const newTime = ts.coordinateToTime(x);
                        if (newPrice !== null && newTime !== null) {
                            if (dragTarget.handle === 'p1') {
                                // Move P1 corner
                                d.p1 = { time: newTime, price: newPrice };
                            } else if (dragTarget.handle === 'p2') {
                                // Move P2 corner
                                d.p2 = { time: newTime, price: newPrice };
                            } else if (dragTarget.handle === 'rect') {
                                // Move whole rectangle
                                const dx = x - dragStartX;
                                const dy = y - dragStartY;
                                const x1 = ts.timeToCoordinate(d.p1.time);
                                const y1 = priceSeries.priceToCoordinate(d.p1.price);
                                const x2 = ts.timeToCoordinate(d.p2.time);
                                const y2 = priceSeries.priceToCoordinate(d.p2.price);
                                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                                    const newTime1 = ts.coordinateToTime(x1 + dx);
                                    const newPrice1 = priceSeries.coordinateToPrice(y1 + dy);
                                    const newTime2 = ts.coordinateToTime(x2 + dx);
                                    const newPrice2 = priceSeries.coordinateToPrice(y2 + dy);
                                    if (newTime1 && newPrice1 && newTime2 && newPrice2) {
                                        d.p1 = { time: newTime1, price: newPrice1 };
                                        d.p2 = { time: newTime2, price: newPrice2 };
                                        dragStartX = x;
                                        dragStartY = y;
                                    }
                                }
                            }
                            // Recalculate percent difference after move
                            d.updatePercent();
                            d.updateAllViews();
                            chart.timeScale().applyOptions({}); // Force redraw
                        }
                    }
                    e.preventDefault();
                    e.stopPropagation();
                }, true);

                container.addEventListener('mouseup', e => {
                    // End Y-panning
                    if (isYPanning) {
                        isYPanning = false;
                        yPanStartRange = null;
                    }

                    if (isDragging && dragTarget) {
                        const d = dragTarget.drawing;
                        // Notify Python if a horizontal stop line was moved
                        if (d.type === 'hline' && d.id && pyBridge) {
                            console.log('Line drag ended:', d.id, 'new price:', d.price);
                            // Call Python bridge to notify about the move
                            pyBridge.onStopLineMoved(d.id, d.price);
                            // Update label with new price
                            d.label = d.label.replace(/@\s*[\d.]+/, '@ ' + d.price.toFixed(2));
                            d.updateAllViews();
                            chart.timeScale().applyOptions({}); // Force redraw
                        }
                        isDragging = false;
                        dragTarget = null;
                        container.style.cursor = currentTool === 'pointer' ? 'default' : 'crosshair';
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }, true);

                container.addEventListener('mouseleave', () => {
                    if (isDragging) {
                        isDragging = false;
                        dragTarget = null;
                    }
                    if (isYPanning) {
                        isYPanning = false;
                        yPanStartRange = null;
                    }
                });

                // Click handler for drawing
                chart.subscribeClick(param => {
                    if (isDragging) return; // Ignore clicks during drag
                    if (!param.time || !param.point) return;
                    const price = priceSeries.coordinateToPrice(param.point.y);
                    if (price === null) return;

                    if (currentTool === 'hline-green') {
                        const line = new HorizontalLinePrimitive(price, '#26a69a', genId());
                        priceSeries.attachPrimitive(line);
                        drawings.push(line);
                        selectTool('pointer');
                    }
                    else if (currentTool === 'hline-red') {
                        const line = new HorizontalLinePrimitive(price, '#ef5350', genId());
                        priceSeries.attachPrimitive(line);
                        drawings.push(line);
                        selectTool('pointer');
                    }
                    else if (currentTool === 'trendline' || currentTool === 'ray') {
                        drawingPoints.push({ time: param.time, price });
                        if (drawingPoints.length === 2) {
                            removePreview();
                            const PrimitiveClass = currentTool === 'trendline' ? TrendLinePrimitive : RayPrimitive;
                            const color = currentTool === 'trendline' ? '#ffeb3b' : '#9c27b0';
                            const line = new PrimitiveClass(drawingPoints[0], drawingPoints[1], color, genId());
                            priceSeries.attachPrimitive(line);
                            drawings.push(line);
                            selectTool('pointer');
                        }
                    }
                    else if (currentTool === 'percent-rect') {
                        drawingPoints.push({ time: param.time, price });
                        if (drawingPoints.length === 2) {
                            removePreview();
                            const rect = new PercentRectPrimitive(drawingPoints[0], drawingPoints[1], genId());
                            priceSeries.attachPrimitive(rect);
                            drawings.push(rect);
                            selectTool('pointer');
                        }
                    }
                    else if (currentTool === 'delete') {
                        let nearest = null;
                        let minDist = 20;
                        drawings.forEach(d => {
                            if (d.type === 'hline') {
                                const lineY = priceSeries.priceToCoordinate(d.price);
                                if (lineY !== null) {
                                    const dist = Math.abs(param.point.y - lineY);
                                    if (dist < minDist) { minDist = dist; nearest = d; }
                                }
                            } else if (d.type === 'trendline' || d.type === 'ray') {
                                const ts = chart.timeScale();
                                const x1 = ts.timeToCoordinate(d.p1.time);
                                const y1 = priceSeries.priceToCoordinate(d.p1.price);
                                const x2 = ts.timeToCoordinate(d.p2.time);
                                const y2 = priceSeries.priceToCoordinate(d.p2.price);
                                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                                    const dist = pointToSegmentDist(param.point.x, param.point.y, x1, y1, x2, y2);
                                    if (dist < minDist) { minDist = dist; nearest = d; }
                                }
                            } else if (d.type === 'percent-rect') {
                                // Check if click is inside the rectangle
                                const ts = chart.timeScale();
                                const x1 = ts.timeToCoordinate(d.p1.time);
                                const y1 = priceSeries.priceToCoordinate(d.p1.price);
                                const x2 = ts.timeToCoordinate(d.p2.time);
                                const y2 = priceSeries.priceToCoordinate(d.p2.price);
                                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                                    const px = param.point.x, py = param.point.y;
                                    const minX = Math.min(x1, x2), maxX = Math.max(x1, x2);
                                    const minY = Math.min(y1, y2), maxY = Math.max(y1, y2);
                                    if (px >= minX && px <= maxX && py >= minY && py <= maxY) {
                                        nearest = d; minDist = 0;
                                    }
                                }
                            }
                        });
                        if (nearest) removeDrawing(nearest);
                    }
                });

                // Mouse move for preview (using raw coordinates, not snapped)
                container.addEventListener('mousemove', e => {
                    if ((currentTool === 'trendline' || currentTool === 'ray') && drawingPoints.length === 1 && !isDragging) {
                        const rect = container.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const y = e.clientY - rect.top;
                        const price = priceSeries.coordinateToPrice(y);
                        const time = chart.timeScale().coordinateToTime(x);
                        if (price === null || time === null) return;
                        removePreview();
                        const PrimitiveClass = currentTool === 'trendline' ? TrendLinePrimitive : RayPrimitive;
                        const color = currentTool === 'trendline' ? 'rgba(255,235,59,0.5)' : 'rgba(156,39,176,0.5)';
                        previewPrimitive = new PrimitiveClass(drawingPoints[0], { time, price }, color, 'preview');
                        priceSeries.attachPrimitive(previewPrimitive);
                    }
                    else if (currentTool === 'percent-rect' && drawingPoints.length === 1 && !isDragging) {
                        const rect = container.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const y = e.clientY - rect.top;
                        const price = priceSeries.coordinateToPrice(y);
                        const time = chart.timeScale().coordinateToTime(x);
                        if (price === null || time === null) return;
                        removePreview();
                        previewPrimitive = new PercentRectPrimitive(drawingPoints[0], { time, price }, 'preview');
                        priceSeries.attachPrimitive(previewPrimitive);
                    }
                });

                // Helper: distance from point to line segment
                function pointToSegmentDist(px, py, x1, y1, x2, y2) {
                    const dx = x2 - x1, dy = y2 - y1;
                    const lenSq = dx*dx + dy*dy;
                    if (lenSq === 0) return Math.sqrt((px-x1)*(px-x1) + (py-y1)*(py-y1));
                    let t = ((px-x1)*dx + (py-y1)*dy) / lenSq;
                    t = Math.max(0, Math.min(1, t));
                    const projX = x1 + t*dx, projY = y1 + t*dy;
                    return Math.sqrt((px-projX)*(px-projX) + (py-projY)*(py-projY));
                }

                // Toolbar button handlers
                document.getElementById('tool-pointer').onclick = () => selectTool('pointer');
                document.getElementById('tool-hline-green').onclick = () => selectTool('hline-green');
                document.getElementById('tool-hline-red').onclick = () => selectTool('hline-red');
                document.getElementById('tool-trendline').onclick = () => selectTool('trendline');
                document.getElementById('tool-ray').onclick = () => selectTool('ray');
                document.getElementById('tool-percent-rect').onclick = () => selectTool('percent-rect');
                document.getElementById('tool-delete').onclick = () => selectTool('delete');
                document.getElementById('tool-clear-all').onclick = () => { clearAllDrawings(); selectTool('pointer'); };

                // Keyboard shortcuts
                document.addEventListener('keydown', e => {
                    if (e.key === 'Escape') selectTool('pointer');
                    if (e.key === 'Delete' && selectedDrawing) { removeDrawing(selectedDrawing); selectedDrawing = null; }
                });

                // Expose drawing API
                window.chartAPI.getDrawings = () => drawings.map(d => ({
                    id: d.id, type: d.type,
                    ...(d.type === 'hline' ? { price: d.price, color: d.color } : { p1: d.p1, p2: d.p2, color: d.color })
                }));
                window.chartAPI.clearDrawings = clearAllDrawings;
                window.chartAPI.addHorizontalLine = (price, color, label = '', lineStyle = 'solid', customId = null) => {
                    // Use custom ID if provided, otherwise generate one
                    const lineId = customId || genId();
                    // Remove existing line with same ID if updating
                    const existingIdx = drawings.findIndex(x => x.id === lineId);
                    if (existingIdx !== -1) {
                        const existing = drawings[existingIdx];
                        priceSeries.detachPrimitive(existing);
                        drawings.splice(existingIdx, 1);
                        console.log('Removed existing line with ID:', lineId);
                    }
                    const line = new HorizontalLinePrimitive(price, color || '#26a69a', lineId, label, lineStyle);
                    priceSeries.attachPrimitive(line);
                    drawings.push(line);
                    console.log('Added horizontal line at', price, 'with label:', label, 'ID:', lineId);
                    return line.id;
                };
                window.chartAPI.addTrendLine = (p1, p2, color) => {
                    const line = new TrendLinePrimitive(p1, p2, color || '#ffeb3b', genId());
                    priceSeries.attachPrimitive(line);
                    drawings.push(line);
                    return line.id;
                };
                window.chartAPI.removeDrawingById = (id) => {
                    const d = drawings.find(x => x.id === id);
                    if (d) removeDrawing(d);
                };

                // ==================== END DRAWING TOOLS ====================

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
