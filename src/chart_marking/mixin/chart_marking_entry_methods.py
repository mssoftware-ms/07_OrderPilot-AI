"""Chart Marking Mixin - Entry Marker Methods.

Refactored from chart_marking_mixin.py monolith.

Module 1/6 of chart_marking_mixin.py split.

Contains:
- Entry marker delegation methods (add, remove, clear)
- Long/short convenience methods
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..models import Direction
from .chart_marking_base import ChartMarkingBase


class ChartMarkingEntryMethods(ChartMarkingBase):
    """Helper für ChartMarkingMixin entry marker methods."""

    def add_entry_marker(
        self,
        marker_id: Optional[str],
        timestamp: int | datetime,
        price: float,
        direction: Direction | str,
        text: str = "",
        tooltip: str = "",
        score: Optional[float] = None,
    ) -> str:
        """Add an entry marker (arrow).

        Args:
            marker_id: Unique identifier (auto-generated if None)
            timestamp: Bar timestamp
            price: Entry price level
            direction: "long"/"short" or Direction enum
            text: Display text
            tooltip: Hover tooltip
            score: Optional signal score

        Returns:
            Marker ID
        """
        return self.parent._entry_markers.add(
            marker_id, timestamp, price, direction, text, tooltip, score
        )

    def add_long_entry(
        self,
        timestamp: int | datetime,
        price: float,
        text: str = "Long Entry",
        marker_id: Optional[str] = None,
        score: Optional[float] = None,
    ) -> str:
        """Add a long entry marker (convenience method)."""
        return self.parent._entry_markers.add_long(timestamp, price, text, marker_id, score)

    def add_short_entry(
        self,
        timestamp: int | datetime,
        price: float,
        text: str = "Short Entry",
        marker_id: Optional[str] = None,
        score: Optional[float] = None,
    ) -> str:
        """Add a short entry marker (convenience method)."""
        return self.parent._entry_markers.add_short(timestamp, price, text, marker_id, score)

    def remove_entry_marker(self, marker_id: str) -> bool:
        """Remove an entry marker."""
        return self.parent._entry_markers.remove(marker_id)

    def clear_entry_markers(self) -> None:
        """Remove all entry markers."""
        self.parent._entry_markers.clear()
