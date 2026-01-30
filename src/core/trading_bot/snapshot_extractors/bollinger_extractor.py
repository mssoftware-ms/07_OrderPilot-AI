"""
Bollinger Bands Field Extractor.

Extracts Bollinger Band values and calculates %B and width.
"""

from typing import Dict, Any
import pandas as pd
from .base_extractor import BaseFieldExtractor


class BollingerExtractor(BaseFieldExtractor):
    """Extracts Bollinger Bands indicator fields."""

    def extract(self, current: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract Bollinger Bands fields.

        Fields:
        - bb_upper, bb_middle, bb_lower: Band values
        - bb_pct_b: Percent B indicator
        - bb_width: Bandwidth indicator

        Args:
            current: Current row
            df: Complete DataFrame

        Returns:
            Dict with Bollinger Band fields
        """
        price = self._to_float(current.get("close", 0))

        bb_upper = self._get_value(current, "bb_upper", "BB_upper")
        bb_middle = self._get_value(current, "bb_middle", "BB_middle")
        bb_lower = self._get_value(current, "bb_lower", "BB_lower")

        bb_pct_b, bb_width = self._calculate_bb_metrics(
            price, bb_upper, bb_middle, bb_lower
        )

        return {
            "bb_upper": self._to_float(bb_upper),
            "bb_middle": self._to_float(bb_middle),
            "bb_lower": self._to_float(bb_lower),
            "bb_pct_b": bb_pct_b,
            "bb_width": bb_width,
        }

    def _calculate_bb_metrics(
        self,
        price: float,
        bb_upper: Any,
        bb_middle: Any,
        bb_lower: Any
    ) -> tuple[float | None, float | None]:
        """
        Calculate Bollinger Band metrics.

        Args:
            price: Current price
            bb_upper: Upper band
            bb_middle: Middle band
            bb_lower: Lower band

        Returns:
            Tuple of (bb_pct_b, bb_width)
        """
        bb_pct_b = None
        bb_width = None

        if not all([bb_upper, bb_lower, bb_middle, price]):
            return bb_pct_b, bb_width

        upper_float = self._to_float(bb_upper)
        lower_float = self._to_float(bb_lower)
        middle_float = self._to_float(bb_middle)

        if not all([upper_float, lower_float, middle_float]):
            return bb_pct_b, bb_width

        # Calculate %B
        if upper_float != lower_float:
            bb_pct_b = (price - lower_float) / (upper_float - lower_float)

        # Calculate width
        if middle_float != 0:
            bb_width = (upper_float - lower_float) / middle_float

        return bb_pct_b, bb_width
