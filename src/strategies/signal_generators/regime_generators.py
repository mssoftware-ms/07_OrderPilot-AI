"""Regime detection indicator signal generators.

Handles: CHOP (Choppiness Index)
Target Complexity: CC < 5
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class CHOPSignalGenerator(BaseSignalGenerator):
    """Choppiness Index signal generator.

    Logic: Trending (low CHOP) vs Ranging (high CHOP)
    Complexity: CC = 2
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['CHOP']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'CHOP'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate Choppiness Index signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry':
            # Entry: Low chop (trending), expect continuation
            signals = df['indicator_value'] < 38.2
        else:
            # Exit: High chop (ranging), exit trend trades
            signals = df['indicator_value'] > 61.8

        return signals
