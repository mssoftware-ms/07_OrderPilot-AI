"""Bollinger Bands calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class BollingerCalculator(BaseIndicatorCalculator):
    """Bollinger Bands calculator. CC=3"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'BB'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 20)
        std = params.get('std', 2.0)

        bbands = ta.bbands(df['close'], length=period, std=std)

        if bbands is not None and not bbands.empty and len(bbands.columns) >= 3:
            result_df['bb_lower'] = bbands.iloc[:, 0]
            result_df['bb_middle'] = bbands.iloc[:, 1]
            result_df['bb_upper'] = bbands.iloc[:, 2]
            result_df['indicator_value'] = bbands.iloc[:, 1]
        else:
            result_df['bb_lower'] = df['close'] * 0.98
            result_df['bb_middle'] = df['close']
            result_df['bb_upper'] = df['close'] * 1.02
            result_df['indicator_value'] = df['close']

        return result_df.dropna()
