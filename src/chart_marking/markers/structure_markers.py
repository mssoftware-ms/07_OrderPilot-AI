"""Structure Break Marker Management for Chart Marking System.

Handles BoS (Break of Structure) and CHoCH (Change of Character) markers.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from ..base_manager import BaseChartElementManager
from ..models import Direction, StructureBreakMarker, StructureBreakType

logger = logging.getLogger(__name__)


class StructureMarkerManager(BaseChartElementManager[StructureBreakMarker]):
    """Manages structure break markers (BoS/CHoCH) on the chart.

    Structure breaks indicate significant market structure changes:
    - BoS (Break of Structure): Continuation of trend
    - CHoCH (Change of Character): Potential trend reversal
    - MSB (Market Structure Break): Generic structure break

    Inherits common CRUD operations from BaseChartElementManager.
    """

    def _get_item_class(self) -> type[StructureBreakMarker]:
        """Return StructureBreakMarker class for deserialization."""
        return StructureBreakMarker

    def _get_item_type_name(self) -> str:
        """Return type name for logging."""
        return "structure marker"

    @property
    def _markers(self) -> dict[str, StructureBreakMarker]:
        """Backward compatibility alias for _items."""
        return self._items

    def _generate_id(self, break_type: StructureBreakType) -> str:
        """Generate a unique marker ID based on break type."""
        prefix = break_type.value.lower()
        return super()._generate_id(prefix)

    def add(
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
            direction: "bullish"/"bearish" or "long"/"short"
            text: Display text

        Returns:
            Marker ID
        """
        if isinstance(break_type, str):
            break_type = StructureBreakType(break_type)
        if isinstance(direction, str):
            direction = Direction(direction.lower())

        if marker_id is None:
            marker_id = self._generate_id(break_type)

        marker = StructureBreakMarker(
            id=marker_id,
            timestamp=timestamp,
            price=price,
            break_type=break_type,
            direction=direction,
            text=text or break_type.value,
        )

        self._items[marker_id] = marker
        logger.debug(f"Added structure marker: {marker_id} {break_type.value} {direction.value} @ {price}")

        self._trigger_update()

        return marker_id

    def add_bos(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "BoS",
    ) -> str:
        """Add a Break of Structure marker (convenience method).

        Args:
            timestamp: Break timestamp
            price: Break price level
            is_bullish: True for bullish, False for bearish
            marker_id: Optional custom ID
            text: Display text

        Returns:
            Marker ID
        """
        direction = Direction.BULLISH if is_bullish else Direction.BEARISH
        return self.add(marker_id, timestamp, price, StructureBreakType.BOS, direction, text)

    def add_choch(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "CHoCH",
    ) -> str:
        """Add a Change of Character marker (convenience method).

        Args:
            timestamp: Break timestamp
            price: Break price level
            is_bullish: True for bullish, False for bearish
            marker_id: Optional custom ID
            text: Display text

        Returns:
            Marker ID
        """
        direction = Direction.BULLISH if is_bullish else Direction.BEARISH
        return self.add(marker_id, timestamp, price, StructureBreakType.CHOCH, direction, text)

    def add_msb(
        self,
        timestamp: int | datetime,
        price: float,
        is_bullish: bool = True,
        marker_id: Optional[str] = None,
        text: str = "MSB",
    ) -> str:
        """Add a Market Structure Break marker (convenience method).

        Args:
            timestamp: Break timestamp
            price: Break price level
            is_bullish: True for bullish, False for bearish
            marker_id: Optional custom ID
            text: Display text

        Returns:
            Marker ID
        """
        direction = Direction.BULLISH if is_bullish else Direction.BEARISH
        return self.add(marker_id, timestamp, price, StructureBreakType.MSB, direction, text)

    # Inherited from BaseChartElementManager:
    # - remove(marker_id) -> bool
    # - clear() -> None

    def clear_by_type(self, break_type: StructureBreakType | str) -> int:
        """Remove all markers of a specific type.

        Args:
            break_type: Type to remove

        Returns:
            Number of markers removed
        """
        if isinstance(break_type, str):
            break_type = StructureBreakType(break_type)

        to_remove = [mid for mid, m in self._items.items() if m.break_type == break_type]
        for mid in to_remove:
            del self._items[mid]

        if to_remove:
            self._trigger_update()

        logger.debug(f"Cleared {len(to_remove)} {break_type.value} markers")
        return len(to_remove)

    # Inherited from BaseChartElementManager:
    # - set_locked(marker_id, is_locked) -> bool
    # - toggle_locked(marker_id) -> bool | None
    # - get(marker_id) -> Optional[StructureBreakMarker]
    # - get_all() -> list[StructureBreakMarker]

    def get_by_type(self, break_type: StructureBreakType | str) -> list[StructureBreakMarker]:
        """Get all markers of a specific type."""
        if isinstance(break_type, str):
            break_type = StructureBreakType(break_type)
        return [m for m in self._markers.values() if m.break_type == break_type]

    def get_chart_markers(self) -> list[dict[str, Any]]:
        """Get all markers in Lightweight Charts format.

        Returns:
            List of markers sorted by time
        """
        markers = [m.to_chart_marker() for m in self._markers.values()]
        markers.sort(key=lambda m: m["time"])
        return markers

    # Inherited from BaseChartElementManager:
    # - to_state() -> list[dict]
    # - restore_state(state) -> None
    # - __len__() -> int
    # - __contains__(marker_id) -> bool
