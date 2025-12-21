"""Demo script for AI-guided Parameter Optimization.

Demonstrates:
- Grid search parameter optimization
- AI-guided optimization with iterative refinement
- Parameter sensitivity analysis
- Quick optimization helper
- Best practices for parameter tuning

Usage:
    python tools/demo_parameter_optimization.py
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.backtesting.optimization import (
    ParameterOptimizer,
    ParameterRange,
    OptimizerConfig,
    quick_optimize,
)
from src.core.models.backtest_models import (
    BacktestResult,
    BacktestMetrics,
    Trade,
    TradeSide,
    EquityPoint,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Mock Backtest Runner ====================

async def mock_backtest_runner(params: dict) -> BacktestResult:
    """Mock backtest runner that simulates strategy performance.

    This simulates a realistic strategy where:
    - Fast periods between 12-18 work best
    - Slow periods between 45-55 work best
    - Stop loss around 2% is optimal
    - Performance degrades outside these ranges

    Args:
        params: Strategy parameters

    Returns:
        Simulated backtest result
    """
    # Extract parameters
    fast_period = params.get("fast_period", 14)
    slow_period = params.get("slow_period", 50)
    stop_loss_pct = params.get("stop_loss_pct", 2.0)

    # Small delay to simulate real backtest
    await asyncio.sleep(0.1)

    # Calculate performance based on parameters
    # This simulates a strategy with optimal parameters

    # Fast period: optimal around 15
    fast_score = 1.0 - abs(fast_period - 15) / 30.0

    # Slow period: optimal around 50
    slow_score = 1.0 - abs(slow_period - 50) / 30.0

    # Stop loss: optimal around 2%
    sl_score = 1.0 - abs(stop_loss_pct - 2.0) / 5.0

    # Combined score (0-1)
    combined_score = (fast_score * 0.4 + slow_score * 0.3 + sl_score * 0.3)
    combined_score = max(0.2, min(1.0, combined_score))  # Clamp to 0.2-1.0

    # Generate metrics based on score
    sharpe_ratio = 0.5 + combined_score * 1.5  # Range: 0.5 to 2.0
    total_return_pct = 10.0 + combined_score * 40.0  # Range: 10% to 50%
    win_rate = 0.45 + combined_score * 0.25  # Range: 45% to 70%
    profit_factor = 1.0 + combined_score * 1.5  # Range: 1.0 to 2.5
    max_drawdown_pct = -25.0 + combined_score * 15.0  # Range: -25% to -10%

    # Calculate other metrics
    total_trades = int(40 + combined_score * 40)  # Range: 40 to 80
    winning_trades = int(total_trades * win_rate)
    losing_trades = total_trades - winning_trades

    initial_capital = 10000.0
    final_capital = initial_capital * (1 + total_return_pct / 100)

    # Create metrics
    metrics = BacktestMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        expectancy=total_return_pct / total_trades if total_trades > 0 else 0,
        max_drawdown_pct=max_drawdown_pct,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sharpe_ratio * 1.2,
        total_return_pct=total_return_pct,
        annual_return_pct=total_return_pct,  # Assume 1 year
        avg_win=200.0 * combined_score,
        avg_loss=-100.0 * combined_score,
        largest_win=500.0 * combined_score,
        largest_loss=-300.0 * combined_score,
        avg_r_multiple=1.5 * combined_score,
        max_consecutive_wins=int(5 + combined_score * 5),
        max_consecutive_losses=int(3 + (1 - combined_score) * 3)
    )

    # Create result
    start = datetime(2023, 1, 1)
    end = datetime(2023, 12, 31)

    result = BacktestResult(
        symbol="AAPL",
        timeframe="1D",
        mode="backtest",
        start=start,
        end=end,
        initial_capital=initial_capital,
        final_capital=final_capital,
        metrics=metrics,
        strategy_name="SMA Crossover",
        strategy_params=params
    )

    return result


# ==================== Demos ====================

async def demo_simple_grid_search():
    """Demonstrate simple grid search optimization."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: Simple Grid Search Optimization")
    logger.info("=" * 80)

    logger.info("\n[1/3] Setting up parameter ranges...")
    logger.info("  Testing 3 x 3 = 9 combinations")

    # Define parameter ranges
    ranges = [
        ParameterRange(
            name="fast_period",
            values=[10, 15, 20],
            type="discrete"
        ),
        ParameterRange(
            name="slow_period",
            values=[40, 50, 60],
            type="discrete"
        )
    ]

    logger.info("\n[2/3] Running grid search...")

    # Create optimizer without AI guidance for speed
    config = OptimizerConfig(
        use_ai_guidance=False,
        primary_metric="sharpe_ratio"
    )
    optimizer = ParameterOptimizer(mock_backtest_runner, config)

    # Run optimization
    result = await optimizer.grid_search(
        ranges,
        base_params={"stop_loss_pct": 2.0}
    )

    logger.info("\n[3/3] Results:")
    logger.info(f"  Total tests: {result.total_tests}")
    logger.info(f"  Successful: {result.successful_tests}")
    logger.info(f"  Time: {result.optimization_time_seconds:.2f}s")
    logger.info(f"\n  Best Score: {result.best_score:.4f}")
    logger.info(f"  Best Parameters:")
    for param, value in result.best_parameters.items():
        logger.info(f"    • {param}: {value}")

    # Show sensitivity
    logger.info(f"\n  Parameter Sensitivity:")
    for param, analysis in result.sensitivity_analysis.items():
        logger.info(f"    • {param}: {analysis['impact']} impact (score: {analysis['sensitivity_score']:.4f})")

    return result


async def demo_advanced_grid_search():
    """Demonstrate advanced grid search with multiple parameters."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: Advanced Grid Search (3 Parameters)")
    logger.info("=" * 80)

    logger.info("\n[1/3] Setting up parameter ranges...")
    logger.info("  Testing 3 x 3 x 3 = 27 combinations")

    ranges = [
        ParameterRange(name="fast_period", values=[12, 15, 18]),
        ParameterRange(name="slow_period", values=[45, 50, 55]),
        ParameterRange(name="stop_loss_pct", values=[1.5, 2.0, 2.5])
    ]

    logger.info("\n[2/3] Running optimization...")

    config = OptimizerConfig(
        use_ai_guidance=False,
        primary_metric="sharpe_ratio",
        secondary_metrics=["total_return_pct", "profit_factor"]
    )
    optimizer = ParameterOptimizer(mock_backtest_runner, config)

    result = await optimizer.grid_search(ranges)

    logger.info("\n[3/3] Results:")
    logger.info(f"  Best Score: {result.best_score:.4f}")
    logger.info(f"  Best Parameters: {result.best_parameters}")

    # Show top 5 results
    logger.info(f"\n  Top 5 Results:")
    top_tests = sorted(
        [t for t in result.all_tests if t.score is not None],
        key=lambda t: t.score,
        reverse=True
    )[:5]

    for i, test in enumerate(top_tests, 1):
        logger.info(f"    {i}. Score: {test.score:.4f}")
        logger.info(f"       Params: {test.parameters}")
        logger.info(f"       Sharpe: {test.metrics.get('sharpe_ratio', 'N/A'):.2f}")

    return result


async def demo_ai_guided_optimization():
    """Demonstrate AI-guided optimization with iterative refinement."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: AI-Guided Optimization (Iterative)")
    logger.info("=" * 80)

    import os
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("\n⚠️  OPENAI_API_KEY not set. Skipping AI-guided demo.")
        logger.info("  Set OPENAI_API_KEY to enable AI-guided optimization")
        return

    logger.info("\n[1/3] Setting up initial parameter ranges...")

    ranges = [
        ParameterRange(name="fast_period", values=[10, 15, 20, 25]),
        ParameterRange(name="slow_period", values=[40, 50, 60])
    ]

    logger.info("\n[2/3] Running AI-guided optimization (3 iterations)...")
    logger.info("  AI will analyze results and suggest refinements")

    config = OptimizerConfig(
        use_ai_guidance=True,
        primary_metric="sharpe_ratio",
        ai_analysis_frequency=5
    )
    optimizer = ParameterOptimizer(mock_backtest_runner, config)

    result, insights = await optimizer.optimize_with_ai(
        ranges,
        base_params={"stop_loss_pct": 2.0},
        max_iterations=2  # Reduced for demo
    )

    logger.info("\n[3/3] AI Insights:")
    logger.info(f"  Summary: {insights.summary}")
    logger.info(f"  Confidence: {insights.confidence_score:.2%}")
    logger.info(f"\n  Best Parameters Analysis:")
    logger.info(f"    {insights.best_parameter_analysis}")

    if insights.parameter_importance:
        logger.info(f"\n  Parameter Importance:")
        for param, importance in sorted(
            insights.parameter_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            logger.info(f"    • {param}: {importance:.2f}")

    if insights.recommendations:
        logger.info(f"\n  Recommendations:")
        for i, rec in enumerate(insights.recommendations, 1):
            logger.info(f"    {i}. {rec.get('improvement', 'N/A')}")
            logger.info(f"       Impact: {rec.get('expected_impact', 'N/A')}")

    return result, insights


async def demo_quick_optimize():
    """Demonstrate quick_optimize convenience function."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: Quick Optimize (Convenience Function)")
    logger.info("=" * 80)

    logger.info("\n[1/2] Running quick optimization...")

    result = await quick_optimize(
        mock_backtest_runner,
        parameter_ranges={
            "fast_period": [12, 14, 16, 18],
            "slow_period": [45, 50, 55]
        },
        base_params={"stop_loss_pct": 2.0},
        primary_metric="sharpe_ratio"
    )

    logger.info("\n[2/2] Results:")
    logger.info(f"  Best Score: {result.best_score:.4f}")
    logger.info(f"  Best Parameters: {result.best_parameters}")
    logger.info(f"  Time: {result.optimization_time_seconds:.2f}s")

    # Show best result metrics
    if result.best_result:
        logger.info(f"\n  Best Result Metrics:")
        logger.info(f"    • Sharpe Ratio: {result.best_result.metrics.sharpe_ratio:.2f}")
        logger.info(f"    • Total Return: {result.best_result.metrics.total_return_pct:.2f}%")
        logger.info(f"    • Win Rate: {result.best_result.metrics.win_rate:.2%}")
        logger.info(f"    • Max Drawdown: {result.best_result.metrics.max_drawdown_pct:.2f}%")

    return result


async def demo_sensitivity_visualization():
    """Demonstrate parameter sensitivity visualization."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 5: Parameter Sensitivity Analysis")
    logger.info("=" * 80)

    logger.info("\n[1/2] Running optimization with detailed sensitivity tracking...")

    ranges = [
        ParameterRange(name="fast_period", values=[8, 10, 12, 14, 16, 18, 20]),
        ParameterRange(name="stop_loss_pct", values=[1.0, 1.5, 2.0, 2.5, 3.0])
    ]

    config = OptimizerConfig(use_ai_guidance=False, primary_metric="sharpe_ratio")
    optimizer = ParameterOptimizer(mock_backtest_runner, config)

    result = await optimizer.grid_search(
        ranges,
        base_params={"slow_period": 50}
    )

    logger.info("\n[2/2] Sensitivity Analysis:")

    for param_name, analysis in result.sensitivity_analysis.items():
        logger.info(f"\n  Parameter: {param_name}")
        logger.info(f"  Impact Level: {analysis['impact'].upper()}")
        logger.info(f"  Sensitivity Score: {analysis['sensitivity_score']:.4f}")

        logger.info(f"  Value Statistics:")
        for value, stats in analysis['value_stats'].items():
            logger.info(f"    • {value}: mean={stats['mean_score']:.4f}, max={stats['max_score']:.4f}, tests={stats['count']}")

    return result


async def main():
    """Run all demos."""
    logger.info("=" * 80)
    logger.info("PARAMETER OPTIMIZATION DEMO")
    logger.info("=" * 80)

    try:
        # Run demos in sequence
        await demo_simple_grid_search()
        await demo_advanced_grid_search()
        await demo_ai_guided_optimization()
        await demo_quick_optimize()
        await demo_sensitivity_visualization()

        logger.info("\n" + "=" * 80)
        logger.info("ALL DEMOS COMPLETE")
        logger.info("=" * 80)

        logger.info("\nKey Takeaways:")
        logger.info("  1. Grid search tests all parameter combinations")
        logger.info("  2. AI guidance provides insights and refinements")
        logger.info("  3. Sensitivity analysis shows parameter importance")
        logger.info("  4. quick_optimize() provides easy-to-use interface")
        logger.info("  5. Multi-objective optimization balances multiple metrics")

        logger.info("\nBest Practices:")
        logger.info("  • Start with wide parameter ranges, then narrow")
        logger.info("  • Use AI guidance for complex parameter spaces")
        logger.info("  • Check sensitivity to avoid overfitting")
        logger.info("  • Validate optimized parameters on out-of-sample data")
        logger.info("  • Consider multiple optimization metrics (not just Sharpe)")

        logger.info("\nNext Steps:")
        logger.info("  • Integrate with real BacktestEngine")
        logger.info("  • Test optimized parameters on different time periods")
        logger.info("  • Use walk-forward optimization for robustness")
        logger.info("  • Implement parameter stability testing")

        return 0

    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
