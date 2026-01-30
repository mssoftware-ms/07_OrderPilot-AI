"""
MACD (Moving Average Convergence Divergence) Field Extractor.

Extracts MACD values and determines crossover direction.
"""

from typing import Dict, Any, Optional
import pandas as pd
from .base_extractor import BaseFieldExtractor


class MACDExtractor(BaseFieldExtractor):
    """Extracts MACD indicator fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract MACD fields.

        Fields:
        - macd_line: MACD line value
        - macd_signal: Signal line value
        - macd_histogram: Histogram value
        - macd_crossover: "BULLISH" or "BEARISH"

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with MACD fields
        """
        macd = self._get_value(current, "macd", "MACD")
        macd_signal = self._get_value(current, "macd_signal", "MACD_signal")
        macd_hist = self._get_value(current, "macd_hist", "MACD_hist")

        macd_crossover = self._determine_macd_crossover(macd, macd_signal)

        return {
            "macd_line": self._to_float(macd),
            "macd_signal": self._to_float(macd_signal),
            "macd_histogram": self._to_float(macd_hist),
            "macd_crossover": macd_crossover,
        }

    def _determine_macd_crossover(
        self,
        macd: Optional[float],
        macd_signal: Optional[float]
    ) -> Optional[str]:
        """
        Determine MACD crossover direction.

        Args:
            macd: MACD line value
            macd_signal: Signal line value

        Returns:
            "BULLISH" or "BEARISH" or None
        """
        if macd is None or macd_signal is None:
            return None

        macd_float = self._to_float(macd)
        signal_float = self._to_float(macd_signal)

        if macd_float is None or signal_float is None:
            return None

        if macd_float > signal_float:
            return "BULLISH"
        else:
            return "BEARISH"
