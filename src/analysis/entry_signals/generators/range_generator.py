"""Range regime entry generator.

Handles mean-reversion entries at Bollinger Band extremes.
"""

from __future__ import annotations

from typing import Any

from ..entry_signal_engine import EntryEvent, EntrySide, OptimParams, RegimeType
from .base_generator import BaseEntryGenerator


class RangeGenerator(BaseEntryGenerator):
    """Generator for RANGE (sideways) mean-reversion entries.

    Logic:
    - Oversold: BB% low + RSI low → LONG
    - Overbought: BB% high + RSI high → SHORT
    - Optional wick rejection or pivot confirmation
    """

    def __init__(self):
        """Initialize RANGE generator."""
        super().__init__(RegimeType.RANGE)

    def can_generate(self, regime: RegimeType) -> bool:
        """Check if this generator handles RANGE."""
        return regime == RegimeType.RANGE

    def generate(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        params: OptimParams,
    ) -> list[EntryEvent]:
        """Generate mean-reversion entries for RANGE regime."""
        if not candles or not features:
            return []

        closes = features["closes"]
        rsi = features["rsi"]
        bbp = features["bb_percent"]
        lo_w = features["lo_wick"]
        up_w = features["up_wick"]
        piv_l = features["pivot_low"]
        piv_h = features["pivot_high"]

        n = len(candles)
        warmup = self._calculate_warmup(features, params)
        raw: list[EntryEvent] = []

        for i in range(n):
            if i < warmup:
                continue

            bbp_i = bbp[i]
            r = rsi[i]
            wick_long = lo_w[i]
            wick_short = up_w[i]
            is_piv_low = piv_l[i] > 0.5
            is_piv_high = piv_h[i] > 0.5

            # LONG at oversold extreme
            if bbp_i <= params.bb_entry and r <= params.rsi_oversold:
                score = 0.55
                score += self._clamp((params.bb_entry - bbp_i) / max(1e-12, params.bb_entry), 0.0, 1.0) * 0.25
                reasons = ["range_bb_oversold", "rsi_oversold"]

                if wick_long >= params.wick_reject or is_piv_low:
                    score += 0.15
                    reasons.append("rejection_or_pivot_low")

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

            # SHORT at overbought extreme
            elif bbp_i >= (1.0 - params.bb_entry) and r >= params.rsi_overbought:
                score = 0.55
                score += self._clamp((bbp_i - (1.0 - params.bb_entry)) / max(1e-12, params.bb_entry), 0.0, 1.0) * 0.25
                reasons = ["range_bb_overbought", "rsi_overbought"]

                if wick_short >= params.wick_reject or is_piv_high:
                    score += 0.15
                    reasons.append("rejection_or_pivot_high")

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
