"""Position-related column updaters (invest, quantity, liquidation)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem
from .base_updater import BaseColumnUpdater

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTableWidget


class InvestUpdater(BaseColumnUpdater):
    """Updates Invest USDT column (column 16)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the invest column."""
        return column_index == 16

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update invested amount with tooltip."""
        invested = signal.get("invested", 0)
        leverage = context.get("leverage", 1.0)
        position_size = context.get("position_size", 0.0)

        item = QTableWidgetItem(f"{invested:.2f}")
        item.setForeground(QColor("#2196f3"))
        item.setToolTip(
            "Invest USDT (Kapital × Risk%)\n"
            f"Eingesetztes Kapital: {invested:.2f} USDT\n"
            f"Mit Hebel {leverage:.0f}x: {position_size:.2f} USDT Notional"
        )

        # Make non-editable
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, column, item)


class QuantityUpdater(BaseColumnUpdater):
    """Updates quantity/Stück column (column 17)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the quantity column."""
        return column_index == 17

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update quantity with calculation tooltip."""
        quantity = context.get("quantity", 0)
        invested = signal.get("invested", 0)
        leverage = context.get("leverage", 1.0)
        entry_price = signal.get("price", 0)

        text = f"{quantity:.6f}" if quantity > 0 else "-"
        item = QTableWidgetItem(text)
        item.setForeground(QColor("#cfd8dc"))
        item.setToolTip(
            f"Stückzahl (Leveraged Position)\n"
            f"Invested: {invested:.2f} USDT\n"
            f"Hebel: {leverage:.0f}x\n"
            f"Entry: {entry_price:.2f}\n"
            f"Berechnung: ({invested:.2f} × {leverage:.0f}) / {entry_price:.2f} = {quantity:.6f}"
        )

        table.setItem(row, column, item)


class LiquidationUpdater(BaseColumnUpdater):
    """Updates liquidation price column (column 24)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the liquidation column."""
        return column_index == 24

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update liquidation price with detailed tooltip."""
        liquidation_price = context.get("liquidation_price")
        mm_rate = context.get("mm_rate", 0.005)
        mm_rate_default = context.get("mm_rate_default", True)
        margin_buffer = context.get("margin_buffer")
        entry_price = signal.get("price", 0)
        invested = signal.get("invested", 0)
        leverage = context.get("leverage", 1.0)
        position_size = context.get("position_size", 0.0)
        quantity = context.get("quantity", 0)

        if liquidation_price and liquidation_price > 0:
            item = QTableWidgetItem(f"{liquidation_price:.2f}")
        else:
            item = QTableWidgetItem("-")

        default_note = " (default)" if mm_rate_default else ""
        buffer_text = f"{margin_buffer:.2f} USDT" if margin_buffer is not None else "N/A"

        item.setToolTip(
            "Liquidation (approx.)\n"
            f"Entry: {entry_price:.2f}\n"
            f"Invested: {invested:.2f} USDT\n"
            f"Leverage: {leverage:.0f}x\n"
            f"MM rate: {mm_rate * 100:.2f}%{default_note}\n"
            f"Notional: {position_size:.2f} USDT\n"
            f"Quantity: {quantity:.6f}\n"
            f"Margin buffer: {buffer_text}\n"
            "Formula: Pliq = Entry +/- (Buffer / Q)\n"
            "Note: Fees/Funding not included"
        )

        # Make non-editable
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, column, item)
