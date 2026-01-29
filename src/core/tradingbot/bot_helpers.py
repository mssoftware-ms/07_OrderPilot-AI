"""Helper Methods Mixin for BotController.

Provides utility methods:
- Feature calculation (_calculate_features)
- Regime update (_update_regime)
- Order intent creation (_create_entry_order)
- Decision creation (_create_decision)
- State transition handling (_on_state_transition)
- Fill simulation (simulate_fill)
- Serialization (to_dict)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd

from .models import (
    BotAction,
    BotDecision,
    FeatureVector,
    OrderIntent,
    PositionState,
    RegimeState,
    RegimeType,
    Signal,
    TradeSide,
    TrailingState,
    VolatilityLevel,
)

if TYPE_CHECKING:
    from .state_machine import StateTransition

logger = logging.getLogger(__name__)


class BotHelpersMixin:
    """Mixin providing helper methods for feature/regime/order operations.

    Expected attributes from BotController:
        config: FullBotConfig
        symbol: str
        timeframe: str
        _regime: RegimeState
        _active_strategy: StrategyProfile | None
        _event_bus: EventBus | None
        _feature_engine: FeatureEngine
        _bar_buffer: list[dict]
        _max_buffer_size: int
        _current_signal: Signal | None
        _position: PositionState | None
        _state_machine: BotStateMachine
        _run_id: str
        _running: bool
        _trades_today: int
        _daily_pnl: float
        _consecutive_losses: int
        _bar_count: int
        _log_activity: Callable[[str, str], None]
    """

    # ==================== Helper Methods ====================

    async def _calculate_features(self, bar: dict[str, Any]) -> FeatureVector:
        """Calculate feature vector from bar data using FeatureEngine.

        Maintains a rolling buffer of bars and uses FeatureEngine to
        calculate all technical indicators.

        Args:
            bar: Bar data with OHLCV

        Returns:
            FeatureVector with calculated indicators
        """
        # Add bar to buffer
        self._bar_buffer.append({
            'timestamp': bar.get('timestamp', datetime.utcnow()),
            'open': bar.get('open', 0),
            'high': bar.get('high', 0),
            'low': bar.get('low', 0),
            'close': bar.get('close', 0),
            'volume': bar.get('volume', 0),
        })

        # Trim buffer if too large
        if len(self._bar_buffer) > self._max_buffer_size:
            self._bar_buffer = self._bar_buffer[-self._max_buffer_size:]

        # Need minimum bars for indicator calculation
        min_bars = self._feature_engine.MIN_BARS
        if len(self._bar_buffer) < min_bars:
            # Return basic features without indicators
            self._log_activity(
                "WARMUP",
                f"Sammle Daten: {len(self._bar_buffer)}/{min_bars} Bars"
            )
            return FeatureVector(
                timestamp=bar.get("timestamp", datetime.utcnow()),
                symbol=self.symbol,
                open=bar.get("open", 0),
                high=bar.get("high", 0),
                low=bar.get("low", 0),
                close=bar.get("close", 0),
                volume=bar.get("volume", 0),
            )

        # Convert buffer to DataFrame for FeatureEngine
        df = pd.DataFrame(self._bar_buffer)
        df.set_index('timestamp', inplace=True)

        # Calculate features using FeatureEngine
        features = self._feature_engine.calculate_features(df, self.symbol)

        if features is None:
            # Fallback to basic features
            return FeatureVector(
                timestamp=bar.get("timestamp", datetime.utcnow()),
                symbol=self.symbol,
                open=bar.get("open", 0),
                high=bar.get("high", 0),
                low=bar.get("low", 0),
                close=bar.get("close", 0),
                volume=bar.get("volume", 0),
            )

        return features

    async def _update_regime(self, features: FeatureVector) -> RegimeState:
        """Update regime classification.

        Uses JSON-based regime detection if available, otherwise falls back
        to hardcoded regime classification.

        Args:
            features: Current features

        Returns:
            Updated RegimeState
        """
        # Store previous regime name (for JSON Entry last_closed_regime())
        if hasattr(self, '_regime') and self._regime:
            prev_regime_name = getattr(self._regime, 'regime_name', None)
            if prev_regime_name:
                self._prev_regime_name = prev_regime_name

        # Try JSON-based regime detection first
        if hasattr(self, '_json_catalog') and self._json_catalog:
            try:
                regime_state = self._json_catalog.get_current_regime(features)
                logger.debug(
                    f"JSON regime detected: {regime_state.regime_name} "
                    f"(strength: {regime_state.regime_strength:.2f})"
                )
                return regime_state
            except Exception as e:
                logger.error(
                    f"JSON regime detection failed: {e}. "
                    f"Falling back to hardcoded detection."
                )
                # Fall through to hardcoded detection

        # Hardcoded regime detection (fallback)
        regime = RegimeType.UNKNOWN
        volatility = VolatilityLevel.NORMAL

        # Trend classification via ADX
        if features.adx is not None:
            if features.adx > 25:
                # Strong trend - determine direction
                if features.plus_di and features.minus_di:
                    if features.plus_di > features.minus_di:
                        regime = RegimeType.TREND_UP
                    else:
                        regime = RegimeType.TREND_DOWN
                elif features.close and features.sma_20:
                    regime = (
                        RegimeType.TREND_UP
                        if features.close > features.sma_20
                        else RegimeType.TREND_DOWN
                    )
            else:
                regime = RegimeType.RANGE

        # Volatility classification via ATR or BB width
        if features.atr_14 and features.close:
            atr_pct = (features.atr_14 / features.close) * 100
            if atr_pct > 3:
                volatility = VolatilityLevel.EXTREME
            elif atr_pct > 2:
                volatility = VolatilityLevel.HIGH
            elif atr_pct < 0.5:
                volatility = VolatilityLevel.LOW
            else:
                volatility = VolatilityLevel.NORMAL

        return RegimeState(
            timestamp=features.timestamp,
            regime=regime,
            volatility=volatility,
            adx_value=features.adx,
            atr_pct=(features.atr_14 / features.close * 100) if features.atr_14 and features.close else None,
            bb_width_pct=features.bb_width
        )

    def _get_active_json_strategies(
        self,
        features: FeatureVector
    ) -> list[str]:
        """Get active strategy IDs from JSON config.

        Args:
            features: Current feature vector

        Returns:
            List of strategy IDs to execute, or empty list if JSON not available
        """
        if not hasattr(self, '_json_catalog') or not self._json_catalog:
            return []

        try:
            matched_sets = self._json_catalog.get_active_strategy_sets(features)
            strategy_ids = self._json_catalog.get_strategy_ids_from_sets(matched_sets)

            if matched_sets:
                logger.info(
                    f"JSON strategies active: {strategy_ids} "
                    f"(from {len(matched_sets)} strategy sets)"
                )

            return strategy_ids

        except Exception as e:
            logger.error(f"Failed to get JSON strategies: {e}")
            return []

    def _execute_json_strategy_sets_with_overrides(
        self,
        features: FeatureVector
    ) -> dict[str, Any]:
        """Execute matched strategy sets with parameter overrides applied.

        This method:
        1. Gets active strategy sets from JSON config
        2. Applies parameter overrides (indicators, strategy params)
        3. Returns strategy execution context with overridden values
        4. Caller is responsible for restoring state after execution

        Args:
            features: Current feature vector

        Returns:
            Dict with:
                - matched_sets: List of MatchedStrategySet
                - execution_contexts: List of ExecutionContext (for state restoration)
                - active_strategy_ids: List of strategy IDs to execute
                - current_indicators: Current indicator definitions (with overrides)
                - current_strategies: Current strategy definitions (with overrides)
        """
        if not hasattr(self, '_json_catalog') or not self._json_catalog:
            return {
                "matched_sets": [],
                "execution_contexts": [],
                "active_strategy_ids": [],
                "current_indicators": {},
                "current_strategies": {},
            }

        try:
            # Get matched strategy sets
            matched_sets = self._json_catalog.get_active_strategy_sets(features)

            if not matched_sets:
                return {
                    "matched_sets": [],
                    "execution_contexts": [],
                    "active_strategy_ids": [],
                    "current_indicators": {},
                    "current_strategies": {},
                }

            # Prepare execution contexts for each matched set
            execution_contexts = []
            active_strategy_ids = []

            for matched_set in matched_sets:
                # Prepare execution (applies overrides)
                context = self._json_catalog.strategy_executor.prepare_execution(
                    matched_set
                )
                execution_contexts.append(context)

                # Collect strategy IDs
                strategy_ids = self._json_catalog.strategy_executor.get_strategy_ids_from_set(
                    matched_set.strategy_set
                )
                active_strategy_ids.extend(strategy_ids)

            # Get current (overridden) indicators and strategies
            current_indicators = self._json_catalog.strategy_executor.current_indicators
            current_strategies = self._json_catalog.strategy_executor.current_strategies

            logger.info(
                f"Executed {len(matched_sets)} strategy sets with overrides. "
                f"Active strategies: {active_strategy_ids}"
            )

            return {
                "matched_sets": matched_sets,
                "execution_contexts": execution_contexts,
                "active_strategy_ids": active_strategy_ids,
                "current_indicators": current_indicators,
                "current_strategies": current_strategies,
            }

        except Exception as e:
            logger.error(f"Failed to execute JSON strategy sets: {e}")
            return {
                "matched_sets": [],
                "execution_contexts": [],
                "active_strategy_ids": [],
                "current_indicators": {},
                "current_strategies": {},
            }

    def _restore_json_strategy_state(
        self,
        execution_contexts: list
    ) -> None:
        """Restore original state after JSON strategy execution.

        Args:
            execution_contexts: List of ExecutionContext from prepare_execution
        """
        if not hasattr(self, '_json_catalog') or not self._json_catalog:
            return

        try:
            for context in execution_contexts:
                self._json_catalog.strategy_executor.restore_state(context)

            logger.debug(
                f"Restored state for {len(execution_contexts)} execution contexts"
            )

        except Exception as e:
            logger.error(f"Failed to restore JSON strategy state: {e}")

    def _create_entry_order(
        self,
        features: FeatureVector,
        signal: Signal
    ) -> OrderIntent:
        """Create entry order intent.

        Args:
            features: Current features
            signal: Entry signal

        Returns:
            OrderIntent
        """
        # Calculate position size
        risk_pct = self.config.risk.risk_per_trade_pct
        sl_distance = abs(signal.entry_price - signal.stop_loss_price)
        # Simplified: assume $10000 account
        account_value = 10000
        risk_amount = account_value * (risk_pct / 100)
        quantity = risk_amount / sl_distance if sl_distance > 0 else 0
        position_value = quantity * signal.entry_price

        return OrderIntent(
            symbol=self.symbol,
            side=signal.side,
            action="entry",
            quantity=quantity,
            order_type="market",
            stop_price=signal.stop_loss_price,
            signal_id=signal.id,
            reason=f"Entry signal {signal.id}: {signal.side.value}",
            risk_amount=risk_amount,
            position_value=position_value
        )

    def _create_decision(
        self,
        action: BotAction,
        side: TradeSide,
        features: FeatureVector,
        reason_codes: list[str],
        stop_before: float | None = None,
        stop_after: float | None = None,
        notes: str = ""
    ) -> BotDecision:
        """Create bot decision record.

        Args:
            action: Decision action
            side: Trade side
            features: Current features
            reason_codes: Decision reasons
            stop_before: Stop price before (if applicable)
            stop_after: Stop price after (if applicable)
            notes: Additional notes

        Returns:
            BotDecision
        """
        return BotDecision(
            symbol=self.symbol,
            action=action,
            side=side,
            confidence=0.5,  # Would be set by LLM in FULL_KI mode
            features_hash=features.compute_hash(),
            regime=self._regime.regime,
            strategy_name=self._active_strategy.name if self._active_strategy else None,
            stop_price_before=stop_before,
            stop_price_after=stop_after,
            reason_codes=reason_codes,
            notes=notes,
            source="rule_based"
        )

    def _on_state_transition(self, transition: "StateTransition") -> None:
        """Handle state transition callback.

        Args:
            transition: State transition record
        """
        logger.debug(
            f"Bot transition: {transition.from_state.value} -> "
            f"{transition.to_state.value} ({transition.trigger.value})"
        )

        # Publish to event bus if available
        if self._event_bus:
            self._event_bus.emit(
                "bot.state_change",
                {
                    "symbol": self.symbol,
                    "from_state": transition.from_state.value,
                    "to_state": transition.to_state.value,
                    "trigger": transition.trigger.value,
                    "timestamp": transition.timestamp.isoformat()
                }
            )

    # ==================== Order Fill Simulation ====================

    def simulate_fill(
        self,
        fill_price: float,
        fill_qty: float,
        order_id: str = "sim"
    ) -> None:
        """Simulate order fill (for paper trading).

        Args:
            fill_price: Fill price
            fill_qty: Filled quantity
            order_id: Order ID
        """
        if not self._current_signal:
            logger.warning("No signal for fill simulation")
            return

        # Create position
        sl_price = self._current_signal.stop_loss_price
        self._position = PositionState(
            symbol=self.symbol,
            side=self._current_signal.side,
            entry_time=datetime.utcnow(),
            entry_price=fill_price,
            quantity=fill_qty,
            current_price=fill_price,
            trailing=TrailingState(
                mode=self.config.bot.trailing_mode,
                current_stop_price=sl_price,
                initial_stop_price=sl_price,
                highest_price=fill_price,
                lowest_price=fill_price,
                trailing_distance=abs(fill_price - sl_price)
            ),
            signal_id=self._current_signal.id,
            strategy_name=self._active_strategy.name if self._active_strategy else None
        )

        # Transition to MANAGE
        self._state_machine.on_order_fill(fill_price, fill_qty, order_id)
        self._current_signal = None

        logger.info(f"Position opened: {self._position.side.value} @ {fill_price}")

    # ==================== Serialization ====================

    def to_dict(self) -> dict[str, Any]:
        """Serialize controller state.

        Returns:
            Controller state as dict
        """
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "run_id": self._run_id,
            "running": self._running,
            "state_machine": self._state_machine.to_dict(),
            "regime": self._regime.model_dump() if self._regime else None,
            "position": self._position.model_dump() if self._position else None,
            "trades_today": self._trades_today,
            "daily_pnl": self._daily_pnl,
            "consecutive_losses": self._consecutive_losses,
            "bar_count": self._bar_count,
        }
