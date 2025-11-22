"""Embedded TradingView Lightweight Charts Widget.

This module provides a fully embedded trading chart using TradingView's Lightweight Charts
library rendered directly in a Qt WebEngine view (Chromium-based).
"""

import json
import logging
from collections import deque
from datetime import datetime
from typing import Optional, Dict, List, Any

import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QUrl
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
    from PyQt6.QtWebChannel import QWebChannel
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
    <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #0a0a0a;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }

        #chart-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100%;
            overflow: hidden;  /* No scrolling - flex takes care of sizing */
        }

        /* Price chart always takes up 3x space of other panels */
        #price-chart {
            flex: 3 1 0;  /* flex-grow: 3, flex-shrink: 1, flex-basis: 0 */
            width: 100%;
            min-height: 0;  /* Important for flex children */
            background-color: #0a0a0a;
            border-bottom: 1px solid #2a2a2a;
            position: relative;
            overflow: hidden;
            box-sizing: border-box;  /* Include border in width */
            padding: 0;
            margin: 0;
        }

        /* Each indicator panel (volume, RSI, etc.) gets equal space */
        .indicator-panel {
            flex: 1 1 0;  /* flex-grow: 1, flex-shrink: 1, flex-basis: 0 */
            width: 100%;
            min-height: 0;  /* Important for flex children */
            background-color: #0a0a0a;
            border-bottom: 1px solid #2a2a2a;
            position: relative;
            overflow: hidden;
            box-sizing: border-box;  /* Include border in width */
            padding: 0;
            margin: 0;
        }

        /* Last panel has no bottom border */
        .indicator-panel:last-child {
            border-bottom: none;
        }

        /* Panel header with indicator name - Stock3 style */
        .panel-header {
            position: absolute;
            top: 3px;
            left: 8px;
            color: #d1d4dc;
            font-size: 12px;
            font-weight: 600;
            z-index: 100;
            pointer-events: all;  /* Enable clicking for editing */
            background: rgba(10, 10, 10, 0.85);
            padding: 3px 8px;
            border-radius: 3px;
            cursor: pointer;
            user-select: none;
        }

        .panel-header:hover {
            background: rgba(10, 10, 10, 0.95);
            color: #FF8C00;
        }

        /* Panel value display (current indicator value) */
        .panel-value {
            position: absolute;
            top: 3px;
            right: 8px;
            color: #d1d4dc;
            font-size: 11px;
            font-weight: 500;
            z-index: 100;
            pointer-events: none;
            background: rgba(10, 10, 10, 0.7);
            padding: 2px 6px;
            border-radius: 2px;
            font-family: monospace;
        }
        #status {
            position: absolute;
            top: 10px;
            left: 10px;
            color: #00ff00;
            font-size: 12px;
            font-family: monospace;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div id="status">Initializing chart...</div>
    <div id="chart-container">
        <div id="price-chart"></div>
        <!-- Indicator panels will be dynamically added here -->
    </div>
    <script>
        console.log('[INIT] Step 1: Script started');

        // Function to initialize charts
        function initializeCharts() {
            console.log('[INIT] Step 2: Initializing charts...');

            try {
                // Debug logging
                console.log('[INIT] Step 3: Starting chart initialization...');

                // Create price chart (top 70%)
                console.log('[INIT] Step 4: Getting price-chart container...');
                const priceContainer = document.getElementById('price-chart');

                if (!priceContainer) {
                    console.error('[ERROR] price-chart container not found!');
                    document.getElementById('status').textContent = 'ERROR: Chart container not found';
                    return;
                }

                console.log('[INIT] Step 5: Creating price chart...');

                // Ensure we have valid dimensions
                const priceWidth = priceContainer.clientWidth || 800;
                const priceHeight = priceContainer.clientHeight || 400;
                console.log('[INIT] Price chart dimensions - width:', priceWidth, 'height:', priceHeight);

                const priceChart = LightweightCharts.createChart(priceContainer, {
                width: priceWidth,
                height: priceHeight,
                layout: {
                    background: { color: '#0a0a0a' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: 'rgba(70, 70, 70, 0.4)' },
                    horzLines: { color: 'rgba(70, 70, 70, 0.4)' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                    borderColor: '#485c7b',
                    visible: true,  // Show time scale
                },
                rightPriceScale: {
                    borderColor: '#485c7b',
                    scaleMargins: {
                        top: 0.1,
                        bottom: 0.1,
                    },
                    minimumWidth: 60,  // Fixed width for alignment
                },
                handleScroll: {
                    mouseWheel: true,      // Zoom with mouse wheel
                    pressedMouseMove: true, // Pan with mouse drag
                    horzTouchDrag: true,   // Pan horizontally on touch
                    vertTouchDrag: true    // Pan vertically on touch
                },
                handleScale: {
                    axisPressedMouseMove: true,   // Enable dragging price scale (vertical pan)
                    mouseWheel: true,             // Zoom with mouse wheel
                    pinch: true                   // Zoom with pinch gesture
                },
                kineticScroll: {
                    mouse: false,  // Disable kinetic scroll with mouse
                    touch: true    // Enable kinetic scroll on touch
                }
            });

            console.log('Price chart created');

            // Create candlestick series
            const candlestickSeries = priceChart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });

            console.log('Candlestick series created');

            // Initial width alignment before any panels are added
            syncPriceScaleWidths();

            // Store all charts and their series
            const charts = {
                price: priceChart
            };
            const indicatorSeries = {};  // For overlays on price chart
            const panelCharts = {};      // For separate indicator panels (Volume, RSI, etc.)
            const panelSeries = {};      // Series in each panel

            // Time scale synchronization array (global for access in API functions)
            window.allCharts = [priceChart];
            window.masterChart = priceChart;  // Price chart is the master

            // Simple synchronization: Master chart controls all others
            let isSyncing = false;

            // Ensure price scale widths stay identical across price/indicator charts
            function applyPriceScaleWidth(width) {
                try {
                    if (!width || width <= 0) return;

                    // Lock master to its measured width to avoid jitter
                    priceChart.priceScale('right').applyOptions({ minimumWidth: width });

                    // Apply the same minimum width to every panel chart
                    Object.values(panelCharts).forEach(chart => {
                        chart.priceScale('right').applyOptions({ minimumWidth: width });
                    });
                } catch(e) {
                    console.error('Error syncing price scale widths:', e);
                }
            }

            // Measure current width and propagate to panels
            function syncPriceScaleWidths() {
                try {
                    const masterScale = priceChart.priceScale('right');
                    const masterWidth = masterScale && masterScale.width ? masterScale.width() : 0;
                    applyPriceScaleWidth(masterWidth);
                } catch(e) {
                    console.error('Error measuring price scale width:', e);
                }
            }

            // Subscribe to master chart changes
            priceChart.timeScale().subscribeVisibleTimeRangeChange(() => {
                if (isSyncing) return;

                const masterTimeScale = priceChart.timeScale();
                const timeRange = masterTimeScale.getVisibleRange();
                if (!timeRange) return;

                isSyncing = true;

                // Sync time range AND bar spacing to all panel charts
                const barSpacing = masterTimeScale.getBarSpacing ? masterTimeScale.getBarSpacing() : (masterTimeScale.options().barSpacing || 6);
                const rightOffset = masterTimeScale.getRightOffset ? masterTimeScale.getRightOffset() : (masterTimeScale.options().rightOffset || 0);

                Object.values(panelCharts).forEach(chart => {
                    try {
                        // Apply time scale options for alignment
                        chart.applyOptions({
                            timeScale: {
                                barSpacing: barSpacing,
                                rightOffset: rightOffset
                            }
                        });
                        chart.timeScale().setVisibleRange(timeRange);
                    } catch(e) {
                        console.error('Error syncing chart:', e);
                    }
                });

                isSyncing = false;

                // Keep widths aligned whenever scale changes
                syncPriceScaleWidths();
            });

            priceChart.timeScale().subscribeVisibleLogicalRangeChange(() => {
                if (isSyncing) return;

                const logicalRange = priceChart.timeScale().getVisibleLogicalRange();
                if (!logicalRange) return;

                isSyncing = true;

                // Apply to all panel charts
                Object.values(panelCharts).forEach(chart => {
                    try {
                        chart.timeScale().setVisibleLogicalRange(logicalRange);
                    } catch(e) {
                        console.error('Error syncing logical range:', e);
                    }
                });

                isSyncing = false;
            });

            // Function to sync a new chart with master
            window.syncChartWithMaster = function(chart) {
                if (!window.masterChart) return;

                try {
                    const masterTimeScale = window.masterChart.timeScale();
                    const chartTimeScale = chart.timeScale();

                    // Sync all time scale properties for perfect alignment
                    const timeRange = masterTimeScale.getVisibleRange();
                    const logicalRange = masterTimeScale.getVisibleLogicalRange();

                    // Get the bar spacing and right offset from master
                    const options = {
                        rightOffset: masterTimeScale.options().rightOffset || 0,
                        barSpacing: masterTimeScale.options().barSpacing || 6,
                    };

                    // Apply to the new chart
                    chart.applyOptions({
                        timeScale: options
                    });

                    if (timeRange) {
                        chartTimeScale.setVisibleRange(timeRange);
                    }
                    if (logicalRange) {
                        chartTimeScale.setVisibleLogicalRange(logicalRange);
                    }

                    // Force the same scroll position
                    const scrollPos = masterTimeScale.scrollPosition();
                    if (scrollPos !== null && scrollPos !== undefined && !isNaN(scrollPos)) {
                        chartTimeScale.scrollToPosition(scrollPos, false);
                    }
                } catch(e) {
                    console.error('Error syncing with master:', e);
                }
            };

            // Old function for compatibility
            window.synchronizeTimeScales = function() {
                // No longer needed, master chart handles it
            };

            // Function to update time scale visibility (only last panel shows time)
            window.updateTimeScaleVisibility = function() {
                // Hide time scale on price chart if there are indicator panels
                const hasIndicators = Object.keys(panelCharts).length > 0;
                priceChart.applyOptions({
                    timeScale: {
                        visible: !hasIndicators  // Hide if indicators exist
                    }
                });

                // Hide time scale on all indicator panels except the last one
                const panelIds = Object.keys(panelCharts);
                panelIds.forEach((panelId, index) => {
                    const isLast = index === panelIds.length - 1;
                    panelCharts[panelId].applyOptions({
                        timeScale: {
                            visible: isLast  // Only show on last panel
                        }
                    });
                });

                console.log('Updated time scale visibility - ' + panelIds.length + ' panels');
            };

            console.log('[INIT] Step 5: Calling synchronizeTimeScales...');
            window.synchronizeTimeScales();
            console.log('[INIT] Step 6: Time scales synchronized');

            // Handle window resize for all charts
            console.log('[INIT] Step 7: Setting up resize handler...');

            // Function to resize a chart based on its container (use price chart width for alignment)
            function resizeChart(chart) {
                if (chart && chart.applyOptions && chart.chartElement) {
                    const container = chart.chartElement().parentElement;
                    if (container) {
                        // For panel charts, use the price chart width for alignment
                        const priceChartElement = document.getElementById('price-chart');
                        const isPriceChart = container.id === 'price-chart';

                        const width = isPriceChart ?
                            container.clientWidth :
                            (priceChartElement ? priceChartElement.clientWidth : container.clientWidth);
                        const height = container.clientHeight;

                        if (width > 0 && height > 0) {
                            chart.applyOptions({ width, height });
                        }
                    }
                }
            }

            // Window resize handler
            window.addEventListener('resize', () => {
                Object.values(charts).forEach(resizeChart);
                Object.values(panelCharts).forEach(resizeChart);
                syncPriceScaleWidths();
            });

            // ResizeObserver to handle flex layout changes
            const resizeObserver = new ResizeObserver(entries => {
                entries.forEach(entry => {
                    const chartElement = entry.target.querySelector('*');
                    if (chartElement) {
                        // Find the chart that belongs to this container
                        Object.values(charts).forEach(chart => {
                            if (chart.chartElement && chart.chartElement().parentElement === entry.target) {
                                resizeChart(chart);
                            }
                        });
                        Object.values(panelCharts).forEach(chart => {
                            if (chart.chartElement && chart.chartElement().parentElement === entry.target) {
                                resizeChart(chart);
                            }
                        });
                    }
                });
            });

            // Observe price chart container
            resizeObserver.observe(priceContainer);

            // Store observer globally so we can observe new panels
            window.chartResizeObserver = resizeObserver;

            // API for Python integration
            console.log('[INIT] Step 8: Creating chartAPI object...');
            window.chartAPI = {
                // Set candlestick data
                setData: function(data) {
                    try {
                        candlestickSeries.setData(data);
                        console.log('Set ' + data.length + ' candles');
                        document.getElementById('status').textContent = 'Loaded ' + data.length + ' bars';
                        syncPriceScaleWidths();
                    } catch(e) {
                        console.error('Error setting data:', e);
                    }
                },

                // Update single candle
                updateCandle: function(candle) {
                    try {
                        candlestickSeries.update(candle);
                        syncPriceScaleWidths();
                    } catch(e) {
                        console.error('Error updating candle:', e);
                    }
                },

                // Legacy: Set volume data (now handled by panels)
                setVolumeData: function(data) {
                    console.warn('setVolumeData is deprecated, use setPanelData instead');
                    return this.setPanelData('volume', data);
                },

                // Legacy: Update volume (now handled by panels)
                updateVolume: function(volume) {
                    console.warn('updateVolume is deprecated, use updatePanelData instead');
                    return this.updatePanelData('volume', volume);
                },

                // Add indicator line
                addIndicator: function(name, color) {
                    try {
                        const series = priceChart.addLineSeries({
                            color: color,
                            lineWidth: 2,
                            title: name,
                        });
                        indicatorSeries[name] = series;
                        console.log('Added indicator: ' + name);
                        return true;
                    } catch(e) {
                        console.error('Error adding indicator:', e);
                        return false;
                    }
                },

                // Remove indicator
                removeIndicator: function(name) {
                    try {
                        if (indicatorSeries[name]) {
                            priceChart.removeSeries(indicatorSeries[name]);
                            delete indicatorSeries[name];
                            console.log('Removed indicator: ' + name);
                            return true;
                        }
                        return false;
                    } catch(e) {
                        console.error('Error removing indicator:', e);
                        return false;
                    }
                },

                // Set indicator data
                setIndicatorData: function(name, data) {
                    try {
                        if (indicatorSeries[name]) {
                            indicatorSeries[name].setData(data);
                            console.log('Set data for indicator: ' + name);
                            return true;
                        }
                        return false;
                    } catch(e) {
                        console.error('Error setting indicator data:', e);
                        return false;
                    }
                },

                // Update indicator point
                updateIndicator: function(name, point) {
                    try {
                        if (indicatorSeries[name]) {
                            indicatorSeries[name].update(point);
                            return true;
                        }
                        return false;
                    } catch(e) {
                        console.error('Error updating indicator:', e);
                        return false;
                    }
                },

                // Create a new indicator panel (for Volume, RSI, MACD, etc.)
                createPanel: function(panelId, name, type, color, min, max) {
                    try {
                        // Check if panel already exists
                        if (panelCharts[panelId]) {
                            console.log('Panel ' + panelId + ' already exists');
                            return true;
                        }

                        // Create panel container
                        const container = document.getElementById('chart-container');
                        const panelDiv = document.createElement('div');
                        panelDiv.id = 'panel-' + panelId;
                        panelDiv.className = 'indicator-panel';

                        // Add header label
                        const header = document.createElement('div');
                        header.className = 'panel-header';
                        header.textContent = name;
                        panelDiv.appendChild(header);

                        container.appendChild(panelDiv);

                        // Use the same width as the price chart for alignment
                        const priceChartElement = document.getElementById('price-chart');
                        const chartWidth = priceChartElement ? priceChartElement.clientWidth : (panelDiv.clientWidth || 800);
                        const chartHeight = panelDiv.clientHeight || 200;

                        // Wait a frame for the browser to calculate flex layout
                        setTimeout(() => {
                            const actualWidth = priceChartElement ? priceChartElement.clientWidth : panelDiv.clientWidth;
                            const actualHeight = panelDiv.clientHeight || 200;

                            console.log('Resizing panel: ' + panelId + ' - width:', actualWidth, 'height:', actualHeight);

                            // Resize chart to match price chart width
                            if (panelCharts[panelId]) {
                                panelCharts[panelId].applyOptions({
                                    width: actualWidth,
                                    height: actualHeight
                                });
                            }
                        }, 0);

                        // Create chart in panel
                        const chart = LightweightCharts.createChart(panelDiv, {
                            width: chartWidth,
                            height: chartHeight,
                            layout: {
                                background: { color: '#0a0a0a' },
                                textColor: '#d1d4dc',
                            },
                            grid: {
                                vertLines: { color: 'rgba(70, 70, 70, 0.4)' },
                                horzLines: { color: 'rgba(70, 70, 70, 0.4)' },
                            },
                            crosshair: {
                                mode: LightweightCharts.CrosshairMode.Normal,
                            },
                            timeScale: {
                                timeVisible: true,
                                secondsVisible: false,
                                borderColor: '#485c7b',
                            },
                            rightPriceScale: {
                                borderColor: '#485c7b',
                                scaleMargins: {
                                    top: 0.1,
                                    bottom: 0.1,
                                },
                                minimumWidth: 60,  // Same width as price chart for alignment
                            },
                            // Horizontal pan/zoom happens only on the master price chart to avoid desync
                            handleScroll: {
                                mouseWheel: false,
                                pressedMouseMove: false,
                                horzTouchDrag: false,
                                vertTouchDrag: true  // Keep vertical drag for price scale
                            },
                            handleScale: {
                                axisPressedMouseMove: false,
                                mouseWheel: false,
                                pinch: false
                            },
                            kineticScroll: {
                                mouse: false,
                                touch: true
                            }
                        });

                        // Create series based on type
                        let series;
                        if (type === 'histogram') {
                            series = chart.addHistogramSeries({
                                color: color,
                                priceFormat: { type: 'volume' }
                            });
                        } else if (type === 'line') {
                            const seriesOptions = {
                                color: color,
                                lineWidth: 2,
                                priceScaleId: 'right'
                            };
                            if (min !== null && max !== null) {
                                seriesOptions.autoscaleInfoProvider = () => ({
                                    priceRange: {
                                        minValue: min,
                                        maxValue: max
                                    }
                                });
                            }
                            series = chart.addLineSeries(seriesOptions);
                        }

                        panelCharts[panelId] = chart;
                        panelSeries[panelId] = series;
                        window.allCharts.push(chart);

                        // Observe panel for resize events
                        if (window.chartResizeObserver) {
                            window.chartResizeObserver.observe(panelDiv);
                        }

                        // Sync new chart with master (price chart)
                        window.syncChartWithMaster(chart);

                        // Align price scale width with master
                        syncPriceScaleWidths();

                        // Update time scale visibility
                        window.updateTimeScaleVisibility();

                        console.log('Created panel: ' + panelId + ' (' + name + ')');
                        return true;
                    } catch(e) {
                        console.error('Error creating panel:', e);
                        return false;
                    }
                },

                // Remove an indicator panel
                removePanel: function(panelId) {
                    try {
                        if (!panelCharts[panelId]) {
                            return false;
                        }

                        // Remove chart
                        const chart = panelCharts[panelId];
                        const index = window.allCharts.indexOf(chart);
                        if (index > -1) {
                            window.allCharts.splice(index, 1);
                        }

                        chart.remove();
                        delete panelCharts[panelId];
                        delete panelSeries[panelId];

                        // Remove DOM element
                        const panel = document.getElementById('panel-' + panelId);
                        if (panel) {
                            // Unobserve panel
                            if (window.chartResizeObserver) {
                                window.chartResizeObserver.unobserve(panel);
                            }
                            panel.remove();
                        }

                        // Update time scale visibility
                        window.updateTimeScaleVisibility();

                        console.log('Removed panel: ' + panelId);
                        return true;
                    } catch(e) {
                        console.error('Error removing panel:', e);
                        return false;
                    }
                },

                // Set data for a panel
                setPanelData: function(panelId, data) {
                    try {
                        if (panelSeries[panelId]) {
                            panelSeries[panelId].setData(data);

                            // Force sync with master chart after setting data
                            if (panelCharts[panelId]) {
                                window.syncChartWithMaster(panelCharts[panelId]);
                            }

                            // Keep price scales aligned if value ranges changed
                            syncPriceScaleWidths();

                            console.log('Set data for panel: ' + panelId);
                            return true;
                        }
                        return false;
                    } catch(e) {
                        console.error('Error setting panel data:', e);
                        return false;
                    }
                },

                // Update panel data (single point)
                updatePanelData: function(panelId, point) {
                    try {
                        if (panelSeries[panelId]) {
                            panelSeries[panelId].update(point);
                            return true;
                        }
                        return false;
                    } catch(e) {
                        console.error('Error updating panel data:', e);
                        return false;
                    }
                },

                // Add additional series to an existing panel (for multi-series indicators like MACD)
                addPanelSeries: function(panelId, seriesKey, type, color, data) {
                    try {
                        if (!panelCharts[panelId]) {
                            console.error('Panel not found:', panelId);
                            return false;
                        }

                        const chart = panelCharts[panelId];
                        let series;

                        if (type === 'histogram') {
                            series = chart.addHistogramSeries({
                                color: color,
                                priceFormat: { type: 'volume' }
                            });
                        } else if (type === 'line') {
                            series = chart.addLineSeries({
                                color: color,
                                lineWidth: 2
                            });
                        }

                        // Store series with composite key
                        const fullKey = panelId + '_' + seriesKey;
                        panelSeries[fullKey] = series;

                        // Set data if provided
                        if (data) {
                            series.setData(data);
                        }

                        console.log('Added series ' + seriesKey + ' to panel ' + panelId);
                        return true;
                    } catch(e) {
                        console.error('Error adding panel series:', e);
                        return false;
                    }
                },

                // Set data for a specific series in a panel
                setPanelSeriesData: function(panelId, seriesKey, data) {
                    try {
                        const fullKey = panelId + '_' + seriesKey;
                        if (panelSeries[fullKey]) {
                            panelSeries[fullKey].setData(data);

                            // Force sync with master chart after setting data (only for first series)
                            if (seriesKey === 'macd' && panelCharts[panelId]) {
                                window.syncChartWithMaster(panelCharts[panelId]);
                            }

                            syncPriceScaleWidths();

                            console.log('Set data for panel series: ' + fullKey);
                            return true;
                        }
                        return false;
                    } catch(e) {
                        console.error('Error setting panel series data:', e);
                        return false;
                    }
                },

                // Add horizontal reference line to a panel (e.g., RSI 30/70)
                addPanelPriceLine: function(panelId, price, color, lineStyle, title) {
                    try {
                        if (!panelSeries[panelId]) {
                            console.error('Panel not found:', panelId);
                            return false;
                        }

                        const series = panelSeries[panelId];

                        // Map lineStyle string to LineStyle enum
                        let style = LightweightCharts.LineStyle.Dashed;
                        if (lineStyle === 'solid') {
                            style = LightweightCharts.LineStyle.Solid;
                        } else if (lineStyle === 'dotted') {
                            style = LightweightCharts.LineStyle.Dotted;
                        } else if (lineStyle === 'dashed') {
                            style = LightweightCharts.LineStyle.Dashed;
                        }

                        series.createPriceLine({
                            price: price,
                            color: color,
                            lineWidth: 1,
                            lineStyle: style,
                            axisLabelVisible: true,
                            title: title || ''
                        });

                        console.log('Added price line to panel ' + panelId + ' at ' + price);
                        return true;
                    } catch(e) {
                        console.error('Error adding panel price line:', e);
                        return false;
                    }
                },

                // Fit content for all charts
                fitContent: function() {
                    try {
                        window.allCharts.forEach(chart => {
                            chart.timeScale().fitContent();
                        });
                        console.log('Fit content (' + window.allCharts.length + ' charts)');
                    } catch(e) {
                        console.error('Error fitting content:', e);
                    }
                },

                // Clear all data
                clear: function() {
                    try {
                        candlestickSeries.setData([]);

                        // Clear overlay indicators
                        for (const name in indicatorSeries) {
                            priceChart.removeSeries(indicatorSeries[name]);
                        }
                        Object.keys(indicatorSeries).forEach(key => delete indicatorSeries[key]);

                        // Clear all panels
                        Object.keys(panelCharts).forEach(panelId => {
                            this.removePanel(panelId);
                        });

                        console.log('Cleared all data (price + all panels)');
                    } catch(e) {
                        console.error('Error clearing data:', e);
                    }
                }
            };

            console.log('chartAPI created successfully');
            console.log('Available API functions:', Object.keys(window.chartAPI));
            console.log('Chart initialization complete!');
            document.getElementById('status').textContent = 'Ready - waiting for data...';

            } catch(error) {
                console.error('[ERROR] CRITICAL ERROR during chart initialization:', error);
                console.error('[ERROR] Stack:', error.stack);
                document.getElementById('status').textContent = 'ERROR: ' + error.message;
                document.getElementById('status').style.color = '#ff0000';
            }
        } // End initializeCharts function

        // Call initialization after a short delay to ensure DOM is fully ready
        // Note: QWebEngineView.setHtml() doesn't fire DOMContentLoaded reliably
        console.log('[INIT] Scheduling initialization...');
        setTimeout(function() {
            console.log('[INIT] Timeout fired, DOM should be ready');
            console.log('[INIT] price-chart exists:', document.getElementById('price-chart') !== null);
            console.log('[INIT] status exists:', document.getElementById('status') !== null);
            initializeCharts();
        }, 50);  // 50ms delay to ensure DOM is ready
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
        self.symbol_combo.addItems(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ"])
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
            action.triggered.connect(lambda checked, a=action: self._on_indicator_toggled(a))
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

        toolbar.addSeparator()

        # Market status
        self.market_status_label = QLabel("Ready")
        self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
        toolbar.addWidget(self.market_status_label)

        return toolbar

    def _execute_js(self, script: str):
        """Execute JavaScript in the web view, queueing until chart is ready."""
        if self.page_loaded and self.chart_initialized:
            self.web_view.page().runJavaScript(script)
        else:
            # Queue command until both page load and chart initialization are done
            self.pending_js_commands.append(script)
            if not self.page_loaded:
                logger.debug("Page not loaded yet, queueing JS execution")
            else:
                logger.debug("Chart not initialized yet, queueing JS execution")

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

    def _update_indicators(self):
        """Update technical indicators on chart."""
        if self.data is None:
            return

        try:
            # Categorize indicators: Overlay (on price chart) vs Oscillator (separate panel)
            # Overlay indicators: SMA, EMA, BB (displayed on price chart)
            # Oscillators: RSI, MACD, STOCH, ATR (displayed in separate panel below)

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

            # Process each indicator
            for ind_id, action in self.indicator_actions.items():
                is_checked = action.isChecked()
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
                else:  # oscillator
                    ind_type, params, display_name, min_val, max_val = oscillator_configs[ind_id]

                if is_checked:
                    # Calculate indicator
                    config = IndicatorConfig(
                        indicator_type=ind_type,
                        params=params
                    )
                    result = self.indicator_engine.calculate(self.data, config)

                    # Convert to chart format
                    # Handle both Series (single line) and DataFrame (multiple lines)
                    is_multi_series = isinstance(result.values, pd.DataFrame) and ind_id == "MACD"

                    if is_multi_series:
                        # MACD has 3 series: MACD line, Signal line, Histogram
                        col_names = result.values.columns.tolist()
                        logger.info(f"MACD columns: {col_names}")

                        # Find columns
                        macd_col = signal_col = hist_col = None
                        for col in col_names:
                            col_lower = col.lower()
                            if 'macd' in col_lower and 'signal' not in col_lower and 'hist' not in col_lower:
                                macd_col = col
                            elif 'signal' in col_lower or 'macds' in col_lower:
                                signal_col = col
                            elif 'hist' in col_lower or 'macdh' in col_lower:
                                hist_col = col

                        # Prepare data for each series; align strictly with price bars to avoid truncation
                        macd_data = []
                        signal_data = []
                        hist_data = []

                        macd_series = result.values[macd_col] if macd_col else None
                        signal_series = result.values[signal_col] if signal_col else None
                        hist_series = result.values[hist_col] if hist_col else None

                        # Pad all bars, even when values are NaN, so zooming doesn't "shrink" the MACD length
                        for ts, macd_val, sig_val, hist_val in zip(
                            self.data.index,
                            macd_series.values if macd_series is not None else [None]*len(self.data),
                            signal_series.values if signal_series is not None else [None]*len(self.data),
                            hist_series.values if hist_series is not None else [None]*len(self.data),
                        ):
                            unix_time = int(ts.timestamp())

                            macd_data.append({
                                'time': unix_time,
                                'value': None if macd_val is None or pd.isna(macd_val) else float(macd_val)
                            })

                            signal_data.append({
                                'time': unix_time,
                                'value': None if sig_val is None or pd.isna(sig_val) else float(sig_val)
                            })

                            if hist_val is None or pd.isna(hist_val):
                                hist_data.append({'time': unix_time})
                            else:
                                hv = float(hist_val)
                                hist_data.append({
                                    'time': unix_time,
                                    'value': hv,
                                    'color': '#26a69a' if hv >= 0 else '#ef5350'
                                })

                        # Store all three data series
                        ind_data = {
                            'macd': macd_data,
                            'signal': signal_data,
                            'histogram': hist_data
                        }

                    elif isinstance(result.values, pd.DataFrame):
                        # Other multi-series indicators (Stochastic, BB, etc.)
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

                        ind_data = [
                            {'time': int(ts.timestamp()), 'value': float(val)}
                            for ts, val in zip(self.data.index, series_data.values)
                            if not pd.isna(val)
                        ]
                    else:
                        # Single series indicator (RSI, ATR, etc.)
                        series_data = result.values

                        ind_data = [
                            {'time': int(ts.timestamp()), 'value': float(val)}
                            for ts, val in zip(self.data.index, series_data.values)
                            if not pd.isna(val)
                        ]

                    # Add/update indicator
                    if ind_id not in self.active_indicators:
                        if is_overlay:
                            # Add as overlay on price chart
                            self._execute_js(f"window.chartAPI.addIndicator('{display_name}', '{color}');")
                        else:
                            # Oscillator - create panel directly in chart
                            panel_id = ind_id.lower()

                            if ind_id == "MACD":
                                # MACD: Create panel with histogram (will add lines separately)
                                js_min = 'null'
                                js_max = 'null'
                                self._execute_js(
                                    f"window.chartAPI.createPanel('{panel_id}', '{display_name}', 'histogram', '#26a69a', {js_min}, {js_max});"
                                )
                                # Add MACD line
                                self._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'macd', 'line', '#2962FF', null);")
                                # Add Signal line
                                self._execute_js(f"window.chartAPI.addPanelSeries('{panel_id}', 'signal', 'line', '#FF6D00', null);")
                                # Add zero line
                                self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'solid', '0');")
                            else:
                                # Other oscillators (RSI, STOCH, etc.)
                                chart_type = 'line'
                                js_min = 'null' if min_val is None else str(min_val)
                                js_max = 'null' if max_val is None else str(max_val)
                                self._execute_js(
                                    f"window.chartAPI.createPanel('{panel_id}', '{display_name}', '{chart_type}', '{color}', {js_min}, {js_max});"
                                )

                                # Add reference lines for specific indicators
                                if ind_id == "RSI":
                                    # RSI: 30 (oversold), 70 (overbought)
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 30, '#FF0000', 'dashed', 'Oversold');")
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 70, '#00FF00', 'dashed', 'Overbought');")
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 50, '#888888', 'dotted', 'Neutral');")
                                elif ind_id == "STOCH":
                                    # Stochastic: 20 (oversold), 80 (overbought)
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 20, '#FF0000', 'dashed', 'Oversold');")
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 80, '#00FF00', 'dashed', 'Overbought');")
                                elif ind_id == "CCI":
                                    # CCI: -100, +100
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', -100, '#FF0000', 'dashed', '-100');")
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 100, '#00FF00', 'dashed', '+100');")
                                    self._execute_js(f"window.chartAPI.addPanelPriceLine('{panel_id}', 0, '#888888', 'dotted', '0');")

                            logger.info(f"Created panel for {ind_id}")

                        self.active_indicators[ind_id] = True

                    # Update data
                    if is_overlay:
                        # Set data on price chart
                        ind_json = json.dumps(ind_data)
                        self._execute_js(f"window.chartAPI.setIndicatorData('{display_name}', {ind_json});")
                    else:
                        # Oscillator - set data on panel
                        panel_id = ind_id.lower()

                        if is_multi_series and ind_id == "MACD":
                            # MACD: Set data for all 3 series
                            macd_json = json.dumps(ind_data['macd'])
                            signal_json = json.dumps(ind_data['signal'])
                            hist_json = json.dumps(ind_data['histogram'])

                            # Set histogram data (main series)
                            self._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {hist_json});")
                            # Set MACD line data
                            self._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'macd', {macd_json});")
                            # Set Signal line data
                            self._execute_js(f"window.chartAPI.setPanelSeriesData('{panel_id}', 'signal', {signal_json});")
                        else:
                            # Regular oscillator - single series
                            ind_json = json.dumps(ind_data)
                            self._execute_js(f"window.chartAPI.setPanelData('{panel_id}', {ind_json});")

                elif ind_id in self.active_indicators:
                    # Remove indicator if unchecked
                    if is_overlay:
                        self._execute_js(f"window.chartAPI.removeIndicator('{display_name}');")
                    else:
                        # Oscillator - remove panel
                        panel_id = ind_id.lower()
                        self._execute_js(f"window.chartAPI.removePanel('{panel_id}');")
                        logger.info(f"Removed panel for {ind_id}")

                    del self.active_indicators[ind_id]

        except Exception as e:
            logger.error(f"Error updating indicators: {e}", exc_info=True)

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

        logger.info(f"Indicator {indicator_id} {'enabled' if is_checked else 'disabled'}")

        # Update indicators display
        self._update_indicators()

        # Update button style to show how many indicators are active
        self._update_indicators_button_badge()

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

            # Update current candle in real-time (Stock3 style)
            if not hasattr(self, '_current_candle_time'):
                # Initialize with current minute boundary
                now = datetime.now()
                self._current_candle_time = int(now.replace(second=0, microsecond=0).timestamp())
                self._current_candle_open = price
                self._current_candle_high = price
                self._current_candle_low = price
                self._current_candle_volume = 0

            # Check if we need a new candle (new minute)
            now = datetime.now()
            current_minute = int(now.replace(second=0, microsecond=0).timestamp())

            if current_minute > self._current_candle_time:
                # New candle - reset
                self._current_candle_time = current_minute
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

                timestamp = bar_data.get('timestamp', datetime.now())
                unix_time = int(timestamp.timestamp())

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

        self.live_streaming_enabled = self.live_stream_button.isChecked()

        if self.live_streaming_enabled:
            # Start live stream
            logger.info(f"Starting live stream for {self.current_symbol}...")
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
            # Start real-time stream via HistoryManager
            success = await self.history_manager.start_realtime_stream([self.current_symbol])

            if success:
                logger.info(f"✓ Live stream started for {self.current_symbol}")
                self.market_status_label.setText(f"🟢 Live: {self.current_symbol}")
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
        """Stop live streaming."""
        if not self.history_manager:
            return

        try:
            await self.history_manager.stop_realtime_stream()
            logger.info("✓ Live stream stopped")
            self.market_status_label.setText("Ready")
            self.market_status_label.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")

        except Exception as e:
            logger.error(f"Error stopping live stream: {e}")

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
            from datetime import timedelta
            from src.core.market_data.history_provider import DataRequest, DataSource, Timeframe

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

            # Map provider
            provider_source = None
            if data_provider:
                provider_map = {
                    "database": DataSource.DATABASE,
                    "alpaca": DataSource.ALPACA,
                    "yahoo": DataSource.YAHOO,
                    "alpha_vantage": DataSource.ALPHA_VANTAGE,
                }
                provider_source = provider_map.get(data_provider)
            else:
                # Default: Use Alpaca for live data (avoid stale database)
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

            logger.info(f"Loading {symbol} - Candles: {self.current_timeframe}, Period: {self.current_period} ({lookback_days} days)")

            # Fetch data
            request = DataRequest(
                symbol=symbol,
                start_date=datetime.now() - timedelta(days=lookback_days),
                end_date=datetime.now(),
                timeframe=timeframe,
                source=provider_source
            )

            bars, source_used = await self.history_manager.fetch_data(request)

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

            # Restart live stream if enabled
            if self.live_streaming_enabled:
                logger.info(f"Switching live stream to new symbol: {symbol}")
                await self._start_live_stream()

        except Exception as e:
            logger.error(f"Error loading symbol: {e}", exc_info=True)
            self.market_status_label.setText(f"Error: {str(e)[:30]}")
            self.market_status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
