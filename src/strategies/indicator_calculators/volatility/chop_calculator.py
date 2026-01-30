"""Choppiness Index calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class ChopCalculator(BaseIndicatorCalculator):
    """CHOP calculator. CC=2"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'CHOP'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 14)
        chop = ta.chop(df['high'], df['low'], df['close'], length=period)
        result_df['indicator_value'] = chop if chop is not None else 50.0
        return result_df.dropna()
