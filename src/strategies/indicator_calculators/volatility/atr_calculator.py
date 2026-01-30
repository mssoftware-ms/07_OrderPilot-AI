"""ATR (Average True Range) calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class ATRCalculator(BaseIndicatorCalculator):
    """ATR calculator. CC=2"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'ATR'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 14)
        atr = ta.atr(df['high'], df['low'], df['close'], length=period)
        result_df['indicator_value'] = atr if atr is not None else df['close'] * 0.02
        return result_df.dropna()
