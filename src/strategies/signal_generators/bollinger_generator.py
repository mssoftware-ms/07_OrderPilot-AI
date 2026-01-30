"""Bollinger Bands signal generator.

Handles BB band touch/reversion signals.
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class BollingerSignalGenerator(BaseSignalGenerator):
    """Generate signals based on Bollinger Bands touches.

    Logic:
    - Entry Long: Price touches lower band (oversold)
    - Entry Short: Price touches upper band (overbought)
    - Exit Long: Price crosses above middle band
    - Exit Short: Price crosses below middle band

    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['BB']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'BB'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate Bollinger Bands signals.

        Requires df columns: 'bb_lower', 'bb_middle', 'bb_upper', 'close'

        Complexity: CC = 4
        """
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Price touches lower band (oversold)
            signals = df['close'] <= df['bb_lower']

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Price touches upper band (overbought)
            signals = df['close'] >= df['bb_upper']

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: Price crosses above middle or upper band
            signals = df['close'] >= df['bb_middle']

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: Price crosses below middle or lower band
            signals = df['close'] <= df['bb_middle']

        return signals
