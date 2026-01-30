"""Trend and overlay indicator signal generators.

Handles: ICHIMOKU, PSAR, VWAP, PIVOTS
Target Complexity: CC < 5 per generator
"""

import pandas as pd
from typing import List
from .base_generator import BaseSignalGenerator


class IchimokuSignalGenerator(BaseSignalGenerator):
    """Ichimoku Cloud signal generator.

    Logic: Price crossing cloud boundaries
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['ICHIMOKU']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'ICHIMOKU'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate Ichimoku cloud signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Price crosses above cloud
            signals = (df['close'] > df['cloud_top']) & \
                      (df['close'].shift(1) <= df['cloud_top'].shift(1))

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Price crosses below cloud
            signals = (df['close'] < df['cloud_bottom']) & \
                      (df['close'].shift(1) >= df['cloud_bottom'].shift(1))

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: Price enters cloud
            signals = (df['close'] < df['cloud_top']) & \
                      (df['close'].shift(1) >= df['cloud_top'].shift(1))

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: Price enters cloud
            signals = (df['close'] > df['cloud_bottom']) & \
                      (df['close'].shift(1) <= df['cloud_bottom'].shift(1))

        return signals


class PSARSignalGenerator(BaseSignalGenerator):
    """Parabolic SAR signal generator.

    Logic: Price crossing PSAR (reversals)
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['PSAR']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'PSAR'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate PSAR reversal signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Price crosses above PSAR (reversal)
            signals = (df['close'] > df['indicator_value']) & \
                      (df['close'].shift(1) <= df['indicator_value'].shift(1))

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Price crosses below PSAR (reversal)
            signals = (df['close'] < df['indicator_value']) & \
                      (df['close'].shift(1) >= df['indicator_value'].shift(1))

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: PSAR flips
            signals = (df['close'] < df['indicator_value']) & \
                      (df['close'].shift(1) >= df['indicator_value'].shift(1))

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: PSAR flips
            signals = (df['close'] > df['indicator_value']) & \
                      (df['close'].shift(1) <= df['indicator_value'].shift(1))

        return signals


class VWAPSignalGenerator(BaseSignalGenerator):
    """VWAP signal generator.

    Logic: Price crossing VWAP
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['VWAP']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'VWAP'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate VWAP crossover signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Price crosses above VWAP
            signals = (df['close'] > df['indicator_value']) & \
                      (df['close'].shift(1) <= df['indicator_value'].shift(1))

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Price crosses below VWAP
            signals = (df['close'] < df['indicator_value']) & \
                      (df['close'].shift(1) >= df['indicator_value'].shift(1))

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: Price crosses below VWAP
            signals = (df['close'] < df['indicator_value']) & \
                      (df['close'].shift(1) >= df['indicator_value'].shift(1))

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: Price crosses above VWAP
            signals = (df['close'] > df['indicator_value']) & \
                      (df['close'].shift(1) <= df['indicator_value'].shift(1))

        return signals


class PivotsSignalGenerator(BaseSignalGenerator):
    """Pivot Points signal generator.

    Logic: Price position relative to pivot
    Complexity: CC = 4
    """

    @property
    def supported_indicators(self) -> List[str]:
        return ['PIVOTS']

    def can_handle(self, indicator_type: str) -> bool:
        return indicator_type == 'PIVOTS'

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ) -> pd.Series:
        """Generate pivot point signals."""
        signals = pd.Series(False, index=df.index)

        if test_type == 'entry' and trade_side == 'long':
            # Entry Long: Price bounces off pivot (above pivot)
            signals = df['close'] > df['indicator_value']

        elif test_type == 'entry' and trade_side == 'short':
            # Entry Short: Price bounces off pivot (below pivot)
            signals = df['close'] < df['indicator_value']

        elif test_type == 'exit' and trade_side == 'long':
            # Exit Long: Price below pivot
            signals = df['close'] < df['indicator_value']

        elif test_type == 'exit' and trade_side == 'short':
            # Exit Short: Price above pivot
            signals = df['close'] > df['indicator_value']

        return signals
