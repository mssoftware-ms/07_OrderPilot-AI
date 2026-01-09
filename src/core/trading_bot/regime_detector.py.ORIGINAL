"""
Regime Detector Service - Shared Service für Marktregime-Erkennung.

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

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


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


# =============================================================================
# REGIME RESULT
# =============================================================================


@dataclass
class RegimeResult:
    """
    Ergebnis der Regime-Erkennung.

    Enthält:
    - Regime Type
    - Confidence (0-1)
    - Reasoning (für Debugging/UI)
    - Components (welche Indikatoren haben beigetragen)
    """

    regime: RegimeType
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Komponenten
    ema_alignment: str | None = None  # "BULL", "BEAR", "NEUTRAL"
    adx_strength: str | None = None  # "STRONG", "WEAK", "NONE"
    volatility_state: str | None = None  # "LOW", "NORMAL", "HIGH", "EXTREME"
    momentum_state: str | None = None  # "BULLISH", "BEARISH", "NEUTRAL"

    # Rohdaten
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    adx: float | None = None
    atr_pct: float | None = None
    rsi: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "components": {
                "ema_alignment": self.ema_alignment,
                "adx_strength": self.adx_strength,
                "volatility_state": self.volatility_state,
                "momentum_state": self.momentum_state,
            },
            "raw_values": {
                "ema_20": self.ema_20,
                "ema_50": self.ema_50,
                "ema_200": self.ema_200,
                "adx": self.adx,
                "atr_pct": self.atr_pct,
                "rsi": self.rsi,
            },
        }

    @property
    def allows_market_entry(self) -> bool:
        """Shortcut für Regime-Check."""
        return self.regime.allows_market_entry

    @property
    def gate_reason(self) -> str | None:
        """
        Gibt Grund zurück, warum Market-Entry blockiert ist.

        Returns None wenn Entry erlaubt.
        """
        if self.regime == RegimeType.CHOP_RANGE:
            return "CHOP_RANGE: Nur Breakout/Retest oder SFP-Reclaim erlaubt"
        elif self.regime == RegimeType.NEUTRAL:
            return "NEUTRAL: Regime unklar, kein Entry"
        elif self.regime == RegimeType.VOLATILITY_EXPLOSIVE:
            return "VOLATILITY_EXPLOSIVE: Erhöhte Vorsicht, reduzierte Position"
        return None


# =============================================================================
# REGIME CONFIG
# =============================================================================


@dataclass
class RegimeConfig:
    """Konfiguration für Regime-Erkennung."""

    # ADX Thresholds
    adx_strong_threshold: float = 30.0
    adx_weak_threshold: float = 20.0
    adx_chop_threshold: float = 15.0

    # EMA Thresholds (für EMA-Alignment)
    ema_alignment_tolerance_pct: float = 0.5  # EMA20 muss 0.5% über/unter EMA50 sein

    # Volatility Thresholds (ATR als % vom Preis)
    volatility_extreme_threshold: float = 5.0
    volatility_high_threshold: float = 3.0
    volatility_low_threshold: float = 1.0

    # RSI Thresholds
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0

    # Multi-Timeframe
    require_mtf_alignment: bool = False
    mtf_timeframes: list[str] = field(default_factory=lambda: ["5m", "1h", "4h"])

    # Zusätzliche Filter
    volume_confirmation: bool = False
    min_volume_ratio: float = 0.5


# =============================================================================
# REGIME DETECTOR SERVICE
# =============================================================================


class RegimeDetectorService:
    """
    Shared Service für Marktregime-Erkennung.

    Deterministisch und wiederverwendbar.

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
        volatility_state = self._determine_volatility_state(atr_pct)
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
        ema_alignment = self._determine_ema_alignment(ema_20, ema_50, close)

        # ADX Strength
        adx_strength = self._determine_adx_strength(adx)

        # Momentum State
        momentum_state = self._determine_momentum_state(rsi)

        # Determine Regime
        regime, confidence, reasons = self._calculate_regime(
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
        volatility_state = self._determine_volatility_state(atr_pct)
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
        ema_alignment = self._determine_ema_alignment(ema_20, ema_50, close)

        # ADX Strength
        adx_strength = self._determine_adx_strength(adx)

        # Momentum State
        momentum_state = self._determine_momentum_state(rsi)

        # Determine Regime
        regime, confidence, reasons = self._calculate_regime(
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

    # =========================================================================
    # COMPONENT DETECTION
    # =========================================================================

    def _determine_volatility_state(self, atr_pct: float | None) -> str:
        """Bestimmt Volatilitäts-Zustand."""
        if atr_pct is None:
            return "NORMAL"

        if atr_pct >= self.config.volatility_extreme_threshold:
            return "EXTREME"
        elif atr_pct >= self.config.volatility_high_threshold:
            return "HIGH"
        elif atr_pct < self.config.volatility_low_threshold:
            return "LOW"
        return "NORMAL"

    def _determine_ema_alignment(
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

        tolerance = self.config.ema_alignment_tolerance_pct

        if diff_pct > tolerance:
            return "BULL"
        elif diff_pct < -tolerance:
            return "BEAR"
        else:
            return "NEUTRAL"

    def _determine_adx_strength(self, adx: float | None) -> str:
        """Bestimmt ADX-Stärke."""
        if adx is None:
            return "NONE"

        if adx >= self.config.adx_strong_threshold:
            return "STRONG"
        elif adx >= self.config.adx_weak_threshold:
            return "WEAK"
        elif adx < self.config.adx_chop_threshold:
            return "CHOP"
        else:
            return "WEAK"

    def _determine_momentum_state(self, rsi: float | None) -> str:
        """Bestimmt Momentum-Zustand."""
        if rsi is None:
            return "NEUTRAL"

        if rsi >= self.config.rsi_overbought:
            return "OVERBOUGHT"
        elif rsi <= self.config.rsi_oversold:
            return "OVERSOLD"
        elif rsi > 50:
            return "BULLISH"
        elif rsi < 50:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_regime(
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
        reasons = []
        confidence = 0.5

        # Handle CHOP
        if adx_strength == "CHOP":
            reasons.append(f"ADX sehr niedrig (< {self.config.adx_chop_threshold})")
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
                reasons.append(f"ADX > {self.config.adx_strong_threshold}")

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
                reasons.append(f"ADX < {self.config.adx_strong_threshold}")
                return RegimeType.WEAK_TREND_BULL, confidence, reasons

        # BEARISH Regime
        if ema_alignment == "BEAR":
            reasons.append("EMA20 < EMA50")

            if adx_strength == "STRONG":
                confidence = 0.85
                reasons.append(f"ADX > {self.config.adx_strong_threshold}")

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
                reasons.append(f"ADX < {self.config.adx_strong_threshold}")
                return RegimeType.WEAK_TREND_BEAR, confidence, reasons

        # Fallback
        return RegimeType.NEUTRAL, 0.4, ["Unklare Situation"]

    # =========================================================================
    # ADDITIONAL METHODS
    # =========================================================================

    def get_regime_gate_info(self, result: RegimeResult) -> dict:
        """
        Gibt detaillierte Gate-Info für UI zurück.

        Returns dict mit:
        - allowed: bool
        - reason: str | None
        - allowed_entry_types: list[str]
        """
        if result.regime == RegimeType.CHOP_RANGE:
            return {
                "allowed": False,
                "reason": "CHOP_RANGE: Market-Entries blockiert",
                "allowed_entry_types": ["BREAKOUT", "RETEST", "SFP_RECLAIM"],
                "recommendation": "Warte auf Breakout oder Mean-Reversion Setup",
            }
        elif result.regime == RegimeType.NEUTRAL:
            return {
                "allowed": False,
                "reason": "NEUTRAL: Regime unklar",
                "allowed_entry_types": [],
                "recommendation": "Kein Entry, warte auf klares Signal",
            }
        elif result.regime == RegimeType.VOLATILITY_EXPLOSIVE:
            return {
                "allowed": True,
                "reason": "VOLATILITY_EXPLOSIVE: Erhöhte Vorsicht",
                "allowed_entry_types": ["ALL"],
                "recommendation": "Reduziere Position Size, engere Stops",
            }
        else:
            return {
                "allowed": True,
                "reason": None,
                "allowed_entry_types": ["ALL"],
                "recommendation": f"Trend {result.regime.value} - Entry erlaubt",
            }


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
