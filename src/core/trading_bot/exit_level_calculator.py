"""
Exit Level Calculator - SL/TP/Trailing Calculation

Calculates exit levels for positions:
- Stop Loss (ATR-based or percent-based)
- Take Profit (ATR-based or percent-based with minimum R:R)
- Trailing Stop activation level
- Partial TP levels
- Structure stops based on key levels

Module 4/5 of trigger_exit_engine.py split (Lines 756-852)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.trading_bot.level_engine import LevelsResult

from src.core.trading_bot.trigger_exit_config import TriggerExitConfig
from src.core.trading_bot.trigger_exit_types import ExitLevels

logger = logging.getLogger(__name__)


# EXIT LEVEL CALCULATOR
class ExitLevelCalculator:
    """
    Calculates SL/TP levels, trailing stops, and structure stops.

    Used by TriggerExitEngine to determine exit levels when entering
    a position based on ATR, percentage, or key level structures.
    """

    def __init__(self, config: TriggerExitConfig):
        """
        Initialize Exit Level Calculator.

        Args:
            config: Trigger/Exit configuration
        """
        self.config = config

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
        # Ensure valid ATR
        atr = self._ensure_valid_atr(atr, entry_price)

        # Calculate distances and methods
        sl_distance, sl_method = self._calculate_sl_distance(entry_price, atr)
        tp_distance, tp_method = self._calculate_tp_distance(entry_price, atr, sl_distance)

        # Calculate direction-specific levels
        levels = self._calculate_direction_levels(
            entry_price, direction, sl_distance, tp_distance
        )

        # Apply structure stop if enabled
        structure_stop = self._apply_structure_stop(
            entry_price, direction, levels["stop_loss"], atr, levels_result
        )
        if structure_stop is not None:
            levels["stop_loss"] = structure_stop
            levels["structure_stop"] = structure_stop

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(entry_price, sl_distance, tp_distance)

        # Build result
        return ExitLevels(
            entry_price=entry_price,
            direction=direction,
            stop_loss=levels["stop_loss"],
            take_profit=levels["take_profit"],
            trailing_activation=levels["trailing_activation"] if self.config.trailing_enabled else None,
            partial_tp_1=levels["partial_tp_1"],
            structure_stop=levels.get("structure_stop"),
            breakeven_price=entry_price,
            sl_distance=sl_distance,
            tp_distance=tp_distance,
            risk_reward=risk_metrics["risk_reward"],
            sl_percent=risk_metrics["sl_percent"],
            tp_percent=risk_metrics["tp_percent"],
            sl_method=sl_method,
            tp_method=tp_method,
        )

    def _ensure_valid_atr(self, atr: Optional[float], entry_price: float) -> float:
        """Ensure ATR is valid, use fallback if needed.

        Args:
            atr: ATR value or None.
            entry_price: Entry price for fallback.

        Returns:
            Valid ATR value.
        """
        if atr is None or atr <= 0:
            return entry_price * 0.01  # 1% fallback
        return atr

    def _calculate_sl_distance(
        self, entry_price: float, atr: float
    ) -> tuple[float, str]:
        """Calculate stop loss distance and method.

        Args:
            entry_price: Entry price.
            atr: ATR value.

        Returns:
            Tuple of (sl_distance, sl_method).
        """
        if self.config.sl_type == "atr_based":
            sl_distance = atr * self.config.sl_atr_multiplier
            sl_method = f"ATR x {self.config.sl_atr_multiplier}"
        else:
            sl_distance = entry_price * (self.config.sl_percent / 100)
            sl_method = f"{self.config.sl_percent}%"
        return sl_distance, sl_method

    def _calculate_tp_distance(
        self, entry_price: float, atr: float, sl_distance: float
    ) -> tuple[float, str]:
        """Calculate take profit distance with R:R enforcement.

        Args:
            entry_price: Entry price.
            atr: ATR value.
            sl_distance: Stop loss distance.

        Returns:
            Tuple of (tp_distance, tp_method).
        """
        if self.config.tp_type == "atr_based":
            tp_distance = atr * self.config.tp_atr_multiplier
            tp_method = f"ATR x {self.config.tp_atr_multiplier}"
        else:
            tp_distance = entry_price * (self.config.tp_percent / 100)
            tp_method = f"{self.config.tp_percent}%"

        # Enforce minimum R:R
        if sl_distance > 0:
            current_rr = tp_distance / sl_distance
            if current_rr < self.config.min_risk_reward:
                tp_distance = sl_distance * self.config.min_risk_reward

        return tp_distance, tp_method

    def _calculate_direction_levels(
        self, entry_price: float, direction: str, sl_distance: float, tp_distance: float
    ) -> dict:
        """Calculate all levels for given direction.

        Args:
            entry_price: Entry price.
            direction: "LONG" or "SHORT".
            sl_distance: Stop loss distance.
            tp_distance: Take profit distance.

        Returns:
            Dictionary with all calculated levels.
        """
        if direction == "LONG":
            return {
                "stop_loss": entry_price - sl_distance,
                "take_profit": entry_price + tp_distance,
                "trailing_activation": entry_price + (
                    entry_price * self.config.trailing_activation_profit_pct / 100
                ),
                "partial_tp_1": (
                    entry_price + (sl_distance * self.config.partial_tp_1_rr)
                    if self.config.partial_tp_enabled
                    else None
                ),
            }
        else:
            return {
                "stop_loss": entry_price + sl_distance,
                "take_profit": entry_price - tp_distance,
                "trailing_activation": entry_price - (
                    entry_price * self.config.trailing_activation_profit_pct / 100
                ),
                "partial_tp_1": (
                    entry_price - (sl_distance * self.config.partial_tp_1_rr)
                    if self.config.partial_tp_enabled
                    else None
                ),
            }

    def _apply_structure_stop(
        self,
        entry_price: float,
        direction: str,
        stop_loss: float,
        atr: float,
        levels_result: Optional["LevelsResult"],
    ) -> Optional[float]:
        """Apply structure-based stop if enabled and tighter.

        Args:
            entry_price: Entry price.
            direction: "LONG" or "SHORT".
            stop_loss: Current stop loss.
            atr: ATR value.
            levels_result: Levels result for structure.

        Returns:
            Updated stop loss or None if no change.
        """
        if not self.config.structure_stop_enabled or not levels_result:
            return None

        buffer = atr * self.config.structure_stop_buffer_atr

        if direction == "LONG":
            support = levels_result.get_nearest_support(entry_price)
            if support and support.price_low < entry_price:
                structure_stop = support.price_low - buffer
                # Use structure stop if tighter (higher for long)
                if structure_stop > stop_loss:
                    return structure_stop
        else:
            resistance = levels_result.get_nearest_resistance(entry_price)
            if resistance and resistance.price_high > entry_price:
                structure_stop = resistance.price_high + buffer
                # Use structure stop if tighter (lower for short)
                if structure_stop < stop_loss:
                    return structure_stop

        return None

    def _calculate_risk_metrics(
        self, entry_price: float, sl_distance: float, tp_distance: float
    ) -> dict:
        """Calculate risk metrics (percentages and R:R).

        Args:
            entry_price: Entry price.
            sl_distance: Stop loss distance.
            tp_distance: Take profit distance.

        Returns:
            Dictionary with risk metrics.
        """
        return {
            "sl_percent": (sl_distance / entry_price) * 100,
            "tp_percent": (tp_distance / entry_price) * 100,
            "risk_reward": tp_distance / sl_distance if sl_distance > 0 else 0,
        }
