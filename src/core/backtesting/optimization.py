"""Parameter Optimization for Trading Strategies.

Provides AI-guided parameter optimization using:
- Grid search with AI analysis
- Parameter sensitivity analysis
- Multi-objective optimization
- AI-driven recommendations

REFACTORED: Data models extracted to optimization_types.py
"""

import asyncio
import logging
from itertools import product
from typing import Any, Callable

from src.core.models.backtest_models import BacktestResult

# Import types from optimization_types
from .optimization_types import (
    AIOptimizationInsight,
    OptimizationMetric,
    OptimizationResult,
    OptimizerConfig,
    ParameterRange,
    ParameterTest,
)

# Re-export for backward compatibility
__all__ = [
    "ParameterRange",
    "OptimizationMetric",
    "ParameterTest",
    "OptimizationResult",
    "AIOptimizationInsight",
    "OptimizerConfig",
    "ParameterOptimizer",
    "quick_optimize",
]

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """AI-guided parameter optimizer for trading strategies."""

    def __init__(
        self,
        backtest_runner: Callable,
        config: OptimizerConfig | None = None
    ):
        """Initialize parameter optimizer.

        Args:
            backtest_runner: Async function that runs backtest with parameters
                            Signature: async def runner(params: dict) -> BacktestResult
            config: Optimizer configuration
        """
        self.backtest_runner = backtest_runner
        self.config = config or OptimizerConfig()
        self._tests: list[ParameterTest] = []
        self._start_time: float = 0.0

    async def grid_search(
        self,
        parameter_ranges: list[ParameterRange],
        base_params: dict[str, Any] | None = None
    ) -> OptimizationResult:
        """Perform grid search optimization.

        Args:
            parameter_ranges: Parameter ranges to search
            base_params: Base parameters (not optimized)

        Returns:
            Optimization result with best parameters
        """
        import time
        self._start_time = time.time()
        self._tests = []

        base_params = base_params or {}
        param_names, combinations = self._generate_combinations(parameter_ranges)
        total_tests = len(combinations)
        logger.info(f"Starting grid search with {total_tests} parameter combinations")

        for i, combination in enumerate(combinations, 1):
            test_params = self._build_test_params(base_params, param_names, combination)
            logger.info(f"[{i}/{total_tests}] Testing: {test_params}")
            await self._run_single_test(i, total_tests, test_params)

            if self.config.use_ai_guidance and i % self.config.ai_analysis_frequency == 0:
                logger.info(f"  Running AI analysis after {i} tests...")

        successful_tests = [t for t in self._tests if t.score is not None]
        if not successful_tests:
            raise ValueError("No successful tests completed")

        best_test = max(successful_tests, key=lambda t: t.score)
        sensitivity = self._analyze_sensitivity(parameter_ranges)
        result = OptimizationResult(
            best_parameters=best_test.parameters,
            best_score=best_test.score,
            best_result=best_test.result,
            all_tests=self._tests,
            total_tests=len(self._tests),
            successful_tests=len(successful_tests),
            optimization_time_seconds=time.time() - self._start_time,
            sensitivity_analysis=sensitivity,
        )

        logger.info(f"Optimization complete: Best score = {best_test.score:.4f}")
        logger.info(f"Best parameters: {best_test.parameters}")
        return result

    def _generate_combinations(
        self,
        parameter_ranges: list[ParameterRange],
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        param_names = [p.name for p in parameter_ranges]
        param_values = [p.values for p in parameter_ranges]
        return param_names, list(product(*param_values))

    def _build_test_params(
        self,
        base_params: dict[str, Any],
        param_names: list[str],
        combination: tuple[Any, ...],
    ) -> dict[str, Any]:
        test_params = base_params.copy()
        test_params.update(dict(zip(param_names, combination)))
        return test_params

    async def _run_single_test(
        self,
        index: int,
        total: int,
        test_params: dict[str, Any],
    ) -> None:
        try:
            result = await asyncio.wait_for(
                self.backtest_runner(test_params),
                timeout=self.config.timeout_per_test,
            )
            score = self._calculate_score(result)
            metrics = self._extract_metrics(result)
            self._tests.append(
                ParameterTest(
                    parameters=test_params,
                    result=result,
                    score=score,
                    metrics=metrics,
                )
            )
            logger.info(
                f"  Score: {score:.4f} | {self.config.primary_metric}: "
                f"{metrics.get(self.config.primary_metric, 'N/A')}"
            )
        except asyncio.TimeoutError:
            logger.warning(f"  Test timed out after {self.config.timeout_per_test}s")
            self._tests.append(ParameterTest(parameters=test_params, error="Timeout"))
        except Exception as e:
            logger.error(f"  Test failed: {e}")
            self._tests.append(ParameterTest(parameters=test_params, error=str(e)))

    async def optimize_with_ai(
        self,
        parameter_ranges: list[ParameterRange],
        base_params: dict[str, Any] | None = None,
        max_iterations: int = 3
    ) -> tuple[OptimizationResult, AIOptimizationInsight]:
        """Perform AI-guided optimization with iterative refinement.

        Args:
            parameter_ranges: Initial parameter ranges
            base_params: Base parameters
            max_iterations: Maximum optimization iterations

        Returns:
            Tuple of (optimization result, AI insights)
        """
        logger.info(f"Starting AI-guided optimization ({max_iterations} iterations)")

        current_ranges = parameter_ranges
        best_overall_result = None
        best_overall_score = float('-inf')

        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"ITERATION {iteration}/{max_iterations}")
            logger.info(f"{'='*80}")

            # Run grid search
            result = await self.grid_search(current_ranges, base_params)

            # Track best overall
            if result.best_score > best_overall_score:
                best_overall_score = result.best_score
                best_overall_result = result

            # Generate AI insights
            try:
                insights = await self._get_ai_insights(result)
                logger.info(f"\n📊 AI Insights:")
                logger.info(f"  {insights.summary}")
                logger.info(f"  Confidence: {insights.confidence_score:.2%}")

                # Refine ranges based on AI suggestions
                if iteration < max_iterations and insights.next_parameters_to_test:
                    logger.info(f"\n🔄 Refining parameter ranges based on AI suggestions...")
                    current_ranges = self._refine_ranges(
                        current_ranges,
                        result,
                        insights
                    )

            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")
                insights = None

            if iteration == max_iterations:
                break

        if insights is None:
            # Generate insights from final result
            insights = await self._get_ai_insights(best_overall_result)

        return best_overall_result, insights

    def _calculate_score(self, result: BacktestResult) -> float:
        """Calculate optimization score for a backtest result.

        Args:
            result: Backtest result

        Returns:
            Optimization score (higher is better)
        """
        # Check constraints
        if result.metrics.total_trades < self.config.min_trades:
            return float('-inf')

        if result.metrics.max_drawdown_pct < self.config.max_drawdown_pct:
            return float('-inf')

        # Calculate primary metric score
        primary_value = self._get_metric_value(result, self.config.primary_metric)
        if primary_value is None:
            return float('-inf')

        score = primary_value

        # Add secondary metrics
        if self.config.secondary_metrics:
            for metric_name in self.config.secondary_metrics:
                value = self._get_metric_value(result, metric_name)
                if value is not None:
                    # Normalize and add (weighted)
                    score += value * 0.1

        return score

    def _get_metric_value(self, result: BacktestResult, metric_name: str) -> float | None:
        """Extract metric value from backtest result.

        Args:
            result: Backtest result
            metric_name: Name of metric to extract

        Returns:
            Metric value or None if not found
        """
        metrics = result.metrics

        metric_map = {
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "total_return_pct": metrics.total_return_pct,
            "annual_return_pct": metrics.annual_return_pct,
            "profit_factor": metrics.profit_factor,
            "win_rate": metrics.win_rate,
            "expectancy": metrics.expectancy,
            "max_drawdown_pct": abs(metrics.max_drawdown_pct),  # Use absolute value
            "avg_r_multiple": metrics.avg_r_multiple,
        }

        return metric_map.get(metric_name)

    def _extract_metrics(self, result: BacktestResult) -> dict[str, float]:
        """Extract key metrics from backtest result.

        Args:
            result: Backtest result

        Returns:
            Dictionary of key metrics
        """
        return {
            "sharpe_ratio": result.metrics.sharpe_ratio or 0.0,
            "sortino_ratio": result.metrics.sortino_ratio or 0.0,
            "total_return_pct": result.metrics.total_return_pct,
            "win_rate": result.metrics.win_rate,
            "profit_factor": result.metrics.profit_factor,
            "max_drawdown_pct": result.metrics.max_drawdown_pct,
            "total_trades": result.metrics.total_trades,
        }

    def _analyze_sensitivity(
        self,
        parameter_ranges: list[ParameterRange]
    ) -> dict[str, dict[str, Any]]:
        """Analyze parameter sensitivity.

        Args:
            parameter_ranges: Parameter ranges tested

        Returns:
            Sensitivity analysis for each parameter
        """
        sensitivity = {}

        for param_range in parameter_ranges:
            param_name = param_range.name

            # Group tests by parameter value
            param_scores: dict[Any, list[float]] = {}

            for test in self._tests:
                if test.score is None:
                    continue

                param_value = test.parameters.get(param_name)
                if param_value is not None:
                    if param_value not in param_scores:
                        param_scores[param_value] = []
                    param_scores[param_value].append(test.score)

            # Calculate statistics
            if param_scores:
                value_stats = {}
                for value, scores in param_scores.items():
                    value_stats[str(value)] = {
                        "mean_score": sum(scores) / len(scores),
                        "max_score": max(scores),
                        "min_score": min(scores),
                        "count": len(scores)
                    }

                # Calculate sensitivity (score variance)
                all_means = [stats["mean_score"] for stats in value_stats.values()]
                sensitivity_score = (max(all_means) - min(all_means)) if len(all_means) > 1 else 0.0

                sensitivity[param_name] = {
                    "value_stats": value_stats,
                    "sensitivity_score": sensitivity_score,
                    "impact": "high" if sensitivity_score > 0.5 else "medium" if sensitivity_score > 0.2 else "low"
                }

        return sensitivity

    async def _get_ai_insights(
        self,
        result: OptimizationResult
    ) -> AIOptimizationInsight:
        """Get AI insights about optimization results.

        Args:
            result: Optimization result

        Returns:
            AI-generated insights
        """
        try:
            # ===== CRITICAL: USE MULTI-PROVIDER AI FACTORY =====
            from src.ai import get_ai_service

            # Get AI service based on user settings (OpenAI or Anthropic)
            service = await get_ai_service()

            try:
                # Build prompt
                prompt = self._build_optimization_prompt(result)

                # Get AI analysis
                insights = await service.structured_completion(
                    prompt=prompt,
                    response_model=AIOptimizationInsight,
                    temperature=0.3
                )

                return insights

            finally:
                await service.close()

        except Exception as e:
            logger.warning(f"AI insights generation failed: {e}")
            # Return default insights
            return AIOptimizationInsight(
                summary="Optimization completed successfully",
                best_parameter_analysis=f"Best parameters achieved score of {result.best_score:.4f}",
                parameter_importance={},
                sensitivity_insights=[],
                recommendations=[],
                confidence_score=0.0
            )

    def _build_optimization_prompt(self, result: OptimizationResult) -> str:
        """Build prompt for AI optimization analysis.

        Args:
            result: Optimization result

        Returns:
            Prompt for AI analysis
        """
        # Get top 5 results
        top_tests = sorted(
            [t for t in result.all_tests if t.score is not None],
            key=lambda t: t.score,
            reverse=True
        )[:5]

        # Build summary
        summary_lines = [
            f"Optimization Results Summary:",
            f"- Total tests: {result.total_tests}",
            f"- Successful: {result.successful_tests}",
            f"- Best score: {result.best_score:.4f}",
            f"- Best parameters: {result.best_parameters}",
            "",
            "Top 5 Results:",
        ]

        for i, test in enumerate(top_tests, 1):
            summary_lines.append(f"{i}. Score: {test.score:.4f} | Params: {test.parameters}")
            summary_lines.append(f"   Metrics: {test.metrics}")

        # Add sensitivity analysis
        if result.sensitivity_analysis:
            summary_lines.append("")
            summary_lines.append("Parameter Sensitivity:")
            for param, analysis in result.sensitivity_analysis.items():
                summary_lines.append(f"- {param}: {analysis['impact']} impact (score: {analysis['sensitivity_score']:.4f})")

        prompt = "\n".join(summary_lines)

        prompt += """

Analyze this parameter optimization and provide:
1. A summary of the optimization results
2. Analysis of why these parameters performed best
3. Parameter importance rankings (0-1 scale)
4. Insights about parameter sensitivity
5. Specific recommendations for further optimization
6. Suggested parameters for next iteration (if any)
7. Your confidence in these recommendations (0-1)

Focus on actionable insights and clear explanations."""

        return prompt

    def _refine_ranges(
        self,
        current_ranges: list[ParameterRange],
        result: OptimizationResult,
        insights: AIOptimizationInsight
    ) -> list[ParameterRange]:
        """Refine parameter ranges based on AI insights.

        Args:
            current_ranges: Current parameter ranges
            result: Optimization result
            insights: AI insights

        Returns:
            Refined parameter ranges
        """
        # For now, narrow ranges around best parameters
        # More sophisticated refinement can be added based on insights

        refined_ranges = []

        for param_range in current_ranges:
            param_name = param_range.name
            best_value = result.best_parameters.get(param_name)

            if best_value is None:
                refined_ranges.append(param_range)
                continue

            # If parameter has high importance, narrow the range
            importance = insights.parameter_importance.get(param_name, 0.5)

            if importance > 0.7 and param_range.type == "continuous":
                # Narrow range around best value
                values = param_range.values
                idx = values.index(best_value) if best_value in values else len(values) // 2

                # Take values around best
                start = max(0, idx - 1)
                end = min(len(values), idx + 2)
                new_values = values[start:end]

                refined_ranges.append(ParameterRange(
                    name=param_name,
                    values=new_values,
                    type=param_range.type
                ))
            else:
                # Keep original range
                refined_ranges.append(param_range)

        return refined_ranges


# ==================== Convenience Functions ====================

async def quick_optimize(
    backtest_runner: Callable,
    parameter_ranges: dict[str, list[Any]],
    base_params: dict[str, Any] | None = None,
    primary_metric: str = "sharpe_ratio"
) -> OptimizationResult:
    """Quick parameter optimization with default settings.

    Args:
        backtest_runner: Async backtest runner function
        parameter_ranges: Dict of parameter name to list of values
        base_params: Base parameters
        primary_metric: Metric to optimize

    Returns:
        Optimization result

    Example:
        >>> async def run_backtest(params):
        ...     # Run backtest with params
        ...     return backtest_result
        >>>
        >>> result = await quick_optimize(
        ...     run_backtest,
        ...     {"fast_period": [10, 15, 20], "slow_period": [40, 50, 60]},
        ...     primary_metric="sharpe_ratio"
        ... )
    """
    # Convert dict to ParameterRange list
    ranges = [
        ParameterRange(name=name, values=values)
        for name, values in parameter_ranges.items()
    ]

    # Create optimizer
    config = OptimizerConfig(primary_metric=primary_metric)
    optimizer = ParameterOptimizer(backtest_runner, config)

    # Run optimization
    return await optimizer.grid_search(ranges, base_params)
