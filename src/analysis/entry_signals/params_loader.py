"""Load OptimParams from JSON config file (v2.0 format support).

This module bridges the gap between the JSON-based configuration
(used in Regime tab tables) and the OptimParams dataclass
(used by entry_signal_engine for Analyze Visible Range).

v2.0 Update:
- Supports new v2.0 format with optimization_results[].indicators[]
- Uses RegimeConfigLoaderV2 for proper v2.0 loading
- Builds flattened params from nested v2.0 structure
- Maintains backward compatibility with v1.0 root-level indicators[]

Fixes the architectural issue where "Analyze Visible Range" was
using hardcoded defaults instead of optimized parameters.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .entry_signal_engine import OptimParams

logger = logging.getLogger(__name__)


def load_optim_params_from_json(json_path: Path | str) -> OptimParams:
    """Load OptimParams from entry_analyzer_regime.json format (v2.0 support).

    Supports both v2.0 and v1.0 formats:
    - v2.0: optimization_results[].indicators[] (nested params array)
    - v1.0: root-level indicators[] (fallback)

    Args:
        json_path: Pfad zur JSON-Datei

    Returns:
        OptimParams mit Werten aus JSON oder Defaults bei Fehler
    """
    json_path = Path(json_path) if isinstance(json_path, str) else json_path

    if not json_path.exists():
        logger.warning("JSON config not found: %s, using defaults", json_path)
        return OptimParams()

    # Try to load with RegimeConfigLoaderV2 (v2.0 format)
    try:
        from src.core.tradingbot.config.regime_loader_v2 import (
            RegimeConfigLoaderV2,
            RegimeConfigLoadError,
        )

        loader = RegimeConfigLoaderV2()
        config = loader.load_config(json_path)

        # Get applied result from v2.0 format
        applied = loader.get_applied_result(config)
        if applied:
            indicators = applied.get("indicators", [])
            regimes = applied.get("regimes", [])

            # Build flattened params from v2.0 nested structure
            flattened_params = _flatten_v2_params(indicators, regimes)

            logger.info(
                "Loading OptimParams from v2.0 format (score=%.1f, trial=%d)",
                applied.get("score", 0),
                applied.get("trial_number", 0),
            )
            return _build_optim_params_from_opt_result(flattened_params, config)

        # No applied result in v2.0 format
        logger.info("No applied optimization results in v2.0 format, using defaults")
        return OptimParams()

    except (RegimeConfigLoadError, Exception) as e:
        # v2.0 loading failed, try v1.0 fallback
        logger.debug("v2.0 loading failed (%s), trying v1.0 fallback", e)

    # Fallback: Try v1.0 format (root-level indicators[])
    try:
        import json

        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Check for old v1.0 format with root-level indicators
        if "indicators" in config:
            logger.info("Loading OptimParams from v1.0 format (root-level indicators)")
            return _build_optim_params_from_indicators(config)

        # No valid format found
        logger.warning("No valid format found in %s, using defaults", json_path)
        return OptimParams()

    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load JSON config: %s, using defaults", e)
        return OptimParams()


def _flatten_v2_params(indicators: list[dict], regimes: list[dict]) -> dict[str, Any]:
    """Flatten v2.0 nested params structure to v1.0 flattened format.

    Converts:
        indicators: [{name: "ADX1", type: "ADX", params: [{name: "period", value: 14}]}]
        regimes: [{id: "BULL", thresholds: [{name: "adx_threshold", value: 25}]}]

    To:
        {"adx.period": 14, "BULL.adx_threshold": 25}

    This allows using the existing _build_optim_params_from_opt_result() logic.

    Args:
        indicators: List of indicator dicts from v2.0 format
        regimes: List of regime dicts from v2.0 format

    Returns:
        Flattened params dict compatible with v1.0 format
    """
    flattened = {}

    # Flatten indicator params
    for ind in indicators:
        ind_name = ind.get("name", "")
        ind_type = ind.get("type", "")

        # Map v2.0 indicator names to v1.0 IDs
        # v2.0: "TREND_FILTER", "STRENGTH_ADX" → v1.0: "sma_fast", "adx"
        ind_id = _map_v2_indicator_name_to_v1_id(ind_name, ind_type)

        for param in ind.get("params", []):
            param_name = param.get("name")
            param_value = param.get("value")

            if param_name and param_value is not None:
                key = f"{ind_id}.{param_name}"
                flattened[key] = param_value

    # Flatten regime thresholds
    for regime in regimes:
        regime_id = regime.get("id", "")

        for threshold in regime.get("thresholds", []):
            threshold_name = threshold.get("name")
            threshold_value = threshold.get("value")

            if threshold_name and threshold_value is not None:
                key = f"{regime_id}.{threshold_name}"
                flattened[key] = threshold_value

    logger.debug("Flattened v2.0 params: %s", flattened)
    return flattened


def _map_v2_indicator_name_to_v1_id(name: str, ind_type: str) -> str:
    """Map v2.0 indicator name to v1.0 indicator ID.

    v2.0 names are generic (e.g., "TREND_FILTER", "STRENGTH_ADX").
    v1.0 IDs are specific (e.g., "sma_fast", "adx", "rsi").

    This mapping uses indicator type + common naming patterns.

    Args:
        name: v2.0 indicator name (e.g., "TREND_FILTER")
        ind_type: Indicator type (e.g., "EMA", "ADX", "RSI")

    Returns:
        v1.0 indicator ID (e.g., "sma_fast", "adx")
    """
    # Direct type-based mapping (most common)
    type_map = {
        "ADX": "adx",
        "RSI": "rsi",
        "BB": "bb",
        "ATR": "atr14",
        "MACD": "macd",
    }

    # If type is in map, use it directly
    if ind_type in type_map:
        return type_map[ind_type]

    # For EMA/SMA, check if it's fast or slow based on name
    if ind_type in ("EMA", "SMA"):
        name_lower = name.lower()
        if "fast" in name_lower or "trend" in name_lower or "filter" in name_lower:
            return "sma_fast"
        elif "slow" in name_lower:
            return "sma_slow"
        else:
            # Default to sma_fast if unclear
            return "sma_fast"

    # Fallback: Use lowercase type
    return ind_type.lower()


def _build_optim_params_from_opt_result(params: dict, config: dict) -> OptimParams:
    """Build OptimParams from optimization_results.params.

    Mapping:
        JSON key                    -> OptimParams field
        sma_fast.period            -> ema_fast
        sma_slow.period            -> ema_slow
        atr14.period               -> atr_period
        rsi.period               -> rsi_period
        bb.period                -> bb_period
        bb.std_dev               -> bb_std
        adx.period               -> adx_period
        BULL.adx_threshold         -> adx_trend
        SIDEWAYS.rsi_low           -> rsi_oversold
        SIDEWAYS.rsi_high          -> rsi_overbought
        bb.width_percentile      -> squeeze_bb_width (converted)

    Args:
        params: Dict from optimization_results[].params
        config: Full config dict (for entry_params section)

    Returns:
        OptimParams instance
    """
    defaults = OptimParams()

    # Helper zum sicheren Auslesen
    def get_param(key: str, default: Any) -> Any:
        return params.get(key, default)

    # Entry params aus config (falls vorhanden)
    entry_params = _get_entry_params(config)

    return OptimParams(
        # Indicator periods aus optimization_results
        ema_fast=int(get_param("sma_fast.period", defaults.ema_fast)),
        ema_slow=int(get_param("sma_slow.period", defaults.ema_slow)),
        atr_period=int(get_param("atr14.period", defaults.atr_period)),
        rsi_period=int(get_param("rsi.period", defaults.rsi_period)),
        bb_period=int(get_param("bb.period", defaults.bb_period)),
        bb_std=float(get_param("bb.std_dev", defaults.bb_std)),
        adx_period=int(get_param("adx.period", defaults.adx_period)),
        # Regime thresholds aus optimization_results
        adx_trend=float(get_param("BULL.adx_threshold", defaults.adx_trend)),
        # RSI thresholds
        rsi_oversold=float(get_param("SIDEWAYS.rsi_low", defaults.rsi_oversold)),
        rsi_overbought=float(get_param("SIDEWAYS.rsi_high", defaults.rsi_overbought)),
        # BB width percentile -> squeeze threshold (convert percentile to ratio)
        squeeze_bb_width=_convert_bb_width_percentile(
            get_param("bb.width_percentile", None), defaults.squeeze_bb_width
        ),
        # Entry params (from entry_params section or defaults)
        pullback_atr=float(entry_params.get("pullback_atr", defaults.pullback_atr)),
        pullback_rsi=float(entry_params.get("pullback_rsi", defaults.pullback_rsi)),
        wick_reject=float(entry_params.get("wick_reject", defaults.wick_reject)),
        bb_entry=float(entry_params.get("bb_entry", defaults.bb_entry)),
        high_vol_atr_pct=float(
            entry_params.get("high_vol_atr_pct", defaults.high_vol_atr_pct)
        ),
        vol_spike_factor=float(
            entry_params.get("vol_spike_factor", defaults.vol_spike_factor)
        ),
        breakout_atr=float(entry_params.get("breakout_atr", defaults.breakout_atr)),
        min_confidence=float(
            entry_params.get("min_confidence", defaults.min_confidence)
        ),
        cooldown_bars=int(entry_params.get("cooldown_bars", defaults.cooldown_bars)),
        cluster_window_bars=int(
            entry_params.get("cluster_window_bars", defaults.cluster_window_bars)
        ),
        # Evaluation params
        eval_horizon_bars=int(
            entry_params.get("eval_horizon_bars", defaults.eval_horizon_bars)
        ),
        eval_tp_atr=float(entry_params.get("eval_tp_atr", defaults.eval_tp_atr)),
        eval_sl_atr=float(entry_params.get("eval_sl_atr", defaults.eval_sl_atr)),
        min_trades_gate=int(
            entry_params.get("min_trades_gate", defaults.min_trades_gate)
        ),
        target_trades_soft=int(
            entry_params.get("target_trades_soft", defaults.target_trades_soft)
        ),
    )


def _build_optim_params_from_indicators(config: dict) -> OptimParams:
    """Build OptimParams from indicators array.

    Used as fallback when no optimization_results are available.

    Args:
        config: Full config dict

    Returns:
        OptimParams instance
    """
    defaults = OptimParams()
    indicators = {ind["id"]: ind for ind in config.get("indicators", [])}

    def get_indicator_param(ind_id: str, param: str, default: Any) -> Any:
        ind = indicators.get(ind_id, {})
        return ind.get("params", {}).get(param, default)

    entry_params = _get_entry_params(config)

    return OptimParams(
        atr_period=int(get_indicator_param("atr14", "period", defaults.atr_period)),
        rsi_period=int(get_indicator_param("rsi", "period", defaults.rsi_period)),
        bb_period=int(get_indicator_param("bb", "period", defaults.bb_period)),
        bb_std=float(get_indicator_param("bb", "std_dev", defaults.bb_std)),
        adx_period=int(get_indicator_param("adx14", "period", defaults.adx_period)),
        # EMA from ema_fast/ema_slow indicators if present
        ema_fast=int(
            get_indicator_param("ema_fast", "period", defaults.ema_fast)
        ),
        ema_slow=int(
            get_indicator_param("ema_slow", "period", defaults.ema_slow)
        ),
        # Entry params
        pullback_atr=float(entry_params.get("pullback_atr", defaults.pullback_atr)),
        pullback_rsi=float(entry_params.get("pullback_rsi", defaults.pullback_rsi)),
        wick_reject=float(entry_params.get("wick_reject", defaults.wick_reject)),
        bb_entry=float(entry_params.get("bb_entry", defaults.bb_entry)),
        rsi_oversold=float(entry_params.get("rsi_oversold", defaults.rsi_oversold)),
        rsi_overbought=float(
            entry_params.get("rsi_overbought", defaults.rsi_overbought)
        ),
        min_confidence=float(
            entry_params.get("min_confidence", defaults.min_confidence)
        ),
        cooldown_bars=int(entry_params.get("cooldown_bars", defaults.cooldown_bars)),
        cluster_window_bars=int(
            entry_params.get("cluster_window_bars", defaults.cluster_window_bars)
        ),
    )


def _get_entry_params(config: dict) -> dict:
    """Extract entry_params from config.

    Also checks for evaluation_params section.

    Args:
        config: Full config dict

    Returns:
        Dict with entry parameters (excluding keys starting with '_')
    """
    result = {}

    # Get entry_params section
    entry = config.get("entry_params", {})
    for k, v in entry.items():
        if not k.startswith("_"):
            result[k] = v

    # Also get evaluation_params if present
    evaluation = config.get("evaluation_params", {})
    for k, v in evaluation.items():
        if not k.startswith("_"):
            result[k] = v

    return result


def _convert_bb_width_percentile(
    percentile: float | None, default: float
) -> float:
    """Convert BB width percentile (0-100) to squeeze ratio.

    The optimization stores bb_width_percentile as 0-100 range.
    The OptimParams squeeze_bb_width expects a ratio (e.g., 0.012).

    Approximate conversion: lower percentile = tighter squeeze.

    Args:
        percentile: BB width percentile from optimization (0-100)
        default: Default squeeze_bb_width if percentile is None

    Returns:
        squeeze_bb_width ratio
    """
    if percentile is None:
        return default

    # Rough conversion: percentile 20 ≈ 0.012, percentile 50 ≈ 0.025
    # This is an approximation; actual values depend on market conditions
    return 0.006 + (float(percentile) / 100.0) * 0.02


def get_default_json_path() -> Path:
    """Get the default path for entry_analyzer_regime.json.

    Returns:
        Path to the default JSON config file
    """
    # Try relative to project root
    candidates = [
        Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json"),
        Path("../../../03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    # Return first candidate even if it doesn't exist
    return candidates[0]
