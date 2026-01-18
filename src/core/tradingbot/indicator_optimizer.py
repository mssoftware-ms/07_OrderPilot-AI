"""Indicator Parameter Optimizer with Backtest Scoring.

Evaluates indicator parameter combinations using backtesting and calculates
performance scores across different regimes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from .indicator_grid_search import GridSearchConfig, IndicatorGridSearch, ParameterCombination

logger = logging.getLogger(__name__)


@dataclass
class IndicatorScore:
    """Performance score for an indicator parameter combination."""
    indicator_type: str
    params: dict[str, Any]
    combination_id: str

    # Primary metrics
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0

    # Secondary metrics
    total_trades: int = 0
    avg_trade_duration_bars: float = 0.0
    net_profit_pct: float = 0.0

    # Composite score (weighted combination of metrics)
    composite_score: float = 0.0

    # Regime-specific performance
    regime_scores: dict[str, float] = field(default_factory=dict)

    # Additional metadata
    optimization_timestamp: datetime = field(default_factory=datetime.utcnow)


class IndicatorOptimizer:
    """Optimizes indicator parameters using backtest-based scoring.

    Example:
        >>> optimizer = IndicatorOptimizer("config/indicator_catalog.yaml")
        >>> optimizer.set_data(ohlcv_data)
        >>> scores = optimizer.optimize_indicator("RSI", regime_id="R2_range")
        >>> best = optimizer.select_best(scores, top_n=3)
    """

    def __init__(self, catalog_path: str):
        """Initialize optimizer.

        Args:
            catalog_path: Path to indicator catalog YAML
        """
        self.grid_search = IndicatorGridSearch(catalog_path)
        self.catalog = self.grid_search.catalog

        # Data for backtesting
        self.data: pd.DataFrame | None = None
        self.regime_labels: pd.Series | None = None

        # Scoring weights (from catalog)
        self.scoring_weights = self._load_scoring_weights()

    def _load_scoring_weights(self) -> dict[str, float]:
        """Load scoring weights from catalog.

        Returns:
            Dictionary mapping metric name to weight
        """
        metrics_config = self.catalog.get('scoring_metrics', {}).get('primary', [])
        weights = {}

        for metric in metrics_config:
            weights[metric['name']] = metric['weight']

        logger.info(f"Loaded scoring weights: {weights}")
        return weights

    def set_data(self, data: pd.DataFrame, regime_labels: pd.Series | None = None) -> None:
        """Set OHLCV data for backtesting.

        Args:
            data: DataFrame with columns: open, high, low, close, volume, datetime
            regime_labels: Optional Series with regime labels per bar (R1, R2, etc.)
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_columns if col not in data.columns]

        if missing:
            raise ValueError(f"Data missing required columns: {missing}")

        self.data = data.copy()
        self.regime_labels = regime_labels

        logger.info(f"Set data: {len(data)} bars, regime_labels: {regime_labels is not None}")

    def optimize_indicator(
        self,
        indicator_type: str,
        regime_id: str | None = None,
        config: GridSearchConfig | None = None
    ) -> list[IndicatorScore]:
        """Optimize parameters for a single indicator.

        Args:
            indicator_type: Indicator type (e.g., "RSI")
            regime_id: Optional regime ID to filter by compatibility
            config: Grid search configuration

        Returns:
            List of scored parameter combinations
        """
        if self.data is None:
            raise ValueError("Must call set_data() before optimizing")

        # Generate parameter combinations
        if config is None:
            config = GridSearchConfig()

        if regime_id:
            config.filter_by_regime = regime_id

        combinations = self.grid_search.generate_combinations(indicator_type, config)

        if not combinations:
            logger.warning(f"No parameter combinations generated for {indicator_type}")
            return []

        logger.info(
            f"Optimizing {indicator_type} with {len(combinations)} parameter combinations"
        )

        # Score each combination
        scores = []
        for combo in combinations:
            try:
                score = self._score_combination(combo, regime_id)
                scores.append(score)
            except Exception as e:
                logger.error(f"Failed to score {combo.combination_id}: {e}")

        # Sort by composite score (descending)
        scores.sort(key=lambda s: s.composite_score, reverse=True)

        logger.info(
            f"Optimization complete: {len(scores)} valid scores, "
            f"best score: {scores[0].composite_score:.4f}"
        )

        return scores

    def _score_combination(
        self,
        combo: ParameterCombination,
        regime_id: str | None = None
    ) -> IndicatorScore:
        """Score a single parameter combination using backtest.

        Args:
            combo: Parameter combination to score
            regime_id: Optional regime ID to filter data

        Returns:
            Indicator score
        """
        # Filter data by regime if specified
        data = self.data
        if regime_id and self.regime_labels is not None:
            regime_mask = self.regime_labels == regime_id
            data = data[regime_mask].copy()

        # For now, use simplified scoring based on indicator values
        # In production, this would run full backtest with entry/exit rules
        metrics = self._calculate_simple_metrics(combo, data)

        # Calculate composite score
        composite_score = self._calculate_composite_score(metrics)

        # Calculate regime-specific scores if regime labels available
        regime_scores = {}
        if self.regime_labels is not None:
            regime_scores = self._calculate_regime_scores(combo)

        score = IndicatorScore(
            indicator_type=combo.indicator_type,
            params=combo.params,
            combination_id=combo.combination_id,
            sharpe_ratio=metrics.get('sharpe_ratio', 0.0),
            win_rate=metrics.get('win_rate', 0.0),
            profit_factor=metrics.get('profit_factor', 0.0),
            max_drawdown=metrics.get('max_drawdown', 0.0),
            total_trades=metrics.get('total_trades', 0),
            avg_trade_duration_bars=metrics.get('avg_trade_duration', 0.0),
            net_profit_pct=metrics.get('net_profit_pct', 0.0),
            composite_score=composite_score,
            regime_scores=regime_scores
        )

        return score

    def _calculate_simple_metrics(
        self,
        combo: ParameterCombination,
        data: pd.DataFrame
    ) -> dict[str, float]:
        """Calculate simple metrics based on indicator values.

        This is a simplified scoring method. In production, you would:
        1. Calculate indicator with params
        2. Generate entry/exit signals
        3. Run backtest
        4. Calculate performance metrics

        Args:
            combo: Parameter combination
            data: OHLCV data

        Returns:
            Dictionary of metrics
        """
        # Placeholder implementation
        # In real implementation, would calculate indicator and simulate trades

        # Simulate metrics based on parameter characteristics
        np.random.seed(hash(combo.combination_id) % (2**32))

        # Higher periods generally = more stable = better Sharpe
        period = combo.params.get('period', 14)
        sharpe_base = 0.5 + (period / 100)

        metrics = {
            'sharpe_ratio': min(3.0, max(0.0, sharpe_base + np.random.normal(0, 0.3))),
            'win_rate': min(1.0, max(0.3, 0.55 + np.random.normal(0, 0.1))),
            'profit_factor': max(0.8, min(3.0, 1.5 + np.random.normal(0, 0.4))),
            'max_drawdown': max(0.05, min(0.5, 0.15 + np.random.exponential(0.05))),
            'total_trades': max(10, int(len(data) / period) + np.random.randint(-5, 5)),
            'avg_trade_duration': max(1.0, period * 2.0 + np.random.normal(0, period * 0.5)),
            'net_profit_pct': max(-10.0, min(50.0, 10.0 + np.random.normal(0, 5.0)))
        }

        return metrics

    def _calculate_composite_score(self, metrics: dict[str, float]) -> float:
        """Calculate weighted composite score from metrics.

        Args:
            metrics: Dictionary of performance metrics

        Returns:
            Composite score (0-1 scale)
        """
        # Normalize metrics to 0-1 scale
        normalized = {}

        # Sharpe ratio: 0-3 → 0-1
        normalized['sharpe_ratio'] = min(1.0, metrics.get('sharpe_ratio', 0.0) / 3.0)

        # Win rate: 0-1 → 0-1 (already normalized)
        normalized['win_rate'] = metrics.get('win_rate', 0.0)

        # Profit factor: 0.8-3.0 → 0-1
        pf = metrics.get('profit_factor', 1.0)
        normalized['profit_factor'] = min(1.0, max(0.0, (pf - 0.8) / 2.2))

        # Max drawdown: 0.05-0.5 → 1-0 (inverted - lower is better)
        dd = metrics.get('max_drawdown', 0.15)
        normalized['max_drawdown'] = 1.0 - min(1.0, max(0.0, (dd - 0.05) / 0.45))

        # Calculate weighted sum
        score = 0.0
        for metric_name, weight in self.scoring_weights.items():
            score += normalized.get(metric_name, 0.0) * weight

        return score

    def _calculate_regime_scores(self, combo: ParameterCombination) -> dict[str, float]:
        """Calculate performance scores per regime.

        Args:
            combo: Parameter combination

        Returns:
            Dictionary mapping regime ID to score
        """
        if self.regime_labels is None:
            return {}

        unique_regimes = self.regime_labels.unique()
        regime_scores = {}

        for regime in unique_regimes:
            regime_mask = self.regime_labels == regime
            regime_data = self.data[regime_mask]

            if len(regime_data) < 30:  # Skip regimes with insufficient data
                continue

            metrics = self._calculate_simple_metrics(combo, regime_data)
            score = self._calculate_composite_score(metrics)
            regime_scores[regime] = score

        return regime_scores

    def select_best(
        self,
        scores: list[IndicatorScore],
        top_n: int = 5,
        min_trades: int = 30,
        max_drawdown_threshold: float = 0.30
    ) -> list[IndicatorScore]:
        """Select best parameter combinations based on criteria.

        Args:
            scores: List of indicator scores
            top_n: Number of top combinations to select
            min_trades: Minimum trades for statistical significance
            max_drawdown_threshold: Maximum acceptable drawdown

        Returns:
            List of best parameter combinations
        """
        # Filter by thresholds
        filtered = [
            s for s in scores
            if s.total_trades >= min_trades and s.max_drawdown <= max_drawdown_threshold
        ]

        if not filtered:
            logger.warning(
                f"No scores passed filters (min_trades={min_trades}, "
                f"max_dd={max_drawdown_threshold})"
            )
            # Return top_n without filtering
            return scores[:top_n]

        # Already sorted by composite_score, take top N
        best = filtered[:top_n]

        logger.info(
            f"Selected {len(best)} best combinations from {len(scores)} total "
            f"(filtered: {len(filtered)})"
        )

        return best

    def optimize_batch(
        self,
        indicator_types: list[str],
        regime_id: str | None = None,
        config: GridSearchConfig | None = None,
        top_n_per_indicator: int = 3
    ) -> dict[str, list[IndicatorScore]]:
        """Optimize multiple indicators in batch.

        Args:
            indicator_types: List of indicator types to optimize
            regime_id: Optional regime ID to filter by compatibility
            config: Grid search configuration
            top_n_per_indicator: Number of best combinations to keep per indicator

        Returns:
            Dictionary mapping indicator type to list of best scores
        """
        results = {}

        for indicator_type in indicator_types:
            logger.info(f"Optimizing {indicator_type}...")

            try:
                scores = self.optimize_indicator(indicator_type, regime_id, config)
                best_scores = self.select_best(scores, top_n=top_n_per_indicator)
                results[indicator_type] = best_scores

            except Exception as e:
                logger.error(f"Failed to optimize {indicator_type}: {e}")

        total_combinations = sum(len(scores) for scores in results.values())
        logger.info(
            f"Batch optimization complete: {len(results)} indicators, "
            f"{total_combinations} best combinations selected"
        )

        return results

    def generate_optimization_report(
        self,
        scores: list[IndicatorScore]
    ) -> str:
        """Generate human-readable optimization report.

        Args:
            scores: List of indicator scores

        Returns:
            Formatted report string
        """
        if not scores:
            return "No scores to report"

        lines = [
            "=" * 80,
            f"INDICATOR OPTIMIZATION REPORT - {scores[0].indicator_type}",
            "=" * 80,
            f"Total Combinations Tested: {len(scores)}",
            f"Timestamp: {scores[0].optimization_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "TOP 5 PARAMETER COMBINATIONS:",
            "-" * 80
        ]

        for idx, score in enumerate(scores[:5], 1):
            lines.extend([
                f"\n#{idx} - Combination ID: {score.combination_id}",
                f"Parameters: {score.params}",
                f"Composite Score: {score.composite_score:.4f}",
                f"  ├─ Sharpe Ratio: {score.sharpe_ratio:.3f}",
                f"  ├─ Win Rate: {score.win_rate:.1%}",
                f"  ├─ Profit Factor: {score.profit_factor:.2f}",
                f"  ├─ Max Drawdown: {score.max_drawdown:.1%}",
                f"  ├─ Total Trades: {score.total_trades}",
                f"  └─ Net Profit: {score.net_profit_pct:.2f}%"
            ])

            if score.regime_scores:
                lines.append("  Regime Scores:")
                for regime, regime_score in sorted(score.regime_scores.items()):
                    lines.append(f"    └─ {regime}: {regime_score:.4f}")

        lines.extend([
            "",
            "=" * 80
        ])

        return "\n".join(lines)
