"""Technical Indicators Package.

Provides modular technical indicator calculations organized by category:
- Trend: SMA, EMA, WMA, VWMA, MACD, ADX, PSAR, ICHIMOKU
- Momentum: RSI, STOCH, MOM, ROC, WILLR, CCI, MFI
- Volatility: BB, KC, ATR, NATR, STD
- Volume: OBV, CMF, AD, FI, VWAP
- Custom: PIVOTS, SUPPORT_RESISTANCE, PATTERN
"""

# Re-export all types and classes for backward compatibility
from .base import PANDAS_TA_AVAILABLE, TALIB_AVAILABLE, BaseIndicatorCalculator
from .custom import CustomIndicators
from .engine import IndicatorEngine
from .momentum import MomentumIndicators
from .trend import TrendIndicators
from .types import IndicatorConfig, IndicatorResult, IndicatorType
from .volatility import VolatilityIndicators
from .volume import VolumeIndicators

__all__ = [
    # Main engine
    'IndicatorEngine',

    # Types
    'IndicatorType',
    'IndicatorConfig',
    'IndicatorResult',

    # Calculator classes
    'BaseIndicatorCalculator',
    'TrendIndicators',
    'MomentumIndicators',
    'VolatilityIndicators',
    'VolumeIndicators',
    'CustomIndicators',

    # Library availability flags
    'TALIB_AVAILABLE',
    'PANDAS_TA_AVAILABLE'
]
