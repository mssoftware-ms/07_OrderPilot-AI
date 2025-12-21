"""Type Definitions for Technical Indicators.

Defines indicator types, configurations, and result structures.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd


class IndicatorType(Enum):
    """Types of technical indicators."""
    # Trend
    SMA = "sma"  # Simple Moving Average
    EMA = "ema"  # Exponential Moving Average
    WMA = "wma"  # Weighted Moving Average
    VWMA = "vwma"  # Volume Weighted Moving Average
    MACD = "macd"  # Moving Average Convergence Divergence
    ADX = "adx"  # Average Directional Index
    PSAR = "psar"  # Parabolic SAR
    ICHIMOKU = "ichimoku"  # Ichimoku Cloud

    # Momentum
    RSI = "rsi"  # Relative Strength Index
    STOCH = "stoch"  # Stochastic Oscillator
    MOM = "mom"  # Momentum
    ROC = "roc"  # Rate of Change
    WILLR = "willr"  # Williams %R
    CCI = "cci"  # Commodity Channel Index
    MFI = "mfi"  # Money Flow Index

    # Volatility
    BB = "bb"  # Bollinger Bands
    KC = "kc"  # Keltner Channels
    ATR = "atr"  # Average True Range
    NATR = "natr"  # Normalized ATR
    STD = "std"  # Standard Deviation

    # Volume
    OBV = "obv"  # On-Balance Volume
    CMF = "cmf"  # Chaikin Money Flow
    AD = "ad"  # Accumulation/Distribution
    FI = "fi"  # Force Index
    VWAP = "vwap"  # Volume Weighted Average Price

    # Custom
    PIVOTS = "pivots"  # Pivot Points
    SUPPORT_RESISTANCE = "sup_res"  # Support/Resistance Levels
    PATTERN = "pattern"  # Price Patterns


@dataclass
class IndicatorConfig:
    """Configuration for an indicator."""
    indicator_type: IndicatorType
    params: dict[str, Any]
    use_talib: bool = True  # Prefer TA-Lib if available
    cache_results: bool = True
    min_periods: int | None = None  # Minimum periods needed


@dataclass
class IndicatorResult:
    """Result from indicator calculation."""
    indicator_type: IndicatorType
    values: pd.Series | pd.DataFrame | dict[str, Any]
    timestamp: datetime
    params: dict[str, Any]
    metadata: dict[str, Any] | None = None
