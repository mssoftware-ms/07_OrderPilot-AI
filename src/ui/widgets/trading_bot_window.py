"""Trading Bot Window - Standalone window for Trading Bot panel.

Replaces the previous QDockWidget implementation with a proper standalone window
that saves and restores its position independently.

Features:
- Standalone window (not docked)
- Position/size persistence via QSettings
- Contains all Bot tabs from PanelsMixin
- Can be toggled via "Trading Bot" button
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QCloseEvent

from src.ui.debug import UIInspectorMixin  # F12 UI Inspector

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class TradingBotWindow(UIInspectorMixin, QMainWindow):  # F12 UI Inspector
    """Standalone window for Trading Bot panel.

    Features:
        - Independent window with own position/size
        - Contains all trading bot tabs
        - State persistence via QSettings
        - Close event emits signal to update button state
    """

    # Signals
    window_closed = pyqtSignal()
    visibility_changed = pyqtSignal(bool)

    def __init__(self, parent_chart: "ChartWindow", panel_content: QWidget):
        """Initialize Trading Bot window.

        Args:
            parent_chart: Parent ChartWindow instance
            panel_content: The QWidget containing all bot tabs (from _create_bottom_panel)
        """
        super().__init__(parent_chart)

        self._parent_chart = parent_chart
        self._panel_content = panel_content
        self.settings = QSettings("OrderPilot", "TradingApp")

        # State tracking
        self._saved_maximized = False
        self._saved_geometry = None

        self._setup_window()
        self._load_window_state()

        # F12 UI Inspector Debug Overlay
        self.setup_ui_inspector()

        logger.info(f"TradingBotWindow created for {parent_chart.symbol}")

    def _setup_window(self) -> None:
        """Configure window properties."""
        symbol = getattr(self._parent_chart, 'symbol', 'Unknown')
        self.setWindowTitle(f"Trading Bot - {symbol}")

        # Window flags: Normal window with standard buttons
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Set minimum size
        self.setMinimumSize(600, 400)

        # Set the panel content as central widget
        self.setCentralWidget(self._panel_content)

    def _get_settings_key(self) -> str:
        """Get sanitized settings key for this window."""
        symbol = getattr(self._parent_chart, 'symbol', 'Unknown')
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        return f"TradingBotWindow/{safe_symbol}"

    def _load_window_state(self) -> None:
        """Load window position, size and maximized state from settings."""
        settings_key = self._get_settings_key()

        # Load geometry (position + size)
        geometry = self.settings.value(f"{settings_key}/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            self._saved_geometry = geometry
            logger.debug(f"Restored TradingBotWindow geometry for {self._parent_chart.symbol}")
        else:
            # Default size and position (below chart window)
            self.resize(800, 350)
            # Try to position below the parent chart
            if self._parent_chart:
                parent_geo = self._parent_chart.geometry()
                self.move(
                    parent_geo.x(),
                    parent_geo.y() + parent_geo.height() + 30
                )

        # Restore window state (toolbars, etc.)
        window_state = self.settings.value(f"{settings_key}/windowState")
        if window_state:
            self.restoreState(window_state)

        # Load maximized state
        self._saved_maximized = self.settings.value(f"{settings_key}/maximized", False, type=bool)
        logger.debug(f"Loaded maximized state: {self._saved_maximized}")

        # Restore visibility - default is hidden, but restore if was visible before
        was_visible = self.settings.value(f"{settings_key}/visible", False, type=bool)
        if was_visible:
            # Don't show immediately - let chart_window_setup handle initial state
            # This just records that we should restore visibility
            self._restore_visibility = True
            logger.debug(f"TradingBotWindow will restore visible state for {self._parent_chart.symbol}")
        else:
            self._restore_visibility = False

        logger.debug(f"Loaded TradingBotWindow state for {self._parent_chart.symbol}")

    def _save_window_state(self) -> None:
        """Save window position, size and maximized state to settings."""
        settings_key = self._get_settings_key()

        # Save maximized state BEFORE saving geometry
        is_maximized = self.isMaximized()
        self.settings.setValue(f"{settings_key}/maximized", is_maximized)

        # If maximized, save the normal geometry (before maximize)
        # Otherwise save current geometry
        if is_maximized and self._saved_geometry:
            # Keep the pre-maximized geometry
            self.settings.setValue(f"{settings_key}/geometry", self._saved_geometry)
        else:
            # Save current geometry and update cached value
            current_geometry = self.saveGeometry()
            self.settings.setValue(f"{settings_key}/geometry", current_geometry)
            if not is_maximized:
                self._saved_geometry = current_geometry

        self.settings.setValue(f"{settings_key}/windowState", self.saveState())
        self.settings.setValue(f"{settings_key}/visible", self.isVisible())

        logger.debug(f"Saved TradingBotWindow state: maximized={is_maximized}, visible={self.isVisible()}")

    def showEvent(self, event) -> None:
        """Handle show event - restore maximized state if needed."""
        super().showEvent(event)

        # Restore maximized state on show (deferred to allow geometry to be applied first)
        if self._saved_maximized and not self.isMaximized():
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.showMaximized)
            logger.debug("Restoring maximized state")

        self.visibility_changed.emit(True)

    def resizeEvent(self, event) -> None:
        """Track geometry changes for save/restore."""
        super().resizeEvent(event)
        # Save normal geometry when not maximized (for restore after maximize)
        if not self.isMaximized():
            self._saved_geometry = self.saveGeometry()

    def moveEvent(self, event) -> None:
        """Track position changes for save/restore."""
        super().moveEvent(event)
        # Save normal geometry when not maximized
        if not self.isMaximized():
            self._saved_geometry = self.saveGeometry()

    def hideEvent(self, event) -> None:
        """Handle hide event - save state before hiding."""
        # Update maximized state before saving
        self._saved_maximized = self.isMaximized()
        self._save_window_state()
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def changeEvent(self, event) -> None:
        """Track window state changes (maximize/restore)."""
        super().changeEvent(event)
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            # Update maximized state tracking
            self._saved_maximized = self.isMaximized()
            logger.debug(f"Window state changed: maximized={self._saved_maximized}")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event.

        Instead of closing, we hide the window and emit signal.
        """
        # Update maximized state before saving
        self._saved_maximized = self.isMaximized()
        self._save_window_state()
        self.hide()
        self.window_closed.emit()
        event.ignore()  # Don't actually close, just hide

    def toggle_visibility(self) -> None:
        """Toggle window visibility with state restoration."""
        if self.isVisible():
            # Save state before hiding
            self._saved_maximized = self.isMaximized()
            self._save_window_state()
            self.hide()
        else:
            # Show and restore state
            self.show()
            self.raise_()
            self.activateWindow()
            # Maximized state is restored in showEvent()

    def update_symbol(self, symbol: str) -> None:
        """Update window title with new symbol.

        Args:
            symbol: New trading symbol
        """
        self.setWindowTitle(f"Trading Bot - {symbol}")


# Re-export
__all__ = ["TradingBotWindow"]
