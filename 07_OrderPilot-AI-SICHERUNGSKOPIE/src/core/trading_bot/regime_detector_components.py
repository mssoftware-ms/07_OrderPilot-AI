"""
Regime Detector Components - Component Detection Methods.

Refactored from regime_detector.py.

Contains:
- _determine_volatility_state: ATR-based volatility classification
- _determine_ema_alignment: EMA20/50 alignment (BULL/BEAR/NEUTRAL)
- _determine_adx_strength: ADX strength classification
- _determine_momentum_state: RSI momentum classification
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .regime_detector import RegimeDetectorService


class RegimeDetectorComponents:
    """Helper for component detection methods."""

    def __init__(self, parent: RegimeDetectorService):
        self.parent = parent

    def determine_volatility_state(self, atr_pct: float | None) -> str:
        """Bestimmt Volatilitäts-Zustand."""
        if atr_pct is None:
            return "NORMAL"

        config = self.parent.config

        if atr_pct >= config.volatility_extreme_threshold:
            return "EXTREME"
        elif atr_pct >= config.volatility_high_threshold:
            return "HIGH"
        elif atr_pct < config.volatility_low_threshold:
            return "LOW"
        return "NORMAL"

    def determine_ema_alignment(
        self,
        ema_20: float | None,
        ema_50: float | None,
        close: float | None = None,
    ) -> str:
        """Bestimmt EMA-Alignment."""
        if ema_20 is None or ema_50 is None:
            return "NEUTRAL"

        # Calculate relative difference
        if ema_50 > 0:
            diff_pct = ((ema_20 - ema_50) / ema_50) * 100
        else:
            diff_pct = 0

        tolerance = self.parent.config.ema_alignment_tolerance_pct

        if diff_pct > tolerance:
            return "BULL"
        elif diff_pct < -tolerance:
            return "BEAR"
        else:
            return "NEUTRAL"

    def determine_adx_strength(self, adx: float | None) -> str:
        """Bestimmt ADX-Stärke."""
        if adx is None:
            return "NONE"

        config = self.parent.config

        if adx >= config.adx_strong_threshold:
            return "STRONG"
        elif adx >= config.adx_weak_threshold:
            return "WEAK"
        elif adx < config.adx_chop_threshold:
            return "CHOP"
        else:
            return "WEAK"

    def determine_momentum_state(self, rsi: float | None) -> str:
        """Bestimmt Momentum-Zustand."""
        if rsi is None:
            return "NEUTRAL"

        config = self.parent.config

        if rsi >= config.rsi_overbought:
            return "OVERBOUGHT"
        elif rsi <= config.rsi_oversold:
            return "OVERSOLD"
        elif rsi > 50:
            return "BULLISH"
        elif rsi < 50:
            return "BEARISH"
        else:
            return "NEUTRAL"
