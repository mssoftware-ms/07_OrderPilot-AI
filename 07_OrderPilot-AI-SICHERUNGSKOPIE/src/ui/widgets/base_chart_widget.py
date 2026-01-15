"""Base Chart Widget.

Provides shared functionality for chart widgets to reduce code duplication.
This is a foundation for future refactoring of chart widgets.
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import Optional

import pandas as pd
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class QWidgetABCMeta(type(QWidget), ABCMeta):
    """Combined metaclass to resolve conflict between QWidget and ABC."""
    pass


class BaseChartWidget(QWidget, metaclass=QWidgetABCMeta):
    """Abstract base class for chart widgets.

    Provides common functionality shared across different chart implementations:
    - embedded_tradingview_chart.py
    - lightweight_chart.py
    - chart_view.py

    Usage:
        Future chart widgets should inherit from this class and implement
        abstract methods for chart-specific rendering logic.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize base chart widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None
        self.current_symbol: Optional[str] = None

    @abstractmethod
    def load_data(self, data: pd.DataFrame, **kwargs):
        """Load OHLCV data into chart.

        Args:
            data: DataFrame with OHLCV columns and timestamp index
            **kwargs: Chart-specific options
        """
        pass

    @abstractmethod
    def update_indicators(self):
        """Update technical indicators on chart."""
        pass

    def _validate_ohlcv_data(self, data: pd.DataFrame) -> bool:
        """Validate that DataFrame contains required OHLCV columns.

        Args:
            data: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_cols)

    def _convert_bars_to_dataframe(self, bars: list) -> pd.DataFrame:
        """Convert market bars to pandas DataFrame.

        Args:
            bars: List of market bar objects with attributes:
                  timestamp, open, high, low, close, volume

        Returns:
            DataFrame with OHLCV data and timestamp index
        """
        if not bars:
            return pd.DataFrame()

        data_dict = {
            'timestamp': [bar.timestamp for bar in bars],
            'open': [float(bar.open) for bar in bars],
            'high': [float(bar.high) for bar in bars],
            'low': [float(bar.low) for bar in bars],
            'close': [float(bar.close) for bar in bars],
            'volume': [bar.volume for bar in bars]
        }

        df = pd.DataFrame(data_dict)
        df.set_index('timestamp', inplace=True)
        return df

    def clear(self):
        """Clear chart data."""
        self.data = None
        self.current_symbol = None
