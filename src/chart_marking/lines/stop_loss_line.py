"""Stop-Loss Line Management for Chart Marking System.

Handles stop-loss, take-profit, and entry price lines with labels and risk display.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from ..base_manager import BaseChartElementManager
from ..constants import Colors
from ..models import Direction, LineStyle, StopLossLine

logger = logging.getLogger(__name__)


class StopLossLineManager(BaseChartElementManager[StopLossLine]):
    """Manages stop-loss and price lines on the chart.

    Handles stop-loss, take-profit, entry, and trailing stop lines.
    Supports risk percentage calculation and display.
    Inherits common CRUD operations from BaseChartElementManager.
    """

    def _get_item_class(self) -> type[StopLossLine]:
        """Return StopLossLine class for deserialization."""
        return StopLossLine

    def _get_item_type_name(self) -> str:
        """Return type name for logging."""
        return "SL line"

    @property
    def _lines(self) -> dict[str, StopLossLine]:
        """Backward compatibility alias for _items."""
        return self._items

    def add(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        direction: Direction | str = Direction.LONG,
        color: str = Colors.STOP_LOSS,
        line_style: LineStyle | str = LineStyle.DASHED,
        label: str = "SL",
        show_risk: bool = True,
        risk_percent: Optional[float] = None,
    ) -> str:
        """Add a stop-loss line.

        Args:
            line_id: Unique identifier
            price: Stop-loss price level
            entry_price: Entry price for risk calculation
            direction: Position direction (affects risk calculation)
            color: Line color
            line_style: Line style (solid/dashed/dotted)
            label: Line label text
            show_risk: Whether to show risk percentage
            risk_percent: Pre-calculated risk (overrides calculation)

        Returns:
            Line ID
        """
        if isinstance(direction, str):
            direction = Direction(direction.lower())
        if isinstance(line_style, str):
            line_style = LineStyle(line_style.lower())

        line = StopLossLine(
            id=line_id,
            price=price,
            entry_price=entry_price,
            direction=direction,
            color=color,
            line_style=line_style,
            label=label,
            show_risk=show_risk,
            risk_percent=risk_percent,
        )

        self._items[line_id] = line
        logger.debug(
            f"Added SL line: {line_id} @ {price:.2f} "
            f"(entry: {entry_price}, risk: {line.calculated_risk_pct}%)"
        )

        self._trigger_update()

        return line_id

    def add_stop_loss(
        self,
        line_id: str,
        price: float,
        entry_price: float,
        is_long: bool = True,
        label: str = "SL",
    ) -> str:
        """Add a stop-loss line with risk display (convenience method).

        Args:
            line_id: Unique identifier
            price: Stop-loss price level
            entry_price: Entry price
            is_long: True for long position
            label: Line label

        Returns:
            Line ID
        """
        direction = Direction.LONG if is_long else Direction.SHORT
        return self.add(
            line_id, price, entry_price, direction,
            Colors.STOP_LOSS, LineStyle.DASHED, label, show_risk=True
        )

    def add_take_profit(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "TP",
    ) -> str:
        """Add a take-profit line (convenience method).

        Args:
            line_id: Unique identifier
            price: Take-profit price level
            entry_price: Optional entry price for R:R display
            is_long: True for long position
            label: Line label

        Returns:
            Line ID
        """
        direction = Direction.LONG if is_long else Direction.SHORT
        return self.add(
            line_id, price, entry_price, direction,
            Colors.TAKE_PROFIT, LineStyle.DASHED, label, show_risk=False
        )

    def add_entry_line(
        self,
        line_id: str,
        price: float,
        is_long: bool = True,
        label: str = "Entry",
    ) -> str:
        """Add an entry price line (convenience method).

        Args:
            line_id: Unique identifier
            price: Entry price level
            is_long: True for long position
            label: Line label

        Returns:
            Line ID
        """
        direction = Direction.LONG if is_long else Direction.SHORT
        return self.add(
            line_id, price, None, direction,
            Colors.ENTRY_LINE, LineStyle.SOLID, label, show_risk=False
        )

    def add_trailing_stop(
        self,
        line_id: str,
        price: float,
        entry_price: Optional[float] = None,
        is_long: bool = True,
        label: str = "TSL",
    ) -> str:
        """Add a trailing stop line (convenience method).

        Args:
            line_id: Unique identifier
            price: Current trailing stop price
            entry_price: Optional entry price for risk display
            is_long: True for long position
            label: Line label

        Returns:
            Line ID
        """
        direction = Direction.LONG if is_long else Direction.SHORT
        return self.add(
            line_id, price, entry_price, direction,
            Colors.TRAILING_STOP, LineStyle.DOTTED, label, show_risk=entry_price is not None
        )

    def update(
        self,
        line_id: str,
        price: Optional[float] = None,
        entry_price: Optional[float] = None,
    ) -> bool:
        """Update a line's price levels.

        Args:
            line_id: ID of line to update
            price: New price level (None = keep current)
            entry_price: New entry price (None = keep current)

        Returns:
            True if updated, False if not found
        """
        line = self._lines.get(line_id)
        if not line:
            return False

        # Create new line with updated values
        new_line = StopLossLine(
            id=line.id,
            price=price if price is not None else line.price,
            entry_price=entry_price if entry_price is not None else line.entry_price,
            direction=line.direction,
            color=line.color,
            line_style=line.line_style,
            label=line.label,
            show_risk=line.show_risk,
            risk_percent=None,  # Recalculate
        )

        self._items[line_id] = new_line
        logger.debug(f"Updated SL line: {line_id} @ {new_line.price:.2f}")

        self._trigger_update()

        return True

    def update_trailing_stop(self, line_id: str, new_price: float) -> bool:
        """Update a trailing stop price (convenience method).

        Args:
            line_id: ID of trailing stop line
            new_price: New stop price

        Returns:
            True if updated, False if not found
        """
        return self.update(line_id, price=new_price)

    # Inherited from BaseChartElementManager:
    # - remove(line_id) -> bool
    # - clear() -> None
    # - set_locked(line_id, is_locked) -> bool
    # - toggle_locked(line_id) -> bool | None
    # - get(line_id) -> Optional[StopLossLine]
    # - get_all() -> list[StopLossLine]

    def get_chart_lines(self) -> list[dict[str, Any]]:
        """Get all lines in chart format for JavaScript."""
        from ..constants import LineStyles

        style_map = {
            LineStyle.SOLID: LineStyles.JS_SOLID,
            LineStyle.DASHED: LineStyles.JS_DASHED,
            LineStyle.DOTTED: LineStyles.JS_DOTTED,
        }

        lines = []
        for line in self._lines.values():
            lines.append({
                "id": line.id,
                "price": line.price,
                "color": line.color,
                "lineStyle": style_map.get(line.line_style, LineStyles.JS_DASHED),
                "lineWidth": 1,
                "axisLabelVisible": True,
                "title": line.display_label,
            })
        return lines

    # Inherited from BaseChartElementManager:
    # - to_state() -> list[dict]
    # - restore_state(state) -> None
    # - __len__() -> int
    # - __contains__(line_id) -> bool
