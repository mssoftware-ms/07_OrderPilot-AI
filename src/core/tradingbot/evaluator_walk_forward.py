"""Strategy Evaluator - Walk-Forward Analysis.

Refactored from strategy_evaluator.py monolith.

Module 5/6 of strategy_evaluator.py split.

Contains:
- Walk-forward analysis orchestration
- Period slicing
- Period validation
- Simple train/test split
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from .evaluator_types import (
    PerformanceMetrics,
    TradeResult,
    WalkForwardConfig,
    WalkForwardResult,
)

if TYPE_CHECKING:
    from .strategy_catalog import StrategyDefinition

logger = logging.getLogger(__name__)


class EvaluatorWalkForward:
    """Helper für StrategyEvaluator walk-forward analysis."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyEvaluator Instanz
        """
        self.parent = parent

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
        config = config or self.parent.walk_forward_config

        if not all_trades:
            return self.empty_walk_forward_result(strategy, config)

        # Sort trades by exit time
        trades = sorted(all_trades, key=lambda t: t.exit_time)

        start_date, end_date, total_days = self.trade_date_range(trades)
        if self.insufficient_history(total_days, config):
            return self.simple_train_test_split(strategy, trades, config)

        is_results = []
        oos_results = []
        periods_passed = 0

        periods = self.get_walk_forward_periods(start_date, end_date, config)

        # Track rolling metrics for visualization
        period_results = []
        rolling_sharpe = []
        rolling_drawdown = []
        period_dates = []

        for train_start, train_end, test_start, test_end in periods:
            train_trades, test_trades = self.slice_trades_for_period(
                trades, train_start, train_end, test_start, test_end
            )

            if len(train_trades) < config.min_training_trades:
                continue

            # Calculate metrics
            is_metrics = self.parent._metrics.calculate_metrics(train_trades, sample_type="in_sample")
            oos_metrics = self.parent._metrics.calculate_metrics(test_trades, sample_type="out_of_sample")

            is_results.append(is_metrics)
            oos_results.append(oos_metrics)

            # Collect for visualization
            period_results.append((is_metrics, oos_metrics))
            period_dates.append((test_start, test_end))

            # Rolling Sharpe (use OOS)
            if oos_metrics.sharpe_ratio is not None:
                rolling_sharpe.append(oos_metrics.sharpe_ratio)
            else:
                rolling_sharpe.append(0.0)

            # Rolling drawdown (use worse of IS/OOS)
            rolling_drawdown.append(
                max(abs(is_metrics.max_drawdown_pct), abs(oos_metrics.max_drawdown_pct))
            )

            # Check if this period passed
            if self.period_passed(is_metrics, oos_metrics):
                periods_passed += 1

        # Aggregate results
        agg_is_metrics = self.parent._aggregation.aggregate_metrics(is_results)
        agg_oos_metrics = self.parent._aggregation.aggregate_metrics(oos_results)

        # Calculate robustness score
        robustness_score = periods_passed / len(is_results) if is_results else 0.0

        # Determine if overall robust
        is_robust = self.is_overall_robust(agg_is_metrics, agg_oos_metrics)

        return WalkForwardResult(
            strategy_name=strategy.profile.name,
            config=config,
            in_sample_metrics=agg_is_metrics,
            out_of_sample_metrics=agg_oos_metrics,
            periods_evaluated=len(is_results),
            periods_passed=periods_passed,
            robustness_score=robustness_score,
            is_robust=is_robust,
            period_results=period_results,
            rolling_sharpe=rolling_sharpe,
            rolling_drawdown=rolling_drawdown,
            period_dates=period_dates,
        )

    def empty_walk_forward_result(
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

    def trade_date_range(self, trades: list[TradeResult]) -> tuple[datetime, datetime, int]:
        start_date = trades[0].entry_time
        end_date = trades[-1].exit_time
        total_days = (end_date - start_date).days
        return start_date, end_date, total_days

    def insufficient_history(self, total_days: int, config: WalkForwardConfig) -> bool:
        if total_days < config.training_window_days + config.test_window_days:
            logger.warning(
                f"Insufficient history for walk-forward: {total_days} days"
            )
            return True
        return False

    def get_walk_forward_periods(
        self,
        start_date: datetime,
        end_date: datetime,
        config: WalkForwardConfig,
    ) -> list[tuple[datetime, datetime, datetime, datetime]]:
        if config.anchored:
            return self.parent._periods.generate_anchored_periods(start_date, end_date, config)
        return self.parent._periods.generate_rolling_periods(start_date, end_date, config)

    def slice_trades_for_period(
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

    def period_passed(self, is_metrics: PerformanceMetrics, oos_metrics: PerformanceMetrics) -> bool:
        is_robust, _ = self.parent._validation.validate_robustness(is_metrics)
        if not is_robust or oos_metrics.total_trades <= 0:
            return False
        degradation = self.parent._periods.calculate_oos_degradation(is_metrics, oos_metrics)
        return degradation <= self.parent.robustness_gate.oos_degradation_max

    def is_overall_robust(
        self,
        agg_is_metrics: PerformanceMetrics,
        agg_oos_metrics: PerformanceMetrics,
    ) -> bool:
        is_robust, _ = self.parent._validation.validate_robustness(agg_is_metrics)
        if self.parent.robustness_gate.require_oos_validation:
            oos_robust = agg_oos_metrics.profit_factor >= 1.0
            return is_robust and oos_robust
        return is_robust

    def simple_train_test_split(
        self,
        strategy: "StrategyDefinition",
        trades: list[TradeResult],
        config: WalkForwardConfig
    ) -> WalkForwardResult:
        """Simple 70/30 train/test split when not enough history."""
        split_idx = int(len(trades) * 0.7)
        train_trades = trades[:split_idx]
        test_trades = trades[split_idx:]

        is_metrics = self.parent._metrics.calculate_metrics(train_trades, sample_type="in_sample")
        oos_metrics = self.parent._metrics.calculate_metrics(test_trades, sample_type="out_of_sample")

        is_robust, _ = self.parent._validation.validate_robustness(is_metrics)

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
