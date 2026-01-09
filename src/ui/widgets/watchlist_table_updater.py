"""Watchlist Table Updater - Table Price Updates.

Refactored from watchlist.py.

Contains:
- update_prices: Main table update loop with market status
- format_volume: Volume formatting delegation
"""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem

from .watchlist_presets import (
    MARKET_STATUS_AFTER_HOURS,
    MARKET_STATUS_OPEN,
    MARKET_STATUS_WEEKEND,
    format_volume,
)

if TYPE_CHECKING:
    from .watchlist import WatchlistWidget


class WatchlistTableUpdater:
    """Helper for table price updates."""

    def __init__(self, parent: WatchlistWidget):
        self.parent = parent

    def update_prices(self):
        """Update prices in the table with market status."""
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        is_market_hours = time(9, 30) <= now.time() <= time(16, 0)

        # Update market status
        if is_weekend:
            status = MARKET_STATUS_WEEKEND
        elif not is_market_hours:
            status = MARKET_STATUS_AFTER_HOURS
        else:
            status = MARKET_STATUS_OPEN

        self.parent.market_status_label.setText(status["text"])
        self.parent.market_status_label.setStyleSheet(status["style"])

        # Update each row
        for row in range(self.parent.table.rowCount()):
            self._update_row(row)

    def _update_row(self, row: int):
        """Update a single table row."""
        symbol_item = self.parent.table.item(row, 0)
        if not symbol_item:
            return

        symbol = symbol_item.text()
        data = self.parent.symbol_data.get(symbol, {})

        self._update_price_column(row, data)
        self._update_change_column(row, data)
        self._update_change_pct_column(row, data)
        self._update_volume_column(row, data)

    def _update_price_column(self, row: int, data: dict):
        """Update price column (column 3)."""
        price = data.get('price')
        if price is not None:
            price_item = QTableWidgetItem(f"${price:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            price_item.setForeground(QColor(255, 255, 255))  # White text
            self.parent.table.setItem(row, 3, price_item)

    def _update_change_column(self, row: int, data: dict):
        """Update change column (column 4)."""
        change = data.get('change')
        if change is not None:
            change_item = QTableWidgetItem(f"{change:+.2f}")
            change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Color coding with better contrast
            if change > 0:
                change_item.setForeground(QColor(100, 255, 100))  # Bright green
            elif change < 0:
                change_item.setForeground(QColor(255, 100, 100))  # Bright red
            else:
                change_item.setForeground(QColor(255, 255, 255))  # White

            self.parent.table.setItem(row, 4, change_item)

    def _update_change_pct_column(self, row: int, data: dict):
        """Update change % column (column 5)."""
        change_pct = data.get('change_pct')
        if change_pct is not None:
            pct_item = QTableWidgetItem(f"{change_pct:+.2f}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Color coding with better contrast
            if change_pct > 0:
                pct_item.setForeground(QColor(100, 255, 100))  # Bright green
            elif change_pct < 0:
                pct_item.setForeground(QColor(255, 100, 100))  # Bright red
            else:
                pct_item.setForeground(QColor(255, 255, 255))  # White

            self.parent.table.setItem(row, 5, pct_item)

    def _update_volume_column(self, row: int, data: dict):
        """Update volume column (column 6)."""
        volume = data.get('volume')
        if volume is not None:
            volume_str = self.format_volume(volume)
            volume_item = QTableWidgetItem(volume_str)
            volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            volume_item.setForeground(QColor(255, 255, 255))  # White text
            self.parent.table.setItem(row, 6, volume_item)

    def format_volume(self, volume: int) -> str:
        """Format volume for display. Delegates to module function."""
        return format_volume(volume)
