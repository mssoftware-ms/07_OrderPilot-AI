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


class AppSettingsMixin:
    """AppSettingsMixin extracted from TradingApplication."""
    def apply_theme(self, theme_name: str):
        """Apply a theme to the application."""
        try:
            # Normalize theme name for keys
            t_key = theme_name.lower().replace(" ", "_")

            # Get customization overrides from settings using PREFIXED keys
            overrides = {}
            keys = [
                "ui_bg_color", "ui_btn_color", "ui_dropdown_color", "ui_edit_color",
                "ui_edit_text_color",
                "ui_active_btn_color", "ui_inactive_btn_color",
                "ui_btn_hover_border_color", "ui_btn_hover_text_color",
                "ui_btn_font_family", "ui_btn_font_size", "ui_btn_width", "ui_btn_height"
            ]
            for key in keys:
                # Try prefixed key first (theme-specific)
                val = self.settings.value(f"{t_key}_{key}")
                if val is not None:
                    overrides[key] = val
                else:
                    # Fallback to legacy global key
                    val = self.settings.value(key)
                    if val is not None:
                        overrides[key] = val

            # Get stylesheet from generic manager with overrides
            style_sheet = self.theme_manager.get_theme(theme_name, overrides=overrides)
            self.setStyleSheet(style_sheet)

            # Update icons - Both our current themes are "dark" based for icons
            set_icon_theme("dark")

            self.settings.setValue("theme", theme_name)

            # Notify ThemeService so all subscribed widgets update
            from src.ui.design_system import theme_service
            theme_service.set_theme(theme_name)

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
    def load_settings(self):
        """Load application settings."""
        # Load theme
        theme = self.settings.value("theme", "dark")
        self.apply_theme(theme)

        # Load icon settings - Now theme aware
        from src.ui.icons import configure_icon_provider
        
        t_key = theme.lower().replace(" ", "_")
        icon_dir = self.settings.value(f"{t_key}_icon_dir", self.settings.value("icon_dir", ""))
        icon_force_white = self.settings.value(f"{t_key}_icon_force_white", self.settings.value("icon_force_white", True), type=bool)
        
        # Configure Icon Provider - ALWAYS use workspace assets
        # (The icon_dir in settings is only a source for the AI to copy from)
        configure_icon_provider(
            icons_dir=None,
            invert_to_white=icon_force_white
        )

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
