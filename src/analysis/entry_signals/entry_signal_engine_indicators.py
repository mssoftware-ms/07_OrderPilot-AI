"""Technical Indicator Calculation Functions for Entry Signal Engine.

This module contains all technical analysis indicator calculations:
- Helper functions (safe_float, clamp)
- Moving averages (SMA, EMA)
- Momentum indicators (RSI, ADX)
- Volatility indicators (ATR, Bollinger Bands)
- Pattern detection (wicks, pivots)

Extracted from entry_signal_engine.py for better modularity.
All functions are stateless and can be used independently.
"""

from __future__ import annotations

import math
from typing import Any


# --- Helper Functions ---


def _safe_float(x: Any, default: float = 0.0) -> float:
    """Safely convert to float.

    Args:
        x: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Float value or default.
    """
    try:
        return float(x)
    except Exception:
        return default


def _clamp(x: float, lo: float, hi: float) -> float:
    """Clamp value to range.

    Args:
        x: Value to clamp.
        lo: Minimum value.
        hi: Maximum value.

    Returns:
        Clamped value in [lo, hi].
    """
    return lo if x < lo else hi if x > hi else x


# --- Moving Averages ---


def _sma(values: list[float], period: int) -> list[float]:
    """Simple moving average.

    Args:
        values: Input values.
        period: Lookback period.

    Returns:
        SMA values (same length as input).
    """
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
    """Exponential moving average.

    Args:
        values: Input values.
        period: Lookback period.

    Returns:
        EMA values (same length as input).
    """
    if period <= 1:
        return values[:]
    out: list[float] = []
    alpha = 2.0 / (period + 1.0)
    ema = values[0] if values else 0.0
    for v in values:
        ema = alpha * v + (1.0 - alpha) * ema
        out.append(ema)
    return out


# --- Momentum Indicators ---


def _rsi(closes: list[float], period: int) -> list[float]:
    """Relative Strength Index.

    Args:
        closes: Close prices.
        period: Lookback period (typically 14).

    Returns:
        RSI values (0-100).
    """
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


# --- Volatility Indicators ---


def _atr(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float]:
    """Average True Range.

    Args:
        highs: High prices.
        lows: Low prices.
        closes: Close prices.
        period: Lookback period (typically 14).

    Returns:
        ATR values.
    """
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

    Args:
        closes: Close prices.
        period: Lookback period (typically 20).
        std_mult: Standard deviation multiplier (typically 2.0).

    Returns:
        Tuple of (mid, upper, lower, width (relative), bb_percent).
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


# --- Directional Indicators ---


def _adx(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float]:
    """Average Directional Index (returns only ADX for backward compatibility).

    Args:
        highs: High prices.
        lows: Low prices.
        closes: Close prices.
        period: Lookback period (typically 14).

    Returns:
        ADX values.
    """
    adx_vals, _, _ = _adx_full(highs, lows, closes, period)
    return adx_vals


def _adx_full(
    highs: list[float], lows: list[float], closes: list[float], period: int
) -> tuple[list[float], list[float], list[float]]:
    """Average Directional Index with DI+ and DI-.

    Args:
        highs: High prices.
        lows: Low prices.
        closes: Close prices.
        period: Lookback period (typically 14).

    Returns:
        Tuple of (ADX, DI+, DI-) arrays.
    """
    n = len(closes)
    if n < 2:
        return [0.0] * n, [0.0] * n, [0.0] * n
    if period <= 1:
        return [0.0] * n, [0.0] * n, [0.0] * n

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
    di_plus = [0.0] * n
    di_minus = [0.0] * n
    dx = [0.0] * n

    for i in range(n):
        if tr_s[i] <= 1e-12:
            continue
        pdi = 100.0 * (p_s[i] / tr_s[i])
        mdi = 100.0 * (m_s[i] / tr_s[i])
        di_plus[i] = pdi
        di_minus[i] = mdi
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

    return adx_vals, di_plus, di_minus


# --- Pattern Detection ---


def _wick_ratios(candles: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    """Calculate upper and lower wick ratios.

    Args:
        candles: List of OHLC candles.

    Returns:
        Tuple of (upper_wick_ratios, lower_wick_ratios).
    """
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
    """Detect pivot highs and lows.

    Args:
        highs: High prices.
        lows: Low prices.
        lookback: Lookback window for pivot detection.

    Returns:
        Tuple of (pivot_highs, pivot_lows) boolean arrays.
    """
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
