"""
Signal Types - Signal-related Enums and Dataclasses.

Refactored from signal_generator.py.

Contains:
- SignalDirection enum
- SignalStrength enum
- ConditionResult dataclass
- TradeSignal dataclass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SignalDirection(str, Enum):
    """Signalrichtung."""

    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class SignalStrength(str, Enum):
    """Signalstärke basierend auf Confluence."""

    STRONG = "STRONG"  # 5/5 Conditions
    MODERATE = "MODERATE"  # 4/5 Conditions
    WEAK = "WEAK"  # 3/5 Conditions
    NONE = "NONE"  # < 3 Conditions


@dataclass
class ConditionResult:
    """Ergebnis einer einzelnen Bedingungsprüfung."""

    name: str
    met: bool
    value: float | str | None = None
    threshold: float | str | None = None
    description: str = ""


@dataclass
class TradeSignal:
    """Trading-Signal mit allen Details."""

    direction: SignalDirection
    strength: SignalStrength
    confluence_score: int  # 0-5
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Bedingungen
    conditions_met: list[ConditionResult] = field(default_factory=list)
    conditions_failed: list[ConditionResult] = field(default_factory=list)

    # Kontext
    current_price: float | None = None
    regime: str | None = None

    # Empfohlene Levels (von RiskManager zu füllen)
    suggested_entry: float | None = None
    suggested_sl: float | None = None
    suggested_tp: float | None = None

    @property
    def is_valid(self) -> bool:
        """Signal ist valid wenn confluence_score >= 3."""
        return self.confluence_score >= 3 and self.direction != SignalDirection.NEUTRAL

    def get_conditions_summary(self) -> dict[str, list[str]]:
        """Gibt Zusammenfassung der Bedingungen zurück."""
        return {
            "met": [f"{c.name}: {c.description}" for c in self.conditions_met],
            "failed": [f"{c.name}: {c.description}" for c in self.conditions_failed],
        }
