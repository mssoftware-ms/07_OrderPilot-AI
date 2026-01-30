"""Channel and breakout indicator signal generators.

Handles: KC (Keltner Channels)
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class KeltnerSignalGenerator(BaseSignalGenerator):
    """Keltner Channel signal generator.

    Logic: Price breakouts from Keltner Channel
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['KC']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'KC'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate Keltner Channel breakout signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Price breaks above upper Keltner
            signals = (df['close'] > df['kc_upper']) & \
                      (df['close'].shift(1) <= df['kc_upper'].shift(1))

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Price breaks below lower Keltner
            signals = (df['close'] < df['kc_lower']) & \
                      (df['close'].shift(1) >= df['kc_lower'].shift(1))

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: Price re-enters channel
            signals = (df['close'] < df['kc_upper']) & \
                      (df['close'].shift(1) >= df['kc_upper'].shift(1))

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: Price re-enters channel
            signals = (df['close'] > df['kc_lower']) & \
                      (df['close'].shift(1) <= df['kc_lower'].shift(1))

        return signals
