"""
Entry Score Types - Enums and Data Classes

Defines core types for entry score calculation:
- Enums: ScoreDirection, ScoreQuality, GateStatus
- Data Classes: ComponentScore, GateResult

Module 1/4 of entry_score_engine.py split (Lines 41-262)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


# =============================================================================
# ENUMS
# =============================================================================


class ScoreDirection(str, Enum):
    """Signal direction for entry."""

    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class ScoreQuality(str, Enum):
    """Quality tier based on final score."""

    EXCELLENT = "EXCELLENT"  # >= 0.8
    GOOD = "GOOD"  # >= 0.65
    MODERATE = "MODERATE"  # >= 0.5
    WEAK = "WEAK"  # >= 0.35
    NO_SIGNAL = "NO_SIGNAL"  # < 0.35


class GateStatus(str, Enum):
    """Status of regime gates."""

    PASS = "PASS"  # Gate passed, entry allowed
    BLOCKED = "BLOCKED"  # Gate blocked entry
    REDUCED = "REDUCED"  # Score reduced due to regime
    BOOSTED = "BOOSTED"  # Score boosted due to regime


# =============================================================================
# COMPONENT SCORES
# =============================================================================


@dataclass
class ComponentScore:
    """Score from a single component."""

    name: str
    raw_score: float  # 0.0 - 1.0
    weight: float
    weighted_score: float  # raw_score * weight
    direction: ScoreDirection  # Direction this component suggests
    details: str = ""
    values: Dict[str, Any] = field(default_factory=dict)

    @property
    def contribution_pct(self) -> float:
        """Contribution percentage to final score."""
        return self.weighted_score * 100


@dataclass
class GateResult:
    """Result of gate evaluation."""

    status: GateStatus
    reason: str
    modifier: float = 0.0  # Score modifier (-1.0 = block, 0.0 = pass, +0.1 = boost 10%)
    allows_entry: bool = True

    @classmethod
    def passed(cls) -> "GateResult":
        return cls(status=GateStatus.PASS, reason="All gates passed", allows_entry=True)

    @classmethod
    def blocked(cls, reason: str) -> "GateResult":
        return cls(status=GateStatus.BLOCKED, reason=reason, modifier=-1.0, allows_entry=False)

    @classmethod
    def reduced(cls, reason: str, penalty: float) -> "GateResult":
        return cls(status=GateStatus.REDUCED, reason=reason, modifier=penalty, allows_entry=True)

    @classmethod
    def boosted(cls, reason: str, boost: float) -> "GateResult":
        return cls(status=GateStatus.BOOSTED, reason=reason, modifier=boost, allows_entry=True)
