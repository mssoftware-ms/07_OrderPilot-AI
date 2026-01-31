"""Chart Marking Mixin - Structure Break Marker Methods.

Refactored from chart_marking_mixin.py monolith.

Module 2/6 of chart_marking_mixin.py split.

Contains:
- Structure break marker delegation methods
- BoS/CHoCH/MSB convenience methods
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..models import Direction, StructureBreakType
from .chart_marking_base import ChartMarkingBase


class ChartMarkingStructureMethods(ChartMarkingBase):
    """Helper für ChartMarkingMixin structure break marker methods."""

    def add_structure_break(
        self,
        marker_id: Optional[str],
        timestamp: int | datetime,
        price: float,
        break_type: StructureBreakType | str,
        direction: Direction | str,
        text: str = "",
    ) -> str:
        """Add a structure break marker.

        Args:
            marker_id: Unique identifier (auto-generated if None)
            timestamp: Break timestamp
            price: Break price level
            break_type: "BoS", "CHoCH", or "MSB"
            direction: "bullish"/"bearish"
            text: Display text

        Returns:
            Marker ID
        """
        return self.parent._structure_markers.add(
            marker_id, timestamp, price, break_type, direction, text
        )

    def add_bos(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "BoS",
    ) -> str:
        """Add a Break of Structure marker (convenience method)."""
        return self.parent._structure_markers.add_bos(timestamp, price, is_bullish, marker_id, text)

    def add_choch(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "CHoCH",
    ) -> str:
        """Add a Change of Character marker (convenience method)."""
        return self.parent._structure_markers.add_choch(timestamp, price, is_bullish, marker_id, text)

    def add_msb(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "MSB",
    ) -> str:
        """Add a Market Structure Break marker (convenience method)."""
        return self.parent._structure_markers.add_msb(timestamp, price, is_bullish, marker_id, text)

    def remove_structure_break(self, marker_id: str) -> bool:
        """Remove a structure break marker."""
        return self.parent._structure_markers.remove(marker_id)

    def clear_structure_breaks(self) -> None:
        """Remove all structure break markers."""
        self.parent._structure_markers.clear()

    def clear_structure_breaks_by_type(self, break_type: StructureBreakType | str) -> int:
        """Remove all structure breaks of a specific type."""
        return self.parent._structure_markers.clear_by_type(break_type)
