"""Squeeze regime entry generator.

Handles breakout entries from narrow Bollinger Band squeezes.
"""

from __future__ import annotations

from typing import Any

from ..entry_signal_engine import EntryEvent, EntrySide, OptimParams, RegimeType
from .base_generator import BaseEntryGenerator


class SqueezeGenerator(BaseEntryGenerator):
    """Generator for SQUEEZE breakout entries.

    Logic:
    - Narrow BB width (squeeze condition)
    - Breakout above/below bands by ATR threshold
    - Volume spike confirmation
    """

    def __init__(self):
        """Initialize SQUEEZE generator."""
        super().__init__(RegimeType.SQUEEZE)

    def can_generate(self, regime: RegimeType) -> bool:
        """Check if this generator handles SQUEEZE."""
        return regime == RegimeType.SQUEEZE

    def generate(
        self,
        candles: list[dict[str, Any]],
        features: dict[str, list[float]],
        params: OptimParams,
    ) -> list[EntryEvent]:
        """Generate breakout entries for SQUEEZE regime."""
        if not candles or not features:
            return []

        closes = features["closes"]
        atr = features["atr"]
        bb_up = features["bb_up"]
        bb_lo = features["bb_lo"]
        bb_width = features["bb_width"]
        vol = features["volume"]
        vol_sma = features["vol_sma"]

        n = len(candles)
        warmup = self._calculate_warmup(features, params)
        raw: list[EntryEvent] = []

        for i in range(n):
            if i < warmup:
                continue

            # Must still be in squeeze (narrow bands)
            if bb_width[i] > params.squeeze_bb_width * 1.4:
                continue

            a = max(1e-12, atr[i])
            conf_vol = (vol[i] / max(1e-12, vol_sma[i])) if i < len(vol_sma) else 1.0

            # Require volume spike
            if conf_vol < params.vol_spike_factor:
                continue

            # LONG breakout above upper band
            if closes[i] > (bb_up[i] + params.breakout_atr * a):
                score = 0.62 + self._clamp((conf_vol - params.vol_spike_factor) / 1.5, 0.0, 1.0) * 0.25
                reasons = ["squeeze_breakout_up", "vol_spike"]

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

            # SHORT breakout below lower band
            elif closes[i] < (bb_lo[i] - params.breakout_atr * a):
                score = 0.62 + self._clamp((conf_vol - params.vol_spike_factor) / 1.5, 0.0, 1.0) * 0.25
                reasons = ["squeeze_breakout_down", "vol_spike"]

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
