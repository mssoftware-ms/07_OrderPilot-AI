"""Stochastic Oscillator signal generator.

Handles Stochastic overbought/oversold crossovers.
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class StochasticSignalGenerator(BaseSignalGenerator):
    """Generate signals based on Stochastic crossovers.

    Logic:
    - Entry Long: Stoch crosses above 20 (oversold recovery)
    - Entry Short: Stoch crosses below 80 (overbought reversal)
    - Exit Long: Stoch crosses below 80
    - Exit Short: Stoch crosses above 20

    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['STOCH']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'STOCH'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate Stochastic signals.

        Complexity: CC = 4
        """
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Stoch crosses above 20 (oversold recovery)
            signals = (df['indicator_value'] > 20) & (df['indicator_value'].shift(1) <= 20)

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Stoch crosses below 80 (overbought reversal)
            signals = (df['indicator_value'] < 80) & (df['indicator_value'].shift(1) >= 80)

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: Stoch crosses below 80 (overbought)
            signals = (df['indicator_value'] < 80) & (df['indicator_value'].shift(1) >= 80)

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: Stoch crosses above 20 (oversold)
            signals = (df['indicator_value'] > 20) & (df['indicator_value'].shift(1) <= 20)

        return signals
