"""Watchlist Events - Event Handling.

Refactored from watchlist.py.

Contains:
- setup_event_handlers
- on_market_tick (async)
- on_market_bar (async)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.common.event_bus import Event, EventType, event_bus

if TYPE_CHECKING:
    from .watchlist import WatchlistWidget

logger = logging.getLogger(__name__)


class WatchlistEvents:
    """Helper for event handling."""

    def __init__(self, parent: WatchlistWidget):
        self.parent = parent

    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.MARKET_TICK, self.on_market_tick)
        event_bus.subscribe(EventType.MARKET_BAR, self.on_market_bar)

    async def on_market_tick(self, event: Event):
        """Handle market tick events."""
        data = event.data
        symbol = data.get('symbol')

        if symbol not in self.parent.symbols:
            return

        if symbol not in self.parent.symbol_data:
            self.parent.symbol_data[symbol] = {}

        self.parent.symbol_data[symbol]['price'] = data.get('price')
        self.parent.symbol_data[symbol]['volume'] = data.get('volume')

        if 'prev_price' in self.parent.symbol_data[symbol]:
            prev = self.parent.symbol_data[symbol]['prev_price']
            current = data.get('price')
            if prev and current:
                self.parent.symbol_data[symbol]['change'] = current - prev
                self.parent.symbol_data[symbol]['change_pct'] = ((current - prev) / prev) * 100

        self.parent.update_timer.start(100)

    async def on_market_bar(self, event: Event):
        """Handle market bar events."""
        data = event.data
        symbol = data.get('symbol')

        if symbol not in self.parent.symbols:
            return

        if symbol not in self.parent.symbol_data:
            self.parent.symbol_data[symbol] = {}

        if 'price' in self.parent.symbol_data[symbol]:
            self.parent.symbol_data[symbol]['prev_price'] = self.parent.symbol_data[symbol]['price']

        self.parent.symbol_data[symbol]['price'] = data.get('close')
        self.parent.symbol_data[symbol]['volume'] = data.get('volume')
