"""
Trigger & Exit Engine - Entry Triggers und Exit Management

Phase 3.4-3.5: Trigger-Model und Exit-Engine Vereinheitlichung.

Entry Triggers:
- Breakout: Level-Durchbruch mit Volumen-Bestätigung
- Pullback: Pullback zu Level nach Breakout
- SFP (Swing Failure Pattern): Wick über Level, Close zurück

Exit Types:
- SL Hit: Stop Loss erreicht
- TP Hit: Take Profit erreicht
- Trailing: ATR- oder Percent-basierter Trailing Stop
- Signal Reversal: Gegensignal vom Entry Score
- Time Stop: Max Holding Time erreicht
- Structure Stop: Preis unter/über nächstem Key Level
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .level_engine import Level, LevelsResult
    from .entry_score_engine import EntryScoreResult

logger = logging.getLogger(__name__)


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
# CONFIG
# =============================================================================


@dataclass
class TriggerExitConfig:
    """Configuration for Trigger and Exit Engine."""

    # Breakout Trigger Settings
    breakout_min_candle_close_pct: float = 0.25  # Min % close beyond level
    breakout_volume_multiplier: float = 1.2      # Min volume vs SMA20
    breakout_confirmation_candles: int = 1       # Candles to confirm

    # Pullback Trigger Settings
    pullback_max_distance_atr: float = 0.5       # Max ATR distance for pullback
    pullback_min_strength: float = 0.3           # Min level strength
    pullback_patience_candles: int = 5           # Candles to wait for pullback

    # SFP Trigger Settings
    sfp_wick_min_pct: float = 0.3                # Min wick beyond level %
    sfp_body_inside_pct: float = 75.0            # Body % must be inside level
    sfp_quick_reversal_candles: int = 2          # Max candles for quick reversal

    # Exit Settings - SL/TP
    sl_type: str = "atr_based"                   # "atr_based" or "percent_based"
    tp_type: str = "atr_based"
    sl_atr_multiplier: float = 1.5
    tp_atr_multiplier: float = 2.5
    sl_percent: float = 0.5                      # Fallback percent
    tp_percent: float = 1.5
    min_risk_reward: float = 1.5                 # Min R:R ratio

    # Exit Settings - Trailing Stop
    trailing_enabled: bool = True
    trailing_type: str = "atr_based"             # "atr_based" or "percent_based"
    trailing_atr_multiplier: float = 1.0
    trailing_percent: float = 0.3
    trailing_activation_profit_pct: float = 0.5  # Activate after X% profit
    trailing_step_percent: float = 0.1           # Min step size

    # Exit Settings - Time Stop
    time_stop_enabled: bool = True
    max_holding_minutes: int = 480               # 8 hours default

    # Exit Settings - Structure Stop
    structure_stop_enabled: bool = True
    structure_stop_buffer_atr: float = 0.2       # Buffer below/above structure

    # Partial Take Profit
    partial_tp_enabled: bool = False
    partial_tp_1_percent: float = 50.0           # Close 50% at TP1
    partial_tp_1_rr: float = 1.0                 # TP1 at 1R
    move_sl_to_be_after_tp1: bool = True         # Move SL to breakeven

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "breakout": {
                "min_candle_close_pct": self.breakout_min_candle_close_pct,
                "volume_multiplier": self.breakout_volume_multiplier,
                "confirmation_candles": self.breakout_confirmation_candles,
            },
            "pullback": {
                "max_distance_atr": self.pullback_max_distance_atr,
                "min_strength": self.pullback_min_strength,
                "patience_candles": self.pullback_patience_candles,
            },
            "sfp": {
                "wick_min_pct": self.sfp_wick_min_pct,
                "body_inside_pct": self.sfp_body_inside_pct,
                "quick_reversal_candles": self.sfp_quick_reversal_candles,
            },
            "sl_tp": {
                "sl_type": self.sl_type,
                "tp_type": self.tp_type,
                "sl_atr_multiplier": self.sl_atr_multiplier,
                "tp_atr_multiplier": self.tp_atr_multiplier,
                "sl_percent": self.sl_percent,
                "tp_percent": self.tp_percent,
                "min_risk_reward": self.min_risk_reward,
            },
            "trailing": {
                "enabled": self.trailing_enabled,
                "type": self.trailing_type,
                "atr_multiplier": self.trailing_atr_multiplier,
                "percent": self.trailing_percent,
                "activation_profit_pct": self.trailing_activation_profit_pct,
                "step_percent": self.trailing_step_percent,
            },
            "time_stop": {
                "enabled": self.time_stop_enabled,
                "max_holding_minutes": self.max_holding_minutes,
            },
            "structure_stop": {
                "enabled": self.structure_stop_enabled,
                "buffer_atr": self.structure_stop_buffer_atr,
            },
            "partial_tp": {
                "enabled": self.partial_tp_enabled,
                "tp1_percent": self.partial_tp_1_percent,
                "tp1_rr": self.partial_tp_1_rr,
                "move_sl_to_be": self.move_sl_to_be_after_tp1,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerExitConfig":
        """Create from dictionary."""
        config = cls()

        if "breakout" in data:
            b = data["breakout"]
            config.breakout_min_candle_close_pct = b.get("min_candle_close_pct", config.breakout_min_candle_close_pct)
            config.breakout_volume_multiplier = b.get("volume_multiplier", config.breakout_volume_multiplier)
            config.breakout_confirmation_candles = b.get("confirmation_candles", config.breakout_confirmation_candles)

        if "pullback" in data:
            p = data["pullback"]
            config.pullback_max_distance_atr = p.get("max_distance_atr", config.pullback_max_distance_atr)
            config.pullback_min_strength = p.get("min_strength", config.pullback_min_strength)
            config.pullback_patience_candles = p.get("patience_candles", config.pullback_patience_candles)

        if "sfp" in data:
            s = data["sfp"]
            config.sfp_wick_min_pct = s.get("wick_min_pct", config.sfp_wick_min_pct)
            config.sfp_body_inside_pct = s.get("body_inside_pct", config.sfp_body_inside_pct)
            config.sfp_quick_reversal_candles = s.get("quick_reversal_candles", config.sfp_quick_reversal_candles)

        if "sl_tp" in data:
            st = data["sl_tp"]
            config.sl_type = st.get("sl_type", config.sl_type)
            config.tp_type = st.get("tp_type", config.tp_type)
            config.sl_atr_multiplier = st.get("sl_atr_multiplier", config.sl_atr_multiplier)
            config.tp_atr_multiplier = st.get("tp_atr_multiplier", config.tp_atr_multiplier)
            config.sl_percent = st.get("sl_percent", config.sl_percent)
            config.tp_percent = st.get("tp_percent", config.tp_percent)
            config.min_risk_reward = st.get("min_risk_reward", config.min_risk_reward)

        if "trailing" in data:
            t = data["trailing"]
            config.trailing_enabled = t.get("enabled", config.trailing_enabled)
            config.trailing_type = t.get("type", config.trailing_type)
            config.trailing_atr_multiplier = t.get("atr_multiplier", config.trailing_atr_multiplier)
            config.trailing_percent = t.get("percent", config.trailing_percent)
            config.trailing_activation_profit_pct = t.get("activation_profit_pct", config.trailing_activation_profit_pct)
            config.trailing_step_percent = t.get("step_percent", config.trailing_step_percent)

        if "time_stop" in data:
            ts = data["time_stop"]
            config.time_stop_enabled = ts.get("enabled", config.time_stop_enabled)
            config.max_holding_minutes = ts.get("max_holding_minutes", config.max_holding_minutes)

        if "structure_stop" in data:
            ss = data["structure_stop"]
            config.structure_stop_enabled = ss.get("enabled", config.structure_stop_enabled)
            config.structure_stop_buffer_atr = ss.get("buffer_atr", config.structure_stop_buffer_atr)

        if "partial_tp" in data:
            pt = data["partial_tp"]
            config.partial_tp_enabled = pt.get("enabled", config.partial_tp_enabled)
            config.partial_tp_1_percent = pt.get("tp1_percent", config.partial_tp_1_percent)
            config.partial_tp_1_rr = pt.get("tp1_rr", config.partial_tp_1_rr)
            config.move_sl_to_be_after_tp1 = pt.get("move_sl_to_be", config.move_sl_to_be_after_tp1)

        return config


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

    # Optional levels
    trailing_activation: Optional[float] = None
    partial_tp_1: Optional[float] = None
    structure_stop: Optional[float] = None
    breakeven_price: Optional[float] = None

    # Risk metrics
    sl_distance: float = 0.0
    tp_distance: float = 0.0
    risk_reward: float = 0.0
    sl_percent: float = 0.0
    tp_percent: float = 0.0

    # Method used
    sl_method: str = "atr_based"
    tp_method: str = "atr_based"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_price": self.entry_price,
            "direction": self.direction,
            "stop_loss": round(self.stop_loss, 2),
            "take_profit": round(self.take_profit, 2),
            "trailing_activation": round(self.trailing_activation, 2) if self.trailing_activation else None,
            "partial_tp_1": round(self.partial_tp_1, 2) if self.partial_tp_1 else None,
            "structure_stop": round(self.structure_stop, 2) if self.structure_stop else None,
            "breakeven_price": round(self.breakeven_price, 2) if self.breakeven_price else None,
            "risk_metrics": {
                "sl_distance": round(self.sl_distance, 2),
                "tp_distance": round(self.tp_distance, 2),
                "risk_reward": round(self.risk_reward, 2),
                "sl_percent": round(self.sl_percent, 3),
                "tp_percent": round(self.tp_percent, 3),
            },
            "methods": {
                "sl_method": self.sl_method,
                "tp_method": self.tp_method,
            }
        }


@dataclass
class ExitSignal:
    """Signal to exit a position."""

    should_exit: bool
    exit_type: ExitType
    reason: str

    suggested_exit_price: Optional[float] = None
    is_partial: bool = False
    partial_percent: float = 100.0

    # New levels after partial exit
    new_sl: Optional[float] = None
    new_tp: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_exit": self.should_exit,
            "exit_type": self.exit_type.value,
            "reason": self.reason,
            "suggested_exit_price": self.suggested_exit_price,
            "is_partial": self.is_partial,
            "partial_percent": self.partial_percent,
        }


# =============================================================================
# TRIGGER & EXIT ENGINE
# =============================================================================


class TriggerExitEngine:
    """
    Unified engine for entry triggers and exit management.

    Entry Triggers:
    - Evaluates market conditions against defined trigger types
    - Uses LevelEngine output for level-based triggers
    - Confirms triggers with volume and price action

    Exit Management:
    - Calculates SL/TP levels (ATR or percent based)
    - Manages trailing stops
    - Checks for exit conditions in real-time
    """

    def __init__(self, config: Optional[TriggerExitConfig] = None):
        """
        Initialize Trigger & Exit Engine.

        Args:
            config: Optional configuration
        """
        self.config = config or TriggerExitConfig()
        logger.info("TriggerExitEngine initialized")

    # =========================================================================
    # ENTRY TRIGGERS
    # =========================================================================

    def evaluate_breakout_trigger(
        self,
        df: pd.DataFrame,
        level: "Level",
        direction: str,
    ) -> TriggerResult:
        """
        Evaluate breakout trigger for a level.

        Breakout conditions:
        1. Price closes beyond level
        2. Close is at least X% beyond level (momentum)
        3. Volume is above average (confirmation)

        Args:
            df: OHLCV DataFrame
            level: Level to evaluate breakout from
            direction: "LONG" (breakout above resistance) or "SHORT" (below support)

        Returns:
            TriggerResult
        """
        if df.empty or len(df) < 2:
            return TriggerResult(
                trigger_type=TriggerType.BREAKOUT,
                status=TriggerStatus.INVALID,
                direction=direction,
                reason="Insufficient data",
            )

        current = df.iloc[-1]
        close = float(current["close"])
        volume = current.get("volume", 0)
        volume_sma = current.get("volume_sma_20") or current.get("volume_sma")

        # Get level price
        level_price = (level.price_high + level.price_low) / 2

        # Check direction
        if direction == "LONG":
            # Breakout above resistance
            target_price = level.price_high
            is_beyond = close > target_price
            distance_pct = ((close - target_price) / target_price) * 100 if target_price > 0 else 0
        else:
            # Breakdown below support
            target_price = level.price_low
            is_beyond = close < target_price
            distance_pct = ((target_price - close) / target_price) * 100 if target_price > 0 else 0

        # Check breakout criteria
        min_distance = self.config.breakout_min_candle_close_pct
        has_breakout = is_beyond and distance_pct >= min_distance

        # Volume confirmation
        volume_confirmed = False
        if volume and volume_sma and volume_sma > 0:
            volume_ratio = volume / volume_sma
            volume_confirmed = volume_ratio >= self.config.breakout_volume_multiplier

        # Calculate confidence
        confidence = 0.0
        if has_breakout:
            confidence = 0.5  # Base confidence for breakout
            if volume_confirmed:
                confidence += 0.3
            # Stronger breakout = higher confidence
            confidence += min(0.2, distance_pct / 2)

        status = TriggerStatus.TRIGGERED if has_breakout and volume_confirmed else TriggerStatus.PENDING

        return TriggerResult(
            trigger_type=TriggerType.BREAKOUT,
            status=status,
            direction=direction,
            trigger_level=level_price,
            trigger_price=close,
            confidence=min(1.0, confidence),
            level_id=level.id,
            level_strength=level.strength.value if hasattr(level.strength, "value") else str(level.strength),
            volume_confirmed=volume_confirmed,
            reason=f"Breakout {'confirmed' if status == TriggerStatus.TRIGGERED else 'pending'} at {level_price:.2f}",
            details={
                "distance_pct": round(distance_pct, 3),
                "volume_ratio": round(volume / volume_sma, 2) if volume and volume_sma else None,
                "required_distance": min_distance,
            }
        )

    def evaluate_pullback_trigger(
        self,
        df: pd.DataFrame,
        level: "Level",
        direction: str,
        atr: Optional[float] = None,
    ) -> TriggerResult:
        """
        Evaluate pullback trigger to a level.

        Pullback conditions:
        1. Price previously moved away from level
        2. Price now returns to level zone
        3. Level is strong enough

        Args:
            df: OHLCV DataFrame
            level: Level to evaluate pullback to
            direction: "LONG" (pullback to support) or "SHORT" (to resistance)
            atr: ATR value for distance calculation

        Returns:
            TriggerResult
        """
        if df.empty or len(df) < 5:
            return TriggerResult(
                trigger_type=TriggerType.PULLBACK,
                status=TriggerStatus.INVALID,
                direction=direction,
                reason="Insufficient data",
            )

        current = df.iloc[-1]
        close = float(current["close"])
        low = float(current["low"])
        high = float(current["high"])

        # Calculate ATR if not provided
        if atr is None:
            atr = self._get_atr(current)
        if atr is None or atr <= 0:
            atr = close * 0.01  # Fallback 1%

        # Level zone
        level_high = level.price_high
        level_low = level.price_low
        max_distance = atr * self.config.pullback_max_distance_atr

        # Check if in pullback zone
        if direction == "LONG":
            # Pullback to support - low should touch zone
            in_zone = low <= level_high + max_distance and close >= level_low
            distance_to_level = close - level_high
        else:
            # Pullback to resistance - high should touch zone
            in_zone = high >= level_low - max_distance and close <= level_high
            distance_to_level = level_low - close

        # Level strength check
        level_strength_value = 0.5
        if hasattr(level, "strength"):
            strength_map = {"key": 1.0, "strong": 0.8, "moderate": 0.6, "weak": 0.3}
            strength_str = level.strength.value if hasattr(level.strength, "value") else str(level.strength)
            level_strength_value = strength_map.get(strength_str.lower(), 0.5)

        is_strong_enough = level_strength_value >= self.config.pullback_min_strength

        # Calculate confidence
        confidence = 0.0
        if in_zone:
            confidence = 0.4
            if is_strong_enough:
                confidence += 0.3
            # Closer to level = higher confidence
            if atr > 0:
                proximity_bonus = max(0, 0.3 - (abs(distance_to_level) / atr) * 0.15)
                confidence += proximity_bonus

        status = TriggerStatus.TRIGGERED if in_zone and is_strong_enough else TriggerStatus.PENDING

        return TriggerResult(
            trigger_type=TriggerType.PULLBACK,
            status=status,
            direction=direction,
            trigger_level=(level_high + level_low) / 2,
            trigger_price=close,
            confidence=min(1.0, confidence),
            level_id=level.id,
            level_strength=level.strength.value if hasattr(level.strength, "value") else str(level.strength),
            volume_confirmed=False,  # Pullback doesn't require volume
            reason=f"Pullback {'to' if in_zone else 'watching'} level {level_low:.2f}-{level_high:.2f}",
            details={
                "distance_to_level": round(distance_to_level, 2),
                "max_distance": round(max_distance, 2),
                "in_zone": in_zone,
                "level_strength": level_strength_value,
            }
        )

    def evaluate_sfp_trigger(
        self,
        df: pd.DataFrame,
        level: "Level",
        direction: str,
    ) -> TriggerResult:
        """
        Evaluate Swing Failure Pattern (SFP) trigger.

        SFP conditions:
        1. Wick extends beyond level (fake breakout)
        2. Body closes back inside level
        3. Quick reversal within N candles

        Args:
            df: OHLCV DataFrame
            level: Level to evaluate SFP at
            direction: "LONG" (bearish SFP at resistance) or "SHORT" (bullish SFP at support)

        Returns:
            TriggerResult
        """
        if df.empty or len(df) < 3:
            return TriggerResult(
                trigger_type=TriggerType.SFP,
                status=TriggerStatus.INVALID,
                direction=direction,
                reason="Insufficient data",
            )

        current = df.iloc[-1]
        close = float(current["close"])
        open_price = float(current["open"])
        high = float(current["high"])
        low = float(current["low"])

        body_high = max(open_price, close)
        body_low = min(open_price, close)
        candle_range = high - low

        if candle_range <= 0:
            return TriggerResult(
                trigger_type=TriggerType.SFP,
                status=TriggerStatus.INVALID,
                direction=direction,
                reason="Invalid candle range",
            )

        level_high = level.price_high
        level_low = level.price_low
        level_mid = (level_high + level_low) / 2

        # SFP evaluation
        if direction == "LONG":
            # Bullish SFP: wick below support, close back above
            wick_beyond = low < level_low
            wick_extension = level_low - low if wick_beyond else 0
            body_inside = body_low >= level_low
            wick_pct = (wick_extension / candle_range) * 100 if candle_range > 0 else 0
        else:
            # Bearish SFP: wick above resistance, close back below
            wick_beyond = high > level_high
            wick_extension = high - level_high if wick_beyond else 0
            body_inside = body_high <= level_high
            wick_pct = (wick_extension / candle_range) * 100 if candle_range > 0 else 0

        # Check SFP criteria
        min_wick = self.config.sfp_wick_min_pct
        has_sfp = wick_beyond and body_inside and wick_pct >= min_wick

        # Calculate confidence
        confidence = 0.0
        if has_sfp:
            confidence = 0.5  # Base for valid SFP
            # Larger wick = stronger rejection
            confidence += min(0.3, wick_pct / 100)
            # Check for reversal candle pattern
            if direction == "LONG" and close > open_price:
                confidence += 0.2  # Bullish close
            elif direction == "SHORT" and close < open_price:
                confidence += 0.2  # Bearish close

        status = TriggerStatus.TRIGGERED if has_sfp else TriggerStatus.PENDING

        return TriggerResult(
            trigger_type=TriggerType.SFP,
            status=status,
            direction=direction,
            trigger_level=level_mid,
            trigger_price=close,
            confidence=min(1.0, confidence),
            level_id=level.id,
            level_strength=level.strength.value if hasattr(level.strength, "value") else str(level.strength),
            volume_confirmed=False,
            reason=f"SFP {'detected' if has_sfp else 'not detected'} at {level_mid:.2f}",
            details={
                "wick_beyond": wick_beyond,
                "wick_extension": round(wick_extension, 2),
                "wick_pct": round(wick_pct, 2),
                "body_inside": body_inside,
                "required_wick_pct": min_wick,
            }
        )

    def find_best_trigger(
        self,
        df: pd.DataFrame,
        levels_result: "LevelsResult",
        entry_score: "EntryScoreResult",
        atr: Optional[float] = None,
    ) -> Optional[TriggerResult]:
        """
        Find the best entry trigger from available levels and entry score.

        Args:
            df: OHLCV DataFrame
            levels_result: Detected levels from LevelEngine
            entry_score: Entry score result
            atr: ATR value

        Returns:
            Best TriggerResult or None
        """
        if not entry_score.is_valid_for_entry:
            return None

        direction = entry_score.direction.value  # "LONG" or "SHORT"
        triggers: List[TriggerResult] = []

        # Get relevant levels
        if direction == "LONG":
            # Look for support levels (pullback) and resistance levels (breakout)
            support = levels_result.get_nearest_support()
            resistance = levels_result.get_nearest_resistance()

            if support:
                triggers.append(self.evaluate_pullback_trigger(df, support, direction, atr))
                triggers.append(self.evaluate_sfp_trigger(df, support, direction))

            if resistance:
                triggers.append(self.evaluate_breakout_trigger(df, resistance, direction))

        else:  # SHORT
            support = levels_result.get_nearest_support()
            resistance = levels_result.get_nearest_resistance()

            if resistance:
                triggers.append(self.evaluate_pullback_trigger(df, resistance, direction, atr))
                triggers.append(self.evaluate_sfp_trigger(df, resistance, direction))

            if support:
                triggers.append(self.evaluate_breakout_trigger(df, support, direction))

        # Filter triggered and sort by confidence
        triggered = [t for t in triggers if t.is_triggered]

        if not triggered:
            return None

        # Return highest confidence trigger
        return max(triggered, key=lambda t: t.confidence)

    # =========================================================================
    # EXIT LEVELS
    # =========================================================================

    def calculate_exit_levels(
        self,
        entry_price: float,
        direction: str,
        atr: Optional[float] = None,
        levels_result: Optional["LevelsResult"] = None,
    ) -> ExitLevels:
        """
        Calculate all exit levels for a position.

        Args:
            entry_price: Entry price
            direction: "LONG" or "SHORT"
            atr: ATR value (required for ATR-based exits)
            levels_result: Optional levels for structure stops

        Returns:
            ExitLevels with all calculated levels
        """
        # Default ATR fallback
        if atr is None or atr <= 0:
            atr = entry_price * 0.01  # 1% fallback

        # Calculate SL
        if self.config.sl_type == "atr_based":
            sl_distance = atr * self.config.sl_atr_multiplier
            sl_method = f"ATR x {self.config.sl_atr_multiplier}"
        else:
            sl_distance = entry_price * (self.config.sl_percent / 100)
            sl_method = f"{self.config.sl_percent}%"

        # Calculate TP
        if self.config.tp_type == "atr_based":
            tp_distance = atr * self.config.tp_atr_multiplier
            tp_method = f"ATR x {self.config.tp_atr_multiplier}"
        else:
            tp_distance = entry_price * (self.config.tp_percent / 100)
            tp_method = f"{self.config.tp_percent}%"

        # Ensure minimum R:R
        if sl_distance > 0:
            current_rr = tp_distance / sl_distance
            if current_rr < self.config.min_risk_reward:
                tp_distance = sl_distance * self.config.min_risk_reward

        # Direction-specific calculations
        if direction == "LONG":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
            trailing_activation = entry_price + (entry_price * self.config.trailing_activation_profit_pct / 100)
            partial_tp_1 = entry_price + (sl_distance * self.config.partial_tp_1_rr) if self.config.partial_tp_enabled else None
        else:
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
            trailing_activation = entry_price - (entry_price * self.config.trailing_activation_profit_pct / 100)
            partial_tp_1 = entry_price - (sl_distance * self.config.partial_tp_1_rr) if self.config.partial_tp_enabled else None

        # Structure stop (based on levels)
        structure_stop = None
        if self.config.structure_stop_enabled and levels_result:
            buffer = atr * self.config.structure_stop_buffer_atr
            if direction == "LONG":
                support = levels_result.get_nearest_support(entry_price)
                if support and support.price_low < entry_price:
                    structure_stop = support.price_low - buffer
                    # Use structure stop if tighter than ATR stop
                    if structure_stop > stop_loss:
                        stop_loss = structure_stop
            else:
                resistance = levels_result.get_nearest_resistance(entry_price)
                if resistance and resistance.price_high > entry_price:
                    structure_stop = resistance.price_high + buffer
                    if structure_stop < stop_loss:
                        stop_loss = structure_stop

        # Risk metrics
        sl_percent = (sl_distance / entry_price) * 100
        tp_percent = (tp_distance / entry_price) * 100
        risk_reward = tp_distance / sl_distance if sl_distance > 0 else 0

        return ExitLevels(
            entry_price=entry_price,
            direction=direction,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_activation=trailing_activation if self.config.trailing_enabled else None,
            partial_tp_1=partial_tp_1,
            structure_stop=structure_stop,
            breakeven_price=entry_price,
            sl_distance=sl_distance,
            tp_distance=tp_distance,
            risk_reward=risk_reward,
            sl_percent=sl_percent,
            tp_percent=tp_percent,
            sl_method=sl_method,
            tp_method=tp_method,
        )

    # =========================================================================
    # EXIT SIGNALS
    # =========================================================================

    def check_exit_conditions(
        self,
        current_price: float,
        exit_levels: ExitLevels,
        entry_time: datetime,
        current_sl: Optional[float] = None,
        entry_score: Optional["EntryScoreResult"] = None,
    ) -> ExitSignal:
        """
        Check all exit conditions for a position.

        Args:
            current_price: Current market price
            exit_levels: Calculated exit levels
            entry_time: When position was entered
            current_sl: Current stop loss (may differ from original if trailed)
            entry_score: Latest entry score for reversal check

        Returns:
            ExitSignal
        """
        direction = exit_levels.direction
        sl = current_sl or exit_levels.stop_loss
        tp = exit_levels.take_profit

        # Check Stop Loss
        if direction == "LONG":
            if current_price <= sl:
                return ExitSignal(
                    should_exit=True,
                    exit_type=ExitType.SL_HIT,
                    reason=f"Stop Loss hit at {sl:.2f}",
                    suggested_exit_price=sl,
                )
        else:
            if current_price >= sl:
                return ExitSignal(
                    should_exit=True,
                    exit_type=ExitType.SL_HIT,
                    reason=f"Stop Loss hit at {sl:.2f}",
                    suggested_exit_price=sl,
                )

        # Check Take Profit
        if direction == "LONG":
            if current_price >= tp:
                return ExitSignal(
                    should_exit=True,
                    exit_type=ExitType.TP_HIT,
                    reason=f"Take Profit hit at {tp:.2f}",
                    suggested_exit_price=tp,
                )
        else:
            if current_price <= tp:
                return ExitSignal(
                    should_exit=True,
                    exit_type=ExitType.TP_HIT,
                    reason=f"Take Profit hit at {tp:.2f}",
                    suggested_exit_price=tp,
                )

        # Check Partial TP
        if self.config.partial_tp_enabled and exit_levels.partial_tp_1:
            if direction == "LONG" and current_price >= exit_levels.partial_tp_1:
                return ExitSignal(
                    should_exit=True,
                    exit_type=ExitType.PARTIAL,
                    reason=f"Partial TP1 at {exit_levels.partial_tp_1:.2f}",
                    suggested_exit_price=current_price,
                    is_partial=True,
                    partial_percent=self.config.partial_tp_1_percent,
                    new_sl=exit_levels.entry_price if self.config.move_sl_to_be_after_tp1 else sl,
                )
            elif direction == "SHORT" and current_price <= exit_levels.partial_tp_1:
                return ExitSignal(
                    should_exit=True,
                    exit_type=ExitType.PARTIAL,
                    reason=f"Partial TP1 at {exit_levels.partial_tp_1:.2f}",
                    suggested_exit_price=current_price,
                    is_partial=True,
                    partial_percent=self.config.partial_tp_1_percent,
                    new_sl=exit_levels.entry_price if self.config.move_sl_to_be_after_tp1 else sl,
                )

        # Check Time Stop
        if self.config.time_stop_enabled:
            holding_time = datetime.now(timezone.utc) - entry_time
            if holding_time > timedelta(minutes=self.config.max_holding_minutes):
                return ExitSignal(
                    should_exit=True,
                    exit_type=ExitType.TIME_STOP,
                    reason=f"Max holding time ({self.config.max_holding_minutes}min) exceeded",
                    suggested_exit_price=current_price,
                )

        # Check Signal Reversal
        if entry_score and entry_score.is_valid_for_entry:
            score_direction = entry_score.direction.value
            if score_direction != direction and score_direction != "NEUTRAL":
                if entry_score.final_score >= 0.6:  # Strong reversal signal
                    return ExitSignal(
                        should_exit=True,
                        exit_type=ExitType.SIGNAL_REVERSAL,
                        reason=f"Signal reversal: {score_direction} with score {entry_score.final_score:.2f}",
                        suggested_exit_price=current_price,
                    )

        # No exit condition met
        return ExitSignal(
            should_exit=False,
            exit_type=ExitType.MANUAL,
            reason="No exit conditions met",
        )

    def calculate_trailing_stop(
        self,
        current_price: float,
        current_sl: float,
        entry_price: float,
        direction: str,
        atr: Optional[float] = None,
    ) -> tuple[float, bool]:
        """
        Calculate new trailing stop level.

        Args:
            current_price: Current market price
            current_sl: Current stop loss
            entry_price: Entry price
            direction: "LONG" or "SHORT"
            atr: ATR value

        Returns:
            Tuple (new_sl, was_updated)
        """
        if not self.config.trailing_enabled:
            return current_sl, False

        # Calculate activation threshold
        activation_pct = self.config.trailing_activation_profit_pct

        if direction == "LONG":
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            if profit_pct < activation_pct:
                return current_sl, False

            # Calculate trailing distance
            if self.config.trailing_type == "atr_based" and atr:
                trail_distance = atr * self.config.trailing_atr_multiplier
            else:
                trail_distance = current_price * (self.config.trailing_percent / 100)

            new_sl = current_price - trail_distance

            # Only move SL up, never down
            if new_sl > current_sl:
                # Check minimum step size
                step = ((new_sl - current_sl) / current_sl) * 100
                if step >= self.config.trailing_step_percent:
                    return new_sl, True

        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100
            if profit_pct < activation_pct:
                return current_sl, False

            if self.config.trailing_type == "atr_based" and atr:
                trail_distance = atr * self.config.trailing_atr_multiplier
            else:
                trail_distance = current_price * (self.config.trailing_percent / 100)

            new_sl = current_price + trail_distance

            # Only move SL down, never up
            if new_sl < current_sl:
                step = ((current_sl - new_sl) / current_sl) * 100
                if step >= self.config.trailing_step_percent:
                    return new_sl, True

        return current_sl, False

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_atr(self, current: pd.Series) -> Optional[float]:
        """Get ATR from current candle data."""
        for key in ["atr_14", "ATR_14", "atr", "ATR"]:
            val = current.get(key)
            if val is not None and not pd.isna(val):
                return float(val)
        return None

    def update_config(self, config: TriggerExitConfig) -> None:
        """Update engine configuration."""
        self.config = config
        logger.info("TriggerExitEngine config updated")


# =============================================================================
# GLOBAL SINGLETON & FACTORY
# =============================================================================

_global_engine: Optional[TriggerExitEngine] = None
_engine_lock = threading.Lock()


def get_trigger_exit_engine(config: Optional[TriggerExitConfig] = None) -> TriggerExitEngine:
    """Get global TriggerExitEngine singleton."""
    global _global_engine

    with _engine_lock:
        if _global_engine is None:
            _global_engine = TriggerExitEngine(config)
            logger.info("Global TriggerExitEngine created")
        return _global_engine


def load_trigger_exit_config(path: Optional[Path] = None) -> TriggerExitConfig:
    """Load config from JSON file."""
    if path is None:
        path = Path("config/trigger_exit_config.json")

    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return TriggerExitConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load trigger/exit config: {e}")

    return TriggerExitConfig()


def save_trigger_exit_config(config: TriggerExitConfig, path: Optional[Path] = None) -> bool:
    """Save config to JSON file."""
    if path is None:
        path = Path("config/trigger_exit_config.json")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Trigger/Exit config saved to {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save trigger/exit config: {e}")
        return False
