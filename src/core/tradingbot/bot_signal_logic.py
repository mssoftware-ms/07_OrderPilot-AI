"""Signal Logic Mixin for BotController.

Provides entry scoring and signal creation methods:
- Rule-based entry score calculation
- Signal creation with stop-loss
- Signal reason generation
"""

from __future__ import annotations

<<<<<<< HEAD
from typing import TYPE_CHECKING
from decimal import Decimal

from .models import FeatureVector, Signal, TradeSide
from src.core.market_data.types import HistoricalBar
from src.core.pattern_db import get_pattern_service

if TYPE_CHECKING:
    pass
=======
from typing import TYPE_CHECKING
from decimal import Decimal

from .models import FeatureVector, Signal, TradeSide
from src.core.market_data.types import HistoricalBar
from src.core.pattern_db import get_pattern_service

if TYPE_CHECKING:
    pass
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268


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

        # Trend indicators (weight: 0.3)
        if features.sma_20 and features.sma_50:
            trend_weight = 0.3
            if side == TradeSide.LONG:
                if features.close > features.sma_20 > features.sma_50:
                    score += trend_weight
                elif features.close > features.sma_20:
                    score += trend_weight * 0.5
            else:  # SHORT
                if features.close < features.sma_20 < features.sma_50:
                    score += trend_weight
                elif features.close < features.sma_20:
                    score += trend_weight * 0.5
            weight_sum += trend_weight

        # Momentum (RSI) (weight: 0.2)
        if features.rsi_14 is not None:
            mom_weight = 0.2
            if side == TradeSide.LONG:
                if 40 <= features.rsi_14 <= 60:
                    score += mom_weight * 0.8  # Neutral zone
                elif features.rsi_14 < 40:
                    score += mom_weight  # Oversold
            else:  # SHORT
                if 40 <= features.rsi_14 <= 60:
                    score += mom_weight * 0.8
                elif features.rsi_14 > 60:
                    score += mom_weight  # Overbought
            weight_sum += mom_weight

        # MACD (weight: 0.2)
        if features.macd is not None and features.macd_signal is not None:
            macd_weight = 0.2
            if side == TradeSide.LONG:
                if features.macd > features.macd_signal:
                    score += macd_weight
                elif features.macd > 0:
                    score += macd_weight * 0.5
            else:  # SHORT
                if features.macd < features.macd_signal:
                    score += macd_weight
                elif features.macd < 0:
                    score += macd_weight * 0.5
            weight_sum += macd_weight

        # ADX trend strength (weight: 0.15)
        if features.adx is not None:
            adx_weight = 0.15
            if features.adx > 25:  # Strong trend
                score += adx_weight
            elif features.adx > 20:
                score += adx_weight * 0.5
            weight_sum += adx_weight

        # Bollinger Bands (weight: 0.15)
        if features.bb_pct is not None:
            bb_weight = 0.15
            if side == TradeSide.LONG:
                if features.bb_pct < 0.2:  # Near lower band
                    score += bb_weight
                elif features.bb_pct < 0.4:
                    score += bb_weight * 0.5
            else:  # SHORT
                if features.bb_pct > 0.8:  # Near upper band
                    score += bb_weight
                elif features.bb_pct > 0.6:
                    score += bb_weight * 0.5
            weight_sum += bb_weight

        # Normalize score
        return score / weight_sum if weight_sum > 0 else 0.0

<<<<<<< HEAD
    def _get_entry_threshold(self) -> float:
        """Get entry threshold based on active strategy and regime."""
        # User-configured override (UI: min score)
        if self.config and self.config.bot.entry_score_threshold is not None:
            return self.config.bot.entry_score_threshold

        if self._active_strategy:
            return self._active_strategy.entry_threshold

        # Default thresholds by regime
        if self._regime.is_trending:
=======
    def _get_entry_threshold(self) -> float:
        """Get entry threshold based on active strategy and regime."""
        # User-configured override (UI: min score)
        if self.config and self.config.bot.entry_score_threshold is not None:
            return self.config.bot.entry_score_threshold

        if self._active_strategy:
            return self._active_strategy.entry_threshold

        # Default thresholds by regime
        if self._regime.is_trending:
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268
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

        return Signal(
            timestamp=features.timestamp,
            symbol=self.symbol,
            side=side,
            score=score,
            entry_price=features.close,
            stop_loss_price=stop_price,
            stop_loss_pct=sl_pct,
            regime=self._regime.regime,
            strategy_name=self._active_strategy.name if self._active_strategy else None,
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
<<<<<<< HEAD
        reasons = []
=======
        reasons = []
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268

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

<<<<<<< HEAD
        return reasons

    # ==================== Pattern Validation ====================

    async def _pattern_gate(self, features: FeatureVector, side: TradeSide) -> tuple[bool, str | None]:
        """Validate current context against pattern DB before creating a signal.

        Returns:
            (ok, reason) where ok=False blocks entry.
        """
        try:
            window = max(25,  self._feature_engine.MIN_BARS if hasattr(self, "_feature_engine") else 25)
            if len(self._bar_buffer) < window:
                return False, "PATTERN_TOO_FEW_BARS"

            bars = self._bar_buffer[-window:]
            hist_bars: list[HistoricalBar] = []
            for b in bars:
                hist_bars.append(
                    HistoricalBar(
                        timestamp=b.get("timestamp"),
                        open=Decimal(str(b.get("open", 0))),
                        high=Decimal(str(b.get("high", 0))),
                        low=Decimal(str(b.get("low", 0))),
                        close=Decimal(str(b.get("close", 0))),
                        volume=int(b.get("volume", 0)),
                    )
                )

            service = await get_pattern_service()
            analysis = await service.analyze_signal(
                bars=hist_bars,
                symbol=self.symbol,
                timeframe=self.timeframe,
                signal_direction=side.value,
                cross_symbol_search=True,
            )

            if not analysis:
                return False, "PATTERN_NO_MATCHES"

            # Checks
            if analysis.similar_patterns_count < self.config.bot.pattern_min_matches:
                return False, "PATTERN_TOO_FEW_MATCHES"

            if analysis.win_rate < self.config.bot.pattern_min_win_rate:
                return False, "PATTERN_LOW_WINRATE"

            if analysis.avg_similarity_score < self.config.bot.pattern_similarity_threshold:
                return False, "PATTERN_LOW_SIMILARITY"

            # Optional: boost score or log
            self._log_activity(
                "PATTERN_OK",
                f"Matches={analysis.similar_patterns_count}, win_rate={analysis.win_rate:.2f}, sim={analysis.avg_similarity_score:.2f}"
            )
            return True, None

        except Exception as e:
            self._log_activity("PATTERN_ERR", f"{e}")
            return False, "PATTERN_ERROR"
=======
        return reasons

    # ==================== Pattern Validation ====================

    async def _pattern_gate(self, features: FeatureVector, side: TradeSide) -> tuple[bool, str | None]:
        """Validate current context against pattern DB before creating a signal.

        Returns:
            (ok, reason) where ok=False blocks entry.
        """
        try:
            window = max(25,  self._feature_engine.MIN_BARS if hasattr(self, "_feature_engine") else 25)
            if len(self._bar_buffer) < window:
                return False, "PATTERN_TOO_FEW_BARS"

            bars = self._bar_buffer[-window:]
            hist_bars: list[HistoricalBar] = []
            for b in bars:
                hist_bars.append(
                    HistoricalBar(
                        timestamp=b.get("timestamp"),
                        open=Decimal(str(b.get("open", 0))),
                        high=Decimal(str(b.get("high", 0))),
                        low=Decimal(str(b.get("low", 0))),
                        close=Decimal(str(b.get("close", 0))),
                        volume=int(b.get("volume", 0)),
                    )
                )

            service = await get_pattern_service()
            analysis = await service.analyze_signal(
                bars=hist_bars,
                symbol=self.symbol,
                timeframe=self.timeframe,
                signal_direction=side.value,
                cross_symbol_search=True,
            )

            if not analysis:
                return False, "PATTERN_NO_MATCHES"

            # Checks
            if analysis.similar_patterns_count < self.config.bot.pattern_min_matches:
                return False, "PATTERN_TOO_FEW_MATCHES"

            if analysis.win_rate < self.config.bot.pattern_min_win_rate:
                return False, "PATTERN_LOW_WINRATE"

            if analysis.avg_similarity_score < self.config.bot.pattern_similarity_threshold:
                return False, "PATTERN_LOW_SIMILARITY"

            # Optional: boost score or log
            self._log_activity(
                "PATTERN_OK",
                f"Matches={analysis.similar_patterns_count}, win_rate={analysis.win_rate:.2f}, sim={analysis.avg_similarity_score:.2f}"
            )
            return True, None

        except Exception as e:
            self._log_activity("PATTERN_ERR", f"{e}")
            return False, "PATTERN_ERROR"
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268
