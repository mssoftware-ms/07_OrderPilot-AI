from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import qasync
from PyQt6.QtCore import QSettings, Qt, QTimer, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ai import get_openai_service
from src.common.event_bus import Event, EventType, event_bus
from src.common.logging_setup import configure_logging
from src.config.loader import config_manager
from src.core.broker import BrokerAdapter
from src.core.market_data.history_provider import HistoryManager
from src.database import initialize_database
from src.chart_marking import MultiMonitorChartManager

from ..chart_window_manager import ChartWindowManager
from ..icons import set_icon_theme
from ..themes import ThemeManager
from ..widgets.alerts import AlertsWidget
from ..widgets.performance_dashboard import PerformanceDashboard
from ..widgets.watchlist import WatchlistWidget

from ..app_console_utils import _show_console_window

logger = logging.getLogger(__name__)


class AppBrokerEventsMixin:
    """AppBrokerEventsMixin extracted from TradingApplication."""
    def on_order_placed(self, order_data: dict[str, Any]):
        """Handle order placement."""
        self.orders_widget.add_order(order_data)
        self.status_bar.showMessage(
            f"Order placed: {order_data['symbol']} {order_data['side']}", 5000
        )
    def on_broker_connected(self, event: Event):
        """Handle broker connection event."""
        logger.info(f"Broker connected: {event.data}")
    def on_broker_disconnected(self, event: Event):
        """Handle broker disconnection event."""
        logger.info(f"Broker disconnected: {event.data}")
    def on_order_filled(self, event: Event):
        """Handle order fill event."""
        order_data = event.data
        self.orders_widget.update_order(order_data)
        self.positions_widget.refresh()

        self.status_bar.showMessage(
            f"Order filled: {order_data.get('symbol')} @ {order_data.get('price')}", 5000
        )
    def on_alert_triggered(self, event: Event):
        """Handle alert trigger event."""
        alert_data = event.data
        self.alerts_widget.add_alert(alert_data)
        QMessageBox.information(self, "Alert",
                              f"Alert triggered: {alert_data.get('message')}")
