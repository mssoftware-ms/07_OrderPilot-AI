"""Walk-Forward Validation for Entry Optimization.

Provides robust out-of-sample validation to prevent overfitting:
- Rolling walk-forward with train/test splits
- Embargo periods to prevent lookahead bias
- Reproducible results with seed control
- Cross-fold performance metrics

Phase 4.1: Walk-Forward Validation MVP
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .objective import ObjectiveFunction, ObjectiveResult, create_objective_for_regime
from .optimizer import FastOptimizer, OptimizerConfig, OptimizationResult
from .trade_simulator import SimulationConfig, SimulationResult, TradeSimulator
from .types import AnalysisResult, EntryEvent, IndicatorSet, RegimeType

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for walk-forward validation.

    Attributes:
        n_folds: Number of walk-forward folds.
        train_ratio: Ratio of data used for training (0.6 = 60%).
        embargo_bars: Bars to skip between train/test (leakage guard).
        min_train_bars: Minimum bars required for training.
        min_test_bars: Minimum bars required for testing.
        seed: Random seed for reproducibility (None = random).
        optimizer_config: Config for FastOptimizer.
        sim_config: Config for TradeSimulator.
        require_positive_oos: Require positive OOS performance.
        max_train_test_ratio: Max ratio between train/test performance.
        track_detailed_metrics: Track per-fold detailed metrics.
    """

    n_folds: int = 3
    train_ratio: float = 0.7
    embargo_bars: int = 5  # Skip 5 bars between train/test
    min_train_bars: int = 50
    min_test_bars: int = 20
    seed: int | None = None
    optimizer_config: OptimizerConfig | None = None
    sim_config: SimulationConfig | None = None
    require_positive_oos: bool = True
    max_train_test_ratio: float = 2.0  # Max 2x better on train vs test
    track_detailed_metrics: bool = True


@dataclass
class FoldResult:
    """Result from a single validation fold.

    Attributes:
        fold_idx: Fold index (0-based).
        train_start_idx: Start index of training data.
        train_end_idx: End index of training data.
        test_start_idx: Start index of test data.
        test_end_idx: End index of test data.
        train_score: Score on training data.
        test_score: Score on test data (out-of-sample).
        train_trades: Number of trades in training.
        test_trades: Number of trades in test.
        train_win_rate: Win rate on training data.
        test_win_rate: Win rate on test data.
        train_pf: Profit factor on training.
        test_pf: Profit factor on test.
        best_set: Best indicator set from training.
        optimization_time_ms: Time for optimization.
        test_entries: Entries generated on test data.
    """

    fold_idx: int
    train_start_idx: int
    train_end_idx: int
    test_start_idx: int
    test_end_idx: int
    train_score: float = 0.0
    test_score: float = 0.0
    train_trades: int = 0
    test_trades: int = 0
    train_win_rate: float = 0.0
    test_win_rate: float = 0.0
    train_pf: float = 0.0
    test_pf: float = 0.0
    best_set: IndicatorSet | None = None
    optimization_time_ms: float = 0.0
    test_entries: list[EntryEvent] = field(default_factory=list)

    @property
    def is_overfit(self) -> bool:
        """Check if fold shows signs of overfitting."""
        if self.test_score <= 0:
            return True
        if self.train_score > 0 and self.test_score > 0:
            ratio = self.train_score / self.test_score
            return ratio > 2.0  # Train 2x better than test = overfit
        return False

    @property
    def train_test_ratio(self) -> float:
        """Ratio of train to test performance."""
        if self.test_score > 0:
            return self.train_score / self.test_score
        return float("inf")


@dataclass
class ValidationResult:
    """Aggregated results from walk-forward validation.

    Attributes:
        folds: Results from each fold.
        avg_train_score: Average training score.
        avg_test_score: Average test (OOS) score.
        avg_train_test_ratio: Average train/test ratio.
        oos_win_rate: Average out-of-sample win rate.
        oos_profit_factor: Average out-of-sample profit factor.
        total_oos_trades: Total trades across all test folds.
        is_valid: Whether validation passed all checks.
        failure_reasons: Reasons for validation failure.
        best_fold_idx: Index of best performing fold.
        best_set: Best overall indicator set.
        all_test_entries: All entries from test folds.
        total_time_ms: Total validation time.
        seed_used: Random seed that was used.
    """

    folds: list[FoldResult] = field(default_factory=list)
    avg_train_score: float = 0.0
    avg_test_score: float = 0.0
    avg_train_test_ratio: float = 0.0
    oos_win_rate: float = 0.0
    oos_profit_factor: float = 0.0
    total_oos_trades: int = 0
    is_valid: bool = False
    failure_reasons: list[str] = field(default_factory=list)
    best_fold_idx: int = -1
    best_set: IndicatorSet | None = None
    all_test_entries: list[EntryEvent] = field(default_factory=list)
    total_time_ms: float = 0.0
    seed_used: int = 0

    @classmethod
    def from_folds(
        cls,
        folds: list[FoldResult],
        config: ValidationConfig,
        seed_used: int,
        total_time_ms: float,
    ) -> ValidationResult:
        """Calculate aggregated metrics from fold results."""
        if not folds:
            return cls(
                is_valid=False,
                failure_reasons=["No folds completed"],
                seed_used=seed_used,
                total_time_ms=total_time_ms,
            )

        # Calculate averages
        avg_train = sum(f.train_score for f in folds) / len(folds)
        avg_test = sum(f.test_score for f in folds) / len(folds)

        valid_ratios = [f.train_test_ratio for f in folds if f.test_score > 0]
        avg_ratio = sum(valid_ratios) / len(valid_ratios) if valid_ratios else float("inf")

        # OOS metrics
        total_test_trades = sum(f.test_trades for f in folds)
        test_wins = sum(f.test_trades * f.test_win_rate for f in folds)
        oos_wr = test_wins / total_test_trades if total_test_trades > 0 else 0.0

        # Weighted average PF
        pf_sum = sum(f.test_pf * f.test_trades for f in folds)
        oos_pf = pf_sum / total_test_trades if total_test_trades > 0 else 0.0

        # Find best fold (by test score)
        best_idx = max(range(len(folds)), key=lambda i: folds[i].test_score)
        best_fold = folds[best_idx]

        # Collect all test entries
        all_entries = []
        for f in folds:
            all_entries.extend(f.test_entries)

        # Validation checks
        failure_reasons = []

        if config.require_positive_oos and avg_test <= 0:
            failure_reasons.append(f"Negative OOS score: {avg_test:.3f}")

        if avg_ratio > config.max_train_test_ratio:
            failure_reasons.append(
                f"High train/test ratio: {avg_ratio:.2f} > {config.max_train_test_ratio}"
            )

        overfit_folds = sum(1 for f in folds if f.is_overfit)
        if overfit_folds > len(folds) // 2:
            failure_reasons.append(f"Majority of folds overfit: {overfit_folds}/{len(folds)}")

        if total_test_trades < config.min_test_bars:
            failure_reasons.append(f"Too few OOS trades: {total_test_trades}")

        is_valid = len(failure_reasons) == 0

        return cls(
            folds=folds,
            avg_train_score=avg_train,
            avg_test_score=avg_test,
            avg_train_test_ratio=avg_ratio,
            oos_win_rate=oos_wr,
            oos_profit_factor=oos_pf,
            total_oos_trades=total_test_trades,
            is_valid=is_valid,
            failure_reasons=failure_reasons,
            best_fold_idx=best_idx,
            best_set=best_fold.best_set,
            all_test_entries=sorted(all_entries, key=lambda e: e.timestamp),
            total_time_ms=total_time_ms,
            seed_used=seed_used,
        )


class WalkForwardValidator:
    """Walk-forward validation for entry optimization.

    Implements anchored walk-forward validation:
    - Data is split into N folds
    - Each fold: train on first portion, test on remaining
    - Embargo period between train/test prevents lookahead
    - Metrics aggregated across all folds

    Example with 3 folds on 100 bars, 70% train, 5 bar embargo:
        Fold 1: Train [0:70], Embargo [70:75], Test [75:100]
        Fold 2: Train [0:47], Embargo [47:52], Test [52:75]
        Fold 3: Train [0:33], Embargo [33:38], Test [38:52]
    """

    def __init__(self, config: ValidationConfig | None = None) -> None:
        """Initialize the validator.

        Args:
            config: Validation configuration.
        """
        self.config = config or ValidationConfig()

        # Set up optimizer config
        opt_config = self.config.optimizer_config or OptimizerConfig()
        self._optimizer = FastOptimizer(opt_config)

        # Set up simulator
        sim_config = self.config.sim_config or SimulationConfig()
        self._simulator = TradeSimulator(sim_config)

    def validate(
        self,
        candles: list[dict],
        regime: RegimeType,
        features: dict[str, list[float]] | None = None,
    ) -> ValidationResult:
        """Run walk-forward validation.

        Args:
            candles: OHLCV candle data.
            regime: Detected market regime.
            features: Pre-calculated features (optional).

        Returns:
            ValidationResult with aggregated metrics.
        """
        start_time = time.perf_counter()

        # Set seed for reproducibility
        seed = self.config.seed if self.config.seed is not None else random.randint(0, 2**31)
        random.seed(seed)

        n_bars = len(candles)

        # Validate minimum data
        min_required = (
            self.config.min_train_bars
            + self.config.embargo_bars
            + self.config.min_test_bars
        )
        if n_bars < min_required:
            return ValidationResult(
                is_valid=False,
                failure_reasons=[f"Insufficient data: {n_bars} < {min_required} bars"],
                seed_used=seed,
                total_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Create fold splits
        fold_splits = self._create_fold_splits(n_bars)

        if not fold_splits:
            return ValidationResult(
                is_valid=False,
                failure_reasons=["Could not create valid fold splits"],
                seed_used=seed,
                total_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Run each fold
        folds: list[FoldResult] = []

        for fold_idx, (train_start, train_end, test_start, test_end) in enumerate(fold_splits):
            logger.debug(
                "Fold %d: train[%d:%d], test[%d:%d]",
                fold_idx,
                train_start,
                train_end,
                test_start,
                test_end,
            )

            fold_result = self._run_fold(
                fold_idx=fold_idx,
                candles=candles,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                regime=regime,
                features=features,
            )

            folds.append(fold_result)

        total_time_ms = (time.perf_counter() - start_time) * 1000

        result = ValidationResult.from_folds(
            folds=folds,
            config=self.config,
            seed_used=seed,
            total_time_ms=total_time_ms,
        )

        logger.info(
            "Walk-forward complete: %d folds, OOS=%.3f, valid=%s, time=%.1fms",
            len(folds),
            result.avg_test_score,
            result.is_valid,
            total_time_ms,
        )

        return result

    def _create_fold_splits(
        self, n_bars: int
    ) -> list[tuple[int, int, int, int]]:
        """Create train/test splits for each fold.

        Uses anchored walk-forward: train always starts at 0,
        test window slides backward from end.

        Args:
            n_bars: Total number of bars.

        Returns:
            List of (train_start, train_end, test_start, test_end) tuples.
        """
        splits = []
        embargo = self.config.embargo_bars

        # Calculate fold sizes
        # Last fold: train_ratio of data for train
        # Earlier folds: test window slides back

        for fold_idx in range(self.config.n_folds):
            # Calculate test window for this fold
            # Fold 0: test at end, fold N: test earlier
            remaining_folds = self.config.n_folds - fold_idx

            # Test window size (roughly equal across folds)
            test_size = int(n_bars * (1 - self.config.train_ratio) / remaining_folds)
            test_size = max(test_size, self.config.min_test_bars)

            # Test end for this fold
            test_end = n_bars - (fold_idx * test_size)
            test_start = test_end - test_size

            # Train ends before embargo
            train_end = test_start - embargo
            train_start = 0

            # Validate sizes
            if train_end - train_start < self.config.min_train_bars:
                logger.debug(
                    "Fold %d: insufficient train data (%d bars)",
                    fold_idx,
                    train_end - train_start,
                )
                continue

            if test_end - test_start < self.config.min_test_bars:
                logger.debug(
                    "Fold %d: insufficient test data (%d bars)",
                    fold_idx,
                    test_end - test_start,
                )
                continue

            if train_end <= train_start or test_end <= test_start:
                continue

            splits.append((train_start, train_end, test_start, test_end))

        return splits

    def _run_fold(
        self,
        fold_idx: int,
        candles: list[dict],
        train_start: int,
        train_end: int,
        test_start: int,
        test_end: int,
        regime: RegimeType,
        features: dict[str, list[float]] | None,
    ) -> FoldResult:
        """Run a single validation fold.

        Args:
            fold_idx: Fold index.
            candles: All candles.
            train_start: Training start index.
            train_end: Training end index.
            test_start: Test start index.
            test_end: Test end index.
            regime: Market regime.
            features: Pre-calculated features.

        Returns:
            FoldResult with train and test metrics.
        """
        # Extract train/test data
        train_candles = candles[train_start:train_end]
        test_candles = candles[test_start:test_end]

        # Slice features if provided
        train_features = None
        test_features = None
        if features:
            train_features = {
                k: v[train_start:train_end] for k, v in features.items()
            }
            test_features = {
                k: v[test_start:test_end] for k, v in features.items()
            }

        # Optimize on training data
        opt_start = time.perf_counter()
        opt_result = self._optimizer.optimize(
            candles=train_candles,
            regime=regime,
            features=train_features,
        )
        opt_time_ms = (time.perf_counter() - opt_start) * 1000

        if not opt_result.best_set:
            return FoldResult(
                fold_idx=fold_idx,
                train_start_idx=train_start,
                train_end_idx=train_end,
                test_start_idx=test_start,
                test_end_idx=test_end,
                optimization_time_ms=opt_time_ms,
            )

        # Evaluate on training data
        train_entries = opt_result.entries
        train_sim = self._simulator.simulate(train_entries, train_candles, train_features)
        train_obj = create_objective_for_regime(regime.value)
        train_hours = self._calc_hours(train_candles)
        train_result = train_obj.evaluate(
            train_sim,
            n_indicators=len(opt_result.best_set.indicators),
            hours_analyzed=train_hours,
        )

        # Generate entries on test data using optimized set
        test_entries = self._generate_test_entries(
            test_candles, opt_result.best_set, regime, test_features
        )

        # Evaluate on test data
        test_sim = self._simulator.simulate(test_entries, test_candles, test_features)
        test_hours = self._calc_hours(test_candles)
        test_result = train_obj.evaluate(
            test_sim,
            n_indicators=len(opt_result.best_set.indicators),
            hours_analyzed=test_hours,
        )

        return FoldResult(
            fold_idx=fold_idx,
            train_start_idx=train_start,
            train_end_idx=train_end,
            test_start_idx=test_start,
            test_end_idx=test_end,
            train_score=train_result.score if train_result.is_valid else 0.0,
            test_score=test_result.score if test_result.is_valid else 0.0,
            train_trades=train_sim.total_trades,
            test_trades=test_sim.total_trades,
            train_win_rate=train_sim.win_rate,
            test_win_rate=test_sim.win_rate,
            train_pf=train_sim.profit_factor,
            test_pf=test_sim.profit_factor,
            best_set=opt_result.best_set,
            optimization_time_ms=opt_time_ms,
            test_entries=test_entries,
        )

    def _generate_test_entries(
        self,
        candles: list[dict],
        indicator_set: IndicatorSet,
        regime: RegimeType,
        features: dict[str, list[float]] | None,
    ) -> list[EntryEvent]:
        """Generate entries on test data using optimized parameters.

        Args:
            candles: Test candles.
            indicator_set: Optimized indicator set.
            regime: Market regime.
            features: Pre-calculated features.

        Returns:
            List of entry events.
        """
        # Use optimizer's entry generation with fixed parameters
        # Create a temporary OptimizableSet from IndicatorSet
        from .indicator_families import IndicatorConfig, OptimizableSet

        # Reconstruct OptimizableSet from IndicatorSet
        indicators = []
        for ind in indicator_set.indicators:
            # Create minimal config for regeneration
            config = IndicatorConfig(
                name=ind.get("name", "Unknown"),
                param_ranges={},
                weight_range=(0.5, 0.5),
            )
            indicators.append((config, ind.get("params", {})))

        opt_set = OptimizableSet(
            indicators=indicators,
            scoring_weights={ind.get("name", ""): ind.get("weight", 0.5) for ind in indicator_set.indicators},
            postprocess_config=indicator_set.postprocess or {},
            stop_config=indicator_set.stop_config or {},
        )

        return self._optimizer._generate_entries(candles, opt_set, regime, features)

    def _calc_hours(self, candles: list[dict]) -> float:
        """Calculate hours covered by candles."""
        if len(candles) < 2:
            return 1.0
        return (candles[-1]["timestamp"] - candles[0]["timestamp"]) / 3600


def validate_with_walkforward(
    candles: list[dict],
    regime: RegimeType,
    features: dict[str, list[float]] | None = None,
    config: ValidationConfig | None = None,
) -> ValidationResult:
    """Convenience function for walk-forward validation.

    Args:
        candles: OHLCV candle data.
        regime: Detected market regime.
        features: Pre-calculated features.
        config: Validation configuration.

    Returns:
        ValidationResult with aggregated metrics.
    """
    validator = WalkForwardValidator(config)
    return validator.validate(candles, regime, features)
