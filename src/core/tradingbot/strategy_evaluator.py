"""Strategy Evaluator for Tradingbot.

Evaluates strategy performance using walk-forward analysis
with rolling windows and out-of-sample validation.

REFACTORED: Data models extracted to evaluator_types.py
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

import numpy as np

# Import types from evaluator_types
from .evaluator_types import (
    PerformanceMetrics,
    RobustnessGate,
    TradeResult,
    WalkForwardConfig,
    WalkForwardResult,
)

# Re-export for backward compatibility
__all__ = [
    "TradeResult",
    "PerformanceMetrics",
    "RobustnessGate",
    "WalkForwardConfig",
    "WalkForwardResult",
    "StrategyEvaluator",
]

if TYPE_CHECKING:
    from .strategy_catalog import StrategyDefinition

logger = logging.getLogger(__name__)


class StrategyEvaluator:
    """Evaluator for strategy performance.

    Provides methods for calculating performance metrics
    and running walk-forward analysis.
    """

    def __init__(
        self,
        robustness_gate: RobustnessGate | None = None,
        walk_forward_config: WalkForwardConfig | None = None
    ):
        """Initialize evaluator.

        Args:
            robustness_gate: Robustness validation criteria
            walk_forward_config: Walk-forward analysis configuration
        """
        self.robustness_gate = robustness_gate or RobustnessGate()
        self.walk_forward_config = walk_forward_config or WalkForwardConfig()

        logger.info(
            f"StrategyEvaluator initialized "
            f"(training={self.walk_forward_config.training_window_days}d, "
            f"test={self.walk_forward_config.test_window_days}d)"
        )

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
        self._calculate_drawdown(trades, initial_capital, metrics)

        # Consecutive wins/losses
        self._calculate_consecutive_streaks(trades, metrics)

        # Risk-adjusted ratios
        self._calculate_risk_ratios(trades, metrics)

        return metrics

    def _calculate_drawdown(
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

    def _calculate_consecutive_streaks(
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

    def _calculate_risk_ratios(
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

    def validate_robustness(
        self,
        metrics: PerformanceMetrics,
        gate: RobustnessGate | None = None
    ) -> tuple[bool, list[str]]:
        """Validate metrics against robustness criteria.

        Args:
            metrics: Performance metrics to validate
            gate: Custom robustness gate (uses default if None)

        Returns:
            (is_robust, list of failure reasons)
        """
        gate = gate or self.robustness_gate
        failures = []

        if metrics.total_trades < gate.min_trades:
            failures.append(
                f"Insufficient trades: {metrics.total_trades} < {gate.min_trades}"
            )

        if metrics.profit_factor < gate.min_profit_factor:
            failures.append(
                f"Low profit factor: {metrics.profit_factor:.2f} < {gate.min_profit_factor}"
            )

        if abs(metrics.max_drawdown_pct) > gate.max_drawdown_pct:
            failures.append(
                f"High drawdown: {abs(metrics.max_drawdown_pct):.1f}% > {gate.max_drawdown_pct}%"
            )

        if metrics.win_rate < gate.min_win_rate:
            failures.append(
                f"Low win rate: {metrics.win_rate:.1%} < {gate.min_win_rate:.1%}"
            )

        if metrics.expectancy < gate.min_expectancy:
            failures.append(
                f"Low expectancy: {metrics.expectancy:.2f} < {gate.min_expectancy}"
            )

        return len(failures) == 0, failures

    def run_walk_forward(
        self,
        strategy: "StrategyDefinition",
        all_trades: list[TradeResult],
        config: WalkForwardConfig | None = None
    ) -> WalkForwardResult:
        """Run walk-forward analysis on strategy.

        Args:
            strategy: Strategy definition
            all_trades: All historical trades for this strategy
            config: Walk-forward configuration

        Returns:
            WalkForwardResult with in-sample and out-of-sample metrics
        """
        config = config or self.walk_forward_config

        if not all_trades:
            return self._empty_walk_forward_result(strategy, config)

        # Sort trades by exit time
        trades = sorted(all_trades, key=lambda t: t.exit_time)

        start_date, end_date, total_days = self._trade_date_range(trades)
        if self._insufficient_history(total_days, config):
            return self._simple_train_test_split(strategy, trades, config)

        is_results = []
        oos_results = []
        periods_passed = 0

        periods = self._get_walk_forward_periods(start_date, end_date, config)

        for train_start, train_end, test_start, test_end in periods:
            train_trades, test_trades = self._slice_trades_for_period(
                trades, train_start, train_end, test_start, test_end
            )

            if len(train_trades) < config.min_training_trades:
                continue

            # Calculate metrics
            is_metrics = self.calculate_metrics(train_trades, sample_type="in_sample")
            oos_metrics = self.calculate_metrics(test_trades, sample_type="out_of_sample")

            is_results.append(is_metrics)
            oos_results.append(oos_metrics)

            # Check if this period passed
            if self._period_passed(is_metrics, oos_metrics):
                periods_passed += 1

        # Aggregate results
        agg_is_metrics = self._aggregate_metrics(is_results)
        agg_oos_metrics = self._aggregate_metrics(oos_results)

        # Calculate robustness score
        robustness_score = periods_passed / len(is_results) if is_results else 0.0

        # Determine if overall robust
        is_robust = self._is_overall_robust(agg_is_metrics, agg_oos_metrics)

        return WalkForwardResult(
            strategy_name=strategy.profile.name,
            config=config,
            in_sample_metrics=agg_is_metrics,
            out_of_sample_metrics=agg_oos_metrics,
            periods_evaluated=len(is_results),
            periods_passed=periods_passed,
            robustness_score=robustness_score,
            is_robust=is_robust,
        )

    def _empty_walk_forward_result(
        self,
        strategy: "StrategyDefinition",
        config: WalkForwardConfig,
    ) -> WalkForwardResult:
        return WalkForwardResult(
            strategy_name=strategy.profile.name,
            config=config,
            in_sample_metrics=PerformanceMetrics(),
            out_of_sample_metrics=PerformanceMetrics(),
        )

    def _trade_date_range(self, trades: list[TradeResult]) -> tuple[datetime, datetime, int]:
        start_date = trades[0].entry_time
        end_date = trades[-1].exit_time
        total_days = (end_date - start_date).days
        return start_date, end_date, total_days

    def _insufficient_history(self, total_days: int, config: WalkForwardConfig) -> bool:
        if total_days < config.training_window_days + config.test_window_days:
            logger.warning(
                f"Insufficient history for walk-forward: {total_days} days"
            )
            return True
        return False

    def _get_walk_forward_periods(
        self,
        start_date: datetime,
        end_date: datetime,
        config: WalkForwardConfig,
    ) -> list[tuple[datetime, datetime, datetime, datetime]]:
        if config.anchored:
            return self._generate_anchored_periods(start_date, end_date, config)
        return self._generate_rolling_periods(start_date, end_date, config)

    def _slice_trades_for_period(
        self,
        trades: list[TradeResult],
        train_start: datetime,
        train_end: datetime,
        test_start: datetime,
        test_end: datetime,
    ) -> tuple[list[TradeResult], list[TradeResult]]:
        train_trades = [
            t for t in trades
            if train_start <= t.exit_time < train_end
        ]
        test_trades = [
            t for t in trades
            if test_start <= t.exit_time < test_end
        ]
        return train_trades, test_trades

    def _period_passed(self, is_metrics: PerformanceMetrics, oos_metrics: PerformanceMetrics) -> bool:
        is_robust, _ = self.validate_robustness(is_metrics)
        if not is_robust or oos_metrics.total_trades <= 0:
            return False
        degradation = self._calculate_oos_degradation(is_metrics, oos_metrics)
        return degradation <= self.robustness_gate.oos_degradation_max

    def _is_overall_robust(
        self,
        agg_is_metrics: PerformanceMetrics,
        agg_oos_metrics: PerformanceMetrics,
    ) -> bool:
        is_robust, _ = self.validate_robustness(agg_is_metrics)
        if self.robustness_gate.require_oos_validation:
            oos_robust = agg_oos_metrics.profit_factor >= 1.0
            return is_robust and oos_robust
        return is_robust

    def _simple_train_test_split(
        self,
        strategy: "StrategyDefinition",
        trades: list[TradeResult],
        config: WalkForwardConfig
    ) -> WalkForwardResult:
        """Simple 70/30 train/test split when not enough history."""
        split_idx = int(len(trades) * 0.7)
        train_trades = trades[:split_idx]
        test_trades = trades[split_idx:]

        is_metrics = self.calculate_metrics(train_trades, sample_type="in_sample")
        oos_metrics = self.calculate_metrics(test_trades, sample_type="out_of_sample")

        is_robust, _ = self.validate_robustness(is_metrics)

        return WalkForwardResult(
            strategy_name=strategy.profile.name,
            config=config,
            in_sample_metrics=is_metrics,
            out_of_sample_metrics=oos_metrics,
            periods_evaluated=1,
            periods_passed=1 if is_robust else 0,
            robustness_score=1.0 if is_robust else 0.0,
            is_robust=is_robust,
        )

    def _generate_rolling_periods(
        self,
        start_date: datetime,
        end_date: datetime,
        config: WalkForwardConfig
    ) -> list[tuple[datetime, datetime, datetime, datetime]]:
        """Generate rolling window periods."""
        periods = []
        current_start = start_date

        while True:
            train_end = current_start + timedelta(days=config.training_window_days)
            test_start = train_end
            test_end = test_start + timedelta(days=config.test_window_days)

            if test_end > end_date:
                break

            periods.append((current_start, train_end, test_start, test_end))
            current_start += timedelta(days=config.step_days)

        return periods

    def _generate_anchored_periods(
        self,
        start_date: datetime,
        end_date: datetime,
        config: WalkForwardConfig
    ) -> list[tuple[datetime, datetime, datetime, datetime]]:
        """Generate anchored (expanding) window periods."""
        periods = []
        anchor_start = start_date
        current_end = anchor_start + timedelta(days=config.training_window_days)

        while True:
            test_start = current_end
            test_end = test_start + timedelta(days=config.test_window_days)

            if test_end > end_date:
                break

            periods.append((anchor_start, current_end, test_start, test_end))
            current_end += timedelta(days=config.step_days)

        return periods

    def _calculate_oos_degradation(
        self,
        is_metrics: PerformanceMetrics,
        oos_metrics: PerformanceMetrics
    ) -> float:
        """Calculate performance degradation from IS to OOS.

        Returns:
            Degradation ratio (0 = same, 0.3 = 30% worse)
        """
        if is_metrics.profit_factor <= 0:
            return 1.0

        if oos_metrics.profit_factor >= is_metrics.profit_factor:
            return 0.0  # No degradation

        degradation = 1 - (oos_metrics.profit_factor / is_metrics.profit_factor)
        return max(0, min(1, degradation))

    def _aggregate_metrics(
        self,
        metrics_list: list[PerformanceMetrics]
    ) -> PerformanceMetrics:
        """Aggregate metrics from multiple periods."""
        if not metrics_list:
            return PerformanceMetrics()

        agg = PerformanceMetrics()

        # Sum totals
        agg.total_trades = sum(m.total_trades for m in metrics_list)
        agg.winning_trades = sum(m.winning_trades for m in metrics_list)
        agg.losing_trades = sum(m.losing_trades for m in metrics_list)
        agg.gross_profit = sum(m.gross_profit for m in metrics_list)
        agg.gross_loss = sum(m.gross_loss for m in metrics_list)
        agg.net_profit = agg.gross_profit - agg.gross_loss

        # Calculate derived metrics
        if agg.total_trades > 0:
            agg.win_rate = agg.winning_trades / agg.total_trades

        if agg.gross_loss > 0:
            agg.profit_factor = agg.gross_profit / agg.gross_loss

        if agg.winning_trades > 0:
            agg.avg_win = agg.gross_profit / agg.winning_trades

        if agg.losing_trades > 0:
            agg.avg_loss = -agg.gross_loss / agg.losing_trades

        if agg.total_trades > 0:
            agg.avg_trade = agg.net_profit / agg.total_trades

        # Expectancy
        if agg.winning_trades > 0 and agg.losing_trades > 0:
            agg.expectancy = (
                agg.win_rate * agg.avg_win +
                (1 - agg.win_rate) * agg.avg_loss
            )

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

        # Date range
        agg.start_date = min(m.start_date for m in metrics_list if m.start_date)
        agg.end_date = max(m.end_date for m in metrics_list if m.end_date)

        return agg

    def compare_strategies(
        self,
        results: list[WalkForwardResult]
    ) -> list[tuple[str, float]]:
        """Rank strategies by composite score.

        Args:
            results: Walk-forward results for strategies

        Returns:
            List of (strategy_name, score) sorted by score descending
        """
        scores = []

        for result in results:
            if not result.is_robust:
                scores.append((result.strategy_name, 0.0))
                continue

            # Composite score components
            pf_score = min(result.in_sample_metrics.profit_factor / 2.0, 1.0)
            wr_score = result.in_sample_metrics.win_rate
            dd_score = 1 - (abs(result.in_sample_metrics.max_drawdown_pct) / 20.0)
            dd_score = max(0, min(1, dd_score))
            robust_score = result.robustness_score

            # OOS bonus/penalty
            oos_bonus = 0.0
            if result.out_of_sample_metrics.total_trades > 0:
                if result.out_of_sample_metrics.profit_factor >= 1.0:
                    oos_bonus = 0.2
                elif result.out_of_sample_metrics.net_profit > 0:
                    oos_bonus = 0.1

            # Weighted composite
            composite = (
                pf_score * 0.30 +
                wr_score * 0.20 +
                dd_score * 0.20 +
                robust_score * 0.20 +
                oos_bonus * 0.10
            )

            scores.append((result.strategy_name, composite))

        return sorted(scores, key=lambda x: x[1], reverse=True)
