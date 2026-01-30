"""Stochastic Oscillator calculator.

Calculates %K and %D lines for overbought/oversold conditions.

Extracted from: indicator_optimization_thread._calculate_indicator()
Original Lines: 635-651 (CC contribution: ~3)
New Complexity: CC=3 (column extraction logic)
"""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class StochasticCalculator(BaseIndicatorCalculator):
    """Calculator for Stochastic Oscillator.

    Measures momentum by comparing closing price to price range:
    - %K: Fast stochastic (position within range)
    - %D: Slow stochastic (SMA of %K)
    - Values 0-100: >80 overbought, <20 oversold

    Complexity: CC=3 (column extraction branches)
    """

    def can_calculate(self, indicator_type: str) -> bool:
        """Check if this calculator handles STOCH."""
        return indicator_type == 'STOCH'

    def calculate(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate Stochastic Oscillator.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            params: {
                'k_period': int - %K period (default: 14),
                'd_period': int - %D period (default: 3)
            }

        Returns:
            DataFrame with:
            - 'indicator_value': %K line
            - 'stoch_d': %D line (if available before dropna)
        """
        result_df = df.copy()

        k_period = params.get('k_period', 14)
        d_period = params.get('d_period', 3)

        stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)

        if stoch is not None and not stoch.empty:
            # Stochastic returns %K and %D columns
            k_cols = [c for c in stoch.columns if 'K' in c.upper() and 'D' not in c]
            d_cols = [c for c in stoch.columns if 'D' in c.upper()]

            if k_cols:
                result_df['indicator_value'] = stoch[k_cols[0]]
                if d_cols:
                    result_df['stoch_d'] = stoch[d_cols[0]]
            else:
                result_df['indicator_value'] = 50.0
        else:
            result_df['indicator_value'] = 50.0

        return result_df.dropna()
