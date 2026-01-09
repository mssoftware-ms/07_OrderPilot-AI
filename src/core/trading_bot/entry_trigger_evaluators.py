"""
Entry Trigger Evaluators - Breakout, Pullback, SFP Logic

Evaluates entry trigger conditions:
- Breakout: Level breakout with volume confirmation
- Pullback: Pullback to level after trend move
- SFP: Swing Failure Pattern (wick extends beyond level, body closes inside)

Module 3/5 of trigger_exit_engine.py split (Lines 402-750)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional

import pandas as pd

if TYPE_CHECKING:
    from src.core.trading_bot.level_engine import Level, LevelsResult
    from src.core.trading_bot.entry_score_engine import EntryScoreResult

from src.core.trading_bot.trigger_exit_config import TriggerExitConfig
from src.core.trading_bot.trigger_exit_types import (
    TriggerResult,
    TriggerStatus,
    TriggerType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENTRY TRIGGER EVALUATORS
# =============================================================================


class EntryTriggerEvaluators:
    """
    Evaluates entry triggers: Breakout, Pullback, SFP.

    Used by TriggerExitEngine to determine entry conditions based on
    level interactions and price action patterns.
    """

    def __init__(self, config: TriggerExitConfig):
        """
        Initialize Entry Trigger Evaluators.

        Args:
            config: Trigger/Exit configuration
        """
        self.config = config

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
    # HELPERS
    # =========================================================================

    def _get_atr(self, current: pd.Series) -> Optional[float]:
        """Get ATR from current candle data."""
        for key in ["atr_14", "ATR_14", "atr", "ATR"]:
            val = current.get(key)
            if val is not None and not pd.isna(val):
                return float(val)
        return None
