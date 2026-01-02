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


class AppLifecycleMixin:
    """AppLifecycleMixin extracted from TradingApplication."""
    async def initialize_services(self) -> None:
        """Initialize background services (AI, etc.)."""
        try:
            self.ai_service = get_openai_service()
            if self.ai_service:
                if hasattr(self, "ai_status"):
                    self.ai_status.setText("AI: Ready")
            else:
                if hasattr(self, "ai_status"):
                    self.ai_status.setText("AI: Disabled")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}", exc_info=True)
            if hasattr(self, "ai_status"):
                self.ai_status.setText("AI: Error")
    def show_console_window(self) -> None:
        """Show the hidden console window."""
        _show_console_window()
        self.status_bar.showMessage("Console window shown", 3000)
    def closeEvent(self, event):
        """Handle application close event."""
        logger.info("Application closing...")

        self._close_chart_windows()
        self._save_settings_safe()
        self._stop_timers()
        self._disconnect_streams()
        self._disconnect_broker()
        self._close_ai_service()

        logger.info("Application closed successfully")

        # Clear log file after logging is done
        self._clear_log_files()

        event.accept()

    def _close_chart_windows(self) -> None:
        try:
            if hasattr(self, 'chart_window_manager'):
                self.chart_window_manager.close_all_windows()
            if hasattr(self, 'backtest_chart_manager'):
                self.backtest_chart_manager.close_all_windows()
        except Exception as e:
            logger.error(f"Error closing chart windows: {e}")

    def _save_settings_safe(self) -> None:
        try:
            self.save_settings()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def _stop_timers(self) -> None:
        try:
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            if hasattr(self, 'dashboard_timer'):
                self.dashboard_timer.stop()
        except Exception as e:
            logger.error(f"Error stopping timers: {e}")

    def _run_async_safe(self, coro) -> None:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)

    def _disconnect_streams(self) -> None:
        try:
            if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                logger.info("Disconnecting stock stream...")
                self._run_async_safe(self.history_manager.stop_realtime_stream())

            if hasattr(self.history_manager, 'crypto_stream_client') and self.history_manager.crypto_stream_client:
                logger.info("Disconnecting crypto stream...")
                self._run_async_safe(self.history_manager.stop_crypto_realtime_stream())
        except Exception as e:
            logger.error(f"Error disconnecting streams: {e}")

    def _disconnect_broker(self) -> None:
        if not self.broker:
            return
        try:
            self._run_async_safe(self.disconnect_broker())
        except Exception as e:
            logger.error(f"Error disconnecting broker: {e}")

    def _close_ai_service(self) -> None:
        if not self.ai_service:
            return
        try:
            if hasattr(self.ai_service, 'close'):
                if asyncio.iscoroutinefunction(self.ai_service.close):
                    self._run_async_safe(self.ai_service.close())
                else:
                    self.ai_service.close()
            logger.info("AI service closed")
        except Exception as e:
            logger.error(f"Error closing AI service: {e}")

    def _clear_log_files(self) -> None:
        """Clear the main log file after application shutdown."""
        try:
            # Close all log handlers to release file locks
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                try:
                    handler.close()
                    root_logger.removeHandler(handler)
                except Exception as e:
                    # Can't log here since handlers are being closed
                    pass

            # Clear the main log file
            log_file = Path("./logs/orderpilot.log")
            if log_file.exists():
                log_file.write_text("")
                # Print to console since logging is closed
                print("✅ Log file cleared: logs/orderpilot.log")
        except Exception as e:
            # Print to console since logging might be closed
            print(f"⚠️ Error clearing log file: {e}")
