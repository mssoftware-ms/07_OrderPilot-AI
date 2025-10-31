"""Positions Widget for OrderPilot-AI Trading Application."""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from src.common.event_bus import Event, EventType, event_bus
from src.database import get_db_manager


class PositionsWidget(QWidget):
    """Widget for displaying current positions."""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_event_handlers()

    def init_ui(self):
        """Initialize the positions UI."""
        layout = QVBoxLayout(self)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Avg Cost", "Current Price",
            "Market Value", "P&L", "P&L %"
        ])

        # Set column stretch
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

    def update_positions(self, positions):
        """Update positions table."""
        self.table.setRowCount(len(positions))

        for row, position in enumerate(positions):
            self.table.setItem(row, 0, QTableWidgetItem(str(position.symbol)))
            self.table.setItem(row, 1, QTableWidgetItem(str(position.quantity)))
            self.table.setItem(row, 2, QTableWidgetItem(f"€{position.average_cost:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(
                f"€{position.current_price:.2f}" if position.current_price else "--"
            ))
            self.table.setItem(row, 4, QTableWidgetItem(
                f"€{position.market_value:.2f}" if position.market_value else "--"
            ))
            self.table.setItem(row, 5, QTableWidgetItem(
                f"€{position.unrealized_pnl:.2f}" if position.unrealized_pnl else "--"
            ))
            self.table.setItem(row, 6, QTableWidgetItem(
                f"{position.pnl_percentage:.2f}%" if position.pnl_percentage else "--"
            ))

    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.ORDER_FILLED, self.on_order_filled)
        event_bus.subscribe(EventType.MARKET_TICK, self.on_market_tick)

    @pyqtSlot(object)
    def on_order_filled(self, event: Event):
        """Handle order filled event - refresh positions."""
        self.refresh()

    @pyqtSlot(object)
    def on_market_tick(self, event: Event):
        """Handle market tick - update prices if needed."""
        # Could implement real-time price updates here
        pass

    def refresh(self):
        """Refresh positions display from database."""
        try:
            # Get database manager
            db = get_db_manager()
            if not db:
                return

            # Query open positions from database
            # In a real implementation, this would query from database
            # For now, just clear table if no active positions
            self.table.setRowCount(0)

        except Exception as e:
            # Log error but don't crash
            import logging
            logging.error(f"Failed to refresh positions: {e}")