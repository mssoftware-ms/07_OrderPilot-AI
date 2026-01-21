"""Watchlist Model Singleton for OrderPilot-AI.

Provides a shared Qt Model for watchlist data that can be used by
multiple WatchlistWidget instances. Changes automatically propagate
to all views through Qt's Model-View architecture.

Part of Phase 0: Singleton Services (UI Refactoring Plan)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    pyqtSignal,
)

from src.common.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


@dataclass
class WatchlistItem:
    """Data structure for a watchlist item."""
    
    symbol: str
    name: str = ""
    wkn: str = ""
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    volume: int = 0
    high: float = 0.0
    low: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "wkn": self.wkn,
        }


class WatchlistModel(QAbstractTableModel):
    """Singleton Qt Model for watchlist data.
    
    This model is shared between all WatchlistWidget instances.
    Changes made in one widget automatically appear in all others
    through Qt's Model-View signal mechanism.
    
    Usage:
        # Get the singleton instance
        model = WatchlistModel.instance()
        
        # Use in a QTableView
        table_view.setModel(model)
        
        # Add/remove symbols
        model.add_symbol("AAPL")
        model.remove_symbol("AAPL")
        
        # Get all symbols
        symbols = model.get_symbols()
    
    Columns:
        0: Symbol
        1: Name
        2: WKN
        3: Price
        4: Change
        5: Change %
        6: Volume
        7: High
        8: Low
    """
    
    _instance: Optional['WatchlistModel'] = None
    
    # Custom signals
    symbol_added = pyqtSignal(str)  # Emitted when symbol is added
    symbol_removed = pyqtSignal(str)  # Emitted when symbol is removed
    symbols_changed = pyqtSignal()  # Emitted when symbols list changes
    
    # Column definitions
    COLUMNS = [
        ("Symbol", "symbol"),
        ("Name", "name"),
        ("WKN", "wkn"),
        ("Price", "price"),
        ("Change", "change"),
        ("Change %", "change_pct"),
        ("Volume", "volume"),
        ("High", "high"),
        ("Low", "low"),
    ]
    
    @classmethod
    def instance(cls) -> 'WatchlistModel':
        """Get the singleton instance.
        
        Returns:
            The global WatchlistModel instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing only)."""
        cls._instance = None
    
    def __init__(self, parent=None):
        """Initialize the WatchlistModel.
        
        Note: Use WatchlistModel.instance() instead of direct instantiation.
        """
        super().__init__(parent)
        
        if WatchlistModel._instance is not None and WatchlistModel._instance is not self:
            raise RuntimeError(
                "WatchlistModel is a singleton. Use WatchlistModel.instance()"
            )
        
        self._items: list[WatchlistItem] = []
        self._symbol_index: dict[str, int] = {}  # symbol -> row index
        
        logger.info("WatchlistModel initialized")
    
    # ========================================================================
    # Qt Model Interface
    # ========================================================================
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows."""
        if parent.isValid():
            return 0
        return len(self._items)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns."""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if row < 0 or row >= len(self._items):
            return None
        
        item = self._items[row]
        
        if role == Qt.ItemDataRole.DisplayRole:
            col_name = self.COLUMNS[col][1]
            value = getattr(item, col_name, "")
            
            # Format specific columns
            if col_name == "price":
                return f"{value:.2f}" if value else ""
            elif col_name == "change":
                return f"{value:+.2f}" if value else ""
            elif col_name == "change_pct":
                return f"{value:+.2f}%" if value else ""
            elif col_name == "volume":
                return self._format_volume(value) if value else ""
            elif col_name in ("high", "low"):
                return f"{value:.2f}" if value else ""
            
            return str(value)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Right-align numeric columns
            if col >= 3:  # Price and after
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Color change column based on positive/negative
            if col in (4, 5):  # Change columns
                from PyQt6.QtGui import QColor
                change = item.change
                if change > 0:
                    return QColor("#26a69a")  # Green
                elif change < 0:
                    return QColor("#ef5350")  # Red
        
        elif role == Qt.ItemDataRole.UserRole:
            # Return the full item for custom use
            return item
        
        return None
    
    def headerData(
        self, 
        section: int, 
        orientation: Qt.Orientation, 
        role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """Return header data."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section][0]
        return None
    
    # ========================================================================
    # Symbol Management
    # ========================================================================
    
    def add_symbol(self, symbol_data: str | dict) -> bool:
        """Add a symbol to the watchlist.
        
        Args:
            symbol_data: Symbol string or dict with {symbol, name, wkn}
        
        Returns:
            True if added, False if already exists
        """
        # Parse symbol data
        if isinstance(symbol_data, str):
            symbol = symbol_data.upper().strip()
            name = ""
            wkn = ""
        else:
            symbol = symbol_data.get("symbol", "").upper().strip()
            name = symbol_data.get("name", "")
            wkn = symbol_data.get("wkn", "")
        
        if not symbol:
            return False
        
        # Check if already exists
        if symbol in self._symbol_index:
            logger.debug(f"Symbol {symbol} already in watchlist")
            return False
        
        # Create item
        item = WatchlistItem(symbol=symbol, name=name, wkn=wkn)
        
        # Add to model
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self._symbol_index[symbol] = row
        self.endInsertRows()
        
        # Emit signals
        self.symbol_added.emit(symbol)
        self.symbols_changed.emit()
        
        # Emit event bus event
        event_bus.emit(Event(
            type=EventType.UI_ACTION,
            timestamp=datetime.now(),
            data={"action": "watchlist_symbol_added", "symbol": symbol},
            source="WatchlistModel"
        ))
        
        logger.debug(f"Added {symbol} to watchlist")
        return True
    
    def remove_symbol(self, symbol: str) -> bool:
        """Remove a symbol from the watchlist.
        
        Args:
            symbol: Symbol to remove
        
        Returns:
            True if removed, False if not found
        """
        symbol = symbol.upper().strip()
        
        if symbol not in self._symbol_index:
            return False
        
        row = self._symbol_index[symbol]
        
        # Remove from model
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._items[row]
        del self._symbol_index[symbol]
        
        # Update indices for remaining items
        for s, idx in self._symbol_index.items():
            if idx > row:
                self._symbol_index[s] = idx - 1
        
        self.endRemoveRows()
        
        # Emit signals
        self.symbol_removed.emit(symbol)
        self.symbols_changed.emit()
        
        # Emit event bus event
        event_bus.emit(Event(
            type=EventType.UI_ACTION,
            timestamp=datetime.now(),
            data={"action": "watchlist_symbol_removed", "symbol": symbol},
            source="WatchlistModel"
        ))
        
        logger.debug(f"Removed {symbol} from watchlist")
        return True
    
    def clear(self) -> None:
        """Remove all symbols from the watchlist."""
        if not self._items:
            return
        
        self.beginResetModel()
        self._items.clear()
        self._symbol_index.clear()
        self.endResetModel()
        
        self.symbols_changed.emit()
        logger.debug("Cleared watchlist")
    
    def get_symbols(self) -> list[str]:
        """Get list of all symbols.
        
        Returns:
            List of symbol strings
        """
        return [item.symbol for item in self._items]
    
    def get_item(self, symbol: str) -> Optional[WatchlistItem]:
        """Get watchlist item by symbol.
        
        Args:
            symbol: Symbol to look up
        
        Returns:
            WatchlistItem or None if not found
        """
        symbol = symbol.upper().strip()
        if symbol in self._symbol_index:
            return self._items[self._symbol_index[symbol]]
        return None
    
    def contains(self, symbol: str) -> bool:
        """Check if symbol is in watchlist.
        
        Args:
            symbol: Symbol to check
        
        Returns:
            True if symbol is in watchlist
        """
        return symbol.upper().strip() in self._symbol_index
    
    # ========================================================================
    # Price Updates
    # ========================================================================
    
    def update_price(
        self,
        symbol: str,
        price: float,
        change: float = 0.0,
        change_pct: float = 0.0,
        volume: int = 0,
        high: float = 0.0,
        low: float = 0.0
    ) -> bool:
        """Update price data for a symbol.
        
        Args:
            symbol: Symbol to update
            price: Current price
            change: Price change
            change_pct: Price change percentage
            volume: Trading volume
            high: Daily high
            low: Daily low
        
        Returns:
            True if updated, False if symbol not found
        """
        symbol = symbol.upper().strip()
        
        if symbol not in self._symbol_index:
            return False
        
        row = self._symbol_index[symbol]
        item = self._items[row]
        
        # Update item
        item.price = price
        item.change = change
        item.change_pct = change_pct
        item.volume = volume
        item.high = high
        item.low = low
        item.last_update = datetime.now()
        
        # Emit data changed for price columns (3-8)
        top_left = self.index(row, 3)
        bottom_right = self.index(row, 8)
        self.dataChanged.emit(top_left, bottom_right)
        
        return True
    
    # ========================================================================
    # Serialization
    # ========================================================================
    
    def to_list(self) -> list[dict]:
        """Serialize watchlist to list of dicts.
        
        Returns:
            List of symbol dictionaries
        """
        return [item.to_dict() for item in self._items]
    
    def from_list(self, data: list[dict | str]) -> None:
        """Load watchlist from list of dicts or strings.
        
        Args:
            data: List of symbol data
        """
        self.beginResetModel()
        self._items.clear()
        self._symbol_index.clear()
        
        for item_data in data:
            if isinstance(item_data, str):
                symbol = item_data.upper().strip()
                item = WatchlistItem(symbol=symbol)
            else:
                symbol = item_data.get("symbol", "").upper().strip()
                item = WatchlistItem(
                    symbol=symbol,
                    name=item_data.get("name", ""),
                    wkn=item_data.get("wkn", ""),
                )
            
            if symbol and symbol not in self._symbol_index:
                self._symbol_index[symbol] = len(self._items)
                self._items.append(item)
        
        self.endResetModel()
        self.symbols_changed.emit()
        
        logger.debug(f"Loaded {len(self._items)} symbols into watchlist")
    
    # ========================================================================
    # Helpers
    # ========================================================================
    
    def _format_volume(self, volume: int) -> str:
        """Format volume for display."""
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        return str(volume)


# Convenience function for getting the singleton
def get_watchlist_model() -> WatchlistModel:
    """Get the global WatchlistModel instance.
    
    Returns:
        The WatchlistModel singleton
    """
    return WatchlistModel.instance()
