"""Backtest Runner State - Enums and Dataclasses.

Refactored from 832 LOC monolith using composition pattern.

Module 1/5 of backtest_runner.py split.

Contains:
- TradeStatus: Enum für Trade-Status
- OpenPosition: Dataclass für offene Positionen
- BacktestState: Dataclass für Backtest-Zustand
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.backtesting.execution_simulator import SimulatedFill
    from src.core.trading_bot.bot_config import OrderSide
    from .config import EquityPoint, Trade


class TradeStatus(Enum):
    """Status eines Trades."""

    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class OpenPosition:
    """Offene Position während des Backtests."""

    id: str
    symbol: str
    side: "OrderSide"
    entry_price: float
    entry_time: datetime
    size: float
    stop_loss: float | None
    take_profit: float | None
    leverage: int
    margin_used: float
    entry_fill: "SimulatedFill"
    entry_reason: str
    entry_fee: float

    # Laufende PnL (wird in _manage_positions aktualisiert)
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

    @property
    def trade_side(self) -> str:
        """Gibt 'long' oder 'short' zurück."""
        from src.core.trading_bot.bot_config import OrderSide

        return "long" if self.side == OrderSide.BUY else "short"


@dataclass
class BacktestState:
    """Zustand während des Backtests."""

    equity: float
    cash: float
    open_positions: list[OpenPosition] = field(default_factory=list)
    closed_trades: list["Trade"] = field(default_factory=list)
    equity_curve: list["EquityPoint"] = field(default_factory=list)
    daily_pnl: float = 0.0
    trade_count_today: int = 0
    loss_streak: int = 0
    cooldown_until: datetime | None = None
    last_reset_date: datetime | None = None
