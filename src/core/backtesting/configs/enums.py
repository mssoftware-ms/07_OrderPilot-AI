"""
Backtesting Configuration - All enum types
"""

from __future__ import annotations

from enum import Enum

class StrategyType(str, Enum):
    """Strategie-Typen."""
    TRENDFOLLOWING = "trendfollowing"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    HYBRID = "hybrid"


class WeightPresetName(str, Enum):
    """Vordefinierte Weight-Presets."""
    W0 = "W0"  # Default/Balanced
    W1 = "W1"  # Trend/ADX-heavy
    W2 = "W2"  # Momentum/Volatility-heavy
    CUSTOM = "custom"


class DirectionBias(str, Enum):
    """Handelsrichtungs-Bias."""
    BOTH = "BOTH"
    LONG_ONLY = "LONG_ONLY"
    SHORT_ONLY = "SHORT_ONLY"


class ScenarioType(str, Enum):
    """Szenario-Typ."""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"


class AssetClass(str, Enum):
    """Asset-Klassen."""
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"
    FUTURES = "futures"


class StopLossType(str, Enum):
    """Stop-Loss Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"
    STRUCTURE_BASED = "structure_based"


class TakeProfitType(str, Enum):
    """Take-Profit Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"
    RR_RATIO = "rr_ratio"
    LEVEL_BASED = "level_based"


class TrailingType(str, Enum):
    """Trailing Stop Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"


class SlippageMethod(str, Enum):
    """Slippage-Berechnungsmethoden."""
    FIXED_BPS = "fixed_bps"
    ATR_BASED = "atr_based"
    VOLUME_ADJUSTED = "volume_adjusted"


class OptimizationMethod(str, Enum):
    """Optimierungsmethoden."""
    GRID = "grid"
    RANDOM = "random"
    BAYESIAN = "bayesian"


class TargetMetric(str, Enum):
    """Ziel-Metriken fuer Optimierung."""
    EXPECTANCY = "expectancy"
    PROFIT_FACTOR = "profit_factor"
    SHARPE = "sharpe"
    SORTINO = "sortino"
    CALMAR = "calmar"
    MAX_DD = "max_dd"

