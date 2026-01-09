"""
Position Monitor Types - Types and Data Structures.

Refactored from position_monitor.py.

Contains:
- ExitTrigger: Exit trigger enum
- MonitoredPosition: Position dataclass with PnL tracking
- ExitResult: Exit result dataclass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .trade_logger import TradeLogEntry


class ExitTrigger(str, Enum):
    """Grund für Position-Exit."""

    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    SIGNAL_EXIT = "SIGNAL_EXIT"
    MANUAL = "MANUAL"
    SESSION_END = "SESSION_END"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    BOT_STOPPED = "BOT_STOPPED"


@dataclass
class MonitoredPosition:
    """Position mit Überwachungs-Details."""

    symbol: str
    side: str  # "BUY" (Long) oder "SELL" (Short)
    entry_price: Decimal
    quantity: Decimal
    entry_time: datetime

    # Stop Levels
    stop_loss: Decimal
    take_profit: Decimal
    initial_stop_loss: Decimal  # Original SL (vor Trailing)

    # Trailing Stop State
    trailing_enabled: bool = True
    trailing_activated: bool = False
    trailing_atr: Decimal | None = None

    # Current State
    current_price: Decimal | None = None
    unrealized_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    unrealized_pnl_percent: float = 0.0
    highest_price: Decimal | None = None  # Für Long Trailing
    lowest_price: Decimal | None = None  # Für Short Trailing

    # Trade Log Reference
    trade_log: "TradeLogEntry | None" = None

    def update_price(self, price: Decimal) -> None:
        """Aktualisiert Preis und berechnet PnL."""
        self.current_price = price

        # Update High/Low für Trailing
        if self.highest_price is None or price > self.highest_price:
            self.highest_price = price
        if self.lowest_price is None or price < self.lowest_price:
            self.lowest_price = price

        # PnL berechnen
        if self.side == "BUY":
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity

        if self.entry_price > 0:
            entry_value = self.entry_price * self.quantity
            self.unrealized_pnl_percent = float(self.unrealized_pnl / entry_value * 100)

    def to_dict(self) -> dict:
        """Serialisiert Position zu Dictionary für Persistenz."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": str(self.entry_price),
            "quantity": str(self.quantity),
            "entry_time": self.entry_time.isoformat(),
            "stop_loss": str(self.stop_loss),
            "take_profit": str(self.take_profit),
            "initial_stop_loss": str(self.initial_stop_loss),
            "trailing_enabled": self.trailing_enabled,
            "trailing_activated": self.trailing_activated,
            "trailing_atr": str(self.trailing_atr) if self.trailing_atr else None,
            "current_price": str(self.current_price) if self.current_price else None,
            "highest_price": str(self.highest_price) if self.highest_price else None,
            "lowest_price": str(self.lowest_price) if self.lowest_price else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonitoredPosition":
        """Deserialisiert Position aus Dictionary."""
        return cls(
            symbol=data["symbol"],
            side=data["side"],
            entry_price=Decimal(data["entry_price"]),
            quantity=Decimal(data["quantity"]),
            entry_time=datetime.fromisoformat(data["entry_time"]),
            stop_loss=Decimal(data["stop_loss"]),
            take_profit=Decimal(data["take_profit"]),
            initial_stop_loss=Decimal(data["initial_stop_loss"]),
            trailing_enabled=data.get("trailing_enabled", True),
            trailing_activated=data.get("trailing_activated", False),
            trailing_atr=(
                Decimal(data["trailing_atr"]) if data.get("trailing_atr") else None
            ),
            current_price=(
                Decimal(data["current_price"]) if data.get("current_price") else None
            ),
            highest_price=(
                Decimal(data["highest_price"]) if data.get("highest_price") else None
            ),
            lowest_price=(
                Decimal(data["lowest_price"]) if data.get("lowest_price") else None
            ),
        )


@dataclass
class ExitResult:
    """Ergebnis einer Exit-Prüfung."""

    should_exit: bool
    trigger: ExitTrigger | None = None
    trigger_price: Decimal | None = None
    reason: str = ""
