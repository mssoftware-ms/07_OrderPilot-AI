"""Main Application for OrderPilot-AI Trading Application.

Implements the main PyQt6 application window with broker connections,
real-time dashboards, and AI-powered order analysis.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from decimal import Decimal
from typing import Any

# qasync for asyncio integration
import qasync
from PyQt6.QtCore import QSettings, QSize, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.ai import get_openai_service
from src.common.event_bus import Event, EventType, event_bus

# Application imports
from src.common.logging_setup import configure_logging
from src.config.loader import config_manager
from src.core.broker import BrokerAdapter, MockBroker
from src.core.broker.ibkr_adapter import IBKRAdapter
from src.core.broker.trade_republic_adapter import TradeRepublicAdapter
from src.core.market_data.history_provider import HistoryManager
from src.database import initialize_database

from .dialogs.backtest_dialog import BacktestDialog
from .dialogs.order_dialog import OrderDialog
from .dialogs.settings_dialog import SettingsDialog

# UI component imports
from .icons import get_icon, set_icon_theme
from .themes import ThemeManager
from .widgets.alerts import AlertsWidget
from .widgets.chart import ChartWidget
from .widgets.chart_view import ChartView
from .widgets.embedded_tradingview_chart import EmbeddedTradingViewChart
from .widgets.dashboard import DashboardWidget
from .widgets.orders import OrdersWidget
from .widgets.performance_dashboard import PerformanceDashboard
from .widgets.positions import PositionsWidget
from .widgets.strategy_configurator import StrategyConfigurator
from .widgets.watchlist import WatchlistWidget

logger = logging.getLogger(__name__)


class TradingApplication(QMainWindow):
    """Main application window for OrderPilot-AI."""

    # Signals
    broker_connected = pyqtSignal(str)
    broker_disconnected = pyqtSignal(str)
    order_placed = pyqtSignal(dict)
    position_updated = pyqtSignal(dict)
    alert_triggered = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        # Initialize components
        self.broker: BrokerAdapter | None = None
        self.ai_service = None
        self.theme_manager = ThemeManager()
        self.settings = QSettings("OrderPilot", "TradingApp")
        self.history_manager = HistoryManager()

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

        # Set application icon (if available)
        # self.setWindowIcon(QIcon("assets/icon.png"))

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Create central widget with tabs
        self.create_central_widget()

        # Create dock widgets
        self.create_dock_widgets()

        # Create status bar
        self.create_status_bar()

        # Apply initial theme
        self.apply_theme("dark")

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        new_order_action = QAction("&New Order...", self)
        new_order_action.setShortcut("Ctrl+N")
        new_order_action.triggered.connect(self.show_order_dialog)
        file_menu.addAction(new_order_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        theme_menu = view_menu.addMenu("&Theme")
        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)

        light_theme_action = QAction("&Light", self)
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_theme_action)

        # Trading Menu
        trading_menu = menubar.addMenu("&Trading")

        connect_broker_action = QAction("&Connect Broker", self)
        connect_broker_action.triggered.connect(self.connect_broker)
        trading_menu.addAction(connect_broker_action)

        disconnect_broker_action = QAction("&Disconnect Broker", self)
        disconnect_broker_action.triggered.connect(self.disconnect_broker)
        trading_menu.addAction(disconnect_broker_action)

        trading_menu.addSeparator()

        backtest_action = QAction("&Run Backtest...", self)
        backtest_action.triggered.connect(self.show_backtest_dialog)
        trading_menu.addAction(backtest_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        ai_monitor_action = QAction("&AI Usage Monitor", self)
        ai_monitor_action.triggered.connect(self.show_ai_monitor)
        tools_menu.addAction(ai_monitor_action)

        tools_menu.addSeparator()

        reset_layout_action = QAction("&Reset Toolbars && Docks", self)
        reset_layout_action.setToolTip("Reset all toolbars and dock widgets to default positions")
        reset_layout_action.triggered.connect(self.reset_toolbars_and_docks)
        tools_menu.addAction(reset_layout_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Create the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Connect/Disconnect actions
        connect_action = QAction(get_icon("connect"), "Connect", self)
        connect_action.setToolTip("Connect to broker")
        connect_action.triggered.connect(self.connect_broker)
        toolbar.addAction(connect_action)

        disconnect_action = QAction(get_icon("disconnect"), "Disconnect", self)
        disconnect_action.setToolTip("Disconnect from broker")
        disconnect_action.triggered.connect(self.disconnect_broker)
        toolbar.addAction(disconnect_action)

        toolbar.addSeparator()

        # Add broker selector
        broker_label = QLabel("Broker: ")
        broker_label.setToolTip("Select your broker for trading")
        toolbar.addWidget(broker_label)

        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["Mock Broker", "IBKR", "Trade Republic"])
        self.broker_combo.setToolTip(
            "Choose broker:\n"
            "• Mock Broker - Testing with simulated trading\n"
            "• IBKR - Interactive Brokers (TWS/Gateway required)\n"
            "• Trade Republic - Mobile trading platform"
        )
        toolbar.addWidget(self.broker_combo)

        toolbar.addSeparator()

        # Add Market Data Provider selector
        data_provider_label = QLabel("Market Data: ")
        data_provider_label.setToolTip("Select market data provider")
        toolbar.addWidget(data_provider_label)

        self.data_provider_combo = QComboBox()
        self.data_provider_combo.setToolTip(
            "Select market data source:\n"
            "• Auto - Use priority order from settings\n"
            "• Database - Cached historical data\n"
            "• IBKR - Real-time from Interactive Brokers\n"
            "• Alpaca - US stocks (free tier: IEX data)\n"
            "• Alpha Vantage - Global markets (rate limited)\n"
            "• Finnhub - Real-time and historical\n"
            "• Yahoo Finance - Free historical data"
        )
        self.data_provider_combo.currentTextChanged.connect(self.on_data_provider_changed)
        toolbar.addWidget(self.data_provider_combo)

        # Refresh market data action
        refresh_action = QAction(get_icon("refresh"), "Refresh", self)
        refresh_action.setToolTip("Refresh market data")
        refresh_action.triggered.connect(self.refresh_market_data)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # Live Data Toggle (for paper mode)
        self.live_data_toggle = QPushButton("Live Data: OFF")
        self.live_data_toggle.setCheckable(True)
        self.live_data_toggle.setToolTip(
            "Toggle live market data in paper mode\n"
            "• ON: Use real-time market data from providers\n"
            "• OFF: Use cached/simulated data"
        )
        self.live_data_toggle.clicked.connect(self.toggle_live_data)
        toolbar.addWidget(self.live_data_toggle)

        toolbar.addSeparator()

        # Add quick actions
        new_order_action = QAction(get_icon("order"), "New Order", self)
        new_order_action.setToolTip("Place new order")
        new_order_action.triggered.connect(self.show_order_dialog)
        toolbar.addAction(new_order_action)

        backtest_action = QAction(get_icon("backtest"), "Backtest", self)
        backtest_action.setToolTip("Run backtest")
        backtest_action.triggered.connect(self.show_backtest_dialog)
        toolbar.addAction(backtest_action)

        settings_action = QAction(get_icon("settings"), "Settings", self)
        settings_action.setToolTip("Open settings")
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)

        # Connection status
        toolbar.addSeparator()
        self.connection_status = QLabel("● Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        self.connection_status.setToolTip("Broker connection status")
        toolbar.addWidget(self.connection_status)

        # AI status
        self.ai_status = QLabel("AI: Ready")
        self.ai_status.setToolTip(
            "AI service status\n"
            "Configure OpenAI API key in Settings → AI"
        )
        toolbar.addWidget(self.ai_status)

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

        # Chart tab (basic)
        self.chart_widget = ChartWidget()
        self.tab_widget.addTab(self.chart_widget, "Charts")

        # Advanced Chart View tab (with history manager)
        self.chart_view = ChartView(history_manager=self.history_manager)
        self.tab_widget.addTab(self.chart_view, "Advanced Charts")

        # Pro Charts tab (embedded lightweight charts with indicators)
        self.embedded_chart = EmbeddedTradingViewChart(history_manager=self.history_manager)
        self.tab_widget.addTab(self.embedded_chart, "⚡ Pro Charts")

        # Positions tab
        self.positions_widget = PositionsWidget()
        self.tab_widget.addTab(self.positions_widget, "Positions")

        # Orders tab
        self.orders_widget = OrdersWidget()
        self.tab_widget.addTab(self.orders_widget, "Orders")

        # Performance Dashboard tab
        self.performance_dashboard = PerformanceDashboard()
        self.tab_widget.addTab(self.performance_dashboard, "Performance")

        # Strategy Configurator tab
        self.strategy_configurator = StrategyConfigurator()
        self.tab_widget.addTab(self.strategy_configurator, "Strategy")

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
        self.watchlist_widget.symbol_selected.connect(self.show_chart_for_symbol)
        self.watchlist_widget.symbol_added.connect(self.on_watchlist_symbol_added)

        watchlist_dock.setWidget(self.watchlist_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, watchlist_dock)

        # Activity log dock
        log_dock = QDockWidget("Activity Log", self)
        log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.addWidget(QLabel("Activity Log"))
        # Add log viewer implementation here
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

            # NOTE: Don't recreate toolbar on theme change
            # Icons update automatically via set_icon_theme()

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

    @qasync.asyncSlot()
    async def connect_broker(self):
        """Connect to the selected broker."""
        try:
            broker_type = self.broker_combo.currentText()

            # Initialize the appropriate broker
            if broker_type == "Mock Broker":
                self.broker = MockBroker(initial_cash=Decimal("10000"))

            elif broker_type == "Interactive Brokers":
                # Load IBKR settings from QSettings
                ibkr_host = self.settings.value("ibkr_host", "localhost")
                ibkr_port_text = self.settings.value("ibkr_port", "7497 (Paper)")
                ibkr_port = int(ibkr_port_text.split()[0])  # Extract number from "7497 (Paper)"
                ibkr_client_id = int(self.settings.value("ibkr_client_id", "1"))

                self.broker = IBKRAdapter(
                    host=ibkr_host,
                    port=ibkr_port,
                    client_id=ibkr_client_id
                )

                # Register IBKR as market data provider when credentials allow
                self.history_manager.set_ibkr_adapter(self.broker)

                logger.info(f"Connecting to IBKR at {ibkr_host}:{ibkr_port} (Client ID: {ibkr_client_id})")

            elif broker_type == "Trade Republic":
                # Load Trade Republic settings
                tr_phone = self.settings.value("tr_phone", "")
                tr_pin = config_manager.get_credential("tr_pin")

                if not tr_phone:
                    QMessageBox.warning(
                        self, "Missing Settings",
                        "Trade Republic phone number not configured.\n\n"
                        "Please configure in Settings → Brokers"
                    )
                    return

                if not tr_pin:
                    QMessageBox.warning(
                        self, "Missing PIN",
                        "Trade Republic PIN not found.\n\n"
                        "Please configure in Settings → Brokers"
                    )
                    return

                self.broker = TradeRepublicAdapter(
                    phone_number=tr_phone,
                    pin=tr_pin
                )

                logger.info(f"Connecting to Trade Republic with phone {tr_phone}")

            else:
                QMessageBox.warning(
                    self, "Unknown Broker",
                    f"Broker type '{broker_type}' is not recognized.\n\n"
                    f"Available brokers:\n"
                    f"  • Mock Broker (for testing)\n"
                    f"  • Interactive Brokers\n"
                    f"  • Trade Republic"
                )
                return

            # Set AI hook if available
            if self.ai_service:
                self.broker.ai_hook = self.analyze_order_with_ai

            # Connect to broker
            await self.broker.connect()

            # Update UI
            self.connection_status.setText("● Connected")
            self.connection_status.setStyleSheet("color: green;")

            # Emit event
            event_bus.emit(Event(
                type=EventType.MARKET_CONNECTED,
                timestamp=datetime.now(),
                data={"broker": broker_type}
            ))

            self.status_bar.showMessage(f"Connected to {broker_type}", 3000)

            # Update dashboard
            await self.update_account_info()

            logger.info(f"Successfully connected to {broker_type}")

        except Exception as e:
            logger.error(f"Failed to connect broker: {e}")
            QMessageBox.critical(
                self, "Connection Error",
                f"Failed to connect to {broker_type}:\n\n{str(e)}\n\n"
                f"Please check:\n"
                f"  • Broker is running (for IBKR: TWS or IB Gateway)\n"
                f"  • Connection settings are correct\n"
                f"  • API is enabled in broker settings"
            )

    @qasync.asyncSlot()
    async def disconnect_broker(self):
        """Disconnect from the broker."""
        if self.broker:
            try:
                await self.broker.disconnect()
                self.broker = None

                self.connection_status.setText("● Disconnected")
                self.connection_status.setStyleSheet("color: red;")

                event_bus.emit(Event(
                    type=EventType.MARKET_DISCONNECTED,
                    timestamp=datetime.now(),
                    data={}
                ))

                self.status_bar.showMessage("Disconnected from broker", 3000)

            except Exception as e:
                logger.error(f"Failed to disconnect broker: {e}")

    def analyze_order_with_ai(self, analysis_request):
        """AI hook for order analysis."""
        # This will be called by the broker before placing orders
        # For now, return a simple approval
        from core.broker import AIAnalysisResult

        return AIAnalysisResult(
            approved=True,
            confidence=0.8,
            reasoning="Mock analysis for testing",
            risks_identified=[],
            opportunities_identified=["Test opportunity"],
            fee_impact_warning=None,
            display_data={}
        )

    def toggle_live_data(self):
        """Toggle live market data on/off."""
        try:
            is_live = self.live_data_toggle.isChecked()

            # Update button text and style
            if is_live:
                self.live_data_toggle.setText("Live Data: ON")
                self.live_data_toggle.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
                self.status_bar.showMessage("Live market data enabled", 3000)
                logger.info("Live market data enabled")

                # Switch to first available live provider if currently on Database
                current_index = self.data_provider_combo.currentIndex()
                current_source = self.data_provider_combo.itemData(current_index)

                if current_source == "database" or current_source is None:
                    # Find first non-database provider
                    for i in range(self.data_provider_combo.count()):
                        source = self.data_provider_combo.itemData(i)
                        if source and source not in ["database", None] and not source.endswith("_disabled"):
                            self.data_provider_combo.setCurrentIndex(i)
                            break
            else:
                self.live_data_toggle.setText("Live Data: OFF")
                self.live_data_toggle.setStyleSheet("")
                self.status_bar.showMessage("Live market data disabled - using cached data", 3000)
                logger.info("Live market data disabled")

                # Switch to Database/Auto
                for i in range(self.data_provider_combo.count()):
                    source = self.data_provider_combo.itemData(i)
                    if source == "database" or source is None:
                        self.data_provider_combo.setCurrentIndex(i)
                        break

            # Save preference
            self.settings.setValue("live_data_enabled", is_live)

        except Exception as e:
            logger.error(f"Failed to toggle live data: {e}")

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

    def reset_toolbars_and_docks(self):
        """Reset all toolbars and dock widgets to their default positions."""
        try:
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Reset Layout",
                "This will reset all toolbars and dock widgets to their default positions.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Clear saved window state
                self.settings.remove("windowState")
                self.settings.remove("geometry")

                # Reset to default state
                # Show all toolbars
                for toolbar in self.findChildren(QToolBar):
                    toolbar.setVisible(True)
                    # Reset toolbar to top area
                    self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

                # Reset dock widgets to default positions
                for dock in self.findChildren(QDockWidget):
                    dock.setVisible(True)

                    # Reset to default area based on object name or class
                    dock_name = dock.windowTitle()
                    if "Watchlist" in dock_name:
                        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
                    elif "Activity" in dock_name or "Log" in dock_name:
                        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

                # Restore default geometry
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
            QMessageBox.critical(
                self,
                "Reset Failed",
                f"Failed to reset layout:\n\n{str(e)}"
            )

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About OrderPilot-AI",
                        "OrderPilot-AI Trading Application\n\n"
                        "Version 1.0.0\n\n"
                        "An AI-powered trading platform for retail investors.\n\n"
                        "© 2025 OrderPilot")

    @qasync.asyncSlot(str)
    async def show_chart_for_symbol(self, symbol: str):
        """Show chart for selected symbol.

        Args:
            symbol: Trading symbol
        """
        logger.info(f"Showing chart for {symbol}")

        # Get currently selected data provider
        current_index = self.data_provider_combo.currentIndex()
        data_provider = self.data_provider_combo.itemData(current_index)

        # Switch to Advanced Charts tab
        self.tab_widget.setCurrentWidget(self.chart_view)

        # Load symbol in chart with selected data provider
        if hasattr(self.chart_view, 'load_symbol'):
            try:
                self.status_bar.showMessage(f"Loading {symbol} chart...", 2000)
                await self.chart_view.load_symbol(symbol, data_provider)
                self.status_bar.showMessage(f"Loaded {symbol} chart", 3000)
            except Exception as e:
                logger.error(f"Failed to load chart for {symbol}: {e}")
                self.status_bar.showMessage(f"Failed to load chart: {e}", 5000)
        else:
            # Update status if not available
            self.status_bar.showMessage(f"Chart for {symbol} (Implementation pending)", 3000)

    def on_watchlist_symbol_added(self, symbol: str):
        """Handle symbol added to watchlist.

        Args:
            symbol: Trading symbol
        """
        logger.info(f"Symbol added to watchlist: {symbol}")

        # Subscribe to real-time data if streaming is active
        if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
            import asyncio
            asyncio.create_task(self.history_manager.stream_client.subscribe([symbol]))

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

        # Show notification
        QMessageBox.information(self, "Alert",
                              f"Alert triggered: {alert_data.get('message')}")

    def update_time(self):
        """Update time display."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)

    @qasync.asyncSlot()
    async def update_dashboard(self):
        """Update dashboard with latest data."""
        # Skip if already updating
        if self._updating:
            return

        self._updating = True
        try:
            if self.broker and await self.broker.is_connected():
                try:
                    # Update positions
                    positions = await self.broker.get_positions()
                    self.positions_widget.update_positions(positions)

                    # Update account info
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

                # Update dashboard
                self.dashboard_widget.update_balance(balance)

            except Exception as e:
                logger.error(f"Failed to update account info: {e}")

    def update_data_provider_list(self):
        """Update the list of available market data providers."""
        try:
            # Get available providers from history manager
            available_sources = self.history_manager.get_available_sources()

            # Clear and repopulate combo box
            self.data_provider_combo.clear()

            # Add "Auto" option (uses priority order)
            self.data_provider_combo.addItem("Auto (Priority Order)", None)

            # Define all possible providers with display names
            provider_display_names = {
                "database": "Database (Cache)",
                "ibkr": "Interactive Brokers",
                "alpaca": "Alpaca",
                "alpha_vantage": "Alpha Vantage",
                "finnhub": "Finnhub",
                "yahoo": "Yahoo Finance"
            }

            # Add available (active) providers
            for source in available_sources:
                display_name = provider_display_names.get(source, source.title())
                self.data_provider_combo.addItem(f"{display_name}", source)

            # Check config for providers that are enabled but not active (no API keys)
            profile = config_manager.load_profile()
            market_config = profile.market_data

            # Check each provider and add with warning if enabled but not available
            if market_config.alpaca_enabled and "alpaca" not in available_sources:
                self.data_provider_combo.addItem(
                    "Alpaca (Configure API Keys)",
                    "alpaca_disabled"
                )

            if market_config.alpha_vantage_enabled and "alpha_vantage" not in available_sources:
                self.data_provider_combo.addItem(
                    "Alpha Vantage (Configure API Key)",
                    "alpha_vantage_disabled"
                )

            if market_config.finnhub_enabled and "finnhub" not in available_sources:
                self.data_provider_combo.addItem(
                    "Finnhub (Configure API Key)",
                    "finnhub_disabled"
                )

            # Yahoo should always be available if enabled (no API key needed)
            if market_config.yahoo_enabled and "yahoo" not in available_sources:
                # If Yahoo is enabled but not registered, register it now
                from src.core.market_data.history_provider import DataSource, YahooFinanceProvider
                self.history_manager.register_provider(DataSource.YAHOO, YahooFinanceProvider())
                self.data_provider_combo.addItem("Yahoo Finance", "yahoo")
                logger.info("Registered Yahoo Finance provider")

            # Load saved preference
            saved_provider = self.settings.value("market_data_provider", "Auto (Priority Order)")
            index = self.data_provider_combo.findText(saved_provider)
            if index >= 0:
                self.data_provider_combo.setCurrentIndex(index)

            logger.info(f"Available market data providers: {available_sources}")
            logger.info(f"Total providers in dropdown: {self.data_provider_combo.count()}")

        except Exception as e:
            logger.error(f"Failed to update data provider list: {e}")

    @qasync.asyncSlot(str)
    async def on_data_provider_changed(self, provider_name: str):
        """Handle market data provider change.

        Args:
            provider_name: Selected provider name
        """
        try:
            # Save preference
            self.settings.setValue("market_data_provider", provider_name)

            # Get provider source from combo box data
            current_index = self.data_provider_combo.currentIndex()
            source = self.data_provider_combo.itemData(current_index)

            # Check if provider is disabled (needs configuration)
            if source and isinstance(source, str) and source.endswith("_disabled"):
                QMessageBox.information(
                    self,
                    "Configure Provider",
                    f"This provider requires API credentials.\n\n"
                    f"Please go to:\n"
                    f"Settings → Market Data → {provider_name.split('(')[0].strip()}\n\n"
                    f"and enter your API keys to enable this provider."
                )
                # Reset to Auto
                self.data_provider_combo.setCurrentIndex(0)
                return

            if source:
                logger.info(f"Switched market data provider to: {provider_name} ({source})")
                self.status_bar.showMessage(f"Market data source: {provider_name}", 3000)
            else:
                logger.info("Using automatic provider priority order")
                self.status_bar.showMessage("Market data: Auto (Priority Order)", 3000)

            # Ensure the advanced chart view uses the newly selected provider
            if hasattr(self.chart_view, 'current_data_provider'):
                self.chart_view.current_data_provider = source

            # Refresh data in chart view if visible
            if hasattr(self.chart_view, 'refresh_data'):
                await self.chart_view.refresh_data()

        except Exception as e:
            logger.error(f"Failed to change data provider: {e}")

    @qasync.asyncSlot()
    async def refresh_market_data(self):
        """Refresh market data for all visible widgets."""
        try:
            self.status_bar.showMessage("Refreshing market data...", 2000)

            # Refresh watchlist
            if hasattr(self.watchlist_widget, 'refresh'):
                await self.watchlist_widget.refresh()

            # Refresh chart view with current data provider
            if hasattr(self.chart_view, 'refresh_data'):
                # Update data provider in case it changed
                current_index = self.data_provider_combo.currentIndex()
                data_provider = self.data_provider_combo.itemData(current_index)
                if hasattr(self.chart_view, 'current_data_provider'):
                    self.chart_view.current_data_provider = data_provider
                await self.chart_view.refresh_data()

            # Refresh dashboard
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

        # Disconnect broker (synchronously)
        if self.broker:
            try:
                # Get the event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule disconnect as a task
                    asyncio.ensure_future(self.disconnect_broker())
                else:
                    # Run synchronously if loop is not running
                    loop.run_until_complete(self.disconnect_broker())
            except Exception as e:
                logger.error(f"Error disconnecting broker: {e}")

        # Close AI service
        if self.ai_service:
            try:
                # AI service may not have a close method, check first
                if hasattr(self.ai_service, 'close'):
                    if asyncio.iscoroutinefunction(self.ai_service.close):
                        # Async close
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(self.ai_service.close())
                        else:
                            loop.run_until_complete(self.ai_service.close())
                    else:
                        # Sync close
                        self.ai_service.close()
                logger.info("AI service closed")
            except Exception as e:
                logger.error(f"Error closing AI service: {e}")

        # Stop real-time stream if active
        try:
            if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self.history_manager.stop_realtime_stream())
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")

        logger.info("Application closed successfully")

        # Accept close
        event.accept()


async def main():
    """Main application entry point."""
    # Configure logging
    configure_logging()
    logger.info("Starting OrderPilot-AI Trading Application")

    # Create QApplication with event loop
    app = QApplication(sys.argv)
    app.setApplicationName("OrderPilot-AI")
    app.setOrganizationName("OrderPilot")

    # Set application style
    app.setStyle("Fusion")

    # Create event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create and show main window
    window = TradingApplication()
    window.show()

    # Run event loop
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
