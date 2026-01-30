"""Parabolic SAR calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class PSARCalculator(BaseIndicatorCalculator):
    """PSAR calculator. CC=3"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'PSAR'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        accel = params.get('accel', 0.02)
        max_accel = params.get('max_accel', 0.2)

        psar = ta.psar(df['high'], df['low'], af=accel, max_af=max_accel)

        if psar is not None and not psar.empty:
            numeric_cols = [c for c in psar.columns if psar[c].dtype in ['float64', 'float32']]
            result_df['indicator_value'] = psar[numeric_cols[0]] if numeric_cols else df['close']
        else:
            result_df['indicator_value'] = df['close']

        return result_df.dropna()
