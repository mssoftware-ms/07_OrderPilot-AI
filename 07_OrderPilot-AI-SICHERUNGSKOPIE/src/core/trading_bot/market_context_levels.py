"""MarketContext Levels - Support/Resistance level data models.

Module 4/8 of market_context.py split.

This module contains:
- Level: Single support/resistance level
- LevelsSnapshot: Snapshot of all detected levels at one point in time
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

from .market_context_enums import LevelStrength, LevelType


@dataclass
class Level:
    """
    Einzelnes Support/Resistance Level.

    Wird von LevelEngine erzeugt und von Chart/Chatbot/Bot konsumiert.
    """

    level_id: str  # Unique ID für Referenzierung
    level_type: LevelType

    # Preis-Range (Zone statt exakter Linie)
    price_low: float
    price_high: float

    # Stärke und Metadata
    strength: LevelStrength = LevelStrength.MODERATE
    touches: int = 0  # Wie oft wurde das Level getestet
    last_touch: datetime | None = None

    # Kontext
    timeframe: str = "5m"  # Auf welchem TF erkannt
    method: str = "pivot"  # pivot, swing, volume_profile, etc.

    # Für Chatbot-Tags
    label: str | None = None  # z.B. "Daily Support", "Weekly Resistance"

    # Berechnet
    is_key_level: bool = False  # Confluence von mehreren Methoden
    distance_from_price_pct: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        if self.last_touch:
            result["last_touch"] = self.last_touch.isoformat()
        result["level_type"] = self.level_type.value
        result["strength"] = self.strength.value
        return result

    def to_chat_tag(self) -> str:
        """
        Erzeugt Chatbot-Tag Format.

        z.B. "[#Support Zone; 91038-91120]"
        """
        type_str = "Support" if self.level_type in [LevelType.SUPPORT, LevelType.SWING_LOW] else "Resistance"
        return f"[#{type_str} Zone; {self.price_low:.0f}-{self.price_high:.0f}]"

    @property
    def midpoint(self) -> float:
        """Mittelpunkt der Zone."""
        return (self.price_low + self.price_high) / 2


@dataclass
class LevelsSnapshot:
    """
    Snapshot aller erkannten Levels zu einem Zeitpunkt.

    Enthält Support/Resistance Zonen sortiert nach Relevanz.
    """

    timestamp: datetime
    symbol: str
    current_price: float

    # Alle Levels
    support_levels: list[Level] = field(default_factory=list)
    resistance_levels: list[Level] = field(default_factory=list)

    # Key Levels (Top-N nach Stärke/Nähe)
    key_supports: list[Level] = field(default_factory=list)
    key_resistances: list[Level] = field(default_factory=list)

    # Nächste Levels (für schnellen Zugriff)
    nearest_support: Level | None = None
    nearest_resistance: Level | None = None

    # Range-Detektion
    in_range: bool = False
    range_high: float | None = None
    range_low: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "current_price": self.current_price,
            "support_levels": [l.to_dict() for l in self.support_levels],
            "resistance_levels": [l.to_dict() for l in self.resistance_levels],
            "key_supports": [l.to_dict() for l in self.key_supports],
            "key_resistances": [l.to_dict() for l in self.key_resistances],
            "nearest_support": self.nearest_support.to_dict() if self.nearest_support else None,
            "nearest_resistance": self.nearest_resistance.to_dict() if self.nearest_resistance else None,
            "in_range": self.in_range,
            "range_high": self.range_high,
            "range_low": self.range_low,
        }

    def get_chat_tags(self) -> list[str]:
        """Erzeugt alle Chatbot-Tags für die Key Levels."""
        tags = []
        for level in self.key_supports[:3]:  # Top 3 Supports
            tags.append(level.to_chat_tag())
        for level in self.key_resistances[:3]:  # Top 3 Resistances
            tags.append(level.to_chat_tag())
        return tags
