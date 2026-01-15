"""
Position Monitor Price - Price Update Handling.

Refactored from position_monitor.py.

Contains:
- on_price_update: Main price update handler
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from .position_monitor_types import ExitResult

if TYPE_CHECKING:
    from .position_monitor import PositionMonitor

logger = logging.getLogger(__name__)


class PositionMonitorPrice:
    """Helper for price update handling."""

    def __init__(self, parent: PositionMonitor):
        self.parent = parent

    async def on_price_update(self, price: Decimal) -> ExitResult | None:
        """
        Wird bei jedem Preis-Update aufgerufen.

        Args:
            price: Aktueller Marktpreis

        Returns:
            ExitResult wenn Exit getriggert wurde, sonst None
        """
        if not self.parent._position:
            return None

        # Update Position
        self.parent._position.update_price(price)

        # Callback für Preis-Update
        if self.parent._on_price_updated:
            await self.parent._on_price_updated(self.parent._position)

        # Prüfe Exit-Bedingungen
        exit_result = self.parent._exit_checks.check_exit_conditions(price)

        if exit_result.should_exit:
            logger.info(
                f"Exit triggered: {exit_result.trigger.value} "
                f"@ {exit_result.trigger_price} - {exit_result.reason}"
            )

            if self.parent._on_exit_triggered:
                await self.parent._on_exit_triggered(self.parent._position, exit_result)

            return exit_result

        # Prüfe Trailing Stop Update
        if self.parent._position.trailing_enabled and self.parent._position.trailing_atr:
            await self.parent._trailing.update_trailing_stop(price)

        return None
