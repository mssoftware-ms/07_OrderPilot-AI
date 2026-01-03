"""JavaScript code for Zone Primitives in Lightweight Charts.

This module provides the JavaScript classes needed to render
support/resistance zones as semi-transparent rectangles on the chart.

The code is injected into the chart HTML template.
"""

from __future__ import annotations

# JavaScript code for zone primitive rendering in Lightweight Charts v5
ZONE_PRIMITIVE_JS = """
// ============================================================
// Zone Primitive Classes for Lightweight Charts
// Renders semi-transparent rectangles for Support/Resistance zones
// ============================================================

class ZonePrimitive {
    /**
     * Zone data container for the primitive.
     * @param {string} id - Unique zone identifier
     * @param {number} startTime - Start timestamp (Unix seconds)
     * @param {number} endTime - End timestamp (Unix seconds)
     * @param {number} topPrice - Upper price boundary
     * @param {number} bottomPrice - Lower price boundary
     * @param {string} fillColor - Fill color (rgba)
     * @param {string} borderColor - Border color (solid)
     * @param {string} label - Optional label text
     * @param {boolean} isLocked - Whether zone is locked (prevent editing)
     */
    constructor(id, startTime, endTime, topPrice, bottomPrice, fillColor, borderColor, label, isLocked) {
        this.id = id;
        this.startTime = startTime;
        this.endTime = endTime;
        this.topPrice = topPrice;
        this.bottomPrice = bottomPrice;
        this.fillColor = fillColor;
        this.borderColor = borderColor;
        this.label = label || '';
        this.isLocked = isLocked || false;
        this._paneViews = [new ZonePaneView(this)];
    }

    updateData(startTime, endTime, topPrice, bottomPrice) {
        this.startTime = startTime;
        this.endTime = endTime;
        this.topPrice = topPrice;
        this.bottomPrice = bottomPrice;
    }

    paneViews() {
        return this._paneViews;
    }

    updateAllViews() {
        this._paneViews.forEach(pv => pv.update());
    }

    attached(param) {
        this._chart = param.chart;
        this._series = param.series;
        this._requestUpdate = param.requestUpdate;
        this.updateAllViews();
    }

    detached() {
        this._chart = null;
        this._series = null;
        this._requestUpdate = null;
    }

    requestUpdate() {
        if (this._requestUpdate) {
            this._requestUpdate();
        }
    }
}

class ZonePaneView {
    /**
     * Pane view that handles coordinate conversion and rendering.
     * @param {ZonePrimitive} source - The zone data source
     */
    constructor(source) {
        this._source = source;
        this._renderer = new ZoneRenderer();
    }

    update() {
        const source = this._source;
        if (!source._series || !source._chart) {
            return;
        }

        const series = source._series;
        const chart = source._chart;
        const timeScale = chart.timeScale();

        // Convert time to x coordinates
        const x1 = timeScale.timeToCoordinate(source.startTime);
        const x2 = timeScale.timeToCoordinate(source.endTime);

        // Convert price to y coordinates
        const y1 = series.priceToCoordinate(source.topPrice);
        const y2 = series.priceToCoordinate(source.bottomPrice);

        // Check if zone is visible
        if (x1 === null || x2 === null || y1 === null || y2 === null) {
            this._renderer.setData(null);
            return;
        }

        this._renderer.setData({
            x: Math.min(x1, x2),
            y: Math.min(y1, y2),
            width: Math.abs(x2 - x1),
            height: Math.abs(y2 - y1),
            fillColor: source.fillColor,
            borderColor: source.borderColor,
            label: source.label,
            isLocked: source.isLocked
        });
    }

    renderer() {
        return this._renderer;
    }

    zOrder() {
        return 'bottom';
    }
}

class ZoneRenderer {
    /**
     * Canvas renderer for zone rectangles.
     */
    constructor() {
        this._data = null;
    }

    setData(data) {
        this._data = data;
    }

    draw(target) {
        if (!this._data) {
            return;
        }

        const { x, y, width, height, fillColor, borderColor, label, isLocked } = this._data;

        target.useBitmapCoordinateSpace(scope => {
            const ctx = scope.context;
            const scaledX = Math.round(x * scope.horizontalPixelRatio);
            const scaledY = Math.round(y * scope.verticalPixelRatio);
            const scaledWidth = Math.round(width * scope.horizontalPixelRatio);
            const scaledHeight = Math.round(height * scope.verticalPixelRatio);

            // Draw fill
            ctx.fillStyle = fillColor;
            ctx.fillRect(scaledX, scaledY, scaledWidth, scaledHeight);

            // Draw border
            ctx.strokeStyle = borderColor;
            ctx.lineWidth = 1;
            ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

            // Draw label if present
            if (label) {
                ctx.fillStyle = borderColor;
                ctx.font = `${Math.round(11 * scope.verticalPixelRatio)}px sans-serif`;
                ctx.textBaseline = 'top';
                ctx.fillText(label, scaledX + 4, scaledY + 4);
            }

            // Draw lock icon if locked
            if (isLocked) {
                ctx.fillStyle = borderColor;
                ctx.font = `${Math.round(16 * scope.verticalPixelRatio)}px sans-serif`;
                ctx.textBaseline = 'top';
                // Draw lock icon (🔒) in top-right corner
                ctx.fillText('🔒', scaledX + scaledWidth - 25, scaledY + 4);
            }
        });
    }
}

// ============================================================
// Zone Manager - handles all zones on the chart
// ============================================================

class ChartZoneManager {
    constructor(chart, series) {
        this._chart = chart;
        this._series = series;
        this._zones = new Map();
    }

    /**
     * Add a new zone to the chart.
     * @param {string} id - Unique zone ID
     * @param {number} startTime - Start timestamp
     * @param {number} endTime - End timestamp
     * @param {number} topPrice - Upper price
     * @param {number} bottomPrice - Lower price
     * @param {string} fillColor - Fill color
     * @param {string} borderColor - Border color
     * @param {string} label - Optional label
     * @returns {boolean} Success status
     */
    addZone(id, startTime, endTime, topPrice, bottomPrice, fillColor, borderColor, label) {
        if (this._zones.has(id)) {
            console.warn(`Zone ${id} already exists, updating instead`);
            return this.updateZone(id, startTime, endTime, topPrice, bottomPrice);
        }

        const zone = new ZonePrimitive(
            id, startTime, endTime, topPrice, bottomPrice,
            fillColor, borderColor, label
        );

        this._series.attachPrimitive(zone);
        this._zones.set(id, zone);
        console.log(`Zone added: ${id}`);
        return true;
    }

    /**
     * Update an existing zone.
     * @param {string} id - Zone ID
     * @param {number} startTime - New start timestamp
     * @param {number} endTime - New end timestamp
     * @param {number} topPrice - New upper price
     * @param {number} bottomPrice - New lower price
     * @returns {boolean} Success status
     */
    updateZone(id, startTime, endTime, topPrice, bottomPrice) {
        const zone = this._zones.get(id);
        if (!zone) {
            console.warn(`Zone ${id} not found for update`);
            return false;
        }

        zone.updateData(startTime, endTime, topPrice, bottomPrice);
        zone.requestUpdate();
        console.log(`Zone updated: ${id}`);
        return true;
    }

    /**
     * Remove a zone from the chart.
     * @param {string} id - Zone ID to remove
     * @returns {boolean} Success status
     */
    removeZone(id) {
        const zone = this._zones.get(id);
        if (!zone) {
            console.warn(`Zone ${id} not found for removal`);
            return false;
        }

        this._series.detachPrimitive(zone);
        this._zones.delete(id);
        console.log(`Zone removed: ${id}`);
        return true;
    }

    /**
     * Remove all zones from the chart.
     */
    clearZones() {
        for (const [id, zone] of this._zones) {
            this._series.detachPrimitive(zone);
        }
        this._zones.clear();
        console.log('All zones cleared');
    }

    /**
     * Get all zone IDs.
     * @returns {string[]} Array of zone IDs
     */
    getZoneIds() {
        return Array.from(this._zones.keys());
    }

    /**
     * Check if a zone exists.
     * @param {string} id - Zone ID
     * @returns {boolean} Exists status
     */
    hasZone(id) {
        return this._zones.has(id);
    }

    /**
     * Get zone count.
     * @returns {number} Number of zones
     */
    getZoneCount() {
        return this._zones.size;
    }
}

// Export for use in chart initialization
window.ZonePrimitive = ZonePrimitive;
window.ZonePaneView = ZonePaneView;
window.ZoneRenderer = ZoneRenderer;
window.ChartZoneManager = ChartZoneManager;
"""

# API extension code to add zone methods to window.chartAPI
ZONE_API_EXTENSION_JS = """
// ============================================================
// Zone API Extensions for window.chartAPI
// ============================================================

(function() {
    // Initialize zone manager when chart is ready
    let zoneManager = null;

    function ensureZoneManager() {
        if (!zoneManager && window.chart && window.mainSeries) {
            zoneManager = new ChartZoneManager(window.chart, window.mainSeries);
            window.zoneManager = zoneManager;
        }
        return zoneManager;
    }

    // Extend chartAPI with zone methods
    if (!window.chartAPI) {
        window.chartAPI = {};
    }

    window.chartAPI.addZone = function(id, startTime, endTime, topPrice, bottomPrice, fillColor, borderColor, label) {
        const mgr = ensureZoneManager();
        if (!mgr) {
            console.error('Zone manager not initialized');
            return false;
        }
        return mgr.addZone(id, startTime, endTime, topPrice, bottomPrice, fillColor, borderColor, label || '');
    };

    window.chartAPI.updateZone = function(id, startTime, endTime, topPrice, bottomPrice) {
        const mgr = ensureZoneManager();
        if (!mgr) {
            console.error('Zone manager not initialized');
            return false;
        }
        return mgr.updateZone(id, startTime, endTime, topPrice, bottomPrice);
    };

    window.chartAPI.removeZone = function(id) {
        const mgr = ensureZoneManager();
        if (!mgr) {
            console.error('Zone manager not initialized');
            return false;
        }
        return mgr.removeZone(id);
    };

    window.chartAPI.clearZones = function() {
        const mgr = ensureZoneManager();
        if (!mgr) {
            console.error('Zone manager not initialized');
            return;
        }
        mgr.clearZones();
    };

    window.chartAPI.getZoneIds = function() {
        const mgr = ensureZoneManager();
        if (!mgr) {
            return [];
        }
        return mgr.getZoneIds();
    };

    window.chartAPI.hasZone = function(id) {
        const mgr = ensureZoneManager();
        if (!mgr) {
            return false;
        }
        return mgr.hasZone(id);
    };

    window.chartAPI.getZoneCount = function() {
        const mgr = ensureZoneManager();
        if (!mgr) {
            return 0;
        }
        return mgr.getZoneCount();
    };

    console.log('Zone API extensions loaded');
})();
"""


def get_zone_javascript() -> str:
    """Get complete JavaScript code for zone functionality.

    Returns:
        Complete JavaScript code including primitives and API extensions.
    """
    return ZONE_PRIMITIVE_JS + "\n\n" + ZONE_API_EXTENSION_JS
