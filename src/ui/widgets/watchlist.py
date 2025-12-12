"""Watchlist Widget for OrderPilot-AI.

Displays a list of watched symbols with real-time updates.
"""

import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QHeaderView,
    QMenu,
    QMessageBox
)
from PyQt6.QtGui import QColor, QAction

from src.common.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class WatchlistWidget(QWidget):
    """Widget displaying watchlist with real-time updates."""

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

    def init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)

        # Market status indicator
        self.market_status_label = QLabel("Market: Checking...")
        self.market_status_label.setStyleSheet(
            "background-color: #2A2D33; color: #EAECEF; padding: 5px; "
            "border-radius: 3px; font-weight: bold;"
        )
        layout.addWidget(self.market_status_label)

        # Add symbol input
        input_layout = QHBoxLayout()

        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter symbol (e.g., AAPL for stocks, BTC/USD for crypto)")
        self.symbol_input.returnPressed.connect(self.add_symbol_from_input)
        input_layout.addWidget(self.symbol_input)

        add_button = QPushButton("+")
        add_button.setMaximumWidth(40)
        add_button.clicked.connect(self.add_symbol_from_input)
        add_button.setToolTip("Add symbol to watchlist")
        input_layout.addWidget(add_button)

        layout.addLayout(input_layout)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Symbol", "Name", "WKN", "Price", "Change", "Change %", "Volume"
        ])

        # Configure table
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        # Set stylesheet for better contrast
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #2d2d2d;
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #FF8C00;
                color: #ffffff;
            }
        """)

        # Configure header - make columns movable and resizable
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)  # Allow column reordering
        header.setSectionsClickable(True)  # Allow sorting by clicking
        header.setStretchLastSection(False)  # Don't auto-stretch last section

        # Set default column widths (Interactive allows user resizing)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Set initial default widths
        self.table.setColumnWidth(0, 80)   # Symbol
        self.table.setColumnWidth(1, 150)  # Name
        self.table.setColumnWidth(2, 80)   # WKN
        self.table.setColumnWidth(3, 100)  # Price
        self.table.setColumnWidth(4, 80)   # Change
        self.table.setColumnWidth(5, 80)   # Change %
        self.table.setColumnWidth(6, 100)  # Volume

        # Connect signals
        self.table.itemDoubleClicked.connect(self.on_symbol_double_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Save column state when columns are moved or resized
        header.sectionMoved.connect(self.save_column_state)
        header.sectionResized.connect(self.save_column_state)

        layout.addWidget(self.table)

        # Quick add buttons
        quick_add_layout = QHBoxLayout()

        indices_btn = QPushButton("Indices")
        indices_btn.clicked.connect(self.add_indices)
        indices_btn.setToolTip("Add major indices (QQQ, DIA, SPY)")
        quick_add_layout.addWidget(indices_btn)

        tech_btn = QPushButton("Tech")
        tech_btn.clicked.connect(self.add_tech_stocks)
        tech_btn.setToolTip("Add tech stocks (AAPL, MSFT, GOOGL, etc.)")
        quick_add_layout.addWidget(tech_btn)

        crypto_btn = QPushButton("Crypto")
        crypto_btn.clicked.connect(self.add_crypto_pairs)
        crypto_btn.setToolTip("Add major crypto pairs (BTC/USD, ETH/USD, SOL/USD, etc.)")
        quick_add_layout.addWidget(crypto_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_watchlist)
        clear_btn.setToolTip("Clear all symbols")
        quick_add_layout.addWidget(clear_btn)

        layout.addLayout(quick_add_layout)

    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.MARKET_TICK, self.on_market_tick)
        event_bus.subscribe(EventType.MARKET_BAR, self.on_market_bar)

    async def on_market_tick(self, event: Event):
        """Handle market tick events.

        Args:
            event: Market tick event
        """
        data = event.data
        symbol = data.get('symbol')

        if symbol in self.symbols:
            # Update symbol data
            if symbol not in self.symbol_data:
                self.symbol_data[symbol] = {}

            self.symbol_data[symbol]['price'] = data.get('price')
            self.symbol_data[symbol]['volume'] = data.get('volume')

            # Calculate change if we have previous price
            if 'prev_price' in self.symbol_data[symbol]:
                prev = self.symbol_data[symbol]['prev_price']
                current = data.get('price')
                if prev and current:
                    change = current - prev
                    change_pct = (change / prev) * 100
                    self.symbol_data[symbol]['change'] = change
                    self.symbol_data[symbol]['change_pct'] = change_pct

            # Will be updated on next timer tick
            self.update_timer.start(100)  # Update soon

    async def on_market_bar(self, event: Event):
        """Handle market bar events.

        Args:
            event: Market bar event
        """
        data = event.data
        symbol = data.get('symbol')

        if symbol in self.symbols:
            if symbol not in self.symbol_data:
                self.symbol_data[symbol] = {}

            # Store previous close for change calculation
            if 'price' in self.symbol_data[symbol]:
                self.symbol_data[symbol]['prev_price'] = self.symbol_data[symbol]['price']

            self.symbol_data[symbol]['price'] = data.get('close')
            self.symbol_data[symbol]['volume'] = data.get('volume')

    def update_prices(self):
        """Update prices in the table."""
        # Check if we have any recent data to determine market status
        from datetime import datetime, time
        now = datetime.now()

        # Simple market hours check (NYSE: 9:30 AM - 4:00 PM ET, Mon-Fri)
        # This is a simplified check - real implementation would need to handle holidays
        is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6
        is_market_hours = time(9, 30) <= now.time() <= time(16, 0)

        if is_weekend:
            self.market_status_label.setText("⚠ Market Closed (Weekend) - Showing last available data")
            self.market_status_label.setStyleSheet(
                "background-color: #4A3000; color: #FFA500; padding: 5px; "
                "border-radius: 3px; font-weight: bold;"
            )
        elif not is_market_hours:
            self.market_status_label.setText("⚠ After Hours - Data may be delayed")
            self.market_status_label.setStyleSheet(
                "background-color: #3A3000; color: #FFD700; padding: 5px; "
                "border-radius: 3px; font-weight: bold;"
            )
        else:
            self.market_status_label.setText("✓ Market Open - Live Data")
            self.market_status_label.setStyleSheet(
                "background-color: #003A00; color: #00FF00; padding: 5px; "
                "border-radius: 3px; font-weight: bold;"
            )

        for row in range(self.table.rowCount()):
            symbol_item = self.table.item(row, 0)
            if not symbol_item:
                continue

            symbol = symbol_item.text()
            data = self.symbol_data.get(symbol, {})

            # Update price (column 3)
            price = data.get('price')
            if price is not None:
                price_item = QTableWidgetItem(f"${price:.2f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                price_item.setForeground(QColor(255, 255, 255))  # White text
                self.table.setItem(row, 3, price_item)

            # Update change (column 4)
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

                self.table.setItem(row, 4, change_item)

            # Update change % (column 5)
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

                self.table.setItem(row, 5, pct_item)

            # Update volume (column 6)
            volume = data.get('volume')
            if volume is not None:
                volume_str = self.format_volume(volume)
                volume_item = QTableWidgetItem(volume_str)
                volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                volume_item.setForeground(QColor(255, 255, 255))  # White text
                self.table.setItem(row, 6, volume_item)

    def format_volume(self, volume: int) -> str:
        """Format volume for display.

        Args:
            volume: Volume value

        Returns:
            Formatted string
        """
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        else:
            return str(volume)

    def add_symbol_from_input(self):
        """Add symbol from input field."""
        symbol = self.symbol_input.text().strip().upper()

        if not symbol:
            return

        self.add_symbol(symbol)
        self.symbol_input.clear()

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

        if symbol in self.symbols:
            logger.info(f"Symbol {symbol} already in watchlist")
            return

        # Add to list
        self.symbols.append(symbol)
        self.symbol_data[symbol] = {
            "name": name,
            "wkn": wkn
        }

        # Add to table
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Symbol column
        symbol_item = QTableWidgetItem(symbol)
        symbol_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        symbol_item.setForeground(QColor(255, 255, 255))  # White text
        self.table.setItem(row, 0, symbol_item)

        # Name column
        name_item = QTableWidgetItem(name)
        name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        name_item.setForeground(QColor(255, 255, 255))
        self.table.setItem(row, 1, name_item)

        # WKN column
        wkn_item = QTableWidgetItem(wkn)
        wkn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        wkn_item.setForeground(QColor(200, 200, 200))
        self.table.setItem(row, 2, wkn_item)

        # Initialize price columns
        for col in range(3, 7):
            item = QTableWidgetItem("--")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setForeground(QColor(180, 180, 180))  # Light gray for placeholder
            self.table.setItem(row, col, item)

        logger.info(f"Added {symbol} ({name}) to watchlist")

        # Emit signal
        self.symbol_added.emit(symbol)

        # Save watchlist (only if not in batch mode)
        if save:
            self.save_watchlist()

    def remove_symbol(self, symbol: str):
        """Remove symbol from watchlist.

        Args:
            symbol: Trading symbol
        """
        if symbol not in self.symbols:
            return

        # Remove from list
        self.symbols.remove(symbol)
        if symbol in self.symbol_data:
            del self.symbol_data[symbol]

        # Remove from table
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == symbol:
                self.table.removeRow(row)
                break

        logger.info(f"Removed {symbol} from watchlist")

        # Emit signal
        self.symbol_removed.emit(symbol)

        # Save watchlist
        self.save_watchlist()

    def clear_watchlist(self):
        """Clear all symbols from watchlist."""
        reply = QMessageBox.question(
            self,
            "Clear Watchlist",
            "Remove all symbols from watchlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.symbols.clear()
            self.symbol_data.clear()
            self.table.setRowCount(0)
            self.save_watchlist()
            logger.info("Cleared watchlist")

    def add_indices(self):
        """Add major market indices."""
        indices = [
            {"symbol": "QQQ", "name": "NASDAQ 100 ETF"},
            {"symbol": "DIA", "name": "Dow Jones ETF"},
            {"symbol": "SPY", "name": "S&P 500 ETF"},
            {"symbol": "IWM", "name": "Russell 2000 ETF"},
            {"symbol": "VTI", "name": "Total Stock Market ETF"}
        ]
        # Batch add: disable save for each symbol
        for index in indices:
            self.add_symbol(index, save=False)
        # Save once at the end
        self.save_watchlist()

    def add_tech_stocks(self):
        """Add major tech stocks."""
        tech_stocks = [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corp."},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "META", "name": "Meta Platforms Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corp."},
            {"symbol": "TSLA", "name": "Tesla Inc."}
        ]
        # Batch add: disable save for each symbol
        for stock in tech_stocks:
            self.add_symbol(stock, save=False)
        # Save once at the end
        self.save_watchlist()

    def add_crypto_pairs(self):
        """Add major cryptocurrency trading pairs."""
        crypto_pairs = [
            {"symbol": "BTC/USD", "name": "Bitcoin", "wkn": ""},
            {"symbol": "ETH/USD", "name": "Ethereum", "wkn": ""},
            {"symbol": "SOL/USD", "name": "Solana", "wkn": ""},
            {"symbol": "AVAX/USD", "name": "Avalanche", "wkn": ""},
            {"symbol": "MATIC/USD", "name": "Polygon", "wkn": ""},
        ]
        # Batch add: disable save for each symbol
        for crypto in crypto_pairs:
            self.add_symbol(crypto, save=False)
        # Save once at the end
        self.save_watchlist()

    def on_symbol_double_clicked(self, item):
        """Handle symbol double-click.

        Args:
            item: Clicked table item
        """
        row = item.row()
        symbol_item = self.table.item(row, 0)
        if symbol_item:
            symbol = symbol_item.text()
            logger.info(f"Symbol selected: {symbol}")
            self.symbol_selected.emit(symbol)

    def show_context_menu(self, position):
        """Show context menu for table.

        Args:
            position: Menu position
        """
        item = self.table.itemAt(position)
        if not item:
            return

        row = item.row()
        symbol_item = self.table.item(row, 0)
        if not symbol_item:
            return

        symbol = symbol_item.text()

        menu = QMenu()

        # View chart action
        chart_action = QAction("View Chart", self)
        chart_action.triggered.connect(lambda: self.symbol_selected.emit(symbol))
        menu.addAction(chart_action)

        # Remove action
        remove_action = QAction("Remove from Watchlist", self)
        remove_action.triggered.connect(lambda: self.remove_symbol(symbol))
        menu.addAction(remove_action)

        menu.addSeparator()

        # New order action
        order_action = QAction("New Order...", self)
        order_action.triggered.connect(lambda: self.create_order(symbol))
        menu.addAction(order_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

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

    def load_default_watchlist(self):
        """Load default watchlist on startup."""
        # Try to load saved watchlist
        from src.config.loader import config_manager

        try:
            watchlist = config_manager.load_watchlist()
            if watchlist:
                # Batch load: disable save for each symbol
                for symbol in watchlist:
                    self.add_symbol(symbol, save=False)
                logger.info(f"Loaded {len(watchlist)} symbols from saved watchlist")
                return
        except Exception as e:
            logger.warning(f"Failed to load saved watchlist: {e}")

        # Load default symbols if no saved watchlist
        default_symbols = [
            {"symbol": "AAPL", "name": "Apple Inc.", "wkn": "865985"},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "wkn": "870747"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "wkn": "A14Y6F"},
            {"symbol": "QQQ", "name": "NASDAQ 100 ETF", "wkn": "A0AE1X"},
            {"symbol": "SPY", "name": "S&P 500 ETF", "wkn": "A1JULM"}
        ]
        # Batch load: disable save for each symbol
        for symbol_data in default_symbols:
            self.add_symbol(symbol_data, save=False)
        # Save once at the end
        self.save_watchlist()
        logger.info("Loaded default watchlist")

    def save_watchlist(self):
        """Save watchlist to settings."""
        from src.config.loader import config_manager

        try:
            # Build watchlist with full data
            watchlist_data = []
            for symbol in self.symbols:
                data = self.symbol_data.get(symbol, {})
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

    def get_symbols(self) -> list[str]:
        """Get list of watched symbols.

        Returns:
            List of symbols
        """
        return self.symbols.copy()

    def save_column_state(self):
        """Save column widths and order to settings."""
        try:
            header = self.table.horizontalHeader()
            # Save header state (includes column order and widths)
            state = header.saveState()
            self.settings.setValue("watchlist/columnState", state)
            logger.debug("Saved watchlist column state")
        except Exception as e:
            logger.error(f"Failed to save column state: {e}")

    def load_column_state(self):
        """Load column widths and order from settings."""
        try:
            header = self.table.horizontalHeader()
            state = self.settings.value("watchlist/columnState")
            if state:
                header.restoreState(state)
                logger.debug("Restored watchlist column state")
            else:
                logger.debug("No saved column state found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load column state: {e}")

    def closeEvent(self, event):
        """Handle widget close event - save column state.

        Args:
            event: Close event
        """
        self.save_column_state()
        super().closeEvent(event)
