"""Backtest Simulator and Release Gate.

Contains:
- BacktestSimulator: Simulates order execution during backtest
- ReleaseGate: Validates backtest results before release
"""

from __future__ import annotations

import logging
import random

from .backtest_types import BacktestResult
from .models import TradeSide

logger = logging.getLogger(__name__)

class BacktestSimulator:
    """Simulates order execution during backtest.

    Provides deterministic slippage and fill simulation.
    """

    def __init__(
        self,
        slippage_pct: float = 0.05,
        commission_pct: float = 0.1,
        seed: int = 42
    ):
        """Initialize simulator.

        Args:
            slippage_pct: Slippage percentage
            commission_pct: Commission per side
            seed: Random seed
        """
        self.slippage_pct = slippage_pct
        self.commission_pct = commission_pct
        self._rng = random.Random(seed)
        self._order_counter = 0

    def simulate_fill(
        self,
        side: TradeSide,
        quantity: float,
        price: float,
        bar_high: float,
        bar_low: float
    ) -> tuple[float, float, float]:
        """Simulate order fill with slippage.

        Args:
            side: Order side
            quantity: Order quantity
            price: Expected price
            bar_high: Bar high price
            bar_low: Bar low price

        Returns:
            (fill_price, slippage_amount, commission)
        """
        # Calculate slippage (adverse direction)
        slippage_factor = self._rng.uniform(0, self.slippage_pct / 100)

        if side == TradeSide.LONG:
            # Buy: slippage increases price
            slippage = price * slippage_factor
            fill_price = min(price + slippage, bar_high)
        else:
            # Sell: slippage decreases price
            slippage = price * slippage_factor
            fill_price = max(price - slippage, bar_low)

        slippage_amount = abs(fill_price - price) * quantity
        commission = fill_price * quantity * (self.commission_pct / 100)

        return fill_price, slippage_amount, commission

    def generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_counter += 1
        return f"bt_order_{self._order_counter:06d}"




class ReleaseGate:
    """Release gate checker for Paper → Live transition.

    Validates that backtest/paper results meet minimum criteria.
    """

    def __init__(
        self,
        min_trades: int = 20,
        min_win_rate: float = 0.4,
        min_profit_factor: float = 1.2,
        max_drawdown_pct: float = 15.0,
        min_sharpe: float = 0.5,
        min_paper_days: int = 7,
        max_consecutive_losses: int = 5
    ):
        """Initialize release gate.

        Args:
            min_trades: Minimum number of trades
            min_win_rate: Minimum win rate
            min_profit_factor: Minimum profit factor
            max_drawdown_pct: Maximum drawdown percentage
            min_sharpe: Minimum Sharpe ratio
            min_paper_days: Minimum days of paper trading
            max_consecutive_losses: Maximum consecutive losses
        """
        self.min_trades = min_trades
        self.min_win_rate = min_win_rate
        self.min_profit_factor = min_profit_factor
        self.max_drawdown_pct = max_drawdown_pct
        self.min_sharpe = min_sharpe
        self.min_paper_days = min_paper_days
        self.max_consecutive_losses = max_consecutive_losses

    def check(self, result: BacktestResult) -> tuple[bool, list[str]]:
        """Check if result passes release gate.

        Args:
            result: Backtest or paper trading result

        Returns:
            (passed, list of failure reasons)
        """
        failures = []

        if result.total_trades < self.min_trades:
            failures.append(
                f"MIN_TRADES: {result.total_trades} < {self.min_trades}"
            )

        if result.metrics.win_rate < self.min_win_rate:
            failures.append(
                f"MIN_WIN_RATE: {result.metrics.win_rate:.1%} < {self.min_win_rate:.1%}"
            )

        if result.metrics.profit_factor < self.min_profit_factor:
            failures.append(
                f"MIN_PROFIT_FACTOR: {result.metrics.profit_factor:.2f} < {self.min_profit_factor:.2f}"
            )

        if result.metrics.max_drawdown_pct > self.max_drawdown_pct:
            failures.append(
                f"MAX_DRAWDOWN: {result.metrics.max_drawdown_pct:.1f}% > {self.max_drawdown_pct:.1f}%"
            )

        if result.metrics.sharpe_ratio < self.min_sharpe:
            failures.append(
                f"MIN_SHARPE: {result.metrics.sharpe_ratio:.2f} < {self.min_sharpe:.2f}"
            )

        # Check consecutive losses
        max_consec = self._calculate_max_consecutive_losses(result.trades)
        if max_consec > self.max_consecutive_losses:
            failures.append(
                f"MAX_CONSECUTIVE_LOSSES: {max_consec} > {self.max_consecutive_losses}"
            )

        passed = len(failures) == 0

        if passed:
            logger.info("Release gate PASSED")
        else:
            logger.warning(f"Release gate FAILED: {failures}")

        return passed, failures

    def _calculate_max_consecutive_losses(
        self,
        trades: list[BacktestTrade]
    ) -> int:
        """Calculate maximum consecutive losses.

        Args:
            trades: List of trades

        Returns:
            Maximum consecutive loss count
        """
        max_consec = 0
        current_consec = 0

        for trade in trades:
            if trade.pnl <= 0:
                current_consec += 1
                max_consec = max(max_consec, current_consec)
            else:
                current_consec = 0

        return max_consec
