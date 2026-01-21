"""Entry Signal Engine with ATR-normalized features and robust regime detection.

This module provides a complete replacement for the simplistic SMA-based entry detection.
It uses:
- ATR-normalized distances (fixes scale issues on 1m/5m timeframes)
- Robust features (ATR, RSI, BB, ADX, wicks, pivots)
- Regime-specific entry logic (Trend Pullback, Range Mean-Reversion, Squeeze Breakout)
- Fast optimizer with hard 0-trade penalty
- Full visible-window entry generation

Designed to integrate seamlessly with VisibleChartAnalyzer without major refactoring.
"""

from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# Types
class RegimeType(str, Enum):
    """Market regime classification (compatible with existing types)."""

    NO_TRADE = "no_trade"
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    SQUEEZE = "squeeze"
    HIGH_VOL = "high_vol"


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


# Helpers
def _safe_float(x: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    try:
        return float(x)
    except Exception:
        return default


def _clamp(x: float, lo: float, hi: float) -> float:
    """Clamp value to range."""
    return lo if x < lo else hi if x > hi else x


def _sma(values: list[float], period: int) -> list[float]:
    """Simple moving average."""
    if period <= 1:
        return values[:]
    out: list[float] = []
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= period:
            s -= values[i - period]
        if i >= period - 1:
            out.append(s / period)
        else:
            out.append(v)
    return out


def _ema(values: list[float], period: int) -> list[float]:
    """Exponential moving average."""
    if period <= 1:
        return values[:]
    out: list[float] = []
    alpha = 2.0 / (period + 1.0)
    ema = values[0] if values else 0.0
    for v in values:
        ema = alpha * v + (1.0 - alpha) * ema
        out.append(ema)
    return out


def _rsi(closes: list[float], period: int) -> list[float]:
    """Relative Strength Index."""
    if period <= 1 or len(closes) < 2:
        return [50.0] * len(closes)
    rsis: list[float] = [50.0] * len(closes)
    gain = 0.0
    loss = 0.0

    # Init
    for i in range(1, min(period + 1, len(closes))):
        ch = closes[i] - closes[i - 1]
        if ch >= 0:
            gain += ch
        else:
            loss -= ch
    avg_gain = gain / period
    avg_loss = loss / period

    for i in range(period, len(closes)):
        ch = closes[i] - closes[i - 1]
        g = ch if ch > 0 else 0.0
        l = -ch if ch < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        if avg_loss <= 1e-12:
            rsis[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsis[i] = 100.0 - (100.0 / (1.0 + rs))
    return rsis


def _atr(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float]:
    """Average True Range."""
    n = len(closes)
    if n == 0:
        return []
    trs: list[float] = [0.0] * n
    prev_close = closes[0]
    for i in range(n):
        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - prev_close)
        tr3 = abs(lows[i] - prev_close)
        trs[i] = max(tr1, tr2, tr3)
        prev_close = closes[i]

    # Wilder smoothing
    out: list[float] = [trs[0]] * n
    if period <= 1:
        return trs
    atr_val = sum(trs[: min(period, n)]) / max(1, min(period, n))
    for i in range(n):
        if i < period:
            out[i] = atr_val
        else:
            atr_val = (atr_val * (period - 1) + trs[i]) / period
            out[i] = atr_val
    return out


def _bollinger(
    closes: list[float], period: int, std_mult: float
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    """Bollinger Bands.

    Returns:
        mid, upper, lower, width (relative), bb_percent
    """
    n = len(closes)
    mid = _sma(closes, period)
    upper: list[float] = [0.0] * n
    lower: list[float] = [0.0] * n
    width: list[float] = [0.0] * n
    bbp: list[float] = [0.5] * n  # BB%
    for i in range(n):
        start = max(0, i - period + 1)
        window = closes[start : i + 1]
        m = sum(window) / max(1, len(window))
        var = sum((x - m) ** 2 for x in window) / max(1, len(window))
        sd = math.sqrt(var)
        up = m + std_mult * sd
        lo = m - std_mult * sd
        upper[i] = up
        lower[i] = lo
        mid[i] = m
        if m != 0:
            width[i] = (up - lo) / m  # relative width
        rng = up - lo
        if rng > 1e-12:
            bbp[i] = _clamp((closes[i] - lo) / rng, 0.0, 1.0)
    return mid, upper, lower, width, bbp


def _adx(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float]:
    """Average Directional Index."""
    n = len(closes)
    if n < 2:
        return [0.0] * n
    if period <= 1:
        return [0.0] * n

    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr = [0.0] * n

    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        plus_dm[i] = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm[i] = down_move if (down_move > up_move and down_move > 0) else 0.0

        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - closes[i - 1])
        tr3 = abs(lows[i] - closes[i - 1])
        tr[i] = max(tr1, tr2, tr3)

    # Wilder smoothing
    def wilder_smooth(arr: list[float]) -> list[float]:
        out = [0.0] * n
        s = sum(arr[1 : min(n, period + 1)])
        out[period] = s
        for i in range(period + 1, n):
            out[i] = out[i - 1] - (out[i - 1] / period) + arr[i]
        # Fill early with first available
        for i in range(0, min(period, n)):
            out[i] = out[period] if period < n else s
        return out

    tr_s = wilder_smooth(tr)
    p_s = wilder_smooth(plus_dm)
    m_s = wilder_smooth(minus_dm)

    adx_vals = [0.0] * n
    dx = [0.0] * n
    for i in range(n):
        if tr_s[i] <= 1e-12:
            continue
        pdi = 100.0 * (p_s[i] / tr_s[i])
        mdi = 100.0 * (m_s[i] / tr_s[i])
        denom = pdi + mdi
        if denom <= 1e-12:
            continue
        dx[i] = 100.0 * abs(pdi - mdi) / denom

    # ADX is Wilder SMA of DX
    if n > period * 2:
        init = sum(dx[period : period * 2]) / period
        adx_vals[period * 2 - 1] = init
        for i in range(period * 2, n):
            adx_vals[i] = (adx_vals[i - 1] * (period - 1) + dx[i]) / period
        for i in range(0, period * 2 - 1):
            adx_vals[i] = adx_vals[period * 2 - 1]
    else:
        # Fallback: simple smoothing
        adx_vals = _sma(dx, max(2, period))
    return adx_vals


def _wick_ratios(candles: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    """Calculate upper and lower wick ratios."""
    up = []
    lo = []
    for c in candles:
        o = _safe_float(c.get("open", c.get("close", 0.0)))
        h = _safe_float(c.get("high", 0.0))
        l = _safe_float(c.get("low", 0.0))
        cl = _safe_float(c.get("close", 0.0))
        rng = max(1e-12, h - l)
        upper_wick = max(0.0, h - max(o, cl))
        lower_wick = max(0.0, min(o, cl) - l)
        up.append(upper_wick / rng)
        lo.append(lower_wick / rng)
    return up, lo


def _pivots(highs: list[float], lows: list[float], lookback: int) -> tuple[list[bool], list[bool]]:
    """Detect pivot highs and lows."""
    n = len(highs)
    ph = [False] * n
    pl = [False] * n
    if lookback <= 1:
        return ph, pl
    for i in range(n):
        s = max(0, i - lookback)
        e = min(n, i + lookback + 1)
        hh = max(highs[s:e])
        ll = min(lows[s:e])
        if highs[i] >= hh and (e - s) >= 3:
            ph[i] = True
        if lows[i] <= ll and (e - s) >= 3:
            pl[i] = True
    return ph, pl


# Feature extraction (replaces your current simplistic SMA/volatility)
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
    adx = _adx(highs, lows, closes, max(2, params.adx_period))
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
        "vol_sma": vol_sma,
        "up_wick": up_wick,
        "lo_wick": lo_wick,
        "pivot_high": [1.0 if x else 0.0 for x in piv_h],
        "pivot_low": [1.0 if x else 0.0 for x in piv_l],
        "dist_ema_atr": dist_ema_atr,
    }


# Regime detection (stable, anti-no-trade)
def detect_regime(features: dict[str, list[float]], params: OptimParams) -> RegimeType:
    """Detect market regime from features.

    Uses ADX, BB width, and ATR% to classify the market state.
    Designed to avoid NO_TRADE unless data is insufficient.

    Args:
        features: Calculated features.
        params: Regime thresholds.

    Returns:
        Detected regime type.
    """
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


# Entry generation (entire visible window)
def generate_entries(
    candles: list[dict[str, Any]],
    features: dict[str, list[float]],
    regime: RegimeType,
    params: OptimParams,
) -> list[EntryEvent]:
    """Generate entry signals for the entire visible range.

    Uses regime-specific logic:
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

    closes = features["closes"]
    atr = features["atr"]
    rsi = features["rsi"]
    bbp = features["bb_percent"]
    bb_up = features["bb_up"]
    bb_lo = features["bb_lo"]
    bb_width = features["bb_width"]
    vol = features["volume"]
    vol_sma = features["vol_sma"]
    dist = features["dist_ema_atr"]
    up_w = features["up_wick"]
    lo_w = features["lo_wick"]
    piv_h = features["pivot_high"]
    piv_l = features["pivot_low"]
    adx = features["adx"]

    n = len(candles)
    warmup = min(50, max(20, int(max(params.ema_slow, params.bb_period, params.adx_period) * 0.6)))
    warmup = min(warmup, n - 1)

    raw: list[EntryEvent] = []

    for i in range(n):
        if i < warmup:
            continue

        side: EntrySide | None = None
        score = 0.0
        reasons: list[str] = []

        a = max(1e-12, atr[i])
        d = dist[i]
        r = rsi[i]
        conf_vol = (vol[i] / max(1e-12, vol_sma[i])) if i < len(vol_sma) else 1.0
        wick_long = lo_w[i]
        wick_short = up_w[i]
        is_piv_low = piv_l[i] > 0.5
        is_piv_high = piv_h[i] > 0.5

        # ---------------- Trend regimes: pullback entries ----------------
        if regime == RegimeType.TREND_UP:
            # Pullback = price below EMA_slow in ATR units, but not "free fall"
            if d <= 0.0 and abs(d) <= params.pullback_atr * 2.2:
                score += _clamp(abs(d) / max(1e-12, params.pullback_atr), 0.0, 1.0) * 0.55
                reasons.append("trend_pullback_atr")

                if r <= params.pullback_rsi:
                    score += 0.18
                    reasons.append("rsi_pullback")

                if wick_long >= params.wick_reject or is_piv_low:
                    score += 0.18
                    reasons.append("rejection_or_pivot_low")

                # Avoid entries when ADX collapsed (anti-flip)
                if adx[i] < params.adx_trend * 0.75:
                    score -= 0.15
                    reasons.append("weak_trend_penalty")

                side = EntrySide.LONG

        elif regime == RegimeType.TREND_DOWN:
            if d >= 0.0 and abs(d) <= params.pullback_atr * 2.2:
                score += _clamp(abs(d) / max(1e-12, params.pullback_atr), 0.0, 1.0) * 0.55
                reasons.append("trend_pullback_atr")

                # In downtrend: RSI high-ish on pullback
                if r >= (100.0 - params.pullback_rsi):
                    score += 0.18
                    reasons.append("rsi_pullback")

                if wick_short >= params.wick_reject or is_piv_high:
                    score += 0.18
                    reasons.append("rejection_or_pivot_high")

                if adx[i] < params.adx_trend * 0.75:
                    score -= 0.15
                    reasons.append("weak_trend_penalty")

                side = EntrySide.SHORT

        # ---------------- Range regime: mean reversion at BB extremes ----------------
        elif regime == RegimeType.RANGE:
            bbp_i = bbp[i]
            if bbp_i <= params.bb_entry and r <= params.rsi_oversold:
                score = 0.55
                score += _clamp((params.bb_entry - bbp_i) / max(1e-12, params.bb_entry), 0.0, 1.0) * 0.25
                if wick_long >= params.wick_reject or is_piv_low:
                    score += 0.15
                    reasons.append("rejection_or_pivot_low")
                reasons += ["range_bb_oversold", "rsi_oversold"]
                side = EntrySide.LONG

            elif bbp_i >= (1.0 - params.bb_entry) and r >= params.rsi_overbought:
                score = 0.55
                score += _clamp((bbp_i - (1.0 - params.bb_entry)) / max(1e-12, params.bb_entry), 0.0, 1.0) * 0.25
                if wick_short >= params.wick_reject or is_piv_high:
                    score += 0.15
                    reasons.append("rejection_or_pivot_high")
                reasons += ["range_bb_overbought", "rsi_overbought"]
                side = EntrySide.SHORT

        # ---------------- Squeeze: breakout with minimal confirmation ----------------
        elif regime == RegimeType.SQUEEZE:
            # Require still narrow bands
            if bb_width[i] <= params.squeeze_bb_width * 1.4:
                # Breakout above upper band by x*ATR
                if closes[i] > (bb_up[i] + params.breakout_atr * a) and conf_vol >= params.vol_spike_factor:
                    score = 0.62 + _clamp((conf_vol - params.vol_spike_factor) / 1.5, 0.0, 1.0) * 0.25
                    reasons += ["squeeze_breakout_up", "vol_spike"]
                    side = EntrySide.LONG
                # Breakout below lower band
                elif closes[i] < (bb_lo[i] - params.breakout_atr * a) and conf_vol >= params.vol_spike_factor:
                    score = 0.62 + _clamp((conf_vol - params.vol_spike_factor) / 1.5, 0.0, 1.0) * 0.25
                    reasons += ["squeeze_breakout_down", "vol_spike"]
                    side = EntrySide.SHORT

        # HIGH_VOL: usually reduce trading (or require stronger confirmation)
        elif regime == RegimeType.HIGH_VOL:
            # For MVP: allow only stronger extremes (avoid spam)
            bbp_i = bbp[i]
            if bbp_i <= (params.bb_entry * 0.75) and r <= (params.rsi_oversold - 3):
                score = 0.62
                reasons += ["high_vol_extreme_long"]
                side = EntrySide.LONG
            elif bbp_i >= (1.0 - params.bb_entry * 0.75) and r >= (params.rsi_overbought + 3):
                score = 0.62
                reasons += ["high_vol_extreme_short"]
                side = EntrySide.SHORT

        if side and score >= params.min_confidence:
            raw.append(
                EntryEvent(
                    timestamp=candles[i].get("timestamp"),
                    side=side,
                    confidence=float(_clamp(score, 0.0, 1.0)),
                    price=closes[i],
                    reason_tags=reasons,
                    regime=regime,
                )
            )

    return _postprocess_entries(raw, cooldown_bars=params.cooldown_bars, cluster_window_bars=params.cluster_window_bars)


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


# Debug helper (why no entries)
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
