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
        theme = self.settings.value("theme", "Dark")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.auto_connect_check.setChecked(
            self.settings.value("auto_connect", False, type=bool)
        )

        default_broker = self.settings.value("default_broker", "Trade Republic")
        index = self.default_broker_combo.findText(default_broker)
        if index >= 0:
            self.default_broker_combo.setCurrentIndex(index)

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

        risk = self.settings.value("risk_tolerance", "Moderate")
        index = self.risk_combo.findText(risk)
        if index >= 0:
            self.risk_combo.setCurrentIndex(index)

        # AI
        self.ai_enabled.setChecked(
            self.settings.value("ai_enabled", True, type=bool)
        )

        # Default provider
        ai_provider = self.settings.value("ai_default_provider", "Anthropic")
        index = self.ai_default_provider.findText(ai_provider)
        if index >= 0:
            self.ai_default_provider.setCurrentIndex(index)

        # Check if environment variables are set
        if os.getenv("OPENAI_API_KEY"):
            self.openai_api_key.setPlaceholderText("API key loaded from environment variable")

        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_api_key.setPlaceholderText("API key loaded from environment variable")

        if os.getenv("GEMINI_API_KEY"):
            self.gemini_api_key.setPlaceholderText("API key loaded from environment variable")

        # OpenAI model
        openai_model = self.settings.value("openai_model", "gpt-5.1 (Thinking Mode)")
        index = self.openai_model.findText(openai_model)
        if index >= 0:
            self.openai_model.setCurrentIndex(index)

        # Anthropic model
        anthropic_model = self.settings.value("anthropic_model", "claude-sonnet-4-5-20250929 (Recommended)")
        index = self.anthropic_model.findText(anthropic_model)
        if index >= 0:
            self.anthropic_model.setCurrentIndex(index)

        # Gemini model
        gemini_model = self.settings.value("gemini_model", "gemini-2.0-flash-exp (Latest)")
        index = self.gemini_model.findText(gemini_model)
        if index >= 0:
            self.gemini_model.setCurrentIndex(index)

        self.ai_budget.setValue(
            self.settings.value("ai_budget", 50, type=float)
        )

        # Broker Settings
        self.ibkr_host.setText(
            self.settings.value("ibkr_host", "localhost")
        )

        ibkr_port = self.settings.value("ibkr_port", "7497 (Paper)")
        index = self.ibkr_port.findText(ibkr_port)
        if index >= 0:
            self.ibkr_port.setCurrentIndex(index)

        ibkr_client_id = self.settings.value("ibkr_client_id", "1")
        index = self.ibkr_client_id.findText(ibkr_client_id)
        if index >= 0:
            self.ibkr_client_id.setCurrentIndex(index)

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
        alpaca_key_exists = bool(config_manager.get_credential("alpaca_api_key"))
        alpaca_secret_exists = bool(config_manager.get_credential("alpaca_api_secret"))
        if alpaca_key_exists:
            self.alpaca_api_key.setPlaceholderText(
                "API key stored securely. Enter a new value to replace it."
            )
        else:
            self.alpaca_api_key.setPlaceholderText("Enter Alpaca API key")
        if alpaca_secret_exists:
            self.alpaca_api_secret.setPlaceholderText(
                "API secret stored securely. Enter a new value to replace it."
            )
        else:
            self.alpaca_api_secret.setPlaceholderText("Enter Alpaca API secret")

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

    def save_settings(self):
        """Save settings to QSettings and configuration."""
        try:
            # General
            self.settings.setValue("theme", self.theme_combo.currentText())
            self.settings.setValue("auto_connect", self.auto_connect_check.isChecked())
            self.settings.setValue("default_broker", self.default_broker_combo.currentText())

            # Trading
            self.settings.setValue("manual_approval", self.manual_approval.isChecked())
            self.settings.setValue("confirm_cancel", self.confirm_cancel.isChecked())
            self.settings.setValue("max_order_size", self.max_order_size.value())
            self.settings.setValue("risk_tolerance", self.risk_combo.currentText())

            # AI
            self.settings.setValue("ai_enabled", self.ai_enabled.isChecked())
            self.settings.setValue("ai_default_provider", self.ai_default_provider.currentText())
            self.settings.setValue("openai_model", self.openai_model.currentText())
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
        market_config.prefer_live_broker = self.prefer_live_broker.isChecked()

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

        # Persist profile changes
        config_manager.save_profile(profile)
