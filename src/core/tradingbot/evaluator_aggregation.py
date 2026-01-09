"""Strategy Evaluator - Metrics Aggregation.

Refactored from strategy_evaluator.py monolith.

Module 4/6 of strategy_evaluator.py split.

Contains:
- Aggregate metrics from multiple periods
- Sum trade totals
- Calculate derived metrics
- Aggregate drawdowns and streaks
- Aggregate date range
"""

from __future__ import annotations

from .evaluator_types import PerformanceMetrics


class EvaluatorAggregation:
    """Helper für StrategyEvaluator metrics aggregation."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyEvaluator Instanz
        """
        self.parent = parent

    def aggregate_metrics(
        self,
        metrics_list: list[PerformanceMetrics]
    ) -> PerformanceMetrics:
        """Aggregate metrics from multiple periods."""
        if not metrics_list:
            return PerformanceMetrics()

        agg = PerformanceMetrics()
        self.sum_trade_totals(agg, metrics_list)
        self.calculate_derived_metrics(agg)
        self.aggregate_drawdowns_and_streaks(agg, metrics_list)
        self.aggregate_date_range(agg, metrics_list)
        return agg

    def sum_trade_totals(self, agg: PerformanceMetrics, metrics_list: list[PerformanceMetrics]) -> None:
        """Sum total trades and profits/losses."""
        agg.total_trades = sum(m.total_trades for m in metrics_list)
        agg.winning_trades = sum(m.winning_trades for m in metrics_list)
        agg.losing_trades = sum(m.losing_trades for m in metrics_list)
        agg.gross_profit = sum(m.gross_profit for m in metrics_list)
        agg.gross_loss = sum(m.gross_loss for m in metrics_list)
        agg.net_profit = agg.gross_profit - agg.gross_loss

    def calculate_derived_metrics(self, agg: PerformanceMetrics) -> None:
        """Calculate win rate, profit factor, averages, and expectancy."""
        # Win rate
        if agg.total_trades > 0:
            agg.win_rate = agg.winning_trades / agg.total_trades

        # Profit factor
        if agg.gross_loss > 0:
            agg.profit_factor = agg.gross_profit / agg.gross_loss

        # Average win/loss
        if agg.winning_trades > 0:
            agg.avg_win = agg.gross_profit / agg.winning_trades
        if agg.losing_trades > 0:
            agg.avg_loss = -agg.gross_loss / agg.losing_trades

        # Average trade
        if agg.total_trades > 0:
            agg.avg_trade = agg.net_profit / agg.total_trades

        # Expectancy
        if agg.winning_trades > 0 and agg.losing_trades > 0:
            agg.expectancy = (
                agg.win_rate * agg.avg_win +
                (1 - agg.win_rate) * agg.avg_loss
            )

    def aggregate_drawdowns_and_streaks(self, agg: PerformanceMetrics, metrics_list: list[PerformanceMetrics]) -> None:
        """Aggregate drawdowns, streaks, and average bars held."""
        # Worst drawdown across periods
        agg.max_drawdown = min(m.max_drawdown for m in metrics_list)
        agg.max_drawdown_pct = min(m.max_drawdown_pct for m in metrics_list)

        # Max consecutive streaks
        agg.max_consecutive_wins = max(m.max_consecutive_wins for m in metrics_list)
        agg.max_consecutive_losses = max(m.max_consecutive_losses for m in metrics_list)

        # Average bars held
        total_bars = sum(m.avg_bars_held * m.total_trades for m in metrics_list)
        if agg.total_trades > 0:
            agg.avg_bars_held = total_bars / agg.total_trades

    def aggregate_date_range(self, agg: PerformanceMetrics, metrics_list: list[PerformanceMetrics]) -> None:
        """Aggregate start and end dates."""
        agg.start_date = min(m.start_date for m in metrics_list if m.start_date)
        agg.end_date = max(m.end_date for m in metrics_list if m.end_date)
