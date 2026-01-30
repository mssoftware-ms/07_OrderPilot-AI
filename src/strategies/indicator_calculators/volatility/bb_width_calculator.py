"""Bollinger Band Width calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class BBWidthCalculator(BaseIndicatorCalculator):
    """BB Width calculator. CC=3"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'BB_WIDTH'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 20)
        std = params.get('std', 2.0)

        bbands = ta.bbands(df['close'], length=period, std=std)

        if bbands is not None and not bbands.empty and len(bbands.columns) >= 3:
            bb_lower = bbands.iloc[:, 0]
            bb_middle = bbands.iloc[:, 1]
            bb_upper = bbands.iloc[:, 2]
            result_df['indicator_value'] = (bb_upper - bb_lower) / bb_middle * 100
        else:
            result_df['indicator_value'] = 2.0

        return result_df.dropna()
