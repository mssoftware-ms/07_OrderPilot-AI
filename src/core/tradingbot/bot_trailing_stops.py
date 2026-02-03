"""Trailing Stop Calculation Mixin for BotController.

Provides trailing stop calculation methods:
- Percentage-based trailing
- ATR-based trailing (with regime-adaptive option)
- Swing/structure-based trailing (Bollinger Bands)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import TrailingMode
from .models import FeatureVector, PositionState, TradeSide

if TYPE_CHECKING:
    pass


class BotTrailingStopsMixin:
    """Mixin providing trailing stop calculation methods.

    Expected attributes from BotController:
        config: FullBotConfig
        _log_activity: Callable[[str, str], None]
    """

    # ==================== Trailing Stop ====================

    def _calculate_trailing_stop(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> float | None:
        """Calculate new trailing stop price.

        Trailing stop is only activated when position is in profit.
        Until then, the initial stop loss remains active.

        Args:
            features: Current features
            position: Current position

        Returns:
            New stop price or None if no update needed
        """
        # Only activate trailing when position reaches activation threshold
        # Activation is based on RETURN ON RISK (not price change)
        # e.g., 10% activation = 10 profit on 100 risk
        entry_price = position.entry_price
        current_price = features.close
        initial_stop = position.trailing.initial_stop_price
        activation_pct = self.config.risk.trailing_activation_pct

        # Calculate return on risk (not price change)
        if position.side == TradeSide.LONG:
            risk_per_unit = entry_price - initial_stop
            pnl_per_unit = current_price - entry_price
        else:  # SHORT
            risk_per_unit = initial_stop - entry_price
            pnl_per_unit = entry_price - current_price

        # Return on risk percentage
        if risk_per_unit > 0:
            profit_pct = (pnl_per_unit / risk_per_unit) * 100
        else:
            profit_pct = 0

        self._log_activity(
            "DEBUG",
            f"Trailing Check: RoR={profit_pct:.2f}%, activation={activation_pct:.2f}%, "
            f"risk/unit={risk_per_unit:.4f}, pnl/unit={pnl_per_unit:.4f}, side={position.side.value}"
        )

        if profit_pct < activation_pct:
            # Position not yet at activation threshold - keep initial stop loss
            self._log_activity("DEBUG", f"Trailing nicht aktiviert: RoR {profit_pct:.2f}% < {activation_pct:.2f}%")
            return None

        self._log_activity("DEBUG", f"Trailing AKTIVIERT: RoR {profit_pct:.2f}% >= {activation_pct:.2f}%")

        mode = self.config.bot.trailing_mode

        if mode == TrailingMode.PCT:
            return self._trailing_pct(features, position)
        elif mode == TrailingMode.ATR:
            return self._trailing_atr(features, position)
        elif mode == TrailingMode.SWING:
            return self._trailing_swing(features, position)

        return None

    def _trailing_pct(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> float | None:
        """Percentage-based trailing stop.

        Distance is calculated from CURRENT price, not highest/lowest.
        The stop only moves in favorable direction (up for long, down for short).

        Args:
            features: Current features
            position: Current position

        Returns:
            New stop price or None
        """
        distance_pct = self.config.risk.trailing_pct_distance
        min_step = self.config.risk.trailing_min_step_pct
        current_price = features.close
        current_stop = position.trailing.current_stop_price

        if position.side == TradeSide.LONG:
            # Stop at X% below current price, only moves up
            new_stop = current_price * (1 - distance_pct / 100)

            self._log_activity(
                "DEBUG",
                f"LONG PCT: current_price={current_price:.4f}, "
                f"distance={distance_pct}%, new_stop={new_stop:.4f}, current_stop={current_stop:.4f}"
            )

            # Only update if new stop is higher (stop can only go up for long)
            if new_stop > current_stop:
                step_pct = ((new_stop - current_stop) / current_stop) * 100
                self._log_activity("DEBUG", f"LONG step_pct={step_pct:.2f}%, min_step={min_step}%")
                if step_pct >= min_step:
                    return new_stop

        else:  # SHORT
            # Stop at X% above current price, only moves down
            new_stop = current_price * (1 + distance_pct / 100)

            self._log_activity(
                "DEBUG",
                f"SHORT PCT: current_price={current_price:.4f}, "
                f"distance={distance_pct}%, new_stop={new_stop:.4f}, current_stop={current_stop:.4f}"
            )

            # Only update if new stop is lower (stop can only go down for short)
            if new_stop < current_stop:
                step_pct = ((current_stop - new_stop) / current_stop) * 100
                self._log_activity("DEBUG", f"SHORT step_pct={step_pct:.2f}%, min_step={min_step}%")
                if step_pct >= min_step:
                    return new_stop

        return None

    def _trailing_atr(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> float | None:
        """ATR-based trailing stop with regime-adaptive multiplier.

        Args:
            features: Current features
            position: Current position

        Returns:
            New stop price or None
        """
        if features.atr_14 is None:
            return None

        min_step = self.config.risk.trailing_min_step_pct

        # Determine ATR multiplier based on settings
        if self.config.risk.regime_adaptive_trailing:
            # Regime-adaptive mode: use ADX to determine multiplier
            adx = features.adx_14 if features.adx_14 is not None else 25.0

            if adx > 25:
                # Trending market - use tighter stop
                atr_multiple = self.config.risk.trailing_atr_trending
                regime_type = "TRENDING"
            elif adx < 20:
                # Ranging/choppy market - use wider stop
                atr_multiple = self.config.risk.trailing_atr_ranging
                regime_type = "RANGING"
            else:
                # Neutral - interpolate between trending and ranging
                t = (adx - 20) / 5.0  # 0 to 1
                atr_multiple = (
                    self.config.risk.trailing_atr_ranging * (1 - t) +
                    self.config.risk.trailing_atr_trending * t
                )
                regime_type = "NEUTRAL"

            # Add volatility bonus if ATR is high (> 2% of price)
            atr_pct = (features.atr_14 / features.close) * 100
            if atr_pct > 2.0:
                vol_bonus = self.config.risk.trailing_volatility_bonus
                atr_multiple += vol_bonus
                self._log_activity(
                    "TRAILING",
                    f"High Vol ({atr_pct:.1f}%): +{vol_bonus}x Bonus | "
                    f"Regime={regime_type} | Final ATR x{atr_multiple:.1f}"
                )
        else:
            # Fixed mode: use single multiplier
            atr_multiple = self.config.risk.trailing_atr_multiple

        distance = features.atr_14 * atr_multiple

        if position.side == TradeSide.LONG:
            new_stop = position.trailing.highest_price - distance
            current_stop = position.trailing.current_stop_price

            step_pct = ((new_stop - current_stop) / current_stop) * 100
            if step_pct >= min_step:
                return new_stop

        else:  # SHORT
            new_stop = position.trailing.lowest_price + distance
            current_stop = position.trailing.current_stop_price

            self._log_activity(
                "DEBUG",
                f"SHORT ATR: lowest={position.trailing.lowest_price:.4f}, "
                f"distance={distance:.4f}, new_stop={new_stop:.4f}, current_stop={current_stop:.4f}"
            )

            step_pct = ((current_stop - new_stop) / current_stop) * 100
            self._log_activity("DEBUG", f"SHORT ATR step_pct={step_pct:.2f}%, min_step={min_step}%")
            if step_pct >= min_step:
                return new_stop

        return None

    def _trailing_swing(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> float | None:
        """Swing/structure-based trailing stop.

        Simplified: uses Bollinger bands as structure levels.

        Args:
            features: Current features
            position: Current position

        Returns:
            New stop price or None
        """
        if features.bb_lower is None or features.bb_upper is None:
            return None

        min_step = self.config.risk.trailing_min_step_pct

        if position.side == TradeSide.LONG:
            # Use BB lower as structure support
            buffer = features.atr_14 * 0.5 if features.atr_14 else features.close * 0.005
            new_stop = features.bb_lower - buffer

            if new_stop > position.trailing.current_stop_price:
                step_pct = ((new_stop - position.trailing.current_stop_price) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= min_step:
                    return new_stop

        else:  # SHORT
            # Use BB upper as structure resistance
            buffer = features.atr_14 * 0.5 if features.atr_14 else features.close * 0.005
            new_stop = features.bb_upper + buffer

            if new_stop < position.trailing.current_stop_price:
                step_pct = ((position.trailing.current_stop_price - new_stop) /
                           position.trailing.current_stop_price) * 100
                if step_pct >= min_step:
                    return new_stop

        return None

    # ==================== Live Trading Integration ====================

    async def _update_trailing_stop_live(self, features: FeatureVector) -> None:
        """Update trailing stop for live trading.

        Called on every bar to check if trailing stop needs updating.
        Throttles updates to max 1 per minute.

        Args:
            features: Current features
        """
        if not self._position:
            return

        # Calculate new trailing stop price
        new_stop_price = self._calculate_trailing_stop(features, self._position)

        if new_stop_price is None:
            return

        # Throttling: Max 1 update per minute
        import time
        last_update = self._last_trailing_update.get(self.symbol, 0)
        current_time = time.time()

        if (current_time - last_update) < 60:
            # Skip update if less than 1 minute since last update
            return

        # Check if live trading adapter with modify capability
        broker_adapter = getattr(self, '_broker_adapter', None)
        if broker_adapter and hasattr(broker_adapter, 'modify_position_tp_sl_order'):
            # Live trading: Send to broker
            from decimal import Decimal

            success = await broker_adapter.modify_position_tp_sl_order(
                symbol=self.symbol,
                sl_price=Decimal(str(new_stop_price))
            )

            if success:
                self._position.trailing.current_stop_price = new_stop_price
                self._last_trailing_update[self.symbol] = current_time
                self._log_activity("TRAILING", f"Stop updated to {new_stop_price:.4f} (LIVE)")
            else:
                self._log_activity("ERROR", "Failed to update trailing stop at broker")
        else:
            # Paper trading: Update locally
            self._position.trailing.current_stop_price = new_stop_price
            self._last_trailing_update[self.symbol] = current_time
            self._log_activity("TRAILING", f"Stop updated to {new_stop_price:.4f} (PAPER)")
