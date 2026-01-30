"""
ADX (Average Directional Index) Field Extractor.

Extracts ADX and directional indicator values.
"""

from typing import Dict, Any
import pandas as pd
from .base_extractor import BaseFieldExtractor


class ADXExtractor(BaseFieldExtractor):
    """Extracts ADX indicator fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract ADX fields.

        Fields:
        - adx_14: ADX value
        - plus_di: +DI value
        - minus_di: -DI value

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with ADX fields
        """
        adx = self._get_value(current, "adx_14", "ADX_14", "adx")
        plus_di = self._get_value(current, "plus_di", "+DI")
        minus_di = self._get_value(current, "minus_di", "-DI")

        return {
            "adx_14": self._to_float(adx),
            "plus_di": self._to_float(plus_di),
            "minus_di": self._to_float(minus_di),
        }
