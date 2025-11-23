"""Positions Widget for OrderPilot-AI Trading Application."""

from decimal import Decimal

from PyQt6.QtCore import pyqtSlot

from src.common.event_bus import Event, EventType
from src.database import get_db_manager
from src.ui.widgets.widget_helpers import BaseTableWidget


class PositionsWidget(BaseTableWidget):
    """Widget for displaying current positions."""

    def _get_table_columns(self) -> list[str]:
        """Define position table columns."""
        return [
            "Symbol", "Quantity", "Avg Cost", "Current Price",
            "Market Value", "P&L", "P&L %"
        ]

    def _get_column_keys(self) -> list[str]:
        """Define keys for mapping position data to columns."""
        return [
            "symbol", "quantity", "average_cost", "current_price",
            "market_value", "unrealized_pnl", "pnl_percentage"
        ]

    def _get_format_functions(self) -> dict:
        """Define format functions for columns."""
        return {
            "average_cost": lambda v: f"€{float(v):.2f}" if v else "--",
            "current_price": lambda v: f"€{float(v):.2f}" if v else "--",
            "market_value": lambda v: f"€{float(v):.2f}" if v else "--",
            "unrealized_pnl": lambda v: f"€{float(v):.2f}" if v else "--",
            "pnl_percentage": lambda v: f"{float(v):.2f}%" if v else "--",
        }

    def update_positions(self, positions):
        """Update positions table."""
        if not self.table:
            return

        self.table.setRowCount(len(positions))

        for row, position in enumerate(positions):
            # Convert position object to dict
            position_data = {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "average_cost": position.average_cost,
                "current_price": position.current_price,
                "market_value": position.market_value,
                "unrealized_pnl": position.unrealized_pnl,
                "pnl_percentage": position.pnl_percentage,
            }
            self.update_row(row, position_data)

    def _setup_event_subscriptions(self):
        """Setup event bus handlers."""
        self._subscribe_event(EventType.ORDER_FILLED, self.on_order_filled)
        self._subscribe_event(EventType.MARKET_TICK, self.on_market_tick)

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