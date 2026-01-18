#!/usr/bin/env python3
"""Indicator Optimization Orchestrator Script.

Complete workflow:
1. Load indicator catalog
2. Generate parameter combinations (Grid Search)
3. Optimize indicators with backtest scoring
4. Select best combinations
5. Generate JSON configs

Usage:
    python tools/optimize_indicators.py --regime R2_range --preset balanced
    python tools/optimize_indicators.py --all-regimes --preset exhaustive
    python tools/optimize_indicators.py --indicators RSI MACD ADX --regime R1_trend
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.tradingbot.indicator_config_generator import IndicatorConfigGenerator
from src.core.tradingbot.indicator_grid_search import GridSearchConfig, IndicatorGridSearch
from src.core.tradingbot.indicator_optimizer import IndicatorOptimizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndicatorOptimizationOrchestrator:
    """Orchestrates the complete indicator optimization workflow."""

    def __init__(self, catalog_path: str = "config/indicator_catalog.yaml"):
        """Initialize orchestrator.

        Args:
            catalog_path: Path to indicator catalog YAML
        """
        self.catalog_path = catalog_path
        self.grid_search = IndicatorGridSearch(catalog_path)
        self.optimizer = IndicatorOptimizer(catalog_path)
        self.config_generator = IndicatorConfigGenerator()

        logger.info("Initialized Indicator Optimization Orchestrator")

    def run_full_workflow(
        self,
        regime_id: str,
        preset: str = "balanced",
        indicator_types: list[str] | None = None,
        output_dir: str = "03_JSON/Trading_Bot"
    ) -> str:
        """Run complete optimization workflow for a single regime.

        Args:
            regime_id: Regime ID (R1_trend, R2_range, etc.)
            preset: Grid search preset (quick_scan, balanced, exhaustive)
            indicator_types: Optional list of specific indicators to optimize
            output_dir: Directory to save generated JSON configs

        Returns:
            Path to generated JSON config file
        """
        logger.info("=" * 80)
        logger.info(f"STARTING OPTIMIZATION WORKFLOW FOR {regime_id}")
        logger.info("=" * 80)

        # Step 1: Determine indicators to optimize
        if indicator_types is None:
            # Get regime-compatible indicators
            indicator_types = self.grid_search.get_regime_compatible_indicators(
                regime_id,
                min_score=0.7
            )
            logger.info(f"Auto-selected {len(indicator_types)} regime-compatible indicators")
        else:
            logger.info(f"Using user-specified indicators: {indicator_types}")

        # Step 2: Generate sample data for backtesting
        # In production, this would load real market data
        sample_data = self._generate_sample_data()
        regime_labels = self._generate_sample_regime_labels(sample_data, regime_id)

        self.optimizer.set_data(sample_data, regime_labels)
        logger.info(f"Loaded {len(sample_data)} bars of sample data")

        # Step 3: Configure grid search
        config = GridSearchConfig(
            preset=preset,
            filter_by_regime=regime_id,
            min_compatibility_score=0.7
        )

        # Step 4: Optimize indicators
        logger.info(f"Starting optimization with preset='{preset}'...")
        optimization_results = self.optimizer.optimize_batch(
            indicator_types=indicator_types,
            regime_id=regime_id,
            config=config,
            top_n_per_indicator=3
        )

        # Step 5: Generate reports
        for indicator_type, scores in optimization_results.items():
            if scores:
                report = self.optimizer.generate_optimization_report(scores)
                print(report)

        # Step 6: Generate JSON config
        strategy_name = f"optimized_{regime_id.lower()}"
        output_path = f"{output_dir}/{strategy_name}.json"

        logger.info(f"Generating JSON config: {output_path}")
        config_dict = self.config_generator.generate_regime_config(
            regime_id=regime_id,
            optimization_results=optimization_results,
            output_path=output_path,
            strategy_name=strategy_name
        )

        logger.info("=" * 80)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info(f"Generated config: {output_path}")
        logger.info(f"Total indicators: {len(optimization_results)}")
        logger.info(f"Total combinations: {sum(len(s) for s in optimization_results.values())}")
        logger.info("=" * 80)

        return output_path

    def run_all_regimes(
        self,
        preset: str = "balanced",
        output_dir: str = "03_JSON/Trading_Bot"
    ) -> dict[str, str]:
        """Run optimization for all regimes.

        Args:
            preset: Grid search preset
            output_dir: Directory to save generated JSON configs

        Returns:
            Dictionary mapping regime_id to output file path
        """
        regimes = ["R1_trend", "R2_range", "R3_breakout", "R4_volatile"]
        output_paths = {}

        for regime_id in regimes:
            logger.info(f"\n\n{'=' * 80}")
            logger.info(f"Processing {regime_id}...")
            logger.info(f"{'=' * 80}\n")

            try:
                output_path = self.run_full_workflow(
                    regime_id=regime_id,
                    preset=preset,
                    output_dir=output_dir
                )
                output_paths[regime_id] = output_path

            except Exception as e:
                logger.error(f"Failed to optimize {regime_id}: {e}")

        # Summary
        logger.info("\n\n" + "=" * 80)
        logger.info("ALL REGIMES OPTIMIZATION COMPLETE")
        logger.info("=" * 80)
        for regime_id, path in output_paths.items():
            logger.info(f"  {regime_id}: {path}")
        logger.info("=" * 80)

        return output_paths

    def _generate_sample_data(self, bars: int = 1000) -> pd.DataFrame:
        """Generate sample OHLCV data for backtesting.

        In production, this would load real market data from database or API.

        Args:
            bars: Number of bars to generate

        Returns:
            DataFrame with OHLCV data
        """
        import numpy as np

        # Generate realistic price data
        base_price = 100.0
        returns = np.random.normal(0.0005, 0.02, bars)
        prices = base_price * (1 + returns).cumprod()

        # Generate OHLC
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, bars)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, bars)))
        open_prices = prices + np.random.normal(0, 1, bars)
        close_prices = prices

        # Generate volume
        volume = np.random.lognormal(15, 1, bars)

        data = pd.DataFrame({
            'open': open_prices,
            'high': high,
            'low': low,
            'close': close_prices,
            'volume': volume,
            'datetime': pd.date_range('2024-01-01', periods=bars, freq='1H')
        })

        return data

    def _generate_sample_regime_labels(
        self,
        data: pd.DataFrame,
        primary_regime: str
    ) -> pd.Series:
        """Generate sample regime labels for data.

        In production, this would use the real RegimeEngine classification.

        Args:
            data: OHLCV DataFrame
            primary_regime: Primary regime for this data

        Returns:
            Series with regime labels per bar
        """
        import numpy as np

        # Assign primary regime to 70% of bars, others to 30%
        labels = [primary_regime] * len(data)
        other_regimes = ["R1_trend", "R2_range", "R3_breakout", "R4_volatile"]
        other_regimes = [r for r in other_regimes if r != primary_regime]

        # Randomly assign 30% to other regimes
        n_other = int(len(data) * 0.3)
        other_indices = np.random.choice(len(data), n_other, replace=False)

        for idx in other_indices:
            labels[idx] = np.random.choice(other_regimes)

        return pd.Series(labels, index=data.index)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Optimize indicator parameters and generate JSON configs"
    )

    parser.add_argument(
        '--regime',
        type=str,
        help='Regime ID to optimize (R1_trend, R2_range, R3_breakout, R4_volatile)'
    )

    parser.add_argument(
        '--all-regimes',
        action='store_true',
        help='Optimize all regimes'
    )

    parser.add_argument(
        '--preset',
        type=str,
        default='balanced',
        choices=['quick_scan', 'balanced', 'exhaustive', 'regime_optimized'],
        help='Grid search preset (default: balanced)'
    )

    parser.add_argument(
        '--indicators',
        nargs='+',
        help='Specific indicators to optimize (e.g., RSI MACD ADX)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='03_JSON/Trading_Bot',
        help='Output directory for JSON configs (default: 03_JSON/Trading_Bot)'
    )

    parser.add_argument(
        '--catalog',
        type=str,
        default='config/indicator_catalog.yaml',
        help='Path to indicator catalog (default: config/indicator_catalog.yaml)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.all_regimes and not args.regime:
        parser.error("Must specify either --regime or --all-regimes")

    # Initialize orchestrator
    orchestrator = IndicatorOptimizationOrchestrator(catalog_path=args.catalog)

    # Run workflow
    if args.all_regimes:
        orchestrator.run_all_regimes(
            preset=args.preset,
            output_dir=args.output_dir
        )
    else:
        orchestrator.run_full_workflow(
            regime_id=args.regime,
            preset=args.preset,
            indicator_types=args.indicators,
            output_dir=args.output_dir
        )


if __name__ == "__main__":
    main()
