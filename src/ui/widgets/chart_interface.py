"""Chart Interface for OrderPilot-AI.

This module provides a common interface that all chart widgets should implement,
ensuring consistency across different chart implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import QObject, pyqtSignal


class IChartWidget(ABC):
    """Interface that all chart widgets should implement."""

    @abstractmethod
    def set_symbol(self, symbol: str) -> None:
        """Set the trading symbol for the chart.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTCUSD')
        """
        pass

    @abstractmethod
    def set_timeframe(self, timeframe: str) -> None:
        """Set the chart timeframe.

        Args:
            timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d')
        """
        pass

    @abstractmethod
    def update_data(self, bars_data: List[Tuple[Any, ...]], append: bool = True) -> None:
        """Update chart with new bar data.

        Args:
            bars_data: List of OHLCV tuples
            append: If True, append to existing data; if False, replace
        """
        pass

    @abstractmethod
    def add_indicator(self, indicator_type: str, **params) -> None:
        """Add a technical indicator to the chart.

        Args:
            indicator_type: Type of indicator (e.g., 'sma', 'rsi', 'macd')
            **params: Indicator-specific parameters
        """
        pass

    @abstractmethod
    def remove_indicator(self, indicator_id: str) -> None:
        """Remove a technical indicator from the chart.

        Args:
            indicator_id: Unique identifier of the indicator to remove
        """
        pass

    @abstractmethod
    def clear_data(self) -> None:
        """Clear all chart data."""
        pass

    @abstractmethod
    def set_theme(self, theme: str) -> None:
        """Set the chart theme.

        Args:
            theme: Theme name ('dark', 'light', etc.)
        """
        pass

    def zoom_to_fit(self) -> None:
        """Zoom chart to fit all data (optional implementation)."""
        pass

    def get_visible_range(self) -> Optional[Tuple[int, int]]:
        """Get the currently visible data range (optional implementation).

        Returns:
            Tuple of (start_index, end_index) or None if not supported
        """
        return None


class ChartSignals(QObject):
    """Common signals that chart widgets can emit."""

    # Data signals
    dataUpdated = pyqtSignal()
    dataCleared = pyqtSignal()

    # User interaction signals
    symbolChanged = pyqtSignal(str)  # symbol
    timeframeChanged = pyqtSignal(str)  # timeframe
    rangeChanged = pyqtSignal(int, int)  # start_index, end_index

    # Indicator signals
    indicatorAdded = pyqtSignal(str, dict)  # indicator_type, params
    indicatorRemoved = pyqtSignal(str)  # indicator_id

    # Error signals
    error = pyqtSignal(str)  # error_message
    warning = pyqtSignal(str)  # warning_message


class BaseChartWidget(IChartWidget):
    """Base implementation of chart widget interface.

    Provides common functionality and default implementations.
    """

    def __init__(self):
        """Initialize base chart widget."""
        self.signals = ChartSignals()
        self._symbol = "AAPL"
        self._timeframe = "1d"
        self._theme = "dark"
        self._indicators = {}
        self._data = []

    @property
    def symbol(self) -> str:
        """Get current symbol."""
        return self._symbol

    @property
    def timeframe(self) -> str:
        """Get current timeframe."""
        return self._timeframe

    @property
    def theme(self) -> str:
        """Get current theme."""
        return self._theme

    def set_symbol(self, symbol: str) -> None:
        """Set trading symbol."""
        if symbol != self._symbol:
            self._symbol = symbol
            self.signals.symbolChanged.emit(symbol)
            self._on_symbol_changed(symbol)

    def set_timeframe(self, timeframe: str) -> None:
        """Set timeframe."""
        if timeframe != self._timeframe:
            self._timeframe = timeframe
            self.signals.timeframeChanged.emit(timeframe)
            self._on_timeframe_changed(timeframe)

    def set_theme(self, theme: str) -> None:
        """Set theme."""
        if theme != self._theme:
            self._theme = theme
            self._on_theme_changed(theme)

    def clear_data(self) -> None:
        """Clear chart data."""
        self._data.clear()
        self.signals.dataCleared.emit()
        self._on_data_cleared()

    def get_data_count(self) -> int:
        """Get number of data points."""
        return len(self._data)

    def is_empty(self) -> bool:
        """Check if chart has no data."""
        return len(self._data) == 0

    # Protected methods for subclasses to override
    def _on_symbol_changed(self, symbol: str) -> None:
        """Called when symbol changes."""
        pass

    def _on_timeframe_changed(self, timeframe: str) -> None:
        """Called when timeframe changes."""
        pass

    def _on_theme_changed(self, theme: str) -> None:
        """Called when theme changes."""
        pass

    def _on_data_cleared(self) -> None:
        """Called when data is cleared."""
        pass

    def _emit_error(self, message: str) -> None:
        """Emit error signal."""
        self.signals.error.emit(message)

    def _emit_warning(self, message: str) -> None:
        """Emit warning signal."""
        self.signals.warning.emit(message)


class ChartCapabilities:
    """Describes capabilities of a chart implementation."""

    def __init__(
        self,
        supports_real_time: bool = True,
        supports_indicators: bool = True,
        supports_drawing_tools: bool = False,
        supports_themes: bool = True,
        supports_zoom: bool = True,
        max_data_points: Optional[int] = None,
        performance_rating: str = "good"  # poor, good, excellent
    ):
        """Initialize chart capabilities.

        Args:
            supports_real_time: Whether real-time updates are supported
            supports_indicators: Whether technical indicators are supported
            supports_drawing_tools: Whether drawing tools are supported
            supports_themes: Whether theme switching is supported
            supports_zoom: Whether zoom functionality is supported
            max_data_points: Maximum number of data points (None = unlimited)
            performance_rating: Performance rating (poor, good, excellent)
        """
        self.supports_real_time = supports_real_time
        self.supports_indicators = supports_indicators
        self.supports_drawing_tools = supports_drawing_tools
        self.supports_themes = supports_themes
        self.supports_zoom = supports_zoom
        self.max_data_points = max_data_points
        self.performance_rating = performance_rating

    def to_dict(self) -> Dict[str, Any]:
        """Convert capabilities to dictionary."""
        return {
            "supports_real_time": self.supports_real_time,
            "supports_indicators": self.supports_indicators,
            "supports_drawing_tools": self.supports_drawing_tools,
            "supports_themes": self.supports_themes,
            "supports_zoom": self.supports_zoom,
            "max_data_points": self.max_data_points,
            "performance_rating": self.performance_rating
        }


def register_chart_adapter(widget_class, capabilities: ChartCapabilities) -> None:
    """Register a chart widget with its capabilities.

    Args:
        widget_class: Chart widget class
        capabilities: Chart capabilities
    """
    # This would be used by a chart registry system
    # For now, just store as class attribute
    widget_class._chart_capabilities = capabilities


def get_chart_capabilities(widget_class) -> Optional[ChartCapabilities]:
    """Get capabilities of a chart widget class.

    Args:
        widget_class: Chart widget class

    Returns:
        Chart capabilities or None if not registered
    """
    return getattr(widget_class, '_chart_capabilities', None)