"""Layout Persistence - Save/Load Layouts to JSON.

Refactored from layout_manager.py.

Contains:
- save_layout: Save layout to JSON file
- load_layout: Load layout from JSON file
- get_available_layouts: List available layout names
- delete_layout: Delete a layout file
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .layout_config_models import ChartLayoutConfig
    from .layout_manager import ChartLayoutManager

logger = logging.getLogger(__name__)


class LayoutPersistence:
    """Helper for layout file persistence."""

    def __init__(self, parent: "ChartLayoutManager"):
        self.parent = parent

    def save_layout(self, layout: "ChartLayoutConfig") -> bool:
        """Save a layout configuration to file.

        Args:
            layout: The layout to save

        Returns:
            True if successful
        """
        try:
            filepath = self.parent._layouts_dir / f"{layout.name}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(layout.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved layout: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save layout: {e}")
            return False

    def load_layout(self, name: str) -> "ChartLayoutConfig | None":
        """Load a layout configuration from file.

        Args:
            name: Layout name (without .json extension)

        Returns:
            ChartLayoutConfig or None if not found
        """
        from .layout_config_models import ChartLayoutConfig

        try:
            filepath = self.parent._layouts_dir / f"{name}.json"
            if not filepath.exists():
                logger.warning(f"Layout not found: {filepath}")
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            return ChartLayoutConfig.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load layout: {e}")
            return None

    def get_available_layouts(self) -> list[str]:
        """Get list of available layout names."""
        layouts = []
        for filepath in self.parent._layouts_dir.glob("*.json"):
            layouts.append(filepath.stem)
        return sorted(layouts)

    def delete_layout(self, name: str) -> bool:
        """Delete a saved layout.

        Args:
            name: Layout name to delete

        Returns:
            True if successful
        """
        try:
            filepath = self.parent._layouts_dir / f"{name}.json"
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted layout: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete layout: {e}")
            return False
