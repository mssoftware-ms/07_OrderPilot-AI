"""Bot Engine Statistics - Daily Reset and Trade Statistics.

Refactored from bot_engine.py.

Contains:
- _check_daily_reset: Check if new trading day and reset statistics
- _update_statistics: Update statistics after trade (wins/losses, PnL, drawdown)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .bot_types import BotStatistics
from .trade_logger import TradeLogEntry, TradeOutcome

if TYPE_CHECKING:
    from .bot_engine import TradingBotEngine

logger = logging.getLogger(__name__)


class BotEngineStatistics:
    """Helper for statistics management."""

    def __init__(self, parent: "TradingBotEngine"):
        self.parent = parent

    def _check_daily_reset(self) -> None:
        """Prüft ob neue Trading-Session (neuer Tag)."""
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.parent._stats.date != current_date:
            self.parent._stats = BotStatistics(date=current_date)
            self.parent._callbacks._log("New trading session started")

    def _update_statistics(self, trade_log: TradeLogEntry) -> None:
        """Aktualisiert Statistiken nach Trade."""
        self.parent._stats.trades_total += 1

        if trade_log.outcome == TradeOutcome.WIN:
            self.parent._stats.trades_won += 1
        elif trade_log.outcome == TradeOutcome.LOSS:
            self.parent._stats.trades_lost += 1
        else:
            self.parent._stats.trades_breakeven += 1

        if trade_log.net_pnl:
            self.parent._stats.total_pnl += trade_log.net_pnl

            # Drawdown tracking
            if self.parent._stats.total_pnl > self.parent._stats.peak_pnl:
                self.parent._stats.peak_pnl = self.parent._stats.total_pnl

            current_drawdown = self.parent._stats.peak_pnl - self.parent._stats.total_pnl
            if current_drawdown > self.parent._stats.max_drawdown:
                self.parent._stats.max_drawdown = current_drawdown

        # Risk Manager informieren
        if trade_log.net_pnl:
            self.parent.risk_manager.record_trade_result(trade_log.net_pnl)
