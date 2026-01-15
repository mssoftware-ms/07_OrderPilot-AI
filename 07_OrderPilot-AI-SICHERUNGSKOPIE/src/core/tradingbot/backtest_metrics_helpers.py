"""Backtest Metrics Calculation Helpers.

Helper functions for calculating backtest metrics from trades.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .strategy_evaluator import PerformanceMetrics, TradeResult

if TYPE_CHECKING:
    from .backtest_types import BacktestTrade


def convert_trades_to_results(trades: list[BacktestTrade]) -> list[TradeResult]:
    """Convert BacktestTrade objects to TradeResult objects.

    Args:
        trades: List of backtest trades

    Returns:
        List of TradeResult objects
    """
    return [
        TradeResult(
            entry_time=t.entry_time,
            exit_time=t.exit_time,
            side=t.side.value if hasattr(t.side, 'value') else str(t.side),
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            quantity=t.entry_size,
            pnl=t.pnl,
            pnl_pct=t.pnl_pct,
            bars_held=t.bars_held,
            exit_reason=t.exit_reason,
            strategy_name="backtest",
        )
        for t in trades
    ]


def calculate_backtest_metrics(trades: list[BacktestTrade]) -> PerformanceMetrics:
    """Calculate performance metrics from backtest trades.

    Args:
        trades: List of backtest trades

    Returns:
        PerformanceMetrics calculated from trades
    """
    if not trades:
        return PerformanceMetrics(
            profit_factor=0, max_drawdown_pct=0, win_rate=0,
            expectancy=0, total_trades=0
        )

    from .strategy_evaluator import StrategyEvaluator

    trade_results = convert_trades_to_results(trades)
    evaluator = StrategyEvaluator()
    return evaluator.calculate_metrics(trade_results)
