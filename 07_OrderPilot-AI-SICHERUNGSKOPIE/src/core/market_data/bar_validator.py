"""Shared bar validation logic for live and historical data.

Implements the validation matrix from 01_Projectplan/Ticks_Validierung.CSV:
- Timestamp continuity (log-only)
- Negative price check
- High/Low inversion fix
- Outlier detection vs previous close (hard drop)
- Z-Score winsorizing (4.7 sigma, median of last 5)
- Volume/Price divergence flag using ATR(14) and avg volume

Keeps per-symbol rolling state to apply identical rules for streaming
and historical loads.
"""

from __future__ import annotations

import logging
import statistics
from collections import deque
from datetime import datetime
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Tunables (aligned with Data-Engineer Matrix)
OUTLIER_PCT = 0.03
MAX_ZSCORE = 4.7
MEDIAN_WINDOW = 5
ATR_PERIOD = 14
HISTORY_WINDOW = 120  # ~2h for 1m bars
RANGE_HARD_PCT = 0.20  # drop if intrabar range > 20% of close when no prev_close


class BarValidator:
    """Stateful validator for OHLCV bars."""

    def __init__(self):
        self._close_history: dict[str, deque[float]] = {}
        self._volume_history: dict[str, deque[int]] = {}
        self._bar_history: dict[str, deque[dict[str, Any]]] = {}
        self._last_close: dict[str, float] = {}
        self._last_timestamp: dict[str, datetime] = {}

    # Seeding -----------------------------------------------------------

    def seed(self, symbol: str, close: float, timestamp: datetime | None = None) -> None:
        """Prime the validator with a known last close to avoid loose first-bar passes."""
        if close <= 0:
            return
        self._last_close[symbol] = close
        if timestamp:
            self._last_timestamp[symbol] = timestamp
        closes = self._ensure_history(self._close_history, symbol)
        closes.append(close)

    # Public API ---------------------------------------------------------

    def validate_stream_bar(
        self,
        symbol: str,
        timestamp: datetime,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: int,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Validate a single bar coming from a live stream."""
        return self._validate_bar(symbol, timestamp, open_, high, low, close, volume, extra)

    def validate_historical_bars(
        self,
        symbol: str,
        bars: Iterable[Any],
        getter,
        builder,
    ) -> list[Any]:
        """Validate a sequence of historical bars.

        Args:
            symbol: symbol being processed
            bars: iterable of source bar objects
            getter: callable that extracts (ts, o, h, l, c, v) from bar
            builder: callable that rebuilds a sanitized bar from extracted values
        """
        cleaned: list[Any] = []
        for bar in bars:
            ts, o, h, l, c, v = getter(bar)
            result = self._validate_bar(symbol, ts, o, h, l, c, v)
            if result is None:
                continue
            cleaned.append(
                builder(
                    ts=result["timestamp"],
                    open_=result["open"],
                    high=result["high"],
                    low=result["low"],
                    close=result["close"],
                    volume=result["volume"],
                    source=getattr(bar, "source", ""),
                    vwap=getattr(bar, "vwap", None),
                    trades=getattr(bar, "trades", None),
                    low_reliability=result.get("low_reliability", False),
                )
            )
        return cleaned

    # Internal -----------------------------------------------------------

    def _validate_bar(
        self,
        symbol: str,
        timestamp: datetime,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: int,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Core validation and sanitization (refactored). Returns dict or None if rejected."""
        extra = extra or {}

        # Basic validation
        if not self._validate_positive_prices(symbol, open_, high, low, close):
            return None

        high, low = self._fix_inverted_high_low(symbol, high, low)
        self._log_timestamp_gap(symbol, timestamp)

        prev_close = self._last_close.get(symbol)

        # Outlier checks
        if self._is_hard_outlier(high, low, close, prev_close):
            self._log_hard_outlier(symbol, open_, high, low, close, prev_close)
            return None

        if not self._validate_first_bar_range(symbol, high, low, close, prev_close):
            return None

        # Z-score winsorizing
        close, high, low = self._apply_zscore_winsorizing(symbol, close, high, low)

        # Volume/price divergence check
        low_reliability = self._check_volume_price_divergence(symbol, close, prev_close, volume)

        # Update history
        self._update_history(symbol, high, low, close, volume, timestamp)

        return {
            "symbol": symbol,
            "timestamp": timestamp,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "low_reliability": low_reliability,
            **extra,
        }

    def _validate_positive_prices(self, symbol: str, open_: float, high: float, low: float, close: float) -> bool:
        """Check all prices are positive."""
        if min(open_, high, low, close) <= 0:
            logger.warning("Rejecting bar with non-positive price for %s", symbol)
            return False
        return True

    def _fix_inverted_high_low(self, symbol: str, high: float, low: float) -> tuple[float, float]:
        """Fix inverted high/low values."""
        if high < low:
            logger.warning("High/Low inverted for %s. Swapping values.", symbol)
            return low, high
        return high, low

    def _log_timestamp_gap(self, symbol: str, timestamp: datetime) -> None:
        """Log timestamp gaps (continuity check)."""
        last_ts = self._last_timestamp.get(symbol)
        if last_ts:
            gap = (timestamp - last_ts).total_seconds()
            if gap > 90:
                logger.info("Gap detected for %s: %.0fs since last bar", symbol, gap)

    def _log_hard_outlier(self, symbol: str, open_: float, high: float, low: float, close: float, prev_close: float | None) -> None:
        """Log hard outlier rejection."""
        logger.warning(
            "Dropping hard outlier bar %s O:%s H:%s L:%s C:%s (prev_close=%s)",
            symbol, open_, high, low, close, prev_close
        )

    def _validate_first_bar_range(self, symbol: str, high: float, low: float, close: float, prev_close: float | None) -> bool:
        """Validate range for first bar (no previous close)."""
        if prev_close is None:
            if close > 0 and (high - low) / close > RANGE_HARD_PCT:
                logger.warning(
                    "Dropping first-bar range outlier for %s: range_pct=%.2f",
                    symbol, (high - low) / close
                )
                return False
        return True

    def _apply_zscore_winsorizing(self, symbol: str, close: float, high: float, low: float) -> tuple[float, float, float]:
        """Apply Z-score winsorizing to close price."""
        closes_hist = self._ensure_history(self._close_history, symbol)
        if len(closes_hist) >= MEDIAN_WINDOW and len(closes_hist) >= ATR_PERIOD:
            stdev = statistics.pstdev(closes_hist) if len(closes_hist) > 1 else 0
            if stdev > 0:
                mean = statistics.fmean(closes_hist)
                z = abs((close - mean) / stdev)
                if z > MAX_ZSCORE:
                    median = statistics.median(list(closes_hist)[-MEDIAN_WINDOW:])
                    logger.warning(
                        "Z-Score %.2f for %s. Winsorizing close from %.6f to %.6f",
                        z, symbol, close, median
                    )
                    close = median
                    high = max(high, close)
                    low = min(low, close)
        return close, high, low

    def _check_volume_price_divergence(self, symbol: str, close: float, prev_close: float | None, volume: int) -> bool:
        """Check for volume/price divergence. Returns True if low reliability."""
        atr = self._calc_atr(symbol)
        avg_vol = self._calc_avg_volume(symbol)

        if (atr is not None and prev_close and abs(close - prev_close) > atr * 2
            and avg_vol is not None and avg_vol > 0 and volume < avg_vol * 0.1):
            logger.warning(
                "Volume/Price divergence for %s: Δp=%.6f, ATR=%.6f, vol=%s, avg_vol=%.1f. Flagging low reliability.",
                symbol, abs(close - prev_close), atr, volume, avg_vol
            )
            return True
        return False

    def _update_history(self, symbol: str, high: float, low: float, close: float, volume: int, timestamp: datetime) -> None:
        """Update symbol history and tracking."""
        self._record_history(symbol, high, low, close, volume, timestamp)
        self._last_close[symbol] = close
        self._last_timestamp[symbol] = timestamp

    @staticmethod
    def _is_hard_outlier(high: float, low: float, close: float, prev_close: float | None) -> bool:
        if prev_close is None or prev_close == 0:
            return False

        def deviates(val: float) -> bool:
            return abs(val - prev_close) / prev_close > OUTLIER_PCT

        return deviates(high) or deviates(low) or deviates(close)

    def _record_history(
        self,
        symbol: str,
        high: float,
        low: float,
        close: float,
        volume: int,
        timestamp: datetime,
    ) -> None:
        closes = self._ensure_history(self._close_history, symbol)
        volumes = self._ensure_history(self._volume_history, symbol)
        bars = self._ensure_history(self._bar_history, symbol)

        closes.append(close)
        volumes.append(volume)
        bars.append(
            {
                "high": high,
                "low": low,
                "close": close,
                "prev_close": self._last_close.get(symbol),
                "timestamp": timestamp,
            }
        )

    def _calc_atr(self, symbol: str) -> float | None:
        bars = self._bar_history.get(symbol)
        if not bars or len(bars) < ATR_PERIOD + 1:
            return None

        trs: list[float] = []
        for b in list(bars)[-ATR_PERIOD:]:
            prev_close = b.get("prev_close")
            if prev_close is None:
                return None
            trs.append(
                max(
                    b["high"] - b["low"],
                    abs(b["high"] - prev_close),
                    abs(b["low"] - prev_close),
                )
            )

        return float(sum(trs) / len(trs)) if trs else None

    def _calc_avg_volume(self, symbol: str) -> float | None:
        vols = self._volume_history.get(symbol)
        if not vols or len(vols) < ATR_PERIOD:
            return None
        return float(sum(list(vols)[-ATR_PERIOD:]) / ATR_PERIOD)

    @staticmethod
    def _ensure_history(store: dict[str, deque], symbol: str) -> deque:
        if symbol not in store:
            store[symbol] = deque(maxlen=HISTORY_WINDOW)
        return store[symbol]
