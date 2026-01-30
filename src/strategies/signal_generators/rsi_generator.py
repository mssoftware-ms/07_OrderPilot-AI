"""RSI (Relative Strength Index) signal generator.

Handles RSI overbought/oversold signals for entries and exits.
Extracted from _generate_signals() monster function (CC=157).

Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class RSISignalGenerator(BaseSignalGenerator):
    """Generate signals based on RSI overbought/oversold levels.

    Logic:
    - Entry Long: RSI < 30 (oversold)
    - Entry Short: RSI > 70 (overbought)
    - Exit Long: RSI > 70 (overbought)
    - Exit Short: RSI < 30 (oversold)

    Complexity: CC = 4 (vs original contribution to CC=157)
    """

    @property
    def supported_indicators(self) -> List[str]:
        """RSI indicator type."""
        return ['RSI']

    def can_handle(self, indicator_type: str) -> bool:
        """Check if this is RSI indicator."""
        return indicator_type == 'RSI'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate RSI-based trading signals.

        Args:
            df: DataFrame with 'indicator_value' column containing RSI values
            indicator_type: Must be 'RSI'
            test_type: 'entry' or 'exit'
            trade_side: 'long' or 'short'

        Returns:
            Boolean Series with signals (True = signal fired)

        Complexity: CC = 4
        """
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: RSI < 30 (oversold)
            signals = df['indicator_value'] < 30

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: RSI > 70 (overbought)
            signals = df['indicator_value'] > 70

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: RSI > 70 (overbought)
            signals = df['indicator_value'] > 70

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: RSI < 30 (oversold)
            signals = df['indicator_value'] < 30

        return signals
