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


class AppSettingsMixin:
    """AppSettingsMixin extracted from TradingApplication."""
    def apply_theme(self, theme_name: str):
        """Apply a theme to the application."""
        try:
            # Normalize theme name to lowercase for comparison
            theme_name_lower = theme_name.lower()

            if theme_name_lower == "dark":
                style_sheet = self.theme_manager.get_dark_theme()
                set_icon_theme("dark")
            else:
                style_sheet = self.theme_manager.get_light_theme()
                set_icon_theme("light")

            self.setStyleSheet(style_sheet)
            self.settings.setValue("theme", theme_name)

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
    def load_settings(self):
        """Load application settings."""
        # Load theme
        theme = self.settings.value("theme", "dark")
        self.apply_theme(theme)

        # Load live data preference
        live_data_enabled = self.settings.value("live_data_enabled", False, type=bool)
        self.live_data_toggle.setChecked(live_data_enabled)
        if live_data_enabled:
            self.live_data_toggle.setText("Live Data: ON")
            self.live_data_toggle.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
        else:
            self.live_data_toggle.setText("Live Data: OFF")

        # Load window geometry with validation to prevent resize loops
        # Issue #22: Corrupted geometry/state can cause infinite resize loops
        self._restoring_state = True  # Flag to prevent resize events during restore
        try:
            geometry = self.settings.value("geometry")
            state = self.settings.value("windowState")

            # Validate geometry before restoring
            if geometry:
                # Try to restore geometry
                restore_ok = self.restoreGeometry(geometry)
                if not restore_ok:
                    logger.warning("Failed to restore window geometry, using defaults")
                    self.setGeometry(100, 100, 1400, 900)

            # Restore window state (docks, toolbars) separately
            # Do NOT restore if geometry failed to prevent conflicts
            if state and geometry:
                self.restoreState(state)

            # Validate final geometry is reasonable
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()
                current_rect = self.geometry()
                # Check if window is visible on screen
                if (current_rect.width() < 200 or current_rect.height() < 200 or
                    current_rect.x() < -100 or current_rect.y() < -100 or
                    current_rect.x() > screen_rect.width() or
                    current_rect.y() > screen_rect.height()):
                    logger.warning("Invalid window geometry detected, resetting to defaults")
                    self.setGeometry(100, 100, 1400, 900)
                    self.settings.remove("geometry")
                    self.settings.remove("windowState")
        except Exception as e:
            logger.error(f"Error restoring window state: {e}, using defaults")
            self.setGeometry(100, 100, 1400, 900)
            self.settings.remove("geometry")
            self.settings.remove("windowState")
        finally:
            # Re-enable resize events after a short delay to let Qt settle
            QTimer.singleShot(100, self._enable_resize_events)
    def _enable_resize_events(self):
        """Re-enable resize events after state restoration."""
        self._restoring_state = False

    def save_settings(self):
        """Save application settings."""
        # Only save if window is in a stable state (not minimized or during restoration)
        if getattr(self, '_restoring_state', False):
            logger.debug("Skipping settings save during state restoration")
            return

        # Check if window is in valid state to save
        if self.isMinimized():
            # Don't save minimized geometry - would restore as tiny window
            logger.debug("Skipping geometry save - window is minimized")
            return

        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
