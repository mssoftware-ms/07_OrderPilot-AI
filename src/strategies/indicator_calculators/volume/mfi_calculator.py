"""MFI (Money Flow Index) calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class MFICalculator(BaseIndicatorCalculator):
    """Money Flow Index calculator. CC=2"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'MFI'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 14)
        mfi = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=period)
        result_df['indicator_value'] = mfi if mfi is not None else 50.0
        return result_df.dropna()
