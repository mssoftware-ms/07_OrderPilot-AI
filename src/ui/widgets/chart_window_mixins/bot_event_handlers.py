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
            return

        self.bot_start_btn.setEnabled(False)
        self.bot_stop_btn.setEnabled(True)
        self.bot_pause_btn.setEnabled(True)

    def _on_bot_stop_clicked(self) -> None:
        """Handle bot stop button click."""
        logger.info("Bot stop requested")
        self._stop_bot()

        self._update_bot_status("STOPPED", "#9e9e9e")
        self.bot_start_btn.setEnabled(True)
        self.bot_stop_btn.setEnabled(False)
        self.bot_pause_btn.setEnabled(False)

    def _on_bot_pause_clicked(self) -> None:
        """Handle bot pause button click."""
        if self._bot_controller:
            if self.bot_pause_btn.text() == "Pause":
                self._bot_controller.pause()
                self.bot_pause_btn.setText("Resume")
                self._update_bot_status("PAUSED", "#ff9800")
            else:
                self._bot_controller.resume()
                self.bot_pause_btn.setText("Pause")
                self._update_bot_status("RUNNING", "#26a69a")

    # ==================== MODE CHANGE HANDLERS ====================

    def _on_ki_mode_changed(self, mode: str) -> None:
        """Handle KI mode change."""
        logger.info(f"KI mode changed to: {mode}")
        if self._bot_controller:
            self._bot_controller.set_ki_mode(mode)

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
            elif self._bot_controller and self._bot_controller.position:
                self.chart_widget.display_position(self._bot_controller.position)

    def _on_debug_hud_changed(self, state: int) -> None:
        """Handle debug HUD checkbox change."""
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'set_debug_hud_visible'):
            self.chart_widget.set_debug_hud_visible(state == Qt.CheckState.Checked.value)

    def _on_derivathandel_changed(self, state: int) -> None:
        """Handle Derivathandel checkbox change - toggle derivative columns visibility."""
        is_enabled = self.enable_derivathandel_cb.isChecked()
        logger.info(f"Derivathandel: {'enabled' if is_enabled else 'disabled'}")

        # Toggle derivative columns visibility in signals table (Spalten 13-16)
        if hasattr(self, 'signals_table'):
            for col in [13, 14, 15, 16]:  # D P&L €, D P&L %, Heb, WKN
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
        if self._bot_controller:
            self._bot_controller.force_strategy_reselection()

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
            if "ki_mode" in settings:
                idx = self.ki_mode_combo.findText(settings["ki_mode"])
                if idx >= 0:
                    self.ki_mode_combo.setCurrentIndex(idx)

            if "trailing_mode" in settings:
                idx = self.trailing_mode_combo.findText(settings["trailing_mode"])
                if idx >= 0:
                    self.trailing_mode_combo.setCurrentIndex(idx)

            if "initial_sl_pct" in settings:
                self.initial_sl_spin.setValue(settings["initial_sl_pct"])

            if "bot_capital" in settings:
                self.bot_capital_spin.setValue(settings["bot_capital"])

            if "risk_per_trade_pct" in settings:
                self.risk_per_trade_spin.setValue(settings["risk_per_trade_pct"])

            if "max_trades_per_day" in settings:
                self.max_trades_spin.setValue(settings["max_trades_per_day"])

            if "max_daily_loss_pct" in settings:
                self.max_daily_loss_spin.setValue(settings["max_daily_loss_pct"])

            if "disable_restrictions" in settings:
                self.disable_restrictions_cb.setChecked(settings["disable_restrictions"])

            if "disable_macd_exit" in settings:
                self.disable_macd_exit_cb.setChecked(settings["disable_macd_exit"])

            if "disable_rsi_exit" in settings:
                self.disable_rsi_exit_cb.setChecked(settings["disable_rsi_exit"])

            if "enable_derivathandel" in settings:
                self.enable_derivathandel_cb.setChecked(settings["enable_derivathandel"])
                self._on_derivathandel_changed(0)  # Update visibility

            # Trailing stop settings
            if "regime_adaptive" in settings:
                self.regime_adaptive_cb.setChecked(settings["regime_adaptive"])

            if "atr_multiplier" in settings:
                self.atr_multiplier_spin.setValue(settings["atr_multiplier"])

            if "atr_trending" in settings:
                self.atr_trending_spin.setValue(settings["atr_trending"])

            if "atr_ranging" in settings:
                self.atr_ranging_spin.setValue(settings["atr_ranging"])

            if "volatility_bonus" in settings:
                self.volatility_bonus_spin.setValue(settings["volatility_bonus"])

            if "min_step_pct" in settings:
                self.min_step_spin.setValue(settings["min_step_pct"])

            if "trailing_activation_pct" in settings:
                self.trailing_activation_spin.setValue(settings["trailing_activation_pct"])

            if "trailing_pct_distance" in settings:
                self.trailing_distance_spin.setValue(settings["trailing_pct_distance"])

            if "min_score_pct" in settings:
                self.min_score_spin.setValue(settings["min_score_pct"])

            if "use_pattern_check" in settings:
                self.use_pattern_cb.setChecked(settings["use_pattern_check"])

            if "pattern_similarity" in settings:
                self.pattern_similarity_spin.setValue(settings["pattern_similarity"])

            if "pattern_min_matches" in settings:
                self.pattern_matches_spin.setValue(settings["pattern_min_matches"])

            if "pattern_min_winrate_pct" in settings:
                self.pattern_winrate_spin.setValue(settings["pattern_min_winrate_pct"])

            # Update UI state
            self._on_trailing_mode_changed()
            self._on_regime_adaptive_changed()

            logger.info(f"Loaded {len(settings)} settings for {symbol}")

        except Exception as e:
            logger.error(f"Error loading settings for {symbol}: {e}")

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
            "disable_rsi_exit": self.disable_rsi_exit_cb.isChecked(),
            "enable_derivathandel": self.enable_derivathandel_cb.isChecked(),

            # Trailing stop settings
            "regime_adaptive": self.regime_adaptive_cb.isChecked(),
            "atr_multiplier": self.atr_multiplier_spin.value(),
            "atr_trending": self.atr_trending_spin.value(),
            "atr_ranging": self.atr_ranging_spin.value(),
            "volatility_bonus": self.volatility_bonus_spin.value(),
            "min_step_pct": self.min_step_spin.value(),
            "trailing_activation_pct": self.trailing_activation_spin.value(),
            "trailing_pct_distance": self.trailing_distance_spin.value(),
            "min_score_pct": self.min_score_spin.value(),
            "use_pattern_check": self.use_pattern_cb.isChecked(),
            "pattern_similarity": self.pattern_similarity_spin.value(),
            "pattern_min_matches": self.pattern_matches_spin.value(),
            "pattern_min_winrate_pct": self.pattern_winrate_spin.value(),
        }

        self._bot_settings_manager.save_settings(symbol, settings)
        logger.info(f"Saved bot settings for {symbol}")
