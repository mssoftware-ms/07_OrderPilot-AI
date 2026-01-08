"""Popup Chart Window for OrderPilot-AI.

Provides a dedicated window for viewing charts with full screen support.
Can be detached from the main application for multi-monitor setups.

REFACTORED: Extracted mixins to meet 600 LOC limit.
- PanelsMixin: Tab creation (Bot tabs only)
- EventBusMixin: Event bus integration for live markers
- StateMixin: State save/restore functionality
- BotPanelsMixin: Trading bot control and signals
"""

import json
import logging
from typing import Optional

from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QHBoxLayout,
    QLabel, QToolButton, QSizePolicy
)
from PyQt6.QtGui import QCloseEvent, QShortcut, QKeySequence

from .embedded_tradingview_chart import EmbeddedTradingViewChart
from .chart_window_mixins import (
    PanelsMixin,
    EventBusMixin,
    StateMixin,
    BotPanelsMixin,
    KOFinderMixin,
    StrategySimulatorMixin,
)
from src.chart_chat import ChartChatMixin
from src.ui.widgets.bitunix_trading import BitunixTradingMixin
from src.ui.ai_analysis_window import AIAnalysisWindow

logger = logging.getLogger(__name__)


class DockTitleBar(QWidget):
    """Custom title bar for dock widget with minimize/maximize buttons."""

    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    reset_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    help_clicked = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_maximized = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Title label
        self.title_label = QLabel(title)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.title_label)

        # Help button (blue circle with ?)
        self.help_btn = QToolButton()
        self.help_btn.setObjectName("helpButton")
        self.help_btn.setText("?")
        self.help_btn.setToolTip("Hilfe zu Trailing Stop & Exit-Strategien (F1)")
        self.help_btn.setFixedSize(24, 24)
        self.help_btn.clicked.connect(self.help_clicked.emit)
        layout.addWidget(self.help_btn)

        # Reset button
        self.reset_btn = QToolButton()
        self.reset_btn.setText("⊞")
        self.reset_btn.setToolTip("Layout zurücksetzen (Strg+R)")
        self.reset_btn.setFixedSize(24, 24)
        self.reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self.reset_btn)

        # Minimize button
        self.minimize_btn = QToolButton()
        self.minimize_btn.setText("−")
        self.minimize_btn.setToolTip("Minimieren")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.minimize_btn)

        # Maximize/Restore button
        self.maximize_btn = QToolButton()
        self.maximize_btn.setText("□")
        self.maximize_btn.setToolTip("Maximieren")
        self.maximize_btn.setFixedSize(24, 24)
        self.maximize_btn.clicked.connect(self._on_maximize_clicked)
        layout.addWidget(self.maximize_btn)

        # Close button
        self.close_btn = QToolButton()
        self.close_btn.setText("×")
        self.close_btn.setToolTip("Schließen")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)

        self.setStyleSheet("""
            DockTitleBar {
                background: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: bold;
                padding-left: 4px;
            }
            QToolButton {
                background: transparent;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: #3d3d3d;
                border-radius: 2px;
            }
            QToolButton:pressed {
                background: #4d4d4d;
            }
            QToolButton#helpButton {
                background: #2196f3;
                border-radius: 12px;
                color: white;
            }
            QToolButton#helpButton:hover {
                background: #1976d2;
            }
        """)

    def _on_maximize_clicked(self):
        self._is_maximized = not self._is_maximized
        if self._is_maximized:
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("Wiederherstellen")
        else:
            self.maximize_btn.setText("□")
            self.maximize_btn.setToolTip("Maximieren")
        self.maximize_clicked.emit()

    def set_maximized(self, maximized: bool):
        """Update button state without emitting signal."""
        self._is_maximized = maximized
        if maximized:
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("Wiederherstellen")
        else:
            self.maximize_btn.setText("□")
            self.maximize_btn.setToolTip("Maximieren")


class ChartWindow(
    BotPanelsMixin,
    KOFinderMixin,
    StrategySimulatorMixin,
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

        self._setup_window()
        self._setup_chart_widget()
        self._setup_dock()
        self._load_window_state()
        self._restore_after_state_load()
        self._setup_shortcuts()
        self._update_toggle_button_text()
        self._connect_dock_signals()
        self._setup_event_subscriptions()
        self._setup_chat()
        self._setup_bitunix_trading()
        self._setup_ai_analysis()
        self._setup_levels_and_context()  # Phase 5.5
        self._ready_to_close = False
        self._connect_data_loaded_signals()

        logger.info(f"ChartWindow created for {symbol}")

    def _setup_window(self) -> None:
        self.setWindowTitle(f"Chart - {self.symbol}")
        # Fenster als vollwertiges Fenster mit Minimize/Maximize/Close (kein Tool Window)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(700, 450)  # Kompakter (war 800x600)

    def _setup_chart_widget(self) -> None:
        self.chart_widget = EmbeddedTradingViewChart(history_manager=self.history_manager)
        if isinstance(self.chart_widget, QWidget):
            self.setCentralWidget(self.chart_widget)
        else:
            self.setCentralWidget(QWidget())

        self.chart_widget.current_symbol = self.symbol
        if hasattr(self.chart_widget, 'symbol_combo'):
            self.chart_widget.symbol_combo.setCurrentText(self.symbol)

    def _setup_dock(self) -> None:
        self.dock_widget = QDockWidget("Analysis & Strategy", self)
        self.dock_widget.setObjectName("analysisDock")
        self.dock_widget.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        self._dock_title_bar = DockTitleBar("Analysis & Strategy")
        self._dock_title_bar.minimize_clicked.connect(self._minimize_dock)
        self._dock_title_bar.maximize_clicked.connect(self._toggle_dock_maximized)
        self._dock_title_bar.reset_clicked.connect(self._reset_layout)
        self._dock_title_bar.close_clicked.connect(self.dock_widget.close)
        self._dock_title_bar.help_clicked.connect(self._open_trailing_stop_help)
        self.dock_widget.setTitleBarWidget(self._dock_title_bar)

        self._dock_maximized = False
        self._dock_minimized = False
        self._saved_dock_height = 200

        self.bottom_panel = self._create_bottom_panel()
        self.dock_widget.setWidget(self.bottom_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_widget)

        if hasattr(self.chart_widget, 'toggle_panel_button'):
            self.chart_widget.toggle_panel_button.clicked.connect(self._toggle_bottom_panel)
            self.chart_widget.toggle_panel_button.setChecked(self.dock_widget.isVisible())

    def _restore_after_state_load(self) -> None:
        self.chart_widget.setVisible(True)
        self._dock_maximized = False
        self._dock_minimized = False
        self._dock_title_bar.set_maximized(False)

    def _setup_shortcuts(self) -> None:
        self._reset_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self._reset_shortcut.activated.connect(self._reset_layout)

        self._help_shortcut = QShortcut(QKeySequence("F1"), self)
        self._help_shortcut.activated.connect(self._open_trailing_stop_help)

        self._chat_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self._chat_shortcut.activated.connect(self.toggle_chat_widget)

        self._analysis_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        self._analysis_shortcut.activated.connect(self.request_chart_analysis)

    def _connect_dock_signals(self) -> None:
        self.dock_widget.visibilityChanged.connect(self._on_dock_visibility_changed)

    def _setup_chat(self) -> None:
        self.setup_chart_chat(self.chart_widget)
        if hasattr(self.chart_widget, 'ai_chat_button'):
            self.chart_widget.ai_chat_button.clicked.connect(
                self._on_ai_chat_button_clicked
            )
        if getattr(self, "_chat_widget", None):
            self._chat_widget.visibilityChanged.connect(self._on_chat_visibility_changed)
            self._chat_widget.topLevelChanged.connect(self._on_chat_top_level_changed)
            self._chat_widget.dockLocationChanged.connect(self._on_chat_dock_location_changed)

    def _setup_bitunix_trading(self) -> None:
        """Set up Bitunix trading widget integration."""
        self.setup_bitunix_trading(self.chart_widget)
        if hasattr(self.chart_widget, 'bitunix_trading_button'):
            self.chart_widget.bitunix_trading_button.clicked.connect(
                self._on_bitunix_trading_button_clicked
            )
        if getattr(self, "_bitunix_widget", None):
            self._bitunix_widget.visibilityChanged.connect(self._on_bitunix_visibility_changed)

    def _setup_ai_analysis(self) -> None:
        """Setup the AI Analysis Popup."""
        if hasattr(self.chart_widget, 'ai_analysis_button'):
            self.chart_widget.ai_analysis_button.clicked.connect(
                self._on_ai_analysis_button_clicked
            )

    def _on_ai_analysis_button_clicked(self, checked: bool) -> None:
        """Open or focus the AI Analysis Popup."""
        if checked:
            if not self._ai_analysis_window:
                self._ai_analysis_window = AIAnalysisWindow(self, symbol=self.symbol)
                self._ai_analysis_window.finished.connect(self._on_analysis_window_closed)
            
            self._ai_analysis_window.show()
            self._ai_analysis_window.raise_()
            self._ai_analysis_window.activateWindow()
        else:
            if self._ai_analysis_window:
                self._ai_analysis_window.hide()

    def _on_analysis_window_closed(self, result: int) -> None:
        """Handle analysis window close event to uncheck the button."""
        self._ai_analysis_window = None
        if hasattr(self.chart_widget, 'ai_analysis_button'):
            self.chart_widget.ai_analysis_button.setChecked(False)

    def _ensure_chat_docked_right(self) -> None:
        """Dock the chat widget to the right if it is not floating."""
        if not getattr(self, "_chat_widget", None):
            return
        if self._chat_widget.isFloating():
            return
        try:
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._chat_widget)
        except Exception as e:
            logger.debug("Failed to dock chat widget: %s", e)

    def _sync_ai_chat_button_state(self) -> None:
        """Ensure the toolbar toggle reflects the dock visibility."""
        if hasattr(self.chart_widget, 'ai_chat_button') and getattr(self, "_chat_widget", None):
            self.chart_widget.ai_chat_button.setChecked(self._chat_widget.isVisible())

    def _schedule_chart_resize(self, delay_ms: int = 120) -> None:
        """Throttle resize requests after dock/undock/visibility changes."""
        if self._chart_resize_pending:
            return
        self._chart_resize_pending = True

        def _do_resize():
            self._chart_resize_pending = False
            try:
                if hasattr(self.chart_widget, "request_chart_resize"):
                    self.chart_widget.request_chart_resize()
            except Exception as e:
                logger.debug("Chart resize after chat change failed: %s", e)

        QTimer.singleShot(delay_ms, _do_resize)

    def _on_chat_visibility_changed(self, visible: bool) -> None:
        if visible:
            self._ensure_chat_docked_right()
        self._sync_ai_chat_button_state()
        self._schedule_chart_resize()

    def _on_chat_top_level_changed(self, floating: bool) -> None:
        # Floating=True means detached; resize ensures chart reclaims full width
        self._schedule_chart_resize()

    def _on_chat_dock_location_changed(self, _area) -> None:
        self._schedule_chart_resize()

    def _connect_data_loaded_signals(self) -> None:
        self.chart_widget.data_loaded.connect(self._restore_chart_state)
        self.chart_widget.data_loaded.connect(self._restore_indicators_after_data_load)
        self.chart_widget.data_loaded.connect(self._activate_live_stream)

    def _activate_live_stream(self):
        """Activate live streaming when chart data is loaded."""
        if hasattr(self.chart_widget, 'live_stream_button'):
            live_data_enabled = self.settings.value("live_data_enabled", False, type=bool)
            if not live_data_enabled:
                logger.info("Live data disabled - skipping auto-activate stream")
                if self.chart_widget.live_stream_button.isChecked():
                    self.chart_widget.live_stream_button.setChecked(False)
                return
            # Only activate if not already streaming
            if not self.chart_widget.live_stream_button.isChecked():
                logger.info(f"Auto-activating live stream for {self.symbol}")
                # click() toggles checked state and triggers the connected slot
                self.chart_widget.live_stream_button.click()

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event with async state saving."""
        self._cleanup_simulation_on_close()

        if not isinstance(self.chart_widget, QWidget):
            self._ready_to_close = True
            event.accept()
            return

        if self._ready_to_close:
            self._finalize_close(event)
            return

        self._request_close_state(event)

    def _cleanup_simulation_on_close(self) -> None:
        if not hasattr(self, "_cleanup_simulation_worker"):
            return
        try:
            self._cleanup_simulation_worker(cancel=True, wait_ms=500)
        except Exception as e:
            logger.debug("Failed to stop simulation worker during close: %s", e)

    def _finalize_close(self, event: QCloseEvent) -> None:
        logger.info(f"Closing ChartWindow for {self.symbol}...")
        self._stop_live_stream_on_close()
        self._unsubscribe_events()
        self._save_optional_state()
        self._save_window_state()
        self._cleanup_chat()
        self._cleanup_bitunix_trading()
        self.window_closed.emit(self.symbol)
        event.accept()

    def _stop_live_stream_on_close(self) -> None:
        if not (hasattr(self.chart_widget, 'live_streaming_enabled') and self.chart_widget.live_streaming_enabled):
            return
        try:
            self.chart_widget.live_streaming_enabled = False
            if hasattr(self.chart_widget, 'live_stream_button'):
                self.chart_widget.live_stream_button.setChecked(False)
            if hasattr(self.chart_widget, '_stop_live_stream_async'):
                import asyncio
                asyncio.ensure_future(self.chart_widget._stop_live_stream_async())
                logger.info(f"Disconnecting live stream for {self.symbol}")
        except Exception as e:
            logger.debug(f"Error stopping live stream: {e}")

    def _save_optional_state(self) -> None:
        if hasattr(self, '_save_signal_history'):
            try:
                self._save_signal_history()
            except Exception as e:
                logger.debug(f"Error saving signal history: {e}")

        if hasattr(self, '_save_simulator_splitter_state'):
            try:
                self._save_simulator_splitter_state()
            except Exception as e:
                logger.debug(f"Error saving simulator splitter state: {e}")

    def _cleanup_chat(self) -> None:
        if hasattr(self, 'cleanup_chart_chat'):
            try:
                self.cleanup_chart_chat()
            except Exception as e:
                logger.debug(f"Error cleaning up chart chat: {e}")

    def _cleanup_bitunix_trading(self) -> None:
        """Clean up Bitunix trading resources."""
        if hasattr(self, 'cleanup_bitunix_trading'):
            try:
                self.cleanup_bitunix_trading()
            except Exception as e:
                logger.debug(f"Error cleaning up Bitunix trading: {e}")

    def _request_close_state(self, event: QCloseEvent) -> None:
        logger.info(f"Requesting chart state before closing {self.symbol}...")
        event.ignore()

        def on_complete_state_received(complete_state):
            try:
                if complete_state and complete_state.get('version'):
                    settings_key = self._get_settings_key()
                    self.settings.setValue(f"{settings_key}/chartState", json.dumps(complete_state))
                    logger.info(f"Saved complete chart state for {self.symbol}")
                else:
                    _save_individual_components()
                    return
            except Exception as e:
                logger.error(f"Error saving complete chart state: {e}")
                _save_individual_components()
                return

            self._ready_to_close = True
            QTimer.singleShot(0, self.close)

        def on_range_received(visible_range):
            try:
                if visible_range:
                    settings_key = self._get_settings_key()
                    self.settings.setValue(f"{settings_key}/visibleRange", json.dumps(visible_range))
                    logger.info(f"Saved visible range for {self.symbol}")
            except Exception as e:
                logger.error(f"Error saving visible range: {e}")

            self._ready_to_close = True
            QTimer.singleShot(0, self.close)

        def _save_individual_components():
            logger.info("Falling back to individual component saving")
            self.chart_widget.get_visible_range(on_range_received)

        def on_layout_received(layout):
            try:
                if layout:
                    settings_key = self._get_settings_key()
                    layout_json = json.dumps(layout)
                    self.settings.setValue(f"{settings_key}/paneLayout", layout_json)
                    logger.info(f"Saved pane layout for {self.symbol}")
            except Exception as e:
                logger.error(f"Error saving pane layout: {e}")

            try:
                self.chart_widget.get_chart_state(on_complete_state_received)
            except Exception as e:
                logger.warning(f"Comprehensive state saving failed: {e}")
                _save_individual_components()

        def force_close():
            if not self._ready_to_close:
                logger.warning("Chart state fetch timed out, forcing close")
                self._ready_to_close = True
                self.close()

        QTimer.singleShot(2000, force_close)
        self.chart_widget.get_pane_layout(on_layout_received)

    async def load_chart(self, data_provider: Optional[str] = None):
        """Load chart data for the symbol.

        Args:
            data_provider: Optional data provider to use
        """
        try:
            logger.info(f"Loading chart for {self.symbol} in popup window")
            await self.chart_widget.load_symbol(self.symbol, data_provider)
        except Exception as e:
            logger.error(f"Error loading chart in popup window: {e}", exc_info=True)

    def _minimize_dock(self):
        """Minimize the dock widget to show only the title bar."""
        if self._dock_minimized:
            # Restore from minimized state
            self._dock_minimized = False
            self.bottom_panel.setVisible(True)
            self.bottom_panel.setMaximumHeight(16777215)
            self.bottom_panel.setMinimumHeight(self._saved_dock_height)
            QTimer.singleShot(10, lambda: self.bottom_panel.setMinimumHeight(0))
            logger.debug("Dock restored from minimized state")
        else:
            # Minimize
            self._dock_minimized = True
            self._saved_dock_height = max(self.bottom_panel.height(), 120)  # Minimum height
            self.bottom_panel.setVisible(False)
            logger.debug("Dock minimized")

    def _toggle_dock_maximized(self):
        """Toggle dock widget between maximized and normal state.

        When dock is floating (undocked), maximize on the screen where the
        dock is currently visible, not where the parent window is.
        """
        if self._dock_maximized:
            # Restore from maximized state
            self._dock_maximized = False
            if self.dock_widget.isFloating():
                # Restore floating dock to saved geometry
                if hasattr(self, '_saved_floating_geometry'):
                    self.dock_widget.setGeometry(self._saved_floating_geometry)
            else:
                self.chart_widget.setVisible(True)
                self.bottom_panel.setMaximumHeight(16777215)
                self.bottom_panel.setMinimumHeight(0)
            logger.debug("Dock restored from maximized state")
        else:
            # Maximize
            self._dock_maximized = True
            self._dock_minimized = False

            if self.dock_widget.isFloating():
                # Save current geometry before maximizing
                self._saved_floating_geometry = self.dock_widget.geometry()

                # Get the screen where the dock widget is currently shown
                from PyQt6.QtGui import QGuiApplication
                dock_center = self.dock_widget.geometry().center()
                current_screen = None
                for screen in QGuiApplication.screens():
                    if screen.geometry().contains(dock_center):
                        current_screen = screen
                        break

                if current_screen is None:
                    current_screen = self.dock_widget.screen()

                # Maximize on the dock's current screen
                screen_geom = current_screen.availableGeometry()
                self.dock_widget.setGeometry(screen_geom)
                logger.debug(f"Dock maximized on screen: {current_screen.name()}")
            else:
                # Docked mode: hide chart and expand dock
                self.bottom_panel.setVisible(True)
                self.chart_widget.setVisible(False)
                logger.debug("Dock maximized (docked mode)")

    def _reset_layout(self):
        """Reset window layout to default state.

        Restores chart visibility, dock position, and clears any
        maximized/minimized state. Use this if the window gets into
        a broken state.
        """
        logger.info("Resetting window layout to defaults")

        # Reset state flags
        self._dock_maximized = False
        self._dock_minimized = False
        self._dock_title_bar.set_maximized(False)

        # Ensure chart is visible
        self.chart_widget.setVisible(True)

        # Ensure dock panel is visible and properly sized
        self.bottom_panel.setVisible(True)
        self.bottom_panel.setMaximumHeight(16777215)
        self.bottom_panel.setMinimumHeight(0)

        # Show dock widget
        self.dock_widget.setVisible(True)
        self.dock_widget.setFloating(False)

        # Re-dock to bottom
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_widget)

        # Reset window size if too small
        if self.width() < 700 or self.height() < 450:
            self.resize(1000, 600)  # Kompakter (-100px Höhe)
            # Center on screen
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

        logger.info("Window layout reset complete")

    def _open_trailing_stop_help(self):
        """Open the trailing stop help documentation in browser."""
        import webbrowser
        from pathlib import Path

        try:
            # Find project root and help file
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent
            help_file = project_root / "Help" / "trailing-stop-hilfe.html"

            if help_file.exists():
                webbrowser.open(help_file.as_uri())
                logger.info(f"Opened help file: {help_file}")
            else:
                logger.warning(f"Help file not found: {help_file}")
        except Exception as e:
            logger.error(f"Error opening help file: {e}")

    def _on_ai_chat_button_clicked(self, checked: bool):
        """Handle AI Chat toolbar button click.

        Args:
            checked: Button checked state
        """
        if checked:
            self.show_chat_widget()
            self._ensure_chat_docked_right()
        else:
            self.hide_chat_widget()

        self._sync_ai_chat_button_state()

    def _on_bitunix_trading_button_clicked(self, checked: bool):
        """Handle Bitunix Trading toolbar button click.

        Args:
            checked: Button checked state
        """
        if checked:
            self.show_bitunix_widget()
        else:
            self.hide_bitunix_widget()

        self._sync_bitunix_trading_button_state()

    def _sync_bitunix_trading_button_state(self) -> None:
        """Ensure the toolbar toggle reflects the Bitunix widget visibility."""
        if hasattr(self.chart_widget, 'bitunix_trading_button') and getattr(self, "_bitunix_widget", None):
            self.chart_widget.bitunix_trading_button.setChecked(self._bitunix_widget.isVisible())

    def _on_bitunix_visibility_changed(self, visible: bool) -> None:
        """Handle Bitunix widget visibility change."""
        self._sync_bitunix_trading_button_state()
        self._schedule_chart_resize()

    # =========================================================================
    # PHASE 5.5: LEVELS & CONTEXT TOOLBAR VERDRAHTUNG
    # =========================================================================

    def _setup_levels_and_context(self) -> None:
        """Setup levels and context toolbar button connections (Phase 5.5)."""
        # Initialize context cache
        self._market_context = None
        self._context_inspector = None

        # Connect levels button
        if hasattr(self.chart_widget, 'levels_button'):
            self.chart_widget.levels_button.clicked.connect(self._on_levels_button_clicked)

        # Connect level signals
        if hasattr(self.chart_widget, 'levels_detect_requested'):
            self.chart_widget.levels_detect_requested.connect(self._on_detect_levels)
        if hasattr(self.chart_widget, 'level_type_toggled'):
            self.chart_widget.level_type_toggled.connect(self._on_level_type_toggled)
        # Phase 5.7: Connect level target suggestion signal
        if hasattr(self.chart_widget, 'level_target_suggested'):
            self.chart_widget.level_target_suggested.connect(self._on_level_target_suggested)

        # Connect context signals
        if hasattr(self.chart_widget, 'context_inspector_requested'):
            self.chart_widget.context_inspector_requested.connect(self._on_open_context_inspector)
        if hasattr(self.chart_widget, 'context_copy_json_requested'):
            self.chart_widget.context_copy_json_requested.connect(self._on_copy_context_json)
        if hasattr(self.chart_widget, 'context_copy_prompt_requested'):
            self.chart_widget.context_copy_prompt_requested.connect(self._on_copy_context_prompt)
        if hasattr(self.chart_widget, 'context_export_file_requested'):
            self.chart_widget.context_export_file_requested.connect(self._on_export_context_file)
        if hasattr(self.chart_widget, 'context_refresh_requested'):
            self.chart_widget.context_refresh_requested.connect(self._on_refresh_context)

        logger.debug("Levels and context toolbar buttons connected")

    def _on_levels_button_clicked(self, checked: bool) -> None:
        """Handle levels button toggle."""
        if checked:
            # Auto-detect levels on first activation
            self._on_detect_levels()
        else:
            # Hide levels
            if hasattr(self.chart_widget, 'clear_zones'):
                self.chart_widget.clear_zones()

        logger.debug(f"Levels button toggled: {checked}")

    def _on_detect_levels(self) -> None:
        """Detect and render levels on chart."""
        try:
            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None:
                logger.warning("No chart data available for level detection")
                return

            # Use LevelZonesMixin if available
            if hasattr(self.chart_widget, 'detect_and_render_levels'):
                df = self.chart_widget.data
                symbol = getattr(self.chart_widget, 'current_symbol', 'UNKNOWN')
                timeframe = getattr(self.chart_widget, 'current_timeframe', '5m')
                current_price = df['close'].iloc[-1] if len(df) > 0 else None

                self.chart_widget.detect_and_render_levels(
                    df=df,
                    symbol=symbol,
                    timeframe=timeframe,
                    current_price=current_price,
                )
                logger.info(f"Levels detected and rendered for {symbol}")

                # Update button state
                if hasattr(self.chart_widget, 'levels_button'):
                    self.chart_widget.levels_button.setChecked(True)
            else:
                logger.warning("detect_and_render_levels not available on chart widget")

        except Exception as e:
            logger.error(f"Level detection failed: {e}", exc_info=True)

    def _on_level_type_toggled(self, level_type: str, checked: bool) -> None:
        """Handle level type toggle from dropdown menu."""
        logger.debug(f"Level type {level_type} toggled: {checked}")
        # Re-render levels with updated filters
        self._on_detect_levels()

    def _get_or_build_context(self):
        """Get current MarketContext or build a new one."""
        try:
            from src.core.trading_bot.market_context_builder import MarketContextBuilder

            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None:
                logger.warning("No chart data for context")
                return None

            builder = MarketContextBuilder()
            symbol = getattr(self.chart_widget, 'current_symbol', 'UNKNOWN')
            timeframe = getattr(self.chart_widget, 'current_timeframe', '5m')

            context = builder.build(
                symbol=symbol,
                timeframe=timeframe,
                df=self.chart_widget.data,
            )
            self._market_context = context
            return context

        except ImportError as e:
            logger.warning(f"MarketContextBuilder not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Context building failed: {e}", exc_info=True)
            return None

    def _on_open_context_inspector(self) -> None:
        """Open MarketContext Inspector dialog."""
        try:
            from src.ui.dialogs.market_context_inspector import MarketContextInspector

            context = self._get_or_build_context()

            if self._context_inspector is None or not self._context_inspector.isVisible():
                self._context_inspector = MarketContextInspector(
                    context=context,
                    refresh_callback=self._get_or_build_context,
                    parent=self,
                )
                self._context_inspector.show()
            else:
                # Update existing inspector
                if context and hasattr(self._context_inspector, '_update_display'):
                    self._context_inspector._update_display(context)
                self._context_inspector.raise_()
                self._context_inspector.activateWindow()

            logger.info("Context inspector opened")

        except ImportError as e:
            logger.warning(f"MarketContextInspector not available: {e}")
        except Exception as e:
            logger.error(f"Failed to open context inspector: {e}", exc_info=True)

    def _on_copy_context_json(self) -> None:
        """Copy MarketContext as JSON to clipboard."""
        try:
            from PyQt6.QtWidgets import QApplication

            context = self._get_or_build_context()
            if context is None:
                logger.warning("No context available to copy")
                return

            # Convert to dict and then JSON
            if hasattr(context, 'to_dict'):
                context_dict = context.to_dict()
            else:
                context_dict = {"error": "Context does not support to_dict()"}

            json_str = json.dumps(context_dict, indent=2, default=str)
            QApplication.clipboard().setText(json_str)
            logger.info("Context JSON copied to clipboard")

        except Exception as e:
            logger.error(f"Failed to copy context JSON: {e}", exc_info=True)

    def _on_copy_context_prompt(self) -> None:
        """Copy MarketContext as AI prompt to clipboard."""
        try:
            from PyQt6.QtWidgets import QApplication

            context = self._get_or_build_context()
            if context is None:
                logger.warning("No context available to copy")
                return

            # Use AI prompt format
            if hasattr(context, 'to_ai_prompt_context'):
                prompt = context.to_ai_prompt_context()
            else:
                prompt = f"MarketContext for {getattr(context, 'symbol', 'UNKNOWN')}"

            QApplication.clipboard().setText(prompt)
            logger.info("Context AI prompt copied to clipboard")

        except Exception as e:
            logger.error(f"Failed to copy context prompt: {e}", exc_info=True)

    def _on_export_context_file(self) -> None:
        """Export MarketContext to JSON file."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            from datetime import datetime

            context = self._get_or_build_context()
            if context is None:
                logger.warning("No context available to export")
                return

            # Generate default filename
            symbol = getattr(context, 'symbol', 'UNKNOWN').replace('/', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"market_context_{symbol}_{timestamp}.json"

            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "MarketContext exportieren",
                default_name,
                "JSON Files (*.json)"
            )

            if filepath:
                if hasattr(context, 'to_dict'):
                    context_dict = context.to_dict()
                else:
                    context_dict = {"error": "Context does not support to_dict()"}

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(context_dict, f, indent=2, default=str)

                logger.info(f"Context exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export context: {e}", exc_info=True)

    def _on_refresh_context(self) -> None:
        """Refresh MarketContext and update inspector if open."""
        try:
            context = self._get_or_build_context()

            # Update inspector if open
            if self._context_inspector and self._context_inspector.isVisible():
                if hasattr(self._context_inspector, '_update_display'):
                    self._context_inspector._update_display(context)

            # Issue #36: Update AI Chat Tab with new context
            if hasattr(self, 'update_ai_chat_context'):
                self.update_ai_chat_context(context)

            logger.info("Context refreshed")

        except Exception as e:
            logger.error(f"Failed to refresh context: {e}", exc_info=True)

    # =========================================================================
    # Phase 5.7: Level Interaction Handlers
    # =========================================================================

    def _on_level_target_suggested(self, target_type: str, price: float) -> None:
        """Handle level target suggestion from chart (Set TP/SL/Entry from level click).

        Args:
            target_type: "TP", "SL", or "Entry"
            price: Target price from level
        """
        try:
            logger.info(f"Level target suggested: {target_type} @ {price:.2f}")

            # Try to set in bot control panel if available
            bot_panel = self._find_bot_control_panel()
            if bot_panel:
                self._apply_target_to_bot_panel(bot_panel, target_type, price)
            else:
                # Fallback: show info dialog and copy to clipboard
                self._show_target_suggestion_dialog(target_type, price)

        except Exception as e:
            logger.error(f"Failed to apply level target: {e}", exc_info=True)

    def _find_bot_control_panel(self):
        """Find bot control panel in the current window hierarchy."""
        # Try to find in parent windows
        from PyQt6.QtWidgets import QApplication

        # Look for bot control panel in all windows
        for widget in QApplication.allWidgets():
            widget_name = type(widget).__name__
            if 'BotControlPanel' in widget_name or 'BotTab' in widget_name:
                return widget

        # Check if we have a direct reference
        if hasattr(self, '_bot_control_panel'):
            return self._bot_control_panel

        return None

    def _apply_target_to_bot_panel(self, bot_panel, target_type: str, price: float) -> None:
        """Apply target price to bot control panel fields.

        Args:
            bot_panel: Bot control panel widget
            target_type: "TP", "SL", or "Entry"
            price: Target price
        """
        try:
            # Map target type to field names
            field_map = {
                "TP": ["take_profit_input", "tp_input", "take_profit_price"],
                "SL": ["stop_loss_input", "sl_input", "stop_loss_price"],
                "Entry": ["entry_price_input", "entry_input", "entry_price"],
            }

            field_names = field_map.get(target_type, [])
            applied = False

            for field_name in field_names:
                if hasattr(bot_panel, field_name):
                    field = getattr(bot_panel, field_name)
                    if hasattr(field, 'setValue'):
                        field.setValue(price)
                        applied = True
                        break
                    elif hasattr(field, 'setText'):
                        field.setText(f"{price:.2f}")
                        applied = True
                        break

            if applied:
                logger.info(f"Applied {target_type} = {price:.2f} to bot panel")
                # Show brief notification
                self._show_brief_notification(f"{target_type} auf {price:.2f} gesetzt")
            else:
                # Fallback to dialog
                self._show_target_suggestion_dialog(target_type, price)

        except Exception as e:
            logger.error(f"Failed to apply target to bot panel: {e}")
            self._show_target_suggestion_dialog(target_type, price)

    def _show_target_suggestion_dialog(self, target_type: str, price: float) -> None:
        """Show dialog suggesting to set the target price.

        Args:
            target_type: "TP", "SL", or "Entry"
            price: Target price
        """
        from PyQt6.QtWidgets import QMessageBox, QApplication

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(f"{target_type} Vorschlag")
        msg.setText(f"Level als {target_type} vorgeschlagen:")
        msg.setInformativeText(
            f"Preis: {price:.2f}\n\n"
            "Der Preis wurde in die Zwischenablage kopiert.\n"
            "Fügen Sie ihn manuell in das Bot-Panel ein."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(f"{price:.2f}")

        msg.exec()
        logger.info(f"{target_type} suggestion shown, price copied to clipboard")

    def _show_brief_notification(self, message: str) -> None:
        """Show brief status notification.

        Args:
            message: Message to display
        """
        # Try to use status label if available
        if hasattr(self.chart_widget, 'info_label'):
            self.chart_widget.info_label.setText(message)
        elif hasattr(self, 'statusBar'):
            self.statusBar().showMessage(message, 3000)
