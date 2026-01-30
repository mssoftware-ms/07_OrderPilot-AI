"""A/D Line (Accumulation/Distribution) calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class ADCalculator(BaseIndicatorCalculator):
    """Accumulation/Distribution Line calculator. CC=2"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'AD'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        ad = ta.ad(df['high'], df['low'], df['close'], df['volume'])
        result_df['indicator_value'] = ad if ad is not None else 0.0
        return result_df.dropna()
