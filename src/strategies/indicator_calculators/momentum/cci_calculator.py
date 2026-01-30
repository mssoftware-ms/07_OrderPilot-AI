"""CCI (Commodity Channel Index) calculator.

Measures deviation from typical price range for trend identification.

Extracted from: indicator_optimization_thread._calculate_indicator()
Original Lines: 653-656 (CC contribution: ~2)
New Complexity: CC=2 (minimal branching)
"""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class CCICalculator(BaseIndicatorCalculator):
    """Calculator for Commodity Channel Index (CCI).

    Measures price deviation from statistical mean:
    - CCI > +100: Overbought / strong uptrend
    - CCI < -100: Oversold / strong downtrend
    - CCI between -100/+100: Normal range

    Complexity: CC=2 (minimal branching)
    """

    def can_calculate(self, indicator_type: str) -> bool:
        """Check if this calculator handles CCI."""
        return indicator_type == 'CCI'

    def calculate(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate CCI with given period.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            params: {'period': int} - CCI period (default: 20)

        Returns:
            DataFrame with 'indicator_value' column (CCI values)
        """
        result_df = df.copy()

        period = params.get('period', 20)
        cci = ta.cci(df['high'], df['low'], df['close'], length=period)
        result_df['indicator_value'] = cci if cci is not None else 0.0

        return result_df.dropna()
