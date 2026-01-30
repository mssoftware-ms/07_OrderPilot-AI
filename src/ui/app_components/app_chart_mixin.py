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
from ..widgets.watchlist import WatchlistWidget

from ..app_console_utils import _show_console_window

logger = logging.getLogger(__name__)


class AppChartMixin:
    """AppChartMixin extracted from TradingApplication."""
    def open_chart_popup(self, symbol: str):
        """Open a popup chart window for the symbol."""
        try:
            logger.info(f"Opening popup chart for {symbol}")

            current_index = self.data_provider_combo.currentIndex()
            data_provider = self.data_provider_combo.itemData(current_index)

            self.chart_window_manager.open_or_focus_chart(symbol, data_provider)
            self.status_bar.showMessage(f"Opened chart window for {symbol}", 3000)

        except Exception as e:
            logger.error(f"Failed to open chart popup for {symbol}: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Chart Error",
                f"Failed to open chart window for {symbol}:\n\n{str(e)}\n\nCheck logs for details."
            )
    def on_watchlist_symbol_added(self, symbol: str):
        """Handle symbol added to watchlist."""
        logger.info(f"Symbol added to watchlist: {symbol}")
        asyncio.create_task(self._subscribe_symbol_to_stream(symbol))
        self.status_bar.showMessage(f"Added {symbol} to watchlist", 3000)
    def _create_chart_window(self, symbol: str, timeframe: str = "1T"):
        """Create a new chart window (factory for MultiMonitorChartManager).

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe

        Returns:
            ChartWindow instance
        """
        window = self.chart_window_manager.open_chart(symbol)
        if window and timeframe != "1T":
            # Set timeframe if not default
            chart_widget = getattr(window, "chart_widget", None)
            if chart_widget and hasattr(chart_widget, "set_timeframe"):
                chart_widget.set_timeframe(timeframe)
        return window
