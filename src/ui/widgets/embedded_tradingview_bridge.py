from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog, QApplication

logger = logging.getLogger(__name__)
class ChartBridge(QObject):
    """Bridge object for JavaScript to Python communication.

    Allows JavaScript in the chart to call Python methods, e.g., when
    a stop line is dragged to a new position or crosshair moves.
    """

    # Signal emitted when a stop line is moved
    stop_line_moved = pyqtSignal(str, float)  # (line_id, new_price)
    # Signal emitted when crosshair moves (for cursor position tracking)
    crosshair_moved = pyqtSignal(float, float)  # (time, price)
    # Signal emitted when a zone is deleted via JavaScript delete tool
    zone_deleted = pyqtSignal(str)  # (zone_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Store last known crosshair position
        self._last_crosshair_time = None
        self._last_crosshair_price = None

    @pyqtSlot(str, float)
    def onStopLineMoved(self, line_id: str, new_price: float):
        """Called from JavaScript when a stop line is dragged.

        Args:
            line_id: ID of the line ("initial_stop", "trailing_stop", "entry_line")
            new_price: New price level after drag
        """
        logger.info(f"[ChartBridge] Stop line moved: {line_id} -> {new_price:.2f}")
        self.stop_line_moved.emit(line_id, new_price)

    @pyqtSlot(float, float)
    def onCrosshairMove(self, time: float, price: float):
        """Called from JavaScript when crosshair moves.

        Args:
            time: Unix timestamp of crosshair position
            price: Price at crosshair position
        """
        self._last_crosshair_time = time
        self._last_crosshair_price = price
        self.crosshair_moved.emit(time, price)

    def get_crosshair_position(self) -> tuple[float | None, float | None]:
        """Get the last known crosshair position.

        Returns:
            Tuple of (time, price) or (None, None) if not available
        """
        return (self._last_crosshair_time, self._last_crosshair_price)

    @pyqtSlot(str)
    def onZoneDeleted(self, zone_id: str):
        """Called from JavaScript when a zone is deleted via the delete tool.

        Args:
            zone_id: ID of the deleted zone
        """
        logger.info(f"[ChartBridge] Zone deleted via JS: {zone_id}")
        self.zone_deleted.emit(zone_id)

    @pyqtSlot(str, result=str)
    def pickColor(self, current_color: str = "rgba(13,110,253,0.18)") -> str:
        """Open QColorDialog and return the chosen color in CSS rgba format.

        Args:
            current_color: Current color in CSS format (rgba or hex)

        Returns:
            Chosen color in rgba(r,g,b,a) format or current_color if cancelled
        """
        try:
            # Parse current color
            qcolor = QColor(current_color)
            if not qcolor.isValid():
                qcolor = QColor("rgba(13,110,253,0.18)")

            # Enable alpha channel in color dialog
            options = QColorDialog.ColorDialogOption.ShowAlphaChannel

            # Get main window for parent
            main_window = QApplication.activeWindow()

            # Open color dialog
            chosen = QColorDialog.getColor(qcolor, main_window, "Farbe wählen", options)

            if chosen.isValid():
                # Convert to CSS rgba format
                r = chosen.red()
                g = chosen.green()
                b = chosen.blue()
                a = chosen.alpha() / 255.0  # Convert 0-255 to 0-1
                return f"rgba({r},{g},{b},{a:.2f})"
            else:
                return current_color
        except Exception as e:
            logger.warning(f"Color dialog failed: {e}", exc_info=True)
            return current_color
