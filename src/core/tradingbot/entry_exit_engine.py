"""Entry/Exit Engine for Tradingbot.

Handles signal generation, entry scoring, exit rule evaluation,
and trailing stop management with strategy-specific rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from .config import TrailingMode
from .models import (
    FeatureVector,
    PositionState,
    RegimeState,
    RegimeType,
    Signal,
    SignalType,
    TradeSide,
    TrailingState,
    VolatilityLevel,
)

if TYPE_CHECKING:
    from .strategy_catalog import EntryRule, ExitRule, StrategyDefinition

logger = logging.getLogger(__name__)


class ExitReason(str, Enum):
    """Exit signal reasons."""
    STOP_HIT = "stop_hit"
    TRAILING_STOP = "trailing_stop"
    TIME_STOP = "time_stop"
    MOMENTUM_REVERSAL = "momentum_reversal"
    TREND_BREAK = "trend_break"
    VOLATILITY_SPIKE = "volatility_spike"
    RSI_EXTREME = "rsi_extreme"
    MACD_CROSS = "macd_cross"
    BB_REVERSAL = "bb_reversal"
    REGIME_FLIP = "regime_flip"
    MANUAL = "manual"


@dataclass
class EntryScoreResult:
    """Result of entry score calculation."""
    side: TradeSide
    score: float
    components: dict[str, float] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=list)
    meets_threshold: bool = False


@dataclass
class ExitSignalResult:
    """Result of exit signal check."""
    should_exit: bool
    reason: ExitReason | None = None
    urgency: int = 1  # 1-3, higher = more urgent
    details: str = ""


@dataclass
class TrailingStopResult:
    """Result of trailing stop calculation."""
    new_stop: float | None = None
    reason: str = ""
    distance_pct: float = 0.0


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


class ExitSignalChecker:
    """Checks for exit signals based on multiple criteria."""

    def __init__(
        self,
        max_bars_held: int = 200,
        rsi_extreme_threshold: float = 85.0,
        enable_time_stop: bool = True
    ):
        """Initialize exit signal checker.

        Args:
            max_bars_held: Maximum bars before time stop
            rsi_extreme_threshold: RSI level for extreme exit
            enable_time_stop: Enable time-based exit
        """
        self.max_bars_held = max_bars_held
        self.rsi_extreme_threshold = rsi_extreme_threshold
        self.enable_time_stop = enable_time_stop

    def check_exit(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState,
        previous_regime: RegimeState | None = None,
        strategy: "StrategyDefinition | None" = None
    ) -> ExitSignalResult:
        """Check all exit conditions.

        Args:
            features: Current features
            position: Current position
            regime: Current regime
            previous_regime: Previous regime for flip detection
            strategy: Optional strategy with custom exit rules

        Returns:
            ExitSignalResult
        """
        # 1. Check stop hit (highest priority)
        if position.is_stopped_out():
            return ExitSignalResult(
                should_exit=True,
                reason=ExitReason.STOP_HIT,
                urgency=3,
                details=f"Stop hit at {position.trailing.current_stop_price:.4f}"
            )

        # 2. Momentum reversal (RSI extreme)
        rsi_exit = self._check_rsi_extreme(features, position)
        if rsi_exit.should_exit:
            return rsi_exit

        # 3. MACD cross against position
        macd_exit = self._check_macd_cross(features, position)
        if macd_exit.should_exit:
            return macd_exit

        # 4. Bollinger Band reversal
        bb_exit = self._check_bb_reversal(features, position)
        if bb_exit.should_exit:
            return bb_exit

        # 5. Trend break (MA cross)
        trend_exit = self._check_trend_break(features, position)
        if trend_exit.should_exit:
            return trend_exit

        # 6. Volatility spike
        vol_exit = self._check_volatility_spike(features, position, regime)
        if vol_exit.should_exit:
            return vol_exit

        # 7. Regime flip
        if previous_regime:
            regime_exit = self._check_regime_flip(position, regime, previous_regime)
            if regime_exit.should_exit:
                return regime_exit

        # 8. Time stop
        if self.enable_time_stop:
            time_exit = self._check_time_stop(position)
            if time_exit.should_exit:
                return time_exit

        return ExitSignalResult(should_exit=False)

    def _check_rsi_extreme(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> ExitSignalResult:
        """Check RSI extreme exit."""
        if features.rsi_14 is None:
            return ExitSignalResult(should_exit=False)

        if position.side == TradeSide.LONG:
            if features.rsi_14 >= self.rsi_extreme_threshold:
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.RSI_EXTREME,
                    urgency=2,
                    details=f"RSI extreme overbought: {features.rsi_14:.1f}"
                )
        else:
            if features.rsi_14 <= (100 - self.rsi_extreme_threshold):
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.RSI_EXTREME,
                    urgency=2,
                    details=f"RSI extreme oversold: {features.rsi_14:.1f}"
                )

        return ExitSignalResult(should_exit=False)

    def _check_macd_cross(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> ExitSignalResult:
        """Check MACD cross against position."""
        if features.macd is None or features.macd_signal is None:
            return ExitSignalResult(should_exit=False)

        if position.side == TradeSide.LONG:
            # Bearish cross for long position
            if (features.macd < features.macd_signal and
                features.macd_hist is not None and features.macd_hist < 0):
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.MACD_CROSS,
                    urgency=2,
                    details="MACD bearish cross"
                )
        else:
            # Bullish cross for short position
            if (features.macd > features.macd_signal and
                features.macd_hist is not None and features.macd_hist > 0):
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.MACD_CROSS,
                    urgency=2,
                    details="MACD bullish cross"
                )

        return ExitSignalResult(should_exit=False)

    def _check_bb_reversal(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> ExitSignalResult:
        """Check Bollinger Band reversal."""
        if features.bb_pct is None:
            return ExitSignalResult(should_exit=False)

        # Check if price has moved from one extreme to middle
        if position.side == TradeSide.LONG:
            # If entered near lower band and now at/above middle
            if features.bb_pct >= 0.5 and position.unrealized_pnl_pct > 1.0:
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.BB_REVERSAL,
                    urgency=1,
                    details=f"BB mean reversion complete: {features.bb_pct:.1%}"
                )
        else:
            # If entered near upper band and now at/below middle
            if features.bb_pct <= 0.5 and position.unrealized_pnl_pct > 1.0:
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.BB_REVERSAL,
                    urgency=1,
                    details=f"BB mean reversion complete: {features.bb_pct:.1%}"
                )

        return ExitSignalResult(should_exit=False)

    def _check_trend_break(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> ExitSignalResult:
        """Check trend break (MA cross)."""
        if not features.sma_20 or not features.sma_50:
            return ExitSignalResult(should_exit=False)

        if position.side == TradeSide.LONG:
            # Price closes below SMA20 while SMA20 < SMA50
            if features.close < features.sma_20 < features.sma_50:
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.TREND_BREAK,
                    urgency=2,
                    details="Trend break: price below declining MAs"
                )
        else:
            # Price closes above SMA20 while SMA20 > SMA50
            if features.close > features.sma_20 > features.sma_50:
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.TREND_BREAK,
                    urgency=2,
                    details="Trend break: price above rising MAs"
                )

        return ExitSignalResult(should_exit=False)

    def _check_volatility_spike(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState
    ) -> ExitSignalResult:
        """Check for volatility spike exit."""
        if regime.volatility == VolatilityLevel.EXTREME:
            # In extreme volatility, consider tighter exit
            if position.unrealized_pnl_pct < -1.0:
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.VOLATILITY_SPIKE,
                    urgency=3,
                    details="Extreme volatility with adverse move"
                )

        return ExitSignalResult(should_exit=False)

    def _check_regime_flip(
        self,
        position: PositionState,
        regime: RegimeState,
        previous_regime: RegimeState
    ) -> ExitSignalResult:
        """Check for significant regime change."""
        # Trend flip against position
        if position.side == TradeSide.LONG:
            if (previous_regime.regime in [RegimeType.TREND_UP, RegimeType.RANGE] and
                regime.regime == RegimeType.TREND_DOWN and
                regime.regime_confidence > 0.7):
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.REGIME_FLIP,
                    urgency=2,
                    details="Regime flipped to downtrend"
                )
        else:
            if (previous_regime.regime in [RegimeType.TREND_DOWN, RegimeType.RANGE] and
                regime.regime == RegimeType.TREND_UP and
                regime.regime_confidence > 0.7):
                return ExitSignalResult(
                    should_exit=True,
                    reason=ExitReason.REGIME_FLIP,
                    urgency=2,
                    details="Regime flipped to uptrend"
                )

        return ExitSignalResult(should_exit=False)

    def _check_time_stop(self, position: PositionState) -> ExitSignalResult:
        """Check time-based exit."""
        if position.bars_held >= self.max_bars_held:
            return ExitSignalResult(
                should_exit=True,
                reason=ExitReason.TIME_STOP,
                urgency=1,
                details=f"Max bars held: {position.bars_held}"
            )
        return ExitSignalResult(should_exit=False)


class TrailingStopManager:
    """Manages trailing stop updates for positions."""

    def __init__(
        self,
        min_step_pct: float = 0.1,
        update_cooldown_bars: int = 3,
        activation_pct: float = 0.0
    ):
        """Initialize trailing stop manager.

        Args:
            min_step_pct: Minimum step size as percentage
            update_cooldown_bars: Bars between updates
            activation_pct: Minimum profit % before trailing activates
        """
        self.min_step_pct = min_step_pct
        self.update_cooldown_bars = update_cooldown_bars
        self.activation_pct = activation_pct

    def calculate_trailing_stop(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState,
        current_bar: int
    ) -> TrailingStopResult:
        """Calculate new trailing stop price.

        Trailing stop is only activated when position is in profit.
        Until then, the initial stop loss remains active.

        Args:
            features: Current features
            position: Current position
            regime: Current regime
            current_bar: Current bar index

        Returns:
            TrailingStopResult with new stop price if applicable
        """
        # Only activate trailing when position reaches activation threshold
        # Until then, the initial stop loss protects against losses
        entry_price = position.entry_price
        current_price = features.close

        if position.side == TradeSide.LONG:
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100

        if profit_pct < self.activation_pct:
            # Position not yet at activation threshold - keep initial stop loss
            return TrailingStopResult()

        # Check cooldown
        bars_since_update = current_bar - position.trailing.last_update_bar
        if bars_since_update < self.update_cooldown_bars:
            return TrailingStopResult()

        mode = position.trailing.mode

        if mode == TrailingMode.PCT:
            return self._trailing_pct(features, position, regime)
        elif mode == TrailingMode.ATR:
            return self._trailing_atr(features, position, regime)
        elif mode == TrailingMode.SWING:
            return self._trailing_swing(features, position)

        return TrailingStopResult()

    def _trailing_pct(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState
    ) -> TrailingStopResult:
        """Percentage-based trailing stop."""
        # Base distance
        distance_pct = 2.0  # 2% default

        # Adjust by volatility
        if regime.volatility == VolatilityLevel.HIGH:
            distance_pct *= 1.3
        elif regime.volatility == VolatilityLevel.EXTREME:
            distance_pct *= 1.5
        elif regime.volatility == VolatilityLevel.LOW:
            distance_pct *= 0.8

        if position.side == TradeSide.LONG:
            new_stop = position.trailing.highest_price * (1 - distance_pct / 100)
            if new_stop > position.trailing.current_stop_price:
                step_pct = ((new_stop - position.trailing.current_stop_price) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="PCT trailing update",
                        distance_pct=distance_pct
                    )
        else:
            new_stop = position.trailing.lowest_price * (1 + distance_pct / 100)
            if new_stop < position.trailing.current_stop_price:
                step_pct = ((position.trailing.current_stop_price - new_stop) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="PCT trailing update",
                        distance_pct=distance_pct
                    )

        return TrailingStopResult()

    def _trailing_atr(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState
    ) -> TrailingStopResult:
        """ATR-based trailing stop."""
        if features.atr_14 is None:
            return TrailingStopResult()

        # Base ATR multiple
        atr_multiple = 2.0

        # Adjust by regime
        if regime.is_trending:
            atr_multiple *= 1.2  # Wider in trends
        if regime.volatility == VolatilityLevel.HIGH:
            atr_multiple *= 1.3
        elif regime.volatility == VolatilityLevel.EXTREME:
            atr_multiple *= 1.5
        elif regime.volatility == VolatilityLevel.LOW:
            atr_multiple *= 0.8

        distance = features.atr_14 * atr_multiple

        if position.side == TradeSide.LONG:
            new_stop = position.trailing.highest_price - distance
            if new_stop > position.trailing.current_stop_price:
                step_pct = ((new_stop - position.trailing.current_stop_price) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason=f"ATR trailing ({atr_multiple:.1f}x ATR)",
                        distance_pct=(distance / features.close) * 100
                    )
        else:
            new_stop = position.trailing.lowest_price + distance
            if new_stop < position.trailing.current_stop_price:
                step_pct = ((position.trailing.current_stop_price - new_stop) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason=f"ATR trailing ({atr_multiple:.1f}x ATR)",
                        distance_pct=(distance / features.close) * 100
                    )

        return TrailingStopResult()

    def _trailing_swing(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> TrailingStopResult:
        """Swing/structure-based trailing stop using BB."""
        if features.bb_lower is None or features.bb_upper is None:
            return TrailingStopResult()

        buffer = features.atr_14 * 0.3 if features.atr_14 else features.close * 0.003

        if position.side == TradeSide.LONG:
            # Use BB lower as support
            new_stop = features.bb_lower - buffer
            if new_stop > position.trailing.current_stop_price:
                step_pct = ((new_stop - position.trailing.current_stop_price) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="Swing trailing (BB support)",
                        distance_pct=((features.close - new_stop) / features.close) * 100
                    )
        else:
            # Use BB upper as resistance
            new_stop = features.bb_upper + buffer
            if new_stop < position.trailing.current_stop_price:
                step_pct = ((position.trailing.current_stop_price - new_stop) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= self.min_step_pct:
                    return TrailingStopResult(
                        new_stop=new_stop,
                        reason="Swing trailing (BB resistance)",
                        distance_pct=((new_stop - features.close) / features.close) * 100
                    )

        return TrailingStopResult()


class EntryExitEngine:
    """Unified engine for entry/exit decisions.

    Combines entry scoring, exit signal checking, and trailing stop
    management into a single interface.
    """

    def __init__(
        self,
        entry_scorer: EntryScorer | None = None,
        exit_checker: ExitSignalChecker | None = None,
        trailing_manager: TrailingStopManager | None = None
    ):
        """Initialize entry/exit engine.

        Args:
            entry_scorer: Entry score calculator
            exit_checker: Exit signal checker
            trailing_manager: Trailing stop manager
        """
        self.entry_scorer = entry_scorer or EntryScorer()
        self.exit_checker = exit_checker or ExitSignalChecker()
        self.trailing_manager = trailing_manager or TrailingStopManager()

        logger.info("EntryExitEngine initialized")

    def evaluate_entry(
        self,
        features: FeatureVector,
        regime: RegimeState,
        strategy: "StrategyDefinition | None" = None
    ) -> tuple[EntryScoreResult, EntryScoreResult]:
        """Evaluate entry scores for both sides.

        Args:
            features: Current features
            regime: Current regime
            strategy: Optional strategy

        Returns:
            (long_score, short_score)
        """
        long_score = self.entry_scorer.calculate_score(
            features, TradeSide.LONG, regime, strategy
        )
        short_score = self.entry_scorer.calculate_score(
            features, TradeSide.SHORT, regime, strategy
        )
        return long_score, short_score

    def check_exit(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState,
        previous_regime: RegimeState | None = None,
        strategy: "StrategyDefinition | None" = None
    ) -> ExitSignalResult:
        """Check for exit signals.

        Args:
            features: Current features
            position: Current position
            regime: Current regime
            previous_regime: Previous regime
            strategy: Optional strategy

        Returns:
            ExitSignalResult
        """
        return self.exit_checker.check_exit(
            features, position, regime, previous_regime, strategy
        )

    def update_trailing_stop(
        self,
        features: FeatureVector,
        position: PositionState,
        regime: RegimeState,
        current_bar: int
    ) -> TrailingStopResult:
        """Update trailing stop.

        Args:
            features: Current features
            position: Current position
            regime: Current regime
            current_bar: Current bar index

        Returns:
            TrailingStopResult
        """
        return self.trailing_manager.calculate_trailing_stop(
            features, position, regime, current_bar
        )
