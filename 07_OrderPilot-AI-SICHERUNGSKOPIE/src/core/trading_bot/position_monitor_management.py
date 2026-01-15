"""
Position Monitor Management - Position Set/Clear/Restore.

Refactored from position_monitor.py.

Contains:
- set_position: Creates new monitored position
- clear_position: Clears monitored position
- restore_position: Restores position from saved data
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from .position_monitor_types import MonitoredPosition

if TYPE_CHECKING:
    from .position_monitor import PositionMonitor
    from .trade_logger import TradeLogEntry

logger = logging.getLogger(__name__)


class PositionMonitorManagement:
    """Helper for position management."""

    def __init__(self, parent: PositionMonitor):
        self.parent = parent

    def set_position(
        self,
        symbol: str,
        side: str,
        entry_price: Decimal,
        quantity: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
        trailing_atr: Decimal | None = None,
        trade_log: "TradeLogEntry | None" = None,
    ) -> MonitoredPosition:
        """
        Setzt neue zu überwachende Position.

        Args:
            symbol: Trading Symbol
            side: "BUY" oder "SELL"
            entry_price: Entry-Preis
            quantity: Position Size
            stop_loss: Stop Loss Preis
            take_profit: Take Profit Preis
            trailing_atr: ATR für Trailing Stop (None = kein Trailing)
            trade_log: Referenz zum Trade Log

        Returns:
            Erstellte MonitoredPosition
        """
        if self.parent._position is not None:
            logger.warning(
                f"Overwriting existing position {self.parent._position.symbol} "
                f"with new position {symbol}"
            )

        self.parent._position = MonitoredPosition(
            symbol=symbol,
            side=side.upper(),
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(timezone.utc),
            stop_loss=stop_loss,
            take_profit=take_profit,
            initial_stop_loss=stop_loss,
            trailing_enabled=trailing_atr is not None,
            trailing_atr=trailing_atr,
            current_price=entry_price,
            highest_price=entry_price,
            lowest_price=entry_price,
            trade_log=trade_log,
        )

        logger.info(
            f"Position monitoring started: {symbol} {side} @ {entry_price}, "
            f"SL: {stop_loss}, TP: {take_profit}, "
            f"Trailing: {'Yes' if trailing_atr else 'No'}"
        )

        return self.parent._position

    def clear_position(self) -> None:
        """Löscht überwachte Position."""
        if self.parent._position:
            logger.info(f"Position monitoring stopped: {self.parent._position.symbol}")
        self.parent._position = None

    def restore_position(self, position_data: dict) -> MonitoredPosition | None:
        """
        Stellt Position aus gespeicherten Daten wieder her.

        Args:
            position_data: Dictionary mit Position-Daten (von to_dict())

        Returns:
            Wiederhergestellte Position oder None bei Fehler
        """
        try:
            self.parent._position = MonitoredPosition.from_dict(position_data)
            logger.info(
                f"Position restored: {self.parent._position.symbol} {self.parent._position.side} "
                f"@ {self.parent._position.entry_price}, SL: {self.parent._position.stop_loss}, "
                f"TP: {self.parent._position.take_profit}"
            )
            return self.parent._position
        except Exception as e:
            logger.error(f"Failed to restore position: {e}")
            return None
