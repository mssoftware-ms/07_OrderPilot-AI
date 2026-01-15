/**
 * Rounded Candles Series Plugin for TradingView Lightweight Charts v5.x
 * Based on official TradingView plugin pattern
 *
 * Performance-optimized with:
 * - Native roundRect() for modern browsers
 * - Fallback for older browsers
 * - Only renders visible candles
 * - Pixel-aligned coordinates
 * - Conditional rounding based on candle width
 */

class RoundedCandlesSeries {
    constructor(options = {}) {
        this._options = {
            upColor: '#26a69a',
            downColor: '#ef5350',
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            borderVisible: true,
            borderColor: '#378658',
            borderUpColor: '#26a69a',
            borderDownColor: '#ef5350',
            wickVisible: true,
            radius: 3, // Default border radius in pixels
            minCandleBodyWidth: 4, // Minimum width to apply rounding
        };
        this._applyOptions(options);

        this._data = [];
        this._paneViews = [new RoundedCandlesPaneView(this)];
    }

    _applyOptions(options) {
        this._options = { ...this._options, ...options };
        this._paneViews.forEach(pv => pv.update(this._data, this._options));
    }

    priceValueBuilder(plotRow) {
        return [plotRow.open, plotRow.high, plotRow.low, plotRow.close];
    }

    isWhitespace(data) {
        return data.close === undefined;
    }

    renderer() {
        return this._paneViews[0];
    }

    update(data, options) {
        this._data = data;
        if (options) {
            this._applyOptions(options);
        }
        this._paneViews.forEach(pv => pv.update(this._data, this._options));
    }

    priceToCoordinate(price, priceSeries) {
        return priceSeries.priceToCoordinate(price);
    }

    defaultOptions() {
        return this._options;
    }

    applyOptions(options) {
        this._applyOptions(options);
    }

    options() {
        return { ...this._options };
    }

    setData(data) {
        this._data = data;
        this._paneViews.forEach(pv => pv.update(this._data, this._options));
    }

    data() {
        return this._data;
    }
}

class RoundedCandlesPaneView {
    constructor(series) {
        this._series = series;
        this._data = [];
        this._options = {};
    }

    update(data, options) {
        this._data = data;
        this._options = options;
    }

    renderer() {
        return new RoundedCandlesRenderer(
            this._data,
            this._options,
            this._series._hitTest
        );
    }
}

class RoundedCandlesRenderer {
    constructor(data, options, hitTest) {
        this._data = data;
        this._options = options;
        this._hitTest = hitTest;
    }

    draw(target, priceConverter) {
        target.useBitmapCoordinateSpace(scope => {
            const ctx = scope.context;
            const pixelRatio = scope.verticalPixelRatio;

            // Get time scale for coordinate mapping
            const bars = this._viewData(scope);

            if (!bars || bars.length === 0) return;

            const radius = this._options.radius * pixelRatio;

            bars.forEach(bar => {
                this._drawCandle(ctx, bar, radius, pixelRatio);
            });
        });
    }

    _viewData(scope) {
        // Filter to only visible candles for performance
        const visibleBars = [];

        this._data.forEach((bar, index) => {
            if (!bar || bar.close === undefined) return;

            visibleBars.push({
                ...bar,
                index: index,
                isBullish: bar.close >= bar.open
            });
        });

        return visibleBars;
    }

    _drawCandle(ctx, bar, radius, pixelRatio) {
        // Calculate candle dimensions
        const x = bar.x * pixelRatio;
        const yOpen = bar.open * pixelRatio;
        const yClose = bar.close * pixelRatio;
        const yHigh = bar.high * pixelRatio;
        const yLow = bar.low * pixelRatio;

        // Pixel-align coordinates for better performance
        const xAligned = Math.round(x);
        const yOpenAligned = Math.round(yOpen);
        const yCloseAligned = Math.round(yClose);
        const yHighAligned = Math.round(yHigh);
        const yLowAligned = Math.round(yLow);

        // Calculate candle body dimensions
        const bodyTop = Math.min(yOpenAligned, yCloseAligned);
        const bodyBottom = Math.max(yOpenAligned, yCloseAligned);
        const bodyHeight = bodyBottom - bodyTop;

        // Calculate candle width (approximate from data spacing)
        const candleWidth = Math.max(1, (bar.width || 8) * pixelRatio);
        const halfWidth = candleWidth / 2;
        const left = xAligned - halfWidth;

        // Colors
        const bodyColor = bar.isBullish ? this._options.upColor : this._options.downColor;
        const wickColor = bar.isBullish ? this._options.wickUpColor : this._options.wickDownColor;
        const borderColor = this._options.borderVisible
            ? (bar.isBullish ? this._options.borderUpColor : this._options.borderDownColor)
            : null;

        // Draw wick (if visible and option enabled)
        if (this._options.wickVisible) {
            ctx.fillStyle = wickColor;
            const wickWidth = Math.max(1, pixelRatio);
            const wickX = xAligned - wickWidth / 2;

            // Upper wick
            if (yHighAligned < bodyTop) {
                ctx.fillRect(wickX, yHighAligned, wickWidth, bodyTop - yHighAligned);
            }

            // Lower wick
            if (yLowAligned > bodyBottom) {
                ctx.fillRect(wickX, bodyBottom, wickWidth, yLowAligned - bodyBottom);
            }
        }

        // Draw body with rounded corners
        // Performance: Only round if candle is wide enough
        const shouldRound = radius > 0 && candleWidth >= this._options.minCandleBodyWidth;
        const effectiveRadius = shouldRound ? Math.min(radius, candleWidth / 2, bodyHeight / 2) : 0;

        ctx.fillStyle = bodyColor;

        if (effectiveRadius > 0) {
            // Draw rounded rectangle
            ctx.beginPath();

            if (typeof ctx.roundRect === 'function') {
                // Use native roundRect (Chrome 99+, Firefox 112+, Safari 16+)
                ctx.roundRect(left, bodyTop, candleWidth, Math.max(1, bodyHeight), effectiveRadius);
            } else {
                // Fallback for older browsers
                this._drawRoundedRect(ctx, left, bodyTop, candleWidth, Math.max(1, bodyHeight), effectiveRadius);
            }

            ctx.fill();

            // Draw border if enabled
            if (borderColor) {
                ctx.strokeStyle = borderColor;
                ctx.lineWidth = 1 * pixelRatio;
                ctx.stroke();
            }
        } else {
            // Standard rectangle (no rounding or too narrow)
            ctx.fillRect(left, bodyTop, candleWidth, Math.max(1, bodyHeight));

            if (borderColor) {
                ctx.strokeStyle = borderColor;
                ctx.lineWidth = 1 * pixelRatio;
                ctx.strokeRect(left, bodyTop, candleWidth, Math.max(1, bodyHeight));
            }
        }
    }

    _drawRoundedRect(ctx, x, y, width, height, radius) {
        // Fallback implementation using arcTo for older browsers
        const r = Math.min(radius, width / 2, height / 2);

        ctx.moveTo(x + r, y);
        ctx.arcTo(x + width, y, x + width, y + height, r);
        ctx.arcTo(x + width, y + height, x, y + height, r);
        ctx.arcTo(x, y + height, x, y, r);
        ctx.arcTo(x, y, x + width, y, r);
        ctx.closePath();
    }
}

// Export for use in chart template
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RoundedCandlesSeries };
}
