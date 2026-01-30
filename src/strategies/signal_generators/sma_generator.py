"""SMA (Simple Moving Average) signal generator.

Handles price crossovers with SMA.
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class SMASignalGenerator(BaseSignalGenerator):
    """Generate signals based on price/SMA crossovers.

    Logic:
    - Entry Long: Price crosses above SMA
    - Entry Short: Price crosses below SMA
    - Exit Long: Price crosses below SMA
    - Exit Short: Price crosses above SMA

    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['SMA']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'SMA'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate SMA crossover signals.

        Complexity: CC = 4
        """
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Price crosses above SMA
            signals = (df['close'] > df['indicator_value']) & \
                      (df['close'].shift(1) <= df['indicator_value'].shift(1))

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Price crosses below SMA
            signals = (df['close'] < df['indicator_value']) & \
                      (df['close'].shift(1) >= df['indicator_value'].shift(1))

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: Price crosses below SMA
            signals = (df['close'] < df['indicator_value']) & \
                      (df['close'].shift(1) >= df['indicator_value'].shift(1))

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: Price crosses above SMA
            signals = (df['close'] > df['indicator_value']) & \
                      (df['close'].shift(1) <= df['indicator_value'].shift(1))

        return signals
