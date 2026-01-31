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
from pathlib import Path
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
        chart_window: Any | None = None,
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

    # ==================== JSON Config Reloading ====================

    def reload_json_config(self) -> bool:
        """Reload JSON configuration (if JSON catalog active).

        Thread-safe reload of JSON strategy configuration without
        restarting the bot. Uses existing config path.

        Returns:
            True if reload successful, False if failed or not using JSON config

        Example:
            >>> controller.reload_json_config()
            True
        """
        if self._json_catalog is None:
            logger.warning("Cannot reload: not using JSON config")
            return False

        if self._json_config_path is None:
            logger.error("Cannot reload: JSON config path not stored")
            return False

        try:
            logger.info(f"Reloading JSON config from {self._json_config_path}")

            # Use catalog's reload method
            self._json_catalog.reload_config()

            logger.info("JSON config reloaded successfully")
            self._log_activity("CONFIG", f"JSON-Konfiguration neu geladen")
            return True

        except Exception as e:
            logger.error(f"Failed to reload JSON config: {e}", exc_info=True)
            self._log_activity("ERROR", f"Config-Reload fehlgeschlagen: {e}")
            return False

    # ==================== Multi-Timeframe Support ====================

    def enable_multi_timeframe(
        self,
        timeframes: list[str],
        auto_resample: bool = True
    ) -> None:
        """Enable multi-timeframe analysis.

        Enables calculation of indicators across multiple timeframes
        for improved regime detection and signal confirmation.

        Args:
            timeframes: List of timeframes (e.g., ["1T", "5T", "1H"])
                       Base timeframe (bot's primary TF) is auto-included
            auto_resample: Automatically resample higher TFs from base

        Example:
            >>> controller.enable_multi_timeframe(["5T", "15T", "1H"])
            >>> # Now indicators calculated on 1T, 5T, 15T, 1H
        """
        try:
            from .timeframe_data_manager import TimeframeDataManager

            # Ensure base timeframe is included
            all_tfs = list(set([self.timeframe] + timeframes))

            self._multi_tf_manager = TimeframeDataManager(
                base_timeframe=self.timeframe,
                auto_resample=auto_resample
            )

            # Register all timeframes
            for tf in all_tfs:
                self._multi_tf_manager.add_timeframe(tf)

            self._multi_tf_timeframes = all_tfs
            self._multi_tf_enabled = True

            logger.info(f"Multi-timeframe enabled: {all_tfs}")
            self._log_activity("CONFIG", f"Multi-Timeframe aktiviert: {', '.join(all_tfs)}")

        except Exception as e:
            logger.error(f"Failed to enable multi-timeframe: {e}")
            self._multi_tf_enabled = False

    def disable_multi_timeframe(self) -> None:
        """Disable multi-timeframe analysis."""
        self._multi_tf_enabled = False
        self._multi_tf_manager = None
        self._multi_tf_timeframes = []
        logger.info("Multi-timeframe disabled")

    def get_multi_timeframe_data(
        self,
        timeframe: str | None = None,
        n: int = 100
    ) -> dict[str, Any] | None:
        """Get multi-timeframe data.

        Args:
            timeframe: Specific timeframe (None = all aligned data)
            n: Number of bars to retrieve

        Returns:
            DataFrame or dict of DataFrames (None if not enabled)
        """
        if not self._multi_tf_enabled or self._multi_tf_manager is None:
            return None

        if timeframe:
            return self._multi_tf_manager.get_bars(
                timeframe=timeframe,
                n=n,
                as_dataframe=True
            )
        else:
            return self._multi_tf_manager.get_aligned_data(n=n)

    def _calculate_multi_timeframe_features(
        self,
        bar_data: dict[str, Any]
    ) -> dict[str, FeatureVector]:
        """Calculate features across all configured timeframes.

        Args:
            bar_data: Base timeframe bar

        Returns:
            Dict mapping timeframe to FeatureVector
        """
        if not self._multi_tf_enabled or self._multi_tf_manager is None:
            return {self.timeframe: self._calculate_features(bar_data)}

        # Add bar to multi-TF manager (auto-resamples higher TFs)
        self._multi_tf_manager.add_bar(self.timeframe, bar_data)

        # Get aligned data across all timeframes
        aligned_data = self._multi_tf_manager.get_aligned_data(n=200)

        # Calculate features for each timeframe
        features_multi = {}

        for tf in self._multi_tf_timeframes:
            if tf not in aligned_data or aligned_data[tf].empty:
                continue

            df = aligned_data[tf]

            # Need at least MIN_BARS for reliable indicators
            if len(df) < self._feature_engine.MIN_BARS:
                continue

            # Convert last row to bar format
            last_bar = {
                "timestamp": df.index[-1],
                "open": df["open"].iloc[-1],
                "high": df["high"].iloc[-1],
                "low": df["low"].iloc[-1],
                "close": df["close"].iloc[-1],
                "volume": df["volume"].iloc[-1],
            }

            # Calculate features for this timeframe
            # Note: FeatureEngine.process_bar() requires full bar buffer
            # For now, use basic feature calculation
            features_multi[tf] = self._calculate_features(last_bar)

        return features_multi

    def enable_json_config_auto_reload(self) -> bool:
        """Enable automatic JSON config reloading with file watching.

        Monitors config file for changes and reloads automatically.
        Only works if JSON catalog is active.

        Returns:
            True if auto-reload enabled, False if failed or not using JSON config

        Example:
            >>> controller.enable_json_config_auto_reload()
            True
        """
        if self._json_catalog is None:
            logger.warning("Cannot enable auto-reload: not using JSON config")
            return False

        if self._json_config_path is None:
            logger.error("Cannot enable auto-reload: JSON config path not stored")
            return False

        try:
            logger.info(f"Enabling auto-reload for {self._json_config_path}")

            # Enable auto-reload on catalog
            self._json_catalog.enable_auto_reload(
                config_path=self._json_config_path,
                event_bus=self._event_bus
            )

            logger.info("JSON config auto-reload enabled")
            self._log_activity("CONFIG", "Auto-Reload aktiviert")
            return True

        except Exception as e:
            logger.error(f"Failed to enable auto-reload: {e}", exc_info=True)
            self._log_activity("ERROR", f"Auto-Reload Aktivierung fehlgeschlagen: {e}")
            return False

    def disable_json_config_auto_reload(self) -> bool:
        """Disable automatic JSON config reloading.

        Returns:
            True if auto-reload disabled, False if failed or not active
        """
        if self._json_catalog is None:
            logger.warning("Cannot disable auto-reload: not using JSON config")
            return False

        try:
            self._json_catalog.disable_auto_reload()
            logger.info("JSON config auto-reload disabled")
            self._log_activity("CONFIG", "Auto-Reload deaktiviert")
            return True

        except Exception as e:
            logger.error(f"Failed to disable auto-reload: {e}", exc_info=True)
            return False

    def is_json_config_auto_reload_enabled(self) -> bool:
        """Check if JSON config auto-reload is enabled.

        Returns:
            True if auto-reload active, False otherwise
        """
        if self._json_catalog is None or self._json_catalog.config_reloader is None:
            return False

        return self._json_catalog.config_reloader.is_watching()

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

    # ==================== JSON-Based Strategy Configuration ====================

    def set_json_config(self, json_config: Any) -> None:
        """Set JSON config for regime-based strategy routing.

        Args:
            json_config: TradingBotConfig instance from ConfigLoader

        Note:
            This method enables dynamic JSON-based strategy selection.
            Call after controller initialization or when changing strategies.
        """
        from src.core.tradingbot.config_integration_bridge import ConfigBasedStrategyCatalog

        try:
            # Store raw config
            self._json_config = json_config

            # Create/update JSON catalog
            self._json_catalog = ConfigBasedStrategyCatalog(json_config)

            # Extract config components for regime detection and routing
            self._config_indicators = json_config.indicators
            self._config_regimes = json_config.regimes
            self._config_strategies = json_config.strategies
            self._config_routing = json_config.routing
            self._config_strategy_sets = json_config.strategy_sets

            logger.info(
                f"JSON config set: {len(json_config.regimes)} regimes, "
                f"{len(json_config.strategies)} strategies, "
                f"{len(json_config.routing)} routing rules"
            )
            self._log_activity(
                "CONFIG",
                f"JSON-Konfiguration geladen: {len(json_config.regimes)} Regimes, "
                f"{len(json_config.strategies)} Strategien"
            )

        except Exception as e:
            logger.error(f"Failed to set JSON config: {e}", exc_info=True)
            self._log_activity("ERROR", f"JSON-Config Fehler: {e}")
            raise

    def set_initial_strategy(self, matched_strategy_set: Any) -> None:
        """Set initial strategy from matched strategy set.

        Args:
            matched_strategy_set: MatchedStrategySet from StrategyRouter

        Note:
            This sets the starting strategy based on current market regime.
            The strategy may change during runtime if regime changes significantly.
        """
        try:
            # Store matched strategy set
            self._matched_strategy_set = matched_strategy_set

            # Extract strategy information
            strategy_set = matched_strategy_set.strategy_set
            active_regimes = matched_strategy_set.active_regimes

            # Log initial strategy
            strategy_names = ", ".join([s.strategy_id for s in strategy_set.strategies])
            regime_names = ", ".join([r.name for r in active_regimes])

            logger.info(
                f"Initial strategy set: {strategy_set.name} | "
                f"Strategies: {strategy_names} | "
                f"Active regimes: {regime_names}"
            )
            self._log_activity(
                "STRATEGY",
                f"Startstrategie: {strategy_set.name} ({regime_names})"
            )

        except Exception as e:
            logger.error(f"Failed to set initial strategy: {e}", exc_info=True)
            self._log_activity("ERROR", f"Strategie-Set Fehler: {e}")
            raise

    # ==================== CEL RulePack Integration (Phase 4) ====================

    def set_json_entry_config(self, json_entry_config) -> None:
        """Set JSON Entry config (Regime-based CEL entry_expression).

        Enables JSON Entry Mode where entry signals are generated by evaluating
        CEL entry_expression from Regime JSON instead of using scoring logic.

        Args:
            json_entry_config: JsonEntryConfig instance with entry_expression

        Example:
            from src.core.tradingbot.json_entry_loader import JsonEntryConfig
            config = JsonEntryConfig.from_files("regime.json")
            bot.set_json_entry_config(config)
        """
        try:
            from .cel_engine import CELEngine
            from .json_entry_scorer import JsonEntryScorer

            # Store config
            self._json_entry_config = json_entry_config
            self._json_entry_mode = True

            # Initialize CEL Engine
            cel_engine = CELEngine()

            # Initialize JsonEntryScorer
            self._json_entry_scorer = JsonEntryScorer(
                json_config=json_entry_config,
                cel_engine=cel_engine
            )

            logger.info(
                f"✅ JSON Entry Mode aktiviert | "
                f"JSON: {Path(json_entry_config.regime_json_path).name} | "
                f"Regimes: {len(json_entry_config.regime_thresholds)} | "
                f"Expression: {json_entry_config.entry_expression[:80]}..."
            )

            self._log_activity(
                "CONFIG",
                f"JSON Entry Mode aktiv | {len(json_entry_config.regime_thresholds)} Regimes"
            )

        except Exception as e:
            logger.error(f"Failed to set JSON Entry config: {e}", exc_info=True)
            self._log_activity("ERROR", f"JSON Entry Config Fehler: {e}")
            # Disable JSON Entry Mode on error
            self._json_entry_mode = False
            self._json_entry_config = None
            self._json_entry_scorer = None
            raise

    def load_rulepack(self, rulepack_path: str) -> bool:
        """Load CEL RulePack from JSON file.

        Args:
            rulepack_path: Path to RulePack JSON file

        Returns:
            True if loaded successfully, False otherwise

        Example:
            bot.load_rulepack("03_JSON/RulePacks/default_rules.json")
        """
        try:
            from .cel import RulePackExecutor
            from .cel.loader import RulePackLoader

            # Load RulePack
            loader = RulePackLoader()
            self._rulepack = loader.load(rulepack_path)
            self._rulepack_path = rulepack_path

            # Initialize executor if not exists
            if self._rule_executor is None:
                self._rule_executor = RulePackExecutor()

            logger.info(
                f"✅ RulePack loaded: {rulepack_path} | "
                f"Version: {self._rulepack.rules_version} | "
                f"Packs: {len(self._rulepack.packs)}"
            )

            self._log_activity(
                "RULES",
                f"RulePack geladen: {len(self._rulepack.packs)} Packs, "
                f"{sum(len(p.rules) for p in self._rulepack.packs)} Rules"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to load RulePack: {e}")
            self._log_activity("ERROR", f"RulePack laden fehlgeschlagen: {e}")
            return False

    def _evaluate_rules(
        self,
        features: FeatureVector,
        pack_types: list[str],
        context_override: dict[str, Any] | None = None
    ) -> tuple[bool, str, Any]:
        """Evaluate CEL RulePack for given pack types.

        Args:
            features: Current feature vector
            pack_types: Pack types to evaluate (e.g., ["risk", "entry"])
            context_override: Optional context overrides

        Returns:
            Tuple of (allowed, reason, summary)
            - allowed: True if decision is ALLOW
            - reason: Block/Exit reason if not allowed
            - summary: Full ExecutionSummary

        Example:
            allowed, reason, summary = bot._evaluate_rules(
                features, ["risk", "entry"]
            )
            if not allowed:
                logger.warning(f"Blocked: {reason}")
        """
        from .cel import RuleContextBuilder, ExecutionResult

        # Check if RulePack is loaded
        if self._rulepack is None or self._rule_executor is None:
            # No rules loaded - allow by default
            return True, "", None

        # Build CEL context
        context = RuleContextBuilder.build(
            features=features,
            trade=self._position,
            config={
                "capital": 10000.0,  # TODO: Get from account
                "max_position_size": self.config.risk.position_size_pct,
                "max_risk_per_trade": self.config.risk.stop_loss_pct,
            },
            timeframe=self.timeframe,
            additional_context=context_override or {}
        )

        # Execute RulePack
        summary = self._rule_executor.execute(
            self._rulepack,
            context,
            pack_types=pack_types
        )

        # Interpret result
        if summary.final_decision == ExecutionResult.ALLOW:
            return True, "", summary

        elif summary.final_decision == ExecutionResult.BLOCK:
            reason = f"Blocked by {summary.blocked_by_pack}/{summary.blocked_by_rule}"
            return False, reason, summary

        elif summary.final_decision == ExecutionResult.EXIT:
            reason = "Exit signal from RulePack"
            return False, reason, summary

        elif summary.final_decision == ExecutionResult.UPDATE_STOP:
            # Not a block, but a signal
            return True, "STOP_UPDATE", summary

        elif summary.final_decision == ExecutionResult.WARN:
            # Warning - allow but log
            logger.warning(f"RulePack warning: {summary}")
            return True, "WARNING", summary

        return True, "", summary

    def get_rule_stats(self) -> dict[str, Any]:
        """Get rule profiling statistics.

        Returns:
            Rule statistics dict or empty dict if no executor

        Example:
            stats = bot.get_rule_stats()
            for rule_id, data in stats.items():
                print(f"{rule_id}: {data['triggers']}/{data['evaluations']}")
        """
        if self._rule_executor is None:
            return {}
        return self._rule_executor.get_rule_stats()

    def get_most_triggered_rules(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Get most frequently triggered rules.

        Args:
            top_n: Number of top rules to return

        Returns:
            List of (rule_id, trigger_count) tuples
        """
        if self._rule_executor is None:
            return []
        return self._rule_executor.get_most_triggered_rules(top_n)

    def clear_rule_stats(self) -> None:
        """Clear rule profiling statistics."""
        if self._rule_executor:
            self._rule_executor.clear_stats()
            logger.info("Rule statistics cleared")

    def _check_regime_change_and_switch(self, features: FeatureVector) -> bool:
        """Check if regime has changed and switch strategy if needed.

        Args:
            features: Current feature vector

        Returns:
            True if strategy was switched, False otherwise

        Note:
            Only active when JSON config is loaded. Monitors regime changes
            and automatically switches to appropriate strategy set.
        """
        # Only check if JSON config is active
        if not hasattr(self, '_json_config') or self._json_config is None:
            return False

        try:
            from src.core.tradingbot.config.detector import RegimeDetector
            from src.core.tradingbot.config.router import StrategyRouter
            from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

            # Calculate indicator values from features (classmethod)
            indicator_values = IndicatorValueCalculator.calculate_indicator_values(features)

            # Detect current active regimes
            detector = RegimeDetector(self._config_regimes)
            current_active_regimes = detector.detect_active_regimes(
                indicator_values,
                scope='entry'
            )

            # Get current regime IDs
            current_regime_ids = [r.id for r in current_active_regimes]

            # Check if regimes have changed
            if hasattr(self, '_last_active_regime_ids'):
                if current_regime_ids == self._last_active_regime_ids:
                    return False  # No change

            # Store current regime IDs
            self._last_active_regime_ids = current_regime_ids

            # Route to new strategy set
            router = StrategyRouter(self._config_routing, self._config_strategy_sets)
            matched_sets = router.route_regimes(current_active_regimes)

            if matched_sets:
                # Use first matched set (highest priority)
                matched_set = matched_sets[0]

                # Check if strategy set has actually changed
                if hasattr(self, '_matched_strategy_set') and self._matched_strategy_set:
                    if matched_set.strategy_set.id == self._matched_strategy_set.strategy_set.id:
                        return False  # Same strategy set

                # Switch to new strategy
                self._switch_strategy(matched_set, current_active_regimes)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check regime change: {e}", exc_info=True)
            return False

    def _switch_strategy(
        self,
        matched_strategy_set: Any,
        active_regimes: list
    ) -> None:
        """Switch to new strategy based on regime change.

        Args:
            matched_strategy_set: New MatchedStrategySet to switch to
            active_regimes: List of active RegimeDefinitions

        Note:
            Applies parameter overrides and updates internal strategy tracking.
            Emits strategy change event for UI notifications.
        """
        try:
            # Store old strategy for logging
            old_strategy_name = None
            if hasattr(self, '_matched_strategy_set'):
                old_strategy_name = self._matched_strategy_set.strategy_set.name

            # Update matched strategy set
            self._matched_strategy_set = matched_strategy_set

            # Extract strategy information
            strategy_set = matched_strategy_set.strategy_set
            strategy_names = ", ".join([s.strategy_id for s in strategy_set.strategies])
            regime_names = ", ".join([r.name for r in active_regimes])

            # Log strategy switch
            switch_msg = (
                f"Strategie gewechselt: {old_strategy_name or 'Keine'} → {strategy_set.name} | "
                f"Regimes: {regime_names}"
            )
            logger.info(f"Strategy switch: {old_strategy_name} -> {strategy_set.name}")
            self._log_activity("STRATEGY_SWITCH", switch_msg)

            # Emit event for UI notification (if event bus available)
            if self._event_bus:
                try:
                    self._event_bus.emit('regime_changed', {
                        'old_strategy': old_strategy_name,
                        'new_strategy': strategy_set.name,
                        'new_regimes': regime_names,
                        'timestamp': datetime.utcnow()
                    })
                except Exception as e:
                    logger.warning(f"Failed to emit regime change event: {e}")

            # Apply parameter overrides from strategy set
            try:
                from src.core.tradingbot.config.executor import StrategySetExecutor

                executor = StrategySetExecutor(
                    self._config_indicators,
                    self._config_strategies
                )

                # Apply overrides (creates modified copies)
                override_context = executor.prepare_execution(matched_strategy_set)

                # Copy modified indicators/strategies back to controller
                # (executor creates deep copies and modifies those, we need to update our references)
                self._config_indicators = list(executor.current_indicators.values())
                self._config_strategies = list(executor.current_strategies.values())

                # Log applied overrides
                if override_context:
                    num_indicator_overrides = len(override_context.applied_overrides.get('indicator_overrides', {}))
                    num_strategy_overrides = len(override_context.applied_overrides.get('strategy_overrides', {}))

                    if num_indicator_overrides > 0 or num_strategy_overrides > 0:
                        override_msg = (
                            f"Parameter-Overrides angewendet: "
                            f"{num_indicator_overrides} Indikatoren, "
                            f"{num_strategy_overrides} Strategien"
                        )
                        logger.info(override_msg)
                        self._log_activity("OVERRIDE", override_msg)

                # Note: We do NOT call restore_state() because we want the overrides
                # to remain active until the next regime change

            except Exception as e:
                logger.warning(f"Failed to apply parameter overrides: {e}")
                self._log_activity("WARNING", f"Parameter-Override Fehler: {e}")

            # Adjust open positions for new regime (if position exists)
            self._adjust_positions_for_new_regime()

        except Exception as e:
            logger.error(f"Failed to switch strategy: {e}", exc_info=True)
            self._log_activity("ERROR", f"Strategie-Wechsel Fehler: {e}")

    def _adjust_positions_for_new_regime(self) -> None:
        """Adjust open positions when regime changes.

        Implements risk management based on regime transitions:
        - High volatility → Tighter stops, reduce exposure
        - Low volatility → Loosen stops, normal exposure
        - Trend reversal → Partial or full exit

        Note:
            Called automatically by _switch_strategy() after regime change.
            Only takes action if position is open.
        """
        # Guard: Only adjust if position exists
        if not self._position:
            return

        # Guard: Only adjust if regime is available
        if not self._regime:
            logger.debug("No regime available for position adjustment")
            return

        try:
            from .models import VolatilityLevel, RegimeType, TradeSide

            current_volatility = self._regime.volatility
            current_regime_type = self._regime.regime
            position_side = self._position.side  # TradeSide enum

            adjustments = []

            # ========== Volatility-Based Adjustments ==========

            # HIGH/EXTREME Volatility → Tighten stops, reduce risk
            if current_volatility in [VolatilityLevel.HIGH, VolatilityLevel.EXTREME]:
                # Calculate tighter stop (reduce from current stop distance)
                current_price = self._position.current_price
                current_stop = self._position.trailing.current_stop_price

                if current_stop and current_price:
                    # Tighten stop by 30% (move closer to current price)
                    stop_distance = abs(current_price - current_stop)
                    new_stop_distance = stop_distance * 0.7  # 30% tighter

                    if position_side == TradeSide.LONG:
                        new_stop = current_price - new_stop_distance
                        if new_stop > current_stop:  # Only tighten, never loosen
                            self._position.trailing.current_stop_price = new_stop
                            adjustments.append(
                                f"Stop-Loss verschärft: {current_stop:.2f} → {new_stop:.2f} "
                                f"(Hohe Volatilität)"
                            )
                    else:  # SHORT
                        new_stop = current_price + new_stop_distance
                        if new_stop < current_stop:  # Only tighten, never loosen
                            self._position.trailing.current_stop_price = new_stop
                            adjustments.append(
                                f"Stop-Loss verschärft: {current_stop:.2f} → {new_stop:.2f} "
                                f"(Hohe Volatilität)"
                            )

            # LOW Volatility → Loosen stops, allow normal movement
            elif current_volatility == VolatilityLevel.LOW:
                # In low volatility, we can afford slightly wider stops
                # to avoid being stopped out by normal noise
                current_price = self._position.current_price
                current_stop = self._position.trailing.current_stop_price

                if current_stop and current_price:
                    # Loosen stop by 20% (move away from current price)
                    stop_distance = abs(current_price - current_stop)
                    new_stop_distance = stop_distance * 1.2  # 20% wider

                    if position_side == TradeSide.LONG:
                        new_stop = current_price - new_stop_distance
                        self._position.trailing.current_stop_price = new_stop
                        adjustments.append(
                            f"Stop-Loss gelockert: {current_stop:.2f} → {new_stop:.2f} "
                            f"(Niedrige Volatilität)"
                        )
                    else:  # SHORT
                        new_stop = current_price + new_stop_distance
                        self._position.trailing.current_stop_price = new_stop
                        adjustments.append(
                            f"Stop-Loss gelockert: {current_stop:.2f} → {new_stop:.2f} "
                            f"(Niedrige Volatilität)"
                        )

            # ========== Trend-Based Adjustments ==========

            # Trend reversal against position → Consider partial exit
            if position_side == TradeSide.LONG and current_regime_type == RegimeType.TREND_DOWN:
                # LONG position in downtrend → High risk
                adjustments.append(
                    "⚠ WARNUNG: LONG-Position in Abwärtstrend - "
                    "Erwäge teilweisen Ausstieg (nicht auto-implementiert)"
                )
                # TODO: Implement partial exit logic
                # partial_exit_size = self._position.quantity * 0.5
                # self._create_exit_order(partial_exit_size, reason="regime_reversal")

            elif position_side == TradeSide.SHORT and current_regime_type == RegimeType.TREND_UP:
                # SHORT position in uptrend → High risk
                adjustments.append(
                    "⚠ WARNUNG: SHORT-Position in Aufwärtstrend - "
                    "Erwäge teilweisen Ausstieg (nicht auto-implementiert)"
                )
                # TODO: Implement partial exit logic
                # partial_exit_size = self._position.quantity * 0.5
                # self._create_exit_order(partial_exit_size, reason="regime_reversal")

            # ========== Logging ==========

            if adjustments:
                adjustment_msg = " | ".join(adjustments)
                logger.info(f"Position adjustments: {adjustment_msg}")
                self._log_activity("POSITION_ADJUST", adjustment_msg)
            else:
                logger.debug(
                    f"No position adjustments needed for {current_regime_type.name} "
                    f"regime with {current_volatility.name} volatility"
                )

        except Exception as e:
            logger.error(f"Failed to adjust positions for regime: {e}", exc_info=True)
            self._log_activity("ERROR", f"Position-Adjustment Fehler: {e}")

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
