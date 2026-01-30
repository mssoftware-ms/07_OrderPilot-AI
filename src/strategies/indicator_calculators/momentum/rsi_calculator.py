"""RSI (Relative Strength Index) calculator.

Calculates RSI oscillator (0-100 range) for momentum analysis.

Extracted from: indicator_optimization_thread._calculate_indicator()
Original Lines: 501-504 (CC contribution: ~2)
New Complexity: CC=2 (can_calculate + calculate)
"""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class RSICalculator(BaseIndicatorCalculator):
    """Calculator for Relative Strength Index (RSI).

    RSI measures momentum on a scale of 0-100:
    - RSI > 70: Overbought
    - RSI < 30: Oversold
    - RSI = 50: Neutral momentum

    Complexity: CC=2 (minimal branching)
    """

    def can_calculate(self, indicator_type: str) -> bool:
        """Check if this calculator handles RSI."""
        return indicator_type == 'RSI'

    def calculate(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate RSI with given period.

        Args:
            df: DataFrame with 'close' column
            params: {'period': int} - RSI period (default: 14)

        Returns:
            DataFrame with 'indicator_value' column (RSI values 0-100)
        """
        result_df = df.copy()

        period = params.get('period', 14)
        rsi = ta.rsi(df['close'], length=period)
        result_df['indicator_value'] = rsi if rsi is not None else 50.0

        return result_df.dropna()
