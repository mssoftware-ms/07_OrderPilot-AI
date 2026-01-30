"""EMA (Exponential Moving Average) calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class EMACalculator(BaseIndicatorCalculator):
    """Exponential Moving Average calculator. CC=2"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'EMA'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 20)
        ema = ta.ema(df['close'], length=period)
        result_df['indicator_value'] = ema if ema is not None else df['close']
        return result_df.dropna()
