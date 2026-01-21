"""
Trigger & Exit Engine - Main Engine and Factory

Unified engine for entry triggers and exit management:
- Orchestrates EntryTriggerEvaluators for breakout/pullback/SFP
- Orchestrates ExitLevelCalculator for SL/TP/trailing
- Checks exit conditions (SL hit, TP hit, time stop, reversal)
- Manages trailing stop updates
- Global singleton factory

Module 5/5 of trigger_exit_engine.py split (Lines 373-397, 858-1074, 1106-end)
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    from src.core.trading_bot.entry_score_engine import EntryScoreResult

from src.core.trading_bot.entry_trigger_evaluators import EntryTriggerEvaluators
from src.core.trading_bot.exit_level_calculator import ExitLevelCalculator
from src.core.trading_bot.trigger_exit_config import (
    TriggerExitConfig,
    load_trigger_exit_config,
    save_trigger_exit_config,
)
from src.core.trading_bot.trigger_exit_types import (
    ExitLevels,
    ExitSignal,
    ExitType,
    TriggerResult,
    TriggerStatus,
    TriggerType,
)

logger = logging.getLogger(__name__)


# TRIGGER & EXIT ENGINE
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
        self.trigger_evaluators = EntryTriggerEvaluators(self.config)
        self.level_calculator = ExitLevelCalculator(self.config)
        logger.info("TriggerExitEngine initialized")

    # =========================================================================
    # ENTRY TRIGGERS (Delegated to EntryTriggerEvaluators)
    # =========================================================================

    def evaluate_breakout_trigger(self, df: pd.DataFrame, level, direction: str) -> TriggerResult:
        """Evaluate breakout trigger (delegated)."""
        return self.trigger_evaluators.evaluate_breakout_trigger(df, level, direction)

    def evaluate_pullback_trigger(self, df: pd.DataFrame, level, direction: str, atr: Optional[float] = None) -> TriggerResult:
        """Evaluate pullback trigger (delegated)."""
        return self.trigger_evaluators.evaluate_pullback_trigger(df, level, direction, atr)

    def evaluate_sfp_trigger(self, df: pd.DataFrame, level, direction: str) -> TriggerResult:
        """Evaluate SFP trigger (delegated)."""
        return self.trigger_evaluators.evaluate_sfp_trigger(df, level, direction)

    def find_best_trigger(self, df: pd.DataFrame, levels_result, entry_score, atr: Optional[float] = None) -> Optional[TriggerResult]:
        """Find best trigger from available levels (delegated)."""
        return self.trigger_evaluators.find_best_trigger(df, levels_result, entry_score, atr)

    # =========================================================================
    # EXIT LEVELS (Delegated to ExitLevelCalculator)
    # =========================================================================

    def calculate_exit_levels(
        self,
        entry_price: float,
        direction: str,
        atr: Optional[float] = None,
        levels_result=None,
    ) -> ExitLevels:
        """Calculate all exit levels for a position (delegated)."""
        return self.level_calculator.calculate_exit_levels(entry_price, direction, atr, levels_result)

    # =========================================================================
    # EXIT SIGNALS (Main Engine Logic)
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

        # Check all exit conditions in priority order
        exit_signal = (
            self._check_stop_loss(current_price, sl, direction) or
            self._check_take_profit(current_price, tp, direction) or
            self._check_partial_tp(current_price, exit_levels, sl, direction) or
            self._check_time_stop(entry_time, current_price) or
            self._check_signal_reversal(entry_score, direction, current_price)
        )

        if exit_signal:
            return exit_signal

        # No exit condition met
        return ExitSignal(
            should_exit=False,
            exit_type=ExitType.MANUAL,
            reason="No exit conditions met",
        )

    def _check_stop_loss(
        self, current_price: float, sl: float, direction: str
    ) -> Optional[ExitSignal]:
        """Check if stop loss was hit.

        Args:
            current_price: Current market price.
            sl: Stop loss level.
            direction: Position direction.

        Returns:
            ExitSignal if SL hit, None otherwise.
        """
        is_sl_hit = (
            (direction == "LONG" and current_price <= sl) or
            (direction == "SHORT" and current_price >= sl)
        )

        if is_sl_hit:
            return ExitSignal(
                should_exit=True,
                exit_type=ExitType.SL_HIT,
                reason=f"Stop Loss hit at {sl:.2f}",
                suggested_exit_price=sl,
            )
        return None

    def _check_take_profit(
        self, current_price: float, tp: float, direction: str
    ) -> Optional[ExitSignal]:
        """Check if take profit was hit.

        Args:
            current_price: Current market price.
            tp: Take profit level.
            direction: Position direction.

        Returns:
            ExitSignal if TP hit, None otherwise.
        """
        is_tp_hit = (
            (direction == "LONG" and current_price >= tp) or
            (direction == "SHORT" and current_price <= tp)
        )

        if is_tp_hit:
            return ExitSignal(
                should_exit=True,
                exit_type=ExitType.TP_HIT,
                reason=f"Take Profit hit at {tp:.2f}",
                suggested_exit_price=tp,
            )
        return None

    def _check_partial_tp(
        self, current_price: float, exit_levels: ExitLevels, sl: float, direction: str
    ) -> Optional[ExitSignal]:
        """Check if partial take profit was hit.

        Args:
            current_price: Current market price.
            exit_levels: Exit levels containing partial TP.
            sl: Current stop loss.
            direction: Position direction.

        Returns:
            ExitSignal if partial TP hit, None otherwise.
        """
        if not self.config.partial_tp_enabled or not exit_levels.partial_tp_1:
            return None

        is_partial_hit = (
            (direction == "LONG" and current_price >= exit_levels.partial_tp_1) or
            (direction == "SHORT" and current_price <= exit_levels.partial_tp_1)
        )

        if is_partial_hit:
            new_sl = (
                exit_levels.entry_price
                if self.config.move_sl_to_be_after_tp1
                else sl
            )
            return ExitSignal(
                should_exit=True,
                exit_type=ExitType.PARTIAL,
                reason=f"Partial TP1 at {exit_levels.partial_tp_1:.2f}",
                suggested_exit_price=current_price,
                is_partial=True,
                partial_percent=self.config.partial_tp_1_percent,
                new_sl=new_sl,
            )
        return None

    def _check_time_stop(
        self, entry_time: datetime, current_price: float
    ) -> Optional[ExitSignal]:
        """Check if max holding time exceeded.

        Args:
            entry_time: Position entry time.
            current_price: Current market price.

        Returns:
            ExitSignal if time stop hit, None otherwise.
        """
        if not self.config.time_stop_enabled:
            return None

        holding_time = datetime.now(timezone.utc) - entry_time
        if holding_time > timedelta(minutes=self.config.max_holding_minutes):
            return ExitSignal(
                should_exit=True,
                exit_type=ExitType.TIME_STOP,
                reason=f"Max holding time ({self.config.max_holding_minutes}min) exceeded",
                suggested_exit_price=current_price,
            )
        return None

    def _check_signal_reversal(
        self, entry_score: Optional["EntryScoreResult"], direction: str, current_price: float
    ) -> Optional[ExitSignal]:
        """Check if signal reversed direction.

        Args:
            entry_score: Latest entry score.
            direction: Current position direction.
            current_price: Current market price.

        Returns:
            ExitSignal if strong reversal detected, None otherwise.
        """
        if not entry_score or not entry_score.is_valid_for_entry:
            return None

        score_direction = entry_score.direction.value
        is_reversed = (
            score_direction != direction and
            score_direction != "NEUTRAL" and
            entry_score.final_score >= 0.6  # Strong reversal threshold
        )

        if is_reversed:
            return ExitSignal(
                should_exit=True,
                exit_type=ExitType.SIGNAL_REVERSAL,
                reason=f"Signal reversal: {score_direction} with score {entry_score.final_score:.2f}",
                suggested_exit_price=current_price,
            )
        return None

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
        self.trigger_evaluators.config = config
        self.level_calculator.config = config
        logger.info("TriggerExitEngine config updated")


# GLOBAL SINGLETON & FACTORY
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


# EXPORTS
__all__ = [
    # Main classes
    "TriggerExitEngine",
    "TriggerExitConfig",
    "ExitLevels",
    "ExitSignal",
    "TriggerResult",
    # Types (re-exported from trigger_exit_types)
    "TriggerType",
    "ExitType",
    "TriggerStatus",
    # Functions
    "get_trigger_exit_engine",
    "load_trigger_exit_config",
    "save_trigger_exit_config",
]
