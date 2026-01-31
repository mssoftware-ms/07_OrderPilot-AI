"""Signal Logic Mixin for BotController.

Provides entry scoring and signal creation methods:
- Rule-based entry score calculation
- Signal creation with stop-loss
- Signal reason generation
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from decimal import Decimal

from .models import FeatureVector, Signal, TradeSide
from src.core.market_data.types import HistoricalBar
from src.core.pattern_db import get_pattern_service

if TYPE_CHECKING:
    pass


class BotSignalLogicMixin:
    """Mixin providing signal scoring and creation methods.

    Expected attributes from BotController:
        config: FullBotConfig
        symbol: str
        _regime: RegimeState
        _active_strategy: StrategyProfile | None
    """

    # ==================== Signal & Scoring ====================

    def _calculate_entry_score(
        self,
        features: FeatureVector,
        side: TradeSide
    ) -> float:
        """Calculate entry score for given side.

        Rule-based scoring using indicators.

        Args:
            features: Current features
            side: Trade side

        Returns:
            Score between 0 and 1
        """
        score = 0.0
        weight_sum = 0.0

        for part_score, weight in (
            self._score_trend(features, side),
            self._score_rsi(features, side),
            self._score_macd(features, side),
            self._score_adx(features),
            self._score_bbands(features, side),
        ):
            if weight > 0:
                score += part_score
                weight_sum += weight

        return score / weight_sum if weight_sum > 0 else 0.0

    def _score_trend(self, features: FeatureVector, side: TradeSide) -> tuple[float, float]:
        if not (features.sma_20 and features.sma_50):
            return 0.0, 0.0
        trend_weight = 0.3
        if side == TradeSide.LONG:
            if features.close > features.sma_20 > features.sma_50:
                return trend_weight, trend_weight
            if features.close > features.sma_20:
                return trend_weight * 0.5, trend_weight
        else:
            if features.close < features.sma_20 < features.sma_50:
                return trend_weight, trend_weight
            if features.close < features.sma_20:
                return trend_weight * 0.5, trend_weight
        return 0.0, trend_weight

    def _score_rsi(self, features: FeatureVector, side: TradeSide) -> tuple[float, float]:
        if features.rsi_14 is None:
            return 0.0, 0.0
        mom_weight = 0.2
        if side == TradeSide.LONG:
            if 40 <= features.rsi_14 <= 60:
                return mom_weight * 0.8, mom_weight
            if features.rsi_14 < 40:
                return mom_weight, mom_weight
        else:
            if 40 <= features.rsi_14 <= 60:
                return mom_weight * 0.8, mom_weight
            if features.rsi_14 > 60:
                return mom_weight, mom_weight
        return 0.0, mom_weight

    def _score_macd(self, features: FeatureVector, side: TradeSide) -> tuple[float, float]:
        if features.macd is None or features.macd_signal is None:
            return 0.0, 0.0
        macd_weight = 0.2
        if side == TradeSide.LONG:
            if features.macd > features.macd_signal:
                return macd_weight, macd_weight
            if features.macd > 0:
                return macd_weight * 0.5, macd_weight
        else:
            if features.macd < features.macd_signal:
                return macd_weight, macd_weight
            if features.macd < 0:
                return macd_weight * 0.5, macd_weight
        return 0.0, macd_weight

    def _score_adx(self, features: FeatureVector) -> tuple[float, float]:
        if features.adx is None:
            return 0.0, 0.0
        adx_weight = 0.15
        if features.adx > 25:
            return adx_weight, adx_weight
        if features.adx > 20:
            return adx_weight * 0.5, adx_weight
        return 0.0, adx_weight

    def _score_bbands(self, features: FeatureVector, side: TradeSide) -> tuple[float, float]:
        if features.bb_pct is None:
            return 0.0, 0.0
        bb_weight = 0.15
        if side == TradeSide.LONG:
            if features.bb_pct < 0.2:
                return bb_weight, bb_weight
            if features.bb_pct < 0.4:
                return bb_weight * 0.5, bb_weight
        else:
            if features.bb_pct > 0.8:
                return bb_weight, bb_weight
            if features.bb_pct > 0.6:
                return bb_weight * 0.5, bb_weight
        return 0.0, bb_weight

    def _get_entry_threshold(self) -> float:
        """Get entry threshold based on active strategy and regime."""
        # User-configured override (UI: min score)
        if self.config and self.config.bot.entry_score_threshold is not None:
            return self.config.bot.entry_score_threshold

        if self._active_strategy:
            return self._active_strategy.entry_threshold

        # Default thresholds by regime
        if self._regime.is_trending:
            return 0.55
        else:
            return 0.65

    def _create_signal(
        self,
        features: FeatureVector,
        side: TradeSide,
        score: float
    ) -> Signal:
        """Create a trading signal.

        Args:
            features: Current features
            side: Trade side
            score: Entry score

        Returns:
            Signal instance
        """
        # Calculate stop-loss price
        sl_pct = self.config.risk.initial_stop_loss_pct
        if side == TradeSide.LONG:
            stop_price = features.close * (1 - sl_pct / 100)
        else:
            stop_price = features.close * (1 + sl_pct / 100)

        # Determine strategy_name with fallback chain:
        # 1. Active strategy name (Standard mode)
        # 2. JSON regime name (JSON Entry mode)
        # 3. Regime type value (last resort)
        strategy_name = None
        if self._active_strategy:
            strategy_name = self._active_strategy.name
        elif hasattr(self._regime, 'regime_name') and self._regime.regime_name:
            strategy_name = self._regime.regime_name
        elif hasattr(self._regime, 'regime'):
            strategy_name = f"Regime_{self._regime.regime.value}"

        return Signal(
            timestamp=features.timestamp,
            symbol=self.symbol,
            side=side,
            score=score,
            entry_price=features.close,
            stop_loss_price=stop_price,
            stop_loss_pct=sl_pct,
            regime=self._regime.regime,
            strategy_name=strategy_name,
            reason_codes=self._get_signal_reasons(features, side)
        )

    def _get_signal_reasons(
        self,
        features: FeatureVector,
        side: TradeSide
    ) -> list[str]:
        """Get reason codes for signal.

        Args:
            features: Current features
            side: Trade side

        Returns:
            List of reason codes
        """
        reasons = []

        # Trend reasons
        if features.sma_20 and features.sma_50:
            if side == TradeSide.LONG and features.close > features.sma_20:
                reasons.append("PRICE_ABOVE_SMA")
            elif side == TradeSide.SHORT and features.close < features.sma_20:
                reasons.append("PRICE_BELOW_SMA")

        # RSI reasons
        if features.rsi_14 is not None:
            if features.rsi_14 < 30:
                reasons.append("RSI_OVERSOLD")
            elif features.rsi_14 > 70:
                reasons.append("RSI_OVERBOUGHT")

        # Regime reason
        reasons.append(f"REGIME_{self._regime.regime.value.upper()}")

        return reasons

    # ==================== Pattern Validation =============
