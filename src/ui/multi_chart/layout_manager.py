"""ChartLayoutManager - Multi-Chart and Multi-Monitor Management (REFACTORED).

Manages multiple chart windows across monitors for pre-trade analysis.
Supports saving/loading layout templates and automatic chart set opening.

REFACTORED: Split into focused helper modules using composition pattern.
- layout_config_models.py: ChartWindowConfig + ChartLayoutConfig dataclasses
- layout_monitor_manager.py: Monitor detection and geometry queries
- layout_window_operations.py: open/close layouts, window creation/positioning
- layout_persistence.py: JSON save/load/list/delete
- layout_default_templates.py: 4 default layout builders
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QObject, pyqtSignal

# Import models (standalone)
from .layout_config_models import ChartWindowConfig, ChartLayoutConfig

# Import helpers
from .layout_monitor_manager import LayoutMonitorManager
from .layout_window_operations import LayoutWindowOperations
from .layout_persistence import LayoutPersistence
from .layout_default_templates import LayoutDefaultTemplates

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)

# Default layouts directory
LAYOUTS_DIR = Path(__file__).parent.parent.parent.parent / "config" / "chart_layouts"


# Re-export models for backward compatibility
__all__ = [
    "ChartLayoutManager",
    "ChartWindowConfig",
    "ChartLayoutConfig",
]


class ChartLayoutManager(QObject):
    """Manages multiple chart windows for pre-trade analysis (REFACTORED).

    Features:
    - Open multiple charts with different timeframes
    - Position windows on specific monitors
    - Save and load layout templates
    - Synchronize crosshair between charts
    - Auto-open predefined chart sets
    """

    # Signals
    layout_opened = pyqtSignal(str)  # layout name
    layout_closed = pyqtSignal()
    window_opened = pyqtSignal(object)  # ChartWindow
    window_closed = pyqtSignal(object)  # ChartWindow

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._active_windows: list["ChartWindow"] = []
        self._current_layout: ChartLayoutConfig | None = None
        self._layouts_dir = LAYOUTS_DIR
        self._history_manager: Any = None

        # Ensure layouts directory exists
        self._layouts_dir.mkdir(parents=True, exist_ok=True)

        # Create helpers (composition pattern)
        self._monitor_manager = LayoutMonitorManager(self)
        self._window_ops = LayoutWindowOperations(self)
        self._persistence = LayoutPersistence(self)
        self._templates = LayoutDefaultTemplates(self)

        # Create default layouts if none exist
        self._templates.create_default_layouts()

    def set_history_manager(self, history_manager: Any) -> None:
        """Set the history manager for data loading."""
        self._history_manager = history_manager

    @property
    def active_windows(self) -> list["ChartWindow"]:
        """Get list of active chart windows."""
        return self._active_windows.copy()

    @property
    def current_layout(self) -> ChartLayoutConfig | None:
        """Get the current layout configuration."""
        return self._current_layout

    # === Monitor Management (Delegiert) ===

    def get_available_monitors(self) -> list[dict]:
        """Get list of available monitors with their geometry (delegiert)."""
        return self._monitor_manager.get_available_monitors()

    def get_monitor_geometry(self, monitor_index: int):
        """Get the geometry of a specific monitor (delegiert)."""
        return self._monitor_manager.get_monitor_geometry(monitor_index)

    # === Layout Operations (Delegiert) ===

    def open_layout(self, layout: ChartLayoutConfig, symbol: str | None = None) -> list["ChartWindow"]:
        """Open a chart layout with multiple windows (delegiert)."""
        return self._window_ops.open_layout(layout, symbol)

    def close_all_windows(self) -> None:
        """Close all active chart windows (delegiert)."""
        return self._window_ops.close_all_windows()

    def open_pre_trade_analysis(self, symbol: str) -> list["ChartWindow"]:
        """Open pre-trade analysis charts for a symbol (delegiert)."""
        return self._window_ops.open_pre_trade_analysis(symbol)

    def create_layout_from_current(self, name: str, description: str = "") -> ChartLayoutConfig | None:
        """Create a layout configuration from currently open windows (delegiert)."""
        return self._window_ops.create_layout_from_current(name, description)

    # === Persistence (Delegiert) ===

    def save_layout(self, layout: ChartLayoutConfig) -> bool:
        """Save a layout configuration to file (delegiert)."""
        return self._persistence.save_layout(layout)

    def load_layout(self, name: str) -> ChartLayoutConfig | None:
        """Load a layout configuration from file (delegiert)."""
        return self._persistence.load_layout(name)

    def get_available_layouts(self) -> list[str]:
        """Get list of available layout names (delegiert)."""
        return self._persistence.get_available_layouts()

    def delete_layout(self, name: str) -> bool:
        """Delete a saved layout (delegiert)."""
        return self._persistence.delete_layout(name)
