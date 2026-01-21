"""Main Application for OrderPilot-AI Trading Application."""

from __future__ import annotations

import asyncio
import logging
import sys
import traceback

import qasync
from PyQt6.QtCore import QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow

from src.common.logging_setup import configure_logging
from src.core.broker import BrokerAdapter
from src.core.market_data.history_provider import HistoryManager
from src.chart_marking import MultiMonitorChartManager

from .app_components import ActionsMixin, BrokerMixin, MenuMixin, ToolbarMixin
from .app_components.app_broker_events_mixin import AppBrokerEventsMixin
from .app_components.app_chart_mixin import AppChartMixin
from .app_components.app_events_mixin import AppEventsMixin
from .app_components.app_lifecycle_mixin import AppLifecycleMixin
from .app_components.app_refresh_mixin import AppRefreshMixin
from .app_components.app_settings_mixin import AppSettingsMixin
from .app_components.app_timers_mixin import AppTimersMixin
from .app_components.app_ui_mixin import AppUIMixin
from .app_console_utils import _hide_console_window, _show_console_window
from .app_icon import get_app_icon, set_window_icon  # Issue #29: App icon (candlestick chart)
from .app_logging import ConsoleOnErrorHandler, LogStream
from .app_resources import _get_startup_icon_path, _load_app_icon
from .app_startup_window import StartupLogWindow
from .chart_window_manager import ChartWindowManager
from .themes import ThemeManager

logger = logging.getLogger(__name__)


class TradingApplication(
    ActionsMixin,
    MenuMixin,
    ToolbarMixin,
    BrokerMixin,
    AppUIMixin,
    AppEventsMixin,
    AppTimersMixin,
    AppSettingsMixin,
    AppChartMixin,
    AppBrokerEventsMixin,
    AppRefreshMixin,
    AppLifecycleMixin,
    QMainWindow,
):
    """Main application window for OrderPilot-AI."""

    _market_data_error = pyqtSignal(object)

    def __init__(self, splash=None):
        super().__init__()
        if splash: splash.set_progress(60, "Initialisiere UI-System...")

        # Issue #29: Set application icon (candlestick chart, white)
        set_window_icon(self)

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

        if splash: splash.set_progress(70, "Multi-Chart Manager...")
        # Multi-Chart Manager for multi-window/multi-monitor support
        self._multi_chart_manager = MultiMonitorChartManager(
            chart_factory=self._create_chart_window
        )

        # Async update lock to prevent concurrent updates
        self._updating = False

        # Setup UI
        self.init_ui()
        if splash: splash.set_progress(80, "Konfiguriere Event-System...")
        self.setup_event_handlers()
        self.load_settings()

        # Populate market data providers
        self.update_data_provider_list()

        # Start timers
        if splash: splash.set_progress(90, "Starte Hintergrunddienste...")
        self.setup_timers()

        # Initialize services
        asyncio.create_task(self.initialize_services())


def _apply_saved_debug_level(level_str: str) -> None:
    """Apply saved console debug level to all loggers.

    Args:
        level_str: Log level string (DEBUG, INFO, WARNING, ERROR)
    """
    import logging

    level = getattr(logging, level_str.upper(), logging.INFO)

    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Set console handler level
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)

    # Stream/chart provider loggers - suppress at WARNING level to reduce noise
    stream_loggers = [
        'src.core.market_data.bitunix_stream',
        'src.core.market_data.bitunix_stream_connection',
        'src.core.market_data.bitunix_stream_handlers',
        'src.core.market_data.bitunix_stream_messages',
        'src.core.market_data.bitunix_stream_subscription',
        'src.core.market_data.history_provider',
        'src.core.market_data.history_provider_streaming',
        'src.ui.widgets.chart_mixins',
        'src.common.event_bus',
        'urllib3',
        'websockets',
        'websockets.client',
        'websockets.protocol',
        'aiohttp',
        'qasync',
        'qasync._QEventLoop',
        'qasync._windows',
    ]

    for logger_name in stream_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(f"Console debug level applied: {level_str}")


async def main(app: QApplication | None = None, splash: QWidget | None = None):
    """Main application entry point."""
    _hide_console_window()

    # CRITICAL: Set Qt.AA_ShareOpenGLContexts BEFORE creating QApplication
    # This is required for QtWebEngineWidgets to work properly
    if not QApplication.instance():
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    if not app:
        app = QApplication(sys.argv)
    
    app.setApplicationName("OrderPilot-AI")
    app.setOrganizationName("OrderPilot")
    app.setStyle("Fusion")
    # Issue #29: Set application icon globally (candlestick chart, white)
    app.setWindowIcon(get_app_icon())

    if not splash:
        from .splash_screen import SplashScreen
        startup_icon_path = _get_startup_icon_path()
        splash = SplashScreen(startup_icon_path)
        splash.show()
        splash.set_progress(10, "Initialisiere Log-System...")

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    stdout_stream = LogStream(mirror=original_stdout)
    stderr_stream = LogStream(mirror=original_stderr)
    # LogStream still redirects output, but we don't display it in SplashScreen
    sys.stdout = stdout_stream
    sys.stderr = stderr_stream

    if splash: splash.set_progress(20, "Konfiguriere Logging-Module...")
    configure_logging()
    logger.info("Starting OrderPilot-AI Trading Application")

    # Load and apply saved console debug level from QSettings
    if splash: splash.set_progress(30, "Lade Benutzereinstellungen...")
    settings = QSettings("OrderPilot", "TradingApp")
    saved_level = settings.value("console_debug_level", "INFO")
    _apply_saved_debug_level(saved_level)

    root_logger = logging.getLogger()
    root_logger.addHandler(ConsoleOnErrorHandler())

    def _excepthook(exc_type, exc_value, exc_tb):
        _show_console_window()
        traceback.print_exception(exc_type, exc_value, exc_tb)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    if splash: splash.set_progress(50, "Erstelle Hauptfenster...")
    window = TradingApplication(splash=splash)
    
    if splash:
        splash.set_progress(100, "Startbereit")
        # Wait at least 1.5 seconds as requested by user
        await asyncio.sleep(1.5)
        splash.close()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
