"""Popup Chart Window for OrderPilot-AI.

Provides a dedicated window for viewing charts with full screen support.
Can be detached from the main application for multi-monitor setups.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtGui import QCloseEvent

from .embedded_tradingview_chart import EmbeddedTradingViewChart

logger = logging.getLogger(__name__)


class ChartWindow(QMainWindow):
    """Popup window for displaying a single chart."""

    # Signals
    window_closed = pyqtSignal(str)  # Emitted when window closes, passes symbol

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

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create chart widget
        self.chart_widget = EmbeddedTradingViewChart(history_manager=history_manager)
        layout.addWidget(self.chart_widget)

        # Set symbol in chart
        self.chart_widget.current_symbol = symbol
        self.chart_widget.symbol_combo.setCurrentText(symbol)

        # Load window geometry from settings
        self._load_window_state()

        logger.info(f"ChartWindow created for {symbol}")

    def _load_window_state(self):
        """Load window position and size from settings."""
        settings_key = f"ChartWindow/{self.symbol}"

        # Load geometry
        geometry = self.settings.value(f"{settings_key}/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size and position
            self.resize(1200, 800)
            # Center on screen
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

        # Load window state (maximized, etc.)
        window_state = self.settings.value(f"{settings_key}/windowState")
        if window_state:
            self.restoreState(window_state)

        # Load chart settings
        timeframe = self.settings.value(f"{settings_key}/timeframe")
        if timeframe:
            self.chart_widget.current_timeframe = timeframe
            # Update combo box
            index = self.chart_widget.timeframe_combo.findData(timeframe)
            if index >= 0:
                self.chart_widget.timeframe_combo.setCurrentIndex(index)

        period = self.settings.value(f"{settings_key}/period")
        if period:
            self.chart_widget.current_period = period
            # Update combo box
            index = self.chart_widget.period_combo.findData(period)
            if index >= 0:
                self.chart_widget.period_combo.setCurrentIndex(index)

        # Load active indicators
        active_indicators = self.settings.value(f"{settings_key}/indicators")
        if active_indicators and isinstance(active_indicators, list):
            for indicator_id in active_indicators:
                if indicator_id in self.chart_widget.indicator_actions:
                    action = self.chart_widget.indicator_actions[indicator_id]
                    action.setChecked(True)

        logger.debug(f"Loaded window state for {self.symbol}")

    def _save_window_state(self):
        """Save window position, size, and chart settings."""
        settings_key = f"ChartWindow/{self.symbol}"

        # Save geometry
        self.settings.setValue(f"{settings_key}/geometry", self.saveGeometry())

        # Save window state
        self.settings.setValue(f"{settings_key}/windowState", self.saveState())

        # Save chart settings
        self.settings.setValue(f"{settings_key}/timeframe", self.chart_widget.current_timeframe)
        self.settings.setValue(f"{settings_key}/period", self.chart_widget.current_period)

        # Save active indicators
        active_indicators = [
            ind_id for ind_id, action in self.chart_widget.indicator_actions.items()
            if action.isChecked()
        ]
        self.settings.setValue(f"{settings_key}/indicators", active_indicators)

        logger.debug(f"Saved window state for {self.symbol}")

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event.

        Args:
            event: Close event
        """
        # Save state before closing
        self._save_window_state()

        # Emit signal that window is closing
        self.window_closed.emit(self.symbol)

        logger.info(f"ChartWindow closed for {self.symbol}")

        # Accept the close event
        event.accept()

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
