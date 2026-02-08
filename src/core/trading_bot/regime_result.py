"""
Regime Result - RegimeResult and RegimeConfig Dataclasses.

Refactored from regime_detector.py.

Contains:
- RegimeResult: Detection result with confidence, reasoning, components
- RegimeConfig: Configuration for regime detection
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .regime_types import RegimeType

logger = logging.getLogger(__name__)


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
    """Konfiguration für Regime-Erkennung.

    Kann aus JSON geladen werden via RegimeConfig.from_json(path).
    """

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

    # Strategy-Type-Inferenz Regeln (aus JSON geladen)
    strategy_type_rules: list[dict] = field(default_factory=list)
    strategy_type_indicator_rules: list[dict] = field(default_factory=list)

    # Dynamic parameters (e.g. SMA/EMA periods)
    parameters: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, path: str | Path) -> RegimeConfig:
        """Lädt RegimeConfig aus einer JSON-Datei.

        Args:
            path: Pfad zur JSON-Konfigurationsdatei

        Returns:
            RegimeConfig mit Werten aus der JSON-Datei.
            Bei fehlender Datei oder Fehlern werden Defaults verwendet.
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Regime config not found: {path}, using defaults")
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load regime config: {e}, using defaults")
            return cls()

        # Thresholds auslesen
        thresholds = data.get("thresholds", {})
        mtf = data.get("multi_timeframe", {})
        volume = data.get("volume", {})

        # Mapping: JSON-Key → Dataclass-Feld
        threshold_mapping = {
            "adx_strong": "adx_strong_threshold",
            "adx_weak": "adx_weak_threshold",
            "adx_chop": "adx_chop_threshold",
            "ema_tolerance_pct": "ema_alignment_tolerance_pct",
            "volatility_extreme": "volatility_extreme_threshold",
            "volatility_high": "volatility_high_threshold",
            "volatility_low": "volatility_low_threshold",
            "rsi_overbought": "rsi_overbought",
            "rsi_oversold": "rsi_oversold",
        }

        kwargs: dict = {}
        for json_key, field_name in threshold_mapping.items():
            if json_key in thresholds:
                kwargs[field_name] = float(thresholds[json_key])

        # Multi-Timeframe
        if "require_mtf_alignment" in mtf:
            kwargs["require_mtf_alignment"] = bool(mtf["require_mtf_alignment"])
        if "mtf_timeframes" in mtf:
            kwargs["mtf_timeframes"] = list(mtf["mtf_timeframes"])

        # Volume
        if "volume_confirmation" in volume:
            kwargs["volume_confirmation"] = bool(volume["volume_confirmation"])
        if "min_volume_ratio" in volume:
            kwargs["min_volume_ratio"] = float(volume["min_volume_ratio"])

        # Strategy-Type Regeln
        kwargs["strategy_type_rules"] = data.get("strategy_type_rules", [])
        kwargs["strategy_type_indicator_rules"] = data.get(
            "strategy_type_indicator_rules", []
        )

        # Dynamic parameters (e.g. SMA/EMA periods)
        kwargs["parameters"] = data.get("parameters", {})

        config = cls(**kwargs)
        logger.info(f"Loaded regime config from {path}")
        return config

    @classmethod
    def find_and_load(cls) -> RegimeConfig:
        """Sucht und lädt die regime_detect.json automatisch.

        Sucht in folgender Reihenfolge:
        1. 03_JSON/Trading_Bot/regime_detect/regime_detect.json (primär)
        2. config/regime_config.json (Fallback)
        3. Defaults
        """
        # Projekt-Root finden
        current = Path(__file__).resolve()
        for parent in current.parents:
            # Primärer Speicherort
            primary = (
                parent
                / "03_JSON"
                / "Trading_Bot"
                / "regime_detect"
                / "regime_detect.json"
            )
            if primary.exists():
                return cls.from_json(primary)

            # Fallback
            fallback = parent / "config" / "regime_config.json"
            if fallback.exists():
                return cls.from_json(fallback)

        logger.info("No regime config found, using defaults")
        return cls()

