from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

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
