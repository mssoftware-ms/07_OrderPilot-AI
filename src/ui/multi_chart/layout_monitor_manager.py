"""Layout Monitor Manager - Monitor Detection and Geometry.

Refactored from layout_manager.py.

Contains:
- get_available_monitors: Query all monitors with geometry
- get_monitor_geometry: Get specific monitor's QRect
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from .layout_manager import ChartLayoutManager


class LayoutMonitorManager:
    """Helper for monitor detection and geometry queries."""

    def __init__(self, parent: "ChartLayoutManager"):
        self.parent = parent

    def get_available_monitors(self) -> list[dict]:
        """Get list of available monitors with their geometry."""
        screens = QApplication.screens()
        monitors = []
        for i, screen in enumerate(screens):
            geo = screen.geometry()
            monitors.append({
                "index": i,
                "name": screen.name(),
                "x": geo.x(),
                "y": geo.y(),
                "width": geo.width(),
                "height": geo.height(),
                "is_primary": screen == QApplication.primaryScreen(),
            })
        return monitors

    def get_monitor_geometry(self, monitor_index: int) -> QRect:
        """Get the geometry of a specific monitor."""
        screens = QApplication.screens()
        if 0 <= monitor_index < len(screens):
            return screens[monitor_index].geometry()
        # Fallback to primary screen
        return QApplication.primaryScreen().geometry()
