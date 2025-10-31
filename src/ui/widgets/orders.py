"""Orders Widget for OrderPilot-AI Trading Application."""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from src.common.event_bus import Event, EventType, event_bus


class OrdersWidget(QWidget):
    """Widget for displaying orders."""

    def __init__(self):
        super().__init__()
        self.order_rows = {}  # Map order_id to row number
        self.init_ui()
        self.setup_event_handlers()

    def init_ui(self):
        """Initialize the orders UI."""
        layout = QVBoxLayout(self)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Order ID", "Symbol", "Side", "Type", "Quantity", "Price", "Status"
        ])

        # Set column stretch
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.ORDER_CREATED, self.on_order_created)
        event_bus.subscribe(EventType.ORDER_SUBMITTED, self.on_order_updated)
        event_bus.subscribe(EventType.ORDER_FILLED, self.on_order_updated)
        event_bus.subscribe(EventType.ORDER_CANCELLED, self.on_order_updated)
        event_bus.subscribe(EventType.ORDER_REJECTED, self.on_order_updated)

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
        order_id = order_data.get("order_id", "--")

        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        # Track row for this order
        self.order_rows[order_id] = row_count

        self.table.setItem(row_count, 0, QTableWidgetItem(str(order_id)))
        self.table.setItem(row_count, 1, QTableWidgetItem(order_data.get("symbol", "--")))
        self.table.setItem(row_count, 2, QTableWidgetItem(str(order_data.get("side", "--"))))
        self.table.setItem(row_count, 3, QTableWidgetItem(str(order_data.get("order_type", "--"))))
        self.table.setItem(row_count, 4, QTableWidgetItem(str(order_data.get("quantity", "--"))))
        self.table.setItem(row_count, 5, QTableWidgetItem(str(order_data.get("price", "--"))))
        self.table.setItem(row_count, 6, QTableWidgetItem(str(order_data.get("status", "--"))))

    def update_order(self, order_data):
        """Update an existing order in the table."""
        order_id = order_data.get("order_id", "--")

        # Find the row for this order
        row = self.order_rows.get(order_id)
        if row is None:
            # Order not in table yet, add it
            self.add_order(order_data)
            return

        # Update the existing row
        if order_data.get("symbol"):
            self.table.setItem(row, 1, QTableWidgetItem(order_data.get("symbol")))
        if order_data.get("side"):
            self.table.setItem(row, 2, QTableWidgetItem(str(order_data.get("side"))))
        if order_data.get("order_type"):
            self.table.setItem(row, 3, QTableWidgetItem(str(order_data.get("order_type"))))
        if order_data.get("quantity"):
            self.table.setItem(row, 4, QTableWidgetItem(str(order_data.get("quantity"))))
        if order_data.get("price"):
            self.table.setItem(row, 5, QTableWidgetItem(str(order_data.get("price"))))
        if order_data.get("status"):
            self.table.setItem(row, 6, QTableWidgetItem(str(order_data.get("status"))))