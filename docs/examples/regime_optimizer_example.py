"""Example usage of RegimeOptimizer class.

This script demonstrates how to use the RegimeOptimizer to find optimal
parameters for regime detection using Optuna TPE optimization.

Example Output:
- Optimization results JSON file
- Best parameters for each regime
- Bar indices for each regime period
- Performance metrics (F1 scores, stability)
"""

import logging
from pathlib import Path

import pandas as pd

from src.core.regime_optimizer import (
    RegimeOptimizer,
    AllParamRanges,
    ADXParamRanges,
    SMAParamRanges,
    RSIParamRanges,
    BBParamRanges,
    ParamRange,
    OptimizationConfig,
    OptimizationMode,
    OptimizationMethod,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sample_data() -> pd.DataFrame:
    """Load sample OHLCV data.

    In production, replace this with actual market data loading.

    Returns:
        OHLCV DataFrame
    """
    # Example: Load from CSV
    # data = pd.read_csv('data/BTCUSDT_5m.csv', parse_dates=['timestamp'])
    # data.set_index('timestamp', inplace=True)

    # For this example, generate synthetic data
    import numpy as np

    np.random.seed(42)
    n = 2000

    dates = pd.date_range(start='2024-01-01', periods=n, freq='5min')

    price = 40000.0
    prices = []
    for _ in range(n):
        change = np.random.randn() * 50
        price += change
        prices.append(price)

    prices = np.array(prices)

    data = pd.DataFrame({
        'open': prices + np.random.randn(n) * 10,
        'high': prices + abs(np.random.randn(n) * 20),
        'low': prices - abs(np.random.randn(n) * 20),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, n),
    }, index=dates)

    logger.info(f"Loaded {len(data)} bars of data")
    return data


def define_param_ranges() -> AllParamRanges:
    """Define parameter ranges for optimization.

    These ranges determine the search space for Optuna.
    Adjust based on your market and timeframe.

    Returns:
        AllParamRanges configuration
    """
    return AllParamRanges(
        adx=ADXParamRanges(
            period=ParamRange(min=10, max=20, step=2),
            threshold=ParamRange(min=20.0, max=30.0, step=2.5),
        ),
        sma_fast=SMAParamRanges(
            period=ParamRange(min=5, max=20, step=5),
        ),
        sma_slow=SMAParamRanges(
            period=ParamRange(min=30, max=60, step=10),
        ),
        rsi=RSIParamRanges(
            period=ParamRange(min=10, max=20, step=5),
            sideways_low=ParamRange(min=35, max=45, step=5),
            sideways_high=ParamRange(min=55, max=65, step=5),
        ),
        bb=BBParamRanges(
            period=ParamRange(min=15, max=25, step=5),
            std_dev=ParamRange(min=1.5, max=2.5, step=0.5),
            width_percentile=ParamRange(min=25.0, max=40.0, step=5.0),
        ),
    )


def create_optimization_config(mode: str = "standard") -> OptimizationConfig:
    """Create optimization configuration.

    Args:
        mode: Optimization mode (quick/standard/thorough/exhaustive)

    Returns:
        OptimizationConfig
    """
    mode_enum = OptimizationMode(mode)

    mode_trials = {
        OptimizationMode.QUICK: 50,
        OptimizationMode.STANDARD: 150,
        OptimizationMode.THOROUGH: 300,
        OptimizationMode.EXHAUSTIVE: 500,
    }

    return OptimizationConfig(
        mode=mode_enum,
        method=OptimizationMethod.TPE_MULTIVARIATE,
        max_trials=mode_trials[mode_enum],
        n_startup_trials=20,
        seed=42,
    )


def run_optimization_example():
    """Run complete optimization example."""
    logger.info("=" * 80)
    logger.info("RegimeOptimizer Example - Stage 1 Optimization")
    logger.info("=" * 80)

    # 1. Load data
    logger.info("\n1. Loading market data...")
    data = load_sample_data()

    # 2. Define parameter ranges
    logger.info("\n2. Defining parameter ranges...")
    param_ranges = define_param_ranges()
    logger.info(f"ADX period: {param_ranges.adx.period.min}-{param_ranges.adx.period.max}")
    logger.info(f"SMA fast: {param_ranges.sma_fast.period.min}-{param_ranges.sma_fast.period.max}")
    logger.info(f"SMA slow: {param_ranges.sma_slow.period.min}-{param_ranges.sma_slow.period.max}")

    # 3. Create optimization config
    logger.info("\n3. Creating optimization config...")
    config = create_optimization_config(mode="standard")
    logger.info(f"Mode: {config.mode.value}")
    logger.info(f"Method: {config.method.value}")
    logger.info(f"Max trials: {config.max_trials}")

    # 4. Create optimizer
    logger.info("\n4. Creating optimizer...")
    optimizer = RegimeOptimizer(
        data=data,
        param_ranges=param_ranges,
        config=config,
        storage_path=Path("optuna_regime_example.db"),
    )

    # 5. Run optimization
    logger.info("\n5. Running optimization...")
    logger.info("This may take a few minutes...")
    results = optimizer.optimize()

    # 6. Display results
    logger.info("\n6. Optimization Results")
    logger.info("=" * 80)

    logger.info(f"\nTotal trials: {len(results)}")
    logger.info(f"Best score: {results[0].score:.2f}")

    logger.info("\nTop 5 Results:")
    for i, result in enumerate(results[:5], 1):
        logger.info(f"\n--- Rank {i} ---")
        logger.info(f"Score: {result.score:.2f}")
        logger.info(f"ADX: period={result.params.adx_period}, threshold={result.params.adx_threshold}")
        logger.info(f"SMA: fast={result.params.sma_fast_period}, slow={result.params.sma_slow_period}")
        logger.info(f"RSI: period={result.params.rsi_period}, range=[{result.params.rsi_sideways_low}, {result.params.rsi_sideways_high}]")
        logger.info(f"BB: period={result.params.bb_period}, std={result.params.bb_std_dev}, percentile={result.params.bb_width_percentile}")
        logger.info(f"Metrics: F1-Bull={result.metrics.f1_bull:.3f}, F1-Bear={result.metrics.f1_bear:.3f}, "
                   f"F1-Sideways={result.metrics.f1_sideways:.3f}, Stability={result.metrics.stability_score:.3f}")
        logger.info(f"Regime Distribution: Bull={result.metrics.bull_bars}, Bear={result.metrics.bear_bars}, "
                   f"Sideways={result.metrics.sideways_bars}")

    # 7. Get regime periods
    logger.info("\n7. Regime Periods (Best Parameters)")
    logger.info("=" * 80)

    periods = optimizer.get_best_regime_periods()
    logger.info(f"\nTotal regime periods: {len(periods)}")

    # Show first 10 periods
    logger.info("\nFirst 10 periods:")
    for i, period in enumerate(periods[:10], 1):
        logger.info(
            f"{i}. {period.regime.value}: bars [{period.start_idx}-{period.end_idx}] "
            f"({period.bars} bars)"
        )
        if period.start_timestamp and period.end_timestamp:
            logger.info(
                f"   Time: {period.start_timestamp.strftime('%Y-%m-%d %H:%M')} - "
                f"{period.end_timestamp.strftime('%Y-%m-%d %H:%M')}"
            )

    # 8. Export results
    logger.info("\n8. Exporting results...")
    output_path = Path("regime_optimization_results.json")
    optimizer.export_results(results, output_path)
    logger.info(f"Results exported to: {output_path}")

    logger.info("\n" + "=" * 80)
    logger.info("Optimization complete!")
    logger.info("=" * 80)


def quick_optimization_example():
    """Quick optimization example with minimal trials."""
    logger.info("Running QUICK optimization (50 trials)...")

    data = load_sample_data()
    param_ranges = define_param_ranges()
    config = create_optimization_config(mode="quick")

    optimizer = RegimeOptimizer(
        data=data,
        param_ranges=param_ranges,
        config=config,
    )

    results = optimizer.optimize()

    logger.info(f"\nBest score: {results[0].score:.2f}")
    logger.info(f"Best params: {results[0].params}")


if __name__ == '__main__':
    # Run full example
    run_optimization_example()

    # Or run quick example
    # quick_optimization_example()
