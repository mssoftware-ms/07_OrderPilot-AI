"""Volume-based indicator signal generators.

Handles: OBV, MFI, AD, CMF
Target Complexity: CC < 5 per generator
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class OBVSignalGenerator(BaseSignalGenerator):
    """On-Balance Volume signal generator.

    Logic: OBV trending above/below its SMA
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['OBV']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'OBV'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate OBV trend signals."""
        signals = pd.Series(False, index=df.index)
        obv_sma = df['indicator_value'].rolling(20).mean()

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: OBV trending up (accumulation)
            signals = (df['indicator_value'] > obv_sma) & \
                      (df['indicator_value'].shift(1) <= obv_sma.shift(1))

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: OBV trending down (distribution)
            signals = (df['indicator_value'] < obv_sma) & \
                      (df['indicator_value'].shift(1) >= obv_sma.shift(1))

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: OBV crosses below SMA
            signals = (df['indicator_value'] < obv_sma) & \
                      (df['indicator_value'].shift(1) >= obv_sma.shift(1))

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: OBV crosses above SMA
            signals = (df['indicator_value'] > obv_sma) & \
                      (df['indicator_value'].shift(1) <= obv_sma.shift(1))

        return signals


class MFISignalGenerator(BaseSignalGenerator):
    """Money Flow Index signal generator.

    Logic: MFI overbought/oversold levels
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['MFI']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'MFI'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate MFI signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: MFI < 20 (oversold)
            signals = df['indicator_value'] < 20

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: MFI > 80 (overbought)
            signals = df['indicator_value'] > 80

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: MFI > 80 (overbought)
            signals = df['indicator_value'] > 80

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: MFI < 20 (oversold)
            signals = df['indicator_value'] < 20

        return signals


class ADSignalGenerator(BaseSignalGenerator):
    """Accumulation/Distribution signal generator.

    Logic: A/D trending above/below its SMA
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['AD']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'AD'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate A/D signals."""
        signals = pd.Series(False, index=df.index)
        ad_sma = df['indicator_value'].rolling(20).mean()

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: A/D trending up
            signals = (df['indicator_value'] > ad_sma) & \
                      (df['indicator_value'].shift(1) <= ad_sma.shift(1))

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: A/D trending down
            signals = (df['indicator_value'] < ad_sma) & \
                      (df['indicator_value'].shift(1) >= ad_sma.shift(1))

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: A/D crosses below SMA
            signals = (df['indicator_value'] < ad_sma) & \
                      (df['indicator_value'].shift(1) >= ad_sma.shift(1))

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: A/D crosses above SMA
            signals = (df['indicator_value'] > ad_sma) & \
                      (df['indicator_value'].shift(1) <= ad_sma.shift(1))

        return signals


class CMFSignalGenerator(BaseSignalGenerator):
    """Chaikin Money Flow signal generator.

    Logic: CMF zero-line crossovers
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['CMF']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'CMF'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate CMF signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: CMF crosses above 0 (accumulation)
            signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: CMF crosses below 0 (distribution)
            signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: CMF crosses below 0
            signals = (df['indicator_value'] < 0) & (df['indicator_value'].shift(1) >= 0)

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: CMF crosses above 0
            signals = (df['indicator_value'] > 0) & (df['indicator_value'].shift(1) <= 0)

        return signals
