"""Multi-Chart and Multi-Monitor support for OrderPilot-AI.

This package provides functionality for managing multiple chart windows
across multiple monitors with layout presets and crosshair synchronization.
"""

from __future__ import annotations

from .crosshair_sync import CrosshairSyncManager
from .layout_manager import LayoutManager
from .multi_monitor_manager import MultiMonitorChartManager

__all__ = [
    "LayoutManager",
    "CrosshairSyncManager",
    "MultiMonitorChartManager",
]
