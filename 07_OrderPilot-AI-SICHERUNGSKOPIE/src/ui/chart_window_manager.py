"""Chart Window Manager for OrderPilot-AI.

Manages popup chart windows, ensuring only one window per symbol
and providing focus management.
"""

import asyncio
import logging
from typing import Dict, Optional

from .widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class ChartWindowManager:
    """Manages popup chart windows."""

    def __init__(self, history_manager=None, parent=None):
        """Initialize chart window manager.

        Args:
            history_manager: HistoryManager instance for loading data
            parent: Parent widget for the windows
        """
        self.history_manager = history_manager
        self.parent = parent
        self.windows: Dict[str, ChartWindow] = {}

        logger.info("ChartWindowManager initialized")

    def open_or_focus_chart(self, symbol: str, data_provider: Optional[str] = None):
        """Open a chart window for the symbol, or focus if already open.

        Args:
            symbol: Trading symbol
            data_provider: Optional data provider to use

        Returns:
            ChartWindow instance
        """
        symbol = symbol.upper()  # Normalize symbol

        # Check if window already exists
        if symbol in self.windows:
            window = self.windows[symbol]

            # Check if window is still valid (not deleted)
            try:
                # Issue #36: Check if window is minimized and restore it
                if window.isMinimized():
                    window.showNormal()  # Restore from minimized state
                    window.raise_()  # Bring to front
                    window.activateWindow()  # Activate and focus
                    logger.info(f"Restored minimized chart window for {symbol}")
                    return window
                elif window.isVisible():
                    # Window exists and is visible, just focus it
                    window.raise_()  # Bring to front
                    window.activateWindow()  # Activate and focus
                    logger.info(f"Focused existing chart window for {symbol}")
                    return window
                else:
                    # Window exists but is hidden, show it
                    window.show()
                    window.raise_()
                    window.activateWindow()
                    logger.info(f"Showed hidden chart window for {symbol}")
                    return window
            except RuntimeError:
                # Window was deleted, remove from dict
                logger.warning(f"Chart window for {symbol} was deleted, creating new one")
                del self.windows[symbol]

        # Create new window
        window = ChartWindow(
            symbol=symbol,
            history_manager=self.history_manager,
            parent=self.parent
        )

        # Connect close signal
        window.window_closed.connect(self._on_window_closed)

        # Store window
        self.windows[symbol] = window

        # Show window
        window.show()
        window.raise_()
        window.activateWindow()

        # Load chart data asynchronously
        asyncio.create_task(window.load_chart(data_provider))

        logger.info(f"Created and opened new chart window for {symbol}")

        return window

    def _on_window_closed(self, symbol: str):
        """Handle window closed signal.

        Args:
            symbol: Symbol of the closed window
        """
        if symbol in self.windows:
            del self.windows[symbol]
            logger.info(f"Removed closed chart window for {symbol} from manager")

    def close_window(self, symbol: str):
        """Close a chart window.

        Args:
            symbol: Symbol of the window to close
        """
        symbol = symbol.upper()

        if symbol in self.windows:
            window = self.windows[symbol]
            window.close()  # This will trigger _on_window_closed
            logger.info(f"Closed chart window for {symbol}")
        else:
            logger.warning(f"No chart window found for {symbol}")

    def close_all_windows(self):
        """Close all open chart windows."""
        # Create a copy of the symbols list to avoid modification during iteration
        symbols = list(self.windows.keys())

        for symbol in symbols:
            self.close_window(symbol)

        logger.info("Closed all chart windows")

    def get_open_symbols(self):
        """Get list of symbols with open chart windows.

        Returns:
            List of symbol strings
        """
        return list(self.windows.keys())

    def has_open_window(self, symbol: str) -> bool:
        """Check if a window is open for the symbol.

        Args:
            symbol: Trading symbol

        Returns:
            True if window is open, False otherwise
        """
        symbol = symbol.upper()
        return symbol in self.windows

    def get_active_symbol(self) -> Optional[str]:
        """Get the symbol of the currently focused/active chart window.

        Returns:
            Symbol string if an active chart exists, None otherwise
        """
        # Check all windows for the one that is currently active
        for symbol, window in self.windows.items():
            try:
                if window.isActiveWindow():
                    logger.debug(f"Active chart window: {symbol}")
                    return symbol
            except RuntimeError:
                # Window was deleted
                continue

        # If no window is active, return the most recently opened window
        if self.windows:
            last_symbol = list(self.windows.keys())[-1]
            logger.debug(f"No active window, returning last opened: {last_symbol}")
            return last_symbol

        return None

    def open_chart(self, symbol: str, chart_type=None):
        """Open a chart window (alias for open_or_focus_chart).

        This method provides compatibility with code that used EnhancedChartWindow.

        Args:
            symbol: Trading symbol
            chart_type: Chart type (ignored, uses TradingView)

        Returns:
            ChartWindow instance
        """
        return self.open_or_focus_chart(symbol)

    def close_all_charts(self):
        """Close all open chart windows (alias for close_all_windows)."""
        self.close_all_windows()

    def refresh_all_chart_colors(self):
        """Refresh colors for all open charts (Issues #34, #37).

        Calls refresh_chart_colors() on each chart's chart_widget.
        """
        refreshed_count = 0
        for symbol, window in list(self.windows.items()):
            try:
                # Access the chart_widget inside the ChartWindow
                if hasattr(window, "chart_widget") and window.chart_widget:
                    if hasattr(window.chart_widget, "refresh_chart_colors"):
                        window.chart_widget.refresh_chart_colors()
                        refreshed_count += 1
                        logger.debug(f"Refreshed colors for chart: {symbol}")
                    else:
                        logger.warning(f"Chart {symbol} has no refresh_chart_colors method")
                else:
                    logger.warning(f"Chart window {symbol} has no chart_widget")
            except RuntimeError:
                # Window was deleted
                logger.debug(f"Chart window for {symbol} was deleted during refresh")
                continue
            except Exception as exc:
                logger.error(f"Failed to refresh colors for chart {symbol}: {exc}")

        logger.info(f"Refreshed colors for {refreshed_count} chart(s)")


# Singleton instance
_chart_window_manager_instance: Optional[ChartWindowManager] = None


def get_chart_window_manager(history_manager=None, parent=None) -> ChartWindowManager:
    """Get or create the singleton ChartWindowManager instance.

    This function provides a global access point to the ChartWindowManager,
    migrated from enhanced_chart_window.py.

    Args:
        history_manager: HistoryManager instance (only used on first call)
        parent: Parent widget (only used on first call)

    Returns:
        ChartWindowManager singleton instance
    """
    global _chart_window_manager_instance

    if _chart_window_manager_instance is None:
        _chart_window_manager_instance = ChartWindowManager(
            history_manager=history_manager,
            parent=parent
        )
        logger.info("Created ChartWindowManager singleton")

    return _chart_window_manager_instance
