"""Support/Resistance Zone Management for Chart Marking System.

Handles the creation, storage, and removal of support/resistance zones.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from ..models import Zone, ZoneType

logger = logging.getLogger(__name__)


class ZoneManager:
    """Manages support/resistance zones on the chart.

    This class handles the creation, storage, and removal of zones.
    It delegates the actual chart rendering to a callback function
    that communicates with the JavaScript zone manager.
    """

    def __init__(self, on_update: Optional[Callable[[], None]] = None):
        """Initialize the zone manager.

        Args:
            on_update: Callback to invoke when zones change (triggers chart update)
        """
        self._zones: dict[str, Zone] = {}
        self._on_update = on_update
        self._id_counter = 0

    def _generate_id(self, zone_type: ZoneType) -> str:
        """Generate a unique zone ID."""
        self._id_counter += 1
        prefix = zone_type.value.lower()
        return f"{prefix}_{int(datetime.now().timestamp() * 1000)}_{self._id_counter}"

    def _normalize_time(self, ts: int | datetime) -> int:
        """Convert timestamp to Unix seconds."""
        if isinstance(ts, datetime):
            return int(ts.timestamp())
        return ts

    def add(
        self,
        zone_id: Optional[str],
        zone_type: ZoneType | str,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        opacity: float = 0.3,
        label: str = "",
        color: Optional[str] = None,
    ) -> str:
        """Add a zone.

        Args:
            zone_id: Unique identifier (auto-generated if None)
            zone_type: Type (support/resistance/demand/supply)
            start_time: Zone start timestamp
            end_time: Zone end timestamp
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            opacity: Fill opacity (0-1)
            label: Zone label text
            color: Optional custom fill color

        Returns:
            Zone ID
        """
        if isinstance(zone_type, str):
            zone_type = ZoneType(zone_type.lower())

        if zone_id is None:
            zone_id = self._generate_id(zone_type)

        # Ensure prices are in correct order
        if top_price < bottom_price:
            top_price, bottom_price = bottom_price, top_price

        zone = Zone(
            id=zone_id,
            zone_type=zone_type,
            start_time=self._normalize_time(start_time),
            end_time=self._normalize_time(end_time),
            top_price=top_price,
            bottom_price=bottom_price,
            color=color,
            opacity=opacity,
            label=label,
            is_active=True,
        )

        self._zones[zone_id] = zone
        logger.debug(
            f"Added zone: {zone_id} {zone_type.value} "
            f"({top_price:.2f}-{bottom_price:.2f})"
        )

        if self._on_update:
            self._on_update()

        return zone_id

    def add_support(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Support",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a support zone (convenience method).

        Args:
            start_time: Zone start timestamp
            end_time: Zone end timestamp
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label
            zone_id: Optional custom ID
            opacity: Fill opacity

        Returns:
            Zone ID
        """
        return self.add(
            zone_id, ZoneType.SUPPORT, start_time, end_time,
            top_price, bottom_price, opacity, label
        )

    def add_resistance(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Resistance",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a resistance zone (convenience method).

        Args:
            start_time: Zone start timestamp
            end_time: Zone end timestamp
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label
            zone_id: Optional custom ID
            opacity: Fill opacity

        Returns:
            Zone ID
        """
        return self.add(
            zone_id, ZoneType.RESISTANCE, start_time, end_time,
            top_price, bottom_price, opacity, label
        )

    def add_demand(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Demand",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a demand zone (convenience method).

        Args:
            start_time: Zone start timestamp
            end_time: Zone end timestamp
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label
            zone_id: Optional custom ID
            opacity: Fill opacity

        Returns:
            Zone ID
        """
        return self.add(
            zone_id, ZoneType.DEMAND, start_time, end_time,
            top_price, bottom_price, opacity, label
        )

    def add_supply(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Supply",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a supply zone (convenience method).

        Args:
            start_time: Zone start timestamp
            end_time: Zone end timestamp
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            label: Zone label
            zone_id: Optional custom ID
            opacity: Fill opacity

        Returns:
            Zone ID
        """
        return self.add(
            zone_id, ZoneType.SUPPLY, start_time, end_time,
            top_price, bottom_price, opacity, label
        )

    def update(
        self,
        zone_id: str,
        start_time: Optional[int | datetime] = None,
        end_time: Optional[int | datetime] = None,
        top_price: Optional[float] = None,
        bottom_price: Optional[float] = None,
    ) -> bool:
        """Update a zone's dimensions.

        Args:
            zone_id: ID of zone to update
            start_time: New start timestamp (None = keep current)
            end_time: New end timestamp (None = keep current)
            top_price: New upper price (None = keep current)
            bottom_price: New lower price (None = keep current)

        Returns:
            True if updated, False if not found
        """
        zone = self._zones.get(zone_id)
        if not zone:
            return False

        # GUARD: Check if locked
        if zone.is_locked:
            logger.warning(f"Cannot update locked zone: {zone_id}")
            return False

        if start_time is not None:
            zone.start_time = self._normalize_time(start_time)
        if end_time is not None:
            zone.end_time = self._normalize_time(end_time)
        if top_price is not None:
            zone.top_price = top_price
        if bottom_price is not None:
            zone.bottom_price = bottom_price

        # Ensure prices are in correct order
        if zone.top_price < zone.bottom_price:
            zone.top_price, zone.bottom_price = zone.bottom_price, zone.top_price

        logger.debug(f"Updated zone: {zone_id}")

        if self._on_update:
            self._on_update()

        return True

    def extend_zone(self, zone_id: str, new_end_time: int | datetime) -> bool:
        """Extend a zone's end time.

        Args:
            zone_id: ID of zone to extend
            new_end_time: New end timestamp

        Returns:
            True if extended, False if not found
        """
        return self.update(zone_id, end_time=new_end_time)

    def set_active(self, zone_id: str, is_active: bool) -> bool:
        """Set zone active status.

        Args:
            zone_id: Zone ID
            is_active: Whether zone is active

        Returns:
            True if updated, False if not found
        """
        zone = self._zones.get(zone_id)
        if not zone:
            return False

        zone.is_active = is_active
        logger.debug(f"Zone {zone_id} active status: {is_active}")

        if self._on_update:
            self._on_update()

        return True

    def set_locked(self, zone_id: str, is_locked: bool) -> bool:
        """Set zone lock status.

        Args:
            zone_id: Zone ID
            is_locked: Whether zone is locked

        Returns:
            True if updated, False if not found
        """
        zone = self._zones.get(zone_id)
        if not zone:
            return False

        zone.is_locked = is_locked
        logger.debug(f"Zone {zone_id} locked={is_locked}")

        # Note: No chart update needed as visual state unchanged (icon added in JS layer)
        return True

    def toggle_locked(self, zone_id: str) -> bool | None:
        """Toggle zone lock status.

        Args:
            zone_id: Zone ID

        Returns:
            New lock state, or None if zone not found
        """
        zone = self._zones.get(zone_id)
        if not zone:
            return None

        zone.is_locked = not zone.is_locked
        logger.debug(f"Zone {zone_id} toggled to {'locked' if zone.is_locked else 'unlocked'}")
        return zone.is_locked

    def remove(self, zone_id: str) -> bool:
        """Remove a zone.

        Args:
            zone_id: ID of zone to remove

        Returns:
            True if removed, False if not found
        """
        if zone_id in self._zones:
            del self._zones[zone_id]
            logger.debug(f"Removed zone: {zone_id}")

            if self._on_update:
                self._on_update()
            return True
        return False

    def clear(self) -> None:
        """Remove all zones."""
        count = len(self._zones)
        self._zones.clear()
        logger.debug(f"Cleared {count} zones")

        if self._on_update:
            self._on_update()

    def clear_by_type(self, zone_type: ZoneType | str) -> int:
        """Remove all zones of a specific type.

        Args:
            zone_type: Type to remove

        Returns:
            Number of zones removed
        """
        if isinstance(zone_type, str):
            zone_type = ZoneType(zone_type.lower())

        to_remove = [zid for zid, z in self._zones.items() if z.zone_type == zone_type]
        for zid in to_remove:
            del self._zones[zid]

        if to_remove and self._on_update:
            self._on_update()

        logger.debug(f"Cleared {len(to_remove)} {zone_type.value} zones")
        return len(to_remove)

    def get(self, zone_id: str) -> Optional[Zone]:
        """Get a zone by ID."""
        return self._zones.get(zone_id)

    def get_all(self) -> list[Zone]:
        """Get all zones."""
        return list(self._zones.values())

    def get_active(self) -> list[Zone]:
        """Get all active zones."""
        return [z for z in self._zones.values() if z.is_active]

    def get_by_type(self, zone_type: ZoneType | str) -> list[Zone]:
        """Get all zones of a specific type."""
        if isinstance(zone_type, str):
            zone_type = ZoneType(zone_type.lower())
        return [z for z in self._zones.values() if z.zone_type == zone_type]

    def get_zones_at_price(self, price: float) -> list[Zone]:
        """Get all zones that contain a given price.

        Args:
            price: Price level to check

        Returns:
            List of zones containing the price
        """
        return [
            z for z in self._zones.values()
            if z.is_active and z.bottom_price <= price <= z.top_price
        ]

    def get_chart_zones(self) -> list[dict[str, Any]]:
        """Get all zones in chart format for JavaScript."""
        zones = []
        for zone in self._zones.values():
            if not zone.is_active:
                continue
            zones.append({
                "id": zone.id,
                "startTime": zone.start_time,
                "endTime": zone.end_time,
                "topPrice": zone.top_price,
                "bottomPrice": zone.bottom_price,
                "fillColor": zone.fill_color,
                "borderColor": zone.border_color,
                "opacity": zone.opacity,
                "label": zone.label,
                "isLocked": zone.is_locked,
            })
        return zones

    def to_state(self) -> list[dict[str, Any]]:
        """Get state for persistence."""
        return [z.to_dict() for z in self._zones.values()]

    def restore_state(self, state: list[dict[str, Any]]) -> None:
        """Restore state from persistence."""
        self._zones.clear()
        for data in state:
            try:
                zone = Zone.from_dict(data)
                self._zones[zone.id] = zone
            except Exception as e:
                logger.warning(f"Failed to restore zone: {e}")

        logger.debug(f"Restored {len(self._zones)} zones")

        if self._on_update:
            self._on_update()

    def __len__(self) -> int:
        """Return number of zones."""
        return len(self._zones)

    def __contains__(self, zone_id: str) -> bool:
        """Check if zone exists."""
        return zone_id in self._zones
