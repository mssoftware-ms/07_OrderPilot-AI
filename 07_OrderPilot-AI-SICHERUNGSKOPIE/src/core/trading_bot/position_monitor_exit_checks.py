"""
Position Monitor Exit Checks - Exit Condition Checking.

Refactored from position_monitor.py.

Contains:
- check_exit_conditions: SL/TP checks
- trigger_manual_exit: Manual exit
- trigger_session_end_exit: Session end exit
- trigger_signal_exit: Signal reversal exit
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from .position_monitor_types import ExitResult, ExitTrigger

if TYPE_CHECKING:
    from .position_monitor import PositionMonitor


class PositionMonitorExitChecks:
    """Helper for exit condition checking."""

    def __init__(self, parent: PositionMonitor):
        self.parent = parent

    def check_exit_conditions(self, price: Decimal) -> ExitResult:
        """Prüft alle Exit-Bedingungen."""
        pos = self.parent._position
        if not pos:
            return ExitResult(should_exit=False)

        # Stop Loss Check
        if pos.side == "BUY":
            if price <= pos.stop_loss:
                return ExitResult(
                    should_exit=True,
                    trigger=(
                        ExitTrigger.TRAILING_STOP
                        if pos.trailing_activated
                        else ExitTrigger.STOP_LOSS
                    ),
                    trigger_price=price,
                    reason=f"Price {price} hit SL {pos.stop_loss}",
                )
        else:  # SHORT
            if price >= pos.stop_loss:
                return ExitResult(
                    should_exit=True,
                    trigger=(
                        ExitTrigger.TRAILING_STOP
                        if pos.trailing_activated
                        else ExitTrigger.STOP_LOSS
                    ),
                    trigger_price=price,
                    reason=f"Price {price} hit SL {pos.stop_loss}",
                )

        # Take Profit Check
        if pos.side == "BUY":
            if price >= pos.take_profit:
                return ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.TAKE_PROFIT,
                    trigger_price=price,
                    reason=f"Price {price} hit TP {pos.take_profit}",
                )
        else:  # SHORT
            if price <= pos.take_profit:
                return ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.TAKE_PROFIT,
                    trigger_price=price,
                    reason=f"Price {price} hit TP {pos.take_profit}",
                )

        return ExitResult(should_exit=False)

    def trigger_manual_exit(self, reason: str = "Manual exit") -> ExitResult:
        """
        Triggert manuellen Exit.

        Returns:
            ExitResult für manuellen Exit
        """
        if not self.parent._position:
            return ExitResult(should_exit=False, reason="No position to exit")

        return ExitResult(
            should_exit=True,
            trigger=ExitTrigger.MANUAL,
            trigger_price=self.parent._position.current_price,
            reason=reason,
        )

    def trigger_session_end_exit(self) -> ExitResult:
        """
        Triggert Session-Ende Exit.

        Returns:
            ExitResult für Session-Ende
        """
        if not self.parent._position:
            return ExitResult(should_exit=False, reason="No position to exit")

        return ExitResult(
            should_exit=True,
            trigger=ExitTrigger.SESSION_END,
            trigger_price=self.parent._position.current_price,
            reason="Session ended - closing position",
        )

    def trigger_signal_exit(self, signal_reason: str) -> ExitResult:
        """
        Triggert Exit durch Signal-Umkehr.

        Returns:
            ExitResult für Signal-Exit
        """
        if not self.parent._position:
            return ExitResult(should_exit=False, reason="No position to exit")

        return ExitResult(
            should_exit=True,
            trigger=ExitTrigger.SIGNAL_EXIT,
            trigger_price=self.parent._position.current_price,
            reason=signal_reason,
        )
