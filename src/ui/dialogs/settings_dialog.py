"""Settings Dialog for OrderPilot-AI Trading Application."""

import logging
import os

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.config.loader import config_manager

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
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

        # General tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        general_layout.addRow("Theme:", self.theme_combo)

        # Auto-connect broker
        self.auto_connect_check = QCheckBox("Auto-connect to broker on startup")
        general_layout.addRow(self.auto_connect_check)

        # Default broker
        self.default_broker_combo = QComboBox()
        self.default_broker_combo.addItems(["Mock Broker", "Interactive Brokers", "Trade Republic"])
        general_layout.addRow("Default Broker:", self.default_broker_combo)

        tabs.addTab(general_tab, "General")

        # Trading tab
        trading_tab = QWidget()
        trading_layout = QFormLayout(trading_tab)

        self.manual_approval = QCheckBox("Require manual approval for orders")
        self.manual_approval.setChecked(True)
        trading_layout.addRow(self.manual_approval)

        self.confirm_cancel = QCheckBox("Confirm before canceling orders")
        self.confirm_cancel.setChecked(True)
        trading_layout.addRow(self.confirm_cancel)

        # Max order size
        self.max_order_size = QDoubleSpinBox()
        self.max_order_size.setRange(100, 100000)
        self.max_order_size.setValue(10000)
        self.max_order_size.setPrefix("€")
        trading_layout.addRow("Max Order Size:", self.max_order_size)

        # Risk tolerance
        self.risk_combo = QComboBox()
        self.risk_combo.addItems(["Conservative", "Moderate", "Aggressive"])
        trading_layout.addRow("Risk Tolerance:", self.risk_combo)

        tabs.addTab(trading_tab, "Trading")

        # Broker Settings tab
        broker_tab = QWidget()
        broker_layout = QFormLayout(broker_tab)

        # IBKR Settings
        broker_layout.addRow(QLabel("<b>Interactive Brokers (IBKR)</b>"))

        self.ibkr_host = QLineEdit()
        self.ibkr_host.setPlaceholderText("localhost or IP address")
        broker_layout.addRow("IBKR Host:", self.ibkr_host)

        self.ibkr_port = QComboBox()
        self.ibkr_port.addItems(["7497 (Paper)", "7496 (Live)"])
        broker_layout.addRow("IBKR Port:", self.ibkr_port)

        self.ibkr_client_id = QComboBox()
        self.ibkr_client_id.addItems(["1", "2", "3", "4", "5"])
        broker_layout.addRow("IBKR Client ID:", self.ibkr_client_id)

        # Trade Republic Settings
        broker_layout.addRow(QLabel("<b>Trade Republic</b>"))

        self.tr_phone = QLineEdit()
        self.tr_phone.setPlaceholderText("+49...")
        broker_layout.addRow("Phone Number:", self.tr_phone)

        self.tr_pin = QLineEdit()
        self.tr_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.tr_pin.setPlaceholderText("4-digit PIN")
        self.tr_pin.setMaxLength(4)
        broker_layout.addRow("PIN:", self.tr_pin)

        tabs.addTab(broker_tab, "Brokers")

        # Market Data tab
        market_tab = QWidget()
        market_layout = QVBoxLayout(market_tab)

        self.market_tabs = QTabWidget()
        market_layout.addWidget(self.market_tabs)

        # Alpha Vantage provider settings
        alpha_tab = QWidget()
        alpha_layout = QFormLayout(alpha_tab)

        self.alpha_enabled = QCheckBox("Enable Alpha Vantage provider")
        alpha_layout.addRow(self.alpha_enabled)

        self.alpha_api_key = QLineEdit()
        self.alpha_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.alpha_api_key.setPlaceholderText("Enter Alpha Vantage API key")
        alpha_layout.addRow("API Key:", self.alpha_api_key)

        alpha_info = QLabel(
            "Alpha Vantage free tier allows up to 5 requests per minute. "
            "Enable only if you entered a valid API key."
        )
        alpha_info.setWordWrap(True)
        alpha_layout.addRow(alpha_info)

        self.market_tabs.addTab(alpha_tab, "Alpha Vantage")

        # Finnhub provider settings
        finnhub_tab = QWidget()
        finnhub_layout = QFormLayout(finnhub_tab)

        self.finnhub_enabled = QCheckBox("Enable Finnhub provider")
        finnhub_layout.addRow(self.finnhub_enabled)

        self.finnhub_api_key = QLineEdit()
        self.finnhub_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.finnhub_api_key.setPlaceholderText("Enter Finnhub API key")
        finnhub_layout.addRow("API Key:", self.finnhub_api_key)

        finnhub_info = QLabel(
            "Finnhub offers real-time and historical market data. "
            "Free plans provide limited intraday history."
        )
        finnhub_info.setWordWrap(True)
        finnhub_layout.addRow(finnhub_info)

        self.market_tabs.addTab(finnhub_tab, "Finnhub")

        # Yahoo Finance provider settings
        yahoo_tab = QWidget()
        yahoo_layout = QFormLayout(yahoo_tab)

        self.yahoo_enabled = QCheckBox("Enable Yahoo Finance provider")
        yahoo_layout.addRow(self.yahoo_enabled)

        yahoo_info = QLabel(
            "Yahoo Finance data is fetched anonymously via public endpoints. "
            "No API key required."
        )
        yahoo_info.setWordWrap(True)
        yahoo_layout.addRow(yahoo_info)

        self.market_tabs.addTab(yahoo_tab, "Yahoo Finance")

        # Alpaca provider settings
        alpaca_tab = QWidget()
        alpaca_layout = QFormLayout(alpaca_tab)

        self.alpaca_enabled = QCheckBox("Enable Alpaca provider")
        alpaca_layout.addRow(self.alpaca_enabled)

        self.alpaca_api_key = QLineEdit()
        self.alpaca_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.alpaca_api_key.setPlaceholderText("Enter Alpaca API key")
        alpaca_layout.addRow("API Key:", self.alpaca_api_key)

        self.alpaca_api_secret = QLineEdit()
        self.alpaca_api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.alpaca_api_secret.setPlaceholderText("Enter Alpaca API secret")
        alpaca_layout.addRow("API Secret:", self.alpaca_api_secret)

        alpaca_info = QLabel(
            "Alpaca provides real-time and historical market data for US stocks. "
            "Free tier includes IEX real-time data with 200 requests/minute. "
            "Paper trading API keys can be used for testing."
        )
        alpaca_info.setWordWrap(True)
        alpaca_layout.addRow(alpaca_info)

        self.market_tabs.addTab(alpaca_tab, "Alpaca")

        # Preferred data source behavior
        self.prefer_live_broker = QCheckBox(
            "Prefer live broker market data when connected"
        )
        market_layout.addWidget(self.prefer_live_broker)

        # Live data in paper mode
        self.enable_live_data_paper = QCheckBox(
            "Enable live market data in paper trading mode"
        )
        self.enable_live_data_paper.setToolTip(
            "When enabled, live market data from configured providers "
            "will be used even in paper trading mode"
        )
        market_layout.addWidget(self.enable_live_data_paper)

        market_layout.addStretch()

        tabs.addTab(market_tab, "Market Data")

        # AI tab with multi-provider support
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)

        # General AI settings
        general_ai_layout = QFormLayout()

        self.ai_enabled = QCheckBox("Enable AI features")
        self.ai_enabled.setChecked(True)
        general_ai_layout.addRow(self.ai_enabled)

        # Default provider
        self.ai_default_provider = QComboBox()
        self.ai_default_provider.addItems(["Anthropic", "OpenAI", "Gemini"])
        general_ai_layout.addRow("Default Provider:", self.ai_default_provider)

        # Monthly budget
        self.ai_budget = QDoubleSpinBox()
        self.ai_budget.setRange(1, 1000)
        self.ai_budget.setValue(50)
        self.ai_budget.setPrefix("€")
        general_ai_layout.addRow("Monthly Budget:", self.ai_budget)

        ai_layout.addLayout(general_ai_layout)

        # Provider-specific settings in tabs
        provider_tabs = QTabWidget()

        # OpenAI settings
        openai_tab = QWidget()
        openai_layout = QFormLayout(openai_tab)

        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_api_key.setPlaceholderText("Enter OpenAI API Key")
        openai_layout.addRow("API Key:", self.openai_api_key)

        self.openai_model = QComboBox()
        self.openai_model.addItems([
            "gpt-5.1 (Thinking Mode)",
            "gpt-5.1-chat-latest (Instant)",
            "gpt-4.1-2025-04-14 (GPT-4.1 Full)",
            "gpt-4.1-mini-2025-04-14 (GPT-4.1 Mini)",
            "gpt-4.1-nano-2025-04-14 (GPT-4.1 Nano - Fastest)"
        ])
        openai_layout.addRow("Default Model:", self.openai_model)

        openai_info = QLabel(
            "GPT-5.1: Adaptive reasoning modes for complex tasks. "
            "GPT-4.1: 1M token context, excellent for coding. "
            "GPT-4.1 Nano: Fastest and cheapest for low-latency tasks. "
            "Set OPENAI_API_KEY environment variable for automatic configuration."
        )
        openai_info.setWordWrap(True)
        openai_layout.addRow(openai_info)

        provider_tabs.addTab(openai_tab, "OpenAI")

        # Anthropic settings
        anthropic_tab = QWidget()
        anthropic_layout = QFormLayout(anthropic_tab)

        self.anthropic_api_key = QLineEdit()
        self.anthropic_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_api_key.setPlaceholderText("Enter Anthropic API Key")
        anthropic_layout.addRow("API Key:", self.anthropic_api_key)

        self.anthropic_model = QComboBox()
        self.anthropic_model.addItems([
            "claude-sonnet-4-5-20250929 (Recommended)",
            "claude-sonnet-4-5 (Latest)"
        ])
        anthropic_layout.addRow("Default Model:", self.anthropic_model)

        anthropic_info = QLabel(
            "Anthropic Claude Sonnet 4.5 excels at complex reasoning, code analysis, "
            "and technical tasks. 1M token context window. "
            "Set ANTHROPIC_API_KEY environment variable for automatic configuration."
        )
        anthropic_info.setWordWrap(True)
        anthropic_layout.addRow(anthropic_info)

        provider_tabs.addTab(anthropic_tab, "Anthropic")

        # Gemini settings
        gemini_tab = QWidget()
        gemini_layout = QFormLayout(gemini_tab)

        self.gemini_api_key = QLineEdit()
        self.gemini_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_api_key.setPlaceholderText("Enter Gemini API Key")
        gemini_layout.addRow("API Key:", self.gemini_api_key)

        self.gemini_model = QComboBox()
        self.gemini_model.addItems([
            "gemini-2.0-flash-exp (Latest)",
            "gemini-1.5-pro (Most Capable)",
            "gemini-1.5-flash (Fast)"
        ])
        gemini_layout.addRow("Default Model:", self.gemini_model)

        gemini_info = QLabel(
            "Google Gemini offers excellent performance at competitive pricing. "
            "gemini-2.0-flash-exp is the latest experimental model. "
            "gemini-1.5-pro has the largest context (2M tokens). "
            "Set GEMINI_API_KEY environment variable for automatic configuration."
        )
        gemini_info.setWordWrap(True)
        gemini_layout.addRow(gemini_info)

        provider_tabs.addTab(gemini_tab, "Gemini")

        ai_layout.addWidget(provider_tabs)

        # Task routing info
        routing_info = QLabel(
            "<b>Note:</b> Task routing is configured in config/ai_providers.yaml. "
            "Different tasks can use different models automatically."
        )
        routing_info.setWordWrap(True)
        ai_layout.addWidget(routing_info)

        ai_layout.addStretch()

        tabs.addTab(ai_tab, "AI")

        # Notifications tab
        notif_tab = QWidget()
        notif_layout = QFormLayout(notif_tab)

        self.order_filled_notif = QCheckBox("Notify on order fills")
        self.order_filled_notif.setChecked(True)
        notif_layout.addRow(self.order_filled_notif)

        self.alert_notif = QCheckBox("Notify on alerts")
        self.alert_notif.setChecked(True)
        notif_layout.addRow(self.alert_notif)

        self.connection_notif = QCheckBox("Notify on connection changes")
        self.connection_notif.setChecked(False)
        notif_layout.addRow(self.connection_notif)

        tabs.addTab(notif_tab, "Notifications")

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

        # Don't load API keys from settings for security - user must enter them each session
        # Check if environment variables are set and show placeholder
        import os
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

            # Save OpenAI API key to secure keyring if provided
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

            # Save Anthropic API key to secure keyring if provided
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

            # Save Gemini API key to secure keyring if provided
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

            # Broker Settings
            self.settings.setValue("ibkr_host", self.ibkr_host.text().strip())
            self.settings.setValue("ibkr_port", self.ibkr_port.currentText())
            self.settings.setValue("ibkr_client_id", self.ibkr_client_id.currentText())
            self.settings.setValue("tr_phone", self.tr_phone.text().strip())

            # Save Trade Republic PIN to secure keyring if provided
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
            profile = config_manager.load_profile()
            market_config = profile.market_data
            market_config.alpaca_enabled = self.alpaca_enabled.isChecked()
            market_config.alpha_vantage_enabled = self.alpha_enabled.isChecked()
            market_config.finnhub_enabled = self.finnhub_enabled.isChecked()
            market_config.yahoo_enabled = self.yahoo_enabled.isChecked()
            market_config.prefer_live_broker = self.prefer_live_broker.isChecked()

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
