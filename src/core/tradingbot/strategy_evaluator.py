"""Strategy Evaluator for Tradingbot.

Evaluates strategy performance using walk-forward analysis
with rolling windows and out-of-sample validation.

REFACTORED: Split into focused helper modules.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

# Import types from evaluator_types
from .evaluator_types import (
    PerformanceMetrics,
    RobustnessGate,
    RobustnessReport,
    TradeResult,
    WalkForwardConfig,
    WalkForwardResult,
)

# Import helpers
from .evaluator_aggregation import EvaluatorAggregation
from .evaluator_comparison import EvaluatorComparison
from .evaluator_metrics import EvaluatorMetrics
from .evaluator_periods import EvaluatorPeriods
from .evaluator_validation import EvaluatorValidation
from .evaluator_visualization import EvaluatorVisualization
from .evaluator_walk_forward import EvaluatorWalkForward

# Re-export for backward compatibility
__all__ = [
    "TradeResult",
    "PerformanceMetrics",
    "RobustnessGate",
    "RobustnessReport",
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

        # Initialize helpers
        self._metrics = EvaluatorMetrics(parent=self)
        self._validation = EvaluatorValidation(parent=self)
        self._periods = EvaluatorPeriods(parent=self)
        self._aggregation = EvaluatorAggregation(parent=self)
        self._walk_forward = EvaluatorWalkForward(parent=self)
        self._comparison = EvaluatorComparison(parent=self)
        self._visualization = EvaluatorVisualization(parent=self)

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
        """Calculate performance metrics from trade results."""
        return self._metrics.calculate_metrics(trades, initial_capital, sample_type)

    def validate_robustness(
        self,
        metrics: PerformanceMetrics,
        gate: RobustnessGate | None = None
    ) -> tuple[bool, list[str]]:
        """Validate metrics against robustness criteria."""
        return self._validation.validate_robustness(metrics, gate)

    def run_walk_forward(
        self,
        strategy: "StrategyDefinition",
        all_trades: list[TradeResult],
        config: WalkForwardConfig | None = None
    ) -> WalkForwardResult:
        """Run walk-forward analysis on strategy."""
        return self._walk_forward.run_walk_forward(strategy, all_trades, config)

    def validate_strategy_robustness(
        self,
        walk_forward_result: WalkForwardResult,
        min_trades: int = 30,
        max_drawdown_threshold: float = 20.0,
        min_sharpe: float = 1.0,
        max_degradation_pct: float = 30.0
    ) -> RobustnessReport:
        """Validate strategy robustness using walk-forward results.

        Args:
            walk_forward_result: Walk-forward analysis result
            min_trades: Minimum total trades required
            max_drawdown_threshold: Maximum allowed drawdown %
            min_sharpe: Minimum Sharpe ratio required
            max_degradation_pct: Maximum allowed OOS degradation %

        Returns:
            RobustnessReport with validation results
        """
        return self._validation.validate_strategy_robustness(
            walk_forward_result,
            min_trades,
            max_drawdown_threshold,
            min_sharpe,
            max_degradation_pct
        )

    def compare_strategies(
        self,
        results: list[WalkForwardResult]
    ) -> list[tuple[str, float]]:
        """Rank strategies by composite score."""
        return self._comparison.compare_strategies(results)

    def create_walk_forward_charts(
        self,
        walk_forward_result: WalkForwardResult,
        robustness_report: RobustnessReport | None = None
    ):
        """Create walk-forward validation charts.

        Args:
            walk_forward_result: Walk-forward analysis result
            robustness_report: Optional robustness report

        Returns:
            Matplotlib Figure with 4 charts
        """
        return self._visualization.create_walk_forward_charts(
            walk_forward_result,
            robustness_report
        )
