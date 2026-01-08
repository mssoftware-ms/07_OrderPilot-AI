"""Chart AI Markings Mixin - Methods for AI-driven chart markings.

Provides methods to add markings from AI analysis:
- Horizontal lines (Stop Loss, Take Profit)
- Price zones (Support, Resistance, Demand, Supply)
- Entry markers (Long, Short)

Refactored to delegate to ChartMarkingMixin for unified state management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.chart_marking.models import ZoneType

logger = logging.getLogger(__name__)


class ChartAIMarkingsMixin:
    """Mixin for AI-driven chart markings via ChartMarkingMixin."""

    def add_horizontal_line(self, price: float, label: str = "", color: str = "#0d6efd") -> str:
        """Add a horizontal line at specified price.

        Args:
            price: Price level for the line
            label: Label text for the line (e.g., "SL", "TP", "Entry")
            color: Line color (hex format, e.g., '#ff0000')

        Returns:
            ID of the created line

        Note:
            Parameter order is (price, label, color) to match EmbeddedTradingViewChart
            and evaluation_dialog.py usage. Issue #26 fix.
        """
        safe_label = label or ""
        line_id = f"ai_{safe_label.lower().replace(' ', '_')}_{int(price)}"

        # Delegate to ChartMarkingMixin's generic add_line
        if hasattr(self, "add_line"):
            return self.add_line(
                line_id=line_id,
                price=price,
                color=color,
                label=safe_label,
                line_style="solid",
                show_risk=False
            )

        logger.error("add_line not found in parent class")
        return ""

    def add_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        fill_color: str,
        border_color: str,
        label: str,
    ) -> str:
        """Add a price zone (rectangle) to the chart.

        Args:
            start_time: Start timestamp (Unix seconds)
            end_time: End timestamp (Unix seconds)
            top_price: Upper price boundary
            bottom_price: Lower price boundary
            fill_color: Fill color (rgba format)
            border_color: Border color (hex format) - Ignored in favor of ZoneType defaults + fill_color
            label: Zone label

        Returns:
            ID of the created zone
        """
        # Determine zone type from label for correct categorization
        from src.chart_marking.models import ZoneType
        
        z_type = ZoneType.SUPPORT
        l_lower = label.lower()
        if "resistance" in l_lower:
            z_type = ZoneType.RESISTANCE
        elif "demand" in l_lower:
            z_type = ZoneType.DEMAND
        elif "supply" in l_lower:
            z_type = ZoneType.SUPPLY

        zone_id = f"ai_zone_{label.lower().replace(' ', '_')}_{int(bottom_price)}"

        # Delegate to ChartMarkingMixin.add_zone
        # We pass fill_color as 'color' to override default type color
        if hasattr(super(), "add_zone"):
            return super().add_zone(
                zone_id=zone_id,
                zone_type=z_type,
                start_time=start_time,
                end_time=end_time,
                top_price=top_price,
                bottom_price=bottom_price,
                opacity=0.15,  # Default AI opacity
                label=label,
                color=fill_color
            )
            
        logger.error("add_zone not found in parent class")
        return ""

    def add_support_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Support",
    ) -> str:
        """Add a support zone (green)."""
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(38, 166, 154, 0.15)",  # Light teal/green
            border_color="#26a69a",
            label=label,
        )

    def add_resistance_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Resistance",
    ) -> str:
        """Add a resistance zone (red)."""
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(239, 83, 80, 0.15)",  # Light red
            border_color="#ef5350",
            label=label,
        )

    def add_demand_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Demand",
    ) -> str:
        """Add a demand zone (blue)."""
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(33, 150, 243, 0.15)",  # Light blue
            border_color="#2196f3",
            label=label,
        )

    def add_supply_zone(
        self,
        start_time: int,
        end_time: int,
        top_price: float,
        bottom_price: float,
        label: str = "Supply",
    ) -> str:
        """Add a supply zone (orange)."""
        return self.add_zone(
            start_time,
            end_time,
            top_price,
            bottom_price,
            fill_color="rgba(255, 152, 0, 0.15)",  # Light orange
            border_color="#ff9800",
            label=label,
        )

    def add_long_entry(self, timestamp: int, price: float, label: str = "Long Entry") -> str:
        """Add a long entry marker (green arrow up)."""
        marker_id = f"ai_long_{int(timestamp)}_{int(price)}"
        
        if hasattr(super(), "add_long_entry"):
            return super().add_long_entry(
                timestamp=timestamp,
                price=price,
                text=label,
                marker_id=marker_id
            )
            
        logger.error("add_long_entry not found in parent class")
        return ""

    def add_short_entry(self, timestamp: int, price: float, label: str = "Short Entry") -> str:
        """Add a short entry marker (red arrow down)."""
        marker_id = f"ai_short_{int(timestamp)}_{int(price)}"
        
        if hasattr(super(), "add_short_entry"):
            return super().add_short_entry(
                timestamp=timestamp,
                price=price,
                text=label,
                marker_id=marker_id
            )

        logger.error("add_short_entry not found in parent class")
        return ""