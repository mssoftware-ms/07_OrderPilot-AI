"""
Risk Manager Daily Tracking - Daily Loss Tracking and Stats.

Refactored from risk_manager.py.

Contains:
- check_daily_loss_limit: Checks if daily loss limit is reached
- record_trade_result: Records trade PnL
- _check_daily_reset: Resets daily stats at new day
- get_daily_stats: Returns daily statistics
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .risk_manager import RiskManager

logger = logging.getLogger(__name__)


class RiskManagerDailyTracking:
    """Helper for daily loss tracking."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def check_daily_loss_limit(self, balance: Decimal) -> tuple[bool, str]:
        """
        Prüft ob Daily Loss Limit erreicht ist.

        Args:
            balance: Aktueller Kontostand

        Returns:
            Tuple (can_trade, reason)
        """
        self._check_daily_reset()

        # 100% = effektiv deaktiviert (für Paper Trading)
        if self.parent.max_daily_loss_percent >= Decimal("100"):
            return True, f"Daily loss limit disabled (100%). PnL: {self.parent._daily_realized_pnl} USDT"

        max_loss = balance * (self.parent.max_daily_loss_percent / Decimal("100"))

        if self.parent._daily_realized_pnl < 0 and abs(
            self.parent._daily_realized_pnl
        ) >= max_loss:
            logger.warning(
                f"Daily loss limit reached: {self.parent._daily_realized_pnl} USDT "
                f"(limit: {self.parent.max_daily_loss_percent}% = -{max_loss} USDT)"
            )
            return False, (
                f"Daily loss limit reached: {self.parent._daily_realized_pnl} USDT "
                f"(max: -{max_loss} USDT)"
            )

        return True, f"Daily PnL: {self.parent._daily_realized_pnl} USDT (limit: {self.parent.max_daily_loss_percent}%)"

    def record_trade_result(self, pnl: Decimal) -> None:
        """
        Zeichnet Trade-Ergebnis auf.

        Args:
            pnl: Realisierter PnL des Trades
        """
        self._check_daily_reset()
        self.parent._daily_realized_pnl += pnl
        self.parent._daily_trades += 1

        logger.info(
            f"Trade recorded. PnL: {pnl} USDT, "
            f"Daily total: {self.parent._daily_realized_pnl} USDT, "
            f"Trades today: {self.parent._daily_trades}"
        )

    def _check_daily_reset(self) -> None:
        """Prüft ob neuer Tag begonnen hat und setzt Daily Stats zurück."""
        now = datetime.now(timezone.utc)
        today = now.date()

        if self.parent._last_reset_date is None or self.parent._last_reset_date != today:
            logger.info(f"Daily stats reset. Previous: {self.parent._last_reset_date}")
            self.parent._daily_realized_pnl = Decimal("0")
            self.parent._daily_trades = 0
            self.parent._last_reset_date = today

    def get_daily_stats(self) -> dict:
        """Gibt tägliche Statistiken zurück."""
        self._check_daily_reset()
        return {
            "date": str(self.parent._last_reset_date),
            "realized_pnl": str(self.parent._daily_realized_pnl),
            "trades": self.parent._daily_trades,
            "max_loss_percent": str(self.parent.max_daily_loss_percent),
        }
