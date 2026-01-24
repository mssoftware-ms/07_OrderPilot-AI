"""Example usage of IndicatorSetOptimizer (Stage 2).

This script demonstrates how to:
1. Load optimized regime configuration from Stage 1
2. Extract regime-specific bar indices
3. Optimize indicator sets for each regime
4. Export results to JSON

Usage:
    python examples/indicator_set_optimizer_example.py
"""

import json
import logging
from pathlib import Path

import pandas as pd

from src.core.indicator_set_optimizer import IndicatorSetOptimizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_regime_config(config_path: Path) -> dict:
    """Load optimized regime configuration from Stage 1.

    Args:
        config_path: Path to optimized_regime_*.json

    Returns:
        Regime configuration dict
    """
    with open(config_path) as f:
        return json.load(f)


def extract_regime_periods(
    regime_config: dict,
    regime_name: str
) -> list[tuple[int, int]]:
    """Extract bar index periods for a specific regime.

    Args:
        regime_config: Regime configuration
        regime_name: BULL/BEAR/SIDEWAYS

    Returns:
        List of (start_idx, end_idx) tuples
    """
    periods = []

    for period in regime_config.get('regime_periods', []):
        if period['regime'] == regime_name:
            periods.append((period['start_idx'], period['end_idx']))

    return periods


def get_regime_bar_indices(
    regime_periods: list[tuple[int, int]]
) -> list[int]:
    """Convert regime periods to flat list of bar indices.

    Args:
        regime_periods: List of (start_idx, end_idx) tuples

    Returns:
        Flat list of all bar indices
    """
    indices = []

    for start_idx, end_idx in regime_periods:
        indices.extend(range(start_idx, end_idx + 1))

    return indices


def optimize_regime_indicators(
    df: pd.DataFrame,
    regime: str,
    regime_config_path: Path,
    output_dir: Path,
    n_trials: int = 40
) -> dict:
    """Optimize indicators for a specific regime.

    Args:
        df: Full price dataframe
        regime: BULL/BEAR/SIDEWAYS
        regime_config_path: Path to regime config
        output_dir: Output directory for results
        n_trials: Number of trials per indicator

    Returns:
        Optimization results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Optimizing Indicators for {regime} Regime")
    logger.info(f"{'='*60}")

    # Load regime config
    regime_config = load_regime_config(regime_config_path)

    # Extract regime periods
    periods = extract_regime_periods(regime_config, regime)
    logger.info(f"Found {len(periods)} {regime} periods")

    # Get bar indices
    regime_indices = get_regime_bar_indices(periods)
    logger.info(f"Total {regime} bars: {len(regime_indices)}")

    if len(regime_indices) < 100:
        logger.warning(f"Not enough {regime} bars for optimization!")
        return {}

    # Extract symbol and timeframe from config
    source = regime_config['meta']['source']
    symbol = source['symbol']
    timeframe = source['timeframe']

    # Create optimizer
    optimizer = IndicatorSetOptimizer(
        df=df,
        regime=regime,
        regime_indices=regime_indices,
        symbol=symbol,
        timeframe=timeframe,
        regime_config_path=str(regime_config_path)
    )

    # Optimize all signal types
    results = optimizer.optimize_all_signals(n_trials_per_indicator=n_trials)

    # Print summary
    logger.info(f"\n{regime} Optimization Results:")
    logger.info("-" * 60)

    for signal_type, result in results.items():
        logger.info(f"\n{signal_type.upper()}:")
        logger.info(f"  Best Indicator: {result.indicator}")
        logger.info(f"  Score: {result.score:.2f}")
        logger.info(f"  Win Rate: {result.metrics.win_rate:.2%}")
        logger.info(f"  Profit Factor: {result.metrics.profit_factor:.2f}")
        logger.info(f"  Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
        logger.info(f"  Trades: {result.metrics.trades}")
        logger.info(f"  Params: {result.params}")

    # Export to JSON
    output_path = optimizer.export_to_json(results, output_dir)
    logger.info(f"\nSaved results to: {output_path}")

    return results


def main():
    """Main execution."""
    # Configuration
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    DATA_DIR = PROJECT_ROOT / '03_JSON' / 'Entry_Analyzer' / 'Regime'

    # Paths
    REGIME_CONFIG_PATH = DATA_DIR / 'STUFE_1_Regime' / 'optimized_regime_BTCUSDT_5m.json'
    OUTPUT_DIR = DATA_DIR / 'STUFE_2_Indicators'

    # Check if regime config exists
    if not REGIME_CONFIG_PATH.exists():
        logger.error(f"Regime config not found: {REGIME_CONFIG_PATH}")
        logger.error("Please run Stage 1 (RegimeOptimizer) first!")
        return

    # Load price data (replace with actual data loading)
    logger.info("Loading price data...")

    # Example: Load from CSV or database
    # For this example, we'll use dummy data
    # In production, replace with actual data loading:
    #
    # from src.core.market_data.providers import YahooProvider
    # provider = YahooProvider()
    # df = provider.get_historical_data('BTCUSDT', '5m', days=30)

    import numpy as np
    from datetime import datetime, timedelta

    # Generate sample data (REPLACE THIS WITH ACTUAL DATA)
    np.random.seed(42)
    n = 2000

    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n) * 1)
    low = close - np.abs(np.random.randn(n) * 1)
    open_ = close + np.random.randn(n) * 0.5
    volume = np.random.randint(1000, 10000, n)

    df = pd.DataFrame({
        'timestamp': [datetime.now() - timedelta(minutes=5*i) for i in range(n)],
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    logger.info(f"Loaded {len(df)} bars")

    # Optimize for each regime
    REGIMES = ['BULL', 'BEAR', 'SIDEWAYS']

    # Create output directories
    for regime in REGIMES:
        regime_dir = OUTPUT_DIR / regime
        regime_dir.mkdir(parents=True, exist_ok=True)

    # Optimization settings
    N_TRIALS = 40  # Trials per indicator (use 5-10 for quick testing)

    all_results = {}

    for regime in REGIMES:
        try:
            results = optimize_regime_indicators(
                df=df,
                regime=regime,
                regime_config_path=REGIME_CONFIG_PATH,
                output_dir=OUTPUT_DIR / regime,
                n_trials=N_TRIALS
            )

            all_results[regime] = results

        except Exception as e:
            logger.error(f"Error optimizing {regime}: {e}", exc_info=True)

    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("STAGE 2 OPTIMIZATION COMPLETE")
    logger.info(f"{'='*60}")

    for regime in REGIMES:
        if regime in all_results:
            logger.info(f"\n{regime}:")
            enabled_count = sum(
                1 for r in all_results[regime].values()
                if r.score > 30
            )
            logger.info(f"  Enabled signals: {enabled_count}/4")


if __name__ == '__main__':
    main()
