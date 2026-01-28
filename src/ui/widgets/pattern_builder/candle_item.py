"""Draggable Candle Item for Pattern Builder Canvas.

Represents a single candlestick that can be dragged on the canvas.
Supports 8 different candle types with visual gradients and properties.
"""

from typing import Optional
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsLineItem, QGraphicsItemGroup
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QLinearGradient, QPainter

from src.ui.windows.cel_editor.theme import (
    CANDLE_BULLISH_BODY, CANDLE_BULLISH_BORDER,
    CANDLE_BEARISH_BODY, CANDLE_BEARISH_BORDER,
    CANDLE_DOJI_BODY, CANDLE_DOJI_BORDER,
    SELECTION, ACCENT_TEAL
)


class CandleItem(QGraphicsItemGroup):
    """Draggable candle item with body, wick, and properties.

    Candle Types:
    1. bullish - Green candle (close > open)
    2. bearish - Red candle (close < open)
    3. doji - Small body (open ≈ close)
    4. hammer - Small body at top, long lower wick
    5. shooting_star - Small body at bottom, long upper wick
    6. spinning_top - Small body, long wicks both sides
    7. marubozu_long - Large bullish body, no wicks
    8. marubozu_short - Large bearish body, no wicks

    Properties:
    - index: Candle position (0=current, -1=previous, -2=two back)
    - open, high, low, close: OHLC values (0-100)
    - candle_type: One of 8 types above
    """

    # Default dimensions
    BODY_WIDTH = 40
    DEFAULT_BODY_HEIGHT = 80
    WICK_WIDTH = 2

    # Grid size for snapping
    GRID_SIZE = 50

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        candle_type: str = "bullish",
        index: int = 0,
        ohlc: Optional[dict] = None
    ):
        """Initialize candle item.

        Args:
            x: X position on canvas
            y: Y position on canvas
            candle_type: Type of candle (bullish, bearish, doji, etc.)
            index: Candle index (0, -1, -2, etc.)
            ohlc: Optional OHLC dict {"open": 50, "high": 80, "low": 40, "close": 70}
        """
        super().__init__()

        self.candle_type = candle_type
        self.index = index

        # OHLC values (0-100 scale)
        if ohlc:
            self.ohlc = ohlc
        else:
            self.ohlc = self._get_default_ohlc(candle_type)

        # Visual components
        self.body_rect: Optional[QGraphicsRectItem] = None
        self.upper_wick: Optional[QGraphicsLineItem] = None
        self.lower_wick: Optional[QGraphicsLineItem] = None

        # Setup
        self._create_visual_components()
        self.setPos(x, y)

        # Enable dragging and selection
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Tooltip
        self._update_tooltip()

    def _get_default_ohlc(self, candle_type: str) -> dict:
        """Get default OHLC values based on candle type."""
        defaults = {
            "bullish": {"open": 40, "high": 85, "low": 35, "close": 80},
            "bearish": {"open": 80, "high": 85, "low": 35, "close": 40},
            "doji": {"open": 60, "high": 75, "low": 45, "close": 60},
            "hammer": {"open": 65, "high": 70, "low": 20, "close": 70},
            "shooting_star": {"open": 30, "high": 80, "low": 25, "close": 30},
            "spinning_top": {"open": 55, "high": 85, "low": 25, "close": 60},
            "marubozu_long": {"open": 20, "high": 80, "low": 20, "close": 80},
            "marubozu_short": {"open": 80, "high": 80, "low": 20, "close": 20}
        }
        return defaults.get(candle_type, defaults["bullish"])

    def _create_visual_components(self):
        """Create body rectangle and wicks."""
        # Calculate dimensions from OHLC
        body_top, body_bottom = self._calculate_body_bounds()
        wick_top = self._scale_price(self.ohlc["high"])
        wick_bottom = self._scale_price(self.ohlc["low"])

        # Body rectangle
        body_height = abs(body_bottom - body_top)
        body_y = min(body_top, body_bottom)

        self.body_rect = QGraphicsRectItem(
            -self.BODY_WIDTH / 2,
            body_y,
            self.BODY_WIDTH,
            max(body_height, 2)  # Minimum 2px for doji
        )

        # Apply gradient and colors
        self._apply_candle_style(self.body_rect, body_y, body_height)

        # Upper wick (high to top of body)
        if wick_top < body_y:
            self.upper_wick = QGraphicsLineItem(0, wick_top, 0, body_y)
            self.upper_wick.setPen(QPen(QColor(self._get_border_color()), self.WICK_WIDTH))
            self.addToGroup(self.upper_wick)

        # Lower wick (bottom of body to low)
        body_bottom_edge = body_y + body_height
        if wick_bottom > body_bottom_edge:
            self.lower_wick = QGraphicsLineItem(0, body_bottom_edge, 0, wick_bottom)
            self.lower_wick.setPen(QPen(QColor(self._get_border_color()), self.WICK_WIDTH))
            self.addToGroup(self.lower_wick)

        # Add body to group
        self.addToGroup(self.body_rect)

    def _calculate_body_bounds(self) -> tuple[float, float]:
        """Calculate body top and bottom Y coordinates.

        Returns:
            (body_top, body_bottom) in pixel coordinates
        """
        open_y = self._scale_price(self.ohlc["open"])
        close_y = self._scale_price(self.ohlc["close"])

        return (open_y, close_y)

    def _scale_price(self, price: float) -> float:
        """Convert price (0-100) to Y coordinate.

        Args:
            price: Price value (0-100)

        Returns:
            Y coordinate (inverted, 0 at top)
        """
        # Scale to -100 to 0 range (inverted Y axis)
        return -price

    def _apply_candle_style(self, body: QGraphicsRectItem, y: float, height: float):
        """Apply gradient and border to body rectangle."""
        # Get colors
        body_color = self._get_body_color()
        border_color = self._get_border_color()

        # Create gradient for 3D effect
        gradient = QLinearGradient(
            -self.BODY_WIDTH / 2, 0,
            self.BODY_WIDTH / 2, 0
        )

        # Lighter on left, darker on right for depth
        lighter = QColor(body_color).lighter(120)
        darker = QColor(body_color).darker(110)

        gradient.setColorAt(0, lighter)
        gradient.setColorAt(0.5, QColor(body_color))
        gradient.setColorAt(1, darker)

        # Apply style
        body.setBrush(QBrush(gradient))
        body.setPen(QPen(QColor(border_color), 2))

    def _get_body_color(self) -> str:
        """Get body fill color based on candle type."""
        # Determine if bullish or bearish
        is_bullish = self.ohlc["close"] >= self.ohlc["open"]

        if self.candle_type == "doji":
            return CANDLE_DOJI_BODY
        elif is_bullish:
            return CANDLE_BULLISH_BODY
        else:
            return CANDLE_BEARISH_BODY

    def _get_border_color(self) -> str:
        """Get border color based on candle type."""
        is_bullish = self.ohlc["close"] >= self.ohlc["open"]

        if self.candle_type == "doji":
            return CANDLE_DOJI_BORDER
        elif is_bullish:
            return CANDLE_BULLISH_BORDER
        else:
            return CANDLE_BEARISH_BORDER

    def _update_tooltip(self):
        """Update tooltip with candle info."""
        tooltip = (
            f"Candle[{self.index}]: {self.candle_type.replace('_', ' ').title()}\n"
            f"Open: {self.ohlc['open']:.1f}\n"
            f"High: {self.ohlc['high']:.1f}\n"
            f"Low: {self.ohlc['low']:.1f}\n"
            f"Close: {self.ohlc['close']:.1f}"
        )
        self.setToolTip(tooltip)

    def itemChange(self, change, value):
        """Handle item changes (e.g., position, selection).

        Args:
            change: Type of change
            value: New value

        Returns:
            Processed value (may snap to grid)
        """
        if change == QGraphicsItemGroup.GraphicsItemChange.ItemPositionChange:
            # Snap to grid
            new_pos = value
            snapped_x = round(new_pos.x() / self.GRID_SIZE) * self.GRID_SIZE
            snapped_y = round(new_pos.y() / self.GRID_SIZE) * self.GRID_SIZE
            return QPointF(snapped_x, snapped_y)

        elif change == QGraphicsItemGroup.GraphicsItemChange.ItemSelectedChange:
            # Update visual feedback for selection
            self._update_selection_visual(value)

        return super().itemChange(change, value)

    def _update_selection_visual(self, selected: bool):
        """Update visual appearance when selected/deselected.

        Args:
            selected: True if item is being selected
        """
        if self.body_rect:
            if selected:
                # Highlight border with teal
                self.body_rect.setPen(QPen(QColor(ACCENT_TEAL), 3))
            else:
                # Reset to normal border
                self.body_rect.setPen(QPen(QColor(self._get_border_color()), 2))

    def update_ohlc(self, ohlc: dict):
        """Update OHLC values and redraw candle.

        Args:
            ohlc: New OHLC dict
        """
        self.ohlc = ohlc

        # Remove old components
        if self.body_rect:
            self.removeFromGroup(self.body_rect)
        if self.upper_wick:
            self.removeFromGroup(self.upper_wick)
        if self.lower_wick:
            self.removeFromGroup(self.lower_wick)

        # Recreate
        self._create_visual_components()
        self._update_tooltip()

    def update_candle_type(self, candle_type: str):
        """Update candle type and redraw.

        Args:
            candle_type: New candle type
        """
        self.candle_type = candle_type

        # Get new default OHLC for this type
        self.ohlc = self._get_default_ohlc(candle_type)

        # Redraw
        self.update_ohlc(self.ohlc)

    def update_index(self, index: int):
        """Update candle index.

        Args:
            index: New index (0, -1, -2, etc.)
        """
        self.index = index
        self._update_tooltip()

    def get_data(self) -> dict:
        """Get candle data for serialization.

        Returns:
            Dict with all candle properties
        """
        return {
            "type": self.candle_type,
            "index": self.index,
            "ohlc": self.ohlc.copy(),
            "position": {"x": self.pos().x(), "y": self.pos().y()}
        }

    @classmethod
    def from_data(cls, data: dict) -> 'CandleItem':
        """Create CandleItem from serialized data.

        Args:
            data: Dict from get_data()

        Returns:
            New CandleItem instance
        """
        pos = data.get("position", {"x": 0, "y": 0})
        return cls(
            x=pos["x"],
            y=pos["y"],
            candle_type=data["type"],
            index=data["index"],
            ohlc=data["ohlc"]
        )

    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint for debugging (optional)."""
        # Let child items paint themselves
        super().paint(painter, option, widget)

    def boundingRect(self) -> QRectF:
        """Return bounding rectangle for this item."""
        return self.childrenBoundingRect()
