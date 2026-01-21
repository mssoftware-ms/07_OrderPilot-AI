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
    CelEditorMixin,
)
from src.chart_chat import ChartChatMixin
from src.ui.app_icon import set_window_icon  # Issue #29: App icon
from src.ui.widgets.bitunix_trading import BitunixTradingMixin

logger = logging.getLogger(__name__)


class ChartWindow(
    CelEditorMixin,
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

        # Issue #29: Set application icon (candlestick chart, white)
        set_window_icon(self)

        self.symbol = symbol
        self.history_manager = history_manager
        self.settings = QSettings("OrderPilot", "TradingApp")
        self._chart_resize_pending = False
        self._ai_analysis_window = None
        self._ready_to_close = False

        # Show splash screen for chart loading
        from src.ui.app_resources import _get_startup_icon_path
        from src.ui.splash_screen import SplashScreen
        splash = SplashScreen(_get_startup_icon_path(), f"Lade Chart: {symbol}...")
        splash.show()
        splash.set_progress(10, "Initialisiere Chart-Fenster...")

        # Instantiate helper modules (composition pattern)
        self._setup = ChartWindowSetup(parent=self)
        self._dock_control = ChartWindowDockControl(parent=self)
        self._handlers = ChartWindowHandlers(parent=self)
        self._lifecycle = ChartWindowLifecycle(parent=self)

        # Setup sequence (delegates to helpers)
        self._setup.setup_window()
        splash.set_progress(30, "Erstelle Chart-Komponenten...")
        self._setup.setup_chart_widget()
        # self._setup.setup_live_data_toggle()  # Issue #14: LiveData Button entfernt
        splash.set_progress(50, "Baue Dock-System...")
        self._setup.setup_dock()
        
        # Phase 3 + 4: New docks for Workspace Manager pattern
        self._setup.setup_watchlist_dock()
        self._setup.setup_activity_log_dock()
        
        self._load_window_state()
        self._setup.restore_after_state_load()
        self._setup.setup_shortcuts()
        
        # Phase 5: Context Menu
        self._setup_context_menu()
        
        self._update_toggle_button_text()
        self._setup.connect_dock_signals()
        self._setup_event_subscriptions()
        self._setup.setup_chat()
        splash.set_progress(70, "Lade Strategie-Module...")
        self._setup.setup_bitunix_trading()
        self._setup.setup_ai_analysis()
        self._setup_levels_and_context()  # Phase 5.5
        self._setup.connect_data_loaded_signals()
        splash.set_progress(90, "Finalisiere Setup...")
        self._init_cel_editor()  # Phase 7: CEL Editor integration

        logger.info(f"ChartWindow created for {symbol}")
        
        # Finish splash and close with delay to ensure visibility
        splash.finish_and_close(1200)
    
    def _setup_context_menu(self) -> None:
        """Setup context menu for ChartWindow (Phase 5: UI Refactoring).
        
        Provides quick access to Settings, docks, and Workspace Manager
        without needing the main menu bar.
        """
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction, QKeySequence, QShortcut
        
        # Enable context menu on the chart widget
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.chart_widget.customContextMenuRequested.connect(self._show_context_menu)
        
        # Keyboard shortcuts for quick access
        # Ctrl+, for Settings (common pattern)
        self._settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self._settings_shortcut.activated.connect(self._open_settings)
        
        # Ctrl+Shift+W for Workspace Manager
        self._workspace_shortcut = QShortcut(QKeySequence("Ctrl+Shift+W"), self)
        self._workspace_shortcut.activated.connect(self._show_workspace_manager)
    
    def _show_context_menu(self, pos) -> None:
        """Show context menu at position."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        
        # Settings action
        settings_action = QAction("⚙️ Einstellungen (Ctrl+,)", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # Toggle Watchlist
        watchlist_action = QAction("📋 Watchlist anzeigen", self)
        watchlist_action.setCheckable(True)
        if hasattr(self, '_watchlist_dock'):
            watchlist_action.setChecked(self._watchlist_dock.isVisible())
        watchlist_action.triggered.connect(lambda: self._setup.toggle_watchlist_dock())
        menu.addAction(watchlist_action)
        
        # Toggle Activity Log
        activity_log_action = QAction("📜 Activity Log anzeigen", self)
        activity_log_action.setCheckable(True)
        if hasattr(self, '_activity_log_dock'):
            activity_log_action.setChecked(self._activity_log_dock.isVisible())
        activity_log_action.triggered.connect(lambda: self._setup.toggle_activity_log_dock())
        menu.addAction(activity_log_action)
        
        menu.addSeparator()
        
        # Show Workspace Manager
        workspace_action = QAction("🏠 Workspace Manager anzeigen (Ctrl+Shift+W)", self)
        workspace_action.triggered.connect(self._show_workspace_manager)
        menu.addAction(workspace_action)
        
        # Close All Charts
        close_all_action = QAction("❌ Alle Charts schließen", self)
        close_all_action.triggered.connect(self._close_all_charts)
        menu.addAction(close_all_action)
        
        # Show at cursor position
        if hasattr(self, 'chart_widget') and self.chart_widget:
            menu.exec(self.chart_widget.mapToGlobal(pos))
    
    def _open_settings(self) -> None:
        """Open settings dialog."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'show_settings_dialog'):
            main_window.show_settings_dialog()
        else:
            logger.warning("Settings dialog not available")
    
    def _show_workspace_manager(self) -> None:
        """Show and focus the Workspace Manager (main window)."""
        main_window = self._get_main_window()
        if main_window:
            main_window.show()
            main_window.raise_()
            main_window.activateWindow()
        else:
            logger.warning("Workspace Manager not found")
    
    def _close_all_charts(self) -> None:
        """Close all chart windows."""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'chart_window_manager'):
            main_window.chart_window_manager.close_all()
        else:
            logger.warning("chart_window_manager not found")


    def _get_main_window(self) -> Optional[QMainWindow]:
        """Return the main window if available."""
        main_window = self.parent()
        if main_window and hasattr(main_window, "toggle_live_data"):
            return main_window
        return None

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
