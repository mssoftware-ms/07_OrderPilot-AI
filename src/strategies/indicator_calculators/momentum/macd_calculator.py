"""MACD (Moving Average Convergence Divergence) calculator.

Calculates MACD line, signal line, and histogram for trend following.

Extracted from: indicator_optimization_thread._calculate_indicator()
Original Lines: 506-521 (CC contribution: ~3)
New Complexity: CC=3 (additional column extraction logic)
"""

from typing import Dict, Any
import pandas as pd
import pandas_ta as ta
from ..base_calculator import BaseIndicatorCalculator


class MACDCalculator(BaseIndicatorCalculator):
    """Calculator for Moving Average Convergence Divergence (MACD).

    MACD shows trend direction and momentum:
    - MACD line: Fast EMA - Slow EMA
    - Signal line: EMA of MACD line
    - Histogram: MACD - Signal

    Complexity: CC=3 (column extraction branches)
    """

    def can_calculate(self, indicator_type: str) -> bool:
        """Check if this calculator handles MACD."""
        return indicator_type == 'MACD'

    def calculate(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate MACD with given parameters.

        Args:
            df: DataFrame with 'close' column
            params: {
                'fast': int - Fast EMA period (default: 12),
                'slow': int - Slow EMA period (default: 26),
                'signal': int - Signal line period (default: 9)
            }

        Returns:
            DataFrame with:
            - 'indicator_value': MACD line
            - 'macd_signal': Signal line (if available before dropna)
        """
        result_df = df.copy()

        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)

        if macd is not None and not macd.empty:
            # MACD returns 3 columns: MACD line, signal, histogram
            # Find MACD line column (excludes 'signal' and 'histogram' in name)
            macd_cols = [c for c in macd.columns if 'MACD' in c and 'signal' not in c.lower() and 'histogram' not in c.lower()]
            result_df['indicator_value'] = macd[macd_cols[0]] if macd_cols else 0

            # Store signal line if available
            signal_cols = [c for c in macd.columns if 'signal' in c.lower()]
            if signal_cols:
                result_df['macd_signal'] = macd[signal_cols[0]]
        else:
            result_df['indicator_value'] = 0

        return result_df.dropna()
