"""Layout Manager for Multi-Chart configurations.

This module handles saving, loading, and managing layout presets
for multi-chart/multi-monitor setups.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

from ..models import ChartConfig, MultiChartLayout

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# Default layouts directory
DEFAULT_LAYOUTS_DIR = Path.home() / ".orderpilot" / "layouts"


class LayoutManager:
    """Manages multi-chart layout presets.

    Handles saving, loading, and listing layout configurations.
    Layouts are persisted as JSON files.

    Attributes:
        layouts_dir: Directory where layouts are stored
        layouts: Dictionary of loaded layouts by ID
    """

    def __init__(
        self,
        layouts_dir: Optional[Path] = None,
        on_layout_changed: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialize the layout manager.

        Args:
            layouts_dir: Custom directory for layouts (default: ~/.orderpilot/layouts)
            on_layout_changed: Callback when a layout changes
        """
        self.layouts_dir = layouts_dir or DEFAULT_LAYOUTS_DIR
        self.layouts_dir.mkdir(parents=True, exist_ok=True)
        self._layouts: dict[str, MultiChartLayout] = {}
        self._on_layout_changed = on_layout_changed
        self._load_all_layouts()

    def _load_all_layouts(self) -> None:
        """Load all layouts from the layouts directory."""
        self._layouts.clear()
        if not self.layouts_dir.exists():
            return

        for layout_file in self.layouts_dir.glob("*.json"):
            try:
                with open(layout_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                layout = MultiChartLayout.from_dict(data)
                self._layouts[layout.id] = layout
                logger.debug("Loaded layout: %s (%s)", layout.name, layout.id)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning("Failed to load layout %s: %s", layout_file, e)

    def save_layout(
        self,
        name: str,
        charts: list[ChartConfig],
        sync_crosshair: bool = False,
        layout_id: Optional[str] = None,
    ) -> MultiChartLayout:
        """Save a layout preset.

        Args:
            name: Display name for the layout
            charts: List of chart configurations
            sync_crosshair: Whether to sync crosshairs
            layout_id: Optional ID (generates new if None)

        Returns:
            The saved layout
        """
        layout = MultiChartLayout(
            id=layout_id or str(uuid.uuid4()),
            name=name,
            charts=charts,
            sync_crosshair=sync_crosshair,
            created_at=datetime.now(),
        )

        # Save to file
        layout_file = self.layouts_dir / f"{layout.id}.json"
        with open(layout_file, "w", encoding="utf-8") as f:
            json.dump(layout.to_dict(), f, indent=2)

        self._layouts[layout.id] = layout
        logger.info("Saved layout: %s (%s)", layout.name, layout.id)

        if self._on_layout_changed:
            self._on_layout_changed(layout.id)

        return layout

    def load_layout(self, layout_id: str) -> Optional[MultiChartLayout]:
        """Load a layout by ID.

        Args:
            layout_id: Layout identifier

        Returns:
            Layout if found, None otherwise
        """
        return self._layouts.get(layout_id)

    def delete_layout(self, layout_id: str) -> bool:
        """Delete a layout.

        Args:
            layout_id: Layout to delete

        Returns:
            True if deleted, False if not found
        """
        if layout_id not in self._layouts:
            return False

        layout_file = self.layouts_dir / f"{layout_id}.json"
        if layout_file.exists():
            layout_file.unlink()

        del self._layouts[layout_id]
        logger.info("Deleted layout: %s", layout_id)

        if self._on_layout_changed:
            self._on_layout_changed(layout_id)

        return True

    def list_layouts(self) -> list[MultiChartLayout]:
        """List all available layouts.

        Returns:
            List of all layouts sorted by name
        """
        return sorted(self._layouts.values(), key=lambda l: l.name)

    def get_layout_names(self) -> dict[str, str]:
        """Get a mapping of layout IDs to names.

        Returns:
            Dictionary of {layout_id: layout_name}
        """
        return {lid: layout.name for lid, layout in self._layouts.items()}

    def capture_current_layout(
        self,
        windows: list["QWidget"],
        name: str = "Current Layout",
    ) -> MultiChartLayout:
        """Capture the current window arrangement as a layout.

        Args:
            windows: List of chart windows to capture
            name: Name for the captured layout

        Returns:
            The captured layout
        """
        charts = []
        for window in windows:
            # Try to get symbol and timeframe from window
            symbol = getattr(window, "symbol", "UNKNOWN")
            timeframe = getattr(window, "timeframe", "1T")

            # Get window geometry
            geo = window.geometry()
            screen = window.screen()
            monitor = 0
            if screen:
                # Get monitor index from screen
                from PyQt6.QtWidgets import QApplication
                screens = QApplication.screens()
                for i, s in enumerate(screens):
                    if s == screen:
                        monitor = i
                        break

            charts.append(ChartConfig(
                symbol=symbol,
                timeframe=timeframe,
                monitor=monitor,
                position={
                    "x": geo.x(),
                    "y": geo.y(),
                    "width": geo.width(),
                    "height": geo.height(),
                },
            ))

        return self.save_layout(name, charts)

    def get_available_monitors(self) -> list[dict[str, Any]]:
        """Get information about available monitors.

        Returns:
            List of monitor info dictionaries
        """
        try:
            from PyQt6.QtWidgets import QApplication
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
                    "is_primary": i == 0,
                })
            return monitors
        except Exception as e:
            logger.warning("Failed to get monitors: %s", e)
            return [{"index": 0, "name": "Primary", "x": 0, "y": 0,
                     "width": 1920, "height": 1080, "is_primary": True}]

    def create_default_layouts(self) -> None:
        """Create some default layout presets if none exist."""
        if self._layouts:
            return  # Already have layouts

        # Single chart layout
        self.save_layout(
            name="Single Chart",
            charts=[
                ChartConfig(
                    symbol="BTC/USD",
                    timeframe="1T",
                    monitor=0,
                    position={"x": 100, "y": 100, "width": 1200, "height": 800},
                )
            ],
            layout_id="default_single",
        )

        # Dual chart layout (side by side)
        self.save_layout(
            name="Dual Charts",
            charts=[
                ChartConfig(
                    symbol="BTC/USD",
                    timeframe="5T",
                    monitor=0,
                    position={"x": 0, "y": 0, "width": 960, "height": 1080},
                ),
                ChartConfig(
                    symbol="BTC/USD",
                    timeframe="1H",
                    monitor=0,
                    position={"x": 960, "y": 0, "width": 960, "height": 1080},
                ),
            ],
            sync_crosshair=True,
            layout_id="default_dual",
        )

        # Multi-timeframe layout (4 charts)
        self.save_layout(
            name="Multi-Timeframe (4)",
            charts=[
                ChartConfig(
                    symbol="BTC/USD",
                    timeframe="1T",
                    monitor=0,
                    position={"x": 0, "y": 0, "width": 960, "height": 540},
                ),
                ChartConfig(
                    symbol="BTC/USD",
                    timeframe="5T",
                    monitor=0,
                    position={"x": 960, "y": 0, "width": 960, "height": 540},
                ),
                ChartConfig(
                    symbol="BTC/USD",
                    timeframe="1H",
                    monitor=0,
                    position={"x": 0, "y": 540, "width": 960, "height": 540},
                ),
                ChartConfig(
                    symbol="BTC/USD",
                    timeframe="1D",
                    monitor=0,
                    position={"x": 960, "y": 540, "width": 960, "height": 540},
                ),
            ],
            sync_crosshair=True,
            layout_id="default_mtf4",
        )

        logger.info("Created default layouts")
