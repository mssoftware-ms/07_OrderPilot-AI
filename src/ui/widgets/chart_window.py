"""Popup Chart Window for OrderPilot-AI.

Provides a dedicated window for viewing charts with full screen support.
Can be detached from the main application for multi-monitor setups.

REFACTORED: Extracted mixins to meet 600 LOC limit.
- PanelsMixin: Tab creation (Strategy, Backtest, Optimization, Results)
- BacktestMixin: Backtest execution and visualization
- EventBusMixin: Event bus integration for live markers
- StateMixin: State save/restore functionality
"""

import json
import logging
from typing import Optional

from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMainWindow, QDockWidget
from PyQt6.QtGui import QCloseEvent

from .embedded_tradingview_chart import EmbeddedTradingViewChart
from .chart_window_mixins import PanelsMixin, BacktestMixin, EventBusMixin, StateMixin

logger = logging.getLogger(__name__)


class ChartWindow(PanelsMixin, BacktestMixin, EventBusMixin, StateMixin, QMainWindow):
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

        # Window configuration
        self.setWindowTitle(f"Chart - {symbol}")
        self.setMinimumSize(800, 600)

        # Center: Chart Widget
        self.chart_widget = EmbeddedTradingViewChart(history_manager=history_manager)
        self.setCentralWidget(self.chart_widget)

        # Set symbol in chart
        self.chart_widget.current_symbol = symbol
        if hasattr(self.chart_widget, 'symbol_combo'):
            self.chart_widget.symbol_combo.setCurrentText(symbol)

        # Dock: Control Panels (Strategy, Backtest, etc.)
        self.dock_widget = QDockWidget("Analysis & Strategy", self)
        self.dock_widget.setObjectName("analysisDock")
        self.dock_widget.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Create panel content (from PanelsMixin)
        self.bottom_panel = self._create_bottom_panel()
        self.dock_widget.setWidget(self.bottom_panel)

        # Add dock to main window
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_widget)

        # Connect toggle button
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            self.chart_widget.toggle_panel_button.clicked.connect(self._toggle_bottom_panel)
            self.chart_widget.toggle_panel_button.setChecked(self.dock_widget.isVisible())

        # Load window geometry from settings (from StateMixin)
        self._load_window_state()

        # Update button text based on loaded state
        self._update_toggle_button_text()

        # Connect dock visibility change
        self.dock_widget.visibilityChanged.connect(self._on_dock_visibility_changed)

        # Setup event bus subscriptions (from EventBusMixin)
        self._setup_event_subscriptions()

        # State for closing
        self._ready_to_close = False

        # Restore layout when data is loaded (from StateMixin)
        self.chart_widget.data_loaded.connect(self._restore_chart_state)
        self.chart_widget.data_loaded.connect(self._restore_indicators_after_data_load)

        logger.info(f"ChartWindow created for {symbol}")

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event with async state saving."""
        if self._ready_to_close:
            logger.info(f"Closing ChartWindow for {self.symbol}...")

            # Stop live stream if running
            if hasattr(self.chart_widget, 'live_streaming_enabled') and self.chart_widget.live_streaming_enabled:
                try:
                    self.chart_widget.live_streaming_enabled = False
                    if hasattr(self.chart_widget, 'live_stream_action'):
                        self.chart_widget.live_stream_action.setChecked(False)
                except Exception as e:
                    logger.debug(f"Error stopping live stream: {e}")

            # Unsubscribe from event bus (from EventBusMixin)
            self._unsubscribe_events()

            # Save sync state (from StateMixin)
            self._save_window_state()

            # Emit signal
            self.window_closed.emit(self.symbol)

            event.accept()
            return

        # Request async cleanup
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

        # Timeout to force close
        def force_close():
            if not self._ready_to_close:
                logger.warning("Chart state fetch timed out, forcing close")
                self._ready_to_close = True
                self.close()

        QTimer.singleShot(2000, force_close)

        # Start chain
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
