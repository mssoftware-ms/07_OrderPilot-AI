"""Entry Marker Management for Chart Marking System.

Handles Long/Short entry arrow markers on the chart.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional
from datetime import datetime

from ..base_manager import BaseChartElementManager
from ..models import Direction, EntryMarker

logger = logging.getLogger(__name__)


class EntryMarkerManager(BaseChartElementManager[EntryMarker]):
    """Manages entry markers (Long/Short arrows) on the chart.

    Inherits common CRUD operations, lock management, and state persistence
    from BaseChartElementManager. Only implements entry-specific business logic.
    """

    def _get_item_class(self) -> type[EntryMarker]:
        """Return EntryMarker class for deserialization."""
        return EntryMarker

    def _get_item_type_name(self) -> str:
        """Return type name for logging."""
        return "entry marker"

    # Alias _items as _markers for backward compatibility
    @property
    def _markers(self) -> dict[str, EntryMarker]:
        """Backward compatibility alias for _items."""
        return self._items

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

        self._items[marker_id] = marker
        logger.debug(f"Added entry marker: {marker_id} {direction.value} @ {price}")

        self._trigger_update()

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

    # Inherited from BaseChartElementManager:
    # - remove(marker_id) -> bool
    # - clear() -> None
    # - set_locked(marker_id, is_locked) -> bool
    # - toggle_locked(marker_id) -> bool | None
    # - get(marker_id) -> Optional[EntryMarker]
    # - get_all() -> list[EntryMarker]
    # - to_state() -> list[dict]
    # - restore_state(state) -> None
    # - __len__(), __contains__()

    def get_chart_markers(self) -> list[dict[str, Any]]:
        """Get all markers in Lightweight Charts format.

        Returns:
            List of markers sorted by time
        """
        markers = [m.to_chart_marker() for m in self._markers.values()]
        # Sort by time
        markers.sort(key=lambda m: m["time"])
        return markers
