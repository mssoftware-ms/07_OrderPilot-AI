"""Relation Line for Pattern Builder Canvas.

Visual line connecting two candles to show their relationship.
Supports 4 relation types: greater (>), less (<), equal (≈), near (~).
"""

from typing import Optional
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QPen, QColor, QFont

from src.ui.windows.cel_editor.theme import (
    RELATION_GREATER, RELATION_LESS, RELATION_EQUAL, RELATION_NEAR,
    TEXT_PRIMARY
)


class RelationLine(QGraphicsLineItem):
    """Visual line showing relationship between two candles.

    Relation Types:
    1. greater (>) - Green line: value1 > value2
    2. less (<) - Red line: value1 < value2
    3. equal (≈) - Orange line: value1 ≈ value2 (approximately equal)
    4. near (~) - Cyan line: values are near each other

    Usage:
        # Create line between two candles
        line = RelationLine(candle1, candle2, relation_type="greater")

        # Line auto-updates when candles move
        candle1.setPos(100, 50)  # Line follows automatically
    """

    # Line styles
    LINE_WIDTH = 2
    LINE_WIDTH_SELECTED = 3

    def __init__(
        self,
        start_candle: Optional['CandleItem'] = None,
        end_candle: Optional['CandleItem'] = None,
        relation_type: str = "greater",
        start_point: Optional[QPointF] = None,
        end_point: Optional[QPointF] = None
    ):
        """Initialize relation line.

        Args:
            start_candle: Source candle (or None if using points)
            end_candle: Target candle (or None if using points)
            relation_type: Type of relation (greater, less, equal, near)
            start_point: Manual start point if not using candles
            end_point: Manual end point if not using candles
        """
        super().__init__()

        self.start_candle = start_candle
        self.end_candle = end_candle
        self.relation_type = relation_type

        # Manual points (used if candles not set)
        self._start_point = start_point or QPointF(0, 0)
        self._end_point = end_point or QPointF(100, 0)

        # Label for relation symbol
        self.label: Optional[QGraphicsTextItem] = None

        # Setup
        self._update_line()
        self._apply_style()
        self._create_label()

        # Enable selection
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Tooltip
        self._update_tooltip()

        # Connect to candle position changes if candles provided
        if start_candle and end_candle:
            # Note: Position changes will be handled by canvas refresh
            pass

    def _update_line(self):
        """Update line coordinates based on candle positions or manual points."""
        if self.start_candle and self.end_candle:
            # Use candle positions
            start_pos = self.start_candle.scenePos()
            end_pos = self.end_candle.scenePos()
        else:
            # Use manual points
            start_pos = self._start_point
            end_pos = self._end_point

        # Set line
        self.setLine(QLineF(start_pos, end_pos))

    def _apply_style(self):
        """Apply color and style based on relation type."""
        color = self._get_color()
        pen = QPen(QColor(color), self.LINE_WIDTH)

        # Dashed line for "near" relation
        if self.relation_type == "near":
            pen.setStyle(Qt.PenStyle.DashLine)

        self.setPen(pen)

    def _get_color(self) -> str:
        """Get line color based on relation type."""
        colors = {
            "greater": RELATION_GREATER,  # Green
            "less": RELATION_LESS,        # Red
            "equal": RELATION_EQUAL,      # Orange
            "near": RELATION_NEAR         # Cyan
        }
        return colors.get(self.relation_type, RELATION_GREATER)

    def _get_symbol(self) -> str:
        """Get relation symbol for label."""
        symbols = {
            "greater": ">",
            "less": "<",
            "equal": "≈",
            "near": "~"
        }
        return symbols.get(self.relation_type, ">")

    def _create_label(self):
        """Create text label showing relation symbol."""
        # Calculate label position (midpoint of line)
        line = self.line()
        mid_x = (line.x1() + line.x2()) / 2
        mid_y = (line.y1() + line.y2()) / 2

        # Create text item
        self.label = QGraphicsTextItem(self._get_symbol())

        # Style label
        font = QFont("Arial", 14, QFont.Weight.Bold)
        self.label.setFont(font)
        self.label.setDefaultTextColor(QColor(self._get_color()))

        # Position label slightly above line
        label_rect = self.label.boundingRect()
        self.label.setPos(
            mid_x - label_rect.width() / 2,
            mid_y - label_rect.height() - 5
        )

        # Make label part of the scene (not a child, as we're a line item)
        # Parent will add this to scene

    def _update_tooltip(self):
        """Update tooltip with relation info."""
        relation_text = {
            "greater": "Greater Than (>)",
            "less": "Less Than (<)",
            "equal": "Approximately Equal (≈)",
            "near": "Near (~)"
        }

        tooltip = f"Relation: {relation_text.get(self.relation_type, 'Unknown')}"

        if self.start_candle and self.end_candle:
            tooltip += f"\nFrom: Candle[{self.start_candle.index}]"
            tooltip += f"\nTo: Candle[{self.end_candle.index}]"

        self.setToolTip(tooltip)

    def update_position(self):
        """Update line position when candles move."""
        self._update_line()
        self._update_label_position()

    def _update_label_position(self):
        """Update label position to midpoint of line."""
        if self.label:
            line = self.line()
            mid_x = (line.x1() + line.x2()) / 2
            mid_y = (line.y1() + line.y2()) / 2

            label_rect = self.label.boundingRect()
            self.label.setPos(
                mid_x - label_rect.width() / 2,
                mid_y - label_rect.height() - 5
            )

    def update_relation_type(self, relation_type: str):
        """Update relation type and redraw.

        Args:
            relation_type: New relation type (greater, less, equal, near)
        """
        self.relation_type = relation_type
        self._apply_style()

        # Update label
        if self.label:
            self.label.setPlainText(self._get_symbol())
            self.label.setDefaultTextColor(QColor(self._get_color()))

        self._update_tooltip()

    def itemChange(self, change, value):
        """Handle item changes (e.g., selection).

        Args:
            change: Type of change
            value: New value

        Returns:
            Processed value
        """
        if change == QGraphicsLineItem.GraphicsItemChange.ItemSelectedChange:
            # Update visual feedback for selection
            if value:
                # Thicker line when selected
                pen = self.pen()
                pen.setWidth(self.LINE_WIDTH_SELECTED)
                self.setPen(pen)
            else:
                # Normal line width
                pen = self.pen()
                pen.setWidth(self.LINE_WIDTH)
                self.setPen(pen)

        return super().itemChange(change, value)

    def get_data(self) -> dict:
        """Get relation line data for serialization.

        Returns:
            Dict with all relation properties
        """
        data = {
            "relation_type": self.relation_type
        }

        # Add candle indices if using candles
        if self.start_candle and self.end_candle:
            data["start_candle_index"] = self.start_candle.index
            data["end_candle_index"] = self.end_candle.index
        else:
            # Add manual points
            data["start_point"] = {"x": self._start_point.x(), "y": self._start_point.y()}
            data["end_point"] = {"x": self._end_point.x(), "y": self._end_point.y()}

        return data

    def get_label(self) -> Optional[QGraphicsTextItem]:
        """Get the label item for adding to scene.

        Returns:
            Label text item or None
        """
        return self.label

    def remove_label(self):
        """Remove label from scene (called before deleting line)."""
        if self.label and self.label.scene():
            self.label.scene().removeItem(self.label)
        self.label = None
