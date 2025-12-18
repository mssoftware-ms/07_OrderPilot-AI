"""Main Application for OrderPilot-AI Trading Application.

Implements the main PyQt6 application window with broker connections,
real-time dashboards, and AI-powered order analysis.

REFACTORED: Extracted mixins to meet 600 LOC limit.
- MenuMixin: Menu bar creation
- ToolbarMixin: Toolbar creation and data provider management
- BrokerMixin: Broker connection and streaming functionality
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from typing import Any

# qasync for asyncio integration
import qasync
from PyQt6.QtCore import QSettings, Qt, QTimer, pyqtSignal, pyqtSlot

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ai import get_openai_service
from src.common.event_bus import Event, EventType, event_bus

# Application imports
from src.common.logging_setup import configure_logging
from src.config.loader import config_manager
from src.core.broker import BrokerAdapter
from src.core.market_data.history_provider import HistoryManager
from src.database import initialize_database

from .app_components import BrokerMixin, MenuMixin, ToolbarMixin
from .dialogs.ai_backtest_dialog import AIBacktestDialog
from .dialogs.backtest_dialog import BacktestDialog
from .dialogs.order_dialog import OrderDialog
from .dialogs.parameter_optimization_dialog import ParameterOptimizationDialog
from .dialogs.settings_dialog import SettingsDialog

# UI component imports
from .chart_window_manager import ChartWindowManager
from .icons import set_icon_theme
from .themes import ThemeManager
from .widgets.alerts import AlertsWidget
from .widgets.dashboard import DashboardWidget
from .widgets.indicators import IndicatorsWidget
from .widgets.orders import OrdersWidget
from .widgets.performance_dashboard import PerformanceDashboard
from .widgets.positions import PositionsWidget
from .widgets.watchlist import WatchlistWidget

logger = logging.getLogger(__name__)


class TradingApplication(MenuMixin, ToolbarMixin, BrokerMixin, QMainWindow):
    """Main application window for OrderPilot-AI."""

    # Signals
    broker_connected = pyqtSignal(str)
    broker_disconnected = pyqtSignal(str)
    order_placed = pyqtSignal(dict)
    position_updated = pyqtSignal(dict)
    alert_triggered = pyqtSignal(dict)
    _market_data_error = pyqtSignal(object)  # Thread-safe error signal

    def __init__(self):
        super().__init__()

        # Initialize components
        self.broker: BrokerAdapter | None = None
        self.ai_service = None
        self.theme_manager = ThemeManager()
        self.settings = QSettings("OrderPilot", "TradingApp")
        self.history_manager = HistoryManager()
        self.chart_window_manager = ChartWindowManager(
            history_manager=self.history_manager,
            parent=self
        )
        self.backtest_chart_manager = ChartWindowManager(
            history_manager=self.history_manager,
            parent=self
        )

        # Async update lock to prevent concurrent updates
        self._updating = False

        # Setup UI
        self.init_ui()
        self.setup_event_handlers()
        self.load_settings()

        # Populate market data providers
        self.update_data_provider_list()

        # Start timers
        self.setup_timers()

        # Initialize services
        asyncio.create_task(self.initialize_services())

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("OrderPilot-AI Trading Application")
        self.setGeometry(100, 100, 1400, 900)

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

    @pyqtSlot(object)
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

    def setup_timers(self):
        """Setup update timers."""
        # Time update timer
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # Update every second

        # Dashboard update timer
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self.update_dashboard)
        self.dashboard_timer.start(5000)  # Update every 5 seconds

    async def initialize_services(self):
        """Initialize application services."""
        try:
            # Load configuration
            profile = config_manager.load_profile()

            # Initialize database
            db_config = profile.database
            initialize_database(db_config)

            # Initialize AI service if enabled
            if profile.ai.enabled:
                api_key = config_manager.get_credential("openai_api_key")
                if api_key:
                    self.ai_service = await get_openai_service(profile.ai, api_key)
                    self.ai_status.setText("AI: Active")
                    self.ai_status.setStyleSheet("color: green;")
                else:
                    logger.warning("OpenAI API key not found")
                    self.ai_status.setText("AI: No API Key")
                    self.ai_status.setStyleSheet("color: orange;")

            # Initialize real-time streaming (from BrokerMixin)
            await self.initialize_realtime_streaming()

            self.status_bar.showMessage("Services initialized", 3000)

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            QMessageBox.critical(self, "Initialization Error",
                                f"Failed to initialize services: {e}")

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

        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def save_settings(self):
        """Save application settings."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def show_order_dialog(self):
        """Show the order placement dialog."""
        if not self.broker:
            QMessageBox.warning(self, "No Broker",
                              "Please connect to a broker first")
            return

        dialog = OrderDialog(self.broker, self.ai_service, self)
        dialog.order_placed.connect(self.on_order_placed)
        dialog.exec()

    def show_settings_dialog(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload settings if changed
            self.load_settings()

    def show_backtest_dialog(self):
        """Show the backtest dialog."""
        dialog = BacktestDialog(self.ai_service, self)
        dialog.exec()

    def show_ai_backtest_dialog(self):
        """Show the AI-powered backtest analysis dialog."""
        current_symbol = None
        if hasattr(self, 'backtest_chart_manager'):
            current_symbol = self.backtest_chart_manager.get_active_symbol()

        dialog = AIBacktestDialog(self, current_symbol=current_symbol)
        dialog.exec()

    def show_parameter_optimization_dialog(self):
        """Show the parameter optimization dialog."""
        current_symbol = None
        if hasattr(self, 'backtest_chart_manager'):
            current_symbol = self.backtest_chart_manager.get_active_symbol()

        dialog = ParameterOptimizationDialog(self, current_symbol=current_symbol)
        dialog.exec()

    def show_ai_monitor(self):
        """Show AI usage monitor."""
        if self.ai_service and hasattr(self.ai_service, 'cost_tracker'):
            try:
                cost = self.ai_service.cost_tracker.current_month_cost
                budget = self.ai_service.cost_tracker.monthly_budget

                QMessageBox.information(self, "AI Usage",
                                      f"Current Month Usage: €{cost:.2f}\n"
                                      f"Monthly Budget: €{budget:.2f}\n"
                                      f"Remaining: €{budget - cost:.2f}")
            except Exception as e:
                logger.error(f"Error showing AI monitor: {e}")
                QMessageBox.warning(self, "AI Usage",
                                   f"Error retrieving AI usage data: {e}")
        else:
            QMessageBox.information(self, "AI Usage", "AI service not initialized")

    def show_pattern_db_dialog(self):
        """Show the pattern database management dialog."""
        from src.ui.dialogs import PatternDatabaseDialog
        dialog = PatternDatabaseDialog(self)
        dialog.exec()

    def reset_toolbars_and_docks(self):
        """Reset all toolbars and dock widgets to their default positions."""
        from PyQt6.QtWidgets import QToolBar

        try:
            reply = QMessageBox.question(
                self,
                "Reset Layout",
                "This will reset all toolbars and dock widgets to their default positions.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.settings.remove("windowState")
                self.settings.remove("geometry")

                for toolbar in self.findChildren(QToolBar):
                    toolbar.setVisible(True)
                    self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

                for dock in self.findChildren(QDockWidget):
                    dock.setVisible(True)
                    dock_name = dock.windowTitle()
                    if "Watchlist" in dock_name:
                        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
                    elif "Activity" in dock_name or "Log" in dock_name:
                        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

                self.setGeometry(100, 100, 1400, 900)
                self.status_bar.showMessage("Layout reset to defaults", 3000)
                logger.info("Toolbars and docks reset to default positions")

                QMessageBox.information(
                    self,
                    "Layout Reset",
                    "Toolbars and dock widgets have been reset to their default positions."
                )

        except Exception as e:
            logger.error(f"Failed to reset layout: {e}")
            QMessageBox.critical(self, "Reset Failed", f"Failed to reset layout:\n\n{str(e)}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About OrderPilot-AI",
                        "OrderPilot-AI Trading Application\n\n"
                        "Version 1.0.0\n\n"
                        "An AI-powered trading platform for retail investors.\n\n"
                        "© 2025 OrderPilot")

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

    @pyqtSlot(dict)
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

    def update_time(self):
        """Update time display."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)

    @qasync.asyncSlot()
    async def update_dashboard(self):
        """Update dashboard with latest data."""
        if self._updating:
            return

        self._updating = True
        try:
            if self.broker and await self.broker.is_connected():
                try:
                    positions = await self.broker.get_positions()
                    self.positions_widget.update_positions(positions)
                    await self.update_account_info()
                except Exception as e:
                    logger.error(f"Failed to update dashboard: {e}")
        finally:
            self._updating = False

    @qasync.asyncSlot()
    async def update_account_info(self):
        """Update account information display."""
        if self.broker:
            try:
                balance = await self.broker.get_balance()
                self.account_info.setText(
                    f"Account: €{balance.total_equity:.2f} | "
                    f"Cash: €{balance.cash:.2f}"
                )
                self.dashboard_widget.update_balance(balance)
            except Exception as e:
                logger.error(f"Failed to update account info: {e}")

    @qasync.asyncSlot(str)
    async def on_data_provider_changed(self, provider_name: str):
        """Handle market data provider change."""
        try:
            self.settings.setValue("market_data_provider", provider_name)

            current_index = self.data_provider_combo.currentIndex()
            source = self.data_provider_combo.itemData(current_index)

            if source and isinstance(source, str) and source.endswith("_disabled"):
                QMessageBox.information(
                    self,
                    "Configure Provider",
                    f"This provider requires API credentials.\n\n"
                    f"Please go to:\n"
                    f"Settings → Market Data → {provider_name.split('(')[0].strip()}\n\n"
                    f"and enter your API keys to enable this provider."
                )
                self.data_provider_combo.setCurrentIndex(0)
                return

            if source:
                logger.info(f"Switched market data provider to: {provider_name} ({source})")
                self.status_bar.showMessage(f"Market data source: {provider_name}", 3000)
            else:
                logger.info("Using automatic provider priority order")
                self.status_bar.showMessage("Market data: Auto (Priority Order)", 3000)

        except Exception as e:
            logger.error(f"Failed to change data provider: {e}")

    @qasync.asyncSlot()
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

    def closeEvent(self, event):
        """Handle application close event."""
        logger.info("Application closing...")

        # Close all chart windows
        try:
            if hasattr(self, 'chart_window_manager'):
                self.chart_window_manager.close_all_windows()
            if hasattr(self, 'backtest_chart_manager'):
                self.backtest_chart_manager.close_all_windows()
        except Exception as e:
            logger.error(f"Error closing chart windows: {e}")

        # Save settings
        try:
            self.save_settings()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

        # Stop timers
        try:
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            if hasattr(self, 'dashboard_timer'):
                self.dashboard_timer.stop()
        except Exception as e:
            logger.error(f"Error stopping timers: {e}")

        # Disconnect real-time streams
        try:
            if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                logger.info("Disconnecting stock stream...")
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.history_manager.stop_realtime_stream())
                else:
                    loop.run_until_complete(self.history_manager.stop_realtime_stream())

            if hasattr(self.history_manager, 'crypto_stream_client') and self.history_manager.crypto_stream_client:
                logger.info("Disconnecting crypto stream...")
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.history_manager.stop_crypto_realtime_stream())
                else:
                    loop.run_until_complete(self.history_manager.stop_crypto_realtime_stream())
        except Exception as e:
            logger.error(f"Error disconnecting streams: {e}")

        # Disconnect broker
        if self.broker:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self.disconnect_broker())
                else:
                    loop.run_until_complete(self.disconnect_broker())
            except Exception as e:
                logger.error(f"Error disconnecting broker: {e}")

        # Close AI service
        if self.ai_service:
            try:
                if hasattr(self.ai_service, 'close'):
                    if asyncio.iscoroutinefunction(self.ai_service.close):
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(self.ai_service.close())
                        else:
                            loop.run_until_complete(self.ai_service.close())
                    else:
                        self.ai_service.close()
                logger.info("AI service closed")
            except Exception as e:
                logger.error(f"Error closing AI service: {e}")

        logger.info("Application closed successfully")
        event.accept()


async def main():
    """Main application entry point."""
    configure_logging()
    logger.info("Starting OrderPilot-AI Trading Application")

    app = QApplication(sys.argv)
    app.setApplicationName("OrderPilot-AI")
    app.setOrganizationName("OrderPilot")
    app.setStyle("Fusion")

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = TradingApplication()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
