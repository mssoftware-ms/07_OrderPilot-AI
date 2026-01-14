Ja – ich kann dir funktionierenden Code geben. Vorweg aber der Grund, warum deine aktuelle Integration **sehr wahrscheinlich gar keine Punkte findet**:

1. Du nutzt `price_vs_sma = (close - sma_20) / sma_20` als „Trend“-Signal. Auf 1m/5m ist das typischerweise **viel kleiner** als deine Schwellwerte (z. B. `0.005`, `0.008`, `0.01`), dadurch triggert praktisch nichts. 
2. Du „wärmst“ pauschal `i < 20` auf. Wenn der sichtbare Bereich klein ist oder Indikatoren längere Perioden brauchen, kommt ebenfalls **nichts**. 
3. Dein Optimizer kann (je nach Objective) unabsichtlich „0 Trades“ bevorzugen, wenn du **0-Entry-Penalty** nicht hart setzt. 

Die Lösung: **Skalierung ändern** (ATR-normalisierte Distanzen statt %-SMA), **robustere Features** (ATR/RSI/BB/ADX) und **eine Optimierung**, die niemals „0 Entries“ als Gewinner akzeptiert.

---

## Drop-in Python-Modul: Regime + Features + Optimizer + Entry-Generator (LONG grün / SHORT rot)

> Das ist ein einzelnes Modul (unter 600 Zeilen), ohne numpy, läuft schnell genug für Visible-Range + Worker.
> Du kannst es z. B. nach `src/analysis/entry_signals/entry_signal_engine.py` legen und in deinem `VisibleChartAnalyzer`/`FastOptimizer` verwenden.

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math
import random
import time


# -----------------------------
# Types
# -----------------------------
class RegimeType(str, Enum):
    NO_TRADE = "NO_TRADE"
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    SQUEEZE = "SQUEEZE"
    HIGH_VOL = "HIGH_VOL"


class EntrySide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class EntryEvent:
    timestamp: Any
    side: EntrySide
    confidence: float
    price: float
    reason_tags: List[str]
    regime: RegimeType


@dataclass
class OptimParams:
    # core indicator periods
    ema_fast: int = 20
    ema_slow: int = 50
    atr_period: int = 14
    rsi_period: int = 14
    bb_period: int = 20
    bb_std: float = 2.0
    adx_period: int = 14

    # regime thresholds
    adx_trend: float = 18.0
    squeeze_bb_width: float = 0.012  # relative width
    high_vol_atr_pct: float = 0.012  # atr/close

    # entry thresholds (ATR-normalized)
    pullback_atr: float = 0.8        # how far against trend is acceptable (in ATR units)
    pullback_rsi: float = 45.0       # long pullback rsi in uptrend / short pullback rsi in downtrend
    wick_reject: float = 0.55        # wick ratio threshold for rejection confirmation
    bb_entry: float = 0.15           # BB% entry extreme (0..1)
    rsi_oversold: float = 35.0
    rsi_overbought: float = 65.0

    # squeeze breakout confirmation
    vol_spike_factor: float = 1.2    # volume / vol_sma
    breakout_atr: float = 0.2        # require close to exceed band by x*ATR

    # postprocessing
    min_confidence: float = 0.58
    cooldown_bars: int = 10          # min distance between same-side entries
    cluster_window_bars: int = 6     # within window keep best

    # evaluation (optimizer objective)
    eval_horizon_bars: int = 40
    eval_tp_atr: float = 1.0
    eval_sl_atr: float = 0.8
    min_trades_gate: int = 8
    target_trades_soft: int = 30     # soft target for signal rate in visible window


# -----------------------------
# Helpers
# -----------------------------
def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _sma(values: List[float], period: int) -> List[float]:
    if period <= 1:
        return values[:]
    out: List[float] = []
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


def _ema(values: List[float], period: int) -> List[float]:
    if period <= 1:
        return values[:]
    out: List[float] = []
    alpha = 2.0 / (period + 1.0)
    ema = values[0] if values else 0.0
    for v in values:
        ema = alpha * v + (1.0 - alpha) * ema
        out.append(ema)
    return out


def _rsi(closes: List[float], period: int) -> List[float]:
    if period <= 1 or len(closes) < 2:
        return [50.0] * len(closes)
    rsis: List[float] = [50.0] * len(closes)
    gain = 0.0
    loss = 0.0

    # init
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


def _atr(highs: List[float], lows: List[float], closes: List[float], period: int) -> List[float]:
    n = len(closes)
    if n == 0:
        return []
    trs: List[float] = [0.0] * n
    prev_close = closes[0]
    for i in range(n):
        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - prev_close)
        tr3 = abs(lows[i] - prev_close)
        trs[i] = max(tr1, tr2, tr3)
        prev_close = closes[i]

    # Wilder smoothing
    out: List[float] = [trs[0]] * n
    if period <= 1:
        return trs
    atr = sum(trs[: min(period, n)]) / max(1, min(period, n))
    for i in range(n):
        if i < period:
            out[i] = atr
        else:
            atr = (atr * (period - 1) + trs[i]) / period
            out[i] = atr
    return out


def _bollinger(closes: List[float], period: int, std_mult: float) -> Tuple[List[float], List[float], List[float], List[float]]:
    n = len(closes)
    mid = _sma(closes, period)
    upper: List[float] = [0.0] * n
    lower: List[float] = [0.0] * n
    width: List[float] = [0.0] * n
    bbp: List[float] = [0.5] * n  # BB%
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


def _adx(highs: List[float], lows: List[float], closes: List[float], period: int) -> List[float]:
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
    def wilder_smooth(arr: List[float]) -> List[float]:
        out = [0.0] * n
        s = sum(arr[1 : min(n, period + 1)])
        out[period] = s
        for i in range(period + 1, n):
            out[i] = out[i - 1] - (out[i - 1] / period) + arr[i]
        # fill early with first available
        for i in range(0, min(period, n)):
            out[i] = out[period] if period < n else s
        return out

    tr_s = wilder_smooth(tr)
    p_s = wilder_smooth(plus_dm)
    m_s = wilder_smooth(minus_dm)

    adx = [0.0] * n
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
    # init
    if n > period * 2:
        init = sum(dx[period : period * 2]) / period
        adx[period * 2 - 1] = init
        for i in range(period * 2, n):
            adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period
        for i in range(0, period * 2 - 1):
            adx[i] = adx[period * 2 - 1]
    else:
        # fallback: simple smoothing
        adx = _sma(dx, max(2, period))
    return adx


def _wick_ratios(candles: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
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


def _pivots(highs: List[float], lows: List[float], lookback: int) -> Tuple[List[bool], List[bool]]:
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


# -----------------------------
# Feature extraction (replace your current simplistic SMA/volatility)
# -----------------------------
def calculate_features(candles: List[Dict[str, Any]], params: OptimParams) -> Dict[str, List[float]]:
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


# -----------------------------
# Regime detection (stable, anti-no-trade)
# -----------------------------
def detect_regime(features: Dict[str, List[float]], params: OptimParams) -> RegimeType:
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

    # squeeze: narrow bands + weak trend
    if bw <= params.squeeze_bb_width and a < params.adx_trend:
        return RegimeType.SQUEEZE

    if a >= params.adx_trend:
        if trend_dir >= 0:
            return RegimeType.TREND_UP
        return RegimeType.TREND_DOWN

    return RegimeType.RANGE


# -----------------------------
# Entry generation (entire visible window)
# -----------------------------
def generate_entries(
    candles: List[Dict[str, Any]],
    features: Dict[str, List[float]],
    regime: RegimeType,
    params: OptimParams,
) -> List[EntryEvent]:
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

    raw: List[EntryEvent] = []

    for i in range(n):
        if i < warmup:
            continue

        side: Optional[EntrySide] = None
        score = 0.0
        reasons: List[str] = []

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

                # avoid entries when ADX collapsed (anti-flip)
                if adx[i] < params.adx_trend * 0.75:
                    score -= 0.15
                    reasons.append("weak_trend_penalty")

                side = EntrySide.LONG

        elif regime == RegimeType.TREND_DOWN:
            if d >= 0.0 and abs(d) <= params.pullback_atr * 2.2:
                score += _clamp(abs(d) / max(1e-12, params.pullback_atr), 0.0, 1.0) * 0.55
                reasons.append("trend_pullback_atr")

                # in downtrend: RSI high-ish on pullback
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
            # require still narrow bands
            if bb_width[i] <= params.squeeze_bb_width * 1.4:
                # breakout above upper band by x*ATR
                if closes[i] > (bb_up[i] + params.breakout_atr * a) and conf_vol >= params.vol_spike_factor:
                    score = 0.62 + _clamp((conf_vol - params.vol_spike_factor) / 1.5, 0.0, 1.0) * 0.25
                    reasons += ["squeeze_breakout_up", "vol_spike"]
                    side = EntrySide.LONG
                # breakout below lower band
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


def _postprocess_entries(entries: List[EntryEvent], cooldown_bars: int, cluster_window_bars: int) -> List[EntryEvent]:
    """
    Two-step:
    1) cluster within +/- cluster_window_bars keeping highest confidence per side
    2) enforce cooldown between same-side entries
    """
    if not entries:
        return []

    # assume entries already time-ordered by candle iteration
    clustered: List[EntryEvent] = []
    last_keep_idx_by_side: Dict[EntrySide, int] = {}

    for e in entries:
        if e.side not in last_keep_idx_by_side:
            clustered.append(e)
            last_keep_idx_by_side[e.side] = len(clustered) - 1
            continue

        last_idx = last_keep_idx_by_side[e.side]
        # approximate "distance" by index gap in the clustered list (works if per-candle generation)
        # If you have candle_index, use it instead.
        if (len(clustered) - 1 - last_idx) <= cluster_window_bars:
            # same cluster window -> keep best confidence
            if e.confidence > clustered[last_idx].confidence:
                clustered[last_idx] = e
        else:
            clustered.append(e)
            last_keep_idx_by_side[e.side] = len(clustered) - 1

    # cooldown
    filtered: List[EntryEvent] = []
    last_keep_pos: Dict[EntrySide, int] = {}

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


# -----------------------------
# Fast optimizer (visible-window, seconds budget)
# -----------------------------
def fast_optimize_params(
    candles: List[Dict[str, Any]],
    base_params: OptimParams,
    budget_ms: int = 1200,
    seed: Optional[int] = None,
) -> OptimParams:
    """
    Fast random search over a *sane* parameter space.
    Objective: maximize hit-rate proxy in the visible window, with penalties, and NEVER accept zero-trade sets.
    """
    if seed is not None:
        random.seed(seed)

    t_end = time.time() + (budget_ms / 1000.0)
    best = base_params
    best_score = -1e9

    # Precompute features once per trial-family? No: features depend on some periods.
    # For speed, we keep period ranges tight; recompute features per trial still ok for visible windows (few hundred candles).
    trials = 0
    while time.time() < t_end:
        trials += 1
        p = _sample_params(base_params)

        feats = calculate_features(candles, p)
        reg = detect_regime(feats, p)
        ents = generate_entries(candles, feats, reg, p)
        score = _evaluate_entries(candles, feats, ents, p)

        if score > best_score:
            best_score = score
            best = p

    return best


def _sample_params(base: OptimParams) -> OptimParams:
    p = OptimParams(**vars(base))

    # tight + realistic ranges (ATR-normalized thresholds)
    p.ema_fast = random.choice([10, 14, 20, 30])
    p.ema_slow = random.choice([40, 50, 80])
    p.atr_period = random.choice([10, 14, 20])
    p.rsi_period = random.choice([10, 14, 18])
    p.bb_period = random.choice([14, 20, 30])
    p.bb_std = random.choice([1.8, 2.0, 2.2])

    p.adx_period = random.choice([10, 14, 20])
    p.adx_trend = random.choice([16.0, 18.0, 20.0, 22.0])

    p.squeeze_bb_width = random.choice([0.010, 0.012, 0.014, 0.016])
    p.high_vol_atr_pct = random.choice([0.010, 0.012, 0.014, 0.016])

    p.pullback_atr = random.choice([0.5, 0.7, 0.9, 1.1])
    p.pullback_rsi = random.choice([40.0, 45.0, 50.0])
    p.wick_reject = random.choice([0.5, 0.55, 0.6])

    p.bb_entry = random.choice([0.10, 0.15, 0.20])
    p.rsi_oversold = random.choice([30.0, 35.0, 40.0])
    p.rsi_overbought = random.choice([60.0, 65.0, 70.0])

    p.vol_spike_factor = random.choice([1.1, 1.2, 1.4])
    p.breakout_atr = random.choice([0.1, 0.2, 0.3])

    p.min_confidence = random.choice([0.56, 0.58, 0.60, 0.62])
    p.cooldown_bars = random.choice([6, 10, 14])
    p.cluster_window_bars = random.choice([4, 6, 8])

    p.eval_horizon_bars = random.choice([30, 40, 60])
    p.eval_tp_atr = random.choice([0.8, 1.0, 1.2])
    p.eval_sl_atr = random.choice([0.6, 0.8, 1.0])

    return p


def _evaluate_entries(
    candles: List[Dict[str, Any]],
    features: Dict[str, List[float]],
    entries: List[EntryEvent],
    params: OptimParams,
) -> float:
    """
    Proxy objective inside visible window:
    - simulate within horizon N bars: TP_atr before SL_atr => win else loss.
    - penalize too few trades or too many (signal spam).
    - NEVER allow 0 trades.
    """
    if not entries:
        return -9999.0  # hard penalty => avoids "no trades" winner

    highs = features.get("highs", [])
    lows = features.get("lows", [])
    closes = features.get("closes", [])
    atr = features.get("atr", [])

    # Build a timestamp->index mapping for quick lookup (fallback: iterate)
    ts_to_idx: Dict[Any, int] = {}
    for i, c in enumerate(candles):
        ts_to_idx[c.get("timestamp")] = i

    wins = 0
    losses = 0
    resolved = 0

    for e in entries:
        idx = ts_to_idx.get(e.timestamp)
        if idx is None or idx >= len(closes):
            continue
        a = max(1e-12, atr[idx])
        tp = params.eval_tp_atr * a
        sl = params.eval_sl_atr * a
        entry_price = closes[idx]

        end = min(len(closes) - 1, idx + params.eval_horizon_bars)
        hit = None  # True/False/None
        for j in range(idx + 1, end + 1):
            if e.side == EntrySide.LONG:
                # worst-first check: SL if low <= entry-sl, TP if high >= entry+tp
                if j < len(lows) and lows[j] <= entry_price - sl:
                    hit = False
                    break
                if j < len(highs) and highs[j] >= entry_price + tp:
                    hit = True
                    break
            else:
                if j < len(highs) and highs[j] >= entry_price + sl:
                    hit = False
                    break
                if j < len(lows) and lows[j] <= entry_price - tp:
                    hit = True
                    break

        if hit is None:
            continue
        resolved += 1
        if hit:
            wins += 1
        else:
            losses += 1

    if resolved < max(3, int(params.min_trades_gate * 0.6)):
        return -5000.0  # too little evidence in this window

    hit_rate = wins / max(1, resolved)

    # soft trade-count shaping (avoid spam, avoid too sparse)
    tc = len(entries)
    target = max(1, params.target_trades_soft)
    trade_penalty = abs(tc - target) / target  # 0 = perfect

    # confidence shaping: prefer higher average confidence
    avg_conf = sum(e.confidence for e in entries) / max(1, len(entries))

    score = (hit_rate * 2.0) + (avg_conf * 0.5) - (trade_penalty * 0.7)

    # small bonus for having both sides (helps avoid one-sided bias in range)
    has_long = any(e.side == EntrySide.LONG for e in entries)
    has_short = any(e.side == EntrySide.SHORT for e in entries)
    if has_long and has_short:
        score += 0.05

    return score


# -----------------------------
# Debug helper (why no entries)
# -----------------------------
def debug_summary(features: Dict[str, List[float]]) -> Dict[str, float]:
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
```

---

## So integrierst du das in deinen bestehenden Ablauf (ohne Repo-Umwurf)

Dein aktueller Ablauf ist: Features → Regime → Optimizer → `_generate_entries()` → Fallback `_score_entries()` 

### 1) Feature Extraction ersetzen

In `VisibleChartAnalyzer._calculate_features(...)` statt SMA/price_vs_sma/volatility:

```python
from src.analysis.entry_signals.entry_signal_engine import OptimParams, calculate_features

params = OptimParams()  # oder aus Settings laden
features = calculate_features(candles, params)
```

### 2) Regime Detection ersetzen

In `_detect_regime(...)`:

```python
from src.analysis.entry_signals.entry_signal_engine import detect_regime
regime = detect_regime(features, params)
```

### 3) Optimizer wirklich nutzen (und 0-Trades hart bestrafen)

In deinem `FastOptimizer` (oder da, wo du `opt_set` baust):

```python
from src.analysis.entry_signals.entry_signal_engine import fast_optimize_params

best_params = fast_optimize_params(candles, base_params=params, budget_ms=1200, seed=42)
```

### 4) Entries für den *gesamten sichtbaren Bereich* erzeugen

In `_generate_entries(...)`:

```python
from src.analysis.entry_signals.entry_signal_engine import generate_entries

entries = generate_entries(candles, features, regime, best_params)
return entries
```

---

## Warum dieser Code bei dir sofort Punkte liefern sollte

* Er nutzt **ATR-normalisierte Distanzen** (`dist_ema_atr`) statt `price_vs_sma`, wodurch Schwellen realistisch werden (0.5–1.1 ATR statt 0.5–1.0%). Das behebt deinen Skalierungsfehler aus dem aktuellen Ablauf. 
* Er hat **Regime-spezifische Logik** (Trend Pullback / Range Mean-Reversion / Squeeze Breakout) statt nur „Trend vs SMA“. 
* Der Optimizer hat eine **harte 0-Trade-Strafe**, damit er niemals „nichts tun“ als bestes Set nimmt. 

---

## Minimaler Debug, wenn trotzdem 0 Punkte

Wenn `entries` leer bleibt, logge einmal:

```python
from src.analysis.entry_signals.entry_signal_engine import debug_summary
logger.info("EntryAnalyzer debug: %s", debug_summary(features))
```

Wenn `last_dist_ema_atr` nahe 0 ist und BB% nie in Extreme kommt, ist das Fenster schlicht „zu ruhig“/zu kurz – dann musst du entweder:

* sichtbares Fenster vergrößern **oder**
* `min_confidence` runter (z. B. 0.54) **oder**
* Range-Trigger lockern (`bb_entry` hoch auf 0.20, `rsi_oversold` hoch auf 40).

---

Wenn du willst, kann ich dir als nächsten Schritt **gezielt** sagen, *welcher* Teil bei dir blockiert (Regime=NO_TRADE? Warmup? BB% nie extrem? ADX permanent niedrig?), **wenn du mir** aus deiner Log-Ausgabe einmal `debug_summary(features)` plus `len(candles)` und das erkannte `regime` postest.
