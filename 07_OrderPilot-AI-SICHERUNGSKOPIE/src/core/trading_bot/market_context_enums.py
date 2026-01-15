"""MarketContext Enums - Enum definitions for market context.

Module 1/8 of market_context.py split.

This module contains all enum types used across market context:
- RegimeType: Market regime types for regime gates
- TrendDirection: Trend direction for multi-timeframe analysis
- LevelType: Support/Resistance level types
- LevelStrength: Level strength based on touches/confluence
- SignalStrength: Entry/Exit signal strength
- SetupType: Detected setup types
"""

from __future__ import annotations

from enum import Enum


class RegimeType(str, Enum):
    """Marktregime-Typen für Regime-Gates."""

    STRONG_TREND_BULL = "STRONG_TREND_BULL"
    WEAK_TREND_BULL = "WEAK_TREND_BULL"
    STRONG_TREND_BEAR = "STRONG_TREND_BEAR"
    WEAK_TREND_BEAR = "WEAK_TREND_BEAR"
    CHOP_RANGE = "CHOP_RANGE"
    VOLATILITY_EXPLOSIVE = "VOLATILITY_EXPLOSIVE"
    NEUTRAL = "NEUTRAL"


class TrendDirection(str, Enum):
    """Trend-Richtung für Multi-Timeframe Analyse."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class LevelType(str, Enum):
    """Typ eines Support/Resistance Levels."""

    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"
    PIVOT = "PIVOT"
    SWING_LOW = "SWING_LOW"
    SWING_HIGH = "SWING_HIGH"
    EMA_SUPPORT = "EMA_SUPPORT"
    EMA_RESISTANCE = "EMA_RESISTANCE"
    VOLUME_NODE = "VOLUME_NODE"


class LevelStrength(str, Enum):
    """Stärke eines Levels basierend auf Touches/Confluence."""

    WEAK = "WEAK"        # 1-2 touches
    MODERATE = "MODERATE"  # 3-4 touches
    STRONG = "STRONG"    # 5+ touches
    KEY_LEVEL = "KEY_LEVEL"  # Confluence von mehreren Methoden


class SignalStrength(str, Enum):
    """Signal-Stärke für Entry/Exit."""

    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class SetupType(str, Enum):
    """Erkannte Setup-Typen."""

    BREAKOUT = "BREAKOUT"
    PULLBACK = "PULLBACK"
    SFP = "SFP"  # Swing Failure Pattern
    MEAN_REVERSION = "MEAN_REVERSION"
    TREND_CONTINUATION = "TREND_CONTINUATION"
    RANGE_BOUNCE = "RANGE_BOUNCE"
    UNKNOWN = "UNKNOWN"
