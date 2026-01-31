"""Price column updaters (current price, exit price)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem
from .base_updater import BaseColumnUpdater

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTableWidget


class CurrentPriceUpdater(BaseColumnUpdater):
    """Updates current/exit price column (column 11)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the current price column."""
        return column_index == 11

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update current price or exit price for closed positions."""
        current_price = context.get("current_price", signal.get("price", 0))
        status = signal.get("status", "")
        is_closed = status.startswith("CLOSED") or status in ("SL", "TR", "MACD", "RSI", "Sell")

        if is_closed:
            exit_price = signal.get("exit_price", current_price)
            item = QTableWidgetItem(f"{exit_price:.2f}")
        else:
            item = QTableWidgetItem(f"{current_price:.2f}")

        # Make non-editable (PyQt6 compatible)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, column, item)

