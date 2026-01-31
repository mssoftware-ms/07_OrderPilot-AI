"""Regime Detection Module for Entry Signal Engine.

This module handles market regime classification and detection:
- Legacy regime detection (detect_regime)
- Dynamic JSON-based regime detection (detect_regime_v2)
- Helper functions for regime classification
- Threshold evaluation logic

Extracted from entry_signal_engine.py for better modularity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entry_signal_engine_core import OptimParams, RegimeType


def detect_regime(features: dict[str, list[float]], params: "OptimParams") -> "RegimeType":
    """Detect market regime from features.

    Uses ADX, BB width, and ATR% to classify the market state.
    Designed to avoid NO_TRADE unless data is insufficient.

    Args:
        features: Calculated features.
        params: Regime thresholds.

    Returns:
        Detected regime type.
    """
    # Import here to avoid circular dependency
    from .entry_signal_engine_core import RegimeType

    if not features or "closes" not in features:
        return RegimeType.NO_TRADE

    closes = features["closes"]
    if len(closes) < 30:
        return RegimeType.NO_TRADE

    adx = features.get("adx", [])
    bb_width = features.get("bb_width", [])
    atr_pct = features.get("atr_pct", [])
    ema_fast = features.get("ema_fast", [])
    ema_slow = features.get("ema_slow", [])

    i = len(closes) - 1
    a = adx[i] if i < len(adx) else 0.0
    bw = bb_width[i] if i < len(bb_width) else 0.0
    av = atr_pct[i] if i < len(atr_pct) else 0.0

    trend_dir = 0.0
    if i < len(ema_fast) and i < len(ema_slow):
        trend_dir = ema_fast[i] - ema_slow[i]

    if av >= params.high_vol_atr_pct:
        return RegimeType.HIGH_VOL

    # Squeeze: narrow bands + weak trend
    if bw <= params.squeeze_bb_width and a < params.adx_trend:
        return RegimeType.SQUEEZE

    if a >= params.adx_trend:
        if trend_dir >= 0:
            return RegimeType.TREND_UP
        return RegimeType.TREND_DOWN

    return RegimeType.RANGE


def detect_regime_v2(
    features: dict[str, list[float]],
    regime_config: dict | list,
) -> str:
    """Detect market regime dynamically from JSON config.

    Evaluates regimes sorted by priority (descending).
    Returns the first regime where ALL thresholds match.

    Threshold naming patterns (dynamic, case-insensitive):
    - `*_min` → feature value >= threshold (minimum required)
    - `*_max` → feature value <= threshold (maximum allowed)
    - `adx_*` → uses ADX value
    - `di_diff_*` → uses abs(DI+ - DI-)
    - `rsi_*` → uses RSI value
    - `*_bull` suffix → for bullish regimes (DI+ > DI-)
    - `*_bear` suffix → for bearish regimes (DI- > DI+)

    Args:
        features: Calculated features dict (must include adx, di_plus, di_minus, rsi).
        regime_config: Either a list of regime dicts OR a full v2.0 config dict.

    Returns:
        Matched regime ID (e.g., "STRONG_TF", "BULL", "SIDEWAYS") or "UNKNOWN".
    """
    if not features:
        return "UNKNOWN"

    # Extract regimes from config
    regimes = _extract_regimes_from_config(regime_config)
    if not regimes:
        return "UNKNOWN"

    # Sort by priority (descending - highest first)
    regimes_sorted = sorted(regimes, key=lambda r: r.get("priority", 0), reverse=True)

    # Get current feature values (last index)
    i = len(features.get("closes", [])) - 1
    if i < 0:
        return "UNKNOWN"

    adx = features.get("adx", [0.0])
    di_plus = features.get("di_plus", [0.0])
    di_minus = features.get("di_minus", [0.0])
    rsi = features.get("rsi", [50.0])

    current_adx = adx[i] if i < len(adx) else 0.0
    current_di_plus = di_plus[i] if i < len(di_plus) else 0.0
    current_di_minus = di_minus[i] if i < len(di_minus) else 0.0
    current_rsi = rsi[i] if i < len(rsi) else 50.0
    current_di_diff = abs(current_di_plus - current_di_minus)

    # Build feature lookup for dynamic threshold evaluation
    feature_values = {
        "adx": current_adx,
        "di_plus": current_di_plus,
        "di_minus": current_di_minus,
        "di_diff": current_di_diff,
        "rsi": current_rsi,
    }

    # Evaluate each regime
    for regime in regimes_sorted:
        regime_id = regime.get("id", "")
        thresholds = regime.get("thresholds", [])

        if not thresholds:
            # Regime without thresholds - skip (or could be fallback)
            continue

        # Check if this is a bullish or bearish regime (for DI direction check)
        is_bull_regime = _is_bullish_regime(regime_id)
        is_bear_regime = _is_bearish_regime(regime_id)

        # For directional regimes, check DI direction first
        if is_bull_regime and current_di_plus <= current_di_minus:
            continue  # Skip bullish regime if DI- > DI+
        if is_bear_regime and current_di_minus <= current_di_plus:
            continue  # Skip bearish regime if DI+ > DI-

        # Evaluate all thresholds
        all_match = True
        for threshold in thresholds:
            threshold_name = threshold.get("name", "").lower()
            threshold_value = threshold.get("value", 0)

            if not _evaluate_threshold(threshold_name, threshold_value, feature_values):
                all_match = False
                break

        if all_match:
            return regime_id

    # No regime matched - return fallback
    return "SIDEWAYS"


def _extract_regimes_from_config(config: dict | list) -> list[dict]:
    """Extract regimes list from config (supports multiple formats).

    Args:
        config: Either a list of regimes OR a full v2.0 config dict.

    Returns:
        List of regime dicts with id, thresholds, priority.
    """
    # Already a list of regimes
    if isinstance(config, list):
        return config

    # v2.0 format: optimization_results[].regimes[]
    if isinstance(config, dict):
        opt_results = config.get("optimization_results", [])
        if opt_results:
            # Get applied result (or first)
            applied = [r for r in opt_results if r.get("applied", False)]
            result = applied[-1] if applied else opt_results[0]
            return result.get("regimes", [])

        # Direct regimes key
        return config.get("regimes", [])

    return []


def _is_bullish_regime(regime_id: str) -> bool:
    """Check if regime is bullish based on ID (dynamic pattern matching).

    Args:
        regime_id: Regime identifier string.

    Returns:
        True if regime is bullish.
    """
    id_lower = regime_id.lower()
    # Bullish patterns: contains 'bull' but not 'bear'
    if "bull" in id_lower and "bear" not in id_lower:
        return True
    # Also: 'long', 'up', 'aufwärts' (German)
    if any(pat in id_lower for pat in ["long", "_up", "aufwaerts", "aufwärts"]):
        return True
    return False


def _is_bearish_regime(regime_id: str) -> bool:
    """Check if regime is bearish based on ID (dynamic pattern matching).

    Args:
        regime_id: Regime identifier string.

    Returns:
        True if regime is bearish.
    """
    id_lower = regime_id.lower()
    # Bearish patterns: contains 'bear' but not 'bull'
    if "bear" in id_lower and "bull" not in id_lower:
        return True
    # Also: 'short', 'down', 'abwärts' (German)
    if any(pat in id_lower for pat in ["short", "_down", "abwaerts", "abwärts"]):
        return True
    return False


def _evaluate_threshold(
    threshold_name: str,
    threshold_value: float,
    feature_values: dict[str, float],
) -> bool:
    """Evaluate a single threshold dynamically based on naming pattern.

    Naming conventions:
    - `adx_min` → ADX >= value
    - `adx_max` → ADX <= value
    - `di_diff_min` → DI diff >= value
    - `rsi_confirm_bull` → RSI > value (for bullish confirmation)
    - `rsi_confirm_bear` → RSI < value (for bearish confirmation)
    - `rsi_exhaustion_max` → RSI < value (bull exhaustion = RSI dropping)
    - `rsi_exhaustion_min` → RSI > value (bear exhaustion = RSI rising)
    - `rsi_oversold` → RSI <= value
    - `rsi_overbought` → RSI >= value

    Args:
        threshold_name: Name of threshold (e.g., "adx_min").
        threshold_value: Threshold value from JSON.
        feature_values: Current feature values dict.

    Returns:
        True if threshold condition is met.
    """
    name = threshold_name.lower()

    # Determine which feature to use
    if "adx" in name:
        feature_val = feature_values.get("adx", 0.0)
    elif "di_diff" in name or "didiff" in name:
        feature_val = feature_values.get("di_diff", 0.0)
    elif "di_plus" in name:
        feature_val = feature_values.get("di_plus", 0.0)
    elif "di_minus" in name:
        feature_val = feature_values.get("di_minus", 0.0)
    elif "rsi" in name:
        feature_val = feature_values.get("rsi", 50.0)
    else:
        # Unknown feature - default to passing
        return True

    # Determine comparison operator based on suffix/pattern
    # RSI special cases (semantic meaning)
    if "rsi" in name:
        if "confirm_bull" in name or "bull" in name:
            # Bullish confirmation: RSI should be HIGH (> threshold)
            return feature_val > threshold_value
        if "confirm_bear" in name or "bear" in name:
            # Bearish confirmation: RSI should be LOW (< threshold)
            return feature_val < threshold_value
        if "exhaustion_max" in name:
            # Bull exhaustion: RSI is dropping (< threshold = exhausted)
            return feature_val < threshold_value
        if "exhaustion_min" in name:
            # Bear exhaustion: RSI is rising (> threshold = exhausted)
            return feature_val > threshold_value
        if "oversold" in name:
            return feature_val <= threshold_value
        if "overbought" in name:
            return feature_val >= threshold_value

    # Generic _min / _max suffix
    if name.endswith("_min") or "_min_" in name:
        return feature_val >= threshold_value
    if name.endswith("_max") or "_max_" in name:
        return feature_val <= threshold_value

    # Default: treat as minimum (>=)
    return feature_val >= threshold_value
