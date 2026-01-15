"""Structure Break Marker Management for Chart Marking System.

Handles BoS (Break of Structure) and CHoCH (Change of Character) markers.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from ..models import Direction, StructureBreakMarker, StructureBreakType

logger = logging.getLogger(__name__)


class StructureMarkerManager:
    """Manages structure break markers (BoS/CHoCH) on the chart.

    Structure breaks indicate significant market structure changes:
    - BoS (Break of Structure): Continuation of trend
    - CHoCH (Change of Character): Potential trend reversal
    - MSB (Market Structure Break): Generic structure break
    """

    def __init__(self, on_update: Optional[Callable[[], None]] = None):
        """Initialize the structure marker manager.

        Args:
            on_update: Callback to invoke when markers change
        """
        self._markers: dict[str, StructureBreakMarker] = {}
        self._on_update = on_update
        self._id_counter = 0

    def _generate_id(self, break_type: StructureBreakType) -> str:
        """Generate a unique marker ID."""
        self._id_counter += 1
        prefix = break_type.value.lower()
        return f"{prefix}_{int(datetime.now().timestamp() * 1000)}_{self._id_counter}"

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

        self._markers[marker_id] = marker
        logger.debug(f"Added structure marker: {marker_id} {break_type.value} {direction.value} @ {price}")

        if self._on_update:
            self._on_update()

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

    def remove(self, marker_id: str) -> bool:
        """Remove a structure marker.

        Args:
            marker_id: ID of marker to remove

        Returns:
            True if removed, False if not found
        """
        if marker_id in self._markers:
            del self._markers[marker_id]
            logger.debug(f"Removed structure marker: {marker_id}")

            if self._on_update:
                self._on_update()
            return True
        return False

    def clear(self) -> None:
        """Remove all structure markers."""
        count = len(self._markers)
        self._markers.clear()
        logger.debug(f"Cleared {count} structure markers")

        if self._on_update:
            self._on_update()

    def clear_by_type(self, break_type: StructureBreakType | str) -> int:
        """Remove all markers of a specific type.

        Args:
            break_type: Type to remove

        Returns:
            Number of markers removed
        """
        if isinstance(break_type, str):
            break_type = StructureBreakType(break_type)

        to_remove = [mid for mid, m in self._markers.items() if m.break_type == break_type]
        for mid in to_remove:
            del self._markers[mid]

        if to_remove and self._on_update:
            self._on_update()

        logger.debug(f"Cleared {len(to_remove)} {break_type.value} markers")
        return len(to_remove)

    def set_locked(self, marker_id: str, is_locked: bool) -> bool:
        """Set structure marker lock status.

        Args:
            marker_id: Marker ID
            is_locked: Whether marker is locked

        Returns:
            True if updated, False if not found
        """
        marker = self._markers.get(marker_id)
        if not marker:
            return False

        marker.is_locked = is_locked
        logger.debug(f"Structure marker {marker_id} locked={is_locked}")
        return True

    def toggle_locked(self, marker_id: str) -> bool | None:
        """Toggle structure marker lock status.

        Args:
            marker_id: Marker ID

        Returns:
            New lock state, or None if marker not found
        """
        marker = self._markers.get(marker_id)
        if not marker:
            return None

        marker.is_locked = not marker.is_locked
        logger.debug(f"Structure marker {marker_id} toggled to {'locked' if marker.is_locked else 'unlocked'}")
        return marker.is_locked

    def get(self, marker_id: str) -> Optional[StructureBreakMarker]:
        """Get a marker by ID."""
        return self._markers.get(marker_id)

    def get_all(self) -> list[StructureBreakMarker]:
        """Get all markers."""
        return list(self._markers.values())

    def get_by_type(self, break_type: StructureBreakType | str) -> list[StructureBreakMarker]:
        """Get all markers of a specific type."""
        if isinstance(break_type, str):
            break_type = StructureBreakType(break_type)
        return [m for m in self._markers.values() if m.break_type == break_type]

    def get_chart_markers(self) -> list[dict[str, Any]]:
        """Get all markers in Lightweight Charts format."""
        markers = [m.to_chart_marker() for m in self._markers.values()]
        markers.sort(key=lambda m: m["time"])
        return markers

    def to_state(self) -> list[dict[str, Any]]:
        """Get state for persistence."""
        return [m.to_dict() for m in self._markers.values()]

    def restore_state(self, state: list[dict[str, Any]]) -> None:
        """Restore state from persistence."""
        self._markers.clear()
        for data in state:
            try:
                marker = StructureBreakMarker.from_dict(data)
                self._markers[marker.id] = marker
            except Exception as e:
                logger.warning(f"Failed to restore structure marker: {e}")

        logger.debug(f"Restored {len(self._markers)} structure markers")

        if self._on_update:
            self._on_update()

    def __len__(self) -> int:
        """Return number of markers."""
        return len(self._markers)

    def __contains__(self, marker_id: str) -> bool:
        """Check if marker exists."""
        return marker_id in self._markers
