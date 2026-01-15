"""Risk Manager for Tradingbot.

Manages trading risk limits and tracking.
Tracks daily P&L, position count, loss streaks,
and enforces risk limits.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from .execution_types import RiskLimits, RiskState

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages trading risk limits and tracking.

    Tracks daily P&L, position count, loss streaks,
    and enforces risk limits.
    """

    def __init__(
        self,
        limits: RiskLimits | None = None,
        account_value: float = 10000.0
    ):
        """Initialize risk manager.

        Args:
            limits: Risk limit configuration
            account_value: Account value for calculations
        """
        self.limits = limits or RiskLimits()
        self.account_value = account_value
        self._state = RiskState()

        logger.info(
            f"RiskManager initialized: max_trades={self.limits.max_trades_per_day}, "
            f"max_daily_loss={self.limits.max_daily_loss_pct}%"
        )

    @property
    def state(self) -> RiskState:
        """Current risk state."""
        self._check_day_rollover()
        self._check_cooldown_expired()
        return self._state

    def can_trade(self) -> tuple[bool, list[str]]:
        """Check if trading is allowed.

        Returns:
            (can_trade, list of blocking reasons)
        """
        self._check_day_rollover()
        self._check_cooldown_expired()

        blocks = []

        # Daily trade limit
        if self._state.trades_today >= self.limits.max_trades_per_day:
            blocks.append(f"MAX_TRADES: {self._state.trades_today}/{self.limits.max_trades_per_day}")

        # Daily loss limit
        daily_loss_pct = (-self._state.daily_pnl / self.account_value) * 100
        if self._state.daily_pnl < 0 and daily_loss_pct >= self.limits.max_daily_loss_pct:
            blocks.append(f"DAILY_LOSS: {daily_loss_pct:.1f}%")

        if self.limits.max_daily_loss_amount:
            if self._state.daily_pnl < 0 and abs(self._state.daily_pnl) >= self.limits.max_daily_loss_amount:
                blocks.append(f"DAILY_LOSS_AMOUNT: ${abs(self._state.daily_pnl):.2f}")

        # Position count
        if self._state.open_positions >= self.limits.max_concurrent_positions:
            blocks.append(f"MAX_POSITIONS: {self._state.open_positions}")

        # Loss streak cooldown
        if self._state.in_cooldown:
            blocks.append(f"COOLDOWN: until {self._state.cooldown_until}")

        return len(blocks) == 0, blocks

    def record_trade_start(self) -> None:
        """Record start of a new trade."""
        self._state.trades_today += 1
        self._state.open_positions += 1
        logger.debug(f"Trade started: count={self._state.trades_today}")

    def record_trade_end(self, pnl: float) -> None:
        """Record end of a trade.

        Args:
            pnl: Trade P&L
        """
        self._state.daily_pnl += pnl
        self._state.open_positions = max(0, self._state.open_positions - 1)

        if pnl < 0:
            self._state.consecutive_losses += 1
            self._state.last_loss_time = datetime.utcnow()

            # Check for cooldown trigger
            if self._state.consecutive_losses >= self.limits.loss_streak_cooldown:
                self._enter_cooldown()
        else:
            self._state.consecutive_losses = 0

        logger.debug(
            f"Trade ended: PnL=${pnl:.2f}, daily=${self._state.daily_pnl:.2f}, "
            f"losses={self._state.consecutive_losses}"
        )

    def _check_day_rollover(self) -> None:
        """Check if we've rolled into a new trading day."""
        now = datetime.utcnow()
        if self._state.date.date() != now.date():
            self._state = RiskState(date=now)
            logger.info("New trading day - risk state reset")

    def _check_cooldown_expired(self) -> None:
        """Check if cooldown has expired."""
        if self._state.in_cooldown and self._state.cooldown_until:
            if datetime.utcnow() >= self._state.cooldown_until:
                self._state.in_cooldown = False
                self._state.cooldown_until = None
                self._state.consecutive_losses = 0
                logger.info("Cooldown expired - trading resumed")

    def _enter_cooldown(self) -> None:
        """Enter cooldown mode."""
        self._state.in_cooldown = True
        self._state.cooldown_until = (
            datetime.utcnow() +
            timedelta(minutes=self.limits.cooldown_duration_minutes)
        )
        logger.warning(
            f"Entering cooldown: {self._state.consecutive_losses} consecutive losses, "
            f"until {self._state.cooldown_until}"
        )

    def update_account_value(self, value: float) -> None:
        """Update account value."""
        self.account_value = value

    def get_stats(self) -> dict[str, Any]:
        """Get current risk stats.

        Returns:
            Dict with risk metrics
        """
        return {
            "date": self._state.date.isoformat(),
            "trades_today": self._state.trades_today,
            "daily_pnl": self._state.daily_pnl,
            "daily_pnl_pct": (self._state.daily_pnl / self.account_value) * 100 if self.account_value > 0 else 0,
            "open_positions": self._state.open_positions,
            "consecutive_losses": self._state.consecutive_losses,
            "in_cooldown": self._state.in_cooldown,
            "cooldown_until": self._state.cooldown_until.isoformat() if self._state.cooldown_until else None,
        }
