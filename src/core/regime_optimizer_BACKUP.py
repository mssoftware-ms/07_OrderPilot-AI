"""Regime Optimizer for Stage 1: Regime Detection Parameter Optimization.

This module implements Optuna-based optimization for regime detection parameters
using ADX, DI+, DI-, RSI, and ATR indicators (matching original regime_engine.py logic).

Regime Classification Logic (ADX/DI-based like original):
- PRIORITY 1: Strong price moves (>strong_move_pct%) override ADX
- PRIORITY 2: Extreme moves (>extreme_move_pct%) ALWAYS override ADX
- BULL: ADX >= trending_threshold AND (DI+ - DI-) > di_diff_threshold
- BEAR: ADX >= trending_threshold AND (DI- - DI+) > di_diff_threshold
- SIDEWAYS: ADX < weak_threshold

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

import numpy as np
import optuna
import pandas as pd
from optuna.pruners import HyperbandPruner
from optuna.samplers import TPESampler
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sklearn.metrics import f1_score

# Try to import talib for DI calculations
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

# Try to import pandas_ta as fallback
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False

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
# Main Optimizer Class
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

    def _suggest_params(self, trial: optuna.Trial) -> RegimeParams:
        """Suggest parameters for trial (ADX/DI-based like original regime_engine).

        Args:
            trial: Optuna trial

        Returns:
            RegimeParams with suggested values
        """
        def suggest_from_range(name: str, rng: ParamRange, integer: bool = False):
            if integer:
                return trial.suggest_int(
                    name, int(rng.min), int(rng.max), step=max(1, int(rng.step))
                )
            return trial.suggest_float(
                name, float(rng.min), float(rng.max), step=float(rng.step)
            )

        use_simple_mode = (
            self.param_ranges.sma_fast is not None
            or self.param_ranges.sma_slow is not None
            or self.param_ranges.bb is not None
            or self.param_ranges.adx.threshold is not None
        )

        # Always choose ADX period
        adx_period = suggest_from_range("adx_period", self.param_ranges.adx.period, integer=True)

        if use_simple_mode:
            # Simple mode parameters (used by tests)
            threshold_rng = (
                self.param_ranges.adx.threshold
                or self.param_ranges.adx.trending_threshold
                or ParamRange(min=20, max=40, step=1)
            )
            adx_threshold = suggest_from_range("adx_threshold", threshold_rng, integer=False)

            # SMA periods
            sma_fast_rng = self.param_ranges.sma_fast.period if self.param_ranges.sma_fast else ParamRange(min=5, max=15, step=1)
            sma_slow_rng = self.param_ranges.sma_slow.period if self.param_ranges.sma_slow else ParamRange(min=20, max=50, step=1)
            sma_fast_period = suggest_from_range("sma_fast_period", sma_fast_rng, integer=True)
            sma_slow_period = suggest_from_range("sma_slow_period", sma_slow_rng, integer=True)

            # RSI
            rsi_period = suggest_from_range("rsi_period", self.param_ranges.rsi.period, integer=True)
            if self.param_ranges.rsi.sideways_low and self.param_ranges.rsi.sideways_high:
                rsi_sideways_low = suggest_from_range("rsi_sideways_low", self.param_ranges.rsi.sideways_low, integer=False)
                rsi_sideways_high = suggest_from_range("rsi_sideways_high", self.param_ranges.rsi.sideways_high, integer=False)
            else:
                # Derive from strong_bear/bull or fallback defaults
                low_rng = self.param_ranges.rsi.strong_bear or ParamRange(min=30, max=45, step=1)
                high_rng = self.param_ranges.rsi.strong_bull or ParamRange(min=55, max=70, step=1)
                rsi_sideways_low = suggest_from_range("rsi_sideways_low", low_rng, integer=False)
                rsi_sideways_high = suggest_from_range("rsi_sideways_high", high_rng, integer=False)

            # Bollinger Bands
            if self.param_ranges.bb:
                bb_period = suggest_from_range("bb_period", self.param_ranges.bb.period, integer=True)
                bb_std_dev = suggest_from_range("bb_std_dev", self.param_ranges.bb.std_dev, integer=False)
                bb_width_percentile = suggest_from_range("bb_width_percentile", self.param_ranges.bb.width_percentile, integer=False)
            else:
                bb_period = 20
                bb_std_dev = 2.0
                bb_width_percentile = 30.0

            atr_period = None
            strong_move_pct = None
            extreme_move_pct = None
            if self.param_ranges.atr:
                atr_period = suggest_from_range("atr_period", self.param_ranges.atr.period, integer=True)
                strong_move_pct = suggest_from_range("strong_move_pct", self.param_ranges.atr.strong_move_pct, integer=False)
                extreme_move_pct = suggest_from_range("extreme_move_pct", self.param_ranges.atr.extreme_move_pct, integer=False)

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
                atr_period=atr_period,
                strong_move_pct=strong_move_pct,
                extreme_move_pct=extreme_move_pct,
            )

        # ===== Original ADX/DI mode =====
        trending_rng = self.param_ranges.adx.trending_threshold or self.param_ranges.adx.threshold or ParamRange(min=20, max=35, step=1)
        weak_rng = self.param_ranges.adx.weak_threshold or ParamRange(min=15, max=25, step=1)
        di_rng = self.param_ranges.adx.di_diff_threshold or ParamRange(min=3, max=10, step=1)

        adx_trending_threshold = suggest_from_range("adx_trending_threshold", trending_rng, integer=False)
        adx_weak_threshold = suggest_from_range(
            "adx_weak_threshold",
            ParamRange(
                min=min(weak_rng.min, adx_trending_threshold - 1),
                max=min(weak_rng.max, adx_trending_threshold - 1),
                step=weak_rng.step,
            ),
            integer=False,
        )
        di_diff_threshold = suggest_from_range("di_diff_threshold", di_rng, integer=False)

        rsi_period = suggest_from_range("rsi_period", self.param_ranges.rsi.period, integer=True)
        rsi_strong_bull = suggest_from_range(
            "rsi_strong_bull",
            self.param_ranges.rsi.strong_bull or ParamRange(min=55, max=70, step=1),
            integer=False,
        )
        rsi_strong_bear = suggest_from_range(
            "rsi_strong_bear",
            self.param_ranges.rsi.strong_bear or ParamRange(min=30, max=45, step=1),
            integer=False,
        )

        atr_period = suggest_from_range(
            "atr_period",
            self.param_ranges.atr.period if self.param_ranges.atr else ParamRange(min=10, max=20, step=1),
            integer=True,
        )
        strong_move_pct = suggest_from_range(
            "strong_move_pct",
            self.param_ranges.atr.strong_move_pct if self.param_ranges.atr else ParamRange(min=1.0, max=2.5, step=0.1),
            integer=False,
        )
        extreme_move_pct = suggest_from_range(
            "extreme_move_pct",
            self.param_ranges.atr.extreme_move_pct if self.param_ranges.atr else ParamRange(min=2.0, max=4.0, step=0.5),
            integer=False,
        )

        return RegimeParams(
            adx_period=adx_period,
            adx_trending_threshold=adx_trending_threshold,
            adx_weak_threshold=adx_weak_threshold,
            di_diff_threshold=di_diff_threshold,
            rsi_period=rsi_period,
            rsi_strong_bull=rsi_strong_bull,
            rsi_strong_bear=rsi_strong_bear,
            atr_period=atr_period,
            strong_move_pct=strong_move_pct,
            extreme_move_pct=extreme_move_pct,
        )

    def _calculate_indicators(self, params: RegimeParams) -> dict[str, pd.Series]:
        """Calculate all required indicators for ADX/DI-based regime detection.

        Calculates:
        - ADX (trend strength)
        - DI+ and DI- (directional indicators for trend direction)
        - RSI (momentum confirmation)
        - ATR (volatility for strong move detection)
        - Price change % (for momentum override)

        Args:
            params: Regime parameters

        Returns:
            Dictionary of indicator values
        """
        indicators = {}
        high = self.data["high"]
        low = self.data["low"]
        close = self.data["close"]
        use_simple_mode = (
            params.sma_fast_period is not None
            and params.sma_slow_period is not None
            and params.adx_threshold is not None
        )

        # Calculate ADX, DI+, DI- using talib or pandas_ta
        if TALIB_AVAILABLE:
            indicators["adx"] = pd.Series(
                talib.ADX(high, low, close, timeperiod=params.adx_period),
                index=self.data.index
            )
            indicators["plus_di"] = pd.Series(
                talib.PLUS_DI(high, low, close, timeperiod=params.adx_period),
                index=self.data.index
            )
            indicators["minus_di"] = pd.Series(
                talib.MINUS_DI(high, low, close, timeperiod=params.adx_period),
                index=self.data.index
            )
        elif PANDAS_TA_AVAILABLE:
            adx_df = ta.adx(high, low, close, length=params.adx_period)
            # pandas_ta returns columns like ADX_14, DMP_14, DMN_14
            adx_col = [c for c in adx_df.columns if c.startswith("ADX_")][0]
            dmp_col = [c for c in adx_df.columns if c.startswith("DMP_")][0]
            dmn_col = [c for c in adx_df.columns if c.startswith("DMN_")][0]
            indicators["adx"] = adx_df[adx_col]
            indicators["plus_di"] = adx_df[dmp_col]
            indicators["minus_di"] = adx_df[dmn_col]
        else:
            # Fallback: simple ADX approximation (not recommended)
            logger.warning("Neither talib nor pandas_ta available. Using simplified ADX.")
            indicators["adx"] = pd.Series(25.0, index=self.data.index)  # Neutral
            indicators["plus_di"] = pd.Series(25.0, index=self.data.index)
            indicators["minus_di"] = pd.Series(25.0, index=self.data.index)

        # RSI for direction confirmation
        if PANDAS_TA_AVAILABLE:
            indicators["rsi"] = ta.rsi(close, length=params.rsi_period)
        else:
            rsi_result = MomentumIndicators.calculate_rsi(
                self.data, {"period": params.rsi_period}, use_talib=True
            )
            indicators["rsi"] = rsi_result.values

        # ATR for volatility-based strong move detection (optional in simple mode)
        if params.atr_period:
            atr_result = VolatilityIndicators.calculate_atr(
                self.data, {"period": params.atr_period}, use_talib=True
            )
            indicators["atr"] = atr_result.values
            lookback = params.atr_period
        else:
            indicators["atr"] = pd.Series(index=self.data.index, dtype=float)
            lookback = max(params.adx_period, 1)

        # Price change percentage over lookback (for strong/ extreme move detection)
        indicators["price_change_pct"] = (close - close.shift(lookback)) / close.shift(lookback) * 100

        # Simple-mode indicators
        if use_simple_mode:
            indicators["sma_fast"] = close.rolling(window=int(params.sma_fast_period)).mean()
            indicators["sma_slow"] = close.rolling(window=int(params.sma_slow_period)).mean()

            if params.bb_period and params.bb_std_dev:
                try:
                    bb = ta.bbands(close, length=int(params.bb_period), std=params.bb_std_dev)
                    lower_col = [c for c in bb.columns if c.startswith("BBL_")][0]
                    middle_col = [c for c in bb.columns if c.startswith("BBM_")][0]
                    upper_col = [c for c in bb.columns if c.startswith("BBU_")][0]
                    indicators["bb_width"] = (bb[upper_col] - bb[lower_col]) / bb[middle_col].abs() * 100
                except Exception:
                    indicators["bb_width"] = pd.Series(index=self.data.index, dtype=float)

        return indicators

    def _classify_regimes(
        self, params: RegimeParams, indicators: dict[str, pd.Series]
    ) -> pd.Series:
        """Classify regimes using either simple SMA/ADX logic (tests) or legacy ADX/DI logic."""
        use_simple_mode = (
            params.adx_threshold is not None
            and "sma_fast" in indicators
            and "sma_slow" in indicators
        )

        regimes = pd.Series(RegimeType.SIDEWAYS.value, index=self.data.index)

        if use_simple_mode:
            adx = indicators["adx"]
            sma_fast = indicators["sma_fast"]
            sma_slow = indicators["sma_slow"]
            close = self.data["close"]
            rsi = indicators["rsi"]

            bull_mask = (adx > params.adx_threshold) & (close > sma_fast) & (sma_fast > sma_slow)
            if params.rsi_sideways_high is not None:
                bull_mask &= rsi > params.rsi_sideways_high

            bear_mask = (adx > params.adx_threshold) & (close < sma_fast) & (sma_fast < sma_slow)
            if params.rsi_sideways_low is not None:
                bear_mask &= rsi < params.rsi_sideways_low

            regimes[bull_mask] = RegimeType.BULL.value
            regimes[bear_mask] = RegimeType.BEAR.value

            # Sideways if RSI inside band or BB width very low
            if params.rsi_sideways_low is not None and params.rsi_sideways_high is not None:
                sideways_mask = rsi.between(params.rsi_sideways_low, params.rsi_sideways_high, inclusive="both")
                regimes.loc[(regimes == RegimeType.SIDEWAYS.value) & sideways_mask] = RegimeType.SIDEWAYS.value

            if "bb_width" in indicators and params.bb_width_percentile:
                bb_mask = indicators["bb_width"] < params.bb_width_percentile
                regimes.loc[(regimes == RegimeType.SIDEWAYS.value) & bb_mask] = RegimeType.SIDEWAYS.value

            return regimes

        # ===== Legacy ADX/DI logic =====
        adx = indicators["adx"]
        plus_di = indicators["plus_di"]
        minus_di = indicators["minus_di"]
        rsi = indicators["rsi"]
        price_change_pct = indicators["price_change_pct"]

        # Calculate DI difference
        di_diff = plus_di - minus_di

        # ==================== PRIORITY 3: ADX/DI-based classification ====================
        # SIDEWAYS: ADX < weak_threshold (ranging/choppy market)
        sideways_mask = adx < params.adx_weak_threshold
        regimes[sideways_mask] = RegimeType.SIDEWAYS.value

        # BULL: ADX >= trending AND DI+ > DI- by threshold
        bull_di_mask = (adx >= params.adx_trending_threshold) & (di_diff > params.di_diff_threshold)
        regimes[bull_di_mask] = RegimeType.BULL.value

        # BEAR: ADX >= trending AND DI- > DI+ by threshold
        bear_di_mask = (adx >= params.adx_trending_threshold) & (di_diff < -params.di_diff_threshold)
        regimes[bear_di_mask] = RegimeType.BEAR.value

        # Borderline ADX (between weak and trending): use RSI for direction
        borderline_mask = (adx >= params.adx_weak_threshold) & (adx < params.adx_trending_threshold)

        # RSI confirmation for borderline cases
        bull_rsi_mask = borderline_mask & (rsi > (params.rsi_strong_bull or 50))
        regimes[bull_rsi_mask] = RegimeType.BULL.value

        bear_rsi_mask = borderline_mask & (rsi < (params.rsi_strong_bear or 50))
        regimes[bear_rsi_mask] = RegimeType.BEAR.value

        # ==================== PRIORITY 2: Strong price moves ====================
        # Strong bullish move with weak ADX -> still BULL
        strong_move_pct = params.strong_move_pct or 0.0
        strong_bull_move = (price_change_pct >= strong_move_pct) & (adx < params.adx_trending_threshold)
        regimes[strong_bull_move] = RegimeType.BULL.value

        # Strong bearish move with weak ADX -> still BEAR
        strong_bear_move = (price_change_pct <= -strong_move_pct) & (adx < params.adx_trending_threshold)
        regimes[strong_bear_move] = RegimeType.BEAR.value

        # ==================== PRIORITY 1: Extreme price moves (ALWAYS override) ====================
        # Extreme bullish move -> ALWAYS BULL regardless of ADX
        extreme_move_pct = params.extreme_move_pct or strong_move_pct
        extreme_bull_move = price_change_pct >= extreme_move_pct
        regimes[extreme_bull_move] = RegimeType.BULL.value

        # Extreme bearish move -> ALWAYS BEAR regardless of ADX
        extreme_bear_move = price_change_pct <= -extreme_move_pct
        regimes[extreme_bear_move] = RegimeType.BEAR.value

        return regimes

    def _build_indicator_type_maps(self) -> None:
        """Build dynamic type→name and name→type mappings from JSON indicators.

        This enables flexible indicator usage without hardcoded mappings.
        """
        if not self._json_indicators_cache:
            return

        self._indicator_type_map.clear()
        self._indicator_name_to_type.clear()

        for ind in self._json_indicators_cache:
            name = ind['name']
            ind_type = ind['type'].upper()

            # Store both mappings
            self._indicator_type_map[ind_type] = name
            self._indicator_name_to_type[name] = ind_type

        logger.debug(
            f"Built indicator type maps: {len(self._indicator_type_map)} types, "
            f"mappings: {self._indicator_type_map}"
        )

    def _calculate_chandelier_stop(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        lookback: int = 22,
        atr_period: int = 22,
        multiplier: float = 3.0,
    ) -> dict[str, pd.Series]:
        """Calculate Chandelier Stop (pipCharlie style).

        Chandelier Stop is an ATR-based trailing stop indicator:
        - Long Stop: highest(lookback) - multiplier * ATR
        - Short Stop: lowest(lookback) + multiplier * ATR
        - Direction: 1 (bullish) when close > short_stop, -1 (bearish) when close < long_stop

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            lookback: Lookback period for highest/lowest
            atr_period: ATR calculation period
            multiplier: ATR multiplier

        Returns:
            Dictionary with 'long_stop', 'short_stop', 'direction', 'color_change'
        """
        # Calculate ATR
        if TALIB_AVAILABLE:
            atr = pd.Series(
                talib.ATR(high, low, close, timeperiod=atr_period),
                index=close.index
            )
        elif PANDAS_TA_AVAILABLE:
            atr = ta.atr(high, low, close, length=atr_period)
        else:
            # Simple ATR approximation
            tr = pd.concat([
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs()
            ], axis=1).max(axis=1)
            atr = tr.rolling(window=atr_period).mean()

        # Calculate highest high and lowest low
        highest_high = high.rolling(window=lookback).max()
        lowest_low = low.rolling(window=lookback).min()

        # Calculate stops
        long_stop = highest_high - multiplier * atr
        short_stop = lowest_low + multiplier * atr

        # Determine direction: 1 = bullish, -1 = bearish
        direction = pd.Series(0, index=close.index)
        direction[close > short_stop] = 1
        direction[close < long_stop] = -1

        # Forward fill for bars where neither condition is met
        direction = direction.replace(0, np.nan).ffill().fillna(0).astype(int)

        # Detect color/direction changes
        color_change = (direction != direction.shift(1)).astype(int)

        return {
            'long_stop': long_stop,
            'short_stop': short_stop,
            'direction': direction,
            'color_change': color_change,
        }

    def _calculate_adx_leaf_west(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        adx_length: int = 8,
        dmi_length: int = 9,
    ) -> dict[str, pd.Series]:
        """Calculate ADX Leaf West style (shorter periods for faster signals).

        This is an ADX/DMI variant with different period settings for ADX vs DMI.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            adx_length: ADX smoothing period (default 8)
            dmi_length: DMI calculation period (default 9)

        Returns:
            Dictionary with 'adx', 'plus_di', 'minus_di', 'di_diff'
        """
        # Calculate True Range
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)

        # Calculate +DM and -DM
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = pd.Series(0.0, index=close.index)
        minus_dm = pd.Series(0.0, index=close.index)

        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

        # Smooth TR, +DM, -DM with Wilder's smoothing (using DMI length)
        smoothed_tr = tr.ewm(alpha=1/dmi_length, adjust=False).mean()
        smoothed_plus_dm = plus_dm.ewm(alpha=1/dmi_length, adjust=False).mean()
        smoothed_minus_dm = minus_dm.ewm(alpha=1/dmi_length, adjust=False).mean()

        # Calculate +DI and -DI
        plus_di = 100 * smoothed_plus_dm / smoothed_tr
        minus_di = 100 * smoothed_minus_dm / smoothed_tr

        # Calculate DX
        di_sum = plus_di + minus_di
        di_diff_abs = (plus_di - minus_di).abs()
        dx = 100 * di_diff_abs / di_sum.replace(0, np.nan)

        # Calculate ADX (smoothed DX using ADX length)
        adx = dx.ewm(alpha=1/adx_length, adjust=False).mean()

        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di,
            'di_diff': plus_di - minus_di,
        }

    def _suggest_json_params(self, trial: optuna.Trial) -> None:
        """Suggest parameter values from JSON config using Optuna.

        Extracts all parameters with 'range' from JSON indicators and regimes,
        then uses Optuna trial to suggest values for each. Results are stored
        in self._trial_params for use by _calculate_json_indicators() and
        _classify_regimes_json().

        Key format for _trial_params:
        - Indicator params: "{ind_name}.{param_name}" (e.g., "STRENGTH_ADX.period")
        - Regime thresholds: "{regime_id}.{thresh_name}" (e.g., "BULL.adx_min")

        Args:
            trial: Optuna trial for parameter suggestion
        """
        self._trial_params.clear()

        # Ensure caches are populated
        if self._json_indicators_cache is None:
            if not self.json_config or "optimization_results" not in self.json_config:
                return
            opt_results = self.json_config["optimization_results"]
            applied = [r for r in opt_results if r.get('applied', False)]
            result = applied[-1] if applied else opt_results[0]
            self._json_indicators_cache = result.get('indicators', [])
            self._json_regimes_cache = result.get('regimes', [])
            self._build_indicator_type_maps()

        # Suggest indicator parameters
        for ind in self._json_indicators_cache:
            ind_name = ind['name']
            for param in ind.get('params', []):
                param_name = param['name']
                param_value = param['value']
                param_range = param.get('range')

                key = f"{ind_name}.{param_name}"

                if param_range:
                    # Has optimization range - suggest via Optuna
                    min_val = param_range['min']
                    max_val = param_range['max']
                    step = param_range.get('step', 1)

                    # Determine if integer or float based on value type and step
                    if isinstance(param_value, int) and step >= 1 and step == int(step):
                        self._trial_params[key] = trial.suggest_int(
                            key, int(min_val), int(max_val), step=int(step)
                        )
                    else:
                        self._trial_params[key] = trial.suggest_float(
                            key, float(min_val), float(max_val), step=float(step)
                        )
                else:
                    # No range - use fixed value from JSON
                    self._trial_params[key] = param_value

        # Suggest regime threshold parameters
        for regime in (self._json_regimes_cache or []):
            regime_id = regime['id'].upper()  # Match case used in _classify_regimes_json
            for thresh in regime.get('thresholds', []):
                thresh_name = thresh['name']
                thresh_value = thresh['value']
                thresh_range = thresh.get('range')

                key = f"{regime_id}.{thresh_name}"

                if thresh_range:
                    # Has optimization range - suggest via Optuna
                    min_val = thresh_range['min']
                    max_val = thresh_range['max']
                    step = thresh_range.get('step', 1)

                    # Thresholds are typically float
                    if isinstance(thresh_value, int) and step >= 1 and step == int(step):
                        self._trial_params[key] = trial.suggest_int(
                            key, int(min_val), int(max_val), step=int(step)
                        )
                    else:
                        self._trial_params[key] = trial.suggest_float(
                            key, float(min_val), float(max_val), step=float(step)
                        )
                else:
                    # No range - use fixed value from JSON
                    self._trial_params[key] = thresh_value

        if trial.number == 0:
            logger.info(
                f"[JSON PARAMS] Suggested {len(self._trial_params)} parameters "
                f"for trial 0: {list(self._trial_params.keys())[:5]}..."
            )

    def _get_json_param_value(
        self, scope: str, param: dict, fallback: float | int | None = None
    ) -> float | int:
        """Get parameter value from trial-suggested params or fallback to JSON value.

        Args:
            scope: Indicator name or regime ID
            param: Parameter dict with 'name' and 'value' keys
            fallback: Optional fallback if not found anywhere

        Returns:
            Parameter value (trial-suggested or JSON default)
        """
        key = f"{scope}.{param['name']}"

        # First check trial-suggested params
        if key in self._trial_params:
            return self._trial_params[key]

        # Fallback to JSON value
        if 'value' in param:
            return param['value']

        # Final fallback
        if fallback is not None:
            return fallback

        raise KeyError(f"No value found for parameter: {key}")

    def _load_trial_params(self, trial: optuna.trial.FrozenTrial) -> None:
        """Load trial-suggested params from a completed trial's stored params.

        Used post-optimization to reload the params for result extraction.
        Only loads keys that match the JSON param pattern (e.g., "STRENGTH_ADX.period").

        Args:
            trial: Completed Optuna trial with stored params
        """
        self._trial_params.clear()

        for key, value in trial.params.items():
            # Only load JSON-style params (contain dots like "INDICATOR.param" or "REGIME.thresh")
            if '.' in key:
                self._trial_params[key] = value

    def _calculate_json_indicators(
        self, params: RegimeParams
    ) -> dict[str, pd.Series]:
        """Calculate all indicators needed for JSON-based regime detection.

        Uses v2.0 JSON config to determine which indicators to calculate.
        Supports dynamic indicator types including:
        - Standard: ADX, RSI, ATR, SMA, EMA
        - Custom: CHANDELIER, ADX_LEAF_WEST, CKSP (Chande Kroll Stop)

        Args:
            params: Trial parameters (used for period values)

        Returns:
            Dictionary of indicator values keyed by indicator name
        """
        # Get indicators from JSON config
        if self._json_indicators_cache is None:
            if not self.json_config or "optimization_results" not in self.json_config:
                return {}
            opt_results = self.json_config["optimization_results"]
            applied = [r for r in opt_results if r.get('applied', False)]
            result = applied[-1] if applied else opt_results[0]
            self._json_indicators_cache = result.get('indicators', [])
            self._json_regimes_cache = result.get('regimes', [])

            # Build dynamic type→name mappings
            self._build_indicator_type_maps()

        indicators = {}
        high = self.data["high"]
        low = self.data["low"]
        close = self.data["close"]

        # Calculate each indicator from JSON config
        for ind in self._json_indicators_cache:
            name = ind['name']
            ind_type = ind['type'].upper()
            # Use trial-suggested params if available, else fallback to JSON values
            json_params = {
                p['name']: self._get_json_param_value(name, p)
                for p in ind.get('params', [])
            }

            try:
                if ind_type == 'ADX':
                    period = int(json_params.get('period', params.adx_period))
                    if TALIB_AVAILABLE:
                        indicators[name] = pd.Series(
                            talib.ADX(high, low, close, timeperiod=period),
                            index=self.data.index
                        )
                        # Store DI values with indicator name prefix for flexibility
                        indicators[f'{name}_PLUS_DI'] = pd.Series(
                            talib.PLUS_DI(high, low, close, timeperiod=period),
                            index=self.data.index
                        )
                        indicators[f'{name}_MINUS_DI'] = pd.Series(
                            talib.MINUS_DI(high, low, close, timeperiod=period),
                            index=self.data.index
                        )
                    elif PANDAS_TA_AVAILABLE:
                        adx_df = ta.adx(high, low, close, length=period)
                        adx_col = [c for c in adx_df.columns if c.startswith("ADX_")][0]
                        dmp_col = [c for c in adx_df.columns if c.startswith("DMP_")][0]
                        dmn_col = [c for c in adx_df.columns if c.startswith("DMN_")][0]
                        indicators[name] = adx_df[adx_col]
                        indicators[f'{name}_PLUS_DI'] = adx_df[dmp_col]
                        indicators[f'{name}_MINUS_DI'] = adx_df[dmn_col]
                    else:
                        indicators[name] = pd.Series(25.0, index=self.data.index)
                        indicators[f'{name}_PLUS_DI'] = pd.Series(25.0, index=self.data.index)
                        indicators[f'{name}_MINUS_DI'] = pd.Series(25.0, index=self.data.index)

                    # Calculate DI difference
                    indicators[f'{name}_DI_DIFF'] = (
                        indicators[f'{name}_PLUS_DI'] - indicators[f'{name}_MINUS_DI']
                    )
                    # Also store without prefix for backward compatibility
                    indicators['PLUS_DI'] = indicators[f'{name}_PLUS_DI']
                    indicators['MINUS_DI'] = indicators[f'{name}_MINUS_DI']
                    indicators['DI_DIFF'] = indicators[f'{name}_DI_DIFF']

                elif ind_type == 'ADX_LEAF_WEST':
                    # ADX Leaf West style with separate ADX/DMI periods
                    adx_length = int(json_params.get('adx_length', 8))
                    dmi_length = int(json_params.get('dmi_length', 9))

                    result = self._calculate_adx_leaf_west(
                        high, low, close, adx_length, dmi_length
                    )
                    indicators[name] = result['adx']
                    indicators[f'{name}_PLUS_DI'] = result['plus_di']
                    indicators[f'{name}_MINUS_DI'] = result['minus_di']
                    indicators[f'{name}_DI_DIFF'] = result['di_diff']

                elif ind_type in ('CHANDELIER', 'CKSP', 'CHANDELIER_STOP'):
                    # Chandelier Stop / Chande Kroll Stop
                    lookback = int(json_params.get('lookback', 22))
                    atr_period = int(json_params.get('atr_period', 22))
                    multiplier = float(json_params.get('multiplier', 3.0))

                    result = self._calculate_chandelier_stop(
                        high, low, close, lookback, atr_period, multiplier
                    )
                    indicators[name] = result['direction']  # Main value: direction
                    indicators[f'{name}_LONG_STOP'] = result['long_stop']
                    indicators[f'{name}_SHORT_STOP'] = result['short_stop']
                    indicators[f'{name}_DIRECTION'] = result['direction']
                    indicators[f'{name}_COLOR_CHANGE'] = result['color_change']

                elif ind_type == 'RSI':
                    period = int(json_params.get('period', params.rsi_period))
                    if PANDAS_TA_AVAILABLE:
                        indicators[name] = ta.rsi(close, length=period)
                    else:
                        rsi_result = MomentumIndicators.calculate_rsi(
                            self.data, {"period": period}, use_talib=True
                        )
                        indicators[name] = rsi_result.values

                elif ind_type == 'ATR':
                    period = int(json_params.get('period', params.atr_period or 14))
                    atr_result = VolatilityIndicators.calculate_atr(
                        self.data, {"period": period}, use_talib=True
                    )
                    indicators[name] = atr_result.values

                elif ind_type == 'SMA':
                    period = int(json_params.get('period', 20))
                    indicators[name] = close.rolling(window=period).mean()

                elif ind_type == 'EMA':
                    period = int(json_params.get('period', 20))
                    indicators[name] = close.ewm(span=period, adjust=False).mean()

                elif ind_type == 'BB':
                    # Bollinger Bands
                    period = int(json_params.get('period', 20))
                    std_dev = float(json_params.get('std_dev', 2.0))
                    if PANDAS_TA_AVAILABLE:
                        bb = ta.bbands(close, length=period, std=std_dev)
                        lower_col = [c for c in bb.columns if c.startswith("BBL_")][0]
                        middle_col = [c for c in bb.columns if c.startswith("BBM_")][0]
                        upper_col = [c for c in bb.columns if c.startswith("BBU_")][0]
                        indicators[name] = bb[middle_col]  # Main value: middle band
                        indicators[f'{name}_UPPER'] = bb[upper_col]
                        indicators[f'{name}_LOWER'] = bb[lower_col]
                        indicators[f'{name}_WIDTH'] = (bb[upper_col] - bb[lower_col]) / bb[middle_col] * 100
                    else:
                        sma = close.rolling(window=period).mean()
                        std = close.rolling(window=period).std()
                        indicators[name] = sma
                        indicators[f'{name}_UPPER'] = sma + std_dev * std
                        indicators[f'{name}_LOWER'] = sma - std_dev * std
                        indicators[f'{name}_WIDTH'] = (2 * std_dev * std) / sma * 100

                else:
                    logger.warning(f"Unknown indicator type: {ind_type}")
                    indicators[name] = pd.Series(np.nan, index=self.data.index)

            except Exception as e:
                logger.error(f"Error calculating indicator {name} ({ind_type}): {e}")
                indicators[name] = pd.Series(np.nan, index=self.data.index)

        # Always calculate price change percentage for extreme move detection
        indicators['PRICE_CHANGE_PCT'] = close.pct_change() * 100

        return indicators

    def _resolve_indicator_name(self, base: str, suffix: str = '') -> str:
        """Dynamically resolve indicator name from type or threshold base name.

        Uses the type→name mapping built from JSON indicators.
        Falls back to uppercase base name if no mapping exists.

        Args:
            base: Threshold base name (e.g., 'adx', 'rsi', 'chandelier')
            suffix: Optional suffix (e.g., '_DI_DIFF', '_DIRECTION')

        Returns:
            Resolved indicator name (e.g., 'STRENGTH_ADX_DI_DIFF')
        """
        base_upper = base.upper()

        # Check if we have a direct mapping for this type
        if base_upper in self._indicator_type_map:
            ind_name = self._indicator_type_map[base_upper]
            return f"{ind_name}{suffix}" if suffix else ind_name

        # Check common aliases - find any alias that exists in the type map
        alias_groups = [
            ['ADX', 'ADX_LEAF_WEST'],  # ADX-family indicators
            ['RSI'],
            ['ATR'],
            ['CHANDELIER', 'CKSP', 'CHANDELIER_STOP'],  # Chandelier-family indicators
            ['BB', 'BOLLINGER'],
            ['SMA'],
            ['EMA'],
        ]

        for alias_list in alias_groups:
            if base_upper in alias_list:
                # Find any alias from this group that exists in the type map
                for alias in alias_list:
                    if alias in self._indicator_type_map:
                        ind_name = self._indicator_type_map[alias]
                        return f"{ind_name}{suffix}" if suffix else ind_name

        # Fallback: return base name with suffix
        return f"{base_upper}{suffix}" if suffix else base_upper

    def _classify_regimes_json(
        self, params: RegimeParams, indicators: dict[str, pd.Series]
    ) -> pd.Series:
        """Classify regimes using v2.0 JSON config with per-regime thresholds.

        Evaluates each bar against all regimes in priority order (highest first).
        Uses dynamic indicator resolution from JSON config.

        Supports threshold types:
        - {type}_min, {type}_max: Generic min/max thresholds for any indicator
        - di_diff_min: DI+ - DI- difference for direction
        - {type}_direction_eq: Indicator direction equals value (1=bull, -1=bear)
        - {type}_color_change: Indicator color/direction change (Chandelier)
        - {type}_above, {type}_below: Threshold comparisons
        - rsi_strong_bull, rsi_strong_bear: RSI confirmation thresholds
        - rsi_confirm_bull, rsi_confirm_bear: RSI momentum confirmation
        - rsi_exhaustion_max, rsi_exhaustion_min: Exhaustion detection
        - extreme_move_pct: Price change percentage override

        Args:
            params: Trial parameters (for indicator periods)
            indicators: Calculated indicator values

        Returns:
            Series with regime labels for each bar
        """
        if not self._json_regimes_cache:
            logger.warning("No JSON regimes configured, falling back to SIDEWAYS")
            return pd.Series("SIDEWAYS", index=self.data.index)

        # Sort regimes by priority (highest first)
        sorted_regimes = sorted(
            self._json_regimes_cache,
            key=lambda r: r.get('priority', 0),
            reverse=True
        )

        # Fallback to lowest priority regime (usually SIDEWAYS)
        fallback_regime_id = sorted_regimes[-1]['id'] if sorted_regimes else "SIDEWAYS"

        def get_indicator_value(ind_name: str, idx: int) -> float:
            """Get indicator value at specific bar index."""
            if ind_name not in indicators:
                # Try without prefix
                for key in indicators:
                    if key.endswith(ind_name) or ind_name.endswith(key):
                        ind_name = key
                        break
                else:
                    return np.nan

            vals = indicators[ind_name]
            if isinstance(vals, pd.DataFrame):
                return float(vals.iloc[idx, 0]) if idx < len(vals) else np.nan
            elif isinstance(vals, pd.Series):
                return float(vals.iloc[idx]) if idx < len(vals) else np.nan
            return np.nan

        def evaluate_regime_at(regime: dict, idx: int) -> bool:
            """Evaluate if regime conditions are met at bar index."""
            thresholds = regime.get('thresholds', [])
            regime_id = regime.get('id', '').upper()

            for thresh in thresholds:
                name = thresh['name']
                # Use trial-suggested threshold value if available, else JSON default
                value = self._get_json_param_value(regime_id, thresh)

                # ===== Direction-based thresholds (Chandelier, etc.) =====
                if name.endswith('_direction_eq'):
                    base = name[:-13]  # Remove '_direction_eq'
                    ind_name = self._resolve_indicator_name(base, '_DIRECTION')
                    direction_val = get_indicator_value(ind_name, idx)
                    if np.isnan(direction_val) or int(direction_val) != int(value):
                        return False
                    continue

                if name.endswith('_color_change'):
                    base = name[:-13]  # Remove '_color_change'
                    ind_name = self._resolve_indicator_name(base, '_COLOR_CHANGE')
                    change_val = get_indicator_value(ind_name, idx)
                    if np.isnan(change_val):
                        return False
                    # value: 1 = require change, 0 = require no change
                    if int(value) == 1 and int(change_val) != 1:
                        return False
                    if int(value) == 0 and int(change_val) != 0:
                        return False
                    continue

                # ===== DI difference threshold (direction confirmation) =====
                if name == 'di_diff_min':
                    # Try to find DI_DIFF from any ADX-type indicator
                    di_diff = np.nan
                    for key in indicators:
                        if key.endswith('_DI_DIFF') or key == 'DI_DIFF':
                            di_diff = get_indicator_value(key, idx)
                            if not np.isnan(di_diff):
                                break

                    if np.isnan(di_diff):
                        return False
                    # TF/TREND: absolute diff (either direction)
                    if regime_id in ('TF', 'STRONG_TF') or 'TREND' in regime_id:
                        if abs(di_diff) < value:
                            return False
                    elif 'BULL' in regime_id:
                        if di_diff < value:  # DI+ - DI- > threshold
                            return False
                    elif 'BEAR' in regime_id:
                        if di_diff > -value:  # DI- - DI+ > threshold
                            return False
                    else:
                        if abs(di_diff) < value:
                            return False
                    continue

                # ===== RSI thresholds (with dynamic resolution) =====
                if name.startswith('rsi_'):
                    # Resolve RSI indicator name dynamically
                    rsi_ind_name = self._resolve_indicator_name('RSI')
                    rsi_val = get_indicator_value(rsi_ind_name, idx)

                    if name == 'rsi_strong_bull':
                        if np.isnan(rsi_val) or rsi_val < value:
                            return False
                        continue

                    if name == 'rsi_strong_bear':
                        if np.isnan(rsi_val) or rsi_val > value:
                            return False
                        continue

                    if name == 'rsi_confirm_bull':
                        if np.isnan(rsi_val) or rsi_val < value:
                            return False
                        continue

                    if name == 'rsi_confirm_bear':
                        if np.isnan(rsi_val) or rsi_val > value:
                            return False
                        continue

                    if name == 'rsi_exhaustion_max':
                        if np.isnan(rsi_val) or rsi_val > value:
                            return False
                        continue

                    if name == 'rsi_exhaustion_min':
                        if np.isnan(rsi_val) or rsi_val < value:
                            return False
                        continue

                # ===== Extreme price move =====
                if name == 'extreme_move_pct':
                    price_change = get_indicator_value('PRICE_CHANGE_PCT', idx)
                    if np.isnan(price_change):
                        return False
                    if 'BULL' in regime_id:
                        if price_change < value:
                            return False
                    elif 'BEAR' in regime_id:
                        if price_change > -value:
                            return False
                    continue

                # ===== Generic _above/_below thresholds =====
                if name.endswith('_above'):
                    base = name[:-6]  # Remove '_above'
                    ind_name = self._resolve_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val <= value:
                        return False
                    continue

                if name.endswith('_below'):
                    base = name[:-6]  # Remove '_below'
                    ind_name = self._resolve_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val >= value:
                        return False
                    continue

                # ===== Standard _min/_max thresholds =====
                if name.endswith('_min'):
                    base = name[:-4]
                    ind_name = self._resolve_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val < value:
                        return False
                    continue

                if name.endswith('_max'):
                    base = name[:-4]
                    ind_name = self._resolve_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val >= value:
                        return False
                    continue

            return True  # All thresholds passed

        # Classify each bar (skip warmup bars)
        warmup = max(50, params.adx_period * 2)
        regimes = pd.Series(fallback_regime_id, index=self.data.index)

        for i in range(warmup, len(self.data)):
            for regime in sorted_regimes:
                if evaluate_regime_at(regime, i):
                    regimes.iloc[i] = regime['id']
                    break

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
        def infer_base_type(regime_id: str) -> str:
            """Infer base regime type from regime ID for color coding."""
            regime_upper = regime_id.upper()
            if 'BULL' in regime_upper:
                return 'BULL'
            elif 'BEAR' in regime_upper:
                return 'BEAR'
            else:
                return 'SIDEWAYS'

        periods = []

        if len(regimes) == 0:
            return periods

        current_regime = str(regimes.iloc[0])
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
                        regime=current_regime,
                        base_type=infer_base_type(current_regime),
                        start_idx=start_idx,
                        end_idx=end_idx,
                        start_timestamp=start_ts,
                        end_timestamp=end_ts,
                        bars=end_idx - start_idx + 1,
                    )
                )

                # Start new regime
                current_regime = str(regimes.iloc[i])
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
                regime=current_regime,
                base_type=infer_base_type(current_regime),
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

        Supports two modes:
        - JSON mode: Uses _classify_regimes_json() with per-regime thresholds from v2.0 config
        - Legacy mode: Uses _classify_regimes() with global thresholds

        Args:
            trial: Optuna trial

        Returns:
            RegimeScore (0-100) to maximize
        """
        try:
            # Suggest parameters
            params = self._suggest_params(trial)

            # Calculate indicators and classify regimes
            # Use JSON mode if json_config is provided
            if self.json_config is not None:
                # JSON mode: Suggest params from JSON ranges using Optuna
                self._suggest_json_params(trial)
                # Calculate indicators with trial-suggested params
                indicators = self._calculate_json_indicators(params)
                # Classify using JSON per-regime thresholds
                regimes = self._classify_regimes_json(params, indicators)

                if trial.number == 0:
                    logger.info(
                        f"[JSON MODE] Using v2.0 config with {len(self._json_regimes_cache or [])} regimes, "
                        f"{len(self._json_indicators_cache or [])} indicators"
                    )
            else:
                # Legacy mode: Use existing classification
                indicators = self._calculate_indicators(params)
                regimes = self._classify_regimes(params, indicators)

            # Convert regimes to Series for scoring
            regimes_series = pd.Series(regimes, index=self.data.index)

            # Calculate new 5-component RegimeScore
            # Adaptive warmup/lookback: Scale with data size
            data_len = len(self.data)

            # Warmup: Max 10% of data, capped at 200
            warmup_bars = min(200, max(50, data_len // 10))

            # Feature lookback: Max of indicator periods, but capped to leave enough data
            period_candidates = [
                params.adx_period,
                params.rsi_period,
                params.atr_period,
                params.sma_fast_period,
                params.sma_slow_period,
                params.bb_period,
            ]
            max_indicator_period = max([p for p in period_candidates if p is not None] or [params.adx_period])
            # Cap lookback to leave at least 60% of data for scoring
            max_feature_lookback = min(max_indicator_period, data_len // 4)

            # Log first trial for debugging
            if trial.number == 0:
                logger.info(
                    f"Trial 0 config: data_len={data_len}, warmup={warmup_bars}, "
                    f"lookback={max_feature_lookback}, max_indicator={max_indicator_period}"
                )

            # Create score config - use JSON weights if available
            if self.json_config is not None:
                # Load weights from JSON evaluation_params.score_weights
                score_config = RegimeScoreConfig.from_json_config(self.json_config)
                if trial.number == 0:
                    logger.info(
                        f"Using score weights from JSON: "
                        f"sep={score_config.w_separability:.2f}, coh={score_config.w_coherence:.2f}, "
                        f"fid={score_config.w_fidelity:.2f}, bnd={score_config.w_boundary:.2f}, "
                        f"cov={score_config.w_coverage:.2f}"
                    )
            else:
                score_config = RegimeScoreConfig()

            # Override data-specific parameters
            score_config.warmup_bars = warmup_bars
            score_config.max_feature_lookback = max_feature_lookback

            # Relax gates for small datasets and high-frequency data (scalping)
            score_config.min_segments = max(3, data_len // 200)  # Reduced: 3 segments per 200 bars
            score_config.min_avg_duration = 2  # Reduced from 3 - allow shorter regimes for scalping
            score_config.max_switch_rate_per_1000 = 500  # Increased from 80 - scalping has high switch rates
            score_config.min_unique_labels = 2  # Must have at least 2 regimes
            score_config.min_bars_for_scoring = max(30, data_len // 10)  # Scale with data size
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
            if self.json_config is not None:
                # JSON mode: Reload best trial's JSON params
                if self._study and self._study.best_trial:
                    self._load_trial_params(self._study.best_trial)
                indicators = self._calculate_json_indicators(best_params)
                regimes = self._classify_regimes_json(best_params, indicators)
            else:
                # Legacy mode
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
            params_kwargs = {"adx_period": trial.params["adx_period"], "rsi_period": trial.params["rsi_period"]}

            # Simple mode keys (present in tests)
            if "adx_threshold" in trial.params:
                params_kwargs["adx_threshold"] = trial.params["adx_threshold"]
            if "sma_fast_period" in trial.params:
                params_kwargs["sma_fast_period"] = trial.params["sma_fast_period"]
            if "sma_slow_period" in trial.params:
                params_kwargs["sma_slow_period"] = trial.params["sma_slow_period"]
            if "rsi_sideways_low" in trial.params:
                params_kwargs["rsi_sideways_low"] = trial.params["rsi_sideways_low"]
            if "rsi_sideways_high" in trial.params:
                params_kwargs["rsi_sideways_high"] = trial.params["rsi_sideways_high"]
            if "bb_period" in trial.params:
                params_kwargs["bb_period"] = trial.params["bb_period"]
            if "bb_std_dev" in trial.params:
                params_kwargs["bb_std_dev"] = trial.params["bb_std_dev"]
            if "bb_width_percentile" in trial.params:
                params_kwargs["bb_width_percentile"] = trial.params["bb_width_percentile"]

            # Legacy ADX/DI keys
            if "adx_trending_threshold" in trial.params:
                params_kwargs["adx_trending_threshold"] = trial.params["adx_trending_threshold"]
            if "adx_weak_threshold" in trial.params:
                params_kwargs["adx_weak_threshold"] = trial.params["adx_weak_threshold"]
            if "di_diff_threshold" in trial.params:
                params_kwargs["di_diff_threshold"] = trial.params["di_diff_threshold"]
            if "rsi_strong_bull" in trial.params:
                params_kwargs["rsi_strong_bull"] = trial.params["rsi_strong_bull"]
            if "rsi_strong_bear" in trial.params:
                params_kwargs["rsi_strong_bear"] = trial.params["rsi_strong_bear"]
            if "atr_period" in trial.params:
                params_kwargs["atr_period"] = trial.params["atr_period"]
            if "strong_move_pct" in trial.params:
                params_kwargs["strong_move_pct"] = trial.params["strong_move_pct"]
            if "extreme_move_pct" in trial.params:
                params_kwargs["extreme_move_pct"] = trial.params["extreme_move_pct"]

            params = RegimeParams(**params_kwargs)

            # Recalculate metrics for this trial
            if self.json_config is not None:
                # JSON mode: Reload trial's JSON params
                self._load_trial_params(trial)
                indicators = self._calculate_json_indicators(params)
                regimes = self._classify_regimes_json(params, indicators)
            else:
                # Legacy mode
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

            # Extract JSON params from trial (keys with '.' like "DIRECTION_CHANDELIER.lookback")
            json_params = {}
            if self.json_config is not None:
                for key, value in trial.params.items():
                    if '.' in key:  # JSON param format: "INDICATOR.param" or "REGIME.threshold"
                        json_params[key] = value

            results.append(
                OptimizationResult(
                    rank=rank,
                    score=trial.value,
                    params=params,
                    metrics=metrics,
                    timestamp=trial.datetime_complete or datetime.utcnow(),
                    json_params=json_params,
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
