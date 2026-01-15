"""Multi-Monitor Chart Manager for OrderPilot-AI.

This module provides functionality for managing multiple chart windows
across multiple monitors, including applying layouts and tiling windows.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

from ..models import ChartConfig, MultiChartLayout
from .crosshair_sync import CrosshairSyncManager
from .layout_manager import LayoutManager

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class MultiMonitorChartManager:
    """Manages multiple chart windows across monitors.

    Extends the basic chart window management with multi-monitor support,
    layout presets, and crosshair synchronization.

    Attributes:
        layout_manager: Handles layout persistence
        crosshair_sync: Handles crosshair synchronization
        windows: Dictionary of open chart windows
    """

    def __init__(
        self,
        chart_factory: Optional[Callable[[str, str], "QWidget"]] = None,
        on_window_opened: Optional[Callable[[str, "QWidget"], None]] = None,
        on_window_closed: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialize the multi-monitor chart manager.

        Args:
            chart_factory: Function to create a new chart window
                           Args: (symbol, timeframe) -> QWidget
            on_window_opened: Callback when a window opens
            on_window_closed: Callback when a window closes
        """
        self.layout_manager = LayoutManager()
        self.crosshair_sync = CrosshairSyncManager()
        self._windows: dict[str, "QWidget"] = {}
        self._chart_factory = chart_factory
        self._on_window_opened = on_window_opened
        self._on_window_closed = on_window_closed
        self._window_counter = 0

    def set_chart_factory(
        self,
        factory: Callable[[str, str], "QWidget"],
    ) -> None:
        """Set the chart factory function.

        Args:
            factory: Function to create chart windows
        """
        self._chart_factory = factory

    def open_chart(
        self,
        symbol: str,
        timeframe: str = "1T",
        monitor: int = 0,
        position: Optional[dict[str, int]] = None,
        window_id: Optional[str] = None,
    ) -> Optional["QWidget"]:
        """Open a new chart window.

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            monitor: Monitor index (0 = primary)
            position: Window position {x, y, width, height}
            window_id: Custom window ID (auto-generated if None)

        Returns:
            The created chart window, or None if failed
        """
        if not self._chart_factory:
            logger.error("No chart factory set")
            return None

        # Generate window ID
        if window_id is None:
            self._window_counter += 1
            window_id = f"chart_{self._window_counter}"

        try:
            # Create the chart window
            window = self._chart_factory(symbol, timeframe)

            # Store symbol and timeframe on window for later reference
            window.symbol = symbol  # type: ignore
            window.timeframe = timeframe  # type: ignore

            # Position the window
            self._position_window(window, monitor, position)

            # Register for crosshair sync
            self._setup_crosshair_sync(window_id, window)

            # Store and track
            self._windows[window_id] = window

            # Connect close event
            if hasattr(window, "destroyed"):
                window.destroyed.connect(
                    lambda: self._on_window_destroyed(window_id)
                )

            # Show the window
            window.show()

            if self._on_window_opened:
                self._on_window_opened(window_id, window)

            logger.info(
                "Opened chart window: %s (%s %s on monitor %d)",
                window_id, symbol, timeframe, monitor
            )
            return window

        except Exception as e:
            logger.error("Failed to open chart window: %s", e)
            return None

    def close_chart(self, window_id: str) -> bool:
        """Close a chart window.

        Args:
            window_id: Window to close

        Returns:
            True if closed, False if not found
        """
        window = self._windows.pop(window_id, None)
        if window is None:
            return False

        self.crosshair_sync.unregister_window(window_id)
        window.close()

        if self._on_window_closed:
            self._on_window_closed(window_id)

        logger.info("Closed chart window: %s", window_id)
        return True

    def close_all(self) -> None:
        """Close all chart windows."""
        window_ids = list(self._windows.keys())
        for window_id in window_ids:
            self.close_chart(window_id)

    def apply_layout(self, layout: MultiChartLayout) -> bool:
        """Apply a layout preset.

        Closes existing windows and opens new ones according to the layout.

        Args:
            layout: Layout to apply

        Returns:
            True if successful
        """
        # Close existing windows
        self.close_all()

        # Configure crosshair sync
        self.crosshair_sync.set_enabled(layout.sync_crosshair)

        # Open windows according to layout
        for i, chart_config in enumerate(layout.charts):
            self.open_chart(
                symbol=chart_config.symbol,
                timeframe=chart_config.timeframe,
                monitor=chart_config.monitor,
                position=chart_config.position,
                window_id=f"layout_{layout.id}_{i}",
            )

        logger.info("Applied layout: %s", layout.name)
        return True

    def apply_layout_by_id(self, layout_id: str) -> bool:
        """Apply a layout by its ID.

        Args:
            layout_id: Layout identifier

        Returns:
            True if successful, False if not found
        """
        layout = self.layout_manager.load_layout(layout_id)
        if layout is None:
            logger.warning("Layout not found: %s", layout_id)
            return False
        return self.apply_layout(layout)

    def save_current_layout(self, name: str) -> Optional[MultiChartLayout]:
        """Save the current window arrangement as a layout.

        Args:
            name: Name for the layout

        Returns:
            The saved layout, or None if failed
        """
        windows = list(self._windows.values())
        if not windows:
            logger.warning("No windows to save")
            return None

        return self.layout_manager.capture_current_layout(windows, name)

    def tile_on_monitor(
        self,
        monitor: int,
        symbols: list[str],
        timeframe: str = "1T",
    ) -> None:
        """Tile multiple charts on a monitor.

        Automatically arranges charts in a grid pattern.

        Args:
            monitor: Target monitor index
            symbols: Symbols to display
            timeframe: Timeframe for all charts
        """
        if not symbols:
            return

        monitors = self.layout_manager.get_available_monitors()
        if monitor >= len(monitors):
            monitor = 0

        mon_info = monitors[monitor]
        width = mon_info["width"]
        height = mon_info["height"]
        base_x = mon_info["x"]
        base_y = mon_info["y"]

        # Calculate grid
        n = len(symbols)
        cols = 2 if n > 1 else 1
        rows = (n + cols - 1) // cols

        cell_width = width // cols
        cell_height = height // rows

        for i, symbol in enumerate(symbols):
            row = i // cols
            col = i % cols
            position = {
                "x": base_x + col * cell_width,
                "y": base_y + row * cell_height,
                "width": cell_width,
                "height": cell_height,
            }
            self.open_chart(symbol, timeframe, monitor, position)

    def get_window_count(self) -> int:
        """Get the number of open windows.

        Returns:
            Number of open chart windows
        """
        return len(self._windows)

    def get_open_symbols(self) -> list[str]:
        """Get list of symbols in open windows.

        Returns:
            List of symbols
        """
        return [
            getattr(w, "symbol", "UNKNOWN")
            for w in self._windows.values()
        ]

    def _position_window(
        self,
        window: "QWidget",
        monitor: int,
        position: Optional[dict[str, int]],
    ) -> None:
        """Position a window on the specified monitor.

        Args:
            window: Window to position
            monitor: Target monitor index
            position: Position dict {x, y, width, height}
        """
        try:
            from PyQt6.QtWidgets import QApplication

            screens = QApplication.screens()
            if monitor >= len(screens):
                monitor = 0

            screen = screens[monitor]
            screen_geo = screen.geometry()

            if position:
                # Use provided position (relative to screen)
                x = screen_geo.x() + position.get("x", 0)
                y = screen_geo.y() + position.get("y", 0)
                w = position.get("width", 800)
                h = position.get("height", 600)
            else:
                # Center on screen
                w, h = 800, 600
                x = screen_geo.x() + (screen_geo.width() - w) // 2
                y = screen_geo.y() + (screen_geo.height() - h) // 2

            window.setGeometry(x, y, w, h)

        except Exception as e:
            logger.warning("Failed to position window: %s", e)

    def _setup_crosshair_sync(
        self,
        window_id: str,
        window: "QWidget",
    ) -> None:
        """Setup crosshair sync for a window.

        Args:
            window_id: Window identifier
            window: Chart window
        """
        # Create callback that updates this window's crosshair
        def on_crosshair_update(timestamp: int, price: float) -> None:
            if hasattr(window, "set_crosshair_position"):
                window.set_crosshair_position(timestamp, price)

        self.crosshair_sync.register_window(
            window_id, window, on_crosshair_update
        )

    def _on_window_destroyed(self, window_id: str) -> None:
        """Handle window destruction.

        Args:
            window_id: Destroyed window ID
        """
        self._windows.pop(window_id, None)
        self.crosshair_sync.unregister_window(window_id)

        if self._on_window_closed:
            self._on_window_closed(window_id)

        logger.debug("Window destroyed: %s", window_id)
