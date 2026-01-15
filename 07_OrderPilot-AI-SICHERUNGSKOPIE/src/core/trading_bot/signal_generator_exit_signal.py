"""
Signal Generator Exit Signal - Exit Signal Logic.

Refactored from signal_generator.py.

Contains:
- check_exit_signal: Checks if exit signal exists for current position
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .signal_types import SignalDirection

if TYPE_CHECKING:
    from .signal_generator import SignalGenerator


class SignalGeneratorExitSignal:
    """Helper for exit signal logic."""

    def __init__(self, parent: SignalGenerator):
        self.parent = parent

    def check_exit_signal(
        self, df: pd.DataFrame, current_position_side: str
    ) -> tuple[bool, str]:
        """
        Prüft ob Exit-Signal für bestehende Position vorliegt.

        Args:
            df: DataFrame mit OHLCV und Indikatoren
            current_position_side: "BUY" (Long) oder "SELL" (Short)

        Returns:
            Tuple (should_exit, reason)
        """
        if df.empty:
            return False, ""

        current = df.iloc[-1]

        # Generiere neues Signal
        new_signal = self.parent.generate_signal(df, require_regime_alignment=False)

        # Exit bei Signal-Umkehr
        if current_position_side == "BUY" and new_signal.direction == SignalDirection.SHORT:
            if new_signal.confluence_score >= self.parent.min_confluence:
                return True, "Signal reversal: SHORT signal while LONG"

        elif current_position_side == "SELL" and new_signal.direction == SignalDirection.LONG:
            if new_signal.confluence_score >= self.parent.min_confluence:
                return True, "Signal reversal: LONG signal while SHORT"

        # Exit bei starkem RSI Extremwert
        rsi = current.get("rsi_14") or current.get("RSI_14") or current.get("rsi")

        if rsi is not None:
            if current_position_side == "BUY" and rsi > 80:
                return True, f"RSI extremely overbought ({rsi:.1f})"
            elif current_position_side == "SELL" and rsi < 20:
                return True, f"RSI extremely oversold ({rsi:.1f})"

        return False, ""
