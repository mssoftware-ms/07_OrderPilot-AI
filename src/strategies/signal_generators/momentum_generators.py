"""Momentum indicator signal generators.

Handles: CCI (Commodity Channel Index)
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class CCISignalGenerator(BaseSignalGenerator):
    """Commodity Channel Index signal generator.

    Logic: CCI overbought/oversold crossovers
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['CCI']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'CCI'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate CCI signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: CCI crosses above -100 (oversold recovery)
            signals = (df['indicator_value'] > -100) & (df['indicator_value'].shift(1) <= -100)

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: CCI crosses below 100 (overbought reversal)
            signals = (df['indicator_value'] < 100) & (df['indicator_value'].shift(1) >= 100)

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: CCI crosses below 100
            signals = (df['indicator_value'] < 100) & (df['indicator_value'].shift(1) >= 100)

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: CCI crosses above -100
            signals = (df['indicator_value'] > -100) & (df['indicator_value'].shift(1) <= -100)

        return signals
