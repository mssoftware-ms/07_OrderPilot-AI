"""Chart Marking Mixin - Zone Methods.

Refactored from chart_marking_mixin.py monolith.

Module 3/6 of chart_marking_mixin.py split.

Contains:
- Zone delegation methods (add, update, extend, remove, clear)
- Support/Resistance/Demand/Supply convenience methods
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from ..models import ZoneType

logger = logging.getLogger(__name__)


class ChartMarkingZoneMethods:
    """Helper für ChartMarkingMixin zone methods."""

    def __init__(self, parent):
        """
        Args:
            parent: ChartMarkingMixin Instanz
        """
        self.parent = parent

    def add_zone(
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
        """Add a support/resistance zone.

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
        logger.debug(f"ChartMarkingMixin.add_zone called: {label} ({zone_type}) [{bottom_price}-{top_price}]")
        return self.parent._zones.add(
            zone_id, zone_type, start_time, end_time,
            top_price, bottom_price, opacity, label, color
        )

    def add_support_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Support",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a support zone (convenience method)."""
        return self.parent._zones.add_support(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def add_resistance_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Resistance",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a resistance zone (convenience method)."""
        return self.parent._zones.add_resistance(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def add_demand_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Demand",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a demand zone (convenience method)."""
        return self.parent._zones.add_demand(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def add_supply_zone(
        self,
        start_time: int | datetime,
        end_time: int | datetime,
        top_price: float,
        bottom_price: float,
        label: str = "Supply",
        zone_id: Optional[str] = None,
        opacity: float = 0.3,
    ) -> str:
        """Add a supply zone (convenience method)."""
        return self.parent._zones.add_supply(
            start_time, end_time, top_price, bottom_price, label, zone_id, opacity
        )

    def update_zone(
        self,
        zone_id: str,
        start_time: Optional[int | datetime] = None,
        end_time: Optional[int | datetime] = None,
        top_price: Optional[float] = None,
        bottom_price: Optional[float] = None,
    ) -> bool:
        """Update a zone's dimensions."""
        return self.parent._zones.update(zone_id, start_time, end_time, top_price, bottom_price)

    def extend_zone(self, zone_id: str, new_end_time: int | datetime) -> bool:
        """Extend a zone's end time."""
        return self.parent._zones.extend_zone(zone_id, new_end_time)

    def remove_zone(self, zone_id: str) -> bool:
        """Remove a zone."""
        return self.parent._zones.remove(zone_id)

    def clear_zones(self) -> None:
        """Remove all zones."""
        self.parent._zones.clear()

    def clear_zones_by_type(self, zone_type: ZoneType | str) -> int:
        """Remove all zones of a specific type."""
        return self.parent._zones.clear_by_type(zone_type)
