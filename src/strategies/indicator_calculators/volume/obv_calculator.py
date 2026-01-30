"""OBV (On Balance Volume) calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class OBVCalculator(BaseIndicatorCalculator):
    """On Balance Volume calculator. CC=2"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'OBV'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        obv = ta.obv(df['close'], df['volume'])
        result_df['indicator_value'] = obv if obv is not None else df['volume'].cumsum()
        return result_df.dropna()
