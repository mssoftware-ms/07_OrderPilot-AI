"""Chart Marking Mixin - Stop-Loss Line Methods.

Refactored from chart_marking_mixin.py monolith.

Module 4/6 of chart_marking_mixin.py split.

Contains:
- Stop-loss line delegation methods
- TP/Entry/Trailing stop convenience methods
"""

from __future__ import annotations

from typing import Optional

from ..constants import Colors
from ..models import Direction, LineStyle


class ChartMarkingLineMethods:
    """Helper für ChartMarkingMixin stop-loss line methods."""

    def __init__(self, parent):
        """
        Args:
            parent: ChartMarkingMixin Instanz
        """
        self.parent = parent

    def add_line(
        self,
        line_id: str,
        price: float,
        color: str,
        label: str = "",
        line_style: str = "solid",
        show_risk: bool = False,
    ) -> str:
        """Add a generic horizontal line.

        Args:
            line_id: Unique identifier
            price: Price level
            color: Line color
            label: Line label
            line_style: "solid", "dashed", or "dotted"
            show_risk: Whether to show risk (requires entry price, defaults to False)

        Returns:
            Line ID
        """
        return self.parent._sl_lines.add(
            line_id, price, None, Direction.LONG,
            color, line_style, label, show_risk
        )

    def add_stop_loss_line(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "SL",
        show_risk: bool = True,
    ) -> str:
        """Add a stop-loss line with optional risk display.

        Args:
            line_id: Unique identifier
            price: Stop-loss price level
            entry_price: Entry price for risk calculation
            is_long: True for long position
            label: Line label
            show_risk: Whether to show risk percentage

        Returns:
            Line ID
        """
        direction = Direction.LONG if is_long else Direction.SHORT
        return self.parent._sl_lines.add(
            line_id, price, entry_price, direction,
            Colors.STOP_LOSS, LineStyle.DASHED, label, show_risk
        )

    def add_take_profit_line(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "TP",
    ) -> str:
        """Add a take-profit line (convenience method)."""
        return self.parent._sl_lines.add_take_profit(line_id, price, entry_price, is_long, label)

    def add_entry_line(
        self,
        line_id: str,
        price: float,
        is_long: bool = True,
        label: str = "Entry",
    ) -> str:
        """Add an entry price line (convenience method)."""
        return self.parent._sl_lines.add_entry_line(line_id, price, is_long, label)

    def add_trailing_stop_line(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "TSL",
    ) -> str:
        """Add a trailing stop line (convenience method)."""
        return self.parent._sl_lines.add_trailing_stop(line_id, price, entry_price, is_long, label)

    def update_stop_loss_line(
        self,
        line_id: str,
        price: Optional[float] = None,
        entry_price: Optional[float] = None,
    ) -> bool:
        """Update a stop-loss line's price levels."""
        return self.parent._sl_lines.update(line_id, price, entry_price)

    def update_trailing_stop(self, line_id: str, new_price: float) -> bool:
        """Update a trailing stop price."""
        return self.parent._sl_lines.update_trailing_stop(line_id, new_price)

    def remove_stop_loss_line(self, line_id: str) -> bool:
        """Remove a stop-loss line."""
        return self.parent._sl_lines.remove(line_id)

    def clear_stop_loss_lines(self) -> None:
        """Remove all stop-loss lines."""
        self.parent._sl_lines.clear()
