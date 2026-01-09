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


# =============================================================================
# EXIT LEVEL CALCULATOR
# =============================================================================


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
