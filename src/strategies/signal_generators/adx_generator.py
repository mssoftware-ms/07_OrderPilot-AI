"""ADX (Average Directional Index) signal generator.

Handles trend strength detection.
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class ADXSignalGenerator(BaseSignalGenerator):
    """Generate signals based on ADX trend strength.

    Logic:
    - Entry: Strong trend (ADX > 25)
    - Exit: Weak trend (ADX < 20)

    Complexity: CC = 2
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['ADX']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'ADX'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate ADX trend strength signals.

        Complexity: CC = 2
        """
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry':
            # Entry: Strong trend (ADX > 25)
            signals = df['indicator_value'] > 25
        else:
            # Exit: Weak trend (ADX < 20)
            signals = df['indicator_value'] < 20

        return signals
