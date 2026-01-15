"""
Position Monitor Trailing - Trailing Stop Logic.

Refactored from position_monitor.py.

Contains:
- update_trailing_stop: ATR-based trailing stop updates
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .position_monitor import PositionMonitor

logger = logging.getLogger(__name__)


class PositionMonitorTrailing:
    """Helper for trailing stop logic."""

    def __init__(self, parent: PositionMonitor):
        self.parent = parent

    async def update_trailing_stop(self, price: Decimal) -> None:
        """Aktualisiert Trailing Stop wenn nötig."""
        pos = self.parent._position
        if not pos or not pos.trailing_atr or not self.parent.risk_manager:
            return

        # Prüfe ob Trailing aktiviert werden soll
        new_sl, was_updated = self.parent.risk_manager.adjust_sl_for_trailing(
            current_price=price,
            current_sl=pos.stop_loss,
            entry_price=pos.entry_price,
            side=pos.side,
            atr=pos.trailing_atr,
        )

        if was_updated:
            old_sl = pos.stop_loss
            pos.stop_loss = new_sl
            pos.trailing_activated = True

            logger.info(
                f"Trailing stop updated: {old_sl} -> {new_sl} (Price: {price})"
            )

            # Trade Log aktualisieren
            if pos.trade_log:
                pos.trade_log.record_trailing_stop_update(
                    old_sl=float(old_sl),
                    new_sl=float(new_sl),
                    trigger_price=float(price),
                )

            # Callback
            if self.parent._on_trailing_updated:
                await self.parent._on_trailing_updated(pos, old_sl, new_sl)
