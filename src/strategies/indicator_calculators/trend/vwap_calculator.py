"""VWAP (Volume Weighted Average Price) calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class VWAPCalculator(BaseIndicatorCalculator):
    """VWAP calculator. CC=2"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'VWAP'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
        result_df['indicator_value'] = vwap if vwap is not None else df['close']
        return result_df.dropna()
