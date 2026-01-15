"""Strategy Evaluator - Metrics Calculation.

Refactored from strategy_evaluator.py monolith.

Module 1/6 of strategy_evaluator.py split.

Contains:
- Main metrics calculation (calculate_metrics)
- Drawdown calculation
- Consecutive streaks calculation
- Risk ratios calculation (Sharpe, Sortino, Calmar)
"""

from __future__ import annotations

import numpy as np

from .evaluator_types import PerformanceMetrics, TradeResult


class EvaluatorMetrics:
    """Helper für StrategyEvaluator metrics calculation."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyEvaluator Instanz
        """
        self.parent = parent

    def calculate_metrics(
        self,
        trades: list[TradeResult],
        initial_capital: float = 10000.0,
        sample_type: str = "in_sample"
    ) -> PerformanceMetrics:
        """Calculate performance metrics from trade results.

        Args:
            trades: List of trade results
            initial_capital: Starting capital for drawdown calculations
            sample_type: "in_sample" or "out_of_sample"

        Returns:
            PerformanceMetrics
        """
        metrics = PerformanceMetrics(sample_type=sample_type)

        if not trades:
            return metrics

        # Sort by exit time
        trades = sorted(trades, key=lambda t: t.exit_time)

        metrics.total_trades = len(trades)
        metrics.start_date = trades[0].entry_time
        metrics.end_date = trades[-1].exit_time

        # Separate wins and losses
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]

        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        metrics.win_rate = len(wins) / len(trades) if trades else 0

        # Profit metrics
        metrics.gross_profit = sum(t.pnl for t in wins)
        metrics.gross_loss = abs(sum(t.pnl for t in losses))
        metrics.net_profit = metrics.gross_profit - metrics.gross_loss

        if metrics.gross_loss > 0:
            metrics.profit_factor = metrics.gross_profit / metrics.gross_loss
        else:
            metrics.profit_factor = float('inf') if metrics.gross_profit > 0 else 0

        # Average metrics
        if wins:
            metrics.avg_win = metrics.gross_profit / len(wins)
            metrics.avg_win_bars = np.mean([t.bars_held for t in wins])
        if losses:
            metrics.avg_loss = -metrics.gross_loss / len(losses)
            metrics.avg_loss_bars = np.mean([t.bars_held for t in losses])

        metrics.avg_trade = metrics.net_profit / len(trades) if trades else 0
        metrics.avg_bars_held = np.mean([t.bars_held for t in trades])

        # Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)
        if metrics.winning_trades > 0 and metrics.losing_trades > 0:
            metrics.expectancy = (
                metrics.win_rate * metrics.avg_win +
                (1 - metrics.win_rate) * metrics.avg_loss  # avg_loss is negative
            )
        else:
            metrics.expectancy = metrics.avg_trade

        # Drawdown calculation
        self.calculate_drawdown(trades, initial_capital, metrics)

        # Consecutive wins/losses
        self.calculate_consecutive_streaks(trades, metrics)

        # Risk-adjusted ratios
        self.calculate_risk_ratios(trades, metrics)

        return metrics

    def calculate_drawdown(
        self,
        trades: list[TradeResult],
        initial_capital: float,
        metrics: PerformanceMetrics
    ) -> None:
        """Calculate maximum drawdown."""
        if not trades:
            return

        # Build equity curve
        equity = [initial_capital]
        for trade in trades:
            equity.append(equity[-1] + trade.pnl)

        equity_array = np.array(equity)
        peak = np.maximum.accumulate(equity_array)
        drawdown = equity_array - peak

        metrics.max_drawdown = float(np.min(drawdown))
        peak_at_max_dd = peak[np.argmin(drawdown)]
        if peak_at_max_dd > 0:
            metrics.max_drawdown_pct = (metrics.max_drawdown / peak_at_max_dd) * 100

    def calculate_consecutive_streaks(
        self,
        trades: list[TradeResult],
        metrics: PerformanceMetrics
    ) -> None:
        """Calculate consecutive win/loss streaks."""
        if not trades:
            return

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        metrics.max_consecutive_wins = max_wins
        metrics.max_consecutive_losses = max_losses

    def calculate_risk_ratios(
        self,
        trades: list[TradeResult],
        metrics: PerformanceMetrics
    ) -> None:
        """Calculate Sharpe, Sortino, Calmar ratios."""
        if len(trades) < 2:
            return

        returns = np.array([t.pnl_pct for t in trades])

        # Sharpe ratio (assuming risk-free rate = 0)
        if np.std(returns) > 0:
            metrics.sharpe_ratio = float(np.mean(returns) / np.std(returns))

        # Sortino ratio (downside deviation)
        downside = returns[returns < 0]
        if len(downside) > 0 and np.std(downside) > 0:
            metrics.sortino_ratio = float(np.mean(returns) / np.std(downside))

        # Calmar ratio (return / max drawdown)
        if abs(metrics.max_drawdown_pct) > 0:
            total_return = sum(t.pnl_pct for t in trades)
            metrics.calmar_ratio = float(total_return / abs(metrics.max_drawdown_pct))
