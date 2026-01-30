"""
Base Field Extractor for Indicator Snapshots.

Provides abstract interface for field extraction.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd


class BaseFieldExtractor(ABC):
    """
    Base class for indicator field extraction.

    Each extractor is responsible for extracting specific fields
    from a DataFrame row and performing associated calculations.
    """

    @abstractmethod
    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract fields from current DataFrame row.

        Args:
            current: Current row (typically df.iloc[-1])
            df: Complete DataFrame (for multi-row calculations if needed)

        Returns:
            Dict with extracted field names and values
        """
        pass

    def _get_value(
        self,
        current: pd.Series,
        *column_names: str,
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Get value from row, trying multiple column names.

        Args:
            current: DataFrame row
            column_names: Column names to try (in order)
            default: Default value if not found

        Returns:
            Value from first matching column, or default
        """
        for col in column_names:
            value = current.get(col)
            if value is not None:
                return value
        return default

    def _to_float(self, value: Any) -> Optional[float]:
        """
        Convert value to float, returning None if not possible.

        Args:
            value: Value to convert

        Returns:
            Float value or None
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
