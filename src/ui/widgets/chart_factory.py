"""Chart Factory for OrderPilot-AI.

This module provides a unified interface for creating different types of charts,
eliminating the complexity of choosing between multiple chart implementations.
"""

import logging
from enum import Enum
from typing import Dict, Any

from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Available chart types."""
    PYQTGRAPH = "pyqtgraph"  # Basic PyQtGraph-based chart
    ADVANCED = "advanced"     # Advanced PyQtGraph chart with indicators
    TRADINGVIEW = "tradingview"  # Embedded TradingView chart
    LIGHTWEIGHT = "lightweight"  # Lightweight charts library
    AUTO = "auto"            # Automatically choose best available


class ChartFactory:
    """Factory for creating chart widgets."""

    @staticmethod
    def create_chart(
        chart_type: ChartType = ChartType.AUTO,
        symbol: str = "AAPL",
        **kwargs
    ) -> QWidget:
        """Create a chart widget of the specified type.

        Args:
            chart_type: Type of chart to create
            symbol: Trading symbol
            **kwargs: Additional chart-specific parameters

        Returns:
            Chart widget instance

        Raises:
            ImportError: If required dependencies are not available
            ValueError: If chart type is not supported
        """
        if chart_type == ChartType.AUTO:
            chart_type = ChartFactory._determine_best_chart_type()

        try:
            if chart_type == ChartType.PYQTGRAPH:
                return ChartFactory._create_pyqtgraph_chart(symbol, **kwargs)
            elif chart_type == ChartType.ADVANCED:
                return ChartFactory._create_advanced_chart(symbol, **kwargs)
            elif chart_type == ChartType.TRADINGVIEW:
                return ChartFactory._create_tradingview_chart(symbol, **kwargs)
            elif chart_type == ChartType.LIGHTWEIGHT:
                return ChartFactory._create_lightweight_chart(symbol, **kwargs)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")

        except ImportError as e:
            logger.warning(f"Failed to create {chart_type.value} chart: {e}")
            # Fallback to basic chart
            if chart_type != ChartType.PYQTGRAPH:
                logger.info("Falling back to basic PyQtGraph chart")
                return ChartFactory._create_pyqtgraph_chart(symbol, **kwargs)
            else:
                raise

    @staticmethod
    def _determine_best_chart_type() -> ChartType:
        """Automatically determine the best available chart type.

        Returns:
            Best available chart type
        """
        # Prefer lightweight charts when the library and WebEngine are available
        try:
            import lightweight_charts  # noqa: F401
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
            logger.info("Using lightweight charts (best performance)")
            return ChartType.LIGHTWEIGHT
        except ImportError:
            pass

        # TradingView embedded charts (requires WebEngine)
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
            logger.info("Using TradingView embedded charts")
            return ChartType.TRADINGVIEW
        except ImportError:
            logger.warning("PyQt6-WebEngine not installed, falling back to PyQtGraph charts")

        # Check for PyQtGraph
        try:
            import pyqtgraph
            logger.info("Using PyQtGraph advanced charts")
            return ChartType.ADVANCED
        except ImportError:
            pass

        # Fallback to basic implementation
        logger.warning("No advanced charting libraries available, using basic implementation")
        return ChartType.PYQTGRAPH

    @staticmethod
    def _create_pyqtgraph_chart(symbol: str, **kwargs) -> QWidget:
        """Create basic PyQtGraph chart."""
        from .chart import ChartWidget

        chart = ChartWidget()
        chart.current_symbol = symbol
        return chart

    @staticmethod
    def _create_advanced_chart(symbol: str, **kwargs) -> QWidget:
        """Create advanced PyQtGraph chart with indicators."""
        from .chart_view import ChartView

        # Default configuration
        config_dict = {
            'symbol': symbol,
            'timeframe': kwargs.get('timeframe', '1T'),
            'show_volume': kwargs.get('show_volume', True),
            'show_indicators': kwargs.get('show_indicators', True),
            'theme': kwargs.get('theme', 'dark'),
            'update_interval': kwargs.get('update_interval', 1000)
        }

        from .chart_view import ChartConfig
        config = ChartConfig(**config_dict)

        chart = ChartView()
        chart.configure(config)
        return chart

    @staticmethod
    def _create_tradingview_chart(symbol: str, **kwargs) -> QWidget:
        """Create embedded TradingView chart."""
        from .embedded_tradingview_chart import EmbeddedTradingViewChart

        chart = EmbeddedTradingViewChart()
        if hasattr(chart, 'symbol_combo'):
            chart.symbol_combo.setCurrentText(symbol)
        else:
            chart.current_symbol = symbol

        # Apply configuration if provided
        if 'theme' in kwargs:
            chart.set_theme(kwargs['theme'])
        if 'timeframe' in kwargs:
            chart.set_timeframe(kwargs['timeframe'])

        return chart

    @staticmethod
    def _create_lightweight_chart(symbol: str, **kwargs) -> QWidget:
        """Create lightweight chart."""
        from .lightweight_chart import LightweightChartWidget

        chart = LightweightChartWidget(embedded=True)
        chart.set_symbol(symbol)
        return chart

    @staticmethod
    def get_available_chart_types() -> Dict[ChartType, bool]:
        """Get information about available chart types.

        Returns:
            Dictionary mapping chart types to availability
        """
        availability = {}

        # Check PyQtGraph
        try:
            import pyqtgraph
            availability[ChartType.PYQTGRAPH] = True
            availability[ChartType.ADVANCED] = True
        except ImportError:
            availability[ChartType.PYQTGRAPH] = False
            availability[ChartType.ADVANCED] = False

        # Check WebEngine for TradingView
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            availability[ChartType.TRADINGVIEW] = True
        except ImportError:
            availability[ChartType.TRADINGVIEW] = False

        # Check Lightweight Charts
        try:
            import lightweight_charts
            availability[ChartType.LIGHTWEIGHT] = True
        except ImportError:
            availability[ChartType.LIGHTWEIGHT] = False

        return availability

    @staticmethod
    def get_chart_features(chart_type: ChartType) -> Dict[str, Any]:
        """Get features supported by a chart type.

        Args:
            chart_type: Chart type to query

        Returns:
            Dictionary of supported features
        """
        features = {
            ChartType.PYQTGRAPH: {
                "performance": "Good",
                "indicators": "Basic",
                "real_time": True,
                "interactive": True,
                "web_based": False,
                "customizable": True
            },
            ChartType.ADVANCED: {
                "performance": "Good",
                "indicators": "Advanced",
                "real_time": True,
                "interactive": True,
                "web_based": False,
                "customizable": True
            },
            ChartType.TRADINGVIEW: {
                "performance": "Excellent",
                "indicators": "Professional",
                "real_time": True,
                "interactive": True,
                "web_based": True,
                "customizable": False
            },
            ChartType.LIGHTWEIGHT: {
                "performance": "Excellent",
                "indicators": "Good",
                "real_time": True,
                "interactive": True,
                "web_based": True,
                "customizable": True
            }
        }

        return features.get(chart_type, {})


# Convenience functions for backward compatibility
def create_chart(symbol: str = "AAPL", chart_type: str = "auto") -> QWidget:
    """Create a chart widget with simplified interface.

    Args:
        symbol: Trading symbol
        chart_type: Type of chart ("auto", "basic", "advanced", "tradingview", "lightweight")

    Returns:
        Chart widget
    """
    type_mapping = {
        "auto": ChartType.AUTO,
        "basic": ChartType.PYQTGRAPH,
        "advanced": ChartType.ADVANCED,
        "tradingview": ChartType.TRADINGVIEW,
        "lightweight": ChartType.LIGHTWEIGHT
    }

    chart_type_enum = type_mapping.get(chart_type.lower(), ChartType.AUTO)
    return ChartFactory.create_chart(chart_type_enum, symbol)


def get_recommended_chart_type() -> ChartType:
    """Get the recommended chart type for current environment.

    Returns:
        Recommended chart type
    """
    return ChartFactory._determine_best_chart_type()
