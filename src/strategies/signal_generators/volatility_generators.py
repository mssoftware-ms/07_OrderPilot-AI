"""Volatility indicator signal generators.

Handles: ATR, BB_WIDTH
Target Complexity: CC < 5 per generator
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class ATRSignalGenerator(BaseSignalGenerator):
    """Average True Range signal generator.

    Logic: ATR expansion/contraction vs its SMA
    Complexity: CC = 2
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['ATR']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'ATR'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate ATR volatility signals."""
        signals = pd.Series(False, index=df.index)
        atr_sma = df['indicator_value'].rolling(20).mean()

        if test_type == 'entry':
            # Entry: High volatility (ATR expanding)
            signals = df['indicator_value'] > atr_sma
        else:
            # Exit: Low volatility (ATR contracting)
            signals = df['indicator_value'] < atr_sma

        return signals


class BBWidthSignalGenerator(BaseSignalGenerator):
    """Bollinger Band Width signal generator.

    Logic: BB Width expansion/contraction vs its SMA
    Complexity: CC = 2
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['BB_WIDTH']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'BB_WIDTH'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate BB Width signals."""
        signals = pd.Series(False, index=df.index)
        bb_width_sma = df['indicator_value'].rolling(20).mean()

        if test_type == 'entry':
            # Entry: High volatility (wide bands)
            signals = df['indicator_value'] > bb_width_sma
        else:
            # Exit: Low volatility (narrow bands, squeeze)
            signals = df['indicator_value'] < bb_width_sma

        return signals
