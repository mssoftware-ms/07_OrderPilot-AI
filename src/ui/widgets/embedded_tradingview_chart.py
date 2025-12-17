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
    <script>
        const { createChart, CrosshairMode, LineStyle, LineSeries, HistogramSeries, CandlestickSeries, createSeriesMarkers } = LightweightCharts;

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

                // Drag state
                let isDragging = false;
                let dragTarget = null;      // { drawing, handle: 'line'|'p1'|'p2' }
                let dragStartY = 0;
                let dragStartX = 0;

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
                        isDragging = true;
                        dragTarget = target;
                        dragStartX = x;
                        dragStartY = y;
                        container.style.cursor = 'grabbing';
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }, true);

                container.addEventListener('mousemove', e => {
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
                    }
                    e.preventDefault();
                    e.stopPropagation();
                }, true);

                container.addEventListener('mouseup', e => {
                    if (isDragging) {
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
                window.chartAPI.addHorizontalLine = (price, color, label = '', lineStyle = 'solid') => {
                    const line = new HorizontalLinePrimitive(price, color || '#26a69a', genId(), label, lineStyle);
                    priceSeries.attachPrimitive(line);
                    drawings.push(line);
                    console.log('Added horizontal line at', price, 'with label:', label);
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
