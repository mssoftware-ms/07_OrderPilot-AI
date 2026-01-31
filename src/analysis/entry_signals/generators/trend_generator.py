"""Trend regime entry generators (TREND_UP, TREND_DOWN).

Handles pullback entries in trending markets using ATR-normalized distances.
"""

from __future__ import annotations

from typing import Any

from ..entry_signal_engine import EntryEvent, EntrySide, OptimParams, RegimeType
from .base_generator import BaseEntryGenerator


class TrendUpGenerator(BaseEntryGenerator):
    """Generator for TREND_UP (bullish) pullback entries.

    Logic:
    - Pullback = price below EMA_slow (in ATR units)
    - RSI confirmation (not oversold)
    - Wick rejection or pivot low
    - Penalty for weak ADX (regime flip protection)
    """

    def __init__(self):
        """Initialize TREND_UP generator."""
        super().__init__(RegimeType.TREND_UP)

    def can_generate(self, regime: RegimeType) -> bool:
        """Check if this generator handles TREND_UP."""
        return regime == RegimeType.TREND_UP

    def generate(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        params: OptimParams,
    ) -> list[EntryEvent]:
        """Generate LONG entries for TREND_UP regime."""
        if not candles or not features:
            return []

        closes = features["closes"]
        atr = features["atr"]
        rsi = features["rsi"]
        dist = features["dist_ema_atr"]
        lo_w = features["lo_wick"]
        piv_l = features["pivot_low"]
        adx = features["adx"]

        n = len(candles)
        warmup = self._calculate_warmup(features, params)
        raw: list[EntryEvent] = []

        for i in range(n):
            if i < warmup:
                continue

            score = 0.0
            reasons: list[str] = []

            d = dist[i]
            r = rsi[i]
            wick_long = lo_w[i]
            is_piv_low = piv_l[i] > 0.5

            # Pullback = price below EMA_slow, but not free fall
            if d <= 0.0 and abs(d) <= params.pullback_atr * 2.2:
                score += self._clamp(abs(d) / max(1e-12, params.pullback_atr), 0.0, 1.0) * 0.55
                reasons.append("trend_pullback_atr")

                if r <= params.pullback_rsi:
                    score += 0.18
                    reasons.append("rsi_pullback")

                if wick_long >= params.wick_reject or is_piv_low:
                    score += 0.18
                    reasons.append("rejection_or_pivot_low")

                # Penalty for weak ADX (avoid regime flip)
                if adx[i] < params.adx_trend * 0.75:
                    score -= 0.15
                    reasons.append("weak_trend_penalty")

                if score >= params.min_confidence:
                    raw.append(
                        EntryEvent(
                            timestamp=candles[i].get("timestamp"),
                            side=EntrySide.LONG,
                            confidence=float(self._clamp(score, 0.0, 1.0)),
                            price=closes[i],
                            reason_tags=reasons,
                            regime=self.regime,
                        )
                    )

        return raw

    def _calculate_warmup(self, features: dict[str, list[float]], params: OptimParams) -> int:
        """Calculate warmup period for indicators."""
        n = len(features.get("closes", []))
        warmup = min(50, max(20, int(max(params.ema_slow, params.bb_period, params.adx_period) * 0.6)))
        return min(warmup, n - 1)


class TrendDownGenerator(BaseEntryGenerator):
    """Generator for TREND_DOWN (bearish) pullback entries.

    Logic:
    - Pullback = price above EMA_slow (in ATR units)
    - RSI confirmation (not overbought)
    - Wick rejection or pivot high
    - Penalty for weak ADX
    """

    def __init__(self):
        """Initialize TREND_DOWN generator."""
        super().__init__(RegimeType.TREND_DOWN)

    def can_generate(self, regime: RegimeType) -> bool:
        """Check if this generator handles TREND_DOWN."""
        return regime == RegimeType.TREND_DOWN

    def generate(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        params: OptimParams,
    ) -> list[EntryEvent]:
        """Generate SHORT entries for TREND_DOWN regime."""
        if not candles or not features:
            return []

        closes = features["closes"]
        atr = features["atr"]
        rsi = features["rsi"]
        dist = features["dist_ema_atr"]
        up_w = features["up_wick"]
        piv_h = features["pivot_high"]
        adx = features["adx"]

        n = len(candles)
        warmup = self._calculate_warmup(features, params)
        raw: list[EntryEvent] = []

        for i in range(n):
            if i < warmup:
                continue

            score = 0.0
            reasons: list[str] = []

            d = dist[i]
            r = rsi[i]
            wick_short = up_w[i]
            is_piv_high = piv_h[i] > 0.5

            # Pullback = price above EMA_slow
            if d >= 0.0 and abs(d) <= params.pullback_atr * 2.2:
                score += self._clamp(abs(d) / max(1e-12, params.pullback_atr), 0.0, 1.0) * 0.55
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

                if score >= params.min_confidence:
                    raw.append(
                        EntryEvent(
                            timestamp=candles[i].get("timestamp"),
                            side=EntrySide.SHORT,
                            confidence=float(self._clamp(score, 0.0, 1.0)),
                            price=closes[i],
                            reason_tags=reasons,
                            regime=self.regime,
                        )
                    )

        return raw

    def _calculate_warmup(self, features: dict[str, list[float]], params: OptimParams) -> int:
        """Calculate warmup period for indicators."""
        n = len(features.get("closes", []))
        warmup = min(50, max(20, int(max(params.ema_slow, params.bb_period, params.adx_period) * 0.6)))
        return min(warmup, n - 1)
