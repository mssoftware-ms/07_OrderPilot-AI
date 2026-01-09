"""Watchlist Widget for OrderPilot-AI (REFACTORED).

Displays a list of watched symbols with real-time updates.

REFACTORED: Split into focused helper modules using composition pattern.
- watchlist_presets.py: Preset lists and constants
- watchlist_ui_builder.py: UI construction
- watchlist_events.py: Event handling
- watchlist_table_updater.py: Table price updates
- watchlist_symbol_manager.py: Symbol add/remove operations
- watchlist_interactions.py: User interactions (double-click, context menu)
- watchlist_persistence.py: Save/load functionality
"""

import logging

from PyQt6.QtCore import pyqtSignal, QTimer, QSettings
from PyQt6.QtWidgets import QWidget, QVBoxLayout

# Import helpers
from .watchlist_ui_builder import WatchlistUIBuilder
from .watchlist_events import WatchlistEvents
from .watchlist_table_updater import WatchlistTableUpdater
from .watchlist_symbol_manager import WatchlistSymbolManager
from .watchlist_interactions import WatchlistInteractions
from .watchlist_persistence import WatchlistPersistence

logger = logging.getLogger(__name__)


class WatchlistWidget(QWidget):
    """Widget displaying watchlist with real-time updates (REFACTORED)."""

    # Signals
    symbol_selected = pyqtSignal(str)  # Emitted when user selects a symbol
    symbol_added = pyqtSignal(str)  # Emitted when symbol is added
    symbol_removed = pyqtSignal(str)  # Emitted when symbol is removed

    def __init__(self, parent=None):
        """Initialize watchlist widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.symbols = []  # List of watched symbols
        self.symbol_data = {}  # Symbol -> {price, change, volume, etc.}

        # Settings for persistent column state
        self.settings = QSettings("OrderPilot", "TradingApp")

        # Create helpers (composition pattern)
        self._ui_builder = WatchlistUIBuilder(self)
        self._events = WatchlistEvents(self)
        self._table_updater = WatchlistTableUpdater(self)
        self._symbol_manager = WatchlistSymbolManager(self)
        self._interactions = WatchlistInteractions(self)
        self._persistence = WatchlistPersistence(self)

        self.init_ui()
        self.setup_event_handlers()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_prices)
        self.update_timer.start(1000)  # Update every second

        # Load column state after UI is initialized
        self.load_column_state()

        # Load default watchlist
        self.load_default_watchlist()

    # === UI Building (Delegiert) ===

    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)

        layout.addWidget(self._ui_builder.build_market_status_label())
        layout.addLayout(self._ui_builder.build_input_row())
        layout.addWidget(self._ui_builder.build_table())
        layout.addLayout(self._ui_builder.build_quick_add_row())

    # === Event Handling (Delegiert) ===

    def setup_event_handlers(self):
        """Setup event bus handlers (delegiert)."""
        return self._events.setup_event_handlers()

    # === Price Updates (Delegiert) ===

    def update_prices(self):
        """Update prices in the table (delegiert)."""
        return self._table_updater.update_prices()

    def format_volume(self, volume: int) -> str:
        """Format volume for display (delegiert)."""
        return self._table_updater.format_volume(volume)

    # === Symbol Management (Delegiert) ===

    def add_symbol_from_input(self):
        """Add symbol from input field (delegiert)."""
        return self._symbol_manager.add_symbol_from_input()

    def add_symbol(self, symbol_data: str | dict, save: bool = True):
        """Add symbol to watchlist (delegiert).

        Args:
            symbol_data: Trading symbol (string) or dict with {symbol, name, wkn}
            save: Whether to save watchlist immediately (default: True, set False for batch operations)
        """
        return self._symbol_manager.add_symbol(symbol_data, save)

    def remove_symbol(self, symbol: str):
        """Remove symbol from watchlist (delegiert).

        Args:
            symbol: Trading symbol
        """
        return self._symbol_manager.remove_symbol(symbol)

    def clear_watchlist(self):
        """Clear all symbols from watchlist (delegiert)."""
        return self._symbol_manager.clear_watchlist()

    def add_indices(self):
        """Add major market indices (delegiert)."""
        return self._symbol_manager.add_indices()

    def add_tech_stocks(self):
        """Add major tech stocks (delegiert)."""
        return self._symbol_manager.add_tech_stocks()

    def add_crypto_pairs(self):
        """Add major cryptocurrency trading pairs (delegiert)."""
        return self._symbol_manager.add_crypto_pairs()

    # === User Interactions (Delegiert) ===

    def on_symbol_double_clicked(self, item):
        """Handle symbol double-click (delegiert).

        Args:
            item: Clicked table item
        """
        return self._interactions.on_symbol_double_clicked(item)

    def show_context_menu(self, position):
        """Show context menu for table (delegiert).

        Args:
            position: Menu position
        """
        return self._interactions.show_context_menu(position)

    def create_order(self, symbol: str):
        """Create order for symbol (delegiert).

        Args:
            symbol: Trading symbol
        """
        return self._interactions.create_order(symbol)

    # === Persistence (Delegiert) ===

    def load_default_watchlist(self):
        """Load default watchlist on startup (delegiert)."""
        return self._persistence.load_default_watchlist()

    def save_watchlist(self):
        """Save watchlist to settings (delegiert)."""
        return self._persistence.save_watchlist()

    def save_column_state(self):
        """Save column widths and order to settings (delegiert)."""
        return self._persistence.save_column_state()

    def load_column_state(self):
        """Load column widths and order from settings (delegiert)."""
        return self._persistence.load_column_state()

    # === Public API ===

    def get_symbols(self) -> list[str]:
        """Get list of watched symbols.

        Returns:
            List of symbols
        """
        return self.symbols.copy()

    def closeEvent(self, event):
        """Handle widget close event - save column state.

        Args:
            event: Close event
        """
        self.save_column_state()
        super().closeEvent(event)
