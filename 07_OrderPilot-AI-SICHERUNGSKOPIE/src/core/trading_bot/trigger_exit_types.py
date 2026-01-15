"""
Trigger & Exit Types - Enums and Data Classes

Defines core types for trigger/exit system:
- Enums: TriggerType, ExitType, TriggerStatus
- Data Classes: TriggerResult, ExitLevels, ExitSignal

Module 1/5 of trigger_exit_engine.py split (Lines 46-340)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


# =============================================================================
# ENUMS
# =============================================================================


class TriggerType(str, Enum):
    """Type of entry trigger."""
    BREAKOUT = "breakout"           # Level breakout
    PULLBACK = "pullback"           # Pullback to level after trend move
    SFP = "sfp"                     # Swing Failure Pattern
    MOMENTUM = "momentum"           # Pure momentum-based entry
    LIMIT_RETEST = "limit_retest"   # Limit order at retest level


class ExitType(str, Enum):
    """Type of exit."""
    SL_HIT = "sl_hit"               # Stop Loss reached
    TP_HIT = "tp_hit"               # Take Profit reached
    TRAILING = "trailing"           # Trailing Stop triggered
    SIGNAL_REVERSAL = "signal_reversal"  # Opposite signal
    TIME_STOP = "time_stop"         # Max holding time
    STRUCTURE_BREAK = "structure_break"  # Key level broken
    MANUAL = "manual"               # Manual exit
    PARTIAL = "partial"             # Partial take profit


class TriggerStatus(str, Enum):
    """Status of trigger evaluation."""
    TRIGGERED = "triggered"         # Trigger conditions met
    PENDING = "pending"             # Watching for trigger
    INVALID = "invalid"             # Conditions not met
    EXPIRED = "expired"             # Trigger expired


# =============================================================================
# RESULT DATACLASSES
# =============================================================================


@dataclass
class TriggerResult:
    """Result of trigger evaluation."""

    trigger_type: TriggerType
    status: TriggerStatus
    direction: str  # "LONG" or "SHORT"

    # Trigger details
    trigger_level: Optional[float] = None
    trigger_price: float = 0.0
    confidence: float = 0.0  # 0.0 - 1.0

    # Context
    level_id: Optional[str] = None
    level_strength: Optional[str] = None
    volume_confirmed: bool = False

    # Reasoning
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_triggered(self) -> bool:
        return self.status == TriggerStatus.TRIGGERED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_type": self.trigger_type.value,
            "status": self.status.value,
            "direction": self.direction,
            "trigger_level": self.trigger_level,
            "trigger_price": self.trigger_price,
            "confidence": round(self.confidence, 3),
            "level_id": self.level_id,
            "level_strength": self.level_strength,
            "volume_confirmed": self.volume_confirmed,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass
class ExitLevels:
    """Calculated exit levels for a position."""

    entry_price: float
    direction: str  # "LONG" or "SHORT"

    stop_loss: float
    take_profit: float

    # Optional partial TP
    partial_tp_1: Optional[float] = None

    # Calculation metadata
    atr: Optional[float] = None
    risk_reward_ratio: float = 1.5
    sl_method: str = "atr_based"
    tp_method: str = "atr_based"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_price": self.entry_price,
            "direction": self.direction,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "partial_tp_1": self.partial_tp_1,
            "atr": self.atr,
            "risk_reward_ratio": self.risk_reward_ratio,
            "sl_method": self.sl_method,
            "tp_method": self.tp_method,
        }


@dataclass
class ExitSignal:
    """Signal to exit a position."""

    should_exit: bool
    exit_type: ExitType
    reason: str

    suggested_exit_price: Optional[float] = None

    # Partial exit info
    is_partial: bool = False
    partial_percent: float = 100.0  # % of position to close
    new_sl: Optional[float] = None  # New SL after partial exit

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_exit": self.should_exit,
            "exit_type": self.exit_type.value,
            "reason": self.reason,
            "suggested_exit_price": self.suggested_exit_price,
            "is_partial": self.is_partial,
            "partial_percent": self.partial_percent,
            "new_sl": self.new_sl,
        }
