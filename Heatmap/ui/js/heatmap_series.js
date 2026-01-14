/**
 * Lightweight Charts Heatmap Series Plugin
 *
 * Custom series for rendering liquidation heatmap as background layer.
 * Based on Lightweight Charts custom series API.
 */

class HeatmapSeries {
    constructor(chart, options = {}) {
        this.chart = chart;
        this.options = {
            opacity: options.opacity || 0.5,
            palette: options.palette || 'hot',
            cellWidth: options.cellWidth || 'auto',
            cellHeight: options.cellHeight || 'auto',
            ...options
        };

        this.data = [];
        this.series = null;
        this.visible = true;

        // Color palettes
        this.palettes = {
            hot: this._generateHotPalette(),
            cool: this._generateCoolPalette(),
            viridis: this._generateViridis(),
            plasma: this._generatePlasma()
        };
    }

    /**
     * Initialize the heatmap series in the chart.
     * Must be called before setting data.
     */
    initialize() {
        // Create custom series using Lightweight Charts API
        this.series = this.chart.addCustomSeries({
            priceFormat: {
                type: 'price',
                precision: 2,
                minMove: 0.01,
            },
        }, {
            renderer: (ctx, data, options) => this._render(ctx, data, options),
            update: (data) => this._prepareData(data),
        });

        console.log('Heatmap series initialized');
    }

    /**
     * Set complete heatmap data (replaces existing).
     */
    setData(cells) {
        if (!this.series) {
            console.error('Heatmap series not initialized');
            return;
        }

        this.data = cells;
        this.series.setData(cells);
    }

    /**
     * Append cells to existing data (incremental update).
     */
    appendData(cells) {
        if (!this.series) {
            console.error('Heatmap series not initialized');
            return;
        }

        // Merge new cells with existing data
        for (const cell of cells) {
            // Check if cell already exists
            const existingIndex = this.data.findIndex(
                c => c.time === cell.time && c.price === cell.price
            );

            if (existingIndex >= 0) {
                // Update existing cell
                this.data[existingIndex] = cell;
            } else {
                // Add new cell
                this.data.push(cell);
            }
        }

        // Sort by time
        this.data.sort((a, b) => a.time - b.time);

        this.series.setData(this.data);
    }

    /**
     * Clear all heatmap data.
     */
    clear() {
        if (!this.series) {
            return;
        }

        this.data = [];
        this.series.setData([]);
    }

    /**
     * Set visibility of heatmap.
     */
    setVisible(visible) {
        this.visible = visible;

        if (this.series) {
            this.series.applyOptions({
                visible: visible
            });
        }
    }

    /**
     * Update heatmap visual settings.
     */
    updateSettings(settings) {
        if (settings.opacity !== undefined) {
            this.options.opacity = settings.opacity;
        }
        if (settings.palette !== undefined) {
            this.options.palette = settings.palette;
        }

        // Trigger redraw
        if (this.series && this.data.length > 0) {
            this.series.setData(this.data);
        }
    }

    /**
     * Render heatmap cells on canvas.
     * Called by Lightweight Charts for each frame.
     */
    _render(ctx, data, options) {
        if (!this.visible || !data || data.length === 0) {
            return;
        }

        const timeScale = this.chart.timeScale();
        const priceScale = this.series.priceScale();

        const palette = this.palettes[this.options.palette] || this.palettes.hot;

        for (const cell of data) {
            // Convert time and price to pixel coordinates
            const x = timeScale.timeToCoordinate(cell.time);
            const y = priceScale.priceToCoordinate(cell.price);

            if (x === null || y === null) {
                continue;
            }

            // Calculate cell dimensions
            const cellWidth = this._calculateCellWidth(timeScale);
            const cellHeight = this._calculateCellHeight(priceScale);

            // Get color from palette based on intensity
            const color = this._getColor(cell.value, palette);

            // Draw cell
            ctx.fillStyle = color;
            ctx.fillRect(
                x - cellWidth / 2,
                y - cellHeight / 2,
                cellWidth,
                cellHeight
            );
        }
    }

    /**
     * Prepare data for rendering (called by Lightweight Charts).
     */
    _prepareData(data) {
        return data.map(cell => ({
            time: cell.time,
            price: cell.price,
            value: cell.value,
        }));
    }

    /**
     * Calculate cell width in pixels based on time scale.
     */
    _calculateCellWidth(timeScale) {
        if (this.options.cellWidth !== 'auto') {
            return this.options.cellWidth;
        }

        // Estimate based on visible range
        const visibleRange = timeScale.getVisibleRange();
        if (!visibleRange) {
            return 5;
        }

        const chartWidth = this.chart.chartElement().clientWidth;
        const timeRange = visibleRange.to - visibleRange.from;
        const secondsPerPixel = timeRange / chartWidth;

        // Aim for ~2-3 pixels per cell
        return Math.max(2, Math.min(10, 60 / secondsPerPixel));
    }

    /**
     * Calculate cell height in pixels based on price scale.
     */
    _calculateCellHeight(priceScale) {
        if (this.options.cellHeight !== 'auto') {
            return this.options.cellHeight;
        }

        // Estimate based on visible range
        const visibleRange = priceScale.getVisibleRange();
        if (!visibleRange) {
            return 3;
        }

        const chartHeight = this.chart.chartElement().clientHeight;
        const priceRange = visibleRange.to - visibleRange.from;
        const pricePerPixel = priceRange / chartHeight;

        // Aim for ~2-3 pixels per cell
        return Math.max(2, Math.min(10, 10 / pricePerPixel));
    }

    /**
     * Get RGBA color from palette based on intensity.
     */
    _getColor(intensity, palette) {
        const index = Math.floor(intensity * (palette.length - 1));
        const color = palette[Math.max(0, Math.min(index, palette.length - 1))];

        const alpha = this.options.opacity * intensity;

        return `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`;
    }

    /**
     * Generate hot color palette (red → orange → yellow).
     */
    _generateHotPalette() {
        const palette = [];
        const levels = 256;

        for (let i = 0; i < levels; i++) {
            const t = i / (levels - 1);

            if (t < 0.33) {
                // Dark red → red
                palette.push({ r: Math.floor(255 * (t / 0.33)), g: 0, b: 0 });
            } else if (t < 0.66) {
                // Red → orange
                palette.push({ r: 255, g: Math.floor(255 * ((t - 0.33) / 0.33)), b: 0 });
            } else {
                // Orange → yellow
                palette.push({ r: 255, g: 255, b: Math.floor(255 * ((t - 0.66) / 0.34)) });
            }
        }

        return palette;
    }

    /**
     * Generate cool color palette (blue → cyan → white).
     */
    _generateCoolPalette() {
        const palette = [];
        const levels = 256;

        for (let i = 0; i < levels; i++) {
            const t = i / (levels - 1);
            palette.push({
                r: Math.floor(255 * t),
                g: Math.floor(255 * t),
                b: 255
            });
        }

        return palette;
    }

    /**
     * Generate viridis palette (approximation).
     */
    _generateViridis() {
        const palette = [];
        const levels = 256;

        for (let i = 0; i < levels; i++) {
            const t = i / (levels - 1);
            palette.push({
                r: Math.floor(255 * (0.267 + 0.575 * t)),
                g: Math.floor(255 * (0.005 + 0.907 * t)),
                b: Math.floor(255 * (0.329 - 0.180 * t))
            });
        }

        return palette;
    }

    /**
     * Generate plasma palette (approximation).
     */
    _generatePlasma() {
        const palette = [];
        const levels = 256;

        for (let i = 0; i < levels; i++) {
            const t = i / (levels - 1);
            palette.push({
                r: Math.floor(255 * (0.050 + 0.950 * t)),
                g: Math.floor(255 * (0.030 + 0.790 * t - 0.360 * t * t)),
                b: Math.floor(255 * (0.528 - 0.530 * t))
            });
        }

        return palette;
    }
}

// Global API for Python bridge
let heatmapInstance = null;

window.initializeHeatmap = function(options) {
    if (!window.chart) {
        console.error('Chart not found, ensure Lightweight Charts is initialized');
        return false;
    }

    heatmapInstance = new HeatmapSeries(window.chart, options);
    heatmapInstance.initialize();
    return true;
};

window.setHeatmapData = function(cells) {
    if (!heatmapInstance) {
        console.error('Heatmap not initialized');
        return false;
    }

    heatmapInstance.setData(cells);
    return true;
};

window.appendHeatmapCells = function(cells) {
    if (!heatmapInstance) {
        console.error('Heatmap not initialized');
        return false;
    }

    heatmapInstance.appendData(cells);
    return true;
};

window.setHeatmapVisible = function(visible) {
    if (!heatmapInstance) {
        console.error('Heatmap not initialized');
        return false;
    }

    heatmapInstance.setVisible(visible);
    return true;
};

window.updateHeatmapSettings = function(settings) {
    if (!heatmapInstance) {
        console.error('Heatmap not initialized');
        return false;
    }

    heatmapInstance.updateSettings(settings);
    return true;
};

window.clearHeatmap = function() {
    if (!heatmapInstance) {
        console.error('Heatmap not initialized');
        return false;
    }

    heatmapInstance.clear();
    return true;
};

console.log('Heatmap series plugin loaded');
