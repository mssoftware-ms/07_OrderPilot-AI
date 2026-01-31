"""Core Entry Signal Engine Module.

This module contains:
- Type definitions (RegimeType, EntrySide, EntryEvent, OptimParams)
- Feature calculation (calculate_features)
- Entry generation (generate_entries, postprocessing)
- Debug utilities

Delegates to:
- entry_signal_engine_indicators.py for technical indicators
- entry_signal_engine_regime.py for regime detection
- generators/ for regime-specific entry logic
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .entry_signal_engine_indicators import (
    _adx_full,
    _atr,
    _bollinger,
    _ema,
    _pivots,
    _rsi,
    _safe_float,
    _sma,
    _wick_ratios,
)

logger = logging.getLogger(__name__)

# Lazy-initialized registry (singleton)
_ENTRY_REGISTRY = None


# --- Type Definitions ---


class RegimeType(str, Enum):
    """Market regime classification (unified v2.0 naming).

    - BULL: Bullish trend (was TREND_UP)
    - BEAR: Bearish trend (was TREND_DOWN)
    - SIDEWAYS: Range/neutral (was RANGE)
    """

    NO_TRADE = "NO_TRADE"
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    SQUEEZE = "SQUEEZE"
    HIGH_VOL = "HIGH_VOL"

    # Legacy aliases
    TREND_UP = "BULL"
    TREND_DOWN = "BEAR"
    RANGE = "SIDEWAYS"


class EntrySide(str, Enum):
    """Entry direction (compatible with existing types)."""

    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class EntryEvent:
    """A detected entry signal.

    Attributes:
        timestamp: Unix timestamp of the candle.
        side: LONG (green) or SHORT (red).
        confidence: Score 0.0-1.0 indicating signal strength.
        price: Price at entry point.
        reason_tags: List of reasons for the signal.
        regime: Market regime at the time of signal.
    """

    timestamp: Any
    side: EntrySide
    confidence: float
    price: float
    reason_tags: list[str]
    regime: RegimeType

    def to_chart_marker(self) -> dict[str, Any]:
        """Convert to TradingView Lightweight Charts marker format.

        Returns:
            Dict with time, position, color, shape, text for chart rendering.
        """
        is_long = self.side == EntrySide.LONG

        return {
            "time": self.timestamp,
            "position": "belowBar" if is_long else "aboveBar",
            "color": "#22c55e" if is_long else "#ef4444",  # green / red
            "shape": "arrowUp" if is_long else "arrowDown",
            "text": f"{self.side.value.upper()} ({self.confidence:.0%})",
            "size": 2,
        }


@dataclass
class OptimParams:
    """Optimizable parameters for the entry signal engine.

    All thresholds are designed for ATR-normalized scales, not percentages.
    """

    # Core indicator periods
    ema_fast: int = 20
    ema_slow: int = 50
    atr_period: int = 14
    rsi_period: int = 14
    bb_period: int = 20
    bb_std: float = 2.0
    adx_period: int = 14

    # Regime thresholds
    adx_trend: float = 18.0
    squeeze_bb_width: float = 0.012  # relative width
    high_vol_atr_pct: float = 0.012  # atr/close

    # Entry thresholds (ATR-normalized)
    pullback_atr: float = 0.8  # how far against trend is acceptable (in ATR units)
    pullback_rsi: float = 45.0  # long pullback rsi in uptrend / short pullback in downtrend
    wick_reject: float = 0.55  # wick ratio threshold for rejection confirmation
    bb_entry: float = 0.15  # BB% entry extreme (0..1)
    rsi_oversold: float = 35.0
    rsi_overbought: float = 65.0

    # Squeeze breakout confirmation
    vol_spike_factor: float = 1.2  # volume / vol_sma
    breakout_atr: float = 0.2  # require close to exceed band by x*ATR

    # Postprocessing
    min_confidence: float = 0.58
    cooldown_bars: int = 10  # min distance between same-side entries
    cluster_window_bars: int = 6  # within window keep best

    # Evaluation (optimizer objective)
    eval_horizon_bars: int = 40
    eval_tp_atr: float = 1.0
    eval_sl_atr: float = 0.8
    min_trades_gate: int = 8
    target_trades_soft: int = 30  # soft target for signal rate in visible window


# --- Feature Calculation ---


def calculate_features(candles: list[dict[str, Any]], params: OptimParams) -> dict[str, list[float]]:
    """Calculate technical features from candles.

    Uses ATR-normalized distances instead of percentage-based thresholds.
    This fixes the scale issue for 1m/5m timeframes.

    Args:
        candles: List of OHLCV candles.
        params: Indicator parameters.

    Returns:
        Dictionary of feature arrays.
    """
    if not candles:
        return {}

    closes = [_safe_float(c.get("close")) for c in candles]
    highs = [_safe_float(c.get("high")) for c in candles]
    lows = [_safe_float(c.get("low")) for c in candles]
    vols = [_safe_float(c.get("volume", 0.0)) for c in candles]

    ema_fast = _ema(closes, max(2, params.ema_fast))
    ema_slow = _ema(closes, max(2, params.ema_slow))
    atr = _atr(highs, lows, closes, max(2, params.atr_period))
    rsi = _rsi(closes, max(2, params.rsi_period))
    bb_mid, bb_up, bb_lo, bb_width, bbp = _bollinger(closes, max(2, params.bb_period), params.bb_std)
    adx, di_plus, di_minus = _adx_full(highs, lows, closes, max(2, params.adx_period))
    vol_sma = _sma(vols, max(2, params.bb_period))
    up_wick, lo_wick = _wick_ratios(candles)
    piv_h, piv_l = _pivots(highs, lows, lookback=max(2, int(params.bb_period / 2)))

    # ATR-normalized distance to slow EMA (fixes your scale issue)
    dist_ema_atr = []
    atr_pct = []
    for i in range(len(closes)):
        a = max(1e-12, atr[i])
        dist_ema_atr.append((closes[i] - ema_slow[i]) / a)
        if closes[i] != 0:
            atr_pct.append(atr[i] / closes[i])
        else:
            atr_pct.append(0.0)

    return {
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "volume": vols,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "atr": atr,
        "atr_pct": atr_pct,
        "rsi": rsi,
        "bb_mid": bb_mid,
        "bb_up": bb_up,
        "bb_lo": bb_lo,
        "bb_width": bb_width,
        "bb_percent": bbp,
        "adx": adx,
        "di_plus": di_plus,
        "di_minus": di_minus,
        "vol_sma": vol_sma,
        "up_wick": up_wick,
        "lo_wick": lo_wick,
        "pivot_high": [1.0 if x else 0.0 for x in piv_h],
        "pivot_low": [1.0 if x else 0.0 for x in piv_l],
        "dist_ema_atr": dist_ema_atr,
    }


# --- Entry Registry Initialization ---


def _init_entry_registry():
    """Initialize entry generator registry (singleton pattern)."""
    global _ENTRY_REGISTRY
    if _ENTRY_REGISTRY is None:
        from .generators import (
            EntryGeneratorRegistry,
            HighVolGenerator,
            RangeGenerator,
            SqueezeGenerator,
            TrendDownGenerator,
            TrendUpGenerator,
        )

        _ENTRY_REGISTRY = EntryGeneratorRegistry()
        _ENTRY_REGISTRY.register(TrendUpGenerator())
        _ENTRY_REGISTRY.register(TrendDownGenerator())
        _ENTRY_REGISTRY.register(RangeGenerator())
        _ENTRY_REGISTRY.register(SqueezeGenerator())
        _ENTRY_REGISTRY.register(HighVolGenerator())
    return _ENTRY_REGISTRY


# --- Entry Generation ---


def generate_entries(
    candles: list[dict[str, Any]],
    features: dict[str, list[float]],
    regime: RegimeType,
    params: OptimParams,
) -> list[EntryEvent]:
    """Generate entry signals using Rule Type Pattern.

    Delegates to specialized generators based on regime type:
    - TREND_UP/DOWN: Pullback entries with ATR-normalized distance
    - RANGE: Mean-reversion at BB extremes
    - SQUEEZE: Breakout confirmation with volume spike
    - HIGH_VOL: Only extreme signals

    Args:
        candles: OHLCV candles.
        features: Calculated features.
        regime: Detected regime.
        params: Entry thresholds.

    Returns:
        List of entry events.
    """
    if not candles or not features:
        return []

    # Initialize registry on first use
    registry = _init_entry_registry()

    # Generate raw entries using regime-specific generator
    raw = registry.generate(candles, features, regime, params)

    # Apply postprocessing (cooldown, clustering)
    return _postprocess_entries(
        raw, cooldown_bars=params.cooldown_bars, cluster_window_bars=params.cluster_window_bars
    )


def _postprocess_entries(entries: list[EntryEvent], cooldown_bars: int, cluster_window_bars: int) -> list[EntryEvent]:
    """Postprocess entries: cluster and cooldown.

    Two-step:
    1) Cluster within +/- cluster_window_bars keeping highest confidence per side
    2) Enforce cooldown between same-side entries

    Args:
        entries: Raw entry events.
        cooldown_bars: Minimum bars between same-side entries.
        cluster_window_bars: Window size for clustering.

    Returns:
        Filtered entry events.
    """
    if not entries:
        return []

    # Assume entries already time-ordered by candle iteration
    clustered: list[EntryEvent] = []
    last_keep_idx_by_side: dict[EntrySide, int] = {}

    for e in entries:
        if e.side not in last_keep_idx_by_side:
            clustered.append(e)
            last_keep_idx_by_side[e.side] = len(clustered) - 1
            continue

        last_idx = last_keep_idx_by_side[e.side]
        # Approximate "distance" by index gap in the clustered list
        if (len(clustered) - 1 - last_idx) <= cluster_window_bars:
            # Same cluster window -> keep best confidence
            if e.confidence > clustered[last_idx].confidence:
                clustered[last_idx] = e
        else:
            clustered.append(e)
            last_keep_idx_by_side[e.side] = len(clustered) - 1

    # Cooldown
    filtered: list[EntryEvent] = []
    last_keep_pos: dict[EntrySide, int] = {}

    for pos, e in enumerate(clustered):
        prev = last_keep_pos.get(e.side)
        if prev is None:
            filtered.append(e)
            last_keep_pos[e.side] = pos
            continue
        if (pos - prev) >= cooldown_bars:
            filtered.append(e)
            last_keep_pos[e.side] = pos

    return filtered


# --- Debug Utilities ---


def debug_summary(features: dict[str, list[float]]) -> dict[str, float]:
    """Generate debug summary of features.

    Args:
        features: Calculated features.

    Returns:
        Dictionary with key feature values.
    """
    if not features or "closes" not in features:
        return {"ok": 0.0}
    n = len(features["closes"])
    last = n - 1

    def lastv(k: str, default: float = 0.0) -> float:
        arr = features.get(k, [])
        return float(arr[last]) if last < len(arr) else default

    return {
        "ok": 1.0,
        "n": float(n),
        "last_close": lastv("closes"),
        "last_atr": lastv("atr"),
        "last_atr_pct": lastv("atr_pct"),
        "last_rsi": lastv("rsi"),
        "last_adx": lastv("adx"),
        "last_bb_width": lastv("bb_width"),
        "last_bb_percent": lastv("bb_percent"),
        "last_dist_ema_atr": lastv("dist_ema_atr"),
    }
