"""
Price and Timestamp Field Extractor.

Extracts basic price and timestamp information.
"""

from typing import Dict, Any
from datetime import datetime, timezone
import pandas as pd
from .base_extractor import BaseFieldExtractor


class PriceTimestampExtractor(BaseFieldExtractor):
    """Extracts price and timestamp fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract price and timestamp fields.

        Fields:
        - current_price: Current close price
        - timestamp: Timestamp of current data

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with price and timestamp fields
        """
        price = self._to_float(current.get("close", 0))
        timestamp = self._extract_timestamp(current)

        return {
            "current_price": price if price else None,
            "timestamp": timestamp,
        }

    def _extract_timestamp(self, current: pd.Series) -> datetime:
        """
        Extract and normalize timestamp.

        Args:
            current: Current row

        Returns:
            Datetime object (current time if not in data)
        """
        timestamp = current.get("timestamp")

        if timestamp is None:
            return datetime.now(timezone.utc)

        if isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp)

        if isinstance(timestamp, datetime):
            return timestamp

        return datetime.now(timezone.utc)
