"""MarketContext Signals - Trading signal data model.

Module 5/8 of market_context.py split.

This module contains:
- SignalSnapshot: Trading signal with entry score, confluence, setup type
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

from .market_context_enums import SetupType, SignalStrength, TrendDirection


@dataclass
class SignalSnapshot:
    """
    Snapshot eines Trading-Signals.

    Enthält Entry-Score, Confluence, Setup-Typ und Gate-Status.
    """

    timestamp: datetime
    symbol: str
    timeframe: str

    # === DIRECTION & STRENGTH ===
    direction: TrendDirection  # BULLISH, BEARISH, NEUTRAL
    strength: SignalStrength = SignalStrength.NONE

    # === ENTRY SCORE (0-100) ===
    entry_score: float = 0.0
    entry_score_components: dict[str, float] = field(default_factory=dict)

    # === CONFLUENCE (0-5) ===
    confluence_score: int = 0
    confluence_conditions_met: list[str] = field(default_factory=list)
    confluence_conditions_failed: list[str] = field(default_factory=list)

    # === SETUP TYPE ===
    setup_type: SetupType = SetupType.UNKNOWN
    setup_confidence: float = 0.0

    # === REGIME GATES ===
    regime_allows_entry: bool = True
    regime_gate_reason: str | None = None  # z.B. "CHOP_RANGE: nur Breakout erlaubt"

    # === TRIGGER ===
    trigger_type: str | None = None  # "breakout", "pullback", "sfp_reclaim"
    trigger_price: float | None = None
    trigger_confirmed: bool = False

    # === TARGETS ===
    suggested_entry: float | None = None
    suggested_sl: float | None = None
    suggested_tp: float | None = None
    risk_reward_ratio: float | None = None

    # === AI VALIDATION (später in Phase 4) ===
    ai_validated: bool = False
    ai_confidence: float | None = None
    ai_approved: bool | None = None
    ai_reasoning: str | None = None
    ai_veto: bool = False
    ai_boost: float | None = None  # Multiplikator für Score

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["direction"] = self.direction.value
        result["strength"] = self.strength.value
        result["setup_type"] = self.setup_type.value
        return result

    @property
    def is_tradeable(self) -> bool:
        """Prüft ob Signal tradeable ist (alle Gates passiert)."""
        return (
            self.strength in [SignalStrength.MODERATE, SignalStrength.STRONG]
            and self.regime_allows_entry
            and self.confluence_score >= 3
            and not self.ai_veto
        )

    def get_final_score(self) -> float:
        """
        Berechnet finalen Score inkl. AI-Boost.

        Returns:
            Score von 0-100
        """
        score = self.entry_score

        # AI Boost/Penalty
        if self.ai_boost is not None:
            score *= self.ai_boost

        # Confluence Bonus
        if self.confluence_score >= 4:
            score *= 1.1
        elif self.confluence_score >= 5:
            score *= 1.2

        return min(100.0, max(0.0, score))
