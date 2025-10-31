"""Alerts Widget for OrderPilot-AI Trading Application."""

from datetime import datetime

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from src.common.event_bus import Event, EventType, event_bus


class AlertsWidget(QWidget):
    """Widget for displaying trading alerts."""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_event_handlers()

    def init_ui(self):
        """Initialize the alerts UI."""
        layout = QVBoxLayout(self)

        # Create list widget for alerts
        self.alerts_list = QListWidget()
        layout.addWidget(self.alerts_list)

    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.ALERT_TRIGGERED, self.on_alert_triggered)
        event_bus.subscribe(EventType.ORDER_REJECTED, self.on_order_rejected)
        event_bus.subscribe(EventType.APP_ERROR, self.on_app_error)

    @pyqtSlot(object)
    def on_alert_triggered(self, event: Event):
        """Handle alert triggered event."""
        if event.data:
            self.add_alert(event.data)

    @pyqtSlot(object)
    def on_order_rejected(self, event: Event):
        """Handle order rejected event."""
        if event.data:
            alert_data = {
                'priority': 'ERROR',
                'message': f"Order rejected: {event.data.get('symbol', 'Unknown')}"
            }
            self.add_alert(alert_data)

    @pyqtSlot(object)
    def on_app_error(self, event: Event):
        """Handle application error event."""
        if event.data:
            alert_data = {
                'priority': 'ERROR',
                'message': f"Error: {event.data.get('message', 'Unknown error')}"
            }
            self.add_alert(alert_data)

    def add_alert(self, alert_data):
        """Add a new alert to the list."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        priority = alert_data.get('priority', 'INFO')
        message = alert_data.get('message', 'Alert')

        alert_text = f"[{timestamp}] [{priority}] {message}"
        item = QListWidgetItem(alert_text)

        # Color code by priority
        if priority == 'ERROR':
            item.setForeground(QColor(255, 0, 0))  # Red
        elif priority == 'WARNING':
            item.setForeground(QColor(255, 165, 0))  # Orange
        else:
            item.setForeground(QColor(255, 255, 255))  # White

        self.alerts_list.addItem(item)

        # Auto-scroll to latest alert
        self.alerts_list.scrollToBottom()