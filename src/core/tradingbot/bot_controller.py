"""Tradingbot Controller.

Main orchestrator for the trading bot. One controller per symbol/timeframe.
Coordinates state machine, feature calculation, signal generation,
and trade management.

REFACTORED: Extracted functionality into mixins to meet 600 LOC limit.
- BotStateHandlersMixin: State processing methods
- BotSignalLogicMixin: Entry scoring and signal creation
- BotTrailingStopsMixin: Trailing stop calculations
- BotHelpersMixin: Feature/regime calculation, order creation
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable
from uuid import uuid4

from .bot_helpers import BotHelpersMixin
from .bot_signal_logic import BotSignalLogicMixin
from .bot_state_handlers import BotStateHandlersMixin
from .bot_trailing_stops import BotTrailingStopsMixin
from .config import FullBotConfig, KIMode
from .feature_engine import FeatureEngine
from .models import (
    BotDecision,
    FeatureVector,
    OrderIntent,
    PositionState,
    RegimeState,
    Signal,
    StrategyProfile,
)
from .state_machine import BotState, BotStateMachine
from .strategy_catalog import StrategyCatalog
from .strategy_selector import StrategySelector

if TYPE_CHECKING:
    from src.common.event_bus import EventBus

logger = logging.getLogger(__name__)


class BotController(
    BotStateHandlersMixin,
    BotSignalLogicMixin,
    BotTrailingStopsMixin,
    BotHelpersMixin,
):
    """Main trading bot controller.

    Orchestrates all bot operations for a single symbol/timeframe.
    Single source of truth for bot state and decisions.

    Functionality is distributed across mixins:
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

    def __init__(
        self,
        config: FullBotConfig,
        event_bus: "EventBus | None" = None,
        on_signal: Callable[[Signal], None] | None = None,
        on_decision: Callable[[BotDecision], None] | None = None,
        on_order: Callable[[OrderIntent], None] | None = None,
        on_log: Callable[[str, str], None] | None = None,
        on_trading_blocked: Callable[[list[str]], None] | None = None,
        on_macd_signal: Callable[[str, float], None] | None = None,
        json_config_path: str | None = None,
    ):
        """Initialize bot controller.

        Args:
            config: Full bot configuration
            event_bus: Event bus for publishing events
            on_signal: Callback for new signals
            on_decision: Callback for bot decisions
            on_order: Callback for order intents
            on_log: Callback for activity logging (log_type, message)
            on_trading_blocked: Callback when trading is blocked (list of reasons)
            on_macd_signal: Callback for MACD cross signals (signal_type, price) for chart markers
            json_config_path: Optional path to JSON strategy config (enables JSON-based regime/strategy detection)
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
        self._on_trading_blocked = on_trading_blocked
        self._on_macd_signal = on_macd_signal

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
        # NOTE: Daytrading mode - no fixed daily strategy, only directional bias
        # allow_intraday_switch=True allows strategy to change with market conditions

        # Try to load JSON config if path provided
        self._json_catalog = None
        if json_config_path:
            try:
                from .config_integration_bridge import (
                    ConfigBasedStrategyCatalog,
                    load_json_config_if_available,
                )
                json_config = load_json_config_if_available(json_config_path)
                if json_config:
                    self._json_catalog = ConfigBasedStrategyCatalog(json_config)
                    logger.info(
                        f"JSON-based strategy catalog loaded from: {json_config_path}"
                    )
                else:
                    logger.warning(
                        f"JSON config path provided but failed to load: {json_config_path}. "
                        f"Falling back to hardcoded strategies."
                    )
            except Exception as e:
                logger.error(
                    f"Failed to load JSON config: {e}. "
                    f"Falling back to hardcoded strategies."
                )

        # Hardcoded catalog (fallback or primary if no JSON)
        self._strategy_catalog = StrategyCatalog()
        self._strategy_selector = StrategySelector(
            catalog=self._strategy_catalog,
            allow_intraday_switch=True,  # Daytrading: allow strategy changes
            require_regime_flip_for_switch=False  # No regime flip required
        )
        self._last_strategy_selection_date: datetime | None = None
        self._manual_strategy_mode: bool = False  # True = manual, False = auto-detection

        # Run state
        self._running: bool = False
        self._run_id: str = str(uuid4())[:8]

        # Block notification tracking (to avoid spam)
        self._trading_blocked: bool = False
        self._last_block_reasons: list[str] = []

        # Initialize state handler helpers (dispatcher, flat/manage/signal/exit)
        self.__init_state_handlers__()

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

        # Skip restrictions if disabled (paper trading mode)
        if self.config.bot.disable_restrictions:
            return True

        # Apply restrictions only if enabled
        if self._trades_today >= self.config.risk.max_trades_per_day:
            return False
        # Calculate daily PnL as percentage of account (assume $10k account)
        # Only block on LOSSES, not profits
        account_value = 10000.0
        daily_pnl_pct = (self._daily_pnl / account_value) * 100
        if daily_pnl_pct <= -self.config.risk.max_daily_loss_pct:
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
        restrictions_status = "AUS (Paper)" if self.config.bot.disable_restrictions else "AN"
        self._log_activity(
            "START",
            f"Bot gestartet: {self.symbol} | Timeframe: {self.timeframe} | "
            f"KI-Mode: {self.config.bot.ki_mode.value} | Restriktionen: {restrictions_status} | "
            f"Run-ID: {self._run_id}"
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

    def force_strategy_reselection_now(self) -> str | None:
        """Force immediate strategy re-selection.

        Unlike force_strategy_reselection(), this immediately selects a new strategy
        instead of waiting for the next bar.

        Returns:
            Name of selected strategy or None if no strategy selected
        """
        self._active_strategy = None
        self._strategy_locked_until = None

        if not self._regime:
            logger.warning("Cannot select strategy: regime not yet initialized")
            return None

        try:
            result = self._strategy_selector.select_strategy(
                regime=self._regime,
                symbol=self.symbol,
                force=True
            )

            self._last_strategy_selection_date = datetime.utcnow()

            selected_name = result.selected_strategy if result else None

            # Update active strategy profile
            if selected_name:
                strategy_def = self._strategy_catalog.get_strategy(selected_name)
                if strategy_def:
                    self._active_strategy = strategy_def.profile
                    logger.info(f"Strategy immediately re-selected: {selected_name}")
                else:
                    logger.warning(f"Strategy definition not found: {selected_name}")
            else:
                self._active_strategy = None
                logger.info("Strategy immediately re-selected: neutral (keine Strategie)")

            return selected_name

        except Exception as e:
            logger.error(f"Failed to force strategy reselection: {e}")
            return None

    @property
    def current_strategy(self) -> StrategyProfile | None:
        """Get current active strategy."""
        return self._active_strategy

    def get_strategy_selection(self):
        """Get current strategy selection result (if any)."""
        return self._strategy_selector.get_current_selection()

    def get_strategy_score_rows(self) -> list[dict]:
        """Get strategy score rows for UI display."""
        selection = self._strategy_selector.get_current_selection()
        scores = selection.strategy_scores if selection else {}
        rows: list[dict] = []
        for name, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
            info = self._strategy_selector.get_strategy_info(name)
            metrics = info.get("metrics") if info else None
            rows.append({
                "name": name,
                "score": float(score) if score is not None else 0.0,
                "profit_factor": float(metrics.get("profit_factor")) if metrics and metrics.get("profit_factor") is not None else 0.0,
                "win_rate": float(metrics.get("win_rate")) if metrics and metrics.get("win_rate") is not None else 0.0,
                "max_drawdown": float(metrics.get("max_drawdown_pct")) if metrics and metrics.get("max_drawdown_pct") is not None else 0.0,
            })
        return rows

    def get_walk_forward_config(self):
        """Get walk-forward configuration for UI display."""
        return self._strategy_selector.evaluator.walk_forward_config

    @property
    def last_regime(self) -> RegimeState:
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
