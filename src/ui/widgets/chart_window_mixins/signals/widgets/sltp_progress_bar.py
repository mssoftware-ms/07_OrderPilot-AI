"""SL/TP Progress Bar Widget.

Custom progress bar showing price position between Stop-Loss and Take-Profit levels.
Provides visual feedback for position risk/reward ratio with gradient colors.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QPolygon
from PyQt6.QtWidgets import QProgressBar


class SLTPProgressBar(QProgressBar):
    """Custom progress bar showing price position between SL and TP.

    Features:
    - Gradient background (Red SL → Orange Entry → Green TP)
    - Current price marker with triangle indicator
    - P&L percentage display
    - Supports both long and short positions

    The bar shows position as percentage between SL (0%) and TP (100%).
    Current price is marked with a white line and triangle.
    """

    def __init__(self, parent=None):
        """Initialize SLTPProgressBar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(50)
        self.setTextVisible(True)
        self.setMinimumHeight(28)
        self.setMaximumHeight(32)
        self._sl_price = 0.0
        self._tp_price = 0.0
        self._current_price = 0.0
        self._entry_price = 0.0
        self._side = "long"

    def set_prices(self, entry: float, sl: float, tp: float, current: float, side: str = "long"):
        """Update the bar with new prices.

        Args:
            entry: Entry price
            sl: Stop-loss price
            tp: Take-profit price
            current: Current market price
            side: Position side ("long" or "short")
        """
        self._entry_price = entry
        self._sl_price = sl
        self._tp_price = tp
        self._current_price = current
        self._side = side.lower()

        if sl <= 0 or tp <= 0 or sl == tp:
            self.setValue(50)
            self.setFormat("No SL/TP set")
            return

        # Calculate position as percentage (SL=0%, TP=100%)
        total_range = tp - sl
        if total_range != 0:
            position = ((current - sl) / total_range) * 100
            position = max(0, min(100, position))  # Clamp to 0-100
        else:
            position = 50

        self.setValue(int(position))

        # Format text
        pnl_pct = 0
        if entry > 0:
            if self._side == "long":
                pnl_pct = ((current - entry) / entry) * 100
            else:
                pnl_pct = ((entry - current) / entry) * 100

        sign = "+" if pnl_pct >= 0 else ""
        self.setFormat(f"SL: {sl:.2f} | Current: {current:.2f} ({sign}{pnl_pct:.2f}%) | TP: {tp:.2f}")
        self.update()

    def paintEvent(self, event):
        """Custom paint for gradient background.

        Draws:
        1. Gradient background (Red → Orange → Green)
        2. Current price marker line
        3. Triangle indicator at current price
        4. Text overlay with prices and P&L
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        rect.adjust(1, 1, -1, -1)

        # Background gradient: red (SL) -> orange (entry) -> green (TP)
        gradient = QLinearGradient(rect.left(), 0, rect.right(), 0)
        gradient.setColorAt(0.0, QColor("#ef5350"))   # Red (SL)
        gradient.setColorAt(0.5, QColor("#ff9800"))   # Orange (Entry)
        gradient.setColorAt(1.0, QColor("#26a69a"))   # Green (TP)

        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)

        # Draw current position marker
        if self._sl_price > 0 and self._tp_price > 0 and self._tp_price != self._sl_price:
            total_range = self._tp_price - self._sl_price
            pos_ratio = (self._current_price - self._sl_price) / total_range
            pos_ratio = max(0, min(1, pos_ratio))

            marker_x = rect.left() + (rect.width() * pos_ratio)

            # Draw marker line
            painter.setPen(QColor("#ffffff"))
            painter.drawLine(int(marker_x), rect.top() + 2, int(marker_x), rect.bottom() - 2)

            # Draw marker triangle
            painter.setBrush(QColor("#ffffff"))
            triangle_size = 6
            points = [
                (int(marker_x), rect.top()),
                (int(marker_x - triangle_size), rect.top() - triangle_size),
                (int(marker_x + triangle_size), rect.top() - triangle_size),
            ]
            polygon = QPolygon([QPoint(x, y) for x, y in points])
            painter.drawPolygon(polygon)

        # Draw text
        painter.setPen(QColor("#ffffff"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.format())

        painter.end()

    def reset_bar(self):
        """Reset bar to default state.

        Clears all prices and resets to neutral position.
        """
        self._sl_price = 0.0
        self._tp_price = 0.0
        self._current_price = 0.0
        self._entry_price = 0.0
        self.setValue(50)
        self.setFormat("No active position")
        self.update()
