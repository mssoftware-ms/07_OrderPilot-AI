"""Base class for indicator calculators.

All indicator calculators must inherit from this base and implement:
- can_calculate(): Check if this calculator handles the indicator type
- calculate(): Perform the actual calculation

Design Pattern: Strategy Pattern with Factory registration
Replaces: 197-line if-elif chain in _calculate_indicator() (CC=86)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class BaseIndicatorCalculator(ABC):
    """Abstract base class for indicator calculations.

    Each concrete calculator:
    1. Handles one or more related indicator types
    2. Implements can_calculate() to identify its indicators
    3. Implements calculate() to compute indicator values
    4. Returns DataFrame with 'indicator_value' column + any auxiliary columns
    5. Must call dropna() on result before returning

    Complexity: CC = 1-3 per calculator (vs. CC=86 for monolithic function)
    """

    @abstractmethod
    def can_calculate(self, indicator_type: str) -> bool:
        """Check if this calculator can handle the indicator type.

        Args:
            indicator_type: Indicator type string (e.g., 'RSI', 'MACD', 'SMA')

        Returns:
            True if this calculator handles the indicator type

        Example:
            >>> calc = RSICalculator()
            >>> calc.can_calculate('RSI')
            True
            >>> calc.can_calculate('MACD')
            False
        """
        pass

    @abstractmethod
    def calculate(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate indicator values.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            params: Indicator parameters (e.g., {'period': 14} for RSI)

        Returns:
            DataFrame with original OHLCV + 'indicator_value' column (+ optional auxiliary columns)
            MUST call dropna() before returning to match original behavior

        Raises:
            ValueError: If required columns are missing or params are invalid

        Example:
            >>> df = pd.DataFrame({'close': [100, 101, 102, ...]})
            >>> calc = RSICalculator()
            >>> result = calc.calculate(df, {'period': 14})
            >>> 'indicator_value' in result.columns
            True
        """
        pass
