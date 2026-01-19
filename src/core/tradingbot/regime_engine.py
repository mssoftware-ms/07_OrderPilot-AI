"""Regime Engine for Tradingbot.

Classifies market regime (Trend/Range) and volatility level
based on technical indicators for strategy selection.

⚠️ DEPRECATION NOTICE:
This hardcoded regime engine is being replaced by RegimeEngineJSON.
New code should use:
    from src.core.tradingbot.regime_engine_json import RegimeEngineJSON

Migration path:
    OLD: RegimeEngine().classify(features) -> RegimeState
    NEW: RegimeEngineJSON().classify_from_config(data, config_path) -> RegimeState

Advantages of JSON-based approach:
- Configurable thresholds (no hardcoded values)
- Uses IndicatorEngine for calculations
- Uses RegimeDetector for condition evaluation
- Supports multi-regime detection with priorities
- Better testability and maintainability

This legacy engine will remain available for backward compatibility.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .models import (
    Direction,
    ExtendedRegimeState,
    FeatureVector,
    RegimeID,
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

    # MOMENTUM/PRICE-BASED TREND DETECTION (ADX fallback)
    # For detecting strong moves even when ADX is low
    STRONG_MOVE_PCT = 2.0    # 2% move over lookback = strong trend
    EXTREME_MOVE_PCT = 4.0   # 4% move = extreme trend (overrides ADX)

    # VOLUME MOMENTUM thresholds
    VOLUME_SPIKE_RATIO = 1.5  # Volume > 1.5x MA = high volume confirmation
    VOLUME_EXTREME_RATIO = 2.5  # Volume > 2.5x MA = extreme volume

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

    def classify_extended(self, features: FeatureVector) -> ExtendedRegimeState:
        """Classify market regime using extended R0-R5 system.

        Uses composite detection with priority-based logic:
        1. R5 if |OBI| very high (orderflow dominant)
        2. R3 if Squeeze ON or BBWidth very low (breakout setup)
        3. R4 if ATRP or BBWidth very high (high volatility)
        4. R1 if ADX >25 or CHOP <38.2 (trending)
        5. R2 if ADX <20 or CHOP >61.8 (ranging)
        6. R0 otherwise (neutral/unclear)

        Args:
            features: Feature vector with indicator values

        Returns:
            ExtendedRegimeState with regime_id (R0-R5), direction, features
        """
        # 1. Calculate segment features
        segment_features = self._calc_segment_features(features)

        # 2. Composite detection with priority logic
        regime_id, confidence = self._composite_detect(segment_features, features)

        # 3. Detect direction for the regime
        direction = self._detect_direction_for_regime(regime_id, segment_features, features)

        # 4. Classify volatility (reuse existing logic)
        volatility, _ = self._classify_volatility(features)

        # 5. Build extended regime state
        state = ExtendedRegimeState(
            timestamp=features.timestamp,
            regime_id=regime_id,
            direction=direction,
            volatility=volatility,
            confidence=confidence,
            features=segment_features,
            bars_in_regime=0,  # Will be updated by RegimeTracker
            regime_start_time=None,
            prev_regime_id=None
        )

        logger.debug(
            f"Extended regime classified: {state.regime_label} "
            f"(confidence={confidence:.2f})"
        )

        return state

    def _calc_segment_features(self, features: FeatureVector) -> dict[str, float | None]:
        """Calculate segment features for regime detection and scoring.

        Features:
        - atrp: ATR as percentage of price
        - bbwidth: Bollinger Band width
        - bbwidth_pctl: BBWidth percentile (requires historical data - placeholder)
        - atrp_pctl: ATRP percentile (requires historical data - placeholder)
        - range_pct: High-Low range as percentage (for current bar)
        - squeeze_on: Squeeze indicator (BBWidth < threshold)
        - obi: Order Book Imbalance (if available)
        - spread_bps: Spread in basis points (if available)
        - depth_bid, depth_ask: Order book depth (if available)
        - adx: ADX value
        - chop: Choppiness Index (placeholder - needs implementation)

        Args:
            features: Feature vector

        Returns:
            Dict with calculated segment features
        """
        segment = {}

        # ATRP (ATR as %)
        atrp = self._calc_atr_pct(features)
        segment["atrp"] = atrp

        # BBWidth
        segment["bbwidth"] = features.bb_width

        # Percentiles (placeholder - would need rolling window)
        # In full implementation, this would track last N bars
        segment["bbwidth_pctl"] = None  # TODO: Implement with rolling stats
        segment["atrp_pctl"] = None     # TODO: Implement with rolling stats

        # Range% for current bar
        if features.high and features.low and features.close > 0:
            mid = (features.high + features.low) / 2
            range_pct = ((features.high - features.low) / mid) * 100 if mid > 0 else 0
            segment["range_pct"] = range_pct
        else:
            segment["range_pct"] = None

        # Squeeze detection
        if features.bb_width is not None:
            segment["squeeze_on"] = features.bb_width < self.BB_SQUEEZE
        else:
            segment["squeeze_on"] = False

        # Orderflow/Liquidity (placeholder - would need order book data)
        segment["obi"] = None           # Order Book Imbalance
        segment["obi_pctl"] = None      # OBI percentile
        segment["spread_bps"] = None    # Spread in basis points
        segment["depth_bid"] = None     # Bid depth
        segment["depth_ask"] = None     # Ask depth

        # Existing indicators
        segment["adx"] = features.adx
        segment["plus_di"] = features.plus_di
        segment["minus_di"] = features.minus_di
        segment["rsi"] = features.rsi_14

        # CHOP (placeholder - would need implementation)
        segment["chop"] = None  # TODO: Implement Choppiness Index

        return segment

    def _composite_detect(
        self,
        segment_features: dict[str, float | None],
        features: FeatureVector
    ) -> tuple[RegimeID, float]:
        """Composite regime detection with priority-based logic.

        Priority order:
        1. R5 if |OBI| > P90 (orderflow dominant)
        2. R3 if Squeeze ON or BBWidth < P20 (breakout setup)
        3. R4 if ATRP > P80 or BBWidth > P80 (high volatility)
        4. R1 if ADX > 25 or CHOP < 38.2 (trending)
        5. R2 if ADX < 20 or CHOP > 61.8 (ranging)
        6. R0 otherwise (neutral/unclear)

        Args:
            segment_features: Calculated segment features
            features: Original feature vector

        Returns:
            (RegimeID, confidence)
        """
        # Priority 1: Orderflow dominant (R5)
        obi = segment_features.get("obi")
        obi_pctl = segment_features.get("obi_pctl")
        if obi is not None and obi_pctl is not None and abs(obi) > 0.7:
            # In full implementation: obi_pctl > 90
            # For now: use absolute threshold
            return RegimeID.R5, 0.8

        # Priority 2: Breakout Setup (R3)
        squeeze_on = segment_features.get("squeeze_on", False)
        bbwidth_pctl = segment_features.get("bbwidth_pctl")
        if squeeze_on:
            return RegimeID.R3, 0.85
        # Placeholder: bbwidth_pctl < 20 would also trigger R3
        # if bbwidth_pctl is not None and bbwidth_pctl < 20:
        #     return RegimeID.R3, 0.75

        # Priority 3: High Volatility (R4)
        atrp = segment_features.get("atrp")
        atrp_pctl = segment_features.get("atrp_pctl")
        bbwidth = segment_features.get("bbwidth")

        # Placeholder: use absolute thresholds instead of percentiles
        if atrp is not None and atrp > self.VOL_HIGH_PCT:
            return RegimeID.R4, 0.8
        if bbwidth is not None and bbwidth > self.BB_EXPANSION:
            return RegimeID.R4, 0.75
        # Full implementation: atrp_pctl > 80 or bbwidth_pctl > 80

        # Priority 4: Trend (R1)
        adx = segment_features.get("adx")
        chop = segment_features.get("chop")

        if adx is not None and adx >= self.ADX_TRENDING:
            return RegimeID.R1, min(0.9, 0.6 + (adx - self.ADX_TRENDING) / 20 * 0.3)
        if chop is not None and chop < 38.2:
            return RegimeID.R1, 0.7

        # Priority 5: Range (R2)
        if adx is not None and adx < self.ADX_WEAK:
            return RegimeID.R2, 0.8
        if chop is not None and chop > 61.8:
            return RegimeID.R2, 0.75

        # Default: Neutral/Unclear (R0)
        return RegimeID.R0, 0.4

    def _detect_direction_for_regime(
        self,
        regime_id: RegimeID,
        segment_features: dict[str, float | None],
        features: FeatureVector
    ) -> Direction:
        """Detect directional bias for a given regime.

        Direction detection logic by regime:
        - R5: sign(OBI) if available, else NONE
        - R1: UP if +DI > -DI (or Ichimoku above cloud), else DOWN
        - R3: NONE until Donchian breakout, then UP/DOWN
        - R0, R2, R4: NONE (no clear direction)

        Args:
            regime_id: Detected regime ID
            segment_features: Calculated segment features
            features: Original feature vector

        Returns:
            Direction enum (UP, DOWN, NONE)
        """
        # R5: Orderflow direction
        if regime_id == RegimeID.R5:
            obi = segment_features.get("obi")
            if obi is not None:
                if obi > 0:
                    return Direction.UP
                elif obi < 0:
                    return Direction.DOWN
            return Direction.NONE

        # R1: Trend direction
        if regime_id == RegimeID.R1:
            plus_di = segment_features.get("plus_di")
            minus_di = segment_features.get("minus_di")

            if plus_di is not None and minus_di is not None:
                di_diff = plus_di - minus_di
                if di_diff > self.DI_MIN_DIFF:
                    return Direction.UP
                if di_diff < -self.DI_MIN_DIFF:
                    return Direction.DOWN

            # Fallback: use RSI
            rsi = segment_features.get("rsi")
            if rsi is not None:
                if rsi > self.RSI_STRONG_UP:
                    return Direction.UP
                if rsi < self.RSI_STRONG_DOWN:
                    return Direction.DOWN

            return Direction.NONE

        # R3: Breakout direction (placeholder - would need Donchian)
        # For now: NONE until breakout detected
        if regime_id == RegimeID.R3:
            # TODO: Check Donchian Upper/Lower breakout
            # if close > donchian_upper: return Direction.UP
            # if close < donchian_lower: return Direction.DOWN
            return Direction.NONE

        # R0, R2, R4: No clear direction
        return Direction.NONE

    def _classify_regime(
        self,
        features: FeatureVector
    ) -> tuple[RegimeType, float]:
        """Classify regime as trend up/down or range.

        Enhanced with momentum-based detection that works even with low ADX.

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

        # PRIORITY 1: Check for strong price moves (even if ADX is low)
        # This catches fast drops/rallies that ADX misses
        strong_move = self._detect_strong_move(features)
        if strong_move is not None:
            direction, move_pct, confidence = strong_move
            # If extreme move (>4%), ALWAYS override ADX
            if abs(move_pct) >= self.EXTREME_MOVE_PCT:
                logger.info(
                    f"⚡ EXTREME MOVE detected: {move_pct:+.2f}% → {direction.name} "
                    f"(overriding ADX={adx:.1f})"
                )
                return direction, confidence
            # If strong move (>2%) and ADX is weak, use momentum
            elif abs(move_pct) >= self.STRONG_MOVE_PCT and adx < self.ADX_TRENDING:
                logger.info(
                    f"💪 STRONG MOVE detected: {move_pct:+.2f}% with low ADX={adx:.1f} → {direction.name}"
                )
                return direction, confidence

        # PRIORITY 2: ADX-based classification (original logic)
        # Ranging market
        if adx < self.ADX_WEAK:
            return RegimeType.RANGE, min(0.9, 1.0 - (adx / self.ADX_WEAK) * 0.5)

        # Trending market - determine direction
        if adx >= self.ADX_TRENDING:
            direction = self._resolve_trend_direction(plus_di, minus_di, rsi)
            confidence = self._calc_trend_confidence(adx)
            confidence = self._apply_rsi_confirmation(direction, rsi, confidence)
            return direction, confidence

        # Borderline case
        return RegimeType.RANGE, 0.5

    def _resolve_trend_direction(
        self,
        plus_di: float | None,
        minus_di: float | None,
        rsi: float | None,
    ) -> RegimeType:
        if plus_di is not None and minus_di is not None:
            di_diff = plus_di - minus_di
            if di_diff > self.DI_MIN_DIFF:
                return RegimeType.TREND_UP
            if di_diff < -self.DI_MIN_DIFF:
                return RegimeType.TREND_DOWN
            return RegimeType.RANGE

        if rsi is not None:
            if rsi > self.RSI_STRONG_UP:
                return RegimeType.TREND_UP
            if rsi < self.RSI_STRONG_DOWN:
                return RegimeType.TREND_DOWN
            return RegimeType.UNKNOWN

        return RegimeType.UNKNOWN

    def _calc_trend_confidence(self, adx: float) -> float:
        if adx >= self.ADX_STRONG_TREND:
            return 0.9
        if adx >= self.ADX_TRENDING:
            return 0.6 + (adx - self.ADX_TRENDING) / (
                self.ADX_STRONG_TREND - self.ADX_TRENDING
            ) * 0.3
        return 0.5

    def _apply_rsi_confirmation(
        self,
        direction: RegimeType,
        rsi: float | None,
        confidence: float,
    ) -> float:
        if not (self.use_rsi_confirmation and rsi is not None):
            return confidence
        if direction == RegimeType.TREND_UP and rsi > self.RSI_STRONG_UP:
            return min(1.0, confidence + 0.1)
        if direction == RegimeType.TREND_DOWN and rsi < self.RSI_STRONG_DOWN:
            return min(1.0, confidence + 0.1)
        if direction == RegimeType.TREND_UP and rsi < self.RSI_STRONG_DOWN:
            return max(0.3, confidence - 0.2)
        if direction == RegimeType.TREND_DOWN and rsi > self.RSI_STRONG_UP:
            return max(0.3, confidence - 0.2)
        return confidence

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

    def _detect_strong_move(
        self,
        features: FeatureVector
    ) -> tuple[RegimeType, float, float] | None:
        """Detect strong price moves based on momentum and volume.

        Uses multiple indicators:
        - SMA slope (fast SMA vs slow SMA)
        - RSI extremes
        - Price position relative to BBands
        - Volume confirmation (volume spike = higher confidence)

        Returns:
            (RegimeType, move_percentage, confidence) or None if no strong move
        """
        # Get indicators
        close = features.close
        sma_fast = features.sma_20
        sma_slow = features.sma_50
        rsi = features.rsi_14
        bb_upper = features.bb_upper
        bb_lower = features.bb_lower
        volume = features.volume
        volume_sma = features.volume_sma

        # Validate required indicators
        if None in (close, sma_fast, sma_slow):
            return None

        # 1. CALCULATE PRICE MOMENTUM
        # Method A: SMA crossover distance (measures trend strength)
        sma_diff_pct = ((sma_fast - sma_slow) / sma_slow) * 100 if sma_slow > 0 else 0

        # Method B: Price vs SMA distance (current momentum)
        price_vs_fast_pct = ((close - sma_fast) / sma_fast) * 100 if sma_fast > 0 else 0

        # Combined momentum score
        momentum_pct = (sma_diff_pct * 0.6) + (price_vs_fast_pct * 0.4)

        # 2. VOLUME CONFIRMATION
        volume_multiplier = 1.0
        if volume is not None and volume_sma is not None and volume_sma > 0:
            volume_ratio = volume / volume_sma
            if volume_ratio >= self.VOLUME_EXTREME_RATIO:
                volume_multiplier = 1.3  # +30% confidence with extreme volume
                logger.debug(f"📊 EXTREME VOLUME: {volume_ratio:.2f}x average")
            elif volume_ratio >= self.VOLUME_SPIKE_RATIO:
                volume_multiplier = 1.15  # +15% confidence with high volume
                logger.debug(f"📊 HIGH VOLUME: {volume_ratio:.2f}x average")

        # 3. RSI CONFIRMATION
        rsi_multiplier = 1.0
        if rsi is not None:
            # Strong RSI extremes add confidence
            if rsi > self.RSI_OVERBOUGHT or rsi < self.RSI_OVERSOLD:
                rsi_multiplier = 1.1  # +10% confidence

        # 4. BOLLINGER BAND POSITION
        bb_multiplier = 1.0
        if bb_upper is not None and bb_lower is not None:
            bb_range = bb_upper - bb_lower
            if bb_range > 0:
                # Price near/beyond bands = stronger move
                if close > bb_upper:
                    bb_multiplier = 1.15  # Price above upper band
                elif close < bb_lower:
                    bb_multiplier = 1.15  # Price below lower band

        # 5. DETERMINE DIRECTION AND BASE CONFIDENCE
        abs_momentum = abs(momentum_pct)

        if abs_momentum < self.STRONG_MOVE_PCT:
            return None  # Not a strong move

        # Calculate base confidence (0.6 for 2%, 0.9 for 4%+)
        if abs_momentum >= self.EXTREME_MOVE_PCT:
            base_confidence = 0.9
        else:
            # Linear interpolation between 0.6 and 0.9
            base_confidence = 0.6 + ((abs_momentum - self.STRONG_MOVE_PCT) /
                                     (self.EXTREME_MOVE_PCT - self.STRONG_MOVE_PCT)) * 0.3

        # Apply multipliers (volume, RSI, BB)
        final_confidence = min(1.0, base_confidence * volume_multiplier * rsi_multiplier * bb_multiplier)

        # Determine direction
        if momentum_pct > 0:
            direction = RegimeType.TREND_UP
        else:
            direction = RegimeType.TREND_DOWN

        logger.debug(
            f"💹 Strong move: {momentum_pct:+.2f}% ({direction.name}), "
            f"confidence={final_confidence:.2f} (base={base_confidence:.2f}, "
            f"vol={volume_multiplier:.2f}x, rsi={rsi_multiplier:.2f}x, bb={bb_multiplier:.2f}x)"
        )

        return direction, abs_momentum, final_confidence

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


class RegimeTracker:
    """Anti-flap regime tracker with confirmation and cooldown logic.

    Prevents regime oscillation by requiring N consecutive bars
    in new regime before switching, plus optional cooldown period.

    Configuration:
    - confirm_bars: Bars required in new regime before switching (default: 3)
    - cooldown_bars: Minimum bars before allowing another switch (default: 5)
    - min_segment_bars: Minimum bars per regime segment (default: 10)
    """

    def __init__(
        self,
        confirm_bars: int = 3,
        cooldown_bars: int = 5,
        min_segment_bars: int = 10
    ):
        """Initialize regime tracker.

        Args:
            confirm_bars: Consecutive bars needed to confirm regime change
            cooldown_bars: Minimum bars before allowing another switch
            min_segment_bars: Minimum bars per regime segment
        """
        self.confirm_bars = confirm_bars
        self.cooldown_bars = cooldown_bars
        self.min_segment_bars = min_segment_bars

        # State tracking
        self.current_regime_id: RegimeID = RegimeID.R0
        self.current_direction: Direction = Direction.NONE
        self.bars_in_current: int = 0
        self.regime_start_time: datetime | None = None

        # Candidate tracking (for confirmation)
        self.candidate_regime_id: RegimeID | None = None
        self.candidate_direction: Direction | None = None
        self.candidate_bars: int = 0

        # Cooldown tracking
        self.bars_since_last_switch: int = 0
        self.last_switch_time: datetime | None = None

        logger.info(
            f"RegimeTracker initialized (confirm={confirm_bars}, "
            f"cooldown={cooldown_bars}, min_segment={min_segment_bars})"
        )

    def update(
        self,
        detected_regime: ExtendedRegimeState,
        current_time: datetime
    ) -> ExtendedRegimeState:
        """Update tracker with newly detected regime.

        Applies anti-flap logic:
        1. If detected regime == current: reset candidate, increment bars_in_current
        2. If detected regime != current:
           a. Check if in cooldown → reject, return current
           b. Check if bars_in_current < min_segment → reject, return current
           c. If candidate matches detected → increment candidate_bars
           d. If candidate != detected → reset candidate to detected
           e. If candidate_bars >= confirm_bars → SWITCH to candidate

        Args:
            detected_regime: Newly detected regime from classify_extended()
            current_time: Current bar timestamp

        Returns:
            Final regime state (may be current or newly confirmed)
        """
        detected_id = detected_regime.regime_id
        detected_dir = detected_regime.direction

        # Case 1: Detected regime matches current → no change
        if detected_id == self.current_regime_id and detected_dir == self.current_direction:
            self.bars_in_current += 1
            self.bars_since_last_switch += 1
            # Reset candidate
            self.candidate_regime_id = None
            self.candidate_direction = None
            self.candidate_bars = 0

            # Update state object with tracking data
            detected_regime.bars_in_regime = self.bars_in_current
            detected_regime.regime_start_time = self.regime_start_time
            detected_regime.prev_regime_id = None

            return detected_regime

        # Case 2: Detected regime differs → apply anti-flap

        # Check cooldown
        if self.bars_since_last_switch < self.cooldown_bars:
            logger.debug(
                f"Regime change rejected (cooldown): {detected_id} "
                f"(bars_since_switch={self.bars_since_last_switch} < {self.cooldown_bars})"
            )
            # Return current regime, not detected
            return self._build_current_state(current_time, detected_regime)

        # Check min segment length
        if self.bars_in_current < self.min_segment_bars:
            logger.debug(
                f"Regime change rejected (min_segment): {detected_id} "
                f"(bars_in_current={self.bars_in_current} < {self.min_segment_bars})"
            )
            return self._build_current_state(current_time, detected_regime)

        # Check if candidate matches detected
        if (
            self.candidate_regime_id == detected_id and
            self.candidate_direction == detected_dir
        ):
            # Increment candidate bars
            self.candidate_bars += 1
            logger.debug(
                f"Candidate confirmed: {detected_id} "
                f"({self.candidate_bars}/{self.confirm_bars})"
            )

            # Check if confirmed
            if self.candidate_bars >= self.confirm_bars:
                # SWITCH to new regime
                prev_regime = self.current_regime_id
                self.current_regime_id = detected_id
                self.current_direction = detected_dir
                self.bars_in_current = self.candidate_bars  # Start count from candidate
                self.regime_start_time = current_time
                self.bars_since_last_switch = 0
                self.last_switch_time = current_time

                # Reset candidate
                self.candidate_regime_id = None
                self.candidate_direction = None
                self.candidate_bars = 0

                logger.info(
                    f"Regime switched: {prev_regime} → {self.current_regime_id} "
                    f"(direction={self.current_direction.value})"
                )

                # Update state object
                detected_regime.bars_in_regime = self.bars_in_current
                detected_regime.regime_start_time = self.regime_start_time
                detected_regime.prev_regime_id = prev_regime

                return detected_regime
            else:
                # Still confirming → return current
                return self._build_current_state(current_time, detected_regime)

        else:
            # New candidate (different from current or existing candidate)
            logger.debug(
                f"New candidate: {detected_id} (direction={detected_dir.value})"
            )
            self.candidate_regime_id = detected_id
            self.candidate_direction = detected_dir
            self.candidate_bars = 1

            # Return current regime while confirming
            return self._build_current_state(current_time, detected_regime)

    def _build_current_state(
        self,
        current_time: datetime,
        template: ExtendedRegimeState
    ) -> ExtendedRegimeState:
        """Build regime state representing current tracked regime.

        Copies features/volatility from template but uses tracked regime_id.

        Args:
            current_time: Current timestamp
            template: Detected regime (for features/volatility)

        Returns:
            State with current tracked regime
        """
        return ExtendedRegimeState(
            timestamp=current_time,
            regime_id=self.current_regime_id,
            direction=self.current_direction,
            volatility=template.volatility,
            confidence=template.confidence,
            features=template.features,
            bars_in_regime=self.bars_in_current,
            regime_start_time=self.regime_start_time,
            prev_regime_id=None
        )

    def reset(self, initial_regime: ExtendedRegimeState) -> None:
        """Reset tracker to a specific regime state.

        Args:
            initial_regime: Regime to initialize with
        """
        self.current_regime_id = initial_regime.regime_id
        self.current_direction = initial_regime.direction
        self.bars_in_current = 0
        self.regime_start_time = initial_regime.timestamp
        self.candidate_regime_id = None
        self.candidate_direction = None
        self.candidate_bars = 0
        self.bars_since_last_switch = 0
        self.last_switch_time = None

        logger.info(f"RegimeTracker reset to {self.current_regime_id}")
