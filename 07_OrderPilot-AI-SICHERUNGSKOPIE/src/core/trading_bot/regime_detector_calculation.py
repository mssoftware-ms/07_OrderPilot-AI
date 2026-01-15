"""
Regime Detector Calculation - Regime Calculation Logic.

Refactored from regime_detector.py.

Contains:
- calculate_regime: Combines components into final regime determination
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .regime_detector import RegimeDetectorService
    from .regime_types import RegimeType


class RegimeDetectorCalculation:
    """Helper for regime calculation."""

    def __init__(self, parent: RegimeDetectorService):
        self.parent = parent

    def calculate_regime(
        self,
        ema_alignment: str,
        adx_strength: str,
        volatility_state: str,
        momentum_state: str,
    ) -> tuple[RegimeType, float, list[str]]:
        """
        Berechnet finales Regime aus Komponenten.

        Returns:
            Tuple von (RegimeType, confidence, list_of_reasons)
        """
        from .regime_types import RegimeType

        reasons = []
        confidence = 0.5

        config = self.parent.config

        # Handle CHOP
        if adx_strength == "CHOP":
            reasons.append(f"ADX sehr niedrig (< {config.adx_chop_threshold})")
            return RegimeType.CHOP_RANGE, 0.7, reasons

        # Handle NEUTRAL EMA
        if ema_alignment == "NEUTRAL":
            reasons.append("EMA20 ≈ EMA50 (keine klare Richtung)")
            if adx_strength in ["WEAK", "NONE"]:
                return RegimeType.CHOP_RANGE, 0.6, reasons
            return RegimeType.NEUTRAL, 0.5, reasons

        # BULLISH Regime
        if ema_alignment == "BULL":
            reasons.append("EMA20 > EMA50")

            if adx_strength == "STRONG":
                confidence = 0.85
                reasons.append(f"ADX > {config.adx_strong_threshold}")

                # Momentum Boost
                if momentum_state == "BULLISH":
                    confidence += 0.05
                    reasons.append("RSI bestätigt bullish")
                elif momentum_state == "OVERBOUGHT":
                    confidence -= 0.1
                    reasons.append("RSI overbought (Vorsicht)")

                return RegimeType.STRONG_TREND_BULL, min(0.95, confidence), reasons

            else:
                confidence = 0.65
                reasons.append(f"ADX < {config.adx_strong_threshold}")
                return RegimeType.WEAK_TREND_BULL, confidence, reasons

        # BEARISH Regime
        if ema_alignment == "BEAR":
            reasons.append("EMA20 < EMA50")

            if adx_strength == "STRONG":
                confidence = 0.85
                reasons.append(f"ADX > {config.adx_strong_threshold}")

                # Momentum Boost
                if momentum_state == "BEARISH":
                    confidence += 0.05
                    reasons.append("RSI bestätigt bearish")
                elif momentum_state == "OVERSOLD":
                    confidence -= 0.1
                    reasons.append("RSI oversold (Vorsicht)")

                return RegimeType.STRONG_TREND_BEAR, min(0.95, confidence), reasons

            else:
                confidence = 0.65
                reasons.append(f"ADX < {config.adx_strong_threshold}")
                return RegimeType.WEAK_TREND_BEAR, confidence, reasons

        # Fallback
        return RegimeType.NEUTRAL, 0.4, ["Unklare Situation"]
