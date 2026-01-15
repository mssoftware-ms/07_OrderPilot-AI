"""
Position Monitor Status - Callbacks & Status Queries.

Refactored from position_monitor.py.

Contains:
- Callback setters (exit, trailing, price)
- Status queries (position status, SL/TP distance)
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from .position_monitor import PositionMonitor
    from .position_monitor_types import ExitResult, MonitoredPosition


class PositionMonitorStatus:
    """Helper for callbacks and status queries."""

    def __init__(self, parent: PositionMonitor):
        self.parent = parent

    # === Callbacks ===

    def set_exit_callback(
        self,
        callback: Callable[[MonitoredPosition, ExitResult], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Exit-Events."""
        self.parent._on_exit_triggered = callback

    def set_trailing_callback(
        self,
        callback: Callable[[MonitoredPosition, Decimal, Decimal], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Trailing-Stop Updates."""
        self.parent._on_trailing_updated = callback

    def set_price_callback(
        self,
        callback: Callable[[MonitoredPosition], Awaitable[None]],
    ) -> None:
        """Setzt Callback für Preis-Updates."""
        self.parent._on_price_updated = callback

    # === Status ===

    def get_position_status(self) -> dict | None:
        """Gibt aktuellen Position-Status zurück."""
        if not self.parent._position:
            return None

        pos = self.parent._position
        return {
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": str(pos.entry_price),
            "current_price": str(pos.current_price) if pos.current_price else None,
            "quantity": str(pos.quantity),
            "stop_loss": str(pos.stop_loss),
            "take_profit": str(pos.take_profit),
            "initial_stop_loss": str(pos.initial_stop_loss),
            "trailing_enabled": pos.trailing_enabled,
            "trailing_activated": pos.trailing_activated,
            "unrealized_pnl": str(pos.unrealized_pnl),
            "unrealized_pnl_percent": pos.unrealized_pnl_percent,
            "entry_time": pos.entry_time.isoformat(),
            "duration_seconds": (
                datetime.now(timezone.utc) - pos.entry_time
            ).total_seconds(),
        }

    def get_sl_tp_distance(self) -> tuple[Decimal, Decimal] | None:
        """Gibt aktuelle Distanz zu SL und TP zurück."""
        if not self.parent._position or not self.parent._position.current_price:
            return None

        pos = self.parent._position
        price = pos.current_price

        if pos.side == "BUY":
            sl_distance = price - pos.stop_loss
            tp_distance = pos.take_profit - price
        else:
            sl_distance = pos.stop_loss - price
            tp_distance = price - pos.take_profit

        return sl_distance, tp_distance
