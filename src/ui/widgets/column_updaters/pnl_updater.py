"""P&L column updaters (percentage and currency)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem
from .base_updater import BaseColumnUpdater

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTableWidget


class PnLPercentUpdater(BaseColumnUpdater):
    """Updates P&L % column (column 12)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the P&L % column."""
        return column_index == 12

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update P&L percentage with color and tooltip."""
        pnl_percent = context.get("pnl_percent", 0.0)
        pnl_pct_raw = context.get("pnl_pct_raw", 0.0)
        leverage = context.get("leverage", 1.0)
        maker_fee = context.get("maker_fee", 0.02)
        taker_fee = context.get("taker_fee", 0.06)
        fees_pct_leveraged = context.get("fees_pct_leveraged", 0.0)

        # Color based on positive/negative
        pnl_color = "#26a69a" if pnl_percent >= 0 else "#ef5350"
        pct_sign = "+" if pnl_percent >= 0 else ""

        item = QTableWidgetItem(f"{pct_sign}{pnl_percent:.2f}%")
        item.setForeground(QColor(pnl_color))
        item.setToolTip(
            f"P&L % (mit Hebel)\n"
            f"Basis: {pnl_pct_raw:.2f}%\n"
            f"× Hebel {leverage:.0f}x = {(pnl_pct_raw * leverage):.2f}%\n"
            f"Trading Fees: ({maker_fee:.3f}% + {taker_fee:.3f}%) × {leverage:.0f}x = {fees_pct_leveraged:.3f}%\n"
            f"Netto: {pnl_percent:.2f}%"
        )

        # Make non-editable
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, column, item)


class PnLCurrencyUpdater(BaseColumnUpdater):
    """Updates P&L USDT column (column 13)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the P&L USDT column."""
        return column_index == 13

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update P&L currency with color and tooltip."""
        pnl_usdt = context.get("pnl_usdt", 0.0)
        pnl_percent = context.get("pnl_percent", 0.0)
        invested = signal.get("invested", 0)

        # Color based on positive/negative
        pnl_color = "#26a69a" if pnl_usdt >= 0 else "#ef5350"
        pnl_sign = "+" if pnl_usdt >= 0 else ""

        item = QTableWidgetItem(f"{pnl_sign}{pnl_usdt:.2f}")
        item.setForeground(QColor(pnl_color))
        item.setToolTip(
            f"P&L USDT (basiert auf Investment)\n"
            f"Invested: {invested:.2f} USDT\n"
            f"P&L %: {pnl_percent:.2f}%\n"
            f"Berechnung: {invested:.2f} × ({pnl_percent:.2f}% / 100) = {pnl_usdt:.2f} USDT"
        )

        # Make non-editable
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, column, item)
