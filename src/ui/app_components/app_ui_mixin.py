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
from ..app_resources import _load_app_icon

logger = logging.getLogger(__name__)


class AppUIMixin:
    """AppUIMixin extracted from TradingApplication."""
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("OrderPilot-AI Trading Application")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(_load_app_icon())

        # Create menu bar (from MenuMixin)
        self.create_menu_bar()

        # Create toolbar (from ToolbarMixin)
        self.create_toolbar()

        # Create central widget with tabs
        self.create_central_widget()

        # Create dock widgets
        self.create_dock_widgets()

        # Create status bar
        self.create_status_bar()

        # Apply initial theme
        self.apply_theme("dark")
    def create_central_widget(self):
        """Create the central widget with tabs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Dashboard tab
        self.dashboard_widget = DashboardWidget()
        self.tab_widget.addTab(self.dashboard_widget, "Dashboard")

        # Positions tab
        self.positions_widget = PositionsWidget()
        self.tab_widget.addTab(self.positions_widget, "Positions")

        # Orders tab
        self.orders_widget = OrdersWidget()
        self.tab_widget.addTab(self.orders_widget, "Orders")

        # Performance Dashboard tab
        self.performance_dashboard = PerformanceDashboard()
        self.tab_widget.addTab(self.performance_dashboard, "Performance")

        # Indicators tab
        self.indicators_widget = IndicatorsWidget()
        self.tab_widget.addTab(self.indicators_widget, "Indicators")

        # Alerts tab
        self.alerts_widget = AlertsWidget()
        self.tab_widget.addTab(self.alerts_widget, "Alerts")
    def create_dock_widgets(self):
        """Create dock widgets for additional panels."""
        # Watchlist dock
        watchlist_dock = QDockWidget("Watchlist", self)
        watchlist_dock.setObjectName("watchlistDock")
        watchlist_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea |
                                      Qt.DockWidgetArea.RightDockWidgetArea)
        self.watchlist_widget = WatchlistWidget()

        # Connect watchlist signals
        # Double-click opens popup chart window
        self.watchlist_widget.symbol_selected.connect(self.open_chart_popup)
        self.watchlist_widget.symbol_added.connect(self.on_watchlist_symbol_added)

        watchlist_dock.setWidget(self.watchlist_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, watchlist_dock)

        # Activity log dock
        log_dock = QDockWidget("Activity Log", self)
        log_dock.setObjectName("activityLogDock")
        log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.addWidget(QLabel("Activity Log"))
        log_dock.setWidget(log_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, log_dock)
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add permanent widgets
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)

        self.market_status = QLabel("Market: Closed")
        self.status_bar.addPermanentWidget(self.market_status)

        self.account_info = QLabel("Account: --")
        self.status_bar.addPermanentWidget(self.account_info)

        # Show initial message
        self.status_bar.showMessage("Ready", 5000)
