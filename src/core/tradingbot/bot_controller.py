"""Tradingbot Controller.

Main orchestrator for the trading bot. One controller per symbol/timeframe.
Coordinates state machine, feature calculation, signal generation,
and trade management.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable
from uuid import uuid4

import pandas as pd

from .config import FullBotConfig, KIMode, TrailingMode
from .feature_engine import FeatureEngine
from .models import (
    BotAction,
    BotDecision,
    FeatureVector,
    OrderIntent,
    PositionState,
    RegimeState,
    RegimeType,
    Signal,
    SignalType,
    StrategyProfile,
    TradeSide,
    TrailingState,
    VolatilityLevel,
)
from .state_machine import BotState, BotStateMachine, BotTrigger, StateTransition
from .strategy_selector import StrategySelector
from .strategy_catalog import StrategyCatalog

if TYPE_CHECKING:
    from src.common.event_bus import EventBus

logger = logging.getLogger(__name__)


class BotController:
    """Main trading bot controller.

    Orchestrates all bot operations for a single symbol/timeframe.
    Single source of truth for bot state and decisions.

    Attributes:
        config: Full bot configuration
        symbol: Trading symbol
        state_machine: Bot state machine
        position: Current position (if any)
        current_signal: Active signal (if any)
        regime: Current market regime
    """

    def __init__(
        self,
        config: FullBotConfig,
        event_bus: "EventBus | None" = None,
        on_signal: Callable[[Signal], None] | None = None,
        on_decision: Callable[[BotDecision], None] | None = None,
        on_order: Callable[[OrderIntent], None] | None = None,
        on_log: Callable[[str, str], None] | None = None,
    ):
        """Initialize bot controller.

        Args:
            config: Full bot configuration
            event_bus: Event bus for publishing events
            on_signal: Callback for new signals
            on_decision: Callback for bot decisions
            on_order: Callback for order intents
            on_log: Callback for activity logging (log_type, message)
        """
        self.config = config
        self.symbol = config.bot.symbol
        self.timeframe = config.bot.timeframe
        self._event_bus = event_bus

        # Callbacks
        self._on_signal = on_signal
        self._on_decision = on_decision
        self._on_order = on_order
        self._on_log = on_log

        # State machine
        self._state_machine = BotStateMachine(
            symbol=self.symbol,
            on_transition=self._on_state_transition
        )

        # Current state
        self._position: PositionState | None = None
        self._current_signal: Signal | None = None
        self._regime: RegimeState = RegimeState()
        self._active_strategy: StrategyProfile | None = None
        self._strategy_locked_until: datetime | None = None

        # Feature engine and bar buffer
        self._feature_engine = FeatureEngine()
        self._bar_buffer: list[dict] = []  # Rolling buffer of recent bars
        self._max_buffer_size: int = 120  # Keep 2 hours of 1-min bars

        # Feature/bar tracking
        self._last_features: FeatureVector | None = None
        self._bar_count: int = 0

        # Decision history
        self._decisions: list[BotDecision] = []
        self._trades_today: int = 0
        self._daily_pnl: float = 0.0
        self._consecutive_losses: int = 0

        # Strategy selection
        self._strategy_catalog = StrategyCatalog()
        self._strategy_selector = StrategySelector(
            catalog=self._strategy_catalog,
            allow_intraday_switch=False,
            require_regime_flip_for_switch=True
        )
        self._last_strategy_selection_date: datetime | None = None

        # Run state
        self._running: bool = False
        self._run_id: str = str(uuid4())[:8]

        logger.info(
            f"BotController initialized: symbol={self.symbol}, "
            f"timeframe={self.timeframe}, run_id={self._run_id}"
        )

    # ==================== Properties ====================

    @property
    def state(self) -> BotState:
        """Current bot state."""
        return self._state_machine.state

    @property
    def position(self) -> PositionState | None:
        """Current position."""
        return self._position

    @property
    def regime(self) -> RegimeState:
        """Current market regime."""
        return self._regime

    @property
    def active_strategy(self) -> StrategyProfile | None:
        """Active strategy profile."""
        return self._active_strategy

    @property
    def is_running(self) -> bool:
        """Check if bot is running."""
        return self._running

    @property
    def can_trade(self) -> bool:
        """Check if bot can enter new trades."""
        if not self._running:
            return False
        if self._state_machine.is_paused() or self._state_machine.is_error():
            return False
        if self._trades_today >= self.config.risk.max_trades_per_day:
            return False
        if abs(self._daily_pnl) >= self.config.risk.max_daily_loss_pct:
            return False
        if self._consecutive_losses >= self.config.risk.loss_streak_cooldown:
            return False
        return True

    # ==================== Activity Logging ====================

    def _log_activity(self, log_type: str, message: str) -> None:
        """Log activity to both logger and UI callback.

        Args:
            log_type: Type of log entry (INFO, BAR, FEATURE, SIGNAL, etc.)
            message: Log message
        """
        logger.info(f"[{log_type}] {message}")
        if self._on_log:
            try:
                self._on_log(log_type, message)
            except Exception as e:
                logger.error(f"Log callback error: {e}")

    # ==================== Lifecycle ====================

    def start(self) -> None:
        """Start the bot.

        Note: Synchronous for easy UI integration. Async operations
        happen in on_bar() which should be awaited.
        """
        if self._running:
            logger.warning(f"Bot already running: {self.symbol}")
            return

        self._running = True
        self._run_id = str(uuid4())[:8]
        self._log_activity(
            "START",
            f"Bot gestartet: {self.symbol} | Timeframe: {self.timeframe} | "
            f"KI-Mode: {self.config.bot.ki_mode.value} | Run-ID: {self._run_id}"
        )

    def stop(self) -> None:
        """Stop the bot.

        Note: Synchronous for easy UI integration.
        """
        if not self._running:
            return

        self._running = False
        self._log_activity(
            "STOP",
            f"Bot gestoppt: {self.symbol} | Bars verarbeitet: {self._bar_count} | "
            f"Trades heute: {self._trades_today}"
        )

    def pause(self, reason: str = "manual") -> None:
        """Pause the bot."""
        self._state_machine.pause(reason)
        logger.info(f"Bot paused: {reason}")

    def resume(self) -> None:
        """Resume the bot."""
        self._state_machine.resume()
        logger.info("Bot resumed")

    def reset(self) -> None:
        """Reset bot to initial state."""
        self._state_machine.reset(clear_history=False)
        self._position = None
        self._current_signal = None
        self._trades_today = 0
        self._daily_pnl = 0.0
        self._consecutive_losses = 0
        logger.info(f"Bot reset: symbol={self.symbol}")

    def warmup_from_history(self, bars: list[dict]) -> int:
        """Pre-fill bar buffer with historical data for instant warmup.

        This allows the bot to skip the warmup period by using existing
        chart data instead of waiting for 60+ new bars.

        Args:
            bars: List of bar dicts with keys: timestamp, open, high, low, close, volume

        Returns:
            Number of bars loaded into buffer
        """
        if not bars:
            logger.warning("No bars provided for warmup")
            return 0

        # Clear existing buffer
        self._bar_buffer.clear()

        # Take last N bars (up to max buffer size)
        recent_bars = bars[-self._max_buffer_size:]

        for bar in recent_bars:
            self._bar_buffer.append({
                'timestamp': bar.get('timestamp', datetime.utcnow()),
                'open': bar.get('open', 0),
                'high': bar.get('high', 0),
                'low': bar.get('low', 0),
                'close': bar.get('close', 0),
                'volume': bar.get('volume', 0),
            })

        loaded_count = len(self._bar_buffer)
        min_bars = self._feature_engine.MIN_BARS

        if loaded_count >= min_bars:
            self._log_activity(
                "WARMUP",
                f"Warmup abgeschlossen: {loaded_count} Bars aus Chart-Historie geladen (min: {min_bars})"
            )
        else:
            self._log_activity(
                "WARMUP",
                f"Teilweise Warmup: {loaded_count}/{min_bars} Bars geladen"
            )

        logger.info(f"Warmup: loaded {loaded_count} bars from chart history")
        return loaded_count

    def set_ki_mode(self, mode: str) -> None:
        """Set KI mode dynamically.

        Args:
            mode: "NO_KI", "LOW_KI", or "FULL_KI" (case-insensitive)
        """
        from .config import KIMode
        try:
            # Convert uppercase UI values to lowercase enum values
            mode_lower = mode.lower()
            self.config.bot.ki_mode = KIMode(mode_lower)
            logger.info(f"KI mode changed to: {mode}")
        except ValueError:
            logger.warning(f"Invalid KI mode: {mode}")

    def force_strategy_reselection(self) -> None:
        """Force strategy re-selection on next bar.

        Clears current strategy so the selector will pick a new one.
        """
        self._active_strategy = None
        self._strategy_locked_until = None  # Clear lock if any
        logger.info("Strategy re-selection forced")

    @property
    def current_strategy(self) -> "StrategyProfile | None":
        """Get current active strategy."""
        return self._active_strategy

    @property
    def last_regime(self) -> "RegimeState":
        """Get last detected regime."""
        return self._regime

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
                    f"Volatilität: {self._regime.volatility.value} | "
                    f"Konfidenz: {self._regime.regime_confidence:.1%}"
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
                    f"Gründe: {reasons}"
                )
                if self._on_decision:
                    self._on_decision(decision)

            return decision

        except Exception as e:
            self._log_activity("ERROR", f"Fehler bei Bar-Verarbeitung: {e}")
            logger.error(f"Error processing bar: {e}", exc_info=True)
            self._state_machine.error(str(e))
            return None

    async def _process_state(
        self,
        features: FeatureVector,
        bar: dict[str, Any]
    ) -> BotDecision | None:
        """Process current state and generate decision.

        Args:
            features: Current feature vector
            bar: Current bar data

        Returns:
            BotDecision or None
        """
        state = self._state_machine.state

        if state == BotState.FLAT:
            return await self._process_flat(features)

        elif state == BotState.SIGNAL:
            return await self._process_signal(features)

        elif state == BotState.ENTERED:
            # Waiting for fill - check timeout
            return None

        elif state == BotState.MANAGE:
            return await self._process_manage(features, bar)

        elif state == BotState.EXITED:
            # Reset for next trade
            self._state_machine.trigger(BotTrigger.RESET)
            return None

        return None

    async def _check_strategy_selection(self, features: FeatureVector) -> None:
        """Check if strategy selection is needed (daily or forced).

        Args:
            features: Current feature vector
        """
        now = datetime.utcnow()

        # Check if new day or forced reselection
        needs_selection = (
            self._active_strategy is None or
            self._last_strategy_selection_date is None or
            now.date() > self._last_strategy_selection_date.date()
        )

        if not needs_selection:
            return

        # Select best strategy for current regime
        try:
            result = self._strategy_selector.select_strategy(
                regime=self._regime,
                symbol=self.symbol
            )

            if result.selected_strategy:
                # Look up StrategyProfile from catalog (result.selected_strategy is a string name)
                strategy_def = self._strategy_catalog.get_strategy(result.selected_strategy)
                if strategy_def:
                    self._active_strategy = strategy_def.profile
                    self._last_strategy_selection_date = now

                    self._log_activity(
                        "STRATEGY",
                        f"Tagesstrategie gewählt: {self._active_strategy.name} | "
                        f"Score: {result.strategy_scores.get(result.selected_strategy, 0):.2f} | "
                        f"Regime: {self._regime.regime.value}"
                    )
                else:
                    self._log_activity(
                        "ERROR",
                        f"Strategie '{result.selected_strategy}' nicht im Katalog gefunden"
                    )

        except Exception as e:
            self._log_activity("ERROR", f"Strategie-Auswahl fehlgeschlagen: {e}")
            # Fallback to first available strategy
            strategies = self._strategy_catalog.get_all_strategies()
            if strategies:
                # strategies[0] is StrategyDefinition, need .profile for StrategyProfile
                self._active_strategy = strategies[0].profile
                self._log_activity(
                    "STRATEGY",
                    f"Fallback-Strategie: {self._active_strategy.name}"
                )

    async def _process_flat(self, features: FeatureVector) -> BotDecision | None:
        """Process FLAT state - look for entry signals.

        Args:
            features: Current feature vector

        Returns:
            BotDecision or None
        """
        if not self.can_trade:
            return None

        # Calculate entry score
        long_score = self._calculate_entry_score(features, TradeSide.LONG)
        short_score = self._calculate_entry_score(features, TradeSide.SHORT)

        # Get best signal
        if long_score > short_score and long_score >= self._get_entry_threshold():
            side = TradeSide.LONG
            score = long_score
        elif short_score > long_score and short_score >= self._get_entry_threshold():
            side = TradeSide.SHORT
            score = short_score
        else:
            # No valid signal
            return self._create_decision(
                BotAction.NO_TRADE,
                TradeSide.NONE,
                features,
                ["SCORE_BELOW_THRESHOLD"]
            )

        # Create signal
        signal = self._create_signal(features, side, score)
        self._current_signal = signal

        if self._on_signal:
            self._on_signal(signal)

        # Transition to SIGNAL state
        self._state_machine.on_signal(signal, confirmed=False)

        return self._create_decision(
            BotAction.NO_TRADE,  # Signal detected, not entry yet
            side,
            features,
            ["SIGNAL_DETECTED"],
            notes=f"Signal {signal.id}: {side.value} score={score:.2f}"
        )

    async def _process_signal(self, features: FeatureVector) -> BotDecision | None:
        """Process SIGNAL state - confirm or expire signal.

        Args:
            features: Current feature vector

        Returns:
            BotDecision or None
        """
        if not self._current_signal:
            self._state_machine.trigger(BotTrigger.SIGNAL_EXPIRED)
            return None

        # Check signal still valid
        side = self._current_signal.side
        new_score = self._calculate_entry_score(features, side)

        if new_score < self._get_entry_threshold() * 0.9:  # Allow some slack
            # Signal expired
            self._current_signal = None
            self._state_machine.trigger(BotTrigger.SIGNAL_EXPIRED)
            return self._create_decision(
                BotAction.NO_TRADE,
                TradeSide.NONE,
                features,
                ["SIGNAL_EXPIRED"]
            )

        # Confirm signal and enter
        self._current_signal.signal_type = SignalType.CONFIRMED
        self._current_signal.score = new_score
        self._state_machine.on_signal(self._current_signal, confirmed=True)

        # Create entry order intent
        order = self._create_entry_order(features, self._current_signal)

        if self._on_order:
            self._on_order(order)

        # Get initial stop price from signal
        initial_stop = self._current_signal.stop_loss_price

        return self._create_decision(
            BotAction.ENTER,
            side,
            features,
            ["SIGNAL_CONFIRMED", "ENTRY_ORDER_SENT"],
            stop_after=initial_stop,  # Initial stop price for chart display
            notes=f"Entry order: {order.id}, Initial SL: {initial_stop:.4f}"
        )

    async def _process_manage(
        self,
        features: FeatureVector,
        bar: dict[str, Any]
    ) -> BotDecision | None:
        """Process MANAGE state - manage open position.

        Args:
            features: Current feature vector
            bar: Current bar data

        Returns:
            BotDecision or None
        """
        if not self._position:
            logger.error("MANAGE state but no position")
            self._state_machine.error("No position in MANAGE state")
            return None

        price = bar.get("close", features.close)
        self._position.update_price(price)
        self._position.bars_held += 1

        # Check stop hit
        if self._position.is_stopped_out():
            return await self._handle_stop_hit(features)

        # Check exit signals
        exit_signal = self._check_exit_signals(features)
        if exit_signal:
            return await self._handle_exit_signal(features, exit_signal)

        # Update trailing stop
        new_stop = self._calculate_trailing_stop(features, self._position)
        if new_stop:
            old_stop = self._position.trailing.current_stop_price
            updated = self._position.trailing.update_stop(
                new_stop,
                self._bar_count,
                datetime.utcnow(),
                is_long=self._position.side == TradeSide.LONG
            )

            if updated:
                self._state_machine.trigger(BotTrigger.STOP_UPDATED)
                return self._create_decision(
                    BotAction.ADJUST_STOP,
                    self._position.side,
                    features,
                    ["TRAILING_STOP_UPDATED"],
                    stop_before=old_stop,
                    stop_after=new_stop
                )

        # Hold position
        return self._create_decision(
            BotAction.HOLD,
            self._position.side,
            features,
            ["POSITION_HELD"]
        )

    async def _handle_stop_hit(self, features: FeatureVector) -> BotDecision:
        """Handle stop-loss hit.

        Args:
            features: Current feature vector

        Returns:
            BotDecision
        """
        self._state_machine.on_stop_hit(features.close)

        pnl = self._position.unrealized_pnl if self._position else 0
        self._daily_pnl += pnl

        if pnl < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        self._trades_today += 1
        side = self._position.side if self._position else TradeSide.NONE
        self._position = None

        return self._create_decision(
            BotAction.EXIT,
            side,
            features,
            ["STOP_HIT", "POSITION_CLOSED"],
            notes=f"P&L: {pnl:.2f}"
        )

    async def _handle_exit_signal(
        self,
        features: FeatureVector,
        reason: str
    ) -> BotDecision:
        """Handle exit signal.

        Args:
            features: Current feature vector
            reason: Exit reason

        Returns:
            BotDecision
        """
        self._state_machine.on_exit_signal(reason)

        pnl = self._position.unrealized_pnl if self._position else 0
        self._daily_pnl += pnl

        if pnl < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        self._trades_today += 1
        side = self._position.side if self._position else TradeSide.NONE
        self._position = None

        return self._create_decision(
            BotAction.EXIT,
            side,
            features,
            [reason.upper(), "POSITION_CLOSED"],
            notes=f"P&L: {pnl:.2f}"
        )

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

    def _get_entry_threshold(self) -> float:
        """Get entry threshold based on active strategy and regime."""
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

    # ==================== Trailing Stop ====================

    def _calculate_trailing_stop(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> float | None:
        """Calculate new trailing stop price.

        Args:
            features: Current features
            position: Current position

        Returns:
            New stop price or None if no update needed
        """
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

        Args:
            features: Current features
            position: Current position

        Returns:
            New stop price or None
        """
        distance_pct = self.config.risk.trailing_pct_distance
        min_step = self.config.risk.trailing_min_step_pct

        if position.side == TradeSide.LONG:
            # Trail up based on highest price
            new_stop = position.trailing.highest_price * (1 - distance_pct / 100)
            current_stop = position.trailing.current_stop_price

            # Check minimum step
            step_pct = ((new_stop - current_stop) / current_stop) * 100
            if step_pct >= min_step:
                return new_stop

        else:  # SHORT
            # Trail down based on lowest price
            new_stop = position.trailing.lowest_price * (1 + distance_pct / 100)
            current_stop = position.trailing.current_stop_price

            # Check minimum step
            step_pct = ((current_stop - new_stop) / current_stop) * 100
            if step_pct >= min_step:
                return new_stop

        return None

    def _trailing_atr(
        self,
        features: FeatureVector,
        position: PositionState
    ) -> float | None:
        """ATR-based trailing stop.

        Args:
            features: Current features
            position: Current position

        Returns:
            New stop price or None
        """
        if features.atr_14 is None:
            return None

        atr_multiple = self.config.risk.trailing_atr_multiple
        min_step = self.config.risk.trailing_min_step_pct

        # Adjust ATR multiple by regime
        if self._regime.volatility == VolatilityLevel.HIGH:
            atr_multiple *= 1.5
        elif self._regime.volatility == VolatilityLevel.LOW:
            atr_multiple *= 0.8

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

            step_pct = ((current_stop - new_stop) / current_stop) * 100
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

    # ==================== Exit Signals ====================

    def _check_exit_signals(self, features: FeatureVector) -> str | None:
        """Check for exit signals.

        Args:
            features: Current features

        Returns:
            Exit reason or None
        """
        if not self._position:
            return None

        # Momentum reversal
        if features.rsi_14 is not None:
            if self._position.side == TradeSide.LONG and features.rsi_14 > 80:
                return "RSI_EXTREME_OVERBOUGHT"
            elif self._position.side == TradeSide.SHORT and features.rsi_14 < 20:
                return "RSI_EXTREME_OVERSOLD"

        # MACD cross
        if features.macd is not None and features.macd_signal is not None:
            if self._position.side == TradeSide.LONG:
                if features.macd < features.macd_signal and features.macd_hist and features.macd_hist < 0:
                    return "MACD_BEARISH_CROSS"
            else:
                if features.macd > features.macd_signal and features.macd_hist and features.macd_hist > 0:
                    return "MACD_BULLISH_CROSS"

        # Time stop (optional)
        max_bars = 200  # ~3 hours at 1m
        if self._position.bars_held > max_bars:
            return "TIME_STOP"

        return None

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

        Args:
            features: Current features

        Returns:
            Updated RegimeState
        """
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

        return OrderIntent(
            symbol=self.symbol,
            side=signal.side,
            action="entry",
            quantity=quantity,
            order_type="market",
            stop_price=signal.stop_loss_price,
            signal_id=signal.id,
            reason=f"Entry signal {signal.id}: {signal.side.value}"
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

    def _on_state_transition(self, transition: StateTransition) -> None:
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
