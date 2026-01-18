"""Bot Event Handlers - UI event handlers and settings management.

Contains methods for handling UI events and managing bot settings:
- Button click handlers (start, stop, pause)
- Mode change handlers (KI mode, trailing mode)
- Settings persistence
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from src.core.tradingbot import BotController

logger = logging.getLogger(__name__)


class BotEventHandlersMixin:
    """Mixin providing bot event handlers and settings management."""

    # ==================== BUTTON EVENT HANDLERS ====================

    def _on_bot_start_clicked(self) -> None:
        """Handle bot start button click."""
        logger.info("Bot start requested")
        self._update_bot_status("STARTING", "#ffeb3b")

        try:
            self._start_bot_with_config()
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self._update_bot_status("ERROR", "#f44336")
            # Issue #9: Update Trading tab button on error
            if hasattr(self, '_update_signals_tab_bot_button'):
                self._update_signals_tab_bot_button(running=False)
            return

        self.bot_start_btn.setEnabled(False)
        self.bot_stop_btn.setEnabled(True)
        self.bot_pause_btn.setEnabled(True)

        # Issue #9: Update Trading tab button to show running state (green)
        if hasattr(self, '_update_signals_tab_bot_button'):
            self._update_signals_tab_bot_button(running=True)

    def _on_bot_stop_clicked(self) -> None:
        """Handle bot stop button click."""
        logger.info("Bot stop requested")
        self._stop_bot()

        self._update_bot_status("STOPPED", "#9e9e9e")
        self.bot_start_btn.setEnabled(True)
        self.bot_stop_btn.setEnabled(False)
        self.bot_pause_btn.setEnabled(False)

        # Issue #9: Update Trading tab button to show stopped state (red)
        if hasattr(self, '_update_signals_tab_bot_button'):
            self._update_signals_tab_bot_button(running=False)

    def _on_bot_pause_clicked(self) -> None:
        """Handle bot pause button click."""
        bot_controller = getattr(self, "_bot_controller", None)
        if bot_controller:
            if self.bot_pause_btn.text() == "Pause":
                bot_controller.pause()
                self.bot_pause_btn.setText("Resume")
                self._update_bot_status("PAUSED", "#ff9800")
            else:
                bot_controller.resume()
                self.bot_pause_btn.setText("Pause")
                self._update_bot_status("RUNNING", "#26a69a")

    # ==================== MODE CHANGE HANDLERS ====================

    def _on_ki_mode_changed(self, mode: str) -> None:
        """Handle KI mode change."""
        logger.info(f"KI mode changed to: {mode}")
        bot_controller = getattr(self, "_bot_controller", None)
        if bot_controller:
            bot_controller.set_ki_mode(mode)

    def _on_trailing_mode_changed(self, mode: str = "") -> None:
        """Handle trailing mode change - toggle field visibility based on mode."""
        current_mode = self.trailing_mode_combo.currentText()
        is_pct = current_mode == "PCT"
        is_atr = current_mode == "ATR"

        disabled_style = "color: #666666;"
        enabled_style = ""

        # PCT distance only for PCT mode
        self.trailing_distance_spin.setEnabled(is_pct)
        self.trailing_distance_spin.setStyleSheet(enabled_style if is_pct else disabled_style)

        # ATR settings only for ATR mode
        self.regime_adaptive_cb.setEnabled(is_atr)
        self.atr_multiplier_spin.setEnabled(is_atr)
        self.atr_trending_spin.setEnabled(is_atr)
        self.atr_ranging_spin.setEnabled(is_atr)
        self.volatility_bonus_spin.setEnabled(is_atr)

        self.regime_adaptive_cb.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_multiplier_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_trending_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_ranging_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.volatility_bonus_spin.setStyleSheet(enabled_style if is_atr else disabled_style)

        # Update regime-adaptive visibility when in ATR mode
        if is_atr:
            self._on_regime_adaptive_changed()

    def _on_regime_adaptive_changed(self, state: int = 0) -> None:
        """Handle regime-adaptive checkbox change - toggle field visibility."""
        if self.trailing_mode_combo.currentText() != "ATR":
            return

        is_adaptive = self.regime_adaptive_cb.isChecked()

        # Fixed multiplier only visible when NOT adaptive
        self.atr_multiplier_spin.setEnabled(not is_adaptive)

        # Adaptive settings only visible when adaptive
        self.atr_trending_spin.setEnabled(is_adaptive)
        self.atr_ranging_spin.setEnabled(is_adaptive)
        self.volatility_bonus_spin.setEnabled(is_adaptive)

        disabled_style = "color: #666666;"
        enabled_style = ""

        self.atr_multiplier_spin.setStyleSheet(enabled_style if not is_adaptive else disabled_style)
        self.atr_trending_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)
        self.atr_ranging_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)
        self.volatility_bonus_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)

    def _on_display_option_changed(self, state: int) -> None:
        """Handle display option checkbox change."""
        if not hasattr(self, 'chart_widget'):
            return

        # Entry markers visibility
        show_markers = self.show_entry_markers_cb.isChecked()
        if hasattr(self.chart_widget, '_bot_overlay_state'):
            if not show_markers:
                self.chart_widget.clear_bot_markers()

        # Stop lines visibility
        show_stops = self.show_stop_lines_cb.isChecked()
        if hasattr(self.chart_widget, '_bot_overlay_state'):
            if not show_stops:
                self.chart_widget.clear_stop_lines()
            else:
                bot_controller = getattr(self, "_bot_controller", None)
                if bot_controller and bot_controller.position:
                    self.chart_widget.display_position(bot_controller.position)

    def _on_debug_hud_changed(self, state: int) -> None:
        """Handle debug HUD checkbox change."""
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'set_debug_hud_visible'):
            self.chart_widget.set_debug_hud_visible(state == Qt.CheckState.Checked.value)

    def _on_derivathandel_changed(self, state: int) -> None:
        """Handle Derivathandel checkbox change - toggle derivative columns visibility."""
        is_enabled = self.enable_derivathandel_cb.isChecked()
        logger.info(f"Derivathandel: {'enabled' if is_enabled else 'disabled'}")

        # Toggle derivative columns visibility in signals table
        # Issue #19 FIX: Correct columns are 18, 19, 20, 21 (D P&L €, D P&L %, Hebel, WKN)
        # NOT 13, 14, 15, 16, 17 which are P&L USDT, Trading fees %, Trading fees, Invest, Stück!
        if hasattr(self, 'signals_table'):
            for col in [18, 19, 20, 21]:  # D P&L €, D P&L %, Hebel, WKN
                self.signals_table.setColumnHidden(col, not is_enabled)

        # Toggle derivative labels visibility in Current Position GroupBox
        deriv_labels = [
            'deriv_separator', 'deriv_wkn_label', 'deriv_leverage_label',
            'deriv_spread_label', 'deriv_ask_label', 'deriv_pnl_label'
        ]
        for label_name in deriv_labels:
            label = getattr(self, label_name, None)
            if label:
                label.setVisible(is_enabled)

    def _on_force_reselect(self) -> None:
        """Handle force re-selection button click."""
        logger.info("Forcing strategy re-selection")
        bot_controller = getattr(self, "_bot_controller", None)
        if bot_controller:
            bot_controller.force_strategy_reselection()

    def _clear_ki_log(self) -> None:
        """Clear KI log display."""
        self.ki_log_text.clear()
        self._ki_log_entries.clear()

    # ==================== SYMBOL & SETTINGS MANAGEMENT ====================

    def update_bot_symbol(self, symbol: str | None = None) -> None:
        """Update the bot panel with current symbol and load its settings.

        Args:
            symbol: Symbol to use, or None to get from chart
        """
        if symbol is None:
            symbol = getattr(self, 'current_symbol', None)
            if symbol is None and hasattr(self, 'chart_widget'):
                symbol = getattr(self.chart_widget, 'current_symbol', None)

        if not symbol:
            symbol = "UNKNOWN"

        if hasattr(self, 'bot_symbol_label'):
            self.bot_symbol_label.setText(symbol)

        if symbol != self._current_bot_symbol:
            self._current_bot_symbol = symbol
            self._last_tick_price = 0.0  # Reset last tick price on symbol change
            self._load_bot_settings(symbol)
            logger.info(f"Bot panel updated for symbol: {symbol}")

    def _load_bot_settings(self, symbol: str) -> None:
        """Load saved settings for a symbol into UI controls.

        Args:
            symbol: Symbol to load settings for
        """
        settings = self._bot_settings_manager.get_settings(symbol)

        if not settings:
            logger.debug(f"No saved settings for {symbol}, using defaults")
            return

        logger.info(f"Loading bot settings for {symbol}")

        try:
            # Bot settings
            self._apply_combo_setting(settings, "ki_mode", self.ki_mode_combo)
            self._apply_combo_setting(settings, "trailing_mode", self.trailing_mode_combo)
            self._apply_spin_setting(settings, "initial_sl_pct", self.initial_sl_spin)
            self._apply_spin_setting(settings, "bot_capital", self.bot_capital_spin)
            self._apply_spin_setting(settings, "risk_per_trade_pct", self.risk_per_trade_spin)
            self._apply_spin_setting(settings, "max_trades_per_day", self.max_trades_spin)
            self._apply_spin_setting(settings, "max_daily_loss_pct", self.max_daily_loss_spin)
            self._apply_checkbox_setting(
                settings, "disable_restrictions", self.disable_restrictions_cb
            )
            self._apply_checkbox_setting(
                settings, "disable_macd_exit", self.disable_macd_exit_cb
            )
            self._apply_checkbox_setting(
                settings, "disable_macd_entry", self.disable_macd_entry_cb
            )
            self._apply_checkbox_setting(settings, "disable_rsi_exit", self.disable_rsi_exit_cb)
            self._apply_checkbox_setting(
                settings, "disable_rsi_entry", self.disable_rsi_entry_cb
            )
            self._apply_checkbox_setting(
                settings,
                "enable_derivathandel",
                self.enable_derivathandel_cb,
                on_change=lambda: self._on_derivathandel_changed(0),
            )

            # Trailing stop settings
            self._apply_checkbox_setting(settings, "regime_adaptive", self.regime_adaptive_cb)
            # Issue #44: Add hasattr checks for bot UI widgets that may not exist
            if hasattr(self, 'atr_multiplier_spin'):
                self._apply_spin_setting(settings, "atr_multiplier", self.atr_multiplier_spin)
            if hasattr(self, 'atr_trending_spin'):
                self._apply_spin_setting(settings, "atr_trending", self.atr_trending_spin)
            if hasattr(self, 'atr_ranging_spin'):
                self._apply_spin_setting(settings, "atr_ranging", self.atr_ranging_spin)
            if hasattr(self, 'volatility_bonus_spin'):
                self._apply_spin_setting(settings, "volatility_bonus", self.volatility_bonus_spin)
            if hasattr(self, 'min_step_spin'):
                self._apply_spin_setting(settings, "min_step", self.min_step_spin)
            if hasattr(self, 'tra_percent_spin'):
                self._apply_spin_setting(
                    settings, "tra_percent", self.tra_percent_spin
                )
            if hasattr(self, 'trailing_distance_spin'):
                self._apply_spin_setting(
                    settings, "trailing_distance", self.trailing_distance_spin
                )
            if hasattr(self, 'min_score_spin'):
                self._apply_spin_setting(settings, "min_score", self.min_score_spin)
            self._apply_checkbox_setting(settings, "use_pattern", self.use_pattern_cb)
            self._apply_spin_setting(
                settings, "pattern_similarity", self.pattern_similarity_spin
            )
            self._apply_spin_setting(
                settings, "pattern_min_matches", self.pattern_matches_spin
            )
            self._apply_spin_setting(
                settings, "pattern_winrate", self.pattern_winrate_spin
            )

            # Update UI state
            self._on_trailing_mode_changed()
            self._on_regime_adaptive_changed()

            logger.info(f"Loaded {len(settings)} settings for {symbol}")

        except Exception as e:
            logger.error(f"Error loading settings for {symbol}: {e}")

    def _apply_combo_setting(self, settings: dict, key: str, combo) -> None:
        if key not in settings:
            return
        idx = combo.findText(settings[key])
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _apply_spin_setting(self, settings: dict, key: str, spin) -> None:
        if key in settings:
            spin.setValue(settings[key])

    def _apply_checkbox_setting(self, settings: dict, key: str, checkbox, on_change=None) -> None:
        if key in settings:
            checkbox.setChecked(settings[key])
            if on_change:
                on_change()

    def _save_bot_settings(self, symbol: str) -> None:
        """Save current UI settings for a symbol.

        Args:
            symbol: Symbol to save settings for
        """
        settings = {
            # Bot settings
            "ki_mode": self.ki_mode_combo.currentText(),
            "trailing_mode": self.trailing_mode_combo.currentText(),
            "initial_sl_pct": self.initial_sl_spin.value(),
            "bot_capital": self.bot_capital_spin.value(),
            "risk_per_trade_pct": self.risk_per_trade_spin.value(),
            "max_trades_per_day": self.max_trades_spin.value(),
            "max_daily_loss_pct": self.max_daily_loss_spin.value(),
            "disable_restrictions": self.disable_restrictions_cb.isChecked(),
            "disable_macd_exit": self.disable_macd_exit_cb.isChecked(),
            "disable_macd_entry": self.disable_macd_entry_cb.isChecked(),
            "disable_rsi_exit": self.disable_rsi_exit_cb.isChecked(),
            "disable_rsi_entry": self.disable_rsi_entry_cb.isChecked(),
            "enable_derivathandel": self.enable_derivathandel_cb.isChecked(),

            # Trailing stop settings
            "regime_adaptive": self.regime_adaptive_cb.isChecked(),
            "tra_percent": self.tra_percent_spin.value() if hasattr(self, 'tra_percent_spin') else None,
            "trailing_distance": self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else None,
            "use_pattern": self.use_pattern_cb.isChecked(),
            "pattern_similarity": self.pattern_similarity_spin.value(),
            "pattern_min_matches": self.pattern_matches_spin.value(),
            "pattern_winrate": self.pattern_winrate_spin.value(),
        }

        # Issue #44: Add optional settings only if widgets exist
        if hasattr(self, 'atr_multiplier_spin'):
            settings["atr_multiplier"] = self.atr_multiplier_spin.value()
        if hasattr(self, 'atr_trending_spin'):
            settings["atr_trending"] = self.atr_trending_spin.value()
        if hasattr(self, 'atr_ranging_spin'):
            settings["atr_ranging"] = self.atr_ranging_spin.value()
        if hasattr(self, 'volatility_bonus_spin'):
            settings["volatility_bonus"] = self.volatility_bonus_spin.value()
        if hasattr(self, 'min_step_spin'):
            settings["min_step"] = self.min_step_spin.value()
        if hasattr(self, 'min_score_spin'):
            settings["min_score"] = self.min_score_spin.value()

        self._bot_settings_manager.save_settings(symbol, settings)
        logger.info(f"Saved bot settings for {symbol}")
