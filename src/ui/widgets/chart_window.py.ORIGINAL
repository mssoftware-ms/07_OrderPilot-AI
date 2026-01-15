"""Popup Chart Window for OrderPilot-AI (Refactored).

Refactored from 706 LOC monolith using composition pattern.

Main Window (Module 6/6).

Delegates to 5 specialized helper modules:
- ChartWindowSetup: Initialization and setup methods
- ChartWindowDockControl: Dock minimize/maximize/reset
- ChartWindowHandlers: Event handlers for buttons
- ChartWindowLifecycle: Close event handling and cleanup
- DockTitleBar: Custom title bar widget (imported)

Provides:
- ChartWindow: Main window class with delegation
- Re-exports helper classes for backward compatibility
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QCloseEvent

from .chart_window_setup import ChartWindowSetup
from .chart_window_dock_control import ChartWindowDockControl
from .chart_window_handlers import ChartWindowHandlers
from .chart_window_lifecycle import ChartWindowLifecycle
from .chart_window_dock_titlebar import DockTitleBar
from .chart_window_mixins import (
    PanelsMixin,
    EventBusMixin,
    StateMixin,
    BotPanelsMixin,
    KOFinderMixin,
    StrategySimulatorMixin,
    LevelsContextMixin,
)
from src.chart_chat import ChartChatMixin
from src.ui.widgets.bitunix_trading import BitunixTradingMixin

logger = logging.getLogger(__name__)


class ChartWindow(
    BotPanelsMixin,
    KOFinderMixin,
    StrategySimulatorMixin,
    LevelsContextMixin,
    PanelsMixin,
    EventBusMixin,
    StateMixin,
    ChartChatMixin,
    BitunixTradingMixin,
    QMainWindow
):
    """Popup window for displaying a single chart."""

    # Signals
    window_closed = pyqtSignal(str)

    def __init__(self, symbol: str, history_manager=None, parent=None):
        """Initialize chart window.

        Args:
            symbol: Trading symbol to display
            history_manager: HistoryManager instance for loading data
            parent: Parent widget
        """
        super().__init__(parent)

        self.symbol = symbol
        self.history_manager = history_manager
        self.settings = QSettings("OrderPilot", "TradingApp")
        self._chart_resize_pending = False
        self._ai_analysis_window = None
        self._ready_to_close = False

        # Instantiate helper modules (composition pattern)
        self._setup = ChartWindowSetup(parent=self)
        self._dock_control = ChartWindowDockControl(parent=self)
        self._handlers = ChartWindowHandlers(parent=self)
        self._lifecycle = ChartWindowLifecycle(parent=self)

        # Setup sequence (delegates to helpers)
        self._setup.setup_window()
        self._setup.setup_chart_widget()
        self._setup.setup_dock()
        self._load_window_state()
        self._setup.restore_after_state_load()
        self._setup.setup_shortcuts()
        self._update_toggle_button_text()
        self._setup.connect_dock_signals()
        self._setup_event_subscriptions()
        self._setup.setup_chat()
        self._setup.setup_bitunix_trading()
        self._setup.setup_ai_analysis()
        self._setup_levels_and_context()  # Phase 5.5
        self._setup.connect_data_loaded_signals()

        logger.info(f"ChartWindow created for {symbol}")

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event with async state saving.

        Delegates to ChartWindowLifecycle.handle_close_event().
        """
        self._lifecycle.handle_close_event(event)

    async def load_chart(self, data_provider: Optional[str] = None):
        """Load chart data for the symbol.

        Delegates to ChartWindowLifecycle.load_chart().

        Args:
            data_provider: Optional data provider to use
        """
        await self._lifecycle.load_chart(data_provider)


# Re-export für backward compatibility
__all__ = [
    "ChartWindow",
    "ChartWindowSetup",
    "ChartWindowDockControl",
    "ChartWindowHandlers",
    "ChartWindowLifecycle",
    "DockTitleBar",
]
