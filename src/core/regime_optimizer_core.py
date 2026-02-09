"""Regime Optimizer Core - Public API & Main Orchestration Class.

This module contains the public API for RegimeOptimizer, including:
- All Pydantic models (ParamRange, RegimeParams, OptimizationResult, etc.)
- All Enums (RegimeType, OptimizationMode, etc.)
- RegimeOptimizer main class (orchestration only)

For implementation details, see:
- regime_optimizer_calculations.py: Calculation algorithms
- regime_optimizer_utils.py: Utility functions & JSON support
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import optuna
import pandas as pd
from optuna.pruners import HyperbandPruner
from optuna.samplers import TPESampler
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class RegimeType(str, Enum):
    """Regime types for classification."""

    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"


class OptimizationMode(str, Enum):
    """Optimization execution modes."""

    QUICK = "quick"  # 50 trials
    STANDARD = "standard"  # 150 trials
    THOROUGH = "thorough"  # 300 trials
    EXHAUSTIVE = "exhaustive"  # 500 trials


class OptimizationMethod(str, Enum):
    """Optimization methods."""

    GRID_SEARCH = "grid_search"
    TPE = "tpe"
    TPE_MULTIVARIATE = "tpe_multivariate"


class PrunerType(str, Enum):
    """Early stopping pruner types."""

    MEDIAN = "median"
    SUCCESSIVE_HALVING = "successive_halving"
    HYPERBAND = "hyperband"


# ============================================================================
# Pydantic Models for Configuration and Results
# ============================================================================


class ParamRange(BaseModel):
    """Parameter range for optimization."""

    min: int | float
    max: int | float
    step: int | float = Field(default=1)

    model_config = ConfigDict(frozen=True)


class ADXParamRanges(BaseModel):
    """ADX parameter ranges for trend strength and direction detection."""

    period: ParamRange
    # Simple mode (tests): single threshold
    threshold: ParamRange | None = None
    # Original mode: trending / weak / di-diff
    trending_threshold: ParamRange | None = None  # ADX above this = trending market
    weak_threshold: ParamRange | None = None  # ADX below this = ranging market
    di_diff_threshold: ParamRange | None = None  # Minimum DI+ - DI- difference for direction

    model_config = ConfigDict(frozen=False)

    @model_validator(mode="after")
    def _ensure_thresholds(self) -> "ADXParamRanges":
        """Backfill thresholds for compatibility with test fixtures."""
        # If only a single threshold is provided, derive trending/weak defaults
        if self.threshold and not self.trending_threshold:
            self.trending_threshold = self.threshold
        if self.threshold and not self.weak_threshold:
            # derive weak threshold slightly below main threshold
            self.weak_threshold = ParamRange(
                min=self.threshold.min * 0.8,
                max=self.threshold.max * 0.8,
                step=self.threshold.step,
            )
        # di_diff optional; default later
        return self


class RSIParamRanges(BaseModel):
    """RSI parameter ranges."""

    period: ParamRange
    # Original fields
    strong_bull: ParamRange | None = None  # RSI above this confirms bullish direction
    strong_bear: ParamRange | None = None  # RSI below this confirms bearish direction
    # Simple mode (tests)
    sideways_low: ParamRange | None = None
    sideways_high: ParamRange | None = None

    model_config = ConfigDict(frozen=False)


class ATRParamRanges(BaseModel):
    """ATR parameter ranges for volatility-based moves."""

    period: ParamRange
    strong_move_pct: ParamRange  # Price move % to detect strong momentum
    extreme_move_pct: ParamRange  # Price move % to override ADX

    model_config = ConfigDict(frozen=True)


class SMAParamRanges(BaseModel):
    """SMA parameter ranges (simple mode)."""

    period: ParamRange

    model_config = ConfigDict(frozen=True)


class BBParamRanges(BaseModel):
    """Bollinger Band parameter ranges (simple mode)."""

    period: ParamRange
    std_dev: ParamRange
    width_percentile: ParamRange

    model_config = ConfigDict(frozen=True)


class AllParamRanges(BaseModel):
    """All parameter ranges for Stage 1 (ADX/DI-based regime detection)."""

    adx: ADXParamRanges
    rsi: RSIParamRanges
    atr: ATRParamRanges | None = None
    # Simple-mode additions
    sma_fast: SMAParamRanges | None = None
    sma_slow: SMAParamRanges | None = None
    bb: BBParamRanges | None = None

    model_config = ConfigDict(frozen=False)


class EarlyStoppingConfig(BaseModel):
    """Early stopping configuration."""

    enabled: bool = True
    pruner: PrunerType = PrunerType.HYPERBAND
    min_fidelity: float = 0.1
    reduction_factor: int = 3

    model_config = ConfigDict(frozen=True)


class OptimizationConfig(BaseModel):
    """Optimization configuration."""

    mode: OptimizationMode = OptimizationMode.STANDARD
    method: OptimizationMethod = OptimizationMethod.TPE_MULTIVARIATE
    max_trials: int = Field(default=150, ge=5, le=1000)
    n_startup_trials: int = Field(default=20, ge=5)
    early_stopping: EarlyStoppingConfig = Field(default_factory=EarlyStoppingConfig)
    n_jobs: int = -1
    storage: str | None = None
    seed: int = 42

    model_config = ConfigDict(frozen=True)

    @field_validator("max_trials")
    @classmethod
    def validate_max_trials(cls, v: int, info) -> int:
        """Validate max_trials based on mode."""
        if "mode" in info.data:
            mode = info.data["mode"]
            mode_trials = {
                OptimizationMode.QUICK: 50,
                OptimizationMode.STANDARD: 150,
                OptimizationMode.THOROUGH: 300,
                OptimizationMode.EXHAUSTIVE: 500,
            }
            expected = mode_trials.get(mode, 150)
            if v != expected:
                logger.warning(
                    f"max_trials={v} doesn't match mode={mode} "
                    f"(expected {expected}). Using provided value."
                )
        return v


class RegimeParams(BaseModel):
    """Optimized regime detection parameters (ADX/DI-based like original)."""

    # ADX parameters
    adx_period: int
    adx_threshold: float | None = None  # Simple mode threshold
    adx_trending_threshold: float | None = None  # ADX >= this = trending market
    adx_weak_threshold: float | None = None  # ADX < this = ranging/sideways market
    di_diff_threshold: float | None = None  # Minimum |DI+ - DI-| for direction confirmation

    # SMA parameters (simple mode)
    sma_fast_period: int | None = None
    sma_slow_period: int | None = None

    # RSI parameters
    rsi_period: int
    rsi_sideways_low: float | None = None
    rsi_sideways_high: float | None = None
    rsi_strong_bull: float | None = None  # RSI > this confirms bullish direction
    rsi_strong_bear: float | None = None  # RSI < this confirms bearish direction

    # Bollinger Bands (simple mode)
    bb_period: int | None = None
    bb_std_dev: float | None = None
    bb_width_percentile: float | None = None

    # ATR/Momentum parameters (for strong move detection)
    atr_period: int | None = None
    strong_move_pct: float | None = None  # Price move % to detect strong momentum
    extreme_move_pct: float | None = None  # Price move % to override ADX (fast crashes/rallies)

    model_config = ConfigDict(frozen=False)

    @model_validator(mode="after")
    def _fill_thresholds(self) -> "RegimeParams":
        """Fill backward-compatible threshold fields."""
        if self.adx_trending_threshold is None and self.adx_threshold is not None:
            self.adx_trending_threshold = self.adx_threshold
        if self.adx_threshold is None and self.adx_trending_threshold is not None:
            self.adx_threshold = self.adx_trending_threshold
        if self.adx_weak_threshold is None and self.adx_trending_threshold is not None:
            # 5-point cushion below trending threshold
            self.adx_weak_threshold = max(self.adx_trending_threshold - 5.0, 0.0)
        if self.di_diff_threshold is None:
            self.di_diff_threshold = 0.0
        return self


class RegimeMetrics(BaseModel):
    """Metrics for a regime optimization result."""

    regime_count: int
    avg_duration_bars: float
    switch_count: int
    stability_score: float
    coverage: float
    f1_bull: float = Field(ge=0.0, le=1.0)
    f1_bear: float = Field(ge=0.0, le=1.0)
    f1_sideways: float = Field(ge=0.0, le=1.0)
    bull_bars: int
    bear_bars: int
    sideways_bars: int

    # RegimeScore components (5-component score)
    separability: float = Field(default=0.0, ge=0.0, le=1.0)
    coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    fidelity: float = Field(default=0.0, ge=0.0, le=1.0)
    boundary: float = Field(default=0.0, ge=0.0, le=1.0)
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)  # Renamed to avoid conflict

    model_config = ConfigDict(frozen=True)


class OptimizationResult(BaseModel):
    """Single optimization trial result."""

    rank: int = Field(ge=1)
    score: float = Field(ge=0.0, le=100.0)
    selected: bool = False
    exported: bool = False
    params: RegimeParams
    metrics: RegimeMetrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # JSON params for JSON mode (e.g., "DIRECTION_CHANDELIER.lookback": 22)
    json_params: dict[str, float | int] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=False)


class RegimePeriod(BaseModel):
    """Regime period for bar index tracking."""

    regime: str  # Regime ID (e.g., "BULL", "BULL_ENTRY", "SIDEWAYS")
    start_idx: int = Field(ge=0)
    end_idx: int = Field(ge=0)
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    bars: int = Field(ge=1)
    # Base regime type for color coding (inferred from regime ID)
    base_type: str | None = None  # "BULL", "BEAR", or "SIDEWAYS"

    @field_validator("bars")
    @classmethod
    def validate_bars(cls, v: int, info) -> int:
        """Validate bars matches indices."""
        if "start_idx" in info.data and "end_idx" in info.data:
            expected = info.data["end_idx"] - info.data["start_idx"] + 1
            if v != expected:
                raise ValueError(f"bars={v} doesn't match indices (expected {expected})")
        return v

    model_config = ConfigDict(frozen=True)


# ============================================================================
# Main Optimizer Class (Orchestration Only)
# ============================================================================


@dataclass
class RegimeOptimizer:
    """Regime detection parameter optimizer using Optuna TPE.

    This class optimizes Stage 1 parameters (ADX, SMA, RSI, BB) for regime
    detection using Tree-structured Parzen Estimator with multivariate sampling.

    Supports two modes:
    1. Legacy mode: Uses hardcoded 3-regime model (BULL, BEAR, SIDEWAYS) with global thresholds
    2. JSON mode: Uses v2.0 JSON config with N regimes and per-regime thresholds

    Attributes:
        data: OHLCV DataFrame with columns [open, high, low, close, volume]
        param_ranges: Parameter ranges for optimization
        config: Optimization configuration
        ground_truth: Optional ground truth regime labels for validation
        storage_path: Path for Optuna SQLite database
        json_config: Optional v2.0 JSON config for per-regime threshold evaluation
    """

    data: pd.DataFrame
    param_ranges: AllParamRanges
    config: OptimizationConfig = field(default_factory=OptimizationConfig)
    ground_truth: pd.Series | None = None
    storage_path: Path | None = None
    json_config: dict | None = None  # v2.0 JSON config for per-regime thresholds

    # Internal state
    _study: optuna.Study | None = field(default=None, init=False, repr=False)
    _best_regime_periods: list[RegimePeriod] = field(default_factory=list, init=False, repr=False)
    _json_indicators_cache: list | None = field(default=None, init=False, repr=False)
    _json_regimes_cache: list | None = field(default=None, init=False, repr=False)
    # Dynamic type→name mapping built from JSON indicators (e.g., {'ADX': 'STRENGTH_ADX'})
    _indicator_type_map: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    # Reverse mapping: name→type (e.g., {'STRENGTH_ADX': 'ADX'})
    _indicator_name_to_type: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    # Trial-suggested parameter values for JSON mode (filled by _suggest_json_params)
    _trial_params: dict[str, float | int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        """Validate data and setup storage."""
        self._validate_data()
        self._setup_storage()

    def _validate_data(self) -> None:
        """Validate input data has required columns."""
        required_cols = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_cols if col not in self.data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        if len(self.data) < 100:
            raise ValueError(f"Insufficient data: {len(self.data)} bars (need >=100)")

        if self.ground_truth is not None:
            if len(self.ground_truth) != len(self.data):
                raise ValueError(
                    f"Ground truth length ({len(self.ground_truth)}) "
                    f"doesn't match data length ({len(self.data)})"
                )

    def _setup_storage(self) -> None:
        """Setup Optuna storage."""
        if self.storage_path is None:
            self.storage_path = Path("optuna_regime.db")

        storage_url = f"sqlite:///{self.storage_path}"
        if self.config.storage is None:
            self.config = self.config.model_copy(update={"storage": storage_url})

    def _create_study(self, study_name: str | None = None) -> optuna.Study:
        """Create Optuna study with TPE sampler and Hyperband pruner.

        Args:
            study_name: Optional study name

        Returns:
            Configured Optuna study
        """
        if study_name is None:
            study_name = f"regime_opt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # TPE Sampler with multivariate=True
        sampler = TPESampler(
            n_startup_trials=self.config.n_startup_trials,
            multivariate=True,
            seed=self.config.seed,
            warn_independent_sampling=False,  # Suppress warning for dynamic search space
        )

        # Hyperband Pruner
        pruner = None
        if self.config.early_stopping.enabled:
            if self.config.early_stopping.pruner == PrunerType.HYPERBAND:
                pruner = HyperbandPruner(
                    min_resource=1,
                    max_resource=100,
                    reduction_factor=self.config.early_stopping.reduction_factor,
                )
            # Add other pruners as needed

        study = optuna.create_study(
            study_name=study_name,
            storage=self.config.storage,
            load_if_exists=True,
            direction="maximize",
            sampler=sampler,
            pruner=pruner,
        )

        logger.info(f"Created study '{study_name}' with TPE sampler and Hyperband pruner")
        return study

    def optimize(
        self,
        study_name: str | None = None,
        n_trials: int | None = None,
        callbacks: list | None = None,
    ) -> list[OptimizationResult]:
        """Run optimization.

        Args:
            study_name: Optional study name
            n_trials: Number of trials (overrides config)
            callbacks: Optional list of callback functions for trial completion

        Returns:
            List of optimization results sorted by score
        """
        # Import calculation functions here to avoid circular imports
        from .regime_optimizer_calculations import (
            create_objective_function,
            extract_results,
            _calculate_indicators as calculate_indicators,
            _classify_regimes as classify_regimes,
            _calculate_json_indicators as calculate_json_indicators,
            _classify_regimes_json as classify_regimes_json,
        )
        from .regime_optimizer_utils import (
            extract_regime_periods,
            load_trial_params,
        )

        logger.info("Starting regime optimization")

        # Create study
        self._study = self._create_study(study_name)

        # Determine number of trials
        if n_trials is None:
            n_trials = self.config.max_trials

        # Create objective function with access to self
        objective = create_objective_function(self)

        # Run optimization
        start_time = datetime.utcnow()
        logger.info(f"Running {n_trials} trials with {self.config.method}")

        self._study.optimize(
            objective,
            n_trials=n_trials,
            n_jobs=self.config.n_jobs,
            callbacks=callbacks,
            show_progress_bar=True,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Optimization completed in {duration:.2f}s")

        # Extract results
        results = extract_results(self)

        # Store best regime periods
        if results:
            best_params = results[0].params
            if self.json_config is not None:
                # JSON mode: Reload best trial's JSON params
                if self._study and self._study.best_trial:
                    load_trial_params(self, self._study.best_trial)
                indicators = calculate_json_indicators(self, best_params)
                regimes = classify_regimes_json(self, best_params, indicators)
            else:
                # Legacy mode
                indicators = calculate_indicators(self, best_params)
                regimes = classify_regimes(self, best_params, indicators)
            self._best_regime_periods = extract_regime_periods(self, regimes)

        logger.info(f"Best score: {results[0].score:.2f}" if results else "No results")

        return results

    def get_best_regime_periods(self) -> list[RegimePeriod]:
        """Get regime periods for best parameters.

        Returns:
            List of regime periods with bar indices
        """
        return self._best_regime_periods.copy()

    def export_results(self, results: list[OptimizationResult], output_path: Path) -> None:
        """Export results to JSON file.

        Args:
            results: Optimization results
            output_path: Output file path
        """
        import json

        output_data = {
            "version": "2.0",
            "meta": {
                "stage": "regime_optimization",
                "created_at": datetime.utcnow().isoformat(),
                "total_combinations": len(results),
                "completed": len(results),
                "method": self.config.method.value,
            },
            "results": [
                {
                    "rank": r.rank,
                    "score": r.score,
                    "params": {**r.params.model_dump(), **r.json_params},  # Merge JSON params
                    "metrics": r.metrics.model_dump(),
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in results
            ],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")

        logger.info(f"Exported {len(results)} results to {output_path}")
