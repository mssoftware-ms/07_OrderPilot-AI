"""Orders Widget for OrderPilot-AI Trading Application."""

from PyQt6.QtCore import pyqtSlot

from src.common.event_bus import Event, EventType
from src.ui.widgets.widget_helpers import BaseTableWidget


class OrdersWidget(BaseTableWidget):
    """Widget for displaying orders."""

    def __init__(self, parent=None):
        self.order_rows = {}  # Map order_id to row number
        super().__init__(parent)

    def _get_table_columns(self) -> list[str]:
        """Define order table columns."""
        return [
            "Order ID", "Symbol", "Side", "Type", "Quantity", "Price", "Status"
        ]

    def _get_column_keys(self) -> list[str]:
        """Define keys for mapping order data to columns."""
        return [
            "order_id", "symbol", "side", "order_type", "quantity", "price", "status"
        ]

    def _setup_event_subscriptions(self):
        """Setup event bus handlers."""
        self._subscribe_event(EventType.ORDER_CREATED, self.on_order_created)
        self._subscribe_event(EventType.ORDER_SUBMITTED, self.on_order_updated)
        self._subscribe_event(EventType.ORDER_FILLED, self.on_order_updated)
        self._subscribe_event(EventType.ORDER_CANCELLED, self.on_order_updated)
        self._subscribe_event(EventType.ORDER_REJECTED, self.on_order_updated)

    @pyqtSlot(object)
    def on_order_created(self, event: Event):
        """Handle order created event."""
        if event.data:
            self.add_order(event.data)

    @pyqtSlot(object)
    def on_order_updated(self, event: Event):
        """Handle order update events."""
        if event.data:
            self.update_order(event.data)

    def add_order(self, order_data):
        """Add a new order to the table."""
        if not self.table:
            return

        order_id = order_data.get("order_id", "--")

        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        # Track row for this order
        self.order_rows[order_id] = row_count

        # Use base class helper to populate row
        self.update_row(row_count, order_data)

    def update_order(self, order_data):
        """Update an existing order in the table."""
        order_id = order_data.get("order_id", "--")

        # Find the row for this order
        row = self.order_rows.get(order_id)
        if row is None:
            # Order not in table yet, add it
            self.add_order(order_data)
            return

        # Use base class helper to update row
        self.update_row(row, order_data)