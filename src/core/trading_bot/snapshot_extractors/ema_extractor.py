"""
EMA (Exponential Moving Average) Field Extractor.

Extracts EMA values and calculates distance from price.
"""

from typing import Dict, Any
import pandas as pd
from .base_extractor import BaseFieldExtractor


class EMAExtractor(BaseFieldExtractor):
    """Extracts EMA indicator fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract EMA fields.

        Fields:
        - ema_20, ema_50, ema_200: EMA values
        - ema_20_distance_pct: Percentage distance from price to EMA20

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with EMA fields
        """
        price = self._to_float(current.get("close", 0))

        # Extract EMA values
        ema20 = self._get_value(current, "ema_20", "EMA_20")
        ema50 = self._get_value(current, "ema_50", "EMA_50")
        ema200 = self._get_value(current, "ema_200", "EMA_200")

        # Calculate EMA distance
        ema20_dist = None
        if ema20 is not None and price:
            ema20_float = self._to_float(ema20)
            if ema20_float and ema20_float != 0:
                ema20_dist = ((price - ema20_float) / ema20_float) * 100

        return {
            "ema_20": self._to_float(ema20),
            "ema_50": self._to_float(ema50),
            "ema_200": self._to_float(ema200),
            "ema_20_distance_pct": self._to_float(ema20_dist),
        }
