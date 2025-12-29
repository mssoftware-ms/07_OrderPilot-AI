"""Exit Signal Checker for Tradingbot.

Checks for exit signals based on multiple criteria including
RSI extremes, MACD crosses, BB reversals, trend breaks, and more.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from .models import (
    FeatureVector,
    PositionState,
    RegimeState,
    RegimeType,
    TradeSide,
)

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
class ExitSignalResult:
    """Result of exit signal check."""
    should_exit: bool
    reason: ExitReason | None = None
    urgency: int = 1  # 1-3, higher = more urgent
    details: str = ""

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

