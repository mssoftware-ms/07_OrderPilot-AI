"""ChartLayoutManager - Multi-Chart and Multi-Monitor Management.

Manages multiple chart windows across monitors for pre-trade analysis.
Supports saving/loading layout templates and automatic chart set opening.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QObject, pyqtSignal, QRect, QPoint
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)

# Default layouts directory
LAYOUTS_DIR = Path(__file__).parent.parent.parent.parent / "config" / "chart_layouts"


@dataclass
class ChartWindowConfig:
    """Configuration for a single chart window."""

    symbol: str
    timeframe: str  # e.g., "1T", "5T", "1H", "1D"
    period: str = "1M"  # How far back to load data
    monitor: int = 0  # Monitor index (0 = primary)
    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600
    indicators: list[str] = field(default_factory=list)
    auto_stream: bool = False  # Auto-start live streaming

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ChartWindowConfig":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ChartLayoutConfig:
    """Configuration for a complete chart layout (multiple windows)."""

    name: str
    description: str = ""
    windows: list[ChartWindowConfig] = field(default_factory=list)
    sync_crosshair: bool = True
    sync_time_range: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "windows": [w.to_dict() for w in self.windows],
            "sync_crosshair": self.sync_crosshair,
            "sync_time_range": self.sync_time_range,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChartLayoutConfig":
        """Create from dictionary."""
        windows = [ChartWindowConfig.from_dict(w) for w in data.get("windows", [])]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            windows=windows,
            sync_crosshair=data.get("sync_crosshair", True),
            sync_time_range=data.get("sync_time_range", False),
        )


class ChartLayoutManager(QObject):
    """Manages multiple chart windows for pre-trade analysis.

    Features:
    - Open multiple charts with different timeframes
    - Position windows on specific monitors
    - Save and load layout templates
    - Synchronize crosshair between charts
    - Auto-open predefined chart sets
    """

    # Signals
    layout_opened = pyqtSignal(str)  # layout name
    layout_closed = pyqtSignal()
    window_opened = pyqtSignal(object)  # ChartWindow
    window_closed = pyqtSignal(object)  # ChartWindow

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._active_windows: list["ChartWindow"] = []
        self._current_layout: ChartLayoutConfig | None = None
        self._layouts_dir = LAYOUTS_DIR
        self._history_manager: Any = None

        # Ensure layouts directory exists
        self._layouts_dir.mkdir(parents=True, exist_ok=True)

        # Create default layouts if none exist
        self._create_default_layouts()

    def set_history_manager(self, history_manager: Any) -> None:
        """Set the history manager for data loading."""
        self._history_manager = history_manager

    @property
    def active_windows(self) -> list["ChartWindow"]:
        """Get list of active chart windows."""
        return self._active_windows.copy()

    @property
    def current_layout(self) -> ChartLayoutConfig | None:
        """Get the current layout configuration."""
        return self._current_layout

    def get_available_monitors(self) -> list[dict]:
        """Get list of available monitors with their geometry."""
        screens = QApplication.screens()
        monitors = []
        for i, screen in enumerate(screens):
            geo = screen.geometry()
            monitors.append({
                "index": i,
                "name": screen.name(),
                "x": geo.x(),
                "y": geo.y(),
                "width": geo.width(),
                "height": geo.height(),
                "is_primary": screen == QApplication.primaryScreen(),
            })
        return monitors

    def get_monitor_geometry(self, monitor_index: int) -> QRect:
        """Get the geometry of a specific monitor."""
        screens = QApplication.screens()
        if 0 <= monitor_index < len(screens):
            return screens[monitor_index].geometry()
        # Fallback to primary screen
        return QApplication.primaryScreen().geometry()

    def open_layout(self, layout: ChartLayoutConfig, symbol: str | None = None) -> list["ChartWindow"]:
        """Open a chart layout with multiple windows.

        Args:
            layout: The layout configuration
            symbol: Optional symbol override for all charts (uses layout's symbols if None)

        Returns:
            List of opened ChartWindow instances
        """
        # Close any existing layout first
        self.close_all_windows()

        self._current_layout = layout
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
                self._active_windows.append(window)
                opened_windows.append(window)

                # Connect close event
                window.destroyed.connect(lambda w=window: self._on_window_destroyed(w))

                self.window_opened.emit(window)
                logger.info(f"Opened chart: {chart_symbol} @ {win_config.timeframe} on monitor {win_config.monitor}")

            except Exception as e:
                logger.error(f"Failed to open chart window: {e}", exc_info=True)

        # Setup crosshair sync if enabled
        if layout.sync_crosshair and len(opened_windows) > 1:
            self._setup_crosshair_sync(opened_windows)

        self.layout_opened.emit(layout.name)
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
        window = ChartWindow(symbol=symbol, history_manager=self._history_manager)

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

    def _position_window(self, window: "ChartWindow", config: ChartWindowConfig) -> None:
        """Position a window according to its configuration."""
        monitor_geo = self.get_monitor_geometry(config.monitor)

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
        if window in self._active_windows:
            self._active_windows.remove(window)
            self.window_closed.emit(window)

    def close_all_windows(self) -> None:
        """Close all active chart windows."""
        for window in self._active_windows.copy():
            try:
                window.close()
            except Exception as e:
                logger.error(f"Error closing window: {e}")

        self._active_windows.clear()
        self._current_layout = None
        self.layout_closed.emit()

    def save_layout(self, layout: ChartLayoutConfig) -> bool:
        """Save a layout configuration to file.

        Args:
            layout: The layout to save

        Returns:
            True if successful
        """
        try:
            filepath = self._layouts_dir / f"{layout.name}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(layout.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved layout: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save layout: {e}")
            return False

    def load_layout(self, name: str) -> ChartLayoutConfig | None:
        """Load a layout configuration from file.

        Args:
            name: Layout name (without .json extension)

        Returns:
            ChartLayoutConfig or None if not found
        """
        try:
            filepath = self._layouts_dir / f"{name}.json"
            if not filepath.exists():
                logger.warning(f"Layout not found: {filepath}")
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            return ChartLayoutConfig.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load layout: {e}")
            return None

    def get_available_layouts(self) -> list[str]:
        """Get list of available layout names."""
        layouts = []
        for filepath in self._layouts_dir.glob("*.json"):
            layouts.append(filepath.stem)
        return sorted(layouts)

    def delete_layout(self, name: str) -> bool:
        """Delete a saved layout.

        Args:
            name: Layout name to delete

        Returns:
            True if successful
        """
        try:
            filepath = self._layouts_dir / f"{name}.json"
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted layout: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete layout: {e}")
            return False

    def _create_default_layouts(self) -> None:
        """Create default layout templates if none exist."""
        if list(self._layouts_dir.glob("*.json")):
            return  # Layouts already exist

        self.save_layout(self._build_mtf_layout())
        self.save_layout(self._build_crypto_layout())
        self.save_layout(self._build_scalping_layout())
        self.save_layout(self._build_dual_monitor_layout())

        logger.info("Created default chart layouts")

    def _build_mtf_layout(self) -> ChartLayoutConfig:
        return ChartLayoutConfig(
            name="Multi-Timeframe-Analyse",
            description="Übergeordneter Trend mit 3 Zeitebenen für Pre-Trade Analyse",
            windows=[
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1D",
                    period="3M",
                    monitor=0,
                    x=0, y=0,
                    width=800, height=500,
                    indicators=["SMA", "RSI"],
                ),
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1H",
                    period="2W",
                    monitor=0,
                    x=800, y=0,
                    width=800, height=500,
                    indicators=["EMA", "MACD"],
                ),
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="5T",
                    period="2D",
                    monitor=0,
                    x=0, y=500,
                    width=1600, height=500,
                    indicators=["BB", "RSI"],
                    auto_stream=True,
                ),
            ],
            sync_crosshair=True,
        )

    def _build_crypto_layout(self) -> ChartLayoutConfig:
        return ChartLayoutConfig(
            name="Crypto-Trading",
            description="BTC und ETH parallel mit Live-Stream",
            windows=[
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1T",
                    period="1D",
                    monitor=0,
                    x=0, y=0,
                    width=960, height=800,
                    auto_stream=True,
                ),
                ChartWindowConfig(
                    symbol="ETH/USD",
                    timeframe="1T",
                    period="1D",
                    monitor=0,
                    x=960, y=0,
                    width=960, height=800,
                    auto_stream=True,
                ),
            ],
        )

    def _build_scalping_layout(self) -> ChartLayoutConfig:
        return ChartLayoutConfig(
            name="Aktien-Scalping",
            description="Schnelles Trading mit 1-Minuten Chart",
            windows=[
                ChartWindowConfig(
                    symbol="SPY",
                    timeframe="1T",
                    period="1D",
                    monitor=0,
                    x=0, y=0,
                    width=1200, height=900,
                    indicators=["EMA", "RSI", "MACD"],
                    auto_stream=True,
                ),
            ],
        )

    def _build_dual_monitor_layout(self) -> ChartLayoutConfig:
        return ChartLayoutConfig(
            name="Dual-Monitor-Setup",
            description="Charts auf 2 Monitoren verteilt",
            windows=[
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="1H",
                    period="1M",
                    monitor=0,
                    x=0, y=0,
                    width=1920, height=1080,
                    indicators=["SMA", "BB"],
                ),
                ChartWindowConfig(
                    symbol="BTC/USD",
                    timeframe="5T",
                    period="5D",
                    monitor=1,
                    x=0, y=0,
                    width=1920, height=540,
                    auto_stream=True,
                ),
                ChartWindowConfig(
                    symbol="ETH/USD",
                    timeframe="5T",
                    period="5D",
                    monitor=1,
                    x=0, y=540,
                    width=1920, height=540,
                    auto_stream=True,
                ),
            ],
            sync_crosshair=True,
        )

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
        layout = self.load_layout("Multi-Timeframe-Analyse")
        if not layout:
            logger.error("Multi-Timeframe-Analyse layout not found!")
            return []

        # Open with the specified symbol
        return self.open_layout(layout, symbol=symbol)

    def create_layout_from_current(self, name: str, description: str = "") -> ChartLayoutConfig | None:
        """Create a layout configuration from currently open windows.

        Args:
            name: Name for the new layout
            description: Optional description

        Returns:
            ChartLayoutConfig or None if no windows are open
        """
        if not self._active_windows:
            logger.warning("No windows open to create layout from")
            return None

        windows_config = []
        screens = QApplication.screens()

        for window in self._active_windows:
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
