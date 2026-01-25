"""Regime Scoring System - 5-component quality score for regime detection.

This module implements a production-ready RegimeScore (0-100) based on:
- Separability (30%): Silhouette, Calinski-Harabasz, Davies-Bouldin
- Temporal Coherence (25%): switch_rate, avg_duration, Markov self-transition
- Fidelity (25%): Hurst exponent per regime type
- Boundary Strength (10%): Feature distance at regime changes (Mahalanobis)
- Coverage/Balance (10%): coverage ratio, balance penalty

Key Features:
- Warmup handling (first N bars excluded)
- Edge-case safe (single label, singular covariance, short segments)
- Deterministic (fixed random_state for sampling)
- Feature standardization (RobustScaler)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import mahalanobis
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class RegimeScoreConfig:
    """Configuration for Regime Scoring System.

    Attributes:
        warmup_bars: Number of bars to exclude at start (indicator warmup)
        max_feature_lookback: Maximum lookback used by features
        silhouette_sample_size: Max samples for Silhouette (performance)
        random_state: Seed for reproducibility
        boundary_window: Bars before/after boundary for strength calc
        cov_reg_lambda: Regularization for Mahalanobis covariance
        hurst_min_len: Minimum segment length for Hurst calculation
        w_*: Component weights (must sum to 1.0)
        min_*/max_*: Gate thresholds
    """

    # Data handling
    warmup_bars: int = 200
    max_feature_lookback: int = 300

    # Performance
    silhouette_sample_size: int = 3000
    random_state: int = 42

    # Boundary calculation
    boundary_window: int = 20
    cov_reg_lambda: float = 1e-4

    # Fidelity
    hurst_min_len: int = 200

    # Component weights (sum = 1.0)
    w_separability: float = 0.30
    w_coherence: float = 0.25
    w_fidelity: float = 0.25
    w_boundary: float = 0.10
    w_coverage: float = 0.10

    # Gates (fail-fast thresholds)
    min_coverage: float = 0.60
    max_switch_rate_per_1000: int = 40
    min_avg_duration: int = 10
    min_segments: int = 8
    min_unique_labels: int = 2
    min_bars_for_scoring: int = 50  # Minimum bars after cleanup


# =============================================================================
# Score Result Types
# =============================================================================


@dataclass
class SeparabilityScore:
    """Cluster separability metrics."""

    silhouette: float = 0.0  # [-1, 1] -> [0, 1]
    calinski_harabasz: float = 0.0  # [0, inf) -> [0, 1]
    davies_bouldin: float = 0.0  # [0, inf), lower better -> [0, 1]
    normalized: float = 0.0  # Combined [0, 1]


@dataclass
class CoherenceScore:
    """Temporal coherence metrics."""

    switch_rate_per_1000: float = 0.0
    avg_duration_bars: float = 0.0
    markov_self_transition: float = 0.0  # How "sticky" regimes are
    normalized: float = 0.0


@dataclass
class FidelityScore:
    """Regime fidelity metrics (behavior matches label)."""

    trend_hurst: float = 0.5  # Should be > 0.5 for trend regimes
    range_hurst: float = 0.5  # Should be < 0.5 for range regimes
    vol_fidelity: float = 0.0  # High-vol should have higher realized vol
    normalized: float = 0.0


@dataclass
class BoundaryScore:
    """Regime boundary quality metrics."""

    avg_boundary_strength: float = 0.0  # Mahalanobis distance at boundaries
    boundary_count: int = 0
    normalized: float = 0.0


@dataclass
class CoverageScore:
    """Coverage and balance metrics."""

    coverage: float = 1.0  # Fraction of bars labeled (vs UNKNOWN)
    balance: float = 0.0  # Penalty for extreme regime dominance
    normalized: float = 0.0


@dataclass
class RegimeScoreResult:
    """Complete regime scoring result."""

    total_score: float = 0.0  # 0-100
    gates_passed: bool = True
    gate_failures: list = field(default_factory=list)

    separability: SeparabilityScore = field(default_factory=SeparabilityScore)
    coherence: CoherenceScore = field(default_factory=CoherenceScore)
    fidelity: FidelityScore = field(default_factory=FidelityScore)
    boundary: BoundaryScore = field(default_factory=BoundaryScore)
    coverage: CoverageScore = field(default_factory=CoverageScore)

    # Debugging info
    n_bars_scored: int = 0
    n_bars_excluded: int = 0
    unique_labels: list = field(default_factory=list)


# =============================================================================
# Helper Functions
# =============================================================================


def _clamp01(x: float) -> float:
    """Clamp value to [0, 1]."""
    return max(0.0, min(1.0, x))


def _silhouette_to_score(sil: float) -> float:
    """Map Silhouette [-1, 1] to [0, 1]."""
    return _clamp01((sil + 1.0) / 2.0)


def _db_to_score(db: float) -> float:
    """Map Davies-Bouldin [0, inf) lower=better to [0, 1]."""
    return _clamp01(1.0 / (1.0 + db))


def _ch_to_score(ch: float) -> float:
    """Map Calinski-Harabasz [0, inf) higher=better to [0, 1]."""
    if ch <= 0:
        return 0.0
    return _clamp01(1.0 - np.exp(-np.log1p(ch) / 10.0))


def _compute_hurst(series: pd.Series, max_k: int = 100) -> float:
    """Compute Hurst exponent using R/S analysis.

    Args:
        series: Price returns or log returns
        max_k: Maximum lag for R/S calculation

    Returns:
        Hurst exponent H in [0, 1]
        H > 0.5: trending (persistent)
        H < 0.5: mean-reverting (anti-persistent)
        H ≈ 0.5: random walk
    """
    ts = series.dropna().values
    n = len(ts)
    if n < 20:
        return 0.5  # Not enough data

    max_k = min(max_k, n // 2)
    if max_k < 4:
        return 0.5

    rs_list = []
    n_list = []

    for k in range(10, max_k + 1, max(1, max_k // 20)):
        subset = ts[:k]
        if len(subset) < 10:
            continue

        mean_val = np.mean(subset)
        deviation = subset - mean_val
        cum_dev = np.cumsum(deviation)

        r = np.max(cum_dev) - np.min(cum_dev)
        s = np.std(subset, ddof=1)

        if s > 1e-10:
            rs_list.append(r / s)
            n_list.append(k)

    if len(rs_list) < 3:
        return 0.5

    # Linear regression on log-log plot
    log_n = np.log(n_list)
    log_rs = np.log(rs_list)

    try:
        slope, _ = np.polyfit(log_n, log_rs, 1)
        return _clamp01(slope)
    except Exception:
        return 0.5


def _compute_mahalanobis_safe(
    x: np.ndarray, mean: np.ndarray, cov: np.ndarray, reg_lambda: float = 1e-4
) -> float:
    """Compute Mahalanobis distance with regularization and fallback.

    Args:
        x: Sample vector
        mean: Mean vector
        cov: Covariance matrix
        reg_lambda: Regularization lambda

    Returns:
        Mahalanobis distance
    """
    n = cov.shape[0]
    cov_reg = cov + reg_lambda * np.eye(n)

    try:
        VI = np.linalg.inv(cov_reg)
    except np.linalg.LinAlgError:
        VI = np.linalg.pinv(cov_reg)

    try:
        return float(mahalanobis(x, mean, VI))
    except Exception:
        return 0.0


# =============================================================================
# Component Score Calculations
# =============================================================================


def _calculate_separability(
    features: pd.DataFrame,
    labels: np.ndarray,
    config: RegimeScoreConfig,
) -> SeparabilityScore:
    """Calculate cluster separability score."""
    result = SeparabilityScore()
    n_samples = len(labels)
    unique_labels = np.unique(labels)
    n_labels = len(unique_labels)

    # Gate: need at least 2 labels
    if n_labels < config.min_unique_labels:
        return result

    # Sample if too large (for performance)
    if n_samples > config.silhouette_sample_size:
        rng = np.random.RandomState(config.random_state)
        idx = rng.choice(n_samples, config.silhouette_sample_size, replace=False)
        features_sample = features.iloc[idx]
        labels_sample = labels[idx]
    else:
        features_sample = features
        labels_sample = labels

    # Silhouette
    try:
        sil = silhouette_score(
            features_sample,
            labels_sample,
            sample_size=min(len(labels_sample), 5000),
            random_state=config.random_state,
        )
        result.silhouette = float(sil)
    except Exception as e:
        logger.warning(f"Silhouette failed: {e}")

    # Calinski-Harabasz
    try:
        ch = calinski_harabasz_score(features_sample, labels_sample)
        result.calinski_harabasz = float(ch)
    except Exception as e:
        logger.warning(f"Calinski-Harabasz failed: {e}")

    # Davies-Bouldin
    try:
        db = davies_bouldin_score(features_sample, labels_sample)
        result.davies_bouldin = float(db)
    except Exception as e:
        logger.warning(f"Davies-Bouldin failed: {e}")

    # Normalize and combine
    sil_s = _silhouette_to_score(result.silhouette)
    ch_s = _ch_to_score(result.calinski_harabasz)
    db_s = _db_to_score(result.davies_bouldin)

    # Equal weight within separability
    result.normalized = (sil_s + ch_s + db_s) / 3.0

    return result


def _calculate_coherence(
    regimes: pd.Series,
    config: RegimeScoreConfig,
) -> CoherenceScore:
    """Calculate temporal coherence score."""
    result = CoherenceScore()
    n_bars = len(regimes)
    if n_bars < 2:
        return result

    # Switch count
    switches = (regimes != regimes.shift(1)).sum()
    result.switch_rate_per_1000 = (switches / n_bars) * 1000

    # Average duration
    regime_changes = regimes != regimes.shift(1)
    regime_ids = regime_changes.cumsum()
    regime_lengths = regime_ids.value_counts()
    result.avg_duration_bars = float(regime_lengths.mean()) if len(regime_lengths) > 0 else 0.0

    # Markov self-transition (how sticky)
    unique_labels = regimes.unique()
    self_trans_probs = []
    for label in unique_labels:
        mask = regimes == label
        stays = ((regimes == label) & (regimes.shift(-1) == label)).sum()
        total = mask.sum() - 1  # Exclude last bar
        if total > 0:
            self_trans_probs.append(stays / total)

    result.markov_self_transition = float(np.mean(self_trans_probs)) if self_trans_probs else 0.0

    # Normalize
    # switch_rate: lower is better (target: < 20 per 1000)
    switch_s = _clamp01(1.0 - result.switch_rate_per_1000 / 100.0)
    # duration: higher is better (target: > 50 bars avg)
    duration_s = _clamp01(result.avg_duration_bars / 100.0)
    # self-transition: higher is better
    self_trans_s = result.markov_self_transition

    result.normalized = (switch_s + duration_s + self_trans_s) / 3.0

    return result


def _calculate_fidelity(
    data: pd.DataFrame,
    regimes: pd.Series,
    config: RegimeScoreConfig,
) -> FidelityScore:
    """Calculate regime fidelity score.

    Trend regimes should have Hurst > 0.5 (persistent).
    Range/sideways regimes should have Hurst < 0.5 (mean-reverting).
    """
    result = FidelityScore()

    # Get returns
    if "close" not in data.columns:
        return result

    returns = data["close"].pct_change().dropna()

    # Align indices safely - use intersection
    common_idx = returns.index.intersection(regimes.index)
    if len(common_idx) < config.hurst_min_len:
        # Not enough data for Hurst calculation
        result.normalized = 0.5  # Neutral score
        return result

    returns = returns.loc[common_idx]
    regimes_aligned = regimes.loc[common_idx]

    # Identify regime types (by name convention)
    unique_labels = regimes_aligned.unique()
    trend_labels = [l for l in unique_labels if "BULL" in str(l).upper() or "BEAR" in str(l).upper() or "TREND" in str(l).upper()]
    range_labels = [l for l in unique_labels if "SIDEWAYS" in str(l).upper() or "RANGE" in str(l).upper()]

    # Hurst for trend regimes
    trend_hursts = []
    for label in trend_labels:
        segment_returns = returns[regimes_aligned == label]
        if len(segment_returns) >= config.hurst_min_len:
            h = _compute_hurst(segment_returns)
            trend_hursts.append(h)

    if trend_hursts:
        result.trend_hurst = float(np.mean(trend_hursts))

    # Hurst for range regimes
    range_hursts = []
    for label in range_labels:
        segment_returns = returns[regimes_aligned == label]
        if len(segment_returns) >= config.hurst_min_len:
            h = _compute_hurst(segment_returns)
            range_hursts.append(h)

    if range_hursts:
        result.range_hurst = float(np.mean(range_hursts))

    # Calculate fidelity scores
    # Trend: H should be > 0.5, score = how much above 0.5
    trend_fidelity = _clamp01((result.trend_hurst - 0.5) * 2 + 0.5) if trend_hursts else 0.5
    # Range: H should be < 0.5, score = how much below 0.5
    range_fidelity = _clamp01((0.5 - result.range_hurst) * 2 + 0.5) if range_hursts else 0.5

    # Combine
    if trend_hursts and range_hursts:
        result.normalized = (trend_fidelity + range_fidelity) / 2.0
    elif trend_hursts:
        result.normalized = trend_fidelity
    elif range_hursts:
        result.normalized = range_fidelity
    else:
        result.normalized = 0.5  # No data, neutral

    return result


def _calculate_boundary(
    features: pd.DataFrame,
    regimes: pd.Series,
    config: RegimeScoreConfig,
) -> BoundaryScore:
    """Calculate boundary strength score using Mahalanobis distance."""
    result = BoundaryScore()

    # Find regime change points
    changes = regimes != regimes.shift(1)
    change_idx = changes[changes].index.tolist()
    result.boundary_count = len(change_idx)

    if result.boundary_count == 0:
        return result

    window = config.boundary_window
    strengths = []

    for idx in change_idx:
        try:
            # Get position in index
            pos = features.index.get_loc(idx)

            # Get features before and after boundary
            start_before = max(0, pos - window)
            end_before = pos
            start_after = pos
            end_after = min(len(features), pos + window)

            if end_before <= start_before or end_after <= start_after:
                continue

            features_before = features.iloc[start_before:end_before].values
            features_after = features.iloc[start_after:end_after].values

            if len(features_before) < 5 or len(features_after) < 5:
                continue

            # Calculate means
            mean_before = np.mean(features_before, axis=0)
            mean_after = np.mean(features_after, axis=0)

            # Combined covariance
            cov_combined = np.cov(np.vstack([features_before, features_after]).T)

            # Mahalanobis distance between means
            dist = _compute_mahalanobis_safe(
                mean_before, mean_after, cov_combined, config.cov_reg_lambda
            )
            strengths.append(dist)

        except Exception as e:
            logger.debug(f"Boundary calc failed at {idx}: {e}")
            continue

    if strengths:
        result.avg_boundary_strength = float(np.mean(strengths))
        # Normalize: higher distance = better separation
        # Target: avg distance > 2.0 is good
        result.normalized = _clamp01(result.avg_boundary_strength / 5.0)

    return result


def _calculate_coverage(
    regimes: pd.Series,
    config: RegimeScoreConfig,
) -> CoverageScore:
    """Calculate coverage and balance score."""
    result = CoverageScore()
    n_bars = len(regimes)
    if n_bars == 0:
        return result

    unique_labels = regimes.unique()

    # Coverage: fraction of bars with valid labels (vs UNKNOWN)
    unknown_labels = [l for l in unique_labels if "UNKNOWN" in str(l).upper() or "NONE" in str(l).upper()]
    unknown_count = sum(regimes.isin(unknown_labels).sum() for l in unknown_labels) if unknown_labels else 0
    result.coverage = (n_bars - unknown_count) / n_bars

    # Balance: penalty for extreme dominance
    # Ideal: roughly equal distribution
    valid_labels = [l for l in unique_labels if l not in unknown_labels]
    if len(valid_labels) > 1:
        counts = regimes.value_counts()
        fractions = counts / n_bars
        ideal = 1.0 / len(valid_labels)
        deviations = abs(fractions - ideal)
        result.balance = 1.0 - float(deviations.mean() * 2)  # Penalty for imbalance
    else:
        result.balance = 0.5  # Single label, neutral

    result.normalized = (result.coverage + _clamp01(result.balance)) / 2.0

    return result


# =============================================================================
# Main Scoring Function
# =============================================================================


def calculate_regime_score(
    data: pd.DataFrame,
    regimes: pd.Series,
    features: Optional[pd.DataFrame] = None,
    config: Optional[RegimeScoreConfig] = None,
) -> RegimeScoreResult:
    """Calculate comprehensive regime quality score.

    Args:
        data: OHLCV DataFrame
        regimes: Series of regime labels (aligned with data index)
        features: Optional feature DataFrame for separability/boundary.
                  If None, basic features are calculated from data.
        config: Scoring configuration

    Returns:
        RegimeScoreResult with total score 0-100 and component breakdowns
    """
    if config is None:
        config = RegimeScoreConfig()

    result = RegimeScoreResult()

    # Determine effective start index
    start_idx = max(config.warmup_bars, config.max_feature_lookback)
    result.n_bars_excluded = start_idx

    # Slice data after warmup
    if len(data) <= start_idx:
        result.gates_passed = False
        result.gate_failures.append("insufficient_data_after_warmup")
        return result

    data_scored = data.iloc[start_idx:]

    # Align regimes to data index safely
    common_idx = data_scored.index.intersection(regimes.index)
    if len(common_idx) == 0:
        result.gates_passed = False
        result.gate_failures.append("no_common_index_between_data_and_regimes")
        return result

    data_scored = data_scored.loc[common_idx]
    regimes_scored = regimes.loc[common_idx]
    result.n_bars_scored = len(regimes_scored)

    # Build default features if not provided
    if features is None:
        features = _build_default_features(data)

    # Align features to common index and drop NaNs
    features_scored = features.reindex(common_idx)
    valid_idx = features_scored.dropna().index

    # Final alignment - all DataFrames/Series use valid_idx
    features_scored = features_scored.loc[valid_idx]
    regimes_scored = regimes_scored.reindex(valid_idx).dropna()
    data_scored = data_scored.reindex(valid_idx).dropna()

    # Ensure all have same index after cleanup
    final_idx = features_scored.index.intersection(regimes_scored.index).intersection(data_scored.index)
    features_scored = features_scored.loc[final_idx]
    regimes_scored = regimes_scored.loc[final_idx]
    data_scored = data_scored.loc[final_idx]

    if len(regimes_scored) < config.min_bars_for_scoring:
        result.gates_passed = False
        result.gate_failures.append(
            f"insufficient_bars_after_cleanup ({len(regimes_scored)} < {config.min_bars_for_scoring})"
        )
        return result

    # Standardize features
    scaler = RobustScaler()
    features_scaled = pd.DataFrame(
        scaler.fit_transform(features_scored),
        index=features_scored.index,
        columns=features_scored.columns,
    )

    labels = regimes_scored.values
    result.unique_labels = list(np.unique(labels))

    # === Gate Checks ===
    n_unique = len(result.unique_labels)
    if n_unique < config.min_unique_labels:
        result.gates_passed = False
        result.gate_failures.append(f"insufficient_label_diversity ({n_unique} < {config.min_unique_labels})")

    # Calculate coherence first (for gates)
    result.coherence = _calculate_coherence(regimes_scored, config)

    if result.coherence.switch_rate_per_1000 > config.max_switch_rate_per_1000:
        result.gates_passed = False
        result.gate_failures.append(f"switch_rate_too_high ({result.coherence.switch_rate_per_1000:.1f} > {config.max_switch_rate_per_1000})")

    if result.coherence.avg_duration_bars < config.min_avg_duration:
        result.gates_passed = False
        result.gate_failures.append(f"avg_duration_too_low ({result.coherence.avg_duration_bars:.1f} < {config.min_avg_duration})")

    # Count segments
    regime_changes = regimes_scored != regimes_scored.shift(1)
    n_segments = regime_changes.sum()
    if n_segments < config.min_segments:
        result.gates_passed = False
        result.gate_failures.append(f"insufficient_segments ({n_segments} < {config.min_segments})")

    # If gates failed, return early with zero score
    if not result.gates_passed:
        result.total_score = 0.0
        return result

    # === Calculate All Components ===
    result.separability = _calculate_separability(features_scaled, labels, config)
    # coherence already calculated above
    result.fidelity = _calculate_fidelity(data_scored, regimes_scored, config)
    result.boundary = _calculate_boundary(features_scaled, regimes_scored, config)
    result.coverage = _calculate_coverage(regimes_scored, config)

    # Coverage gate
    if result.coverage.coverage < config.min_coverage:
        result.gates_passed = False
        result.gate_failures.append(f"coverage_too_low ({result.coverage.coverage:.2f} < {config.min_coverage})")
        result.total_score = 0.0
        return result

    # === Calculate Composite Score ===
    composite = (
        config.w_separability * result.separability.normalized
        + config.w_coherence * result.coherence.normalized
        + config.w_fidelity * result.fidelity.normalized
        + config.w_boundary * result.boundary.normalized
        + config.w_coverage * result.coverage.normalized
    )

    result.total_score = _clamp01(composite) * 100.0

    return result


def _build_default_features(data: pd.DataFrame) -> pd.DataFrame:
    """Build default feature set from OHLCV data.

    Features:
    - ret_1: 1-bar return
    - ret_5: 5-bar return
    - atr_norm: ATR normalized by close
    - vol_z: Volume z-score
    - range_width: High-Low range normalized
    """
    close = data["close"]
    high = data["high"]
    low = data["low"]
    volume = data.get("volume", pd.Series(1, index=data.index))

    features = pd.DataFrame(index=data.index)

    # Returns
    features["ret_1"] = close.pct_change(1)
    features["ret_5"] = close.pct_change(5)

    # ATR normalized
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    features["atr_norm"] = atr / close

    # Volume z-score
    vol_mean = volume.rolling(20).mean()
    vol_std = volume.rolling(20).std()
    features["vol_z"] = (volume - vol_mean) / (vol_std + 1e-8)

    # Range width
    features["range_width"] = (high - low) / close

    return features
