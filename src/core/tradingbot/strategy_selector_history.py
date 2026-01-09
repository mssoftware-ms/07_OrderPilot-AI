"""
Strategy Selector History - Trade History Management.

Refactored from strategy_selector.py.

Contains:
- record_trade: Record trade result for strategy
- load_trade_history: Load historical trades
- get_trade_history: Get trade history for strategy
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .strategy_evaluator import TradeResult
    from .strategy_selector import StrategySelector

logger = logging.getLogger(__name__)


class StrategySelectorHistory:
    """Helper for trade history management."""

    def __init__(self, parent: StrategySelector):
        self.parent = parent

    def record_trade(self, strategy_name: str, trade: TradeResult) -> None:
        """Record a trade result for strategy evaluation.

        Args:
            strategy_name: Name of strategy that generated trade
            trade: Trade result
        """
        if strategy_name not in self.parent._trade_history:
            self.parent._trade_history[strategy_name] = []

        self.parent._trade_history[strategy_name].append(trade)

        # Keep bounded history (last 1000 trades per strategy)
        if len(self.parent._trade_history[strategy_name]) > 1000:
            self.parent._trade_history[strategy_name] = self.parent._trade_history[
                strategy_name
            ][-500:]

        logger.debug(
            f"Recorded trade for {strategy_name}: "
            f"PnL={trade.pnl:.2f} ({trade.pnl_pct:.2f}%)"
        )

    def load_trade_history(self, strategy_name: str, trades: list[TradeResult]) -> None:
        """Load historical trades for a strategy.

        Args:
            strategy_name: Strategy name
            trades: Historical trades
        """
        self.parent._trade_history[strategy_name] = trades
        logger.info(f"Loaded {len(trades)} historical trades for {strategy_name}")

    def get_trade_history(self, strategy_name: str) -> list[TradeResult]:
        """Get trade history for a strategy.

        Args:
            strategy_name: Strategy name

        Returns:
            List of trade results
        """
        return self.parent._trade_history.get(strategy_name, [])
