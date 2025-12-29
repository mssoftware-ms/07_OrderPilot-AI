"""Entry Score Calculator for Tradingbot.

Calculates entry scores based on strategy rules and indicators.
Supports both generic scoring and strategy-specific rule evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import (
    FeatureVector,
    RegimeState,
    RegimeType,
    TradeSide,
)

if TYPE_CHECKING:
    from .strategy_catalog import EntryRule, StrategyDefinition


@dataclass
class EntryScoreResult:
    """Result of entry score calculation."""
    side: TradeSide
    score: float
    components: dict[str, float] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=list)
    meets_threshold: bool = False

class EntryScorer:
    """Calculates entry scores based on strategy rules and indicators.

    Supports both generic scoring and strategy-specific rule evaluation.
    """

    # Default indicator weights for generic scoring
    DEFAULT_WEIGHTS = {
        'trend_alignment': 0.25,
        'momentum_rsi': 0.15,
        'momentum_macd': 0.15,
        'trend_strength': 0.15,
        'mean_reversion': 0.15,
        'volume_confirmation': 0.10,
        'regime_match': 0.05,
    }

    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize entry scorer.

        Args:
            weights: Custom indicator weights
        """
        self.weights = weights or self.DEFAULT_WEIGHTS

    def calculate_score(
        self,
        features: FeatureVector,
        side: TradeSide,
        regime: RegimeState,
        strategy: "StrategyDefinition | None" = None
    ) -> EntryScoreResult:
        """Calculate entry score for a side.

        Args:
            features: Current feature vector
            side: Trade direction
            regime: Current market regime
            strategy: Optional strategy with custom rules

        Returns:
            EntryScoreResult with score and breakdown
        """
        if strategy and strategy.entry_rules:
            return self._score_with_rules(features, side, regime, strategy)
        return self._score_generic(features, side, regime)

    def _score_generic(
        self,
        features: FeatureVector,
        side: TradeSide,
        regime: RegimeState
    ) -> EntryScoreResult:
        """Generic scoring without strategy-specific rules."""
        components = {}
        reason_codes = []
        total_weight = 0.0
        weighted_score = 0.0

        # 1. Trend Alignment (SMA alignment)
        trend_score = self._score_trend_alignment(features, side)
        if trend_score > 0:
            reason_codes.append("TREND_ALIGNED")
        components['trend_alignment'] = trend_score
        weighted_score += trend_score * self.weights['trend_alignment']
        total_weight += self.weights['trend_alignment']

        # 2. Momentum RSI
        rsi_score = self._score_rsi_momentum(features, side)
        if rsi_score > 0.7:
            reason_codes.append("RSI_FAVORABLE")
        components['momentum_rsi'] = rsi_score
        weighted_score += rsi_score * self.weights['momentum_rsi']
        total_weight += self.weights['momentum_rsi']

        # 3. MACD Momentum
        macd_score = self._score_macd_momentum(features, side)
        if macd_score > 0.7:
            reason_codes.append("MACD_FAVORABLE")
        components['momentum_macd'] = macd_score
        weighted_score += macd_score * self.weights['momentum_macd']
        total_weight += self.weights['momentum_macd']

        # 4. Trend Strength (ADX)
        adx_score = self._score_trend_strength(features, regime)
        if adx_score > 0.7:
            reason_codes.append("STRONG_TREND")
        components['trend_strength'] = adx_score
        weighted_score += adx_score * self.weights['trend_strength']
        total_weight += self.weights['trend_strength']

        # 5. Mean Reversion (BB position)
        mr_score = self._score_mean_reversion(features, side)
        if mr_score > 0.7:
            reason_codes.append("MEAN_REVERSION_SETUP")
        components['mean_reversion'] = mr_score
        weighted_score += mr_score * self.weights['mean_reversion']
        total_weight += self.weights['mean_reversion']

        # 6. Volume Confirmation
        vol_score = self._score_volume(features)
        if vol_score > 0.7:
            reason_codes.append("VOLUME_CONFIRMED")
        components['volume_confirmation'] = vol_score
        weighted_score += vol_score * self.weights['volume_confirmation']
        total_weight += self.weights['volume_confirmation']

        # 7. Regime Match
        regime_score = self._score_regime_match(side, regime)
        if regime_score > 0.7:
            reason_codes.append(f"REGIME_{regime.regime.value.upper()}")
        components['regime_match'] = regime_score
        weighted_score += regime_score * self.weights['regime_match']
        total_weight += self.weights['regime_match']

        # Normalize
        final_score = weighted_score / total_weight if total_weight > 0 else 0.0

        return EntryScoreResult(
            side=side,
            score=final_score,
            components=components,
            reason_codes=reason_codes,
            meets_threshold=final_score >= 0.6
        )

    def _score_with_rules(
        self,
        features: FeatureVector,
        side: TradeSide,
        regime: RegimeState,
        strategy: "StrategyDefinition"
    ) -> EntryScoreResult:
        """Score using strategy-specific entry rules."""
        components = {}
        reason_codes = []
        total_weight = 0.0
        weighted_score = 0.0

        for rule in strategy.entry_rules:
            if not rule.enabled:
                continue

            score = self._evaluate_entry_rule(rule, features, side, regime)
            components[rule.name] = score

            if score > 0.5:
                reason_codes.append(rule.name.upper())

            weighted_score += score * rule.weight
            total_weight += rule.weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0.0

        return EntryScoreResult(
            side=side,
            score=final_score,
            components=components,
            reason_codes=reason_codes,
            meets_threshold=final_score >= strategy.min_entry_score
        )

    def _evaluate_entry_rule(
        self,
        rule: "EntryRule",
        features: FeatureVector,
        side: TradeSide,
        regime: RegimeState
    ) -> float:
        """Evaluate a single entry rule."""
        indicator = rule.indicator
        condition = rule.condition
        threshold = rule.threshold

        # Map indicator names to feature values
        value = self._get_indicator_value(features, indicator)

        if value is None:
            return 0.5  # Neutral if indicator unavailable

        # Evaluate condition
        if condition == "above":
            return 1.0 if value > threshold else 0.0
        elif condition == "below":
            return 1.0 if value < threshold else 0.0
        elif condition == "between":
            # threshold is upper bound, assume lower = 30 for RSI-like
            return 1.0 if 30 <= value <= threshold else 0.0
        elif condition == "extreme":
            # For RSI/Stoch - check if at extremes
            if side == TradeSide.LONG:
                return 1.0 if value <= threshold else 0.0
            else:
                return 1.0 if value >= (100 - threshold) else 0.0
        elif condition == "aligned":
            return self._score_trend_alignment(features, side)
        elif condition == "direction_match":
            return self._check_direction_match(features, side, indicator)
        elif condition == "growing":
            # Would need historical data - use proxy
            return 0.5
        elif condition == "crosses":
            # Would need previous bar - use current relationship
            return self._score_macd_momentum(features, side)

        return 0.5

    def _get_indicator_value(
        self,
        features: FeatureVector,
        indicator: str | None
    ) -> float | None:
        """Get indicator value from features."""
        if not indicator:
            return None

        mapping = {
            'adx': features.adx,
            'rsi_14': features.rsi_14,
            'rsi': features.rsi_14,
            'macd': features.macd,
            'macd_hist': features.macd_hist,
            'stoch_k': features.stoch_k,
            'stoch_d': features.stoch_d,
            'cci': features.cci,
            'mfi': features.mfi,
            'bb_pct': features.bb_pct,
            'bb_width': features.bb_width,
            'atr_14': features.atr_14,
            'volume_ratio': features.volume_ratio,
            'price_vs_sma20': features.price_vs_sma20,
        }
        return mapping.get(indicator)

    def _check_direction_match(
        self,
        features: FeatureVector,
        side: TradeSide,
        indicator: str | None
    ) -> float:
        """Check if indicator direction matches trade side."""
        if indicator == "macd_hist":
            if features.macd_hist is None:
                return 0.5
            if side == TradeSide.LONG:
                return 1.0 if features.macd_hist > 0 else 0.0
            else:
                return 1.0 if features.macd_hist < 0 else 0.0
        elif indicator == "rsi_momentum":
            if features.rsi_14 is None:
                return 0.5
            if side == TradeSide.LONG:
                return 1.0 if features.rsi_14 > 50 else 0.0
            else:
                return 1.0 if features.rsi_14 < 50 else 0.0
        return 0.5

    # ==================== Component Scorers ====================

    def _score_trend_alignment(
        self,
        features: FeatureVector,
        side: TradeSide
    ) -> float:
        """Score trend alignment (MA alignment)."""
        if not features.sma_20 or not features.sma_50:
            return 0.5

        if side == TradeSide.LONG:
            if features.close > features.sma_20 > features.sma_50:
                return 1.0
            elif features.close > features.sma_20:
                return 0.7
            elif features.close > features.sma_50:
                return 0.4
            return 0.0
        else:
            if features.close < features.sma_20 < features.sma_50:
                return 1.0
            elif features.close < features.sma_20:
                return 0.7
            elif features.close < features.sma_50:
                return 0.4
            return 0.0

    def _score_rsi_momentum(
        self,
        features: FeatureVector,
        side: TradeSide
    ) -> float:
        """Score RSI momentum."""
        if features.rsi_14 is None:
            return 0.5

        rsi = features.rsi_14

        if side == TradeSide.LONG:
            if rsi < 30:
                return 1.0  # Oversold - strong for long
            elif rsi < 40:
                return 0.8
            elif 40 <= rsi <= 60:
                return 0.6  # Neutral
            elif rsi < 70:
                return 0.4
            return 0.2  # Overbought - weak for long
        else:
            if rsi > 70:
                return 1.0  # Overbought - strong for short
            elif rsi > 60:
                return 0.8
            elif 40 <= rsi <= 60:
                return 0.6
            elif rsi > 30:
                return 0.4
            return 0.2  # Oversold - weak for short

    def _score_macd_momentum(
        self,
        features: FeatureVector,
        side: TradeSide
    ) -> float:
        """Score MACD momentum."""
        if features.macd is None or features.macd_signal is None:
            return 0.5

        if side == TradeSide.LONG:
            if features.macd > features.macd_signal:
                if features.macd_hist and features.macd_hist > 0:
                    return 1.0
                return 0.7
            return 0.3
        else:
            if features.macd < features.macd_signal:
                if features.macd_hist and features.macd_hist < 0:
                    return 1.0
                return 0.7
            return 0.3

    def _score_trend_strength(
        self,
        features: FeatureVector,
        regime: RegimeState
    ) -> float:
        """Score trend strength via ADX."""
        if features.adx is None:
            return 0.5

        if features.adx >= 40:
            return 1.0
        elif features.adx >= 30:
            return 0.8
        elif features.adx >= 25:
            return 0.6
        elif features.adx >= 20:
            return 0.4
        return 0.2

    def _score_mean_reversion(
        self,
        features: FeatureVector,
        side: TradeSide
    ) -> float:
        """Score mean reversion setup (BB position)."""
        if features.bb_pct is None:
            return 0.5

        if side == TradeSide.LONG:
            if features.bb_pct <= 0.1:
                return 1.0  # At/below lower BB
            elif features.bb_pct <= 0.2:
                return 0.8
            elif features.bb_pct <= 0.3:
                return 0.6
            return 0.3
        else:
            if features.bb_pct >= 0.9:
                return 1.0  # At/above upper BB
            elif features.bb_pct >= 0.8:
                return 0.8
            elif features.bb_pct >= 0.7:
                return 0.6
            return 0.3

    def _score_volume(self, features: FeatureVector) -> float:
        """Score volume confirmation."""
        if features.volume_ratio is None:
            return 0.5

        if features.volume_ratio >= 2.0:
            return 1.0
        elif features.volume_ratio >= 1.5:
            return 0.8
        elif features.volume_ratio >= 1.0:
            return 0.6
        elif features.volume_ratio >= 0.7:
            return 0.4
        return 0.2

    def _score_regime_match(
        self,
        side: TradeSide,
        regime: RegimeState
    ) -> float:
        """Score regime appropriateness."""
        if side == TradeSide.LONG:
            if regime.regime == RegimeType.TREND_UP:
                return 1.0
            elif regime.regime == RegimeType.RANGE:
                return 0.6
            elif regime.regime == RegimeType.TREND_DOWN:
                return 0.2
        else:
            if regime.regime == RegimeType.TREND_DOWN:
                return 1.0
            elif regime.regime == RegimeType.RANGE:
                return 0.6
            elif regime.regime == RegimeType.TREND_UP:
                return 0.2

        return 0.5

