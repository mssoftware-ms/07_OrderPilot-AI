"""Watchlist Persistence - Save/Load Functionality.

Refactored from watchlist.py.

Contains:
- load_default_watchlist
- save_watchlist
- save_column_state
- load_column_state
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .watchlist_presets import DEFAULT_WATCHLIST

if TYPE_CHECKING:
    from .watchlist import WatchlistWidget

logger = logging.getLogger(__name__)


class WatchlistPersistence:
    """Helper for save/load functionality."""

    def __init__(self, parent: WatchlistWidget):
        self.parent = parent

    def load_default_watchlist(self):
        """Load default watchlist on startup."""
        from src.config.loader import config_manager

        try:
            watchlist = config_manager.load_watchlist()
            if watchlist:
                for symbol in watchlist:
                    self.parent.add_symbol(symbol, save=False)
                logger.info(f"Loaded {len(watchlist)} symbols from saved watchlist")
                return
        except Exception as e:
            logger.warning(f"Failed to load saved watchlist: {e}")

        # Load default symbols from presets
        for symbol_data in DEFAULT_WATCHLIST:
            self.parent.add_symbol(symbol_data, save=False)
        self.parent.save_watchlist()
        logger.info("Loaded default watchlist")

    def save_watchlist(self):
        """Save watchlist to settings."""
        from src.config.loader import config_manager

        try:
            # Build watchlist with full data
            watchlist_data = []
            for symbol in self.parent.symbols:
                data = self.parent.symbol_data.get(symbol, {})
                watchlist_data.append({
                    "symbol": symbol,
                    "name": data.get("name", ""),
                    "wkn": data.get("wkn", "")
                })

            # Update settings and save to file
            config_manager.settings.watchlist = watchlist_data
            config_manager.save_watchlist()
            logger.debug(f"Saved watchlist: {watchlist_data}")

        except Exception as e:
            logger.error(f"Failed to save watchlist: {e}")

    def save_column_state(self):
        """Save column widths and order to settings."""
        try:
            header = self.parent.table.horizontalHeader()
            # Save header state (includes column order and widths)
            state = header.saveState()
            self.parent.settings.setValue("watchlist/columnState", state)
            logger.debug("Saved watchlist column state")
        except Exception as e:
            logger.error(f"Failed to save column state: {e}")

    def load_column_state(self):
        """Load column widths and order from settings."""
        try:
            header = self.parent.table.horizontalHeader()
            state = self.parent.settings.value("watchlist/columnState")
            if state:
                header.restoreState(state)
                logger.debug("Restored watchlist column state")
            else:
                logger.debug("No saved column state found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load column state: {e}")
