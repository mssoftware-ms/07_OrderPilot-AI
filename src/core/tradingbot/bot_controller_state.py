"""Bot Controller State Management.

Handles initialization and state management for the trading bot controller.
Extracted from bot_controller.py as part of refactoring to maintain <500 LOC per file.

This module contains:
- Initialization logic (__init__)
- State properties (state, position, regime, active_strategy, is_running, can_trade)
- State-related attributes
- State machine integration
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable
from uuid import uuid4

from .config import FullBotConfig
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


class BotControllerState:
    """State management for bot controller.

    Handles initialization, state properties, and state-related logic.
    Base class for BotController - inherited to provide state management.

    Attributes:
        config: Full bot configuration
        symbol: Trading symbol
        timeframe: Trading timeframe
        state: Current bot state (from state machine)
        position: Current position (if any)
        regime: Current market regime
        active_strategy: Active strategy profile
        is_running: Whether bot is running
        can_trade: Whether bot can enter new trades
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
        chart_window: Any | None = None,
    ):
        """Initialize bot controller state.

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
            chart_window: Optional chart window reference (enables regime visualization via trigger_regime_analysis())
        """
        self.config = config
        self.symbol = config.bot.symbol
        self.timeframe = config.bot.timeframe
        self._event_bus = event_bus
        self._chart_window = chart_window

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

        # Multi-timeframe support (optional)
        self._multi_tf_enabled: bool = False
        self._multi_tf_manager = None  # TimeframeDataManager instance
        self._multi_tf_timeframes: list[str] = []  # Configured timeframes

        # Feature/bar tracking
        self._last_features: FeatureVector | None = None
        self._bar_count: int = 0

        # Decision history
        self._decisions: list[BotDecision] = []
        self._trades_today: int = 0
        self._daily_pnl: float = 0.0
        self._consecutive_losses: int = 0

        # Live trading throttling (for trailing stop updates)
        self._last_trailing_update: dict[str, float] = {}  # symbol -> timestamp

        # Strategy selection
        # NOTE: Daytrading mode - no fixed daily strategy, only directional bias
        # allow_intraday_switch=True allows strategy to change with market conditions

        # Try to load JSON config if path provided
        self._json_catalog = None
        self._json_config_path = json_config_path  # Store for reloading
        self._config_indicators = None
        self._config_regimes = None
        self._config_strategies = None
        self._config_routing = None
        self._config_strategy_sets = None
        self._json_config = None

        if json_config_path:
            try:
                from .config_integration_bridge import (
                    ConfigBasedStrategyCatalog,
                    load_json_config_if_available,
                )
                json_config = load_json_config_if_available(json_config_path)
                if json_config:
                    # Use set_json_config to properly set all attributes
                    self.set_json_config(json_config)
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

        # CEL RulePack System (Phase 4)
        self._rule_executor = None  # RulePackExecutor instance
        self._rulepack = None        # Loaded RulePack
        self._rulepack_path = None   # Path to RulePack JSON

        # JSON Entry System (Regime-based CEL entry_expression)
        self._json_entry_config = None  # JsonEntryConfig instance
        self._json_entry_scorer = None  # JsonEntryScorer instance
        self._json_entry_mode = False   # True when using JSON Entry

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
