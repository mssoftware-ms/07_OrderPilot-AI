"""Main Application for OrderPilot-AI Trading Application.

Implements the main PyQt6 application window with broker connections,
real-time dashboards, and AI-powered order analysis.

REFACTORED: Extracted mixins to meet 600 LOC limit.
- MenuMixin: Menu bar creation
- ToolbarMixin: Toolbar creation and data provider management
- BrokerMixin: Broker connection and streaming functionality
- ActionsMixin: Dialog show methods and UI action handlers
"""

from __future__ import annotations

import asyncio
import ctypes
import logging
import sys
import traceback
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

# qasync for asyncio integration
import qasync
from PyQt6.QtCore import QSettings, Qt, QTimer, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QFont, QIcon, QPixmap

# PyQt6 imports
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

# Application imports
from src.common.logging_setup import configure_logging
from src.config.loader import config_manager
from src.core.broker import BrokerAdapter
from src.core.market_data.history_provider import HistoryManager
from src.database import initialize_database
from src.chart_marking import MultiMonitorChartManager

from .app_components import ActionsMixin, BrokerMixin, MenuMixin, ToolbarMixin

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


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def _get_console_hwnd() -> int:
    if not _is_windows():
        return 0
    return ctypes.windll.kernel32.GetConsoleWindow()


def _hide_console_window() -> None:
    if not _is_windows():
        return
    hwnd = _get_console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)


def _show_console_window() -> None:
    if not _is_windows():
        return
    hwnd = _get_console_hwnd()
    if not hwnd:
        ctypes.windll.kernel32.AllocConsole()
        hwnd = _get_console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 5)


class ConsoleOnErrorHandler(logging.Handler):
    """Show console window on errors."""

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            _show_console_window()


class LogStream(QObject):
    """Redirect stdout/stderr to Qt signal (optional mirror)."""

    text_written = pyqtSignal(str)

    def __init__(self, mirror: Any | None = None) -> None:
        super().__init__()
        self._buffer = ""
        self._mirror = mirror

    def write(self, text: str) -> None:
        if not text:
            return
        if self._mirror is not None:
            try:
                self._mirror.write(text)
                self._mirror.flush()
            except Exception:
                pass
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self.text_written.emit(line)

    def flush(self) -> None:
        if self._mirror is not None:
            try:
                self._mirror.flush()
            except Exception:
                pass
        if self._buffer:
            self.text_written.emit(self._buffer)
            self._buffer = ""


class StartupLogWindow(QWidget):
    """Frameless startup log window."""

    def __init__(self, icon_path: Path):
        super().__init__()
        self._queue: deque[str] = deque()
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._drain_queue)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(520, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(0)

        self._container = QWidget(self)
        self._container.setObjectName("startupContainer")
        self._container.setStyleSheet(
            "QWidget#startupContainer { background-color: white; border-radius: 18px; }"
        )
        outer_layout.addWidget(self._container)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(icon_path))
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            self._icon_label.setPixmap(pixmap)
        layout.addWidget(self._icon_label)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(1000)
        self._log_view.setFrameStyle(QPlainTextEdit.Shape.NoFrame)
        self._log_view.setStyleSheet(
            "QPlainTextEdit { background-color: white; color: black; border: none; }"
        )
        self._log_view.setFont(QFont("Aptos", 10))
        layout.addWidget(self._log_view)

    def enqueue_line(self, line: str) -> None:
        if line is None:
            return
        self._queue.append(line)
        if not self._timer.isActive():
            self._timer.start()

    def _drain_queue(self) -> None:
        if not self._queue:
            self._timer.stop()
            return
        line = self._queue.popleft()
        if line != "":
            self._log_view.appendPlainText(line)


def _load_app_icon() -> QIcon:
    """Load application icon from marketing assets."""
    root_dir = Path(__file__).resolve().parents[2]
    icon_dir = root_dir / "02_Marketing" / "Icons"
    png_icon = icon_dir / "Icon-Orderpilot-AI-Arrow2-256x256.png"
    ico_icon = icon_dir / "Icon-Orderpilot-AI-256x256.ico"

    if png_icon.exists():
        return QIcon(str(png_icon))
    if ico_icon.exists():
        return QIcon(str(ico_icon))

    logger.warning("Application icon not found in %s", icon_dir)
    return QIcon()


def _get_startup_icon_path() -> Path:
    root_dir = Path(__file__).resolve().parents[2]
    return root_dir / "02_Marketing" / "Icons" / "Icon-Orderpilot-AI-Arrow2.png"


class TradingApplication(ActionsMixin, MenuMixin, ToolbarMixin, BrokerMixin, QMainWindow):
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

        # Multi-Chart Manager for multi-window/multi-monitor support
        self._multi_chart_manager = MultiMonitorChartManager(
            chart_factory=self._create_chart_window
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
        self.setWindowIcon(_load_app_icon())

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

    def show_console_window(self) -> None:
        """Show the hidden console window."""
        _show_console_window()
        self.status_bar.showMessage("Console window shown", 3000)

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
    _hide_console_window()

    app = QApplication(sys.argv)
    app.setApplicationName("OrderPilot-AI")
    app.setOrganizationName("OrderPilot")
    app.setStyle("Fusion")
    app.setWindowIcon(_load_app_icon())

    startup_icon_path = _get_startup_icon_path()
    startup_window = StartupLogWindow(startup_icon_path)
    startup_window.show()

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    stdout_stream = LogStream(mirror=original_stdout)
    stderr_stream = LogStream(mirror=original_stderr)
    stdout_stream.text_written.connect(startup_window.enqueue_line, Qt.ConnectionType.QueuedConnection)
    stderr_stream.text_written.connect(startup_window.enqueue_line, Qt.ConnectionType.QueuedConnection)
    sys.stdout = stdout_stream
    sys.stderr = stderr_stream

    configure_logging()
    logger.info("Starting OrderPilot-AI Trading Application")

    root_logger = logging.getLogger()
    root_logger.addHandler(ConsoleOnErrorHandler())

    def _excepthook(exc_type, exc_value, exc_tb):
        _show_console_window()
        traceback.print_exception(exc_type, exc_value, exc_tb)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = TradingApplication()
    window.show()
    QTimer.singleShot(0, startup_window.close)

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
