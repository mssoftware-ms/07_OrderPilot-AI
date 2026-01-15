"""
Regime Result - RegimeResult and RegimeConfig Dataclasses.

Refactored from regime_detector.py.

Contains:
- RegimeResult: Detection result with confidence, reasoning, components
- RegimeConfig: Configuration for regime detection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .regime_types import RegimeType


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
