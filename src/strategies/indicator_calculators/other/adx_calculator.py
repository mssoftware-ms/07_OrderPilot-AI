"""ADX (Average Directional Index) calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class ADXCalculator(BaseIndicatorCalculator):
    """ADX calculator. CC=3"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'ADX'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        period = params.get('period', 14)

        adx = ta.adx(df['high'], df['low'], df['close'], length=period)

        if adx is not None and not adx.empty:
            # Extract ADX value
            adx_cols = [c for c in adx.columns if 'ADX' in c and 'DMP' not in c and 'DMN' not in c]
            result_df['indicator_value'] = adx[adx_cols[0]] if adx_cols else 25.0

            # Also extract DI+ (DMP) and DI- (DMN) for di_diff calculation
            dmp_cols = [c for c in adx.columns if 'DMP' in c]
            dmn_cols = [c for c in adx.columns if 'DMN' in c]

            if dmp_cols:
                result_df['plus_di'] = adx[dmp_cols[0]]
            if dmn_cols:
                result_df['minus_di'] = adx[dmn_cols[0]]
        else:
            result_df['indicator_value'] = 25.0

        return result_df.dropna()
