"""MACD (Moving Average Convergence Divergence) signal generator.

Handles MACD zero-line crossover signals.
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class MACDSignalGenerator(BaseSignalGenerator):
    """Generate signals based on MACD zero-line crossovers.

    Logic:
    - Entry Long: MACD crosses above 0
    - Entry Short: MACD crosses below 0
    - Exit Long: MACD crosses below 0
    - Exit Short: MACD crosses above 0

    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['MACD']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'MACD'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate MACD crossover signals.

        Complexity: CC = 4
        """
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: MACD crosses above 0
            signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: MACD crosses below 0
            signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: MACD crosses below 0
            signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: MACD crosses above 0
            signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)

        return signals
