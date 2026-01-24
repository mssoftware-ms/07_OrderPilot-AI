"""Load OptimParams from JSON config file.

This module bridges the gap between the JSON-based configuration
(used in Regime tab tables) and the OptimParams dataclass
(used by entry_signal_engine for Analyze Visible Range).

Fixes the architectural issue where "Analyze Visible Range" was
using hardcoded defaults instead of optimized parameters.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .entry_signal_engine import OptimParams

logger = logging.getLogger(__name__)


def load_optim_params_from_json(json_path: Path | str) -> OptimParams:
    """Load OptimParams from entry_analyzer_regime.json format.

    Falls JSON existiert und optimization_results hat, nutze die neuesten
    applied=true Parameter. Sonst nutze indicators direkt.

    Args:
        json_path: Pfad zur JSON-Datei

    Returns:
        OptimParams mit Werten aus JSON oder Defaults bei Fehler
    """
    json_path = Path(json_path) if isinstance(json_path, str) else json_path

    if not json_path.exists():
        logger.warning("JSON config not found: %s, using defaults", json_path)
        return OptimParams()

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load JSON config: %s", e)
        return OptimParams()

    # 1. Versuche optimization_results (neueste applied=true)
    opt_results = config.get("optimization_results", [])
    applied_results = [r for r in opt_results if r.get("applied", False)]

    if applied_results:
        # Neuestes Ergebnis (letztes in Liste)
        latest = applied_results[-1]
        params_dict = latest.get("params", {})
        logger.info(
            "Loading OptimParams from optimization_results (score=%.1f, trial=%d)",
            latest.get("score", 0),
            latest.get("trial_number", 0),
        )
        return _build_optim_params_from_opt_result(params_dict, config)

    # 2. Fallback: Nutze indicators direkt
    logger.info("No applied optimization results, using indicator defaults from JSON")
    return _build_optim_params_from_indicators(config)


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
