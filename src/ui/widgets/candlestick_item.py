"""Shared Candlestick Item Component.

This module provides a reusable candlestick graphics item for PyQtGraph-based charts,
eliminating code duplication across different chart implementations.
"""

import logging
from typing import List, Tuple, Optional

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    logging.warning("PyQtGraph not available. Candlestick functionality will be limited.")

logger = logging.getLogger(__name__)


class CandlestickItem(pg.GraphicsObject):
    """Custom GraphicsObject for drawing candlestick charts.

    This class provides a reusable candlestick implementation that can be used
    across different chart widgets to eliminate code duplication.
    """

    def __init__(self):
        """Initialize candlestick item."""
        if not PYQTGRAPH_AVAILABLE:
            raise ImportError("PyQtGraph is required for candlestick charts")

        super().__init__()
        self.data: List[Tuple[float, float, float, float, float]] = []
        self.picture: Optional[pg.QtGui.QPicture] = None
        self._colors = {
            'up': pg.mkColor(0, 255, 0, 200),      # Green for bullish candles
            'down': pg.mkColor(255, 0, 0, 200),    # Red for bearish candles
            'wick': pg.mkColor(255, 255, 255, 255)  # White for wicks
        }
        self.generatePicture()

    def set_data(self, data: List[Tuple[float, float, float, float, float]]):
        """Set candlestick data.

        Args:
            data: List of tuples containing (timestamp, open, high, low, close)
        """
        self.data = data
        self.generatePicture()
        self.informViewBoundsChanged()

    def set_colors(self, up_color=None, down_color=None, wick_color=None):
        """Set custom colors for candlesticks.

        Args:
            up_color: Color for bullish candles
            down_color: Color for bearish candles
            wick_color: Color for wicks
        """
        if up_color:
            self._colors['up'] = pg.mkColor(up_color)
        if down_color:
            self._colors['down'] = pg.mkColor(down_color)
        if wick_color:
            self._colors['wick'] = pg.mkColor(wick_color)

        # Regenerate with new colors
        if self.data:
            self.generatePicture()

    def generatePicture(self):
        """Generate the candlestick picture."""
        self.picture = pg.QtGui.QPicture()

        if not self.data:
            return

        painter = pg.QtGui.QPainter(self.picture)
        painter.setPen(pg.mkPen(self._colors['wick']))

        for t, open_price, high, low, close in self.data:
            try:
                self._draw_candlestick(painter, t, open_price, high, low, close)
            except Exception as e:
                logger.warning(f"Error drawing candlestick at time {t}: {e}")
                continue

        painter.end()

    def _draw_candlestick(self, painter, t: float, open_price: float,
                         high: float, low: float, close: float):
        """Draw a single candlestick.

        Args:
            painter: QPainter instance
            t: Timestamp/x-coordinate
            open_price: Opening price
            high: High price
            low: Low price
            close: Closing price
        """
        # Determine candle color based on price movement
        is_bullish = close > open_price
        body_color = self._colors['up'] if is_bullish else self._colors['down']

        # Set body color
        painter.setBrush(pg.QtGui.QBrush(body_color))
        painter.setPen(pg.mkPen(body_color))

        # Calculate candle dimensions
        candle_width = 0.3
        body_top = max(open_price, close)
        body_bottom = min(open_price, close)

        # Draw candle body (rectangle)
        if body_top != body_bottom:  # Avoid zero-height rectangles
            body_rect = pg.QtCore.QRectF(
                t - candle_width/2, body_bottom,
                candle_width, body_top - body_bottom
            )
            painter.drawRect(body_rect)
        else:
            # Doji case - draw a line
            painter.drawLine(
                pg.QtCore.QPointF(t - candle_width/2, open_price),
                pg.QtCore.QPointF(t + candle_width/2, open_price)
            )

        # Draw wicks (high/low lines)
        painter.setPen(pg.mkPen(self._colors['wick']))

        # Upper wick
        if high > body_top:
            painter.drawLine(
                pg.QtCore.QPointF(t, body_top),
                pg.QtCore.QPointF(t, high)
            )

        # Lower wick
        if low < body_bottom:
            painter.drawLine(
                pg.QtCore.QPointF(t, body_bottom),
                pg.QtCore.QPointF(t, low)
            )

    def paint(self, p, *args):
        """Paint the candlestick chart."""
        if self.picture:
            p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        """Return the bounding rectangle of the candlestick data."""
        if not self.data:
            return pg.QtCore.QRectF()

        # Find data bounds
        times = [item[0] for item in self.data]
        highs = [item[2] for item in self.data]
        lows = [item[3] for item in self.data]

        if not times or not highs or not lows:
            return pg.QtCore.QRectF()

        min_time, max_time = min(times), max(times)
        min_price, max_price = min(lows), max(highs)

        # Add some padding
        padding = 0.5
        return pg.QtCore.QRectF(
            min_time - padding, min_price,
            max_time - min_time + 2*padding, max_price - min_price
        )

    def clear(self):
        """Clear all candlestick data."""
        self.data = []
        self.generatePicture()
        self.informViewBoundsChanged()

    def get_data_count(self) -> int:
        """Get the number of candlesticks."""
        return len(self.data)

    def is_empty(self) -> bool:
        """Check if the candlestick item has no data."""
        return len(self.data) == 0


# Convenience function for backward compatibility
def create_candlestick_item() -> CandlestickItem:
    """Create a new CandlestickItem instance.

    Returns:
        CandlestickItem: A new candlestick graphics item

    Raises:
        ImportError: If PyQtGraph is not available
    """
    return CandlestickItem()