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
from ..widgets.dashboard import DashboardWidget
from ..widgets.indicators import IndicatorsWidget
from ..widgets.orders import OrdersWidget
from ..widgets.performance_dashboard import PerformanceDashboard
from ..widgets.positions import PositionsWidget
from ..widgets.watchlist import WatchlistWidget

from ..app_console_utils import _show_console_window

logger = logging.getLogger(__name__)


class AppEventsMixin:
    """AppEventsMixin extracted from TradingApplication."""
    def setup_event_handlers(self):
        """Setup event bus handlers."""
        event_bus.subscribe(EventType.MARKET_CONNECTED, self.on_broker_connected)
        event_bus.subscribe(EventType.MARKET_DISCONNECTED, self.on_broker_disconnected)
        event_bus.subscribe(EventType.ORDER_FILLED, self.on_order_filled)
        event_bus.subscribe(EventType.ALERT_TRIGGERED, self.on_alert_triggered)
        event_bus.subscribe(EventType.MARKET_DATA_ERROR, self._on_market_data_error_event)

        # Connect thread-safe signal for error popups
        self._market_data_error.connect(self._show_market_data_error_popup)
    def _on_market_data_error_event(self, event: Event):
        """Handle market data error from background thread."""
        # Emit signal to show popup in main thread
        self._market_data_error.emit(event)
    def _show_market_data_error_popup(self, event: Event):
        """Show error popup in main thread (thread-safe)."""
        error_type = event.data.get("error", "unknown")
        message = event.data.get("message", "Ein unbekannter Fehler ist aufgetreten.")
        source = event.data.get("source", "Market Data")

        if error_type == "connection_limit_exceeded":
            QMessageBox.warning(
                self,
                f"⚠️ {source} - Verbindungsfehler",
                message,
                QMessageBox.StandardButton.Ok
            )
        else:
            QMessageBox.critical(
                self,
                f"❌ {source} - Fehler",
                message,
                QMessageBox.StandardButton.Ok
            )
