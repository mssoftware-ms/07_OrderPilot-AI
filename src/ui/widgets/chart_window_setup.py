"""Chart Window Setup - Initialization and setup methods.

Refactored from 706 LOC monolith using composition pattern.

Module 2/6 of chart_window.py split.

Contains:
- setup_window(): Window configuration
- setup_chart_widget(): Central chart widget setup
- setup_dock(): Dock widget with custom title bar
- setup_shortcuts(): Keyboard shortcuts (Ctrl+R, F1, Ctrl+Shift+C, Ctrl+Shift+A, Ctrl+Shift+S)
- setup_chat(): Chart chat integration
- setup_bitunix_trading(): Bitunix trading widget
- setup_ai_analysis(): AI analysis popup
- Helper methods for dock and chat

Note: setup_live_data_toggle() removed as per Issue #14
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDockWidget, QWidget, QPushButton
from PyQt6.QtGui import QShortcut, QKeySequence

from src.ui.widgets.chart_window_dock_titlebar import DockTitleBar
from src.ui.widgets.trading_bot_window import TradingBotWindow

logger = logging.getLogger(__name__)


class ChartWindowSetup:
    """Helper für ChartWindow Setup und Initialization."""

    def __init__(self, parent):
        """
        Args:
            parent: ChartWindow Instanz
        """
        self.parent = parent

    def setup_window(self) -> None:
        """Configure main window properties."""
        self.parent.setWindowTitle(f"Chart - {self.parent.symbol}")
        # Fenster als vollwertiges Fenster mit Minimize/Maximize/Close (kein Tool Window)
        self.parent.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.parent.setMinimumSize(700, 450)  # Kompakter (war 800x600)

    def setup_chart_widget(self) -> None:
        """Setup central chart widget."""
        from .embedded_tradingview_chart import EmbeddedTradingViewChart

        self.parent.chart_widget = EmbeddedTradingViewChart(history_manager=self.parent.history_manager)
        if isinstance(self.parent.chart_widget, QWidget):
            self.parent.setCentralWidget(self.parent.chart_widget)
        else:
            self.parent.setCentralWidget(QWidget())

        self.parent.chart_widget.current_symbol = self.parent.symbol
        if hasattr(self.parent.chart_widget, 'symbol_combo'):
            self.parent.chart_widget.symbol_combo.setCurrentText(self.parent.symbol)

    def setup_dock(self) -> None:
        """Setup Trading Bot window (standalone window, not a dock).

        Creates a TradingBotWindow that can be toggled via the "Trading Bot" button.
        The window saves and restores its position independently.
        """
        # Create the panel content (same as before)
        self.parent.bottom_panel = self.parent._create_bottom_panel()

        # Create standalone TradingBotWindow instead of QDockWidget
        self.parent._trading_bot_window = TradingBotWindow(
            parent_chart=self.parent,
            panel_content=self.parent.bottom_panel
        )

        # Connect window signals
        self.parent._trading_bot_window.window_closed.connect(self._on_trading_bot_window_closed)
        self.parent._trading_bot_window.visibility_changed.connect(
            self.parent._handlers.on_dock_visibility_changed
        )

        # Legacy compatibility: also set dock_widget reference (some code might still use it)
        # But point it to None to avoid confusion - use _trading_bot_window instead
        self.parent.dock_widget = None
        self.parent._dock_title_bar = None
        self.parent._dock_maximized = False
        self.parent._dock_minimized = False
        self.parent._saved_dock_height = 200

        # Connect toggle button
        if hasattr(self.parent.chart_widget, 'toggle_panel_button'):
            self.parent.chart_widget.toggle_panel_button.clicked.connect(self.parent._toggle_bottom_panel)

            # Restore visibility from previous session
            if getattr(self.parent._trading_bot_window, '_restore_visibility', False):
                self.parent.chart_widget.toggle_panel_button.setChecked(True)
                self.parent._trading_bot_window.show()
                logger.info(f"TradingBotWindow restored visible for {self.parent.symbol}")
            else:
                # Start with window hidden
                self.parent.chart_widget.toggle_panel_button.setChecked(False)

        logger.info(f"TradingBotWindow created for {self.parent.symbol}")

    # Issue #14: LiveData Button entfernt
    # def setup_live_data_toggle(self) -> None:
    #     """Add a main-window-style live data toggle next to the zoom-back button."""
    #     toolbar = getattr(self.parent.chart_widget, "toolbar_row1", None)
    #     if toolbar is None:
    #         logger.warning("Chart toolbar row1 missing - live data toggle not added")
    #         return
    #
    #     self.parent.chart_live_data_toggle = QPushButton("Live Data: OFF")
    #     self.parent.chart_live_data_toggle.setCheckable(True)
    #     self.parent.chart_live_data_toggle.setToolTip(
    #         "Toggle live market data in paper mode\n"
    #         "• ON: Use real-time market data from providers\n"
    #         "• OFF: Use cached/simulated data"
    #     )
    #     self.parent.chart_live_data_toggle.clicked.connect(
    #         self.parent._handlers.on_chart_live_data_toggle_clicked
    #     )
    #
    #     if hasattr(self.parent.chart_widget, "zoom_back_button"):
    #         ref_button = self.parent.chart_widget.zoom_back_button
    #         ref_height = ref_button.sizeHint().height()
    #         ref_width = ref_button.sizeHint().width()
    #         if ref_height > 0:
    #             self.parent.chart_live_data_toggle.setFixedHeight(ref_height)
    #         self.parent.chart_live_data_toggle.setMinimumWidth(max(ref_width + 70, 130))
    #
    #     toolbar.addWidget(self.parent.chart_live_data_toggle)
    #
    #     main_window = self.parent._get_main_window()
    #     if main_window and hasattr(main_window, "live_data_toggle"):
    #         self.parent._handlers.on_main_live_data_toggled(main_window.live_data_toggle.isChecked())
    #         main_window.live_data_toggle.toggled.connect(
    #             self.parent._handlers.on_main_live_data_toggled
    #         )
    #     else:
    #         live_data_enabled = self.parent.settings.value("live_data_enabled", False, type=bool)
    #         self.parent._handlers.update_chart_live_data_toggle(live_data_enabled)
    #         if hasattr(self.parent.chart_widget, "live_stream_button"):
    #             self.parent.chart_widget.live_stream_button.toggled.connect(
    #                 self.parent._handlers.on_chart_stream_button_toggled
    #             )

    def _on_trading_bot_window_closed(self) -> None:
        """Handle Trading Bot window close event."""
        if hasattr(self.parent.chart_widget, 'toggle_panel_button'):
            self.parent.chart_widget.toggle_panel_button.setChecked(False)
        self.parent._update_toggle_button_text()

    def restore_after_state_load(self) -> None:
        """Restore UI after state load."""
        self.parent.chart_widget.setVisible(True)
        # Legacy dock properties (kept for compatibility but not used)
        self.parent._dock_maximized = False
        self.parent._dock_minimized = False
        # Note: _dock_title_bar is None now since we use TradingBotWindow

    def setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        self.parent._reset_shortcut = QShortcut(QKeySequence("Ctrl+R"), self.parent)
        self.parent._reset_shortcut.activated.connect(self.parent._dock_control.reset_layout)

        self.parent._help_shortcut = QShortcut(QKeySequence("F1"), self.parent)
        self.parent._help_shortcut.activated.connect(self.open_trailing_stop_help)

        self.parent._chat_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self.parent)
        self.parent._chat_shortcut.activated.connect(self.parent.toggle_chat_widget)

        self.parent._analysis_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self.parent)
        self.parent._analysis_shortcut.activated.connect(self.parent.request_chart_analysis)

        # Phase 6: Strategy Concept shortcut
        self.parent._strategy_concept_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self.parent)
        self.parent._strategy_concept_shortcut.activated.connect(self.open_strategy_concept)

    def open_strategy_concept(self) -> None:
        """Open Strategy Concept window (keyboard shortcut handler)."""
        if hasattr(self.parent, "chart_widget") and hasattr(self.parent.chart_widget, "show_strategy_concept"):
            self.parent.chart_widget.show_strategy_concept()
        else:
            logger.warning("Strategy Concept not available")

    def connect_dock_signals(self) -> None:
        """Connect dock/window signals.

        For TradingBotWindow: visibility_changed signal is already connected in setup_dock().
        For legacy dock_widget: connect visibilityChanged here.
        """
        # TradingBotWindow signals are connected in setup_dock()
        if hasattr(self.parent, '_trading_bot_window') and self.parent._trading_bot_window:
            # Already connected in setup_dock()
            return

        # Legacy dock_widget handling
        if hasattr(self.parent, 'dock_widget') and self.parent.dock_widget:
            self.parent.dock_widget.visibilityChanged.connect(self.parent._handlers.on_dock_visibility_changed)

    def setup_chat(self) -> None:
        """Setup chart chat integration."""
        self.parent.setup_chart_chat(self.parent.chart_widget)
        if hasattr(self.parent.chart_widget, 'ai_chat_button'):
            self.parent.chart_widget.ai_chat_button.clicked.connect(
                self.parent._handlers.on_ai_chat_button_clicked
            )
        if getattr(self.parent, "_chat_widget", None):
            self.parent._chat_widget.visibilityChanged.connect(self.on_chat_visibility_changed)
            self.parent._chat_widget.topLevelChanged.connect(self.on_chat_top_level_changed)
            self.parent._chat_widget.dockLocationChanged.connect(self.on_chat_dock_location_changed)

    def setup_bitunix_trading(self) -> None:
        """Set up Bitunix trading widget integration."""
        self.parent.setup_bitunix_trading(self.parent.chart_widget)
        if hasattr(self.parent.chart_widget, 'bitunix_trading_button'):
            logger.info("✅ Bitunix button found, connecting clicked signal...")
            self.parent.chart_widget.bitunix_trading_button.clicked.connect(
                self.parent._handlers.on_bitunix_trading_button_clicked
            )
            logger.info("✅ Bitunix button click handler connected")
        else:
            logger.warning("❌ Bitunix button NOT found on chart_widget!")
        if getattr(self.parent, "_bitunix_widget", None):
            self.parent._bitunix_widget.visibilityChanged.connect(self.parent._handlers.on_bitunix_visibility_changed)
            # Restore Bitunix visibility from settings (created AFTER restoreState, so manual restore needed)
            self._restore_bitunix_visibility()

    def _restore_bitunix_visibility(self) -> None:
        """Restore Bitunix widget visibility from settings."""
        if not getattr(self.parent, "_bitunix_widget", None):
            logger.info("_restore_bitunix_visibility: No _bitunix_widget found")
            return

        settings_key = self.parent._get_settings_key() if hasattr(self.parent, '_get_settings_key') else f"ChartWindow/{self.parent.symbol}"
        bitunix_visible = self.parent.settings.value(f"{settings_key}/bitunix_visible", False, type=bool)
        logger.info(f"_restore_bitunix_visibility: bitunix_visible from settings = {bitunix_visible}")

        # Always ensure widget is docked, not floating (QSettings might have restored floating state)
        if self.parent._bitunix_widget.isFloating():
            logger.info("   Bitunix widget was floating, forcing docked state...")
            self.parent._bitunix_widget.setFloating(False)

        if bitunix_visible:
            self.parent._bitunix_widget.show()
            if hasattr(self.parent.chart_widget, 'bitunix_trading_button'):
                self.parent.chart_widget.bitunix_trading_button.setChecked(True)
            logger.info("   Restored Bitunix widget visibility from settings (visible=True)")
        else:
            # Ensure it's hidden if settings say so
            self.parent._bitunix_widget.hide()
            logger.info("   Bitunix widget remains hidden per settings")

    def setup_ai_analysis(self) -> None:
        """Setup the AI Analysis Popup."""
        if hasattr(self.parent.chart_widget, 'ai_analysis_button'):
            self.parent.chart_widget.ai_analysis_button.clicked.connect(
                self.parent._handlers.on_ai_analysis_button_clicked
            )

    def connect_data_loaded_signals(self) -> None:
        """Connect data loaded signals."""
        self.parent.chart_widget.data_loaded.connect(self.parent._restore_chart_state)
        self.parent.chart_widget.data_loaded.connect(self.parent._restore_indicators_after_data_load)
        self.parent.chart_widget.data_loaded.connect(self.activate_live_stream)
        if hasattr(self.parent, "_update_compact_chart_from_main"):
            self.parent.chart_widget.data_loaded.connect(self.parent._update_compact_chart_from_main)

    def activate_live_stream(self):
        """Activate live streaming when chart data is loaded."""
        if hasattr(self.parent.chart_widget, 'live_stream_button'):
            live_data_enabled = self.parent.settings.value("live_data_enabled", False, type=bool)
            if not live_data_enabled:
                logger.info("Live data disabled - skipping auto-activate stream")
                if self.parent.chart_widget.live_stream_button.isChecked():
                    self.parent.chart_widget.live_stream_button.setChecked(False)
                return
            # Only activate if not already streaming
            if not self.parent.chart_widget.live_stream_button.isChecked():
                logger.info(f"Auto-activating live stream for {self.parent.symbol}")
                # click() toggles checked state and triggers the connected slot
                self.parent.chart_widget.live_stream_button.click()

    # =========================================================================
    # Chat helper methods
    # =========================================================================

    def ensure_chat_docked_right(self) -> None:
        """Dock the chat widget to the right if it is not floating."""
        if not getattr(self.parent, "_chat_widget", None):
            return
        if self.parent._chat_widget.isFloating():
            return
        try:
            self.parent.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.parent._chat_widget)
        except Exception as e:
            logger.debug("Failed to dock chat widget: %s", e)

    def sync_ai_chat_button_state(self) -> None:
        """Ensure the toolbar toggle reflects the dock visibility."""
        if hasattr(self.parent.chart_widget, 'ai_chat_button') and getattr(self.parent, "_chat_widget", None):
            self.parent.chart_widget.ai_chat_button.setChecked(self.parent._chat_widget.isVisible())

    def schedule_chart_resize(self, delay_ms: int = 120) -> None:
        """Throttle resize requests after dock/undock/visibility changes."""
        if self.parent._chart_resize_pending:
            return
        self.parent._chart_resize_pending = True

        def _do_resize():
            self.parent._chart_resize_pending = False
            try:
                if hasattr(self.parent.chart_widget, "request_chart_resize"):
                    self.parent.chart_widget.request_chart_resize()
            except Exception as e:
                logger.debug("Chart resize after chat change failed: %s", e)

        QTimer.singleShot(delay_ms, _do_resize)

    def on_chat_visibility_changed(self, visible: bool) -> None:
        if visible:
            self.ensure_chat_docked_right()
        self.sync_ai_chat_button_state()
        self.schedule_chart_resize()

    def on_chat_top_level_changed(self, floating: bool) -> None:
        # Floating=True means detached; resize ensures chart reclaims full width
        self.schedule_chart_resize()

    def on_chat_dock_location_changed(self, _area) -> None:
        self.schedule_chart_resize()

    def open_trailing_stop_help(self):
        """Open the trailing stop help documentation in browser."""
        import webbrowser
        from pathlib import Path

        try:
            # Find project root and help file
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            help_file = project_root / "Help" / "trailing-stop-hilfe.html"

            if help_file.exists():
                webbrowser.open(help_file.as_uri())
                logger.info(f"Opened help file: {help_file}")
            else:
                logger.warning(f"Help file not found: {help_file}")
        except Exception as e:
            logger.error(f"Error opening help file: {e}")
