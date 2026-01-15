"""Level Engine State - Enums, Dataclasses and Config.

Refactored from 797 LOC monolith using composition pattern.

Module 1/4 of level_engine.py split.

Contains:
- LevelType enum (SUPPORT, RESISTANCE, PIVOT, etc.)
- LevelStrength enum (WEAK, MODERATE, STRONG, KEY)
- DetectionMethod enum (SWING, PIVOT, CLUSTER, VOLUME, etc.)
- Level dataclass (single level with zone properties)
- LevelsResult dataclass (result container with properties)
- LevelEngineConfig dataclass (all detection thresholds)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

import pandas as pd


# =============================================================================
# ENUMS
# =============================================================================


class LevelType(Enum):
    """Typ des Levels."""

    SUPPORT = "support"
    RESISTANCE = "resistance"
    PIVOT = "pivot"
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"
    DAILY_HIGH = "daily_high"
    DAILY_LOW = "daily_low"
    WEEKLY_HIGH = "weekly_high"
    WEEKLY_LOW = "weekly_low"
    VWAP = "vwap"
    POC = "poc"  # Point of Control (Volume Profile)


class LevelStrength(Enum):
    """Stärke des Levels."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    KEY = "key"  # Besonders wichtiges Level


class DetectionMethod(Enum):
    """Methode zur Level-Erkennung."""

    SWING = "swing"  # Swing High/Low based
    PIVOT = "pivot"  # Pivot Points (PP, R1, S1, etc.)
    CLUSTER = "cluster"  # Price clustering
    VOLUME = "volume"  # Volume-based (POC, VAH, VAL)
    FRACTAL = "fractal"  # Fractal-based detection
    MANUAL = "manual"  # Manuell hinzugefügt


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class Level:
    """
    Einzelnes Level (Support/Resistance/Pivot etc.).

    Repräsentiert eine Zone, nicht nur einen Preis-Punkt.
    """

    id: str  # Unique ID
    level_type: LevelType
    price_low: float  # Untere Grenze der Zone
    price_high: float  # Obere Grenze der Zone
    strength: LevelStrength
    method: DetectionMethod
    timeframe: str
    touches: int = 1  # Wie oft wurde das Level getestet
    broken: bool = False  # Wurde das Level durchbrochen
    first_touch: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_touch: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def price_mid(self) -> float:
        """Mittelpunkt der Zone."""
        return (self.price_low + self.price_high) / 2

    @property
    def zone_width(self) -> float:
        """Breite der Zone in absoluten Zahlen."""
        return self.price_high - self.price_low

    @property
    def zone_width_pct(self) -> float:
        """Breite der Zone in Prozent des Mittelpreises."""
        return (self.zone_width / self.price_mid) * 100 if self.price_mid > 0 else 0

    def contains_price(self, price: float) -> bool:
        """Prüft ob ein Preis in der Zone liegt."""
        return self.price_low <= price <= self.price_high

    def is_near(self, price: float, tolerance_pct: float = 0.5) -> bool:
        """Prüft ob ein Preis in der Nähe der Zone liegt."""
        tolerance = self.price_mid * (tolerance_pct / 100)
        return (self.price_low - tolerance) <= price <= (self.price_high + tolerance)

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "id": self.id,
            "type": self.level_type.value,
            "price_low": self.price_low,
            "price_high": self.price_high,
            "price_mid": self.price_mid,
            "strength": self.strength.value,
            "method": self.method.value,
            "timeframe": self.timeframe,
            "touches": self.touches,
            "broken": self.broken,
            "label": self.label,
            "zone_width_pct": round(self.zone_width_pct, 4),
        }


@dataclass
class LevelsResult:
    """Ergebnis der Level-Analyse."""

    levels: List[Level]
    symbol: str
    timeframe: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    current_price: Optional[float] = None

    @property
    def support_levels(self) -> List[Level]:
        """Nur Support-Levels (unter aktuellem Preis)."""
        if self.current_price is None:
            return [
                l
                for l in self.levels
                if l.level_type in (LevelType.SUPPORT, LevelType.SWING_LOW)
            ]
        return [l for l in self.levels if l.price_mid < self.current_price]

    @property
    def resistance_levels(self) -> List[Level]:
        """Nur Resistance-Levels (über aktuellem Preis)."""
        if self.current_price is None:
            return [
                l
                for l in self.levels
                if l.level_type in (LevelType.RESISTANCE, LevelType.SWING_HIGH)
            ]
        return [l for l in self.levels if l.price_mid > self.current_price]

    @property
    def key_levels(self) -> List[Level]:
        """Nur Key Levels (strength=KEY)."""
        return [l for l in self.levels if l.strength == LevelStrength.KEY]

    def get_nearest_support(self, price: Optional[float] = None) -> Optional[Level]:
        """Findet nächstes Support-Level unter dem Preis."""
        price = price or self.current_price
        if price is None:
            return None
        supports = [l for l in self.levels if l.price_mid < price]
        if not supports:
            return None
        return max(supports, key=lambda l: l.price_mid)

    def get_nearest_resistance(self, price: Optional[float] = None) -> Optional[Level]:
        """Findet nächstes Resistance-Level über dem Preis."""
        price = price or self.current_price
        if price is None:
            return None
        resistances = [l for l in self.levels if l.price_mid > price]
        if not resistances:
            return None
        return min(resistances, key=lambda l: l.price_mid)

    def get_top_n(self, n: int = 5, sort_by: str = "strength") -> List[Level]:
        """Gibt die Top-N wichtigsten Levels zurück."""
        if sort_by == "strength":
            strength_order = {
                LevelStrength.KEY: 4,
                LevelStrength.STRONG: 3,
                LevelStrength.MODERATE: 2,
                LevelStrength.WEAK: 1,
            }
            sorted_levels = sorted(
                self.levels, key=lambda l: strength_order.get(l.strength, 0), reverse=True
            )
        elif sort_by == "touches":
            sorted_levels = sorted(self.levels, key=lambda l: l.touches, reverse=True)
        elif sort_by == "proximity" and self.current_price:
            sorted_levels = sorted(
                self.levels, key=lambda l: abs(l.price_mid - self.current_price)
            )
        else:
            sorted_levels = self.levels

        return sorted_levels[:n]

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "current_price": self.current_price,
            "total_levels": len(self.levels),
            "support_count": len(self.support_levels),
            "resistance_count": len(self.resistance_levels),
            "key_levels_count": len(self.key_levels),
            "levels": [l.to_dict() for l in self.levels],
        }

    def to_tag_format(self) -> str:
        """Konvertiert zu Tag-Format für Chatbot."""
        tags = []
        for level in self.get_top_n(10):
            type_tag = (
                "Support"
                if level.price_mid < (self.current_price or 0)
                else "Resistance"
            )
            if level.strength == LevelStrength.KEY:
                type_tag = f"Key {type_tag}"
            tags.append(
                f"[#{type_tag} Zone; {level.price_low:.2f}-{level.price_high:.2f}]"
            )
        return " ".join(tags)


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class LevelEngineConfig:
    """Konfiguration für LevelEngine."""

    # Swing Detection
    swing_lookback: int = 10  # Bars links/rechts für Swing High/Low
    min_swing_touches: int = 2  # Min. Touches für valides Level

    # Zone Width
    zone_width_atr_mult: float = 0.3  # Zone-Breite als Vielfaches von ATR
    min_zone_width_pct: float = 0.1  # Minimale Zone-Breite in %
    max_zone_width_pct: float = 2.0  # Maximale Zone-Breite in %

    # Clustering
    cluster_threshold_pct: float = 0.5  # Preise innerhalb X% werden geclustert
    min_cluster_size: int = 3  # Minimum Punkte für einen Cluster

    # Strength Calculation
    strong_touch_threshold: int = 3  # Touches für "STRONG"
    key_touch_threshold: int = 5  # Touches für "KEY"

    # Filtering
    max_levels: int = 20  # Maximum Levels pro Analyse
    proximity_merge_pct: float = 0.3  # Levels innerhalb X% werden gemerged

    # Pivot Points
    include_pivots: bool = True
    pivot_type: str = "standard"  # standard, fibonacci, woodie, camarilla

    # Historical Levels
    include_daily_hl: bool = True
    include_weekly_hl: bool = True
    daily_lookback: int = 5  # Tage für Daily H/L
    weekly_lookback: int = 4  # Wochen für Weekly H/L
