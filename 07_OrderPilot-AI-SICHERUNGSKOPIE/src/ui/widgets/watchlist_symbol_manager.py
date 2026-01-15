"""Watchlist Symbol Manager - Symbol Add/Remove Operations.

Refactored from watchlist.py.

Contains:
- add_symbol_from_input
- add_symbol (with dict/string support)
- remove_symbol
- clear_watchlist
- add_indices
- add_tech_stocks
- add_crypto_pairs
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from .watchlist_presets import CRYPTO_PRESETS, INDICES_PRESETS, TECH_STOCKS_PRESETS

if TYPE_CHECKING:
    from .watchlist import WatchlistWidget

logger = logging.getLogger(__name__)


class WatchlistSymbolManager:
    """Helper for symbol add/remove operations."""

    def __init__(self, parent: WatchlistWidget):
        self.parent = parent

    def add_symbol_from_input(self):
        """Add symbol from input field."""
        symbol = self.parent.symbol_input.text().strip().upper()

        if not symbol:
            return

        self.add_symbol(symbol)
        self.parent.symbol_input.clear()

    def add_symbol(self, symbol_data: str | dict, save: bool = True):
        """Add symbol to watchlist.

        Args:
            symbol_data: Trading symbol (string) or dict with {symbol, name, wkn}
            save: Whether to save watchlist immediately (default: True, set False for batch operations)
        """
        # Handle both string and dict input
        if isinstance(symbol_data, dict):
            symbol = symbol_data.get("symbol", "").upper()
            name = symbol_data.get("name", "")
            wkn = symbol_data.get("wkn", "")
        else:
            symbol = symbol_data.upper()
            name = ""
            wkn = ""

        if symbol in self.parent.symbols:
            logger.info(f"Symbol {symbol} already in watchlist")
            return

        # Add to list
        self.parent.symbols.append(symbol)
        self.parent.symbol_data[symbol] = {
            "name": name,
            "wkn": wkn
        }

        # Add to table
        self._add_symbol_to_table(symbol, name, wkn)

        logger.info(f"Added {symbol} ({name}) to watchlist")

        # Emit signal
        self.parent.symbol_added.emit(symbol)

        # Save watchlist (only if not in batch mode)
        if save:
            self.parent.save_watchlist()

    def _add_symbol_to_table(self, symbol: str, name: str, wkn: str):
        """Add symbol row to table."""
        row = self.parent.table.rowCount()
        self.parent.table.insertRow(row)

        # Symbol column
        symbol_item = QTableWidgetItem(symbol)
        symbol_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        symbol_item.setForeground(QColor(255, 255, 255))  # White text
        self.parent.table.setItem(row, 0, symbol_item)

        # Name column
        name_item = QTableWidgetItem(name)
        name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        name_item.setForeground(QColor(255, 255, 255))
        self.parent.table.setItem(row, 1, name_item)

        # WKN column
        wkn_item = QTableWidgetItem(wkn)
        wkn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        wkn_item.setForeground(QColor(200, 200, 200))
        self.parent.table.setItem(row, 2, wkn_item)

        # Initialize price columns
        for col in range(3, 7):
            item = QTableWidgetItem("--")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setForeground(QColor(180, 180, 180))  # Light gray for placeholder
            self.parent.table.setItem(row, col, item)

    def remove_symbol(self, symbol: str):
        """Remove symbol from watchlist.

        Args:
            symbol: Trading symbol
        """
        if symbol not in self.parent.symbols:
            return

        # Remove from list
        self.parent.symbols.remove(symbol)
        if symbol in self.parent.symbol_data:
            del self.parent.symbol_data[symbol]

        # Remove from table
        for row in range(self.parent.table.rowCount()):
            item = self.parent.table.item(row, 0)
            if item and item.text() == symbol:
                self.parent.table.removeRow(row)
                break

        logger.info(f"Removed {symbol} from watchlist")

        # Emit signal
        self.parent.symbol_removed.emit(symbol)

        # Save watchlist
        self.parent.save_watchlist()

    def clear_watchlist(self):
        """Clear all symbols from watchlist."""
        reply = QMessageBox.question(
            self.parent,
            "Clear Watchlist",
            "Remove all symbols from watchlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.parent.symbols.clear()
            self.parent.symbol_data.clear()
            self.parent.table.setRowCount(0)
            self.parent.save_watchlist()
            logger.info("Cleared watchlist")

    def add_indices(self):
        """Add major market indices."""
        for index in INDICES_PRESETS:
            self.add_symbol(index, save=False)
        self.parent.save_watchlist()

    def add_tech_stocks(self):
        """Add major tech stocks."""
        for stock in TECH_STOCKS_PRESETS:
            self.add_symbol(stock, save=False)
        self.parent.save_watchlist()

    def add_crypto_pairs(self):
        """Add major cryptocurrency trading pairs."""
        for crypto in CRYPTO_PRESETS:
            self.add_symbol(crypto, save=False)
        self.parent.save_watchlist()
