"""Entry Marker Management for Chart Marking System.

Handles Long/Short entry arrow markers on the chart.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from ..models import Direction, EntryMarker

logger = logging.getLogger(__name__)


class EntryMarkerManager:
    """Manages entry markers (Long/Short arrows) on the chart.

    This class handles the creation, storage, and removal of entry markers.
    It delegates the actual chart rendering to a callback function.
    """

    def __init__(self, on_update: Optional[Callable[[], None]] = None):
        """Initialize the entry marker manager.

        Args:
            on_update: Callback to invoke when markers change (triggers chart update)
        """
        self._markers: dict[str, EntryMarker] = {}
        self._on_update = on_update
        self._id_counter = 0

    def _generate_id(self, prefix: str = "entry") -> str:
        """Generate a unique marker ID."""
        self._id_counter += 1
        return f"{prefix}_{int(datetime.now().timestamp() * 1000)}_{self._id_counter}"

    def add(
        self,
        marker_id: Optional[str],
        timestamp: int | datetime,
        price: float,
        direction: Direction | str,
        text: str = "",
        tooltip: str = "",
        score: Optional[float] = None,
    ) -> str:
        """Add an entry marker.

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
        if isinstance(direction, str):
            direction = Direction(direction.lower())

        if marker_id is None:
            prefix = "long" if direction in (Direction.LONG, Direction.BULLISH) else "short"
            marker_id = self._generate_id(prefix)

        marker = EntryMarker(
            id=marker_id,
            timestamp=timestamp,
            price=price,
            direction=direction,
            text=text,
            tooltip=tooltip,
            score=score,
        )

        self._markers[marker_id] = marker
        logger.debug(f"Added entry marker: {marker_id} {direction.value} @ {price}")

        if self._on_update:
            self._on_update()

        return marker_id

    def add_long(
        self,
        timestamp: int | datetime,
        price: float,
        text: str = "Long Entry",
        marker_id: Optional[str] = None,
        score: Optional[float] = None,
    ) -> str:
        """Add a long entry marker (convenience method).

        Args:
            timestamp: Bar timestamp
            price: Entry price
            text: Display text
            marker_id: Optional custom ID
            score: Optional signal score

        Returns:
            Marker ID
        """
        return self.add(marker_id, timestamp, price, Direction.LONG, text, score=score)

    def add_short(
        self,
        timestamp: int | datetime,
        price: float,
        text: str = "Short Entry",
        marker_id: Optional[str] = None,
        score: Optional[float] = None,
    ) -> str:
        """Add a short entry marker (convenience method).

        Args:
            timestamp: Bar timestamp
            price: Entry price
            text: Display text
            marker_id: Optional custom ID
            score: Optional signal score

        Returns:
            Marker ID
        """
        return self.add(marker_id, timestamp, price, Direction.SHORT, text, score=score)

    def remove(self, marker_id: str) -> bool:
        """Remove an entry marker.

        Args:
            marker_id: ID of marker to remove

        Returns:
            True if removed, False if not found
        """
        if marker_id in self._markers:
            del self._markers[marker_id]
            logger.debug(f"Removed entry marker: {marker_id}")

            if self._on_update:
                self._on_update()
            return True
        return False

    def clear(self) -> None:
        """Remove all entry markers."""
        count = len(self._markers)
        self._markers.clear()
        logger.debug(f"Cleared {count} entry markers")

        if self._on_update:
            self._on_update()

    def set_locked(self, marker_id: str, is_locked: bool) -> bool:
        """Set entry marker lock status.

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
        logger.debug(f"Entry marker {marker_id} locked={is_locked}")
        return True

    def toggle_locked(self, marker_id: str) -> bool | None:
        """Toggle entry marker lock status.

        Args:
            marker_id: Marker ID

        Returns:
            New lock state, or None if marker not found
        """
        marker = self._markers.get(marker_id)
        if not marker:
            return None

        marker.is_locked = not marker.is_locked
        logger.debug(f"Entry marker {marker_id} toggled to {'locked' if marker.is_locked else 'unlocked'}")
        return marker.is_locked

    def get(self, marker_id: str) -> Optional[EntryMarker]:
        """Get a marker by ID."""
        return self._markers.get(marker_id)

    def get_all(self) -> list[EntryMarker]:
        """Get all markers."""
        return list(self._markers.values())

    def get_chart_markers(self) -> list[dict[str, Any]]:
        """Get all markers in Lightweight Charts format."""
        markers = [m.to_chart_marker() for m in self._markers.values()]
        # Sort by time
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
                marker = EntryMarker.from_dict(data)
                self._markers[marker.id] = marker
            except Exception as e:
                logger.warning(f"Failed to restore entry marker: {e}")

        logger.debug(f"Restored {len(self._markers)} entry markers")

        if self._on_update:
            self._on_update()

    def __len__(self) -> int:
        """Return number of markers."""
        return len(self._markers)

    def __contains__(self, marker_id: str) -> bool:
        """Check if marker exists."""
        return marker_id in self._markers
