"""Regime Engine for Tradingbot.

Classifies market regime (Trend/Range) and volatility level
based on technical indicators for strategy selection.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .models import (
    FeatureVector,
    RegimeState,
    RegimeType,
    VolatilityLevel,
)

logger = logging.getLogger(__name__)


class RegimeEngine:
    """Engine for market regime classification.

    Analyzes technical indicators to determine:
    - Trend direction (up/down/range)
    - Volatility level (low/normal/high/extreme)

    Classification is used for:
    - Daily strategy selection
    - Entry/exit parameter adjustment
    - Risk management tuning
    """

    # ADX thresholds for trend strength
    ADX_TRENDING = 25.0      # Above = trending market
    ADX_STRONG_TREND = 40.0  # Above = strong trend
    ADX_WEAK = 20.0          # Below = ranging/choppy

    # DI thresholds
    DI_MIN_DIFF = 5.0  # Minimum +DI/-DI difference for trend direction

    # Volatility thresholds (ATR as % of price)
    VOL_LOW_PCT = 0.5      # Below = low volatility
    VOL_NORMAL_PCT = 1.5   # Below = normal
    VOL_HIGH_PCT = 3.0     # Below = high, above = extreme

    # BB width thresholds (as ratio)
    BB_SQUEEZE = 0.02      # Below = squeeze/low vol
    BB_EXPANSION = 0.06    # Above = expansion/high vol

    # RSI extremes for trend confirmation
    RSI_OVERBOUGHT = 70.0
    RSI_OVERSOLD = 30.0
    RSI_STRONG_UP = 60.0
    RSI_STRONG_DOWN = 40.0

    def __init__(
        self,
        adx_trending: float | None = None,
        vol_high_pct: float | None = None,
        use_rsi_confirmation: bool = True
    ):
        """Initialize regime engine.

        Args:
            adx_trending: Custom ADX threshold for trending
            vol_high_pct: Custom volatility high threshold
            use_rsi_confirmation: Use RSI to confirm trend direction
        """
        if adx_trending is not None:
            self.ADX_TRENDING = adx_trending
        if vol_high_pct is not None:
            self.VOL_HIGH_PCT = vol_high_pct
        self.use_rsi_confirmation = use_rsi_confirmation

        logger.info(
            f"RegimeEngine initialized (ADX threshold={self.ADX_TRENDING}, "
            f"vol_high={self.VOL_HIGH_PCT}%)"
        )

    def classify(self, features: FeatureVector) -> RegimeState:
        """Classify current market regime from features.

        Args:
            features: Feature vector with indicator values

        Returns:
            RegimeState with regime and volatility classification
        """
        # Classify trend/range
        regime, regime_conf = self._classify_regime(features)

        # Classify volatility
        volatility, vol_conf = self._classify_volatility(features)

        # Build regime state with underlying metrics
        state = RegimeState(
            timestamp=features.timestamp,
            regime=regime,
            volatility=volatility,
            regime_confidence=regime_conf,
            volatility_confidence=vol_conf,
            adx_value=features.adx,
            atr_pct=self._calc_atr_pct(features),
            bb_width_pct=features.bb_width
        )

        logger.debug(
            f"Regime classified: {state.regime_label} "
            f"(regime_conf={regime_conf:.2f}, vol_conf={vol_conf:.2f})"
        )

        return state

    def _classify_regime(
        self,
        features: FeatureVector
    ) -> tuple[RegimeType, float]:
        """Classify regime as trend up/down or range.

        Returns:
            (RegimeType, confidence)
        """
        adx = features.adx
        plus_di = features.plus_di
        minus_di = features.minus_di
        rsi = features.rsi_14

        # Default to unknown with low confidence
        if adx is None:
            return RegimeType.UNKNOWN, 0.3

        # Ranging market
        if adx < self.ADX_WEAK:
            return RegimeType.RANGE, min(0.9, 1.0 - (adx / self.ADX_WEAK) * 0.5)

        # Trending market - determine direction
        if adx >= self.ADX_TRENDING:
            # Use DI for direction
            if plus_di is not None and minus_di is not None:
                di_diff = plus_di - minus_di

                if di_diff > self.DI_MIN_DIFF:
                    # Uptrend
                    direction = RegimeType.TREND_UP
                elif di_diff < -self.DI_MIN_DIFF:
                    # Downtrend
                    direction = RegimeType.TREND_DOWN
                else:
                    # Inconclusive DI
                    direction = RegimeType.RANGE
            else:
                # No DI data, use RSI as fallback
                if rsi is not None:
                    if rsi > self.RSI_STRONG_UP:
                        direction = RegimeType.TREND_UP
                    elif rsi < self.RSI_STRONG_DOWN:
                        direction = RegimeType.TREND_DOWN
                    else:
                        direction = RegimeType.UNKNOWN
                else:
                    direction = RegimeType.UNKNOWN

            # Calculate confidence based on ADX strength
            if adx >= self.ADX_STRONG_TREND:
                confidence = 0.9
            elif adx >= self.ADX_TRENDING:
                confidence = 0.6 + (adx - self.ADX_TRENDING) / (self.ADX_STRONG_TREND - self.ADX_TRENDING) * 0.3
            else:
                confidence = 0.5

            # RSI confirmation adjustment
            if self.use_rsi_confirmation and rsi is not None:
                if direction == RegimeType.TREND_UP and rsi > self.RSI_STRONG_UP:
                    confidence = min(1.0, confidence + 0.1)
                elif direction == RegimeType.TREND_DOWN and rsi < self.RSI_STRONG_DOWN:
                    confidence = min(1.0, confidence + 0.1)
                elif direction == RegimeType.TREND_UP and rsi < self.RSI_STRONG_DOWN:
                    confidence = max(0.3, confidence - 0.2)  # Contradiction
                elif direction == RegimeType.TREND_DOWN and rsi > self.RSI_STRONG_UP:
                    confidence = max(0.3, confidence - 0.2)  # Contradiction

            return direction, confidence

        # Borderline case
        return RegimeType.RANGE, 0.5

    def _classify_volatility(
        self,
        features: FeatureVector
    ) -> tuple[VolatilityLevel, float]:
        """Classify volatility level.

        Uses ATR % and BB width as primary indicators.

        Returns:
            (VolatilityLevel, confidence)
        """
        atr_pct = self._calc_atr_pct(features)
        bb_width = features.bb_width

        # Score from ATR
        atr_score = 0.0
        atr_conf = 0.5

        if atr_pct is not None:
            if atr_pct < self.VOL_LOW_PCT:
                atr_score = 0.0
                atr_conf = 0.8
            elif atr_pct < self.VOL_NORMAL_PCT:
                atr_score = 1.0
                atr_conf = 0.7
            elif atr_pct < self.VOL_HIGH_PCT:
                atr_score = 2.0
                atr_conf = 0.75
            else:
                atr_score = 3.0
                atr_conf = 0.85

        # Score from BB width
        bb_score = 0.0
        bb_conf = 0.5

        if bb_width is not None:
            if bb_width < self.BB_SQUEEZE:
                bb_score = 0.0
                bb_conf = 0.75
            elif bb_width < 0.04:
                bb_score = 1.0
                bb_conf = 0.65
            elif bb_width < self.BB_EXPANSION:
                bb_score = 2.0
                bb_conf = 0.7
            else:
                bb_score = 3.0
                bb_conf = 0.8

        # Combine scores (weighted average)
        if atr_pct is not None and bb_width is not None:
            combined_score = atr_score * 0.6 + bb_score * 0.4
            combined_conf = atr_conf * 0.6 + bb_conf * 0.4
        elif atr_pct is not None:
            combined_score = atr_score
            combined_conf = atr_conf * 0.8  # Reduce confidence without BB
        elif bb_width is not None:
            combined_score = bb_score
            combined_conf = bb_conf * 0.8
        else:
            return VolatilityLevel.NORMAL, 0.3

        # Map score to level
        if combined_score < 0.5:
            level = VolatilityLevel.LOW
        elif combined_score < 1.5:
            level = VolatilityLevel.NORMAL
        elif combined_score < 2.5:
            level = VolatilityLevel.HIGH
        else:
            level = VolatilityLevel.EXTREME

        return level, combined_conf

    def _calc_atr_pct(self, features: FeatureVector) -> float | None:
        """Calculate ATR as percentage of price."""
        if features.atr_14 is None or features.close <= 0:
            return None
        return (features.atr_14 / features.close) * 100

    def is_favorable_for_trend(self, state: RegimeState) -> bool:
        """Check if regime is favorable for trend-following strategies.

        Args:
            state: Current regime state

        Returns:
            True if trend-following is favorable
        """
        return (
            state.is_trending and
            state.regime_confidence >= 0.6 and
            state.volatility != VolatilityLevel.EXTREME
        )

    def is_favorable_for_range(self, state: RegimeState) -> bool:
        """Check if regime is favorable for range/mean-reversion strategies.

        Args:
            state: Current regime state

        Returns:
            True if range trading is favorable
        """
        return (
            state.regime == RegimeType.RANGE and
            state.regime_confidence >= 0.6 and
            state.volatility in (VolatilityLevel.LOW, VolatilityLevel.NORMAL)
        )

    def get_risk_multiplier(self, state: RegimeState) -> float:
        """Get risk adjustment multiplier based on volatility.

        Args:
            state: Current regime state

        Returns:
            Multiplier for position sizing (0.5 to 1.0)
        """
        multipliers = {
            VolatilityLevel.LOW: 1.0,
            VolatilityLevel.NORMAL: 1.0,
            VolatilityLevel.HIGH: 0.75,
            VolatilityLevel.EXTREME: 0.5,
        }
        return multipliers.get(state.volatility, 0.75)

    def get_trailing_multiplier(self, state: RegimeState) -> float:
        """Get trailing stop distance multiplier based on volatility.

        Args:
            state: Current regime state

        Returns:
            Multiplier for trailing distance (1.0 to 2.0)
        """
        multipliers = {
            VolatilityLevel.LOW: 1.0,
            VolatilityLevel.NORMAL: 1.2,
            VolatilityLevel.HIGH: 1.5,
            VolatilityLevel.EXTREME: 2.0,
        }
        return multipliers.get(state.volatility, 1.2)

    def detect_regime_change(
        self,
        current: RegimeState,
        previous: RegimeState | None
    ) -> dict[str, bool]:
        """Detect if regime has changed significantly.

        Args:
            current: Current regime state
            previous: Previous regime state

        Returns:
            Dict with change flags
        """
        if previous is None:
            return {
                'regime_changed': False,
                'volatility_changed': False,
                'significant_change': False
            }

        regime_changed = current.regime != previous.regime
        vol_changed = current.volatility != previous.volatility

        # Significant = trend flip or extreme volatility transition
        significant = (
            (previous.is_trending and not current.is_trending) or
            (not previous.is_trending and current.is_trending) or
            (previous.regime == RegimeType.TREND_UP and current.regime == RegimeType.TREND_DOWN) or
            (previous.regime == RegimeType.TREND_DOWN and current.regime == RegimeType.TREND_UP) or
            (current.volatility == VolatilityLevel.EXTREME and previous.volatility != VolatilityLevel.EXTREME)
        )

        return {
            'regime_changed': regime_changed,
            'volatility_changed': vol_changed,
            'significant_change': significant
        }
