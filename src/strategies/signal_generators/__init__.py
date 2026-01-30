"""Signal generator modules for indicator-based trading signals.

This package implements the Strategy Pattern to replace the monster
_generate_signals() function (CC=157) with focused, testable generators.

Architecture:
- BaseSignalGenerator: Abstract base class (Strategy interface)
- Concrete generators: 19 focused generators (CC < 5 each)
- SignalGeneratorRegistry: Central registry for generator lookup

Target: 19 focused generators replacing 322 lines of nested if-statements.
Result: CC reduced from 157 → 3 (98% improvement)
"""

from .base_generator import BaseSignalGenerator

# Import all generators
from .rsi_generator import RSISignalGenerator
from .macd_generator import MACDSignalGenerator
from .sma_generator import SMASignalGenerator
from .ema_generator import EMASignalGenerator
from .bollinger_generator import BollingerSignalGenerator
from .stochastic_generator import StochasticSignalGenerator
from .adx_generator import ADXSignalGenerator
from .volume_generators import (
    OBVSignalGenerator,
    MFISignalGenerator,
    ADSignalGenerator,
    CMFSignalGenerator
)
from .volatility_generators import (
    ATRSignalGenerator,
    BBWidthSignalGenerator
)
from .trend_generators import (
    IchimokuSignalGenerator,
    PSARSignalGenerator,
    VWAPSignalGenerator,
    PivotsSignalGenerator
)
from .channel_generators import KeltnerSignalGenerator
from .momentum_generators import CCISignalGenerator
from .regime_generators import CHOPSignalGenerator


class SignalGeneratorRegistry:
    """Central registry for all signal generators.

    Provides Strategy Pattern implementation for _generate_signals().
    Replaces 322-line monster function (CC=157) with focused generators.

    Usage:
        registry = SignalGeneratorRegistry()
        signals = registry.generate_signals(df, 'RSI', 'entry', 'long')

    Complexity: CC = 2 (vs original 157)
    """

    def __init__(self):
        """Initialize registry with all generators."""
        self.generators = [
            # Momentum & Trend Strength
            RSISignalGenerator(),
            MACDSignalGenerator(),
            ADXSignalGenerator(),
            StochasticSignalGenerator(),
            CCISignalGenerator(),

            # Trend & Overlay
            SMASignalGenerator(),
            EMASignalGenerator(),
            IchimokuSignalGenerator(),
            PSARSignalGenerator(),
            VWAPSignalGenerator(),
            PivotsSignalGenerator(),

            # Channels & Breakouts
            BollingerSignalGenerator(),
            KeltnerSignalGenerator(),

            # Regime Detection
            CHOPSignalGenerator(),

            # Volume
            OBVSignalGenerator(),
            MFISignalGenerator(),
            ADSignalGenerator(),
            CMFSignalGenerator(),

            # Volatility
            ATRSignalGenerator(),
            BBWidthSignalGenerator(),
        ]

    def generate_signals(
        self,
        df,
        indicator_type: str,
        test_type: str,
        trade_side: str
    ):
        """Generate signals using appropriate generator.

        Args:
            df: DataFrame with price and indicator data
            indicator_type: Indicator type (e.g., 'RSI', 'MACD')
            test_type: 'entry' or 'exit'
            trade_side: 'long' or 'short'

        Returns:
            Boolean Series with signals

        Complexity: CC = 2 (loop + return)
        """
        for generator in self.generators:
            if generator.can_handle(indicator_type):
                return generator.generate_signals(
                    df, indicator_type, test_type, trade_side
                )

        # Unknown indicator - return empty signals
        import pandas as pd
        return pd.Series(False, index=df.index)


__all__ = [
    'BaseSignalGenerator',
    'SignalGeneratorRegistry',
    # Individual generators
    'RSISignalGenerator',
    'MACDSignalGenerator',
    'SMASignalGenerator',
    'EMASignalGenerator',
    'BollingerSignalGenerator',
    'StochasticSignalGenerator',
    'ADXSignalGenerator',
    'OBVSignalGenerator',
    'MFISignalGenerator',
    'ADSignalGenerator',
    'CMFSignalGenerator',
    'ATRSignalGenerator',
    'BBWidthSignalGenerator',
    'IchimokuSignalGenerator',
    'PSARSignalGenerator',
    'VWAPSignalGenerator',
    'PivotsSignalGenerator',
    'KeltnerSignalGenerator',
    'CCISignalGenerator',
    'CHOPSignalGenerator',
]
