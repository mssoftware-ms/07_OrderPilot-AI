"""
Regime Types - Market Regime Enum.

Refactored from regime_detector.py.

Contains:
- RegimeType enum with properties
"""

from __future__ import annotations

from enum import Enum


class RegimeType(str, Enum):
    """Marktregime-Typen."""

    STRONG_TREND_BULL = "STRONG_TREND_BULL"
    WEAK_TREND_BULL = "WEAK_TREND_BULL"
    STRONG_TREND_BEAR = "STRONG_TREND_BEAR"
    WEAK_TREND_BEAR = "WEAK_TREND_BEAR"
    CHOP_RANGE = "CHOP_RANGE"
    VOLATILITY_EXPLOSIVE = "VOLATILITY_EXPLOSIVE"
    NEUTRAL = "NEUTRAL"

    @property
    def is_bullish(self) -> bool:
        """Prüft ob bullish."""
        return self in [self.STRONG_TREND_BULL, self.WEAK_TREND_BULL]

    @property
    def is_bearish(self) -> bool:
        """Prüft ob bearish."""
        return self in [self.STRONG_TREND_BEAR, self.WEAK_TREND_BEAR]

    @property
    def is_trending(self) -> bool:
        """Prüft ob Trend-Regime."""
        return self in [
            self.STRONG_TREND_BULL,
            self.WEAK_TREND_BULL,
            self.STRONG_TREND_BEAR,
            self.WEAK_TREND_BEAR,
        ]

    @property
    def is_ranging(self) -> bool:
        """Prüft ob Range/Chop."""
        return self == self.CHOP_RANGE

    @property
    def allows_market_entry(self) -> bool:
        """
        Prüft ob Market-Entries erlaubt sind.

        In CHOP_RANGE sind nur Breakout/Retest oder SFP-Reclaim erlaubt.
        """
        return self not in [self.CHOP_RANGE, self.NEUTRAL]
