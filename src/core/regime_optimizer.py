"""Regime Optimizer for Stage 1: Regime Detection Parameter Optimization.

This module implements Optuna-based optimization for regime detection parameters
using ADX, SMA, RSI, and Bollinger Bands indicators.

Regime Classification Logic:
- BULL: ADX > threshold AND Close > SMA_Fast AND SMA_Fast > SMA_Slow
- BEAR: ADX > threshold AND Close < SMA_Fast AND SMA_Fast < SMA_Slow
- SIDEWAYS: ADX < threshold AND BB_Width < percentile AND RSI between low-high

Scoring (5-component RegimeScore 0-100):
- Separability (30%): Silhouette, CH, DB cluster metrics
- Temporal Coherence (25%): switch_rate, duration, Markov self-transition
- Fidelity (25%): Hurst exponent per regime type
- Boundary Strength (10%): Feature distance at regime changes
- Coverage/Balance (10%): coverage ratio, balance penalty

Note: First 200 bars are warmup and excluded from scoring.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import optuna
import pandas as pd
from optuna.pruners import HyperbandPruner
from optuna.samplers import TPESampler
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sklearn.metrics import f1_score

from src.core.indicators.momentum import MomentumIndicators
from src.core.indicators.trend import TrendIndicators
from src.core.indicators.volatility import VolatilityIndicators
from src.core.scoring import calculate_regime_score, RegimeScoreConfig, RegimeScoreResult

logger = logging.getLogger(__name__)


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
    """ADX parameter ranges."""

    period: ParamRange
    threshold: ParamRange

    model_config = ConfigDict(frozen=True)


class SMAParamRanges(BaseModel):
    """SMA parameter ranges."""

    period: ParamRange

    model_config = ConfigDict(frozen=True)


class RSIParamRanges(BaseModel):
    """RSI parameter ranges."""

    period: ParamRange
    sideways_low: ParamRange
    sideways_high: ParamRange

    model_config = ConfigDict(frozen=True)


class BBParamRanges(BaseModel):
    """Bollinger Bands parameter ranges."""

    period: ParamRange
    std_dev: ParamRange
    width_percentile: ParamRange

    model_config = ConfigDict(frozen=True)


class AllParamRanges(BaseModel):
    """All parameter ranges for Stage 1."""

    adx: ADXParamRanges
    sma_fast: SMAParamRanges
    sma_slow: SMAParamRanges
    rsi: RSIParamRanges
    bb: BBParamRanges

    model_config = ConfigDict(frozen=True)


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
    max_trials: int = Field(default=150, ge=10, le=1000)
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
    """Optimized regime detection parameters."""

    adx_period: int
    adx_threshold: float
    sma_fast_period: int
    sma_slow_period: int
    rsi_period: int
    rsi_sideways_low: int
    rsi_sideways_high: int
    bb_period: int
    bb_std_dev: float
    bb_width_percentile: float

    model_config = ConfigDict(frozen=True)


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

    model_config = ConfigDict(frozen=False)


class RegimePeriod(BaseModel):
    """Regime period for bar index tracking."""

    regime: RegimeType
    start_idx: int = Field(ge=0)
    end_idx: int = Field(ge=0)
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    bars: int = Field(ge=1)

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
# Main Optimizer Class
# ============================================================================


@dataclass
class RegimeOptimizer:
    """Regime detection parameter optimizer using Optuna TPE.

    This class optimizes Stage 1 parameters (ADX, SMA, RSI, BB) for regime
    detection using Tree-structured Parzen Estimator with multivariate sampling.

    Attributes:
        data: OHLCV DataFrame with columns [open, high, low, close, volume]
        param_ranges: Parameter ranges for optimization
        config: Optimization configuration
        ground_truth: Optional ground truth regime labels for validation
        storage_path: Path for Optuna SQLite database
    """

    data: pd.DataFrame
    param_ranges: AllParamRanges
    config: OptimizationConfig = field(default_factory=OptimizationConfig)
    ground_truth: pd.Series | None = None
    storage_path: Path | None = None

    # Internal state
    _study: optuna.Study | None = field(default=None, init=False, repr=False)
    _best_regime_periods: list[RegimePeriod] = field(default_factory=list, init=False, repr=False)

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

    def _suggest_params(self, trial: optuna.Trial) -> RegimeParams:
        """Suggest parameters for trial.

        Args:
            trial: Optuna trial

        Returns:
            RegimeParams with suggested values
        """
        # ADX
        adx_period = trial.suggest_int(
            "adx_period",
            int(self.param_ranges.adx.period.min),
            int(self.param_ranges.adx.period.max),
            step=int(self.param_ranges.adx.period.step),
        )
        adx_threshold = trial.suggest_float(
            "adx_threshold",
            float(self.param_ranges.adx.threshold.min),
            float(self.param_ranges.adx.threshold.max),
            step=float(self.param_ranges.adx.threshold.step),
        )

        # SMA Fast
        sma_fast_period = trial.suggest_int(
            "sma_fast_period",
            int(self.param_ranges.sma_fast.period.min),
            int(self.param_ranges.sma_fast.period.max),
            step=int(self.param_ranges.sma_fast.period.step),
        )

        # SMA Slow (must be > fast)
        sma_slow_min = max(int(self.param_ranges.sma_slow.period.min), sma_fast_period + 1)
        sma_slow_period = trial.suggest_int(
            "sma_slow_period",
            sma_slow_min,
            int(self.param_ranges.sma_slow.period.max),
            step=int(self.param_ranges.sma_slow.period.step),
        )

        # RSI
        rsi_period = trial.suggest_int(
            "rsi_period",
            int(self.param_ranges.rsi.period.min),
            int(self.param_ranges.rsi.period.max),
            step=int(self.param_ranges.rsi.period.step),
        )
        rsi_sideways_low = trial.suggest_int(
            "rsi_sideways_low",
            int(self.param_ranges.rsi.sideways_low.min),
            int(self.param_ranges.rsi.sideways_low.max),
            step=int(self.param_ranges.rsi.sideways_low.step),
        )
        rsi_sideways_high = trial.suggest_int(
            "rsi_sideways_high",
            int(self.param_ranges.rsi.sideways_high.min),
            int(self.param_ranges.rsi.sideways_high.max),
            step=int(self.param_ranges.rsi.sideways_high.step),
        )

        # Ensure RSI high > low
        if rsi_sideways_high <= rsi_sideways_low:
            rsi_sideways_high = rsi_sideways_low + 5

        # Bollinger Bands
        bb_period = trial.suggest_int(
            "bb_period",
            int(self.param_ranges.bb.period.min),
            int(self.param_ranges.bb.period.max),
            step=int(self.param_ranges.bb.period.step),
        )
        bb_std_dev = trial.suggest_float(
            "bb_std_dev",
            float(self.param_ranges.bb.std_dev.min),
            float(self.param_ranges.bb.std_dev.max),
            step=float(self.param_ranges.bb.std_dev.step),
        )
        bb_width_percentile = trial.suggest_float(
            "bb_width_percentile",
            float(self.param_ranges.bb.width_percentile.min),
            float(self.param_ranges.bb.width_percentile.max),
            step=float(self.param_ranges.bb.width_percentile.step),
        )

        return RegimeParams(
            adx_period=adx_period,
            adx_threshold=adx_threshold,
            sma_fast_period=sma_fast_period,
            sma_slow_period=sma_slow_period,
            rsi_period=rsi_period,
            rsi_sideways_low=rsi_sideways_low,
            rsi_sideways_high=rsi_sideways_high,
            bb_period=bb_period,
            bb_std_dev=bb_std_dev,
            bb_width_percentile=bb_width_percentile,
        )

    def _calculate_indicators(self, params: RegimeParams) -> dict[str, pd.Series]:
        """Calculate all required indicators.

        Args:
            params: Regime parameters

        Returns:
            Dictionary of indicator values
        """
        indicators = {}

        # ADX
        adx_result = TrendIndicators.calculate_adx(
            self.data, {"period": params.adx_period}, use_talib=True
        )
        indicators["adx"] = adx_result.values

        # SMA Fast
        sma_fast_result = TrendIndicators.calculate_sma(
            self.data, {"period": params.sma_fast_period, "price": "close"}, use_talib=True
        )
        indicators["sma_fast"] = sma_fast_result.values

        # SMA Slow
        sma_slow_result = TrendIndicators.calculate_sma(
            self.data, {"period": params.sma_slow_period, "price": "close"}, use_talib=True
        )
        indicators["sma_slow"] = sma_slow_result.values

        # RSI
        rsi_result = MomentumIndicators.calculate_rsi(
            self.data, {"period": params.rsi_period}, use_talib=True
        )
        indicators["rsi"] = rsi_result.values

        # Bollinger Bands
        bb_result = VolatilityIndicators.calculate_bb(
            self.data, {"period": params.bb_period, "std_dev": params.bb_std_dev}, use_talib=True
        )
        indicators["bb_width"] = bb_result.values["bandwidth"]

        return indicators

    def _classify_regimes(
        self, params: RegimeParams, indicators: dict[str, pd.Series]
    ) -> pd.Series:
        """Classify regimes based on parameters and indicators.

        Classification Logic:
        - BULL: ADX > threshold AND Close > SMA_Fast AND SMA_Fast > SMA_Slow
        - BEAR: ADX > threshold AND Close < SMA_Fast AND SMA_Fast < SMA_Slow
        - SIDEWAYS: ADX < threshold AND BB_Width < percentile AND RSI between low-high

        Args:
            params: Regime parameters
            indicators: Dictionary of indicator values

        Returns:
            Series of regime classifications
        """
        close = self.data["close"]
        adx = indicators["adx"]
        sma_fast = indicators["sma_fast"]
        sma_slow = indicators["sma_slow"]
        rsi = indicators["rsi"]
        bb_width = indicators["bb_width"]

        # Calculate BB width percentile threshold
        bb_width_threshold = bb_width.quantile(params.bb_width_percentile / 100.0)

        # Initialize regime array
        regimes = pd.Series(RegimeType.SIDEWAYS.value, index=self.data.index)

        # BULL: ADX > threshold AND Close > SMA_Fast AND SMA_Fast > SMA_Slow
        bull_mask = (adx > params.adx_threshold) & (close > sma_fast) & (sma_fast > sma_slow)
        regimes[bull_mask] = RegimeType.BULL.value

        # BEAR: ADX > threshold AND Close < SMA_Fast AND SMA_Fast < SMA_Slow
        bear_mask = (adx > params.adx_threshold) & (close < sma_fast) & (sma_fast < sma_slow)
        regimes[bear_mask] = RegimeType.BEAR.value

        # SIDEWAYS: ADX < threshold AND BB_Width < percentile AND RSI between low-high
        sideways_mask = (
            (adx < params.adx_threshold)
            & (bb_width < bb_width_threshold)
            & (rsi >= params.rsi_sideways_low)
            & (rsi <= params.rsi_sideways_high)
        )
        regimes[sideways_mask] = RegimeType.SIDEWAYS.value

        return regimes

    def _calculate_metrics(self, regimes: pd.Series, params: RegimeParams) -> RegimeMetrics:
        """Calculate performance metrics for regime classification.

        Args:
            regimes: Classified regimes
            params: Parameters used

        Returns:
            RegimeMetrics with all metrics
        """
        # Count bars per regime
        regime_counts = regimes.value_counts()
        bull_bars = regime_counts.get(RegimeType.BULL.value, 0)
        bear_bars = regime_counts.get(RegimeType.BEAR.value, 0)
        sideways_bars = regime_counts.get(RegimeType.SIDEWAYS.value, 0)
        total_bars = len(regimes)

        # Calculate regime switches
        switches = (regimes != regimes.shift(1)).sum()

        # Calculate average duration
        regime_changes = regimes != regimes.shift(1)
        regime_ids = regime_changes.cumsum()
        regime_lengths = regime_ids.value_counts()
        avg_duration = regime_lengths.mean() if len(regime_lengths) > 0 else 0.0

        # Calculate stability (fewer switches = more stable)
        stability_score = max(0.0, 1.0 - (switches / total_bars))

        # Calculate coverage (how many bars are classified)
        coverage = 1.0  # All bars are classified

        # Calculate F1 scores (if ground truth available)
        if self.ground_truth is not None:
            f1_bull = f1_score(
                self.ground_truth == RegimeType.BULL.value,
                regimes == RegimeType.BULL.value,
                zero_division=0.0,
            )
            f1_bear = f1_score(
                self.ground_truth == RegimeType.BEAR.value,
                regimes == RegimeType.BEAR.value,
                zero_division=0.0,
            )
            f1_sideways = f1_score(
                self.ground_truth == RegimeType.SIDEWAYS.value,
                regimes == RegimeType.SIDEWAYS.value,
                zero_division=0.0,
            )
        else:
            # Use balanced distribution as proxy when no ground truth
            ideal_dist = 1.0 / 3.0
            bull_dist = bull_bars / total_bars
            bear_dist = bear_bars / total_bars
            sideways_dist = sideways_bars / total_bars

            f1_bull = 1.0 - abs(bull_dist - ideal_dist)
            f1_bear = 1.0 - abs(bear_dist - ideal_dist)
            f1_sideways = 1.0 - abs(sideways_dist - ideal_dist)

        return RegimeMetrics(
            regime_count=len(regime_counts),
            avg_duration_bars=float(avg_duration),
            switch_count=int(switches),
            stability_score=float(stability_score),
            coverage=float(coverage),
            f1_bull=float(f1_bull),
            f1_bear=float(f1_bear),
            f1_sideways=float(f1_sideways),
            bull_bars=int(bull_bars),
            bear_bars=int(bear_bars),
            sideways_bars=int(sideways_bars),
        )

    def _calculate_composite_score(self, metrics: RegimeMetrics) -> float:
        """Calculate composite score from metrics.

        Weights:
        - F1-Bull: 25%
        - F1-Bear: 30%
        - F1-Sideways: 20%
        - Stability: 25%

        Args:
            metrics: Regime metrics

        Returns:
            Composite score (0-100)
        """
        score = (
            metrics.f1_bull * 0.25
            + metrics.f1_bear * 0.30
            + metrics.f1_sideways * 0.20
            + metrics.stability_score * 0.25
        ) * 100.0

        return min(100.0, max(0.0, score))

    def _extract_regime_periods(self, regimes: pd.Series) -> list[RegimePeriod]:
        """Extract regime periods with bar indices.

        Args:
            regimes: Classified regimes

        Returns:
            List of regime periods
        """
        periods = []

        if len(regimes) == 0:
            return periods

        current_regime = regimes.iloc[0]
        start_idx = 0

        for i in range(1, len(regimes)):
            if regimes.iloc[i] != current_regime:
                # End of current regime
                end_idx = i - 1

                # Get timestamps if index is datetime
                start_ts = None
                end_ts = None
                if isinstance(self.data.index, pd.DatetimeIndex):
                    start_ts = self.data.index[start_idx].to_pydatetime()
                    end_ts = self.data.index[end_idx].to_pydatetime()

                periods.append(
                    RegimePeriod(
                        regime=RegimeType(current_regime),
                        start_idx=start_idx,
                        end_idx=end_idx,
                        start_timestamp=start_ts,
                        end_timestamp=end_ts,
                        bars=end_idx - start_idx + 1,
                    )
                )

                # Start new regime
                current_regime = regimes.iloc[i]
                start_idx = i

        # Add final regime
        end_idx = len(regimes) - 1
        start_ts = None
        end_ts = None
        if isinstance(self.data.index, pd.DatetimeIndex):
            start_ts = self.data.index[start_idx].to_pydatetime()
            end_ts = self.data.index[end_idx].to_pydatetime()

        periods.append(
            RegimePeriod(
                regime=RegimeType(current_regime),
                start_idx=start_idx,
                end_idx=end_idx,
                start_timestamp=start_ts,
                end_timestamp=end_ts,
                bars=end_idx - start_idx + 1,
            )
        )

        return periods

    def _objective(self, trial: optuna.Trial) -> float:
        """Optimization objective function using 5-component RegimeScore.

        Args:
            trial: Optuna trial

        Returns:
            RegimeScore (0-100) to maximize
        """
        try:
            # Suggest parameters
            params = self._suggest_params(trial)

            # Calculate indicators
            indicators = self._calculate_indicators(params)

            # Classify regimes
            regimes = self._classify_regimes(params, indicators)

            # Convert regimes to Series for scoring
            regimes_series = pd.Series(regimes, index=self.data.index)

            # Calculate new 5-component RegimeScore
            # Adaptive warmup/lookback: Scale with data size
            data_len = len(self.data)

            # Warmup: Max 10% of data, capped at 200
            warmup_bars = min(200, max(50, data_len // 10))

            # Feature lookback: Max of indicator periods, but capped to leave enough data
            max_indicator_period = max(
                params.adx_period,
                params.sma_slow_period,
                params.rsi_period,
                params.bb_period,
            )
            # Cap lookback to leave at least 60% of data for scoring
            max_feature_lookback = min(max_indicator_period, data_len // 4)

            # Log first trial for debugging
            if trial.number == 0:
                logger.info(
                    f"Trial 0 config: data_len={data_len}, warmup={warmup_bars}, "
                    f"lookback={max_feature_lookback}, max_indicator={max_indicator_period}"
                )

            score_config = RegimeScoreConfig(
                warmup_bars=warmup_bars,
                max_feature_lookback=max_feature_lookback,
                # Relax gates for small datasets
                min_segments=max(3, data_len // 200),  # Reduced: 3 segments per 200 bars
                min_avg_duration=3,  # Reduced from 5
                max_switch_rate_per_1000=80,  # Relaxed from 60
                min_unique_labels=2,  # Must have at least 2 regimes
                min_bars_for_scoring=max(30, data_len // 10),  # Scale with data size
            )
            score_result = calculate_regime_score(
                data=self.data,
                regimes=regimes_series,
                config=score_config,
            )

            # If gates failed, log details and return 0
            if not score_result.gates_passed:
                # Use INFO level to ensure visibility
                logger.info(
                    f"[GATE FAIL] Trial {trial.number}: {score_result.gate_failures} | "
                    f"bars_scored={score_result.n_bars_scored}, excluded={score_result.n_bars_excluded}, "
                    f"labels={score_result.unique_labels}"
                )
                return 0.0

            score = score_result.total_score

            # Log successful scoring for first few trials
            if trial.number < 3:
                logger.info(
                    f"[SCORE OK] Trial {trial.number}: total={score:.1f} | "
                    f"sep={score_result.separability.normalized:.2f}, "
                    f"coh={score_result.coherence.normalized:.2f}, "
                    f"fid={score_result.fidelity.normalized:.2f}, "
                    f"bnd={score_result.boundary.normalized:.2f}, "
                    f"cov={score_result.coverage.normalized:.2f}"
                )

            # Store score components for analysis
            trial.set_user_attr("separability", score_result.separability.normalized)
            trial.set_user_attr("coherence", score_result.coherence.normalized)
            trial.set_user_attr("fidelity", score_result.fidelity.normalized)
            trial.set_user_attr("boundary", score_result.boundary.normalized)
            trial.set_user_attr("coverage", score_result.coverage.normalized)

            # Report intermediate result for pruning
            trial.report(score, step=1)

            # Check if trial should be pruned
            if trial.should_prune():
                raise optuna.TrialPruned()

            return score

        except optuna.TrialPruned:
            raise
        except Exception as e:
            logger.error(f"Trial {trial.number} failed: {e}", exc_info=True)
            return 0.0

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
        logger.info("Starting regime optimization")

        # Create study
        self._study = self._create_study(study_name)

        # Determine number of trials
        if n_trials is None:
            n_trials = self.config.max_trials

        # Run optimization
        start_time = datetime.utcnow()
        logger.info(f"Running {n_trials} trials with {self.config.method}")

        self._study.optimize(
            self._objective,
            n_trials=n_trials,
            n_jobs=self.config.n_jobs,
            callbacks=callbacks,
            show_progress_bar=True,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Optimization completed in {duration:.2f}s")

        # Extract results
        results = self._extract_results()

        # Store best regime periods
        if results:
            best_params = results[0].params
            indicators = self._calculate_indicators(best_params)
            regimes = self._classify_regimes(best_params, indicators)
            self._best_regime_periods = self._extract_regime_periods(regimes)

        logger.info(f"Best score: {results[0].score:.2f}" if results else "No results")

        return results

    def _extract_results(self) -> list[OptimizationResult]:
        """Extract results from study.

        Returns:
            List of optimization results sorted by score
        """
        if self._study is None:
            return []

        results = []

        for rank, trial in enumerate(
            sorted(self._study.trials, key=lambda t: t.value or 0.0, reverse=True), start=1
        ):
            if trial.value is None:
                continue

            # Extract params
            params = RegimeParams(
                adx_period=trial.params["adx_period"],
                adx_threshold=trial.params["adx_threshold"],
                sma_fast_period=trial.params["sma_fast_period"],
                sma_slow_period=trial.params["sma_slow_period"],
                rsi_period=trial.params["rsi_period"],
                rsi_sideways_low=trial.params["rsi_sideways_low"],
                rsi_sideways_high=trial.params["rsi_sideways_high"],
                bb_period=trial.params["bb_period"],
                bb_std_dev=trial.params["bb_std_dev"],
                bb_width_percentile=trial.params["bb_width_percentile"],
            )

            # Recalculate metrics for this trial
            indicators = self._calculate_indicators(params)
            regimes = self._classify_regimes(params, indicators)
            metrics = self._calculate_metrics(regimes, params)

            # Extract score components from user_attrs (saved during optimization)
            separability = trial.user_attrs.get("separability", 0.0)
            coherence = trial.user_attrs.get("coherence", 0.0)
            fidelity = trial.user_attrs.get("fidelity", 0.0)
            boundary = trial.user_attrs.get("boundary", 0.0)
            coverage_comp = trial.user_attrs.get("coverage", 0.0)

            # Create new metrics dict with score components
            metrics_dict = metrics.model_dump()
            metrics_dict.update({
                "separability": separability,
                "coherence": coherence,
                "fidelity": fidelity,
                "boundary": boundary,
                "coverage_score": coverage_comp,
            })
            metrics = RegimeMetrics(**metrics_dict)

            results.append(
                OptimizationResult(
                    rank=rank,
                    score=trial.value,
                    params=params,
                    metrics=metrics,
                    timestamp=trial.datetime_complete or datetime.utcnow(),
                )
            )

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
                    "params": r.params.model_dump(),
                    "metrics": r.metrics.model_dump(),
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in results
            ],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")

        logger.info(f"Exported {len(results)} results to {output_path}")
