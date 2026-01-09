"""Backtest Harness Helpers - Calculation Utilities.

Refactored from backtest_harness.py.

Contains:
- calculate_initial_stop: Calculate initial stop-loss price based on risk config
- calculate_equity: Calculate current equity including unrealized P&L
- calculate_metrics: Calculate performance metrics from trades
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .backtest_metrics_helpers import calculate_backtest_metrics
from .models import FeatureVector, RegimeState, TradeSide
from .strategy_evaluator import PerformanceMetrics

if TYPE_CHECKING:
    from .backtest_harness import BacktestHarness


class BacktestHarnessHelpers:
    """Helper for calculation utilities."""

    def __init__(self, parent: "BacktestHarness"):
        self.parent = parent

    def calculate_initial_stop(
        self,
        features: FeatureVector,
        side: TradeSide,
        regime: RegimeState
    ) -> float:
        """Calculate initial stop-loss price.

        Args:
            features: Current features
            side: Trade side
            regime: Current regime

        Returns:
            Stop-loss price
        """
        stop_pct = self.parent.bot_config.risk.initial_stop_loss_pct / 100

        if side == TradeSide.LONG:
            return features.close * (1 - stop_pct)
        else:
            return features.close * (1 + stop_pct)

    def calculate_equity(self) -> float:
        """Calculate current equity.

        Returns:
            Current equity value
        """
        equity = self.parent._state.capital

        if self.parent._state.position and self.parent._state.position.is_open:
            position = self.parent._state.position
            current_price = self.parent._state.current_bar["close"]

            if position.side == TradeSide.LONG:
                unrealized = (current_price - position.entry_price) * position.quantity
            else:
                unrealized = (position.entry_price - current_price) * position.quantity

            equity += unrealized

        return equity

    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from trades."""
        return calculate_backtest_metrics(self.parent._state.trades)
