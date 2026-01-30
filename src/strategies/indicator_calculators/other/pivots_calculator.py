"""Pivot Points calculator."""

from typing import Dict, Any
import pandas as pd
from ..base_calculator import BaseIndicatorCalculator


class PivotsCalculator(BaseIndicatorCalculator):
    """Pivot Points calculator. CC=3"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'PIVOTS'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        pivot_type = params.get('type', 'standard')

        if pivot_type == 'standard':
            pivot = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
        elif pivot_type == 'fibonacci':
            pivot = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
        else:  # camarilla
            pivot = df['close'].shift(1)

        result_df['indicator_value'] = pivot
        return result_df.dropna()
