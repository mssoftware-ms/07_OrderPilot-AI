"""High volatility regime entry generator.

Handles conservative entries during high-volatility periods.
"""

from __future__ import annotations

from typing import Any

from ..entry_signal_engine import EntryEvent, EntrySide, OptimParams, RegimeType
from .base_generator import BaseEntryGenerator


class HighVolGenerator(BaseEntryGenerator):
    """Generator for HIGH_VOL regime entries.

    Logic:
    - Only trade extreme signals (avoid spam)
    - Stricter BB% and RSI thresholds
    - Reduced entry frequency for risk management
    """

    def __init__(self):
        """Initialize HIGH_VOL generator."""
        super().__init__(RegimeType.HIGH_VOL)

    def can_generate(self, regime: RegimeType) -> bool:
        """Check if this generator handles HIGH_VOL."""
        return regime == RegimeType.HIGH_VOL

    def generate(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        params: OptimParams,
    ) -> list[EntryEvent]:
        """Generate conservative entries for HIGH_VOL regime."""
        if not candles or not features:
            return []

        closes = features["closes"]
        rsi = features["rsi"]
        bbp = features["bb_percent"]

        n = len(candles)
        warmup = self._calculate_warmup(features, params)
        raw: list[EntryEvent] = []

        for i in range(n):
            if i < warmup:
                continue

            bbp_i = bbp[i]
            r = rsi[i]

            # LONG at extreme oversold (stricter than normal)
            if bbp_i <= (params.bb_entry * 0.75) and r <= (params.rsi_oversold - 3):
                score = 0.62
                reasons = ["high_vol_extreme_long"]

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

            # SHORT at extreme overbought
            elif bbp_i >= (1.0 - params.bb_entry * 0.75) and r >= (params.rsi_overbought + 3):
                score = 0.62
                reasons = ["high_vol_extreme_short"]

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
