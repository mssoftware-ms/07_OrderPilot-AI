"""Watchlist Interactions - User Interactions.

Refactored from watchlist.py.

Contains:
- on_symbol_double_clicked
- show_context_menu
- create_order
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction

from src.common.event_bus import Event, EventType, event_bus

if TYPE_CHECKING:
    from .watchlist import WatchlistWidget

logger = logging.getLogger(__name__)


class WatchlistInteractions:
    """Helper for user interactions."""

    def __init__(self, parent: WatchlistWidget):
        self.parent = parent

    def on_symbol_double_clicked(self, item):
        """Handle symbol double-click.

        Args:
            item: Clicked table item
        """
        row = item.row()
        symbol_item = self.parent.table.item(row, 0)
        if symbol_item:
            symbol = symbol_item.text()
            logger.info(f"Symbol selected: {symbol}")
            self.parent.symbol_selected.emit(symbol)

    def show_context_menu(self, position):
        """Show context menu for table.

        Args:
            position: Menu position
        """
        item = self.parent.table.itemAt(position)
        if not item:
            return

        row = item.row()
        symbol_item = self.parent.table.item(row, 0)
        if not symbol_item:
            return

        symbol = symbol_item.text()

        menu = QMenu()

        # View chart action
        chart_action = QAction("View Chart", self.parent)
        chart_action.triggered.connect(lambda: self.parent.symbol_selected.emit(symbol))
        menu.addAction(chart_action)

        # Remove action
        remove_action = QAction("Remove from Watchlist", self.parent)
        remove_action.triggered.connect(lambda: self.parent.remove_symbol(symbol))
        menu.addAction(remove_action)

        menu.addSeparator()

        # New order action
        order_action = QAction("New Order...", self.parent)
        order_action.triggered.connect(lambda: self.create_order(symbol))
        menu.addAction(order_action)

        menu.exec(self.parent.table.viewport().mapToGlobal(position))

    def create_order(self, symbol: str):
        """Create order for symbol.

        Args:
            symbol: Trading symbol
        """
        # Emit event to open order dialog
        event_bus.emit(Event(
            type=EventType.UI_ACTION,
            timestamp=datetime.now(),
            data={"action": "new_order", "symbol": symbol}
        ))
