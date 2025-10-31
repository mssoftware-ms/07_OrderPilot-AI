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
from src.database import initialize_database

from .dialogs.backtest_dialog import BacktestDialog
from .dialogs.order_dialog import OrderDialog
from .dialogs.settings_dialog import SettingsDialog

# UI component imports
from .themes import ThemeManager
from .widgets.alerts import AlertsWidget
from .widgets.chart import ChartWidget
from .widgets.chart_view import ChartView
from .widgets.dashboard import DashboardWidget
from .widgets.orders import OrdersWidget
from .widgets.performance_dashboard import PerformanceDashboard
from .widgets.positions import PositionsWidget
from .widgets.strategy_configurator import StrategyConfigurator

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

        # Async update lock to prevent concurrent updates
        self._updating = False

        # Setup UI
        self.init_ui()
        self.setup_event_handlers()
        self.load_settings()

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

        # Add broker selector
        broker_label = QLabel("Broker: ")
        toolbar.addWidget(broker_label)

        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["Mock Broker", "IBKR", "Trade Republic"])
        toolbar.addWidget(self.broker_combo)

        toolbar.addSeparator()

        # Add quick actions
        new_order_btn = QPushButton("New Order")
        new_order_btn.clicked.connect(self.show_order_dialog)
        toolbar.addWidget(new_order_btn)

        # Connection status
        toolbar.addSeparator()
        self.connection_status = QLabel("● Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        toolbar.addWidget(self.connection_status)

        # AI status
        self.ai_status = QLabel("AI: Ready")
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

        # Advanced Chart View tab
        self.chart_view = ChartView()
        self.tab_widget.addTab(self.chart_view, "Advanced Charts")

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
        watchlist_widget = QWidget()
        watchlist_layout = QVBoxLayout(watchlist_widget)
        watchlist_layout.addWidget(QLabel("Watchlist"))
        # Add watchlist implementation here
        watchlist_dock.setWidget(watchlist_widget)
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
            if theme_name == "dark":
                style_sheet = self.theme_manager.get_dark_theme()
            else:
                style_sheet = self.theme_manager.get_light_theme()

            self.setStyleSheet(style_sheet)
            self.settings.setValue("theme", theme_name)

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")

    def load_settings(self):
        """Load application settings."""
        # Load theme
        theme = self.settings.value("theme", "dark")
        self.apply_theme(theme)

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
        if self.ai_service:
            cost = self.ai_service.cost_tracker.current_month_cost
            budget = self.ai_service.cost_tracker.monthly_budget

            QMessageBox.information(self, "AI Usage",
                                  f"Current Month Usage: €{cost:.2f}\n"
                                  f"Monthly Budget: €{budget:.2f}\n"
                                  f"Remaining: €{budget - cost:.2f}")
        else:
            QMessageBox.information(self, "AI Usage", "AI service not initialized")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About OrderPilot-AI",
                        "OrderPilot-AI Trading Application\n\n"
                        "Version 1.0.0\n\n"
                        "An AI-powered trading platform for retail investors.\n\n"
                        "© 2025 OrderPilot")

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

    def closeEvent(self, event):
        """Handle application close event."""
        # Save settings
        self.save_settings()

        # Disconnect broker
        if self.broker:
            asyncio.create_task(self.disconnect_broker())

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
        await loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())