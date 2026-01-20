"""QGraphicsView Drag & Drop Prototype for Pattern Builder.

Phase 0.3.4: Verify QGraphicsView + draggable items work correctly.
This is a proof-of-concept for the Pattern Builder canvas.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsLineItem, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter

from ui.windows.cel_editor.theme import (
    BACKGROUND_PRIMARY, GRID_MAJOR, GRID_MINOR,
    CANDLE_BULLISH_BODY, CANDLE_BULLISH_BORDER,
    CANDLE_BEARISH_BODY, CANDLE_BEARISH_BORDER,
    CANDLE_DOJI_BODY, CANDLE_DOJI_BORDER
)


class DraggableCandleItem(QGraphicsRectItem):
    """Prototype draggable candle item."""

    def __init__(self, x: float, y: float, candle_type: str = "bullish"):
        """Initialize draggable candle.

        Args:
            x: X position
            y: Y position
            candle_type: 'bullish', 'bearish', or 'doji'
        """
        super().__init__(-20, -40, 40, 80)  # Centered rect

        self.candle_type = candle_type
        self.setPos(x, y)

        # Enable dragging
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Set colors based on type
        self._update_colors()

    def _update_colors(self):
        """Update colors based on candle type."""
        colors = {
            'bullish': (CANDLE_BULLISH_BODY, CANDLE_BULLISH_BORDER),
            'bearish': (CANDLE_BEARISH_BODY, CANDLE_BEARISH_BORDER),
            'doji': (CANDLE_DOJI_BODY, CANDLE_DOJI_BORDER)
        }

        body_color, border_color = colors.get(
            self.candle_type,
            (CANDLE_BULLISH_BODY, CANDLE_BULLISH_BORDER)
        )

        self.setBrush(QBrush(QColor(body_color)))
        self.setPen(QPen(QColor(border_color), 2))

    def itemChange(self, change, value):
        """Handle item changes (e.g., position)."""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            # Snap to grid (50px intervals)
            new_pos = value
            grid_size = 50
            snapped_x = round(new_pos.x() / grid_size) * grid_size
            snapped_y = round(new_pos.y() / grid_size) * grid_size
            return QPointF(snapped_x, snapped_y)

        return super().itemChange(change, value)


class PatternBuilderPrototype(QGraphicsView):
    """Prototype Pattern Builder canvas with grid and draggable candles."""

    def __init__(self, parent=None):
        """Initialize prototype canvas."""
        super().__init__(parent)

        # Create scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Set background
        self.setBackgroundBrush(QColor(BACKGROUND_PRIMARY))

        # Draw grid
        self._draw_grid()

        # Add sample candles
        self._add_sample_candles()

    def _draw_grid(self):
        """Draw grid on canvas."""
        # Major grid lines (50px)
        major_pen = QPen(QColor(GRID_MAJOR), 1)
        for x in range(-500, 501, 50):
            self.scene.addLine(x, -500, x, 500, major_pen)
        for y in range(-500, 501, 50):
            self.scene.addLine(-500, y, 500, y, major_pen)

        # Minor grid lines (10px)
        minor_pen = QPen(QColor(GRID_MINOR), 1)
        for x in range(-500, 501, 10):
            if x % 50 != 0:  # Skip major grid lines
                self.scene.addLine(x, -500, x, 500, minor_pen)
        for y in range(-500, 501, 10):
            if y % 50 != 0:
                self.scene.addLine(-500, y, 500, y, minor_pen)

    def _add_sample_candles(self):
        """Add sample draggable candles."""
        # Add 3 candles representing a simple pattern
        candles = [
            (0, 0, 'bullish'),      # Current candle
            (-100, 50, 'bearish'),  # Previous candle
            (-200, -50, 'bearish'), # Two candles ago
        ]

        for x, y, candle_type in candles:
            candle = DraggableCandleItem(x, y, candle_type)
            self.scene.addItem(candle)

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        # Zoom factor
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Get current scale
        old_pos = self.mapToScene(event.position().toPoint())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

        # Get new position
        new_pos = self.mapToScene(event.position().toPoint())

        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())


class PrototypeWindow(QMainWindow):
    """Main window for QGraphicsView prototype test."""

    def __init__(self):
        """Initialize prototype window."""
        super().__init__()

        self.setWindowTitle("QGraphicsView Prototype - Pattern Builder")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Info label
        info = QLabel(
            "✅ QGraphicsView Drag & Drop Prototype\n"
            "• Drag candles to move them (snaps to grid)\n"
            "• Mouse wheel to zoom in/out\n"
            "• Click candle to select (shows border)\n"
            "• This demonstrates the Pattern Builder canvas functionality"
        )
        info.setStyleSheet(f"color: #26a69a; padding: 10px; background: {BACKGROUND_PRIMARY};")
        layout.addWidget(info)

        # Pattern Builder canvas
        self.canvas = PatternBuilderPrototype()
        layout.addWidget(self.canvas)

        # Controls
        controls = QHBoxLayout()

        # Add candle buttons
        self.add_bullish_btn = QPushButton("Add Bullish Candle")
        self.add_bullish_btn.clicked.connect(lambda: self._add_candle('bullish'))

        self.add_bearish_btn = QPushButton("Add Bearish Candle")
        self.add_bearish_btn.clicked.connect(lambda: self._add_candle('bearish'))

        self.add_doji_btn = QPushButton("Add Doji Candle")
        self.add_doji_btn.clicked.connect(lambda: self._add_candle('doji'))

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_candles)

        controls.addWidget(self.add_bullish_btn)
        controls.addWidget(self.add_bearish_btn)
        controls.addWidget(self.add_doji_btn)
        controls.addWidget(self.clear_btn)
        controls.addStretch()

        layout.addLayout(controls)

        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BACKGROUND_PRIMARY};
            }}
            QPushButton {{
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 3px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: #353535;
                border-color: #4a4a4a;
            }}
            QPushButton:pressed {{
                background-color: {BACKGROUND_PRIMARY};
            }}
        """)

        self._next_candle_pos = 100  # X position for next candle

    def _add_candle(self, candle_type: str):
        """Add new candle to canvas."""
        candle = DraggableCandleItem(self._next_candle_pos, 0, candle_type)
        self.canvas.scene.addItem(candle)
        self._next_candle_pos += 100  # Offset next candle

    def _clear_candles(self):
        """Clear all candles from canvas."""
        # Remove all items except grid lines
        for item in self.canvas.scene.items():
            if isinstance(item, DraggableCandleItem):
                self.canvas.scene.removeItem(item)

        self._next_candle_pos = 100  # Reset position


def main():
    """Run QGraphicsView prototype."""
    print("\n" + "=" * 60)
    print("QGraphicsView Drag & Drop Prototype")
    print("Phase 0.3.4: Pattern Builder Canvas Proof-of-Concept")
    print("=" * 60)

    app = QApplication(sys.argv)

    window = PrototypeWindow()
    window.show()

    print("\n✅ Prototype window opened")
    print("   Test the following features:")
    print("   1. Drag candles around (should snap to grid)")
    print("   2. Zoom with mouse wheel")
    print("   3. Click to select candles")
    print("   4. Add new candles with buttons")
    print("   5. Clear all candles")
    print("\nClose the window when done testing.")
    print("=" * 60 + "\n")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
