"""Stop-Loss Line Management for Chart Marking System.

Handles stop-loss, take-profit, and entry price lines with labels and risk display.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from ..constants import Colors
from ..models import Direction, LineStyle, StopLossLine

logger = logging.getLogger(__name__)


class StopLossLineManager:
    """Manages stop-loss and price lines on the chart.

    This class handles the creation, storage, and removal of horizontal
    price lines including stop-loss, take-profit, and entry levels.
    It supports risk percentage calculation and display.
    """

    def __init__(self, on_update: Optional[Callable[[], None]] = None):
        """Initialize the stop-loss line manager.

        Args:
            on_update: Callback to invoke when lines change (triggers chart update)
        """
        self._lines: dict[str, StopLossLine] = {}
        self._on_update = on_update

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

        self._lines[line_id] = line
        logger.debug(
            f"Added SL line: {line_id} @ {price:.2f} "
            f"(entry: {entry_price}, risk: {line.calculated_risk_pct}%)"
        )

        if self._on_update:
            self._on_update()

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

        self._lines[line_id] = new_line
        logger.debug(f"Updated SL line: {line_id} @ {new_line.price:.2f}")

        if self._on_update:
            self._on_update()

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

    def remove(self, line_id: str) -> bool:
        """Remove a line.

        Args:
            line_id: ID of line to remove

        Returns:
            True if removed, False if not found
        """
        if line_id in self._lines:
            del self._lines[line_id]
            logger.debug(f"Removed SL line: {line_id}")

            if self._on_update:
                self._on_update()
            return True
        return False

    def clear(self) -> None:
        """Remove all lines."""
        count = len(self._lines)
        self._lines.clear()
        logger.debug(f"Cleared {count} SL lines")

        if self._on_update:
            self._on_update()

    def set_locked(self, line_id: str, is_locked: bool) -> bool:
        """Set stop-loss line lock status.

        Args:
            line_id: Line ID
            is_locked: Whether line is locked

        Returns:
            True if updated, False if not found
        """
        line = self._lines.get(line_id)
        if not line:
            return False

        line.is_locked = is_locked
        logger.debug(f"SL line {line_id} locked={is_locked}")
        return True

    def toggle_locked(self, line_id: str) -> bool | None:
        """Toggle stop-loss line lock status.

        Args:
            line_id: Line ID

        Returns:
            New lock state, or None if line not found
        """
        line = self._lines.get(line_id)
        if not line:
            return None

        line.is_locked = not line.is_locked
        logger.debug(f"SL line {line_id} toggled to {'locked' if line.is_locked else 'unlocked'}")
        return line.is_locked

    def get(self, line_id: str) -> Optional[StopLossLine]:
        """Get a line by ID."""
        return self._lines.get(line_id)

    def get_all(self) -> list[StopLossLine]:
        """Get all lines."""
        return list(self._lines.values())

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

    def to_state(self) -> list[dict[str, Any]]:
        """Get state for persistence."""
        return [line.to_dict() for line in self._lines.values()]

    def restore_state(self, state: list[dict[str, Any]]) -> None:
        """Restore state from persistence."""
        self._lines.clear()
        for data in state:
            try:
                line = StopLossLine.from_dict(data)
                self._lines[line.id] = line
            except Exception as e:
                logger.warning(f"Failed to restore SL line: {e}")

        logger.debug(f"Restored {len(self._lines)} SL lines")

        if self._on_update:
            self._on_update()

    def __len__(self) -> int:
        """Return number of lines."""
        return len(self._lines)

    def __contains__(self, line_id: str) -> bool:
        """Check if line exists."""
        return line_id in self._lines
