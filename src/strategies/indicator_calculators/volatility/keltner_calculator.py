"""Keltner Channels calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class KeltnerCalculator(BaseIndicatorCalculator):
    """Keltner Channels calculator. CC=3"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'KC'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 20)
        mult = params.get('mult', 2.0)

        kc = ta.kc(df['high'], df['low'], df['close'], length=period, scalar=mult)

        if kc is not None and not kc.empty and len(kc.columns) >= 3:
            result_df['kc_lower'] = kc.iloc[:, 0]
            result_df['kc_middle'] = kc.iloc[:, 1]
            result_df['kc_upper'] = kc.iloc[:, 2]
            result_df['indicator_value'] = kc.iloc[:, 1]
        else:
            result_df['indicator_value'] = df['close']

        return result_df.dropna()
