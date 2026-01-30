"""
RSI (Relative Strength Index) Field Extractor.

Extracts RSI value and determines overbought/oversold state.
"""

from typing import Dict, Any, Optional
import pandas as pd
from .base_extractor import BaseFieldExtractor


class RSIExtractor(BaseFieldExtractor):
    """Extracts RSI indicator fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract RSI fields.

        Fields:
        - rsi_14: RSI value
        - rsi_state: "OVERBOUGHT" (>70), "OVERSOLD" (<30), "NEUTRAL"

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with RSI fields
        """
        rsi = self._get_value(current, "rsi_14", "RSI_14", "rsi")
        rsi_state = self._determine_rsi_state(rsi)

        return {
            "rsi_14": self._to_float(rsi),
            "rsi_state": rsi_state,
        }

    def _determine_rsi_state(self, rsi: Optional[float]) -> Optional[str]:
        """
        Determine RSI state based on value.

        Args:
            rsi: RSI value

        Returns:
            "OVERBOUGHT", "OVERSOLD", or "NEUTRAL"
        """
        if rsi is None:
            return None

        rsi_float = self._to_float(rsi)
        if rsi_float is None:
            return None

        if rsi_float > 70:
            return "OVERBOUGHT"
        elif rsi_float < 30:
            return "OVERSOLD"
        else:
            return "NEUTRAL"
