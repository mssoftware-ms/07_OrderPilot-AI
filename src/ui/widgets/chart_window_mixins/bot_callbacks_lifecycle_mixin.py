from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)

class BotCallbacksLifecycleMixin:
    """BotCallbacksLifecycleMixin extracted from BotCallbacksMixin."""
    def _start_bot_with_config(self) -> None:
        """Start bot with current UI configuration."""
        from src.core.tradingbot import (
            BotConfig,
            FullBotConfig,
            KIMode,
            MarketType,
            RiskConfig,
            TrailingMode,
        )

        symbol = self._resolve_bot_symbol()
        ki_mode = KIMode(self.ki_mode_combo.currentText().lower())
        trailing_mode = TrailingMode(self.trailing_mode_combo.currentText().lower())
        market_type = MarketType.CRYPTO if '/' in symbol else MarketType.NASDAQ

        config = FullBotConfig.create_default(symbol, market_type)
        self._apply_bot_ui_config(config, ki_mode, trailing_mode)

        # Create and start controller with callbacks
        from src.core.tradingbot.bot_controller import BotController

        self._bot_controller = BotController(
            config,
            on_signal=self._on_bot_signal,
            on_decision=self._on_bot_decision,
            on_order=self._on_bot_order,
            on_log=self._on_bot_log,
            on_trading_blocked=self._on_trading_blocked,
            on_macd_signal=self._on_macd_signal,
        )

        # Update bot log UI status (Issue #23)
        if hasattr(self, '_set_bot_run_status_label'):
            self._set_bot_run_status_label(True)

        # Register state change callback
        self._bot_controller._state_machine._on_transition = lambda t: (
            self._on_bot_state_change(t.from_state.value, t.to_state.value)
        )

        self._warmup_bot_from_chart()

        # Start the bot
        self._bot_controller.start()
        self._update_bot_status("RUNNING", "#26a69a")

        # Start update timer
        self._ensure_bot_update_timer()

        # Save settings for this symbol
        self._save_bot_settings(symbol)

        logger.info(f"Bot started for {symbol} with {ki_mode.value} mode")

    def _resolve_bot_symbol(self) -> str:
        symbol = getattr(self, 'current_symbol', 'AAPL')
        if hasattr(self, 'chart_widget'):
            symbol = getattr(self.chart_widget, 'current_symbol', symbol)
        return symbol

    def _apply_bot_ui_config(
        self,
        config: FullBotConfig,
        ki_mode,
        trailing_mode,
    ) -> None:
        config.bot.ki_mode = ki_mode
        config.bot.trailing_mode = trailing_mode
        # Issue #44/#48: Add hasattr checks to prevent AttributeError when widgets don't exist
        if hasattr(self, 'disable_restrictions_cb'):
            config.bot.disable_restrictions = self.disable_restrictions_cb.isChecked()
        if hasattr(self, 'disable_macd_exit_cb'):
            config.bot.disable_macd_exit = self.disable_macd_exit_cb.isChecked()
        if hasattr(self, 'disable_macd_entry_cb'):
            config.bot.disable_macd_entry = self.disable_macd_entry_cb.isChecked()
        if hasattr(self, 'disable_rsi_exit_cb'):
            config.bot.disable_rsi_exit = self.disable_rsi_exit_cb.isChecked()
        if hasattr(self, 'disable_rsi_entry_cb'):
            config.bot.disable_rsi_entry = self.disable_rsi_entry_cb.isChecked()
        if hasattr(self, 'min_score_spin'):
            config.bot.entry_score_threshold = self.min_score_spin.value() / 100.0
        if hasattr(self, 'use_pattern_cb'):
            config.bot.use_pattern_check = self.use_pattern_cb.isChecked()
        if hasattr(self, 'pattern_similarity_spin'):
            config.bot.pattern_similarity_threshold = self.pattern_similarity_spin.value()
        # Continue with remaining widget checks
        if hasattr(self, 'pattern_matches_spin'):
            config.bot.pattern_min_matches = self.pattern_matches_spin.value()
        if hasattr(self, 'pattern_winrate_spin'):
            config.bot.pattern_min_win_rate = self.pattern_winrate_spin.value() / 100.0
        if hasattr(self, 'initial_sl_spin'):
            config.risk.initial_stop_loss_pct = self.initial_sl_spin.value()
        if hasattr(self, 'risk_per_trade_spin'):
            config.risk.risk_per_trade_pct = self.risk_per_trade_spin.value()
        if hasattr(self, 'max_trades_spin'):
            config.risk.max_trades_per_day = self.max_trades_spin.value()
        if hasattr(self, 'max_daily_loss_spin'):
            config.risk.max_daily_loss_pct = self.max_daily_loss_spin.value()
        if hasattr(self, 'regime_adaptive_cb'):
            config.risk.regime_adaptive_trailing = self.regime_adaptive_cb.isChecked()
        if hasattr(self, 'atr_multiplier_spin'):
            config.risk.trailing_atr_multiple = self.atr_multiplier_spin.value()
        if hasattr(self, 'atr_trending_spin'):
            config.risk.trailing_atr_trending = self.atr_trending_spin.value()
        if hasattr(self, 'atr_ranging_spin'):
            config.risk.trailing_atr_ranging = self.atr_ranging_spin.value()
        if hasattr(self, 'volatility_bonus_spin'):
            config.risk.trailing_volatility_bonus = self.volatility_bonus_spin.value()
        if hasattr(self, 'min_step_spin'):
            config.risk.trailing_min_step_pct = self.min_step_spin.value()
        if hasattr(self, 'trailing_activation_spin'):
            config.risk.trailing_activation_pct = self.trailing_activation_spin.value()
        if hasattr(self, 'trailing_distance_spin'):
            config.risk.trailing_pct_distance = self.trailing_distance_spin.value()

    def _warmup_bot_from_chart(self) -> None:
        if not (
            hasattr(self, 'chart_widget')
            and hasattr(self.chart_widget, 'data')
            and self.chart_widget.data is not None
        ):
            return
        try:
            chart_data = self.chart_widget.data
            warmup_bars = []
            for timestamp, row in chart_data.iterrows():
                warmup_bars.append({
                    'timestamp': timestamp,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row.get('volume', 0)),
                })
            loaded = self._bot_controller.warmup_from_history(warmup_bars)
            logger.info(f"Bot warmup: {loaded} bars from chart history")
        except Exception as e:
            logger.warning(f"Could not warmup from chart data: {e}")

    def _ensure_bot_update_timer(self) -> None:
        if not self._bot_update_timer:
            self._bot_update_timer = QTimer()
            self._bot_update_timer.timeout.connect(self._update_bot_display)
        self._bot_update_timer.start(1000)

        # Issue #29: Start entry check timer (checks every 60 seconds if no position)
        self._ensure_entry_check_timer()

    def _ensure_entry_check_timer(self) -> None:
        """Ensure entry check timer is running (Issue #29).

        Checks every 60 seconds if an entry opportunity exists when no position is open.
        """
        if not hasattr(self, '_entry_check_timer') or self._entry_check_timer is None:
            self._entry_check_timer = QTimer()
            self._entry_check_timer.timeout.connect(self._check_entry_opportunity)
        self._entry_check_timer.start(60000)  # 60 seconds
        logger.info("Entry check timer started (60s interval)")

    def _check_entry_opportunity(self) -> None:
        """Check if an entry opportunity exists (Issue #29).

        Called every 60 seconds by timer when bot is running without open position.
        """
        if not self._bot_controller or not self._bot_controller.is_running:
            return

        # Only check if no position is open
        if self._bot_controller.position is not None:
            return

        # Get current bar from chart
        if not hasattr(self, 'chart_widget') or not hasattr(self.chart_widget, 'data'):
            return

        try:
            chart_data = self.chart_widget.data
            if chart_data is None or len(chart_data) == 0:
                return

            # Get latest bar
            last_row = chart_data.iloc[-1]
            last_timestamp = chart_data.index[-1]

            bar = {
                'timestamp': last_timestamp,
                'open': float(last_row['open']),
                'high': float(last_row['high']),
                'low': float(last_row['low']),
                'close': float(last_row['close']),
                'volume': float(last_row.get('volume', 0)),
            }

            # Process bar for entry check
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create task if loop is already running
                asyncio.create_task(self._bot_controller.on_bar(bar))
            else:
                # Run synchronously if no loop
                loop.run_until_complete(self._bot_controller.on_bar(bar))

            logger.debug(f"Entry check executed at {last_timestamp}")
        except Exception as e:
            logger.error(f"Entry check failed: {e}")

    def _stop_bot(self) -> None:
        """Stop the running bot."""
        if self._bot_controller:
            self._bot_controller.stop()
            self._bot_controller = None

        if self._bot_update_timer:
            self._bot_update_timer.stop()

        # Issue #29: Stop entry check timer
        if hasattr(self, '_entry_check_timer') and self._entry_check_timer:
            self._entry_check_timer.stop()
            logger.info("Entry check timer stopped")

        # Update bot log UI status (Issue #23)
        if hasattr(self, '_set_bot_run_status_label'):
            self._set_bot_run_status_label(False)

        logger.info("Bot stopped")

    def _start_bot_with_json_config(self, config_path: str, matched_strategy_set: any) -> None:
        """Start bot with JSON config and matched strategy set.

        Args:
            config_path: Path to JSON config file
            matched_strategy_set: Matched strategy set from routing
        """
        from src.core.tradingbot import (
            BotConfig,
            FullBotConfig,
            KIMode,
            MarketType,
            RiskConfig,
            TrailingMode,
        )
        from src.core.tradingbot.config.loader import ConfigLoader

        symbol = self._resolve_bot_symbol()
        ki_mode = KIMode(self.ki_mode_combo.currentText().lower())
        trailing_mode = TrailingMode(self.trailing_mode_combo.currentText().lower())
        market_type = MarketType.CRYPTO if '/' in symbol else MarketType.NASDAQ

        # Load JSON config
        loader = ConfigLoader()
        json_config = loader.load_config(config_path)

        # Create base config
        config = FullBotConfig.create_default(symbol, market_type)
        self._apply_bot_ui_config(config, ki_mode, trailing_mode)

        # Create and start controller with callbacks + JSON config
        from src.core.tradingbot.bot_controller import BotController

        self._bot_controller = BotController(
            config,
            on_signal=self._on_bot_signal,
            on_decision=self._on_bot_decision,
            on_order=self._on_bot_order,
            on_log=self._on_bot_log,
            on_trading_blocked=self._on_trading_blocked,
            on_macd_signal=self._on_macd_signal,
        )

        # Set JSON config on bot controller
        if hasattr(self._bot_controller, 'set_json_config'):
            self._bot_controller.set_json_config(json_config)
            logger.info(f"JSON config loaded: {config_path}")

        # Set initial strategy from matched set
        if hasattr(self._bot_controller, 'set_initial_strategy'):
            self._bot_controller.set_initial_strategy(matched_strategy_set)
            logger.info(f"Initial strategy set: {matched_strategy_set.strategy_set.id if hasattr(matched_strategy_set.strategy_set, 'id') else 'unknown'}")

        # Update bot log UI status (Issue #23)
        if hasattr(self, '_set_bot_run_status_label'):
            self._set_bot_run_status_label(True)

        # Register state change callback
        self._bot_controller._state_machine._on_transition = lambda t: (
            self._on_bot_state_change(t.from_state.value, t.to_state.value)
        )

        self._warmup_bot_from_chart()

        # Start the bot
        self._bot_controller.start()
        self._update_bot_status("RUNNING", "#26a69a")

        # Start update timer
        self._ensure_bot_update_timer()

        # Save settings for this symbol
        self._save_bot_settings(symbol)

        logger.info(f"Bot started with JSON strategy for {symbol} ({ki_mode.value} mode)")

    def _start_bot_with_json_entry(self, json_entry_config) -> None:
        """Start bot with JSON Entry config (Regime-based CEL entry_expression).
        
        Flow:
        1. Normaler Bot-Start (wie _start_bot_with_json_config)
        2. ABER: JsonEntryScorer statt normalem Entry System
        3. Nach jeder Candle:
           - Regime-Analyse triggern (via Entry Analyzer)
           - CEL Expression evaluieren
           - Bei Entry-Signal: _on_bot_signal aufrufen (ab hier normale Logik)
        
        Args:
            json_entry_config: JsonEntryConfig mit entry_expression
        """
        from src.core.tradingbot import (
            BotConfig,
            FullBotConfig,
            KIMode,
            MarketType,
            RiskConfig,
            TrailingMode,
        )
        
        logger.info(f"Starting bot with JSON Entry mode...")
        logger.info(f"Regime JSON: {json_entry_config.regime_json_path}")
        logger.info(f"Entry expression: {json_entry_config.entry_expression[:100]}...")
        
        symbol = self._resolve_bot_symbol()
        ki_mode = KIMode(self.ki_mode_combo.currentText().lower())
        trailing_mode = TrailingMode(self.trailing_mode_combo.currentText().lower())
        market_type = MarketType.CRYPTO if '/' in symbol else MarketType.NASDAQ
        
        # Create base config
        config = FullBotConfig.create_default(symbol, market_type)
        self._apply_bot_ui_config(config, ki_mode, trailing_mode)
        
        # Create bot controller mit JSON Entry mode
        from src.core.tradingbot.bot_controller import BotController
        
        self._bot_controller = BotController(
            config,
            on_signal=self._on_bot_signal,
            on_decision=self._on_bot_decision,
            on_order=self._on_bot_order,
            on_log=self._on_bot_log,
            on_trading_blocked=self._on_trading_blocked,
            on_macd_signal=self._on_macd_signal,
        )
        
        # Set JSON Entry config
        if hasattr(self._bot_controller, 'set_json_entry_config'):
            self._bot_controller.set_json_entry_config(json_entry_config)
            logger.info(f"JSON Entry config loaded")
        else:
            logger.warning("BotController.set_json_entry_config not available - manual setup needed")
            # Store config for manual processing
            self._bot_controller._json_entry_config = json_entry_config
        
        # Update bot log UI status
        if hasattr(self, '_set_bot_run_status_label'):
            self._set_bot_run_status_label(True)
        
        # Register state change callback
        self._bot_controller._state_machine._on_transition = lambda t: (
            self._on_bot_state_change(t.from_state.value, t.to_state.value)
        )
        
        # Warmup from chart
        self._warmup_bot_from_chart()
        
        # Start the bot
        self._bot_controller.start()
        self._update_bot_status("RUNNING (JSON Entry)", "#2196F3")
        
        # Start update timer (evaluiert nach jeder Candle)
        self._ensure_bot_update_timer()
        
        # Save settings
        self._save_bot_settings(symbol)
        
        logger.info(f"Bot started with JSON Entry for {symbol}")
        logger.info(f"  Regimes: {len(json_entry_config.regime_thresholds)}")
        logger.info(f"  Indicators: {len(json_entry_config.indicators)}")
        logger.info(f"  Mode: {ki_mode.value}")
        
        self._add_ki_log_entry(
            "BOT", 
            f"Bot gestartet (JSON Entry Mode)\n"
            f"  JSON: {Path(json_entry_config.regime_json_path).name}\n"
            f"  Regimes: {len(json_entry_config.regime_thresholds)}\n"
            f"  Expression: {json_entry_config.entry_expression[:80]}..."
        )
