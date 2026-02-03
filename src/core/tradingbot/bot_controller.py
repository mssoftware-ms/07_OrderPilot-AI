"""Tradingbot Controller - Main Orchestrator.

Main orchestrator for the trading bot. One controller per symbol/timeframe.
Coordinates state machine, feature calculation, signal generation,
and trade management.

REFACTORED v2: Split into modular components (2026-01-31)
- bot_controller_state.py: State management & initialization
- bot_controller_events.py: Event handling & lifecycle
- bot_controller_logic.py: Business logic (strategy, config, regime)
- bot_helpers.py: Feature/regime calculation, order creation (existing mixin)
- bot_signal_logic.py: Entry scoring and signal creation (existing mixin)
- bot_state_handlers.py: State processing methods (existing mixin)
- bot_trailing_stops.py: Trailing stop calculations (existing mixin)

This file now serves as the main orchestrator, inheriting from all components
and implementing only the main event loop (on_bar).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .bot_controller_events import BotControllerEvents
from .bot_controller_logic import BotControllerLogic
from .bot_controller_state import BotControllerState
from .bot_helpers import BotHelpersMixin
from .bot_signal_logic import BotSignalLogicMixin
from .bot_state_handlers import BotStateHandlersMixin
from .bot_trailing_stops import BotTrailingStopsMixin
from .models import BotDecision

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BotController(
    BotControllerState,      # State management & initialization
    BotControllerEvents,     # Event handling & lifecycle
    BotControllerLogic,      # Business logic
    BotStateHandlersMixin,   # State processing methods (existing mixin)
    BotSignalLogicMixin,     # Entry scoring and signal creation (existing mixin)
    BotTrailingStopsMixin,   # Trailing stop calculations (existing mixin)
    BotHelpersMixin,         # Feature/regime calculation, order creation (existing mixin)
):
    """Main trading bot controller.

    Orchestrates all bot operations for a single symbol/timeframe.
    Single source of truth for bot state and decisions.

    Functionality is distributed across base classes and mixins:
    - BotControllerState: State management & initialization
    - BotControllerEvents: Event handling & lifecycle
    - BotControllerLogic: Business logic (strategy, config, regime)
    - BotStateHandlersMixin: State processing methods
    - BotSignalLogicMixin: Entry scoring and signal creation
    - BotTrailingStopsMixin: Trailing stop calculations
    - BotHelpersMixin: Feature/regime calculation, order creation

    Attributes:
        config: Full bot configuration
        symbol: Trading symbol
        state_machine: Bot state machine
        position: Current position (if any)
        current_signal: Active signal (if any)
        regime: Current market regime
    """

    # ==================== Main Processing ====================

    async def on_bar(self, bar: dict[str, Any]) -> BotDecision | None:
        """Process a new bar (candle close).

        Main entry point for bot logic. Called on each candle close.

        Args:
            bar: Bar data with OHLCV

        Returns:
            BotDecision if any action taken, None otherwise
        """
        if not self._running:
            return None

        # Issue #11: Auto-recovery from ERROR state on next bar
        if self._state_machine.is_error():
            self._log_activity("RECOVERY", "Auto-clearing error state, resuming normal operation")
            self._state_machine.clear_error()

        self._bar_count += 1

        # Log new bar with price data
        bar_time = bar.get('timestamp', bar.get('time', 'N/A'))
        self._log_activity(
            "BAR",
            f"#{self._bar_count} | O:{bar.get('open', 0):.2f} H:{bar.get('high', 0):.2f} "
            f"L:{bar.get('low', 0):.2f} C:{bar.get('close', 0):.2f} V:{bar.get('volume', 0):,.0f}"
        )

        try:
            # 1. Calculate features
            features = await self._calculate_features(bar)
            features.is_candle_close = True  # Mark as candle-close event for CEL evaluation
            self._last_features = features

            # Log feature summary (handle None values during warmup)
            if features.rsi_14 is not None:
                self._log_activity(
                    "FEATURE",
                    f"RSI:{features.rsi_14:.1f} | ATR:{features.atr_14 or 0:.4f} | "
                    f"SMA20:{features.sma_20 or 0:.2f} | EMA12:{features.ema_12 or 0:.2f} | "
                    f"BB-Upper:{features.bb_upper or 0:.2f} BB-Lower:{features.bb_lower or 0:.2f}"
                )

            # 2. Update regime
            old_regime = self._regime.regime if self._regime else None
            self._regime = await self._update_regime(features)

            # Log regime if changed
            if old_regime != self._regime.regime:
                self._log_activity(
                    "REGIME",
                    f"Marktregime: {self._regime.regime.value} | "
                    f"Volatilitaet: {self._regime.volatility.value} | "
                    f"Konfidenz: {self._regime.regime_confidence:.1%}"
                )

            # 2b. Update trailing stop for live trading (after regime update)
            if self._position and self.config.bot.trailing_enabled:
                await self._update_trailing_stop_live(features)

            # 2a. Check for JSON-based regime change and strategy switching
            if hasattr(self, '_json_config') and self._json_config is not None:
                strategy_switched = self._check_regime_change_and_switch(features)
                if strategy_switched:
                    self._log_activity(
                        "REGIME_CHANGE",
                        "Automatischer Strategie-Wechsel aufgrund Regime-Änderung"
                    )

            # 3. Daily strategy selection (once per day or on first bar)
            await self._check_strategy_selection(features)

            # 4. Process based on state
            state_before = self._state_machine.state
            decision = await self._process_state(features, bar)

            # Log state and decision
            strategy_name = self._active_strategy.name if self._active_strategy else "None"
            self._log_activity(
                "STATE",
                f"Status: {state_before.value} | Strategie: {strategy_name} | "
                f"Position: {'JA' if self._position else 'NEIN'}"
            )

            # 4. Record decision
            if decision:
                self._decisions.append(decision)
                reasons = ", ".join(decision.reason_codes) if decision.reason_codes else "keine"
                self._log_activity(
                    "DECISION",
                    f"Aktion: {decision.action.value} | Konfidenz: {decision.confidence:.1%} | "
                    f"Gruende: {reasons}"
                )
                if self._on_decision:
                    self._on_decision(decision)

            return decision

        except Exception as e:
            self._log_activity("ERROR", f"Fehler bei Bar-Verarbeitung: {e}")
            logger.error(f"Error processing bar: {e}", exc_info=True)
            self._state_machine.error(str(e))
            return None
