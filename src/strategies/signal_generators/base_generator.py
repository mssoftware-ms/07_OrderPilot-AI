"""Base class for indicator-specific signal generation.

This module implements the Strategy Pattern for signal generation,
replacing the monster if-elif chain in _generate_signals().

Each concrete generator handles one or more related indicator types
with focused, testable logic (CC < 5 per class).
"""

from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class BaseSignalGenerator(ABC):
    """Base class for indicator-specific signal generation.

    Each concrete generator implements signal logic for one or more
    related indicator types, following the Single Responsibility Principle.

    Complexity Target: CC < 5 per generator
    """

    @abstractmethod
    def can_handle(self, indicator_type: str) -> bool:
        """Check if this generator can handle the indicator type.

        Args:
            indicator_type: The indicator type (e.g., 'RSI', 'MACD', 'SMA')

        Returns:
            True if this generator handles this indicator type
        """
        pass

    @abstractmethod
    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate trading signals based on indicator logic.

        Args:
            df: DataFrame with price data and indicator values
            indicator_type: The indicator type (e.g., 'RSI', 'MACD')
            test_type: 'entry' or 'exit'
            trade_side: 'long' or 'short'

        Returns:
            Boolean Series indicating signal points (True = signal fired)

        Complexity: Should be CC < 5 for each concrete implementation
        """
        pass

    @property
    @abstractmethod
    def supported_indicators(self) -> List[str]:
        """List of indicator types this generator supports.

        Returns:
            List of indicator type strings (e.g., ['RSI'])
        """
        pass
