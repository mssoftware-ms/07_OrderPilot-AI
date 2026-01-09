"""
Regime Detector Service - Shared Service für Marktregime-Erkennung (REFACTORED).

REFACTORED: Split into focused helper modules using composition pattern.

Erkennt:
- STRONG_TREND_BULL/BEAR (EMA-Stack + ADX > 30)
- WEAK_TREND_BULL/BEAR (EMA-Stack + ADX < 30)
- CHOP_RANGE (ADX niedrig, keine klare Richtung)
- VOLATILITY_EXPLOSIVE (ATR sehr hoch)
- NEUTRAL (unklare Situation)

Wird von Trading-Engine, AI Popup und Chatbot verwendet.

Phase 2.1 der Bot-Integration.
"""

from __future__ import annotations

import pandas as pd

# Import types and results from new locations
from .regime_result import RegimeConfig, RegimeResult
from .regime_types import RegimeType

# Import helper modules
from .regime_detector_calculation import RegimeDetectorCalculation
from .regime_detector_components import RegimeDetectorComponents
from .regime_detector_gate_info import RegimeDetectorGateInfo

# Re-export types for backward compatibility
__all__ = [
    "RegimeDetectorService",
    "RegimeType",
    "RegimeResult",
    "RegimeConfig",
    "get_regime_detector",
    "detect_regime",
    "is_trending",
    "is_ranging",
]


class RegimeDetectorService:
    """
    Shared Service für Marktregime-Erkennung (REFACTORED).

    Deterministisch und wiederverwendbar.
    Delegiert spezifische Aufgaben an Helper-Klassen.

    Usage:
        detector = RegimeDetectorService()
        result = detector.detect(df)

        if result.allows_market_entry:
            # Proceed with entry
        else:
            logger.info(f"Entry blocked: {result.gate_reason}")
    """

    def __init__(self, config: RegimeConfig | None = None):
        self.config = config or RegimeConfig()

        # Create helpers (composition pattern)
        self._components = RegimeDetectorComponents(self)
        self._calculation = RegimeDetectorCalculation(self)
        self._gate_info = RegimeDetectorGateInfo(self)

    def detect(self, df: pd.DataFrame) -> RegimeResult:
        """
        Erkennt Marktregime aus DataFrame.

        Args:
            df: DataFrame mit Indikatoren (ema_20, ema_50, adx_14, atr_percent, rsi_14)

        Returns:
            RegimeResult mit Regime, Confidence und Reasoning
        """
        if df is None or df.empty:
            return RegimeResult(
                regime=RegimeType.NEUTRAL,
                confidence=0.0,
                reasoning="No data available",
            )

        current = df.iloc[-1]

        # Extract Values
        ema_20 = current.get("ema_20")
        ema_50 = current.get("ema_50")
        ema_200 = current.get("ema_200")
        adx = current.get("adx_14")
        atr_pct = current.get("atr_percent")
        rsi = current.get("rsi_14")
        close = current.get("close")

        # Volatility Check First (überlagert alles)
        volatility_state = self._components.determine_volatility_state(atr_pct)
        if volatility_state == "EXTREME":
            return RegimeResult(
                regime=RegimeType.VOLATILITY_EXPLOSIVE,
                confidence=0.9,
                reasoning=f"ATR% = {atr_pct:.2f}% > {self.config.volatility_extreme_threshold}%",
                volatility_state=volatility_state,
                atr_pct=atr_pct,
                ema_20=ema_20,
                ema_50=ema_50,
                adx=adx,
            )

        # EMA Alignment
        ema_alignment = self._components.determine_ema_alignment(ema_20, ema_50, close)

        # ADX Strength
        adx_strength = self._components.determine_adx_strength(adx)

        # Momentum State
        momentum_state = self._components.determine_momentum_state(rsi)

        # Determine Regime
        regime, confidence, reasons = self._calculation.calculate_regime(
            ema_alignment, adx_strength, volatility_state, momentum_state
        )

        return RegimeResult(
            regime=regime,
            confidence=confidence,
            reasoning="; ".join(reasons),
            ema_alignment=ema_alignment,
            adx_strength=adx_strength,
            volatility_state=volatility_state,
            momentum_state=momentum_state,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            adx=adx,
            atr_pct=atr_pct,
            rsi=rsi,
        )

    def detect_from_values(
        self,
        ema_20: float | None,
        ema_50: float | None,
        adx: float | None,
        atr_pct: float | None = None,
        rsi: float | None = None,
        close: float | None = None,
    ) -> RegimeResult:
        """
        Erkennt Regime aus einzelnen Werten (ohne DataFrame).

        Nützlich wenn Indikatoren bereits extrahiert wurden.
        """
        # Volatility Check First
        volatility_state = self._components.determine_volatility_state(atr_pct)
        if volatility_state == "EXTREME":
            return RegimeResult(
                regime=RegimeType.VOLATILITY_EXPLOSIVE,
                confidence=0.9,
                reasoning=f"ATR% = {atr_pct:.2f}% > {self.config.volatility_extreme_threshold}%",
                volatility_state=volatility_state,
                atr_pct=atr_pct,
                ema_20=ema_20,
                ema_50=ema_50,
                adx=adx,
            )

        # EMA Alignment
        ema_alignment = self._components.determine_ema_alignment(ema_20, ema_50, close)

        # ADX Strength
        adx_strength = self._components.determine_adx_strength(adx)

        # Momentum State
        momentum_state = self._components.determine_momentum_state(rsi)

        # Determine Regime
        regime, confidence, reasons = self._calculation.calculate_regime(
            ema_alignment, adx_strength, volatility_state, momentum_state
        )

        return RegimeResult(
            regime=regime,
            confidence=confidence,
            reasoning="; ".join(reasons),
            ema_alignment=ema_alignment,
            adx_strength=adx_strength,
            volatility_state=volatility_state,
            momentum_state=momentum_state,
            ema_20=ema_20,
            ema_50=ema_50,
            adx=adx,
            atr_pct=atr_pct,
            rsi=rsi,
        )

    def get_regime_gate_info(self, result: RegimeResult) -> dict:
        """Gibt detaillierte Gate-Info für UI zurück (delegiert)."""
        return self._gate_info.get_regime_gate_info(result)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================


_global_detector: RegimeDetectorService | None = None


def get_regime_detector(config: RegimeConfig | None = None) -> RegimeDetectorService:
    """
    Gibt globale Detector-Instanz zurück (Singleton).

    Usage:
        detector = get_regime_detector()
        result = detector.detect(df)
    """
    global _global_detector

    if _global_detector is None:
        _global_detector = RegimeDetectorService(config)

    return _global_detector


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def detect_regime(df: pd.DataFrame) -> RegimeResult:
    """
    Convenience-Funktion für Regime-Erkennung.

    Usage:
        result = detect_regime(df)
        if result.allows_market_entry:
            proceed()
    """
    detector = get_regime_detector()
    return detector.detect(df)


def is_trending(df: pd.DataFrame) -> bool:
    """
    Quick-Check ob Markt im Trend ist.

    Usage:
        if is_trending(df):
            execute_trend_strategy()
    """
    result = detect_regime(df)
    return result.regime.is_trending


def is_ranging(df: pd.DataFrame) -> bool:
    """
    Quick-Check ob Markt in Range/Chop ist.

    Usage:
        if is_ranging(df):
            wait_for_breakout()
    """
    result = detect_regime(df)
    return result.regime.is_ranging
