"""Regime Optimizer Calculations - Core Algorithms.

This module contains calculation functions extracted from regime_optimizer.py.
All functions accept optimizer instance as first parameter.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from datetime import datetime
import numpy as np
import pandas as pd
import optuna
from sklearn.metrics import f1_score

if TYPE_CHECKING:
    from .regime_optimizer_core import RegimeOptimizer

from .regime_optimizer_core import (
    RegimeParams,
    RegimeMetrics,
    OptimizationResult,
    RegimeType,
    ParamRange,
)
from src.core.scoring import calculate_regime_score, RegimeScoreConfig, RegimeScoreResult
from src.core.indicators.momentum import MomentumIndicators
from src.core.indicators.trend import TrendIndicators
from src.core.indicators.volatility import VolatilityIndicators

# Try to import talib
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

# Try to import pandas_ta
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False

logger = logging.getLogger(__name__)

def _suggest_params(optimizer: "RegimeOptimizer", trial: optuna.Trial) -> RegimeParams:
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
        optimizer.param_ranges.sma_fast is not None
        or optimizer.param_ranges.sma_slow is not None
        or optimizer.param_ranges.bb is not None
        or optimizer.param_ranges.adx.threshold is not None
    )

    # Always choose ADX period
    adx_period = suggest_from_range("adx_period", optimizer.param_ranges.adx.period, integer=True)

    if use_simple_mode:
        # Simple mode parameters (used by tests)
        threshold_rng = (
            optimizer.param_ranges.adx.threshold
            or optimizer.param_ranges.adx.trending_threshold
            or ParamRange(min=20, max=40, step=1)
        )
        adx_threshold = suggest_from_range("adx_threshold", threshold_rng, integer=False)

        # SMA periods
        sma_fast_rng = optimizer.param_ranges.sma_fast.period if optimizer.param_ranges.sma_fast else ParamRange(min=5, max=15, step=1)
        sma_slow_rng = optimizer.param_ranges.sma_slow.period if optimizer.param_ranges.sma_slow else ParamRange(min=20, max=50, step=1)
        sma_fast_period = suggest_from_range("sma_fast_period", sma_fast_rng, integer=True)
        sma_slow_period = suggest_from_range("sma_slow_period", sma_slow_rng, integer=True)

        # RSI
        rsi_period = suggest_from_range("rsi_period", optimizer.param_ranges.rsi.period, integer=True)
        if optimizer.param_ranges.rsi.sideways_low and optimizer.param_ranges.rsi.sideways_high:
            rsi_sideways_low = suggest_from_range("rsi_sideways_low", optimizer.param_ranges.rsi.sideways_low, integer=False)
            rsi_sideways_high = suggest_from_range("rsi_sideways_high", optimizer.param_ranges.rsi.sideways_high, integer=False)
        else:
            # Derive from strong_bear/bull or fallback defaults
            low_rng = optimizer.param_ranges.rsi.strong_bear or ParamRange(min=30, max=45, step=1)
            high_rng = optimizer.param_ranges.rsi.strong_bull or ParamRange(min=55, max=70, step=1)
            rsi_sideways_low = suggest_from_range("rsi_sideways_low", low_rng, integer=False)
            rsi_sideways_high = suggest_from_range("rsi_sideways_high", high_rng, integer=False)

        # Bollinger Bands
        if optimizer.param_ranges.bb:
            bb_period = suggest_from_range("bb_period", optimizer.param_ranges.bb.period, integer=True)
            bb_std_dev = suggest_from_range("bb_std_dev", optimizer.param_ranges.bb.std_dev, integer=False)
            bb_width_percentile = suggest_from_range("bb_width_percentile", optimizer.param_ranges.bb.width_percentile, integer=False)
        else:
            bb_period = 20
            bb_std_dev = 2.0
            bb_width_percentile = 30.0

        atr_period = None
        strong_move_pct = None
        extreme_move_pct = None
        if optimizer.param_ranges.atr:
            atr_period = suggest_from_range("atr_period", optimizer.param_ranges.atr.period, integer=True)
            strong_move_pct = suggest_from_range("strong_move_pct", optimizer.param_ranges.atr.strong_move_pct, integer=False)
            extreme_move_pct = suggest_from_range("extreme_move_pct", optimizer.param_ranges.atr.extreme_move_pct, integer=False)

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
    trending_rng = optimizer.param_ranges.adx.trending_threshold or optimizer.param_ranges.adx.threshold or ParamRange(min=20, max=35, step=1)
    weak_rng = optimizer.param_ranges.adx.weak_threshold or ParamRange(min=15, max=25, step=1)
    di_rng = optimizer.param_ranges.adx.di_diff_threshold or ParamRange(min=3, max=10, step=1)

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

    rsi_period = suggest_from_range("rsi_period", optimizer.param_ranges.rsi.period, integer=True)
    rsi_strong_bull = suggest_from_range(
        "rsi_strong_bull",
        optimizer.param_ranges.rsi.strong_bull or ParamRange(min=55, max=70, step=1),
        integer=False,
    )
    rsi_strong_bear = suggest_from_range(
        "rsi_strong_bear",
        optimizer.param_ranges.rsi.strong_bear or ParamRange(min=30, max=45, step=1),
        integer=False,
    )

    atr_period = suggest_from_range(
        "atr_period",
        optimizer.param_ranges.atr.period if optimizer.param_ranges.atr else ParamRange(min=10, max=20, step=1),
        integer=True,
    )
    strong_move_pct = suggest_from_range(
        "strong_move_pct",
        optimizer.param_ranges.atr.strong_move_pct if optimizer.param_ranges.atr else ParamRange(min=1.0, max=2.5, step=0.1),
        integer=False,
    )
    extreme_move_pct = suggest_from_range(
        "extreme_move_pct",
        optimizer.param_ranges.atr.extreme_move_pct if optimizer.param_ranges.atr else ParamRange(min=2.0, max=4.0, step=0.5),
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


def _calculate_indicators(optimizer: "RegimeOptimizer", params: RegimeParams) -> dict[str, pd.Series]:
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
    high = optimizer.data["high"]
    low = optimizer.data["low"]
    close = optimizer.data["close"]
    use_simple_mode = (
        params.sma_fast_period is not None
        and params.sma_slow_period is not None
        and params.adx_threshold is not None
    )

    # Calculate ADX, DI+, DI- using talib or pandas_ta
    if TALIB_AVAILABLE:
        indicators["adx"] = pd.Series(
            talib.ADX(high, low, close, timeperiod=params.adx_period),
            index=optimizer.data.index
        )
        indicators["plus_di"] = pd.Series(
            talib.PLUS_DI(high, low, close, timeperiod=params.adx_period),
            index=optimizer.data.index
        )
        indicators["minus_di"] = pd.Series(
            talib.MINUS_DI(high, low, close, timeperiod=params.adx_period),
            index=optimizer.data.index
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
        indicators["adx"] = pd.Series(25.0, index=optimizer.data.index)  # Neutral
        indicators["plus_di"] = pd.Series(25.0, index=optimizer.data.index)
        indicators["minus_di"] = pd.Series(25.0, index=optimizer.data.index)

    # RSI for direction confirmation
    if PANDAS_TA_AVAILABLE:
        indicators["rsi"] = ta.rsi(close, length=params.rsi_period)
    else:
        rsi_result = MomentumIndicators.calculate_rsi(
            optimizer.data, {"period": params.rsi_period}, use_talib=True
        )
        indicators["rsi"] = rsi_result.values

    # ATR for volatility-based strong move detection (optional in simple mode)
    if params.atr_period:
        atr_result = VolatilityIndicators.calculate_atr(
            optimizer.data, {"period": params.atr_period}, use_talib=True
        )
        indicators["atr"] = atr_result.values
        lookback = params.atr_period
    else:
        indicators["atr"] = pd.Series(index=optimizer.data.index, dtype=float)
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
                indicators["bb_width"] = pd.Series(index=optimizer.data.index, dtype=float)

    return indicators


def _classify_regimes(
    optimizer: "RegimeOptimizer",
    params: RegimeParams,
    indicators: dict[str, pd.Series],
) -> pd.Series:
    """Classify regimes using either simple SMA/ADX logic (tests) or legacy ADX/DI logic."""
    use_simple_mode = (
        params.adx_threshold is not None
        and "sma_fast" in indicators
        and "sma_slow" in indicators
    )

    regimes = pd.Series(RegimeType.SIDEWAYS.value, index=optimizer.data.index)

    if use_simple_mode:
        adx = indicators["adx"]
        sma_fast = indicators["sma_fast"]
        sma_slow = indicators["sma_slow"]
        close = optimizer.data["close"]
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


def _suggest_json_params(optimizer: "RegimeOptimizer", trial: optuna.Trial) -> None:
    """Suggest parameter values from JSON config using Optuna.

    Extracts all parameters with 'range' from JSON indicators and regimes,
    then uses Optuna trial to suggest values for each. Results are stored
    in optimizer._trial_params for use by _calculate_json_indicators() and
    _classify_regimes_json().

    Key format for _trial_params:
    - Indicator params: "{ind_name}.{param_name}" (e.g., "STRENGTH_ADX.period")
    - Regime thresholds: "{regime_id}.{thresh_name}" (e.g., "BULL.adx_min")

    Args:
        trial: Optuna trial for parameter suggestion
    """
    optimizer._trial_params.clear()

    # Ensure caches are populated
    if optimizer._json_indicators_cache is None:
        if not optimizer.json_config or "optimization_results" not in optimizer.json_config:
            return
        opt_results = optimizer.json_config["optimization_results"]
        applied = [r for r in opt_results if r.get('applied', False)]
        result = applied[-1] if applied else opt_results[0]
        optimizer._json_indicators_cache = result.get('indicators', [])
        optimizer._json_regimes_cache = result.get('regimes', [])
        optimizer._build_indicator_type_maps()

    # Suggest indicator parameters
    for ind in optimizer._json_indicators_cache:
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
                    optimizer._trial_params[key] = trial.suggest_int(
                        key, int(min_val), int(max_val), step=int(step)
                    )
                else:
                    optimizer._trial_params[key] = trial.suggest_float(
                        key, float(min_val), float(max_val), step=float(step)
                    )
            else:
                # No range - use fixed value from JSON
                optimizer._trial_params[key] = param_value

    # Suggest regime threshold parameters
    for regime in (optimizer._json_regimes_cache or []):
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
                    optimizer._trial_params[key] = trial.suggest_int(
                        key, int(min_val), int(max_val), step=int(step)
                    )
                else:
                    optimizer._trial_params[key] = trial.suggest_float(
                        key, float(min_val), float(max_val), step=float(step)
                    )
            else:
                # No range - use fixed value from JSON
                optimizer._trial_params[key] = thresh_value

    if trial.number == 0:
        logger.info(
            f"[JSON PARAMS] Suggested {len(optimizer._trial_params)} parameters "
            f"for trial 0: {list(optimizer._trial_params.keys())[:5]}..."
        )


def _calculate_json_indicators(
    optimizer: "RegimeOptimizer",
    params: RegimeParams,
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
    if optimizer._json_indicators_cache is None:
        if not optimizer.json_config or "optimization_results" not in optimizer.json_config:
            return {}
        opt_results = optimizer.json_config["optimization_results"]
        applied = [r for r in opt_results if r.get('applied', False)]
        result = applied[-1] if applied else opt_results[0]
        optimizer._json_indicators_cache = result.get('indicators', [])
        optimizer._json_regimes_cache = result.get('regimes', [])

        # Build dynamic type→name mappings
        optimizer._build_indicator_type_maps()

    indicators = {}
    high = optimizer.data["high"]
    low = optimizer.data["low"]
    close = optimizer.data["close"]

    # Calculate each indicator from JSON config
    for ind in optimizer._json_indicators_cache:
        name = ind['name']
        ind_type = ind['type'].upper()
        # Use trial-suggested params if available, else fallback to JSON values
        json_params = {
            p['name']: optimizer._get_json_param_value(name, p)
            for p in ind.get('params', [])
        }

        try:
            if ind_type == 'ADX':
                period = int(json_params.get('period', params.adx_period))
                if TALIB_AVAILABLE:
                    indicators[name] = pd.Series(
                        talib.ADX(high, low, close, timeperiod=period),
                        index=optimizer.data.index
                    )
                    # Store DI values with indicator name prefix for flexibility
                    indicators[f'{name}_PLUS_DI'] = pd.Series(
                        talib.PLUS_DI(high, low, close, timeperiod=period),
                        index=optimizer.data.index
                    )
                    indicators[f'{name}_MINUS_DI'] = pd.Series(
                        talib.MINUS_DI(high, low, close, timeperiod=period),
                        index=optimizer.data.index
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
                    indicators[name] = pd.Series(25.0, index=optimizer.data.index)
                    indicators[f'{name}_PLUS_DI'] = pd.Series(25.0, index=optimizer.data.index)
                    indicators[f'{name}_MINUS_DI'] = pd.Series(25.0, index=optimizer.data.index)

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

                result = optimizer._calculate_adx_leaf_west(
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

                result = optimizer._calculate_chandelier_stop(
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
                        optimizer.data, {"period": period}, use_talib=True
                    )
                    indicators[name] = rsi_result.values

            elif ind_type == 'ATR':
                period = int(json_params.get('period', params.atr_period or 14))
                atr_result = VolatilityIndicators.calculate_atr(
                    optimizer.data, {"period": period}, use_talib=True
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
                indicators[name] = pd.Series(np.nan, index=optimizer.data.index)

        except Exception as e:
            logger.error(f"Error calculating indicator {name} ({ind_type}): {e}")
            indicators[name] = pd.Series(np.nan, index=optimizer.data.index)

    # Always calculate price change percentage for extreme move detection
    indicators['PRICE_CHANGE_PCT'] = close.pct_change() * 100

    return indicators


def _classify_regimes_json(
    optimizer: "RegimeOptimizer",
    params: RegimeParams,
    indicators: dict[str, pd.Series],
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
    if not optimizer._json_regimes_cache:
        logger.warning("No JSON regimes configured, falling back to SIDEWAYS")
        return pd.Series("SIDEWAYS", index=optimizer.data.index)

    # Sort regimes by priority (highest first)
    sorted_regimes = sorted(
        optimizer._json_regimes_cache,
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
            value = optimizer._get_json_param_value(regime_id, thresh)

            # ===== Direction-based thresholds (Chandelier, etc.) =====
            if name.endswith('_direction_eq'):
                base = name[:-13]  # Remove '_direction_eq'
                ind_name = optimizer._resolve_indicator_name(base, '_DIRECTION')
                direction_val = get_indicator_value(ind_name, idx)
                if np.isnan(direction_val) or int(direction_val) != int(value):
                    return False
                continue

            if name.endswith('_color_change'):
                base = name[:-13]  # Remove '_color_change'
                ind_name = optimizer._resolve_indicator_name(base, '_COLOR_CHANGE')
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
                rsi_ind_name = optimizer._resolve_indicator_name('RSI')
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
                ind_name = optimizer._resolve_indicator_name(base)
                ind_val = get_indicator_value(ind_name, idx)
                if np.isnan(ind_val) or ind_val <= value:
                    return False
                continue

            if name.endswith('_below'):
                base = name[:-6]  # Remove '_below'
                ind_name = optimizer._resolve_indicator_name(base)
                ind_val = get_indicator_value(ind_name, idx)
                if np.isnan(ind_val) or ind_val >= value:
                    return False
                continue

            # ===== Standard _min/_max thresholds =====
            if name.endswith('_min'):
                base = name[:-4]
                ind_name = optimizer._resolve_indicator_name(base)
                ind_val = get_indicator_value(ind_name, idx)
                if np.isnan(ind_val) or ind_val < value:
                    return False
                continue

            if name.endswith('_max'):
                base = name[:-4]
                ind_name = optimizer._resolve_indicator_name(base)
                ind_val = get_indicator_value(ind_name, idx)
                if np.isnan(ind_val) or ind_val >= value:
                    return False
                continue

        return True  # All thresholds passed

    # Classify each bar (skip warmup bars)
    warmup = max(50, params.adx_period * 2)
    regimes = pd.Series(fallback_regime_id, index=optimizer.data.index)

    for i in range(warmup, len(optimizer.data)):
        for regime in sorted_regimes:
            if evaluate_regime_at(regime, i):
                regimes.iloc[i] = regime['id']
                break

    return regimes


def _calculate_metrics(optimizer: "RegimeOptimizer", regimes: pd.Series, params: RegimeParams) -> RegimeMetrics:
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
    if optimizer.ground_truth is not None:
        f1_bull = f1_score(
            optimizer.ground_truth == RegimeType.BULL.value,
            regimes == RegimeType.BULL.value,
            zero_division=0.0,
        )
        f1_bear = f1_score(
            optimizer.ground_truth == RegimeType.BEAR.value,
            regimes == RegimeType.BEAR.value,
            zero_division=0.0,
        )
        f1_sideways = f1_score(
            optimizer.ground_truth == RegimeType.SIDEWAYS.value,
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


def _calculate_composite_score(optimizer: "RegimeOptimizer", metrics: RegimeMetrics) -> float:
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


def _objective(optimizer: "RegimeOptimizer", trial: optuna.Trial) -> float:
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
        params = optimizer._suggest_params(trial)

        # Calculate indicators and classify regimes
        # Use JSON mode if json_config is provided
        if optimizer.json_config is not None:
            # JSON mode: Suggest params from JSON ranges using Optuna
            optimizer._suggest_json_params(trial)
            # Calculate indicators with trial-suggested params
            indicators = optimizer._calculate_json_indicators(params)
            # Classify using JSON per-regime thresholds
            regimes = optimizer._classify_regimes_json(params, indicators)

            if trial.number == 0:
                logger.info(
                    f"[JSON MODE] Using v2.0 config with {len(optimizer._json_regimes_cache or [])} regimes, "
                    f"{len(optimizer._json_indicators_cache or [])} indicators"
                )
        else:
            # Legacy mode: Use existing classification
            indicators = optimizer._calculate_indicators(params)
            regimes = optimizer._classify_regimes(params, indicators)

        # Convert regimes to Series for scoring
        regimes_series = pd.Series(regimes, index=optimizer.data.index)

        # Calculate new 5-component RegimeScore
        # Adaptive warmup/lookback: Scale with data size
        data_len = len(optimizer.data)

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
        if optimizer.json_config is not None:
            # Load weights from JSON evaluation_params.score_weights
            score_config = RegimeScoreConfig.from_json_config(optimizer.json_config)
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
            data=optimizer.data,
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



def create_objective_function(optimizer: "RegimeOptimizer"):
    """Factory to create Optuna objective function with access to optimizer.

    Args:
    optimizer: RegimeOptimizer instance

    Returns:
    Objective function for Optuna optimization
    """
    def objective_wrapper(trial: optuna.Trial) -> float:
        return _objective(optimizer, trial)
    return objective_wrapper

def _extract_results(optimizer: "RegimeOptimizer") -> list[OptimizationResult]:
    """Extract results from study.

    Returns:
        List of optimization results sorted by score
    """
    if optimizer._study is None:
        return []

    results = []

    for rank, trial in enumerate(
        sorted(optimizer._study.trials, key=lambda t: t.value or 0.0, reverse=True), start=1
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
        if optimizer.json_config is not None:
            # JSON mode: Reload trial's JSON params
            optimizer._load_trial_params(trial)
            indicators = optimizer._calculate_json_indicators(params)
            regimes = optimizer._classify_regimes_json(params, indicators)
        else:
            # Legacy mode
            indicators = optimizer._calculate_indicators(params)
            regimes = optimizer._classify_regimes(params, indicators)
        metrics = optimizer._calculate_metrics(regimes, params)

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
        if optimizer.json_config is not None:
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



def extract_results(optimizer: "RegimeOptimizer") -> list[OptimizationResult]:
    """Extract results from optimizer study.

    Args:
    optimizer: RegimeOptimizer instance

    Returns:
    List of optimization results sorted by score
    """
    return _extract_results(optimizer)
