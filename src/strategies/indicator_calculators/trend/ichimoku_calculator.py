"""Ichimoku Cloud calculator."""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class IchimokuCalculator(BaseIndicatorCalculator):
    """Ichimoku Cloud calculator. CC=4"""

    def can_calculate(self, indicator_type: str) -> bool:
        return indicator_type == 'ICHIMOKU'

    def calculate(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        result_df = df.copy()
        tenkan = params.get('tenkan', 9)
        kijun = params.get('kijun', 26)
        senkou = params.get('senkou', 52)

        ichimoku_result = ta.ichimoku(df['high'], df['low'], df['close'],
                                      tenkan=tenkan, kijun=kijun, senkou=senkou)

        if ichimoku_result is not None and len(ichimoku_result) > 0:
            ichimoku = ichimoku_result[0]
            if ichimoku is not None and not ichimoku.empty:
                isa_cols = [c for c in ichimoku.columns if 'ISA' in c or 'SPAN_A' in c.upper()]
                isb_cols = [c for c in ichimoku.columns if 'ISB' in c or 'SPAN_B' in c.upper()]

                if isa_cols and isb_cols:
                    result_df['indicator_value'] = ichimoku[isa_cols[0]]
                    result_df['cloud_top'] = ichimoku[isa_cols[0]].combine(ichimoku[isb_cols[0]], max)
                    result_df['cloud_bottom'] = ichimoku[isa_cols[0]].combine(ichimoku[isb_cols[0]], min)
                else:
                    result_df['indicator_value'] = df['close']
            else:
                result_df['indicator_value'] = df['close']
        else:
            result_df['indicator_value'] = df['close']

        return result_df.dropna()
