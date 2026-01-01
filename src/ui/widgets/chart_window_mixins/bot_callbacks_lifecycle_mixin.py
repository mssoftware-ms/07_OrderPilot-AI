from __future__ import annotations

import logging

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
        config.bot.disable_restrictions = self.disable_restrictions_cb.isChecked()
        config.bot.disable_macd_exit = self.disable_macd_exit_cb.isChecked()
        config.bot.entry_score_threshold = self.min_score_spin.value() / 100.0
        config.bot.use_pattern_check = self.use_pattern_cb.isChecked()
        config.bot.pattern_similarity_threshold = self.pattern_similarity_spin.value()
        config.bot.pattern_min_matches = self.pattern_matches_spin.value()
        config.bot.pattern_min_win_rate = self.pattern_winrate_spin.value() / 100.0
        config.risk.initial_stop_loss_pct = self.initial_sl_spin.value()
        config.risk.risk_per_trade_pct = self.risk_per_trade_spin.value()
        config.risk.max_trades_per_day = self.max_trades_spin.value()
        config.risk.max_daily_loss_pct = self.max_daily_loss_spin.value()
        config.risk.regime_adaptive_trailing = self.regime_adaptive_cb.isChecked()
        config.risk.trailing_atr_multiple = self.atr_multiplier_spin.value()
        config.risk.trailing_atr_trending = self.atr_trending_spin.value()
        config.risk.trailing_atr_ranging = self.atr_ranging_spin.value()
        config.risk.trailing_volatility_bonus = self.volatility_bonus_spin.value()
        config.risk.trailing_min_step_pct = self.min_step_spin.value()
        config.risk.trailing_activation_pct = self.trailing_activation_spin.value()
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
    def _stop_bot(self) -> None:
        """Stop the running bot."""
        if self._bot_controller:
            self._bot_controller.stop()
            self._bot_controller = None

        if self._bot_update_timer:
            self._bot_update_timer.stop()

        logger.info("Bot stopped")
