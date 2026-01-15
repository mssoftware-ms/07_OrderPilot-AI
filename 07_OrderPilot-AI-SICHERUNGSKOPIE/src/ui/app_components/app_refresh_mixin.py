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


class AppRefreshMixin:
    """AppRefreshMixin extracted from TradingApplication."""
    async def refresh_market_data(self):
        """Refresh market data for all visible widgets."""
        try:
            self.status_bar.showMessage("Refreshing market data...", 2000)

            if hasattr(self.watchlist_widget, 'refresh'):
                await self.watchlist_widget.refresh()

            if hasattr(self.dashboard_widget, 'refresh'):
                await self.dashboard_widget.refresh()

            self.status_bar.showMessage("Market data refreshed", 3000)
            logger.info("Market data refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh market data: {e}")
            self.status_bar.showMessage(f"Refresh failed: {e}", 5000)

    def update_dashboard(self):
        """Periodic dashboard refresh (timer callback)."""
        try:
            if hasattr(self, "dashboard_widget") and hasattr(self.dashboard_widget, "refresh_stats"):
                self.dashboard_widget.refresh_stats()
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}", exc_info=True)
