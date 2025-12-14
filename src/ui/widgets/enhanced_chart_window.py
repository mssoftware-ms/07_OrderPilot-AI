"""Enhanced Chart Window with Comprehensive State Persistence.

This module provides an enhanced chart window that automatically saves and restores:
- Zoom factors and pan positions
- Indicator configurations and their row heights
- Window geometry and layout
- Pane layouts and splitter positions
"""

import logging
from typing import Optional, Dict, Any
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDockWidget, QLabel, QSplitter
)
from PyQt6.QtGui import QCloseEvent

from .chart_factory import ChartFactory, ChartType
from .chart_state_integration import install_chart_state_persistence
from .chart_state_manager import get_chart_state_manager, ChartState

logger = logging.getLogger(__name__)


class EnhancedChartWindow(QMainWindow):
    """Enhanced chart window with automatic state persistence.

    Features:
    - Automatic save/restore of all chart states
    - Support for multiple chart types (TradingView, PyQtGraph)
    - Window geometry persistence
    - Indicator configuration persistence
    - Zoom and pan state preservation
    - Pane layout (row heights) preservation
    """

    # Signals
    chart_opened = pyqtSignal(str)  # symbol
    chart_closed = pyqtSignal(str)  # symbol
    state_saved = pyqtSignal(str)   # symbol
    state_restored = pyqtSignal(str) # symbol

    def __init__(self, symbol: str, chart_type: ChartType = ChartType.AUTO, parent=None):
        """Initialize enhanced chart window.

        Args:
            symbol: Trading symbol to display
            chart_type: Type of chart to create
            parent: Parent widget
        """
        try:
            logger.info(f"🔧 Initializing EnhancedChartWindow for {symbol}")
            super().__init__(parent)

            self.symbol = symbol
            self.chart_type = chart_type
            self.state_manager = get_chart_state_manager()

            # State management
            self._auto_save_enabled = True
            self._state_save_timer = QTimer()
            self._state_save_timer.setSingleShot(True)
            self._state_save_timer.timeout.connect(self._save_window_state)

            # Chart widget
            self.chart_widget = None

            logger.info(f"📐 Setting up UI for {symbol}")
            # Setup UI
            self._setup_ui()

            logger.info(f"📊 Setting up chart for {symbol}")
            self._setup_chart()

            logger.info(f"🔗 Connecting signals for {symbol}")
            # Connect signals
            self._connect_signals()

            logger.info(f"💾 Scheduling state restoration for {symbol}")
            # Load saved state
            QTimer.singleShot(1000, self._restore_window_state)

            logger.info(f"✅ Enhanced chart window initialized for {symbol}")

        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to initialize EnhancedChartWindow for {symbol}: {e}", exc_info=True)
            # Don't raise - show error in UI instead
            import traceback
            error_msg = f"Failed to initialize chart window:\n\n{str(e)}\n\n{traceback.format_exc()}"
            logger.error(error_msg)

    def _setup_ui(self):
        """Setup the main window UI."""
        try:
            logger.info(f"Setting window title for {self.symbol}")
            self.setWindowTitle(f"Chart - {self.symbol}")

            logger.info(f"Setting minimum size")
            self.setMinimumSize(800, 600)

            logger.info(f"Creating central widget")
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            logger.info(f"Creating main layout")
            # Main layout
            self.main_layout = QVBoxLayout(central_widget)
            self.main_layout.setContentsMargins(5, 5, 5, 5)

            logger.info(f"Setting status bar message")
            # Status bar
            self.statusBar().showMessage(f"Loading chart for {self.symbol}...")

            logger.info(f"✅ UI setup completed for {self.symbol}")

        except Exception as e:
            logger.error(f"❌ Failed to setup UI: {e}", exc_info=True)
            raise

    def _setup_chart(self):
        """Setup the chart widget with state persistence."""
        try:
            logger.info(f"Creating chart widget for {self.symbol} with type {self.chart_type}")

            # Create chart using factory
            self.chart_widget = ChartFactory.create_chart(
                chart_type=self.chart_type,
                symbol=self.symbol
            )

            if not self.chart_widget:
                raise RuntimeError("Chart factory returned None")

            logger.info(f"Chart widget created: {type(self.chart_widget).__name__}")

            # Install state persistence
            self.chart_widget = install_chart_state_persistence(
                self.chart_widget,
                chart_type="auto"
            )

            logger.info("State persistence installed on chart widget")

            # Add to layout
            self.main_layout.addWidget(self.chart_widget)

            # Set symbol if method exists
            if hasattr(self.chart_widget, 'set_symbol'):
                self.chart_widget.set_symbol(self.symbol)
                logger.info(f"Symbol set via set_symbol(): {self.symbol}")
            elif hasattr(self.chart_widget, 'current_symbol'):
                self.chart_widget.current_symbol = self.symbol
                logger.info(f"Symbol set via current_symbol: {self.symbol}")

            logger.info(f"✅ Chart widget created and enhanced with state persistence")

        except Exception as e:
            logger.error(f"❌ Failed to setup chart: {e}", exc_info=True)
            self._show_error_message(f"Failed to create chart: {e}")

    def _connect_signals(self):
        """Connect signals for automatic state management."""
        try:
            logger.info("Connecting chart widget signals")

            # Chart widget signals (if available)
            if hasattr(self.chart_widget, 'chart_state_saved'):
                self.chart_widget.chart_state_saved.connect(self._on_chart_state_saved)
                logger.debug("Connected chart_state_saved signal")

            if hasattr(self.chart_widget, 'chart_state_loaded'):
                self.chart_widget.chart_state_loaded.connect(self._on_chart_state_loaded)
                logger.debug("Connected chart_state_loaded signal")

            logger.info("Connecting state manager signals")
            # State manager signals
            self.state_manager.state_saved.connect(self._on_state_manager_saved)
            self.state_manager.state_loaded.connect(self._on_state_manager_loaded)

            logger.info("✅ All signals connected successfully")

        except Exception as e:
            logger.error(f"❌ Failed to connect signals: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't crash - continue without signal connections

    def _show_error_message(self, message: str):
        """Show error message in status bar and central widget."""
        self.statusBar().showMessage(f"Error: {message}")

        error_label = QLabel(f"⚠️ {message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14pt; padding: 20px;")

        self.main_layout.addWidget(error_label)

    def save_state_now(self):
        """Immediately save all window and chart state."""
        try:
            # Save chart state
            if hasattr(self.chart_widget, 'save_chart_state_now'):
                self.chart_widget.save_chart_state_now(include_window_state=True)

            # Save window-specific state
            self._save_window_state()

            logger.info(f"Saved complete state for {self.symbol}")
            self.state_saved.emit(self.symbol)

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def load_state_now(self) -> bool:
        """Load saved state immediately.

        Returns:
            True if state was loaded successfully
        """
        try:
            # Load window state
            window_loaded = self._restore_window_state()

            # Load chart state
            chart_loaded = False
            if hasattr(self.chart_widget, 'load_chart_state_now'):
                chart_loaded = self.chart_widget.load_chart_state_now()

            success = window_loaded or chart_loaded
            if success:
                logger.info(f"Restored state for {self.symbol}")
                self.state_restored.emit(self.symbol)

            return success

        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False

    def clear_saved_state(self):
        """Clear all saved state for this symbol."""
        try:
            self.state_manager.remove_chart_state(self.symbol)
            logger.info(f"Cleared saved state for {self.symbol}")

        except Exception as e:
            logger.error(f"Failed to clear saved state: {e}")

    def enable_auto_save(self, enabled: bool = True):
        """Enable or disable automatic state saving.

        Args:
            enabled: Whether to enable auto-save
        """
        self._auto_save_enabled = enabled

        # Also enable/disable on chart widget
        if hasattr(self.chart_widget, 'enable_auto_save_state'):
            self.chart_widget.enable_auto_save_state(enabled)

        logger.info(f"Auto-save {'enabled' if enabled else 'disabled'} for {self.symbol}")

    def _save_window_state(self):
        """Save window-specific state (geometry, splitters, etc.)."""
        try:
            if not self._auto_save_enabled:
                return

            # Get or create chart state
            chart_state = self.state_manager.load_chart_state(self.symbol)
            if not chart_state:
                chart_state = ChartState(
                    symbol=self.symbol,
                    timeframe="1D",
                    chart_type=self.chart_type.value if hasattr(self.chart_type, 'value') else str(self.chart_type)
                )

            # Update window state
            chart_state.window_geometry = self.saveGeometry()
            chart_state.window_state = self.saveState()

            # Save to manager
            self.state_manager.save_chart_state(
                self.symbol,
                chart_state,
                auto_save=True
            )

        except Exception as e:
            logger.error(f"Failed to save window state: {e}")

    def _restore_window_state(self) -> bool:
        """Restore window-specific state.

        Returns:
            True if state was restored
        """
        try:
            chart_state = self.state_manager.load_chart_state(self.symbol)
            if not chart_state:
                return False

            # Restore window geometry
            if chart_state.window_geometry:
                self.restoreGeometry(chart_state.window_geometry)

            # Restore window state (toolbars, docks)
            if chart_state.window_state:
                self.restoreState(chart_state.window_state)

            logger.debug(f"Restored window state for {self.symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore window state: {e}")
            return False

    def _schedule_auto_save(self, delay_ms: int = 2000):
        """Schedule an auto-save with debouncing."""
        if self._auto_save_enabled:
            self._state_save_timer.start(delay_ms)

    # Event handlers
    def resizeEvent(self, event):
        """Handle window resize - trigger auto-save."""
        super().resizeEvent(event)
        self._schedule_auto_save(delay_ms=3000)  # Longer delay for resize

    def moveEvent(self, event):
        """Handle window move - trigger auto-save."""
        super().moveEvent(event)
        self._schedule_auto_save(delay_ms=3000)  # Longer delay for move

    def closeEvent(self, event: QCloseEvent):
        """Handle window close - save state immediately."""
        try:
            # Force immediate save on close
            if self._auto_save_enabled:
                self.save_state_now()

            # Emit signal
            self.chart_closed.emit(self.symbol)

            logger.info(f"Chart window closed for {self.symbol}")

        except Exception as e:
            logger.error(f"Error during close: {e}")

        # Accept close event
        event.accept()

    def showEvent(self, event):
        """Handle window show - emit opened signal."""
        super().showEvent(event)
        self.chart_opened.emit(self.symbol)

    # Signal handlers
    @pyqtSlot(str)
    def _on_chart_state_saved(self, symbol: str):
        """Handle chart state saved signal."""
        if symbol == self.symbol:
            self.statusBar().showMessage(f"Chart state saved for {symbol}", 2000)

    @pyqtSlot(str, dict)
    def _on_chart_state_loaded(self, symbol: str, state: Dict[str, Any]):
        """Handle chart state loaded signal."""
        if symbol == self.symbol:
            self.statusBar().showMessage(f"Chart state restored for {symbol}", 2000)

    @pyqtSlot(str)
    def _on_state_manager_saved(self, symbol: str):
        """Handle state manager saved signal."""
        if symbol == self.symbol:
            logger.debug(f"State manager saved state for {symbol}")

    @pyqtSlot(str, dict)
    def _on_state_manager_loaded(self, symbol: str, state: Dict[str, Any]):
        """Handle state manager loaded signal."""
        if symbol == self.symbol:
            logger.debug(f"State manager loaded state for {symbol}")

    # Public API for external integration
    def get_chart_widget(self):
        """Get the chart widget instance."""
        return self.chart_widget

    def set_symbol(self, symbol: str):
        """Change the symbol and load appropriate state.

        Args:
            symbol: New symbol to display
        """
        old_symbol = self.symbol

        # Save current state
        if self._auto_save_enabled:
            self.save_state_now()

        # Update symbol
        self.symbol = symbol
        self.setWindowTitle(f"Chart - {symbol}")

        # Update chart widget
        if hasattr(self.chart_widget, 'set_symbol'):
            self.chart_widget.set_symbol(symbol)
        elif hasattr(self.chart_widget, 'current_symbol'):
            self.chart_widget.current_symbol = symbol

        # Load new state
        QTimer.singleShot(500, self.load_state_now)

        logger.info(f"Changed symbol from {old_symbol} to {symbol}")

    def get_symbol(self) -> str:
        """Get current symbol."""
        return self.symbol

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state for debugging."""
        try:
            chart_state = self.state_manager.load_chart_state(self.symbol)
            if not chart_state:
                return {"symbol": self.symbol, "has_saved_state": False}

            return {
                "symbol": self.symbol,
                "has_saved_state": True,
                "timeframe": chart_state.timeframe,
                "chart_type": chart_state.chart_type,
                "indicator_count": len(chart_state.indicators) if chart_state.indicators else 0,
                "has_window_geometry": chart_state.window_geometry is not None,
                "has_view_range": chart_state.view_range is not None,
                "has_pane_layout": chart_state.pane_layout is not None,
                "auto_save_enabled": self._auto_save_enabled
            }

        except Exception as e:
            return {"symbol": self.symbol, "error": str(e)}


class ChartWindowManager(QObject):
    """Manager for multiple enhanced chart windows."""

    def __init__(self):
        super().__init__()
        self.windows: Dict[str, EnhancedChartWindow] = {}
        self.state_manager = get_chart_state_manager()

    def open_chart(self, symbol: str, chart_type: ChartType = ChartType.AUTO) -> EnhancedChartWindow:
        """Open or focus chart window for symbol.

        Args:
            symbol: Trading symbol
            chart_type: Chart type to create

        Returns:
            Chart window instance
        """
        try:
            # Check if window already exists
            if symbol in self.windows:
                window = self.windows[symbol]
                try:
                    # Verify window is still valid
                    if window.isVisible():
                        window.show()
                        window.raise_()
                        window.activateWindow()
                        logger.info(f"Focused existing chart window for {symbol}")
                        return window
                except RuntimeError:
                    # Window was deleted
                    logger.warning(f"Existing window for {symbol} was deleted, creating new one")
                    del self.windows[symbol]

            # Create new window
            logger.info(f"Creating new chart window for {symbol} with type {chart_type}")
            window = EnhancedChartWindow(symbol, chart_type)

            # Connect close signal to cleanup
            window.chart_closed.connect(self._on_window_closed)

            # Store and show
            logger.info(f"Storing window in manager for {symbol}")
            self.windows[symbol] = window

            logger.info(f"Calling window.show() for {symbol}")
            # Show window with explicit flags
            window.show()

            logger.info(f"Calling window.raise_() for {symbol}")
            window.raise_()

            logger.info(f"Calling window.activateWindow() for {symbol}")
            window.activateWindow()

            logger.info(f"Setting window state for {symbol}")
            # Force window to front on Windows
            window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)

            logger.info(f"✅ Opened new chart window for {symbol}")
            return window

        except Exception as e:
            logger.error(f"❌ Failed to open chart window for {symbol}: {e}", exc_info=True)
            # Retry once with a safe PyQtGraph chart if auto/advanced chart creation fails
            if chart_type != ChartType.PYQTGRAPH:
                logger.warning(f"Retrying {symbol} with PyQtGraph fallback after failure")
                return self.open_chart(symbol, ChartType.PYQTGRAPH)
            # Re-raise to be caught by caller after fallback failure
            raise

    def close_chart(self, symbol: str):
        """Close chart window for symbol.

        Args:
            symbol: Symbol to close
        """
        if symbol in self.windows:
            window = self.windows[symbol]
            window.close()

    def close_all_charts(self):
        """Close all open chart windows."""
        for window in list(self.windows.values()):
            window.close()

    def get_chart_window(self, symbol: str) -> Optional[EnhancedChartWindow]:
        """Get chart window for symbol if it exists.

        Args:
            symbol: Symbol to get window for

        Returns:
            Chart window or None
        """
        return self.windows.get(symbol)

    def list_open_charts(self) -> list:
        """Get list of symbols with open chart windows."""
        return list(self.windows.keys())

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of all chart window states."""
        return {
            symbol: window.get_state_summary()
            for symbol, window in self.windows.items()
        }

    @pyqtSlot(str)
    def _on_window_closed(self, symbol: str):
        """Handle chart window closed."""
        if symbol in self.windows:
            del self.windows[symbol]
            logger.info(f"Cleaned up chart window for {symbol}")


# Global chart window manager instance
_chart_window_manager = None

def get_chart_window_manager() -> ChartWindowManager:
    """Get global chart window manager."""
    global _chart_window_manager
    if _chart_window_manager is None:
        _chart_window_manager = ChartWindowManager()
    return _chart_window_manager
