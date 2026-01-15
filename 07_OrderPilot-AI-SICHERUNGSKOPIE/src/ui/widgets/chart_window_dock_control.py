"""Chart Window Dock Control - Window control methods.

Refactored from 706 LOC monolith using composition pattern.

Module 3/6 of chart_window.py split.

Contains:
- minimize_dock(): Legacy - minimize dock (no-op for TradingBotWindow)
- toggle_dock_maximized(): Legacy - toggle maximize (no-op for TradingBotWindow)
- reset_layout(): Reset window layout to default state
- toggle_trading_bot_window(): Toggle TradingBotWindow visibility
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QTimer

logger = logging.getLogger(__name__)


class ChartWindowDockControl:
    """Helper für ChartWindow Window Control (Layout Reset, TradingBotWindow toggle)."""

    def __init__(self, parent):
        """
        Args:
            parent: ChartWindow Instanz
        """
        self.parent = parent

    def minimize_dock(self):
        """Legacy method - minimize dock (no-op for TradingBotWindow).

        With TradingBotWindow, users can use the standard window minimize button.
        """
        # Check if we have TradingBotWindow (new) or dock_widget (legacy)
        if hasattr(self.parent, '_trading_bot_window') and self.parent._trading_bot_window:
            # TradingBotWindow: use standard window minimize
            self.parent._trading_bot_window.showMinimized()
            logger.debug("TradingBotWindow minimized")
            return

        # Legacy dock widget handling
        if not hasattr(self.parent, 'dock_widget') or self.parent.dock_widget is None:
            return

        if self.parent._dock_minimized:
            # Restore from minimized state
            self.parent._dock_minimized = False
            self.parent.bottom_panel.setVisible(True)
            self.parent.bottom_panel.setMaximumHeight(16777215)
            self.parent.bottom_panel.setMinimumHeight(self.parent._saved_dock_height)
            QTimer.singleShot(10, lambda: self.parent.bottom_panel.setMinimumHeight(0))
            logger.debug("Dock restored from minimized state")
        else:
            # Minimize
            self.parent._dock_minimized = True
            self.parent._saved_dock_height = max(self.parent.bottom_panel.height(), 120)
            self.parent.bottom_panel.setVisible(False)
            logger.debug("Dock minimized")

    def toggle_dock_maximized(self):
        """Legacy method - toggle dock maximize (no-op for TradingBotWindow).

        With TradingBotWindow, users can use the standard window maximize button.
        """
        # Check if we have TradingBotWindow (new) or dock_widget (legacy)
        if hasattr(self.parent, '_trading_bot_window') and self.parent._trading_bot_window:
            # TradingBotWindow: use standard window maximize
            if self.parent._trading_bot_window.isMaximized():
                self.parent._trading_bot_window.showNormal()
            else:
                self.parent._trading_bot_window.showMaximized()
            logger.debug("TradingBotWindow maximize toggled")
            return

        # Legacy dock widget handling
        if not hasattr(self.parent, 'dock_widget') or self.parent.dock_widget is None:
            return

        if self.parent._dock_maximized:
            # Restore from maximized state
            self.parent._dock_maximized = False
            if self.parent.dock_widget.isFloating():
                if hasattr(self.parent, '_saved_floating_geometry'):
                    self.parent.dock_widget.setGeometry(self.parent._saved_floating_geometry)
            else:
                self.parent.chart_widget.setVisible(True)
                self.parent.bottom_panel.setMaximumHeight(16777215)
                self.parent.bottom_panel.setMinimumHeight(0)
            logger.debug("Dock restored from maximized state")
        else:
            # Maximize
            self.parent._dock_maximized = True
            self.parent._dock_minimized = False

            if self.parent.dock_widget.isFloating():
                self.parent._saved_floating_geometry = self.parent.dock_widget.geometry()
                from PyQt6.QtGui import QGuiApplication
                dock_center = self.parent.dock_widget.geometry().center()
                current_screen = None
                for screen in QGuiApplication.screens():
                    if screen.geometry().contains(dock_center):
                        current_screen = screen
                        break
                if current_screen is None:
                    current_screen = self.parent.dock_widget.screen()
                screen_geom = current_screen.availableGeometry()
                self.parent.dock_widget.setGeometry(screen_geom)
                logger.debug(f"Dock maximized on screen: {current_screen.name()}")
            else:
                self.parent.bottom_panel.setVisible(True)
                self.parent.chart_widget.setVisible(False)
                logger.debug("Dock maximized (docked mode)")

    def reset_layout(self):
        """Reset window layout to default state.

        Restores chart visibility and clears any maximized/minimized state.
        """
        logger.info("Resetting window layout to defaults")

        # Reset state flags
        self.parent._dock_maximized = False
        self.parent._dock_minimized = False

        # Ensure chart is visible
        self.parent.chart_widget.setVisible(True)

        # Handle TradingBotWindow (new)
        if hasattr(self.parent, '_trading_bot_window') and self.parent._trading_bot_window:
            # Show TradingBotWindow in normal state
            self.parent._trading_bot_window.showNormal()
            self.parent._trading_bot_window.show()
            logger.debug("TradingBotWindow reset to normal state")
        # Handle legacy dock_widget
        elif hasattr(self.parent, 'dock_widget') and self.parent.dock_widget:
            if hasattr(self.parent, '_dock_title_bar') and self.parent._dock_title_bar:
                self.parent._dock_title_bar.set_maximized(False)
            self.parent.bottom_panel.setVisible(True)
            self.parent.bottom_panel.setMaximumHeight(16777215)
            self.parent.bottom_panel.setMinimumHeight(0)
            self.parent.dock_widget.setVisible(True)
            self.parent.dock_widget.setFloating(False)
            self.parent.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.parent.dock_widget)

        # Reset window size if too small
        if self.parent.width() < 700 or self.parent.height() < 450:
            self.parent.resize(1000, 600)
            screen = self.parent.screen().geometry()
            x = (screen.width() - self.parent.width()) // 2
            y = (screen.height() - self.parent.height()) // 2
            self.parent.move(x, y)

        logger.info("Window layout reset complete")
