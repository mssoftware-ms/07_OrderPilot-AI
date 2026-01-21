"""Settings Dialog for OrderPilot-AI Trading Application.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- settings_tabs_mixin.py: Tab creation methods
- settings_dialog.py: Main SettingsDialog class (this file)
"""

import logging
import os

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
)

from src.config.loader import config_manager
from .settings_tabs_mixin import SettingsTabsMixin

logger = logging.getLogger(__name__)


class SettingsDialog(SettingsTabsMixin, QDialog):
    """Application settings dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.settings = QSettings("OrderPilot", "TradingApp")
        self.profile = config_manager.load_profile()
        
        # Pre-declare theme attributes to prevent early access issues
        self.ui_bg_color_btn = None
        self.ui_btn_color_btn = None
        self.ui_dropdown_color_btn = None
        self.ui_edit_color_btn = None
        self.ui_edit_text_color_btn = None
        self.ui_active_btn_color_btn = None
        self.ui_inactive_btn_color_btn = None
        self.ui_btn_hover_border_color_btn = None
        self.ui_btn_hover_text_color_btn = None
        
        # Pre-declare color objects
        from PyQt6.QtGui import QColor
        self.ui_bg_color = QColor()
        self.ui_btn_color = QColor()
        self.ui_dropdown_color = QColor()
        self.ui_edit_color = QColor()
        self.ui_edit_text_color = QColor()
        self.ui_active_btn_color = QColor()
        self.ui_inactive_btn_color = QColor()
        self.ui_btn_hover_border_color = QColor()
        self.ui_btn_hover_text_color = QColor()
        
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        """Initialize the settings dialog UI."""
        self.setMinimumSize(600, 400)
        self.setMaximumHeight(750)

        # Set smaller font for compact layout
        from PyQt6.QtGui import QFont
        font = QFont()
        font.setPointSize(9)
        self.setFont(font)

        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # Create tabs using mixin methods
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_theme_tab(), "Theme")
        tabs.addTab(self._create_trading_tab(), "Trading")
        tabs.addTab(self._create_broker_tab(), "Brokers")
        tabs.addTab(self._create_market_data_tab(), "Market Data")
        tabs.addTab(self._create_data_quality_tab(), "Data Quality")
        tabs.addTab(self._create_ai_tab(), "AI")
        tabs.addTab(self._create_notifications_tab(), "Notifications")

        layout.addWidget(tabs)

        # Connect theme change to live update UI
        self._last_theme_name = self.settings.value("theme", "Dark Orange")
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def load_current_settings(self):
        """Load current settings from QSettings."""
        # Refresh profile reference to capture external changes
        self.profile = config_manager.load_profile()

        # Theme & UI - This will trigger _on_theme_changed but we need to load initial values
        initial_theme = self.settings.value("theme", "Dark Orange")
        self._set_combo_value(self.theme_combo, initial_theme)
        
        # Load values for the selected theme
        self._apply_theme_to_ui(initial_theme)
        
        # General settings (Always independent)
        self.auto_connect_check.setChecked(
            self.settings.value("auto_connect", False, type=bool)
        )
        self._set_combo_value(
            self.default_broker_combo,
            self.settings.value("default_broker", "Trade Republic"),
        )
        self._set_combo_value(
            self.console_debug_level,
            self.settings.value("console_debug_level", "INFO"),
        )

        from PyQt6.QtGui import QColor

        # App UI Colors
        # Note: Theme-specific colors/fonts are now loaded via _apply_theme_to_ui

        # Trading
        self.manual_approval.setChecked(
            self.settings.value("manual_approval", True, type=bool)
        )
        self.confirm_cancel.setChecked(
            self.settings.value("confirm_cancel", True, type=bool)
        )
        self.max_order_size.setValue(
            self.settings.value("max_order_size", 10000, type=float)
        )

        self._set_combo_value(
            self.risk_combo,
            self.settings.value("risk_tolerance", "Moderate"),
        )

        # AI
        self.ai_enabled.setChecked(
            self.settings.value("ai_enabled", True, type=bool)
        )

        # Default provider
        self._set_combo_value(
            self.ai_default_provider,
            self.settings.value("ai_default_provider", "Anthropic"),
        )
        self._set_env_placeholders()
        self._set_combo_value(
            self.openai_model,
            self.settings.value("openai_model", "gpt-5.1 (GPT-5.1)"),
        )

        # Trigger model change to populate reasoning efforts
        self._on_openai_model_changed(self.openai_model.currentText())

        # OpenAI Reasoning settings
        self._set_combo_value(
            self.openai_reasoning_effort,
            self.settings.value("openai_reasoning_effort", "medium"),
        )
        self.openai_max_tokens.setValue(
            self.settings.value("openai_max_tokens", 3000, type=int)
        )
        self.openai_temperature.setValue(
            self.settings.value("openai_temperature", 0.1, type=float)
        )
        self.openai_top_p.setValue(
            self.settings.value("openai_top_p", 1.0, type=float)
        )

        self._set_combo_value(
            self.anthropic_model,
            self.settings.value(
                "anthropic_model",
                "claude-sonnet-4-5-20250929 (Recommended)",
            ),
        )
        self._set_combo_value(
            self.gemini_model,
            self.settings.value("gemini_model", "gemini-2.0-flash-exp (Latest)"),
        )

        self.ai_budget.setValue(
            self.settings.value("ai_budget", 50, type=float)
        )

        # Broker Settings
        self.ibkr_host.setText(
            self.settings.value("ibkr_host", "localhost")
        )

        self._set_combo_value(
            self.ibkr_port,
            self.settings.value("ibkr_port", "7497 (Paper)"),
        )
        self._set_combo_value(
            self.ibkr_client_id,
            self.settings.value("ibkr_client_id", "1"),
        )

        self.tr_phone.setText(
            self.settings.value("tr_phone", "")
        )

        # Market Data provider settings
        market_config = self.profile.market_data

        self.alpha_enabled.setChecked(market_config.alpha_vantage_enabled)
        alpha_key_exists = bool(config_manager.get_credential("alpha_vantage_api_key"))
        if alpha_key_exists:
            self.alpha_api_key.setPlaceholderText(
                "API key stored securely. Enter a new value to replace it."
            )
        else:
            self.alpha_api_key.setPlaceholderText("Enter Alpha Vantage API key")

        self.finnhub_enabled.setChecked(market_config.finnhub_enabled)
        finnhub_key_exists = bool(config_manager.get_credential("finnhub_api_key"))
        if finnhub_key_exists:
            self.finnhub_api_key.setPlaceholderText(
                "API key stored securely. Enter a new value to replace it."
            )
        else:
            self.finnhub_api_key.setPlaceholderText("Enter Finnhub API key")

        self.yahoo_enabled.setChecked(market_config.yahoo_enabled)

        self.alpaca_enabled.setChecked(market_config.alpaca_enabled)
        self._set_credential_placeholder(
            self.alpaca_api_key,
            "alpaca_api_key",
            "Enter Alpaca API key",
            "API key stored securely. Enter a new value to replace it.",
        )
        self._set_credential_placeholder(
            self.alpaca_api_secret,
            "alpaca_api_secret",
            "Enter Alpaca API secret",
            "API secret stored securely. Enter a new value to replace it.",
        )

        self.bitunix_enabled.setChecked(market_config.bitunix_enabled)
        self._set_credential_placeholder(
            self.bitunix_api_key,
            "bitunix_api_key",
            "Enter Bitunix API key",
            "API key stored securely. Enter a new value to replace it.",
        )
        self._set_credential_placeholder(
            self.bitunix_api_secret,
            "bitunix_secret_key",
            "Enter Bitunix API secret",
            "API secret stored securely. Enter a new value to replace it.",
        )
        self.bitunix_testnet.setChecked(
            self.settings.value("bitunix_testnet", True, type=bool)
        )
        self.bitunix_broker_enabled.setChecked(
            self.settings.value("bitunix_broker_enabled", False, type=bool)
        )

        self.prefer_live_broker.setChecked(market_config.prefer_live_broker)

        # Live data in paper mode
        self.enable_live_data_paper.setChecked(
            self.settings.value("live_data_enabled", False, type=bool)
        )

        # Notifications
        self.order_filled_notif.setChecked(
            self.settings.value("order_filled_notif", True, type=bool)
        )
        self.alert_notif.setChecked(
            self.settings.value("alert_notif", True, type=bool)
        )
        self.connection_notif.setChecked(
            self.settings.value("connection_notif", False, type=bool)
        )

    def _set_combo_value(self, combo, value: str) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _set_env_placeholders(self) -> None:
        if os.getenv("OPENAI_API_KEY"):
            self.openai_api_key.setPlaceholderText(
                "API key loaded from environment variable"
            )
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_api_key.setPlaceholderText(
                "API key loaded from environment variable"
            )
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_api_key.setPlaceholderText(
                "API key loaded from environment variable"
            )

    def _set_credential_placeholder(
        self,
        field,
        credential_key: str,
        empty_text: str,
        stored_text: str,
    ) -> None:
        key_exists = bool(config_manager.get_credential(credential_key))
        field.setPlaceholderText(stored_text if key_exists else empty_text)

    def save_settings(self):
        """Save settings to QSettings and configuration."""
        try:
            # 1. Current active theme
            theme_name = self.theme_combo.currentText()
            self.settings.setValue("theme", theme_name)
            
            # 2. Cache CURRENT UI state to the active theme in the cache
            self._cache_current_ui_to_theme(theme_name)
            
            # 3. Save ALL cached theme settings to QSettings with prefixes
            if hasattr(self, '_theme_cache'):
                for t_name, vals in self._theme_cache.items():
                    t_key = t_name.lower().replace(" ", "_")
                    for k, v in vals.items():
                        self.settings.setValue(f"{t_key}_{k}", v)

            # 4. Save General Settings
            self.settings.setValue("auto_connect", self.auto_connect_check.isChecked())
            self.settings.setValue("default_broker", self.default_broker_combo.currentText())
            self.settings.setValue("console_debug_level", self.console_debug_level.currentText())

            # Apply UI updates immediately
            # Update Icon Provider - ALWAYS use workspace assets
            from src.ui.icons import configure_icon_provider
            configure_icon_provider(
                icons_dir=None,
                invert_to_white=self.icon_force_white_check.isChecked()
            )

            # Clear custom colors cache to force reload in charts
            from src.ui.widgets.chart_shared.theme_utils import clear_custom_colors_cache
            clear_custom_colors_cache()
            
            # Refresh colors in all open charts
            try:
                from src.ui.chart_window_manager import get_chart_window_manager
                chart_mgr = get_chart_window_manager()
                if chart_mgr:
                    chart_mgr.refresh_all_chart_colors()
            except Exception as exc:
                logger.warning(f"Could not refresh chart colors: {exc}")

            # Apply console debug level immediately
            self._apply_console_debug_level()

            # 5. Trading
            self.settings.setValue("manual_approval", self.manual_approval.isChecked())
            self.settings.setValue("confirm_cancel", self.confirm_cancel.isChecked())
            self.settings.setValue("max_order_size", self.max_order_size.value())
            self.settings.setValue("risk_tolerance", self.risk_combo.currentText())

            # 6. AI
            self.settings.setValue("ai_enabled", self.ai_enabled.isChecked())
            self.settings.setValue("ai_default_provider", self.ai_default_provider.currentText())
            self.settings.setValue("openai_model", self.openai_model.currentText())
            self.settings.setValue("openai_reasoning_effort", self.openai_reasoning_effort.currentText())
            self.settings.setValue("openai_max_tokens", self.openai_max_tokens.value())
            self.settings.setValue("openai_temperature", self.openai_temperature.value())
            self.settings.setValue("openai_top_p", self.openai_top_p.value())
            self.settings.setValue("anthropic_model", self.anthropic_model.currentText())
            self.settings.setValue("gemini_model", self.gemini_model.currentText())
            self.settings.setValue("ai_budget", self.ai_budget.value())

            # Reset AI service to apply new settings
            from src.ai import reset_ai_service
            reset_ai_service()

            # Save API keys
            self._save_api_keys()

            # 7. Broker Settings
            self.settings.setValue("ibkr_host", self.ibkr_host.text().strip())
            self.settings.setValue("ibkr_port", self.ibkr_port.currentText())
            self.settings.setValue("ibkr_client_id", self.ibkr_client_id.currentText())
            self.settings.setValue("tr_phone", self.tr_phone.text().strip())

            # Save Trade Republic PIN
            tr_pin = self.tr_pin.text().strip()
            if tr_pin:
                try:
                    config_manager.set_credential("tr_pin", tr_pin)
                except Exception as e:
                    QMessageBox.warning(self, "PIN Storage", f"Could not store Trade Republic PIN securely:\n{str(e)}")

            # 8. Market Data provider toggles
            self._save_market_data_settings()

            # 9. Live data in paper mode
            self.settings.setValue("live_data_enabled", self.enable_live_data_paper.isChecked())

            # 10. Notifications
            self.settings.setValue("order_filled_notif", self.order_filled_notif.isChecked())
            self.settings.setValue("alert_notif", self.alert_notif.isChecked())
            self.settings.setValue("connection_notif", self.connection_notif.isChecked())

            self.settings.sync()

            # Apply theme immediately to main window
            if self.parent() and hasattr(self.parent(), "apply_theme"):
                self.parent().apply_theme(self.theme_combo.currentText())

            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings:\n{str(e)}")

    def _apply_console_debug_level(self):
        """Apply console debug level to all loggers immediately."""
        import logging

        level_str = self.console_debug_level.currentText()
        level = getattr(logging, level_str, logging.INFO)

        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Also set console handler level
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(level)

        # Special handling for stream/chart provider loggers at WARNING level
        # These are suppressed unless DEBUG is selected
        stream_loggers = [
            'src.core.market_data.bitunix_stream',
            'src.core.market_data.bitunix_stream_connection',
            'src.core.market_data.bitunix_stream_handlers',
            'src.core.market_data.bitunix_stream_messages',
            'src.core.market_data.bitunix_stream_subscription',
            'src.core.market_data.history_provider',
            'src.core.market_data.history_provider_streaming',
            'src.ui.widgets.chart_mixins',
            'urllib3',
            'websockets',
            'aiohttp',
        ]

        # If WARNING or higher, suppress stream loggers to WARNING
        if level >= logging.WARNING:
            for logger_name in stream_loggers:
                logging.getLogger(logger_name).setLevel(logging.WARNING)
        else:
            # For DEBUG/INFO, let stream loggers use the global level
            for logger_name in stream_loggers:
                logging.getLogger(logger_name).setLevel(level)

        logger.info(f"Console debug level set to: {level_str}")

    def _save_api_keys(self):
        """Save API keys to secure keyring."""
        # OpenAI
        openai_key = self.openai_api_key.text().strip()
        if openai_key:
            try:
                config_manager.set_credential("openai_api_key", openai_key)
                self.openai_api_key.clear()
            except Exception as e:
                QMessageBox.warning(
                    self, "API Key Storage",
                    f"Could not store OpenAI API key securely:\n{str(e)}\n\n"
                    "You may need to re-enter it next session."
                )

        # Anthropic
        anthropic_key = self.anthropic_api_key.text().strip()
        if anthropic_key:
            try:
                config_manager.set_credential("anthropic_api_key", anthropic_key)
                self.anthropic_api_key.clear()
            except Exception as e:
                QMessageBox.warning(
                    self, "API Key Storage",
                    f"Could not store Anthropic API key securely:\n{str(e)}\n\n"
                    "You may need to re-enter it next session."
                )

        # Gemini
        gemini_key = self.gemini_api_key.text().strip()
        if gemini_key:
            try:
                config_manager.set_credential("gemini_api_key", gemini_key)
                self.gemini_api_key.clear()
            except Exception as e:
                QMessageBox.warning(
                    self, "API Key Storage",
                    f"Could not store Gemini API key securely:\n{str(e)}\n\n"
                    "You may need to re-enter it next session."
                )

    def _save_market_data_settings(self):
        """Save market data provider settings."""
        profile = config_manager.load_profile()
        market_config = profile.market_data
        market_config.alpaca_enabled = self.alpaca_enabled.isChecked()
        market_config.alpha_vantage_enabled = self.alpha_enabled.isChecked()
        market_config.finnhub_enabled = self.finnhub_enabled.isChecked()
        market_config.yahoo_enabled = self.yahoo_enabled.isChecked()
        market_config.bitunix_enabled = self.bitunix_enabled.isChecked()
        market_config.prefer_live_broker = self.prefer_live_broker.isChecked()

        # Bitunix testnet setting
        self.settings.setValue("bitunix_testnet", self.bitunix_testnet.isChecked())
        self.settings.setValue("bitunix_broker_enabled", self.bitunix_broker_enabled.isChecked())

        # Alpha Vantage API key
        alpha_key = self.alpha_api_key.text().strip()
        if alpha_key:
            try:
                config_manager.set_credential("alpha_vantage_api_key", alpha_key)
                self.alpha_api_key.clear()
            except Exception as e:
                QMessageBox.warning(
                    self, "API Key Storage",
                    f"Could not store Alpha Vantage API key securely:\n{str(e)}\n\n"
                    "You may need to re-enter it next session."
                )

        # Finnhub API key
        finnhub_key = self.finnhub_api_key.text().strip()
        if finnhub_key:
            try:
                config_manager.set_credential("finnhub_api_key", finnhub_key)
                self.finnhub_api_key.clear()
            except Exception as e:
                QMessageBox.warning(
                    self, "API Key Storage",
                    f"Could not store Finnhub API key securely:\n{str(e)}\n\n"
                    "You may need to re-enter it next session."
                )

        # Alpaca credentials
        alpaca_key = self.alpaca_api_key.text().strip()
        alpaca_secret = self.alpaca_api_secret.text().strip()
        if alpaca_key and alpaca_secret:
            try:
                config_manager.set_credential("alpaca_api_key", alpaca_key)
                config_manager.set_credential("alpaca_api_secret", alpaca_secret)
                self.alpaca_api_key.clear()
                self.alpaca_api_secret.clear()
            except Exception as e:
                QMessageBox.warning(
                    self, "API Key Storage",
                    f"Could not store Alpaca API credentials securely:\n{str(e)}\n\n"
                    "You may need to re-enter them next session."
                )
        elif alpaca_key or alpaca_secret:
            QMessageBox.warning(
                self, "Incomplete Credentials",
                "Both API key and secret are required for Alpaca.\n\n"
                "Please provide both or leave both empty."
            )

        # Bitunix credentials
        bitunix_key = self.bitunix_api_key.text().strip()
        bitunix_secret = self.bitunix_api_secret.text().strip()
        if bitunix_key and bitunix_secret:
            try:
                config_manager.set_credential("bitunix_api_key", bitunix_key)
                config_manager.set_credential("bitunix_secret_key", bitunix_secret)
                self.bitunix_api_key.clear()
                self.bitunix_api_secret.clear()
            except Exception as e:
                QMessageBox.warning(
                    self, "API Key Storage",
                    f"Could not store Bitunix API credentials securely:\n{str(e)}\n\n"
                    "You may need to re-enter them next session."
                )
        elif bitunix_key or bitunix_secret:
            QMessageBox.warning(
                self, "Incomplete Credentials",
                "Both API key and secret are required for Bitunix.\n\n"
                "Please provide both or leave both empty."
            )

        # Persist profile changes
        config_manager.save_profile(profile)

    # ========================================================================
    # Theme Management Helpers
    # ========================================================================

    def _on_theme_changed(self, theme_name: str):
        """Handle theme combo change - swap cached values."""
        if hasattr(self, '_last_theme_name') and self._last_theme_name != theme_name:
            # Save current state to cache
            self._cache_current_ui_to_theme(self._last_theme_name)
            
            # Load new theme state from cache/settings
            self._apply_theme_to_ui(theme_name)
            
            self._last_theme_name = theme_name

    def _cache_current_ui_to_theme(self, theme_name: str):
        """Store current UI state in theme cache."""
        if not hasattr(self, '_theme_cache'):
            self._theme_cache = {}
            
        self._theme_cache[theme_name] = {
            "ui_bg_color": self.ui_bg_color.name(),
            "ui_btn_color": self.ui_btn_color.name(),
            "ui_dropdown_color": self.ui_dropdown_color.name(),
            "ui_edit_color": self.ui_edit_color.name(),
            "ui_edit_text_color": self.ui_edit_text_color.name(),
            "ui_active_btn_color": self.ui_active_btn_color.name(),
            "ui_inactive_btn_color": self.ui_inactive_btn_color.name(),
            "ui_btn_hover_border_color": self.ui_btn_hover_border_color.name(),
            "ui_btn_hover_text_color": self.ui_btn_hover_text_color.name(),
            "ui_btn_font_family": self.ui_btn_font_combo.currentText(),
            "ui_btn_font_size": self.ui_btn_font_size.value(),
            "ui_btn_width": self.ui_btn_width.value(),
            "ui_btn_height": self.ui_btn_height.value(),
            "chart_bullish_color": self.bullish_color.name(),
            "chart_bearish_color": self.bearish_color.name(),
            "chart_background_color": self.background_color.name(),
            "chart_background_image": self.background_image_path,
            "chart_background_image_opacity": self.background_image_opacity_slider.value(),
            "chart_candle_border_radius": self.candle_border_radius_slider.value(),
            "icon_dir": self.icon_dir_path,
            "icon_force_white": self.icon_force_white_check.isChecked()
        }

    def _apply_theme_to_ui(self, theme_name: str):
        """Apply theme-specific values from cache/settings to UI."""
        from PyQt6.QtGui import QColor
        t_key = theme_name.lower().replace(" ", "_")
        
        # Helper to get value from cache or settings or default
        def gt(key, default):
            if hasattr(self, '_theme_cache') and theme_name in self._theme_cache:
                return self._theme_cache[theme_name].get(key, default)
            return self.settings.value(f"{t_key}_{key}", default)

        # Colors
        self.ui_bg_color = QColor(gt("ui_bg_color", "#0F1115" if "Orange" in theme_name else "#09090b"))
        self._basic_helper._update_color_button(self.ui_bg_color_btn, self.ui_bg_color)
        
        self.ui_btn_color = QColor(gt("ui_btn_color", "#2A2D33" if "Orange" in theme_name else "#000000"))
        self._basic_helper._update_color_button(self.ui_btn_color_btn, self.ui_btn_color)
        
        self.ui_dropdown_color = QColor(gt("ui_dropdown_color", "#23262E" if "Orange" in theme_name else "#27272a"))
        self._basic_helper._update_color_button(self.ui_dropdown_color_btn, self.ui_dropdown_color)
        
        self.ui_edit_color = QColor(gt("ui_edit_color", "#23262E" if "Orange" in theme_name else "#27272a"))
        self._basic_helper._update_color_button(self.ui_edit_color_btn, self.ui_edit_color)
        
        self.ui_edit_text_color = QColor(gt("ui_edit_text_color", "#EAECEF" if "Orange" in theme_name else "#f4f4f5"))
        self._basic_helper._update_color_button(self.ui_edit_text_color_btn, self.ui_edit_text_color)
        
        self.ui_active_btn_color = QColor(gt("ui_active_btn_color", "#F29F05" if "Orange" in theme_name else "#ffffff"))
        self._basic_helper._update_color_button(self.ui_active_btn_color_btn, self.ui_active_btn_color)
        
        self.ui_inactive_btn_color = QColor(gt("ui_inactive_btn_color", "#2A2D33" if "Orange" in theme_name else "#000000"))
        self._basic_helper._update_color_button(self.ui_inactive_btn_color_btn, self.ui_inactive_btn_color)

        self.ui_btn_hover_border_color = QColor(gt("ui_btn_hover_border_color", "#F29F05" if "Orange" in theme_name else "#ffffff"))
        self._basic_helper._update_color_button(self.ui_btn_hover_border_color_btn, self.ui_btn_hover_border_color)

        self.ui_btn_hover_text_color = QColor(gt("ui_btn_hover_text_color", "#F29F05" if "Orange" in theme_name else "#000000"))
        self._basic_helper._update_color_button(self.ui_btn_hover_text_color_btn, self.ui_btn_hover_text_color)

        # Fonts & Sizes
        self.ui_btn_font_combo.setEnabled(True) # Force enabled
        font_family = gt("ui_btn_font_family", "")
        if font_family:
            self.ui_btn_font_combo.setCurrentText(font_family)
        else:
            self.ui_btn_font_combo.setCurrentFont(self.parent().font() if self.parent() else self.font())
            
        self.ui_btn_font_size.setValue(int(gt("ui_btn_font_size", 12)))
        self.ui_btn_width.setValue(int(gt("ui_btn_width", 80)))
        self.ui_btn_height.setValue(int(gt("ui_btn_height", 32)))

        # Chart Colors
        self.bullish_color = QColor(gt("chart_bullish_color", "#26a69a" if "Orange" in theme_name else "#4ade80"))
        self._basic_helper._update_color_button(self.bullish_color_btn, self.bullish_color)

        self.bearish_color = QColor(gt("chart_bearish_color", "#ef5350" if "Orange" in theme_name else "#f87171"))
        self._basic_helper._update_color_button(self.bearish_color_btn, self.bearish_color)

        self.background_color = QColor(gt("chart_background_color", "#1e1e1e" if "Orange" in theme_name else "#09090b"))
        self._basic_helper._update_color_button(self.background_color_btn, self.background_color)

        # Background Image
        self.background_image_path = gt("chart_background_image", "")
        if self.background_image_path:
            import os
            filename = os.path.basename(self.background_image_path)
            self.background_image_label.setText(filename)
            self.background_image_label.setStyleSheet("color: #26a69a;")
        else:
            self.background_image_label.setText("Kein Bild ausgewählt")
            self.background_image_label.setStyleSheet("color: #888; font-style: italic;")

        bg_opacity = int(gt("chart_background_image_opacity", 30))
        self.background_image_opacity_slider.setValue(bg_opacity)
        self.background_image_opacity_label.setText(f"{bg_opacity}%")

        # Candle Border Radius
        border_radius = int(gt("chart_candle_border_radius", 0))
        self.candle_border_radius_slider.setValue(border_radius)
        self.candle_border_radius_label.setText(f"{border_radius} px")

        # Icon Collection Source
        self.icon_dir_path = gt("icon_dir", "")
        if self.icon_dir_path:
            self.icon_dir_label.setText(self.icon_dir_path)
            self.icon_dir_label.setStyleSheet("color: #F29F05; font-size: 10px;")
            self.icon_dir_label.setToolTip(self.icon_dir_path)
        else:
            self.icon_dir_label.setText("Standard (Projekt-Assets)")
            self.icon_dir_label.setStyleSheet("color: #888; font-style: italic;")
            self.icon_dir_label.setToolTip("")

        # Fix for type casting from QSettings
        val = gt("icon_force_white", True)
        if isinstance(val, str):
            val = val.lower() == 'true'
        self.icon_force_white_check.setChecked(bool(val))
