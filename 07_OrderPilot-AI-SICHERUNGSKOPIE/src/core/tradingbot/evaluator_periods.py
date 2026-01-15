"""Strategy Evaluator - Period Generation.

Refactored from strategy_evaluator.py monolith.

Module 3/6 of strategy_evaluator.py split.

Contains:
- Rolling period generation
- Anchored period generation
- OOS degradation calculation
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .evaluator_types import PerformanceMetrics, WalkForwardConfig


class EvaluatorPeriods:
    """Helper für StrategyEvaluator period generation."""

    def __init__(self, parent):
        """
        Args:
            parent: StrategyEvaluator Instanz
        """
        self.parent = parent

    def generate_rolling_periods(
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

    def generate_anchored_periods(
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

    def calculate_oos_degradation(
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
