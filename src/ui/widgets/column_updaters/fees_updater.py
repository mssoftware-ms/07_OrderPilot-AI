"""Trading fees column updaters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem
from .base_updater import BaseColumnUpdater

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTableWidget


class FeesPercentUpdater(BaseColumnUpdater):
    """Updates Trading fees % column (column 14)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the fees % column."""
        return column_index == 14

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update trading fees percentage with tooltip."""
        maker_fee = context.get("maker_fee", 0.02)
        taker_fee = context.get("taker_fee", 0.06)
        fees_pct = maker_fee + taker_fee
        leverage = context.get("leverage", 1.0)
        fees_pct_leveraged = fees_pct * leverage

        item = QTableWidgetItem(f"{fees_pct:.3f}%")
        item.setForeground(QColor("#ff9800"))
        item.setToolTip(
            "Trading fees % (Maker + Taker)\n"
            f"Maker: {maker_fee:.3f}%\n"
            f"Taker: {taker_fee:.3f}%\n"
            f"Summe: {fees_pct:.3f}%\n"
            f"× Hebel {leverage:.0f}x = {fees_pct_leveraged:.3f}% (P&L-Abzug)"
        )

        # Make non-editable
        item.setFlags(item.flags() & ~0x00000002)
        table.setItem(row, column, item)


class FeesCurrencyUpdater(BaseColumnUpdater):
    """Updates Trading fees USDT column (column 15)."""

    def can_update(self, column_index: int) -> bool:
        """Check if this is the fees USDT column."""
        return column_index == 15

    def update(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        signal: dict,
        context: dict[str, Any],
    ) -> None:
        """Update trading fees in USDT with breakdown tooltip."""
        fees_usdt = context.get("fees_usdt", 0.0)
        position_size = context.get("position_size", 0.0)
        entry_fee = context.get("entry_fee_euro", 0.0)
        exit_fee = context.get("exit_fee_euro", 0.0)
        taker_fee = context.get("taker_fee", 0.06)

        item = QTableWidgetItem(f"{fees_usdt:.4f}")
        item.setForeground(QColor("#ff9800"))
        item.setToolTip(
            "Trading fees (BitUnix Futures)\n"
            f"Leverage-Notional: {position_size:.2f} USDT\n"
            f"Entry (Taker {taker_fee:.3f}%): {entry_fee:.4f} USDT\n"
            f"Exit (Taker {taker_fee:.3f}%): {exit_fee:.4f} USDT\n"
            f"Round-trip total: {fees_usdt:.4f} USDT"
        )

        # Make non-editable
        item.setFlags(item.flags() & ~0x00000002)
        table.setItem(row, column, item)
