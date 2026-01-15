"""Layout Window Operations - Open/Close Layouts and Windows.

Refactored from layout_manager.py.

Contains:
- open_layout: Open multiple windows from layout config
- close_all_windows: Close all tracked windows
- _create_chart_window: Create single ChartWindow with configuration
- _position_window: Position window on specific monitor
- _setup_crosshair_sync: Setup crosshair synchronization (placeholder)
- _on_window_destroyed: Handle window close event
- open_pre_trade_analysis: Entry point for pre-trade analysis
- create_layout_from_current: Capture current windows into layout config
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow
    from .layout_config_models import ChartWindowConfig, ChartLayoutConfig
    from .layout_manager import ChartLayoutManager

logger = logging.getLogger(__name__)


class LayoutWindowOperations:
    """Helper for window operations and layout management."""

    def __init__(self, parent: "ChartLayoutManager"):
        self.parent = parent

    def open_layout(self, layout: "ChartLayoutConfig", symbol: str | None = None) -> list["ChartWindow"]:
        """Open a chart layout with multiple windows.

        Args:
            layout: The layout configuration
            symbol: Optional symbol override for all charts (uses layout's symbols if None)

        Returns:
            List of opened ChartWindow instances
        """
        # Close any existing layout first
        self.close_all_windows()

        self.parent._current_layout = layout
        opened_windows = []

        for win_config in layout.windows:
            # Override symbol if provided
            chart_symbol = symbol if symbol else win_config.symbol

            try:
                window = self._create_chart_window(
                    symbol=chart_symbol,
                    timeframe=win_config.timeframe,
                    period=win_config.period,
                    indicators=win_config.indicators,
                    auto_stream=win_config.auto_stream,
                )

                # Position the window
                self._position_window(window, win_config)

                # Show and track the window
                window.show()
                self.parent._active_windows.append(window)
                opened_windows.append(window)

                # Connect close event
                window.destroyed.connect(lambda w=window: self._on_window_destroyed(w))

                self.parent.window_opened.emit(window)
                logger.info(f"Opened chart: {chart_symbol} @ {win_config.timeframe} on monitor {win_config.monitor}")

            except Exception as e:
                logger.error(f"Failed to open chart window: {e}", exc_info=True)

        # Setup crosshair sync if enabled
        if layout.sync_crosshair and len(opened_windows) > 1:
            self._setup_crosshair_sync(opened_windows)

        self.parent.layout_opened.emit(layout.name)
        logger.info(f"Layout '{layout.name}' opened with {len(opened_windows)} windows")

        return opened_windows

    def _create_chart_window(
        self,
        symbol: str,
        timeframe: str,
        period: str,
        indicators: list[str],
        auto_stream: bool,
    ) -> "ChartWindow":
        """Create a new chart window with the specified configuration."""
        from src.ui.widgets.chart_window import ChartWindow

        # Create window with symbol and history manager
        window = ChartWindow(symbol=symbol, history_manager=self.parent._history_manager)

        # Set timeframe and period
        if hasattr(window, 'chart_widget'):
            chart = window.chart_widget
            chart.current_symbol = symbol
            chart.current_timeframe = timeframe
            chart.current_period = period

            # Update UI elements
            if hasattr(chart, 'symbol_combo'):
                idx = chart.symbol_combo.findText(symbol)
                if idx >= 0:
                    chart.symbol_combo.setCurrentIndex(idx)
                else:
                    chart.symbol_combo.setCurrentText(symbol)

            if hasattr(chart, 'timeframe_combo'):
                idx = chart.timeframe_combo.findData(timeframe)
                if idx >= 0:
                    chart.timeframe_combo.setCurrentIndex(idx)

            if hasattr(chart, 'period_combo'):
                idx = chart.period_combo.findData(period)
                if idx >= 0:
                    chart.period_combo.setCurrentIndex(idx)

            # Enable indicators
            for ind_id in indicators:
                if hasattr(chart, 'indicator_actions') and ind_id in chart.indicator_actions:
                    chart.indicator_actions[ind_id].setChecked(True)

        return window

    def _position_window(self, window: "ChartWindow", config: "ChartWindowConfig") -> None:
        """Position a window according to its configuration."""
        monitor_geo = self.parent._monitor_manager.get_monitor_geometry(config.monitor)

        # Calculate absolute position
        abs_x = monitor_geo.x() + config.x
        abs_y = monitor_geo.y() + config.y

        # Set geometry
        window.setGeometry(abs_x, abs_y, config.width, config.height)

        logger.debug(f"Positioned window at ({abs_x}, {abs_y}) size ({config.width}x{config.height})")

    def _setup_crosshair_sync(self, windows: list["ChartWindow"]) -> None:
        """Setup crosshair synchronization between chart windows."""
        # TODO: Implement crosshair sync via JavaScript bridge
        # This requires coordination between the chart widgets
        logger.info(f"Crosshair sync setup for {len(windows)} windows (placeholder)")

    def _on_window_destroyed(self, window: "ChartWindow") -> None:
        """Handle window destruction."""
        if window in self.parent._active_windows:
            self.parent._active_windows.remove(window)
            self.parent.window_closed.emit(window)

    def close_all_windows(self) -> None:
        """Close all active chart windows."""
        for window in self.parent._active_windows.copy():
            try:
                window.close()
            except Exception as e:
                logger.error(f"Error closing window: {e}")

        self.parent._active_windows.clear()
        self.parent._current_layout = None
        self.parent.layout_closed.emit()

    def open_pre_trade_analysis(self, symbol: str) -> list["ChartWindow"]:
        """Open pre-trade analysis charts for a symbol.

        This is the main entry point for opening charts BEFORE a trade.
        Opens multiple timeframes to analyze the overarching trend.

        Args:
            symbol: The trading symbol (e.g., "BTC/USD", "AAPL")

        Returns:
            List of opened chart windows
        """
        # Load the default multi-timeframe layout
        layout = self.parent._persistence.load_layout("Multi-Timeframe-Analyse")
        if not layout:
            logger.error("Multi-Timeframe-Analyse layout not found!")
            return []

        # Open with the specified symbol
        return self.open_layout(layout, symbol=symbol)

    def create_layout_from_current(self, name: str, description: str = "") -> "ChartLayoutConfig | None":
        """Create a layout configuration from currently open windows.

        Args:
            name: Name for the new layout
            description: Optional description

        Returns:
            ChartLayoutConfig or None if no windows are open
        """
        from .layout_config_models import ChartLayoutConfig, ChartWindowConfig

        if not self.parent._active_windows:
            logger.warning("No windows open to create layout from")
            return None

        windows_config = []
        screens = QApplication.screens()

        for window in self.parent._active_windows:
            # Determine which monitor the window is on
            window_center = window.geometry().center()
            monitor_idx = 0
            for i, screen in enumerate(screens):
                if screen.geometry().contains(window_center):
                    monitor_idx = i
                    break

            # Get relative position on that monitor
            monitor_geo = screens[monitor_idx].geometry()
            rel_x = window.x() - monitor_geo.x()
            rel_y = window.y() - monitor_geo.y()

            # Get chart settings
            chart = getattr(window, 'chart_widget', None)
            if chart:
                config = ChartWindowConfig(
                    symbol=getattr(chart, 'current_symbol', 'BTC/USD'),
                    timeframe=getattr(chart, 'current_timeframe', '1T'),
                    period=getattr(chart, 'current_period', '1D'),
                    monitor=monitor_idx,
                    x=rel_x,
                    y=rel_y,
                    width=window.width(),
                    height=window.height(),
                    indicators=[],  # TODO: Get active indicators
                    auto_stream=getattr(chart, 'live_streaming_enabled', False),
                )
                windows_config.append(config)

        layout = ChartLayoutConfig(
            name=name,
            description=description,
            windows=windows_config,
        )

        return layout
