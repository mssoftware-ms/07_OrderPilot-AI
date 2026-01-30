"""
ATR (Average True Range) Field Extractor.

Extracts ATR value and calculates percentage of price.
"""

from typing import Dict, Any
import pandas as pd
from .base_extractor import BaseFieldExtractor


class ATRExtractor(BaseFieldExtractor):
    """Extracts ATR indicator fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract ATR fields.

        Fields:
        - atr_14: ATR value
        - atr_percent: ATR as percentage of price

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with ATR fields
        """
        price = self._to_float(current.get("close", 0))
        atr = self._get_value(current, "atr_14", "ATR_14", "atr")

        atr_pct = None
        if atr is not None and price and price != 0:
            atr_float = self._to_float(atr)
            if atr_float is not None:
                atr_pct = (atr_float / price) * 100

        return {
            "atr_14": self._to_float(atr),
            "atr_percent": self._to_float(atr_pct),
        }
