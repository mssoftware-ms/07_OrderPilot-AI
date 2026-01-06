"""Chart Factory for OrderPilot-AI.

This module provides a unified interface for creating chart widgets.

REFACTORED V2.0:
- Removed redundant chart types (PYQTGRAPH, ADVANCED, LIGHTWEIGHT)
- Now only creates EmbeddedTradingViewChart (TradingView Lightweight Charts)
- ChartType enum kept for backward compatibility but all types map to TradingView

Previously supported chart types (NOW REMOVED):
- chart.py (ChartWidget) - replaced by EmbeddedTradingViewChart
- chart_view.py (ChartView) - replaced by EmbeddedTradingViewChart
- lightweight_chart.py (LightweightChartWidget) - replaced by EmbeddedTradingViewChart
"""

import logging
from enum import Enum
from typing import Dict, Any

from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Available chart types.

    NOTE: All types now map to TradingView implementation for consistency.
    These are kept for backward compatibility only.
    """
    # Deprecated - all map to TRADINGVIEW
    PYQTGRAPH = "pyqtgraph"      # Deprecated: maps to TradingView
    ADVANCED = "advanced"        # Deprecated: maps to TradingView
    LIGHTWEIGHT = "lightweight"  # Deprecated: maps to TradingView

    # Current implementation
    TRADINGVIEW = "tradingview"  # Embedded TradingView Lightweight Charts
    AUTO = "auto"                # Same as TRADINGVIEW


class ChartFactory:
    """Factory for creating chart widgets.

    All chart types now use EmbeddedTradingViewChart for consistency
    and best user experience.
    """

    @staticmethod
    def create_chart(
        chart_type: ChartType = ChartType.AUTO,
        symbol: str = "AAPL",
        history_manager=None,
        **kwargs
    ) -> QWidget:
        """Create a chart widget.

        Args:
            chart_type: Type of chart (all types now use TradingView)
            symbol: Trading symbol
            history_manager: Optional HistoryManager for data loading
            **kwargs: Additional chart parameters

        Returns:
            EmbeddedTradingViewChart widget instance

        Note:
            All chart_type values now create EmbeddedTradingViewChart.
            The parameter is kept for backward compatibility.
        """
        # Log deprecation warning for old chart types
        if chart_type in (ChartType.PYQTGRAPH, ChartType.ADVANCED, ChartType.LIGHTWEIGHT):
            logger.warning(
                f"ChartType.{chart_type.name} is deprecated. "
                f"Using TradingView chart instead for best performance."
            )

        return ChartFactory._create_tradingview_chart(
            symbol=symbol,
            history_manager=history_manager,
            **kwargs
        )

    @staticmethod
    def _create_tradingview_chart(
        symbol: str,
        history_manager=None,
        **kwargs
    ) -> QWidget:
        """Create embedded TradingView chart.

        CRITICAL: Creates provider-specific chart based on symbol:
        - Alpaca Crypto: BTC/USD, ETH/USD (symbols with /)
        - Bitunix: BTCUSDT, ETHUSDT (symbols with USDT/USDC)
        - Alpaca Stock: AAPL, MSFT (everything else)

        Args:
            symbol: Trading symbol
            history_manager: Optional HistoryManager for data loading
            **kwargs: Additional chart parameters

        Returns:
            AlpacaTradingViewChart or BitunixTradingViewChart instance
        """
        # CRITICAL: Detect provider based on symbol format
        is_bitunix = "USDT" in symbol or "USDC" in symbol
        is_alpaca = not is_bitunix  # Everything else is Alpaca (Stock + Crypto)

        # Import the correct chart class
        if is_bitunix:
            from .bitunix_tradingview_chart import BitunixTradingViewChart
            chart = BitunixTradingViewChart(history_manager=history_manager)
            import logging
            logging.getLogger(__name__).info(f"✅ Created BitunixTradingViewChart for {symbol}")
        else:
            from .alpaca_tradingview_chart import AlpacaTradingViewChart
            chart = AlpacaTradingViewChart(history_manager=history_manager)
            import logging
            logging.getLogger(__name__).info(f"✅ Created AlpacaTradingViewChart for {symbol}")

        # Set symbol
        if hasattr(chart, 'symbol_combo'):
            chart.symbol_combo.setCurrentText(symbol)
        chart.current_symbol = symbol

        # Apply configuration if provided
        if 'theme' in kwargs and hasattr(chart, 'set_theme'):
            chart.set_theme(kwargs['theme'])
        if 'timeframe' in kwargs and hasattr(chart, 'set_timeframe'):
            chart.set_timeframe(kwargs['timeframe'])

        return chart

    @staticmethod
    def get_available_chart_types() -> Dict[ChartType, bool]:
        """Get information about available chart types.

        Returns:
            Dictionary mapping chart types to availability

        Note:
            All types return True if WebEngine is available,
            as they all use the same TradingView implementation.
        """
        webengine_available = False
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
            webengine_available = True
        except ImportError:
            logger.error(
                "PyQt6-WebEngine not installed! Charts will not work. "
                "Install with: pip install PyQt6-WebEngine"
            )

        return {
            ChartType.PYQTGRAPH: webengine_available,  # Deprecated, uses TradingView
            ChartType.ADVANCED: webengine_available,   # Deprecated, uses TradingView
            ChartType.TRADINGVIEW: webengine_available,
            ChartType.LIGHTWEIGHT: webengine_available,  # Deprecated, uses TradingView
            ChartType.AUTO: webengine_available,
        }

    @staticmethod
    def get_chart_features(chart_type: ChartType = ChartType.AUTO) -> Dict[str, Any]:
        """Get features supported by chart implementation.

        Args:
            chart_type: Chart type (ignored, all use same features)

        Returns:
            Dictionary of supported features
        """
        # All chart types now have the same features
        return {
            "performance": "Excellent",
            "indicators": "Professional",
            "real_time": True,
            "interactive": True,
            "web_based": True,
            "customizable": True,
            "state_persistence": True,
            "multi_pane": True,
        }

    @staticmethod
    def _determine_best_chart_type() -> ChartType:
        """Determine the best available chart type.

        Returns:
            Always returns ChartType.TRADINGVIEW
        """
        return ChartType.TRADINGVIEW


# Convenience functions for backward compatibility
def create_chart(
    symbol: str = "AAPL",
    chart_type: str = "auto",
    history_manager=None
) -> QWidget:
    """Create a chart widget with simplified interface.

    Args:
        symbol: Trading symbol
        chart_type: Type of chart (ignored, always uses TradingView)
        history_manager: Optional HistoryManager for data loading

    Returns:
        EmbeddedTradingViewChart widget
    """
    return ChartFactory.create_chart(
        ChartType.AUTO,
        symbol,
        history_manager=history_manager
    )


def get_recommended_chart_type() -> ChartType:
    """Get the recommended chart type.

    Returns:
        Always ChartType.TRADINGVIEW
    """
    return ChartType.TRADINGVIEW
