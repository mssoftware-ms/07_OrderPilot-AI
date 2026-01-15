"""Market Context Builder Configuration.

Configuration for MarketContext building process.

Module 1/4 of market_context_builder.py split (Lines 45-101)
"""

from __future__ import annotations

from .data_preflight import PreflightConfig


class MarketContextBuilderConfig:
    """Konfiguration für den MarketContext Builder."""

    def __init__(
        self,
        # Preflight
        preflight_enabled: bool = True,
        preflight_config: PreflightConfig | None = None,
        # Indicators
        ema_periods: list[int] | None = None,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        atr_period: int = 14,
        adx_period: int = 14,
        # Regime
        adx_strong_threshold: float = 30.0,
        adx_weak_threshold: float = 20.0,
        volatility_high_atr_pct: float = 3.0,
        volatility_extreme_atr_pct: float = 5.0,
        # Levels
        pivot_lookback: int = 20,
        level_min_touches: int = 2,
        level_zone_atr_mult: float = 0.3,
        top_n_levels: int = 5,
    ):
        self.preflight_enabled = preflight_enabled
        self.preflight_config = preflight_config or PreflightConfig()

        self.ema_periods = ema_periods or [9, 20, 50, 200]
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period
        self.adx_period = adx_period

        self.adx_strong_threshold = adx_strong_threshold
        self.adx_weak_threshold = adx_weak_threshold
        self.volatility_high_atr_pct = volatility_high_atr_pct
        self.volatility_extreme_atr_pct = volatility_extreme_atr_pct

        self.pivot_lookback = pivot_lookback
        self.level_min_touches = level_min_touches
        self.level_zone_atr_mult = level_zone_atr_mult
        self.top_n_levels = top_n_levels
