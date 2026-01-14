"""Settings Dialog for OrderPilot-AI Trading Application.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- settings_tabs_mixin.py: Tab creation methods
- settings_dialog.py: Main SettingsDialog class (this file)
"""

import logging
import os

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor
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
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        """Initialize the settings dialog UI."""
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # Create tabs using mixin methods
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_trading_tab(), "Trading")
        tabs.addTab(self._create_broker_tab(), "Brokers")
        tabs.addTab(self._create_market_data_tab(), "Market Data")
        tabs.addTab(self._create_ai_tab(), "AI")
        tabs.addTab(self._create_heatmap_tab(), "Heatmap")
        tabs.addTab(self._create_notifications_tab(), "Notifications")

        layout.addWidget(tabs)

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

        # General
        self._set_combo_value(self.theme_combo, self.settings.value("theme", "Dark"))

        # UI Customization
        ui_btn_border_color_name = self.settings.value("ui_btn_border_color", "#3A3D43")
        self.ui_btn_border_color = QColor(ui_btn_border_color_name)
        if hasattr(self, '_basic_helper'):
            self._basic_helper._update_color_button(self.ui_btn_border_color_btn, self.ui_btn_border_color)

        ui_font_color_name = self.settings.value("ui_font_color", "#EAECEF")
        self.ui_font_color = QColor(ui_font_color_name)
        if hasattr(self, '_basic_helper'):
            self._basic_helper._update_color_button(self.ui_font_color_btn, self.ui_font_color)

        current_font = self.settings.value("ui_font_family", "Segoe UI")
        self.ui_font_family_combo.setCurrentFont(self.ui_font_family_combo.currentFont()) # Set default first
        # Find font in combo
        idx = -1
        # Iterate to find the font family match
        for i in range(self.ui_font_family_combo.count()):
            if self.ui_font_family_combo.itemText(i) == current_font:
                idx = i
                break
        if idx >= 0:
            self.ui_font_family_combo.setCurrentIndex(idx)

        self.ui_font_size_spin.setValue(
            self.settings.value("ui_font_size", 14, type=int)
        )

        self.auto_connect_check.setChecked(
            self.settings.value("auto_connect", False, type=bool)
        )
        self._set_combo_value(
            self.default_broker_combo,
            self.settings.value("default_broker", "Trade Republic"),
        )
        # Console Debug Level
        self._set_combo_value(
            self.console_debug_level,
            self.settings.value("console_debug_level", "INFO"),
        )

        # Issue #34: Chart Colors
        bullish_color_name = self.settings.value("chart_bullish_color", "#26a69a")
        self.bullish_color = QColor(bullish_color_name)
        if hasattr(self, '_basic_helper'):
            self._basic_helper._update_color_button(self.bullish_color_btn, self.bullish_color)

        bearish_color_name = self.settings.value("chart_bearish_color", "#ef5350")
        self.bearish_color = QColor(bearish_color_name)
        if hasattr(self, '_basic_helper'):
            self._basic_helper._update_color_button(self.bearish_color_btn, self.bearish_color)

        background_color_name = self.settings.value("chart_background_color", "#1e1e1e")
        self.background_color = QColor(background_color_name)
        if hasattr(self, '_basic_helper'):
            self._basic_helper._update_color_button(self.background_color_btn, self.background_color)

        # Issue #35: Background Image
        bg_image_path = self.settings.value("chart_background_image", "")
        self.background_image_path = bg_image_path
        if bg_image_path:
            import os
            filename = os.path.basename(bg_image_path)
            self.background_image_label.setText(filename)
            self.background_image_label.setStyleSheet("color: #26a69a;")
        else:
            self.background_image_label.setText("Kein Bild ausgewählt")
            self.background_image_label.setStyleSheet("color: #888; font-style: italic;")

        bg_opacity = self.settings.value("chart_background_image_opacity", 30, type=int)
        self.background_image_opacity_slider.setValue(bg_opacity)
        self.background_image_opacity_label.setText(f"{bg_opacity}%")

        # Issue #39/#49: Load Candle Border Radius (0.25px increments)
        border_radius = self.settings.value("chart_candle_border_radius", 0, type=int)
        self.candle_border_radius_slider.setValue(border_radius)
        # Display with 2 decimal places (value/4 to convert slider steps to pixels)
        pixels = border_radius / 4.0
        self.candle_border_radius_label.setText(f"{pixels:.2f} px")

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
            "bitunix_api_secret",
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

        # Heatmap settings
        if hasattr(self, '_heatmap_helper'):
            self._heatmap_helper.load_heatmap_settings()

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
            # General
            self.settings.setValue("theme", self.theme_combo.currentText())
            
            # UI Customization
            self.settings.setValue("ui_btn_border_color", self.ui_btn_border_color.name())
            self.settings.setValue("ui_font_color", self.ui_font_color.name())
            self.settings.setValue("ui_font_family", self.ui_font_family_combo.currentFont().family())
            self.settings.setValue("ui_font_size", self.ui_font_size_spin.value())

            self.settings.setValue("auto_connect", self.auto_connect_check.isChecked())
            self.settings.setValue("default_broker", self.default_broker_combo.currentText())
            self.settings.setValue("console_debug_level", self.console_debug_level.currentText())

            # Issue #34: Save Chart Colors
            self.settings.setValue("chart_bullish_color", self.bullish_color.name())
            self.settings.setValue("chart_bearish_color", self.bearish_color.name())
            self.settings.setValue("chart_background_color", self.background_color.name())

            # Issue #35: Save Background Image Settings
            self.settings.setValue("chart_background_image", self.background_image_path)
            self.settings.setValue("chart_background_image_opacity", self.background_image_opacity_slider.value())

            # Issue #39: Save Candle Border Radius
            self.settings.setValue("chart_candle_border_radius", self.candle_border_radius_slider.value())

            # Clear custom colors cache to force reload in charts
            from src.ui.widgets.chart_shared.theme_utils import clear_custom_colors_cache
            clear_custom_colors_cache()
            logger.info("Custom chart colors and background image saved, cache cleared")

            # Issues #34, #37: Refresh colors in all open charts
            try:
                from src.ui.chart_window_manager import get_chart_window_manager
                chart_mgr = get_chart_window_manager()
                if chart_mgr:
                    chart_mgr.refresh_all_chart_colors()
                    logger.info("All open charts refreshed with new colors")
            except Exception as exc:
                logger.warning(f"Could not refresh chart colors: {exc}")

            # Apply console debug level immediately
            self._apply_console_debug_level()

            # Trading
            self.settings.setValue("manual_approval", self.manual_approval.isChecked())
            self.settings.setValue("confirm_cancel", self.confirm_cancel.isChecked())
            self.settings.setValue("max_order_size", self.max_order_size.value())
            self.settings.setValue("risk_tolerance", self.risk_combo.currentText())

            # AI
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
            logger.info("AI service reset to apply new provider/model settings")

            # Save API keys
            self._save_api_keys()

            # Broker Settings
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
                    QMessageBox.warning(
                        self, "PIN Storage",
                        f"Could not store Trade Republic PIN securely:\n{str(e)}\n\n"
                        "You may need to re-enter it when connecting."
                    )

            # Market Data provider toggles
            self._save_market_data_settings()

            # Live data in paper mode
            self.settings.setValue("live_data_enabled", self.enable_live_data_paper.isChecked())

            # Notifications
            self.settings.setValue("order_filled_notif", self.order_filled_notif.isChecked())
            self.settings.setValue("alert_notif", self.alert_notif.isChecked())
            self.settings.setValue("connection_notif", self.connection_notif.isChecked())

            # Heatmap settings
            if hasattr(self, '_heatmap_helper'):
                self._heatmap_helper.save_heatmap_settings()

            # Sync settings to disk
            self.settings.sync()

            QMessageBox.information(
                self, "Settings Saved",
                "Settings have been saved successfully.\n\n"
                "Some changes may require restarting the application."
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save settings:\n{str(e)}"
            )

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
                config_manager.set_credential("bitunix_api_secret", bitunix_secret)
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
