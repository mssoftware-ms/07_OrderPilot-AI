"""Settings Dialog Tab Creation Mixin.

Contains tab creation methods for SettingsDialog.
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsTabsMixin:
    """Mixin providing tab creation methods for SettingsDialog."""

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        layout.addRow("Theme:", self.theme_combo)

        # Auto-connect broker
        self.auto_connect_check = QCheckBox("Auto-connect to broker on startup")
        layout.addRow(self.auto_connect_check)

        # Default broker
        self.default_broker_combo = QComboBox()
        self.default_broker_combo.addItems(["Mock Broker", "Interactive Brokers", "Trade Republic"])
        layout.addRow("Default Broker:", self.default_broker_combo)

        return tab

    def _create_trading_tab(self) -> QWidget:
        """Create trading settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.manual_approval = QCheckBox("Require manual approval for orders")
        self.manual_approval.setChecked(True)
        layout.addRow(self.manual_approval)

        self.confirm_cancel = QCheckBox("Confirm before canceling orders")
        self.confirm_cancel.setChecked(True)
        layout.addRow(self.confirm_cancel)

        # Max order size
        self.max_order_size = QDoubleSpinBox()
        self.max_order_size.setRange(100, 100000)
        self.max_order_size.setValue(10000)
        self.max_order_size.setPrefix("€")
        layout.addRow("Max Order Size:", self.max_order_size)

        # Risk tolerance
        self.risk_combo = QComboBox()
        self.risk_combo.addItems(["Conservative", "Moderate", "Aggressive"])
        layout.addRow("Risk Tolerance:", self.risk_combo)

        return tab

    def _create_broker_tab(self) -> QWidget:
        """Create broker settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # IBKR Settings
        layout.addRow(QLabel("<b>Interactive Brokers (IBKR)</b>"))

        self.ibkr_host = QLineEdit()
        self.ibkr_host.setPlaceholderText("localhost or IP address")
        layout.addRow("IBKR Host:", self.ibkr_host)

        self.ibkr_port = QComboBox()
        self.ibkr_port.addItems(["7497 (Paper)", "7496 (Live)"])
        layout.addRow("IBKR Port:", self.ibkr_port)

        self.ibkr_client_id = QComboBox()
        self.ibkr_client_id.addItems(["1", "2", "3", "4", "5"])
        layout.addRow("IBKR Client ID:", self.ibkr_client_id)

        # Trade Republic Settings
        layout.addRow(QLabel("<b>Trade Republic</b>"))

        self.tr_phone = QLineEdit()
        self.tr_phone.setPlaceholderText("+49...")
        layout.addRow("Phone Number:", self.tr_phone)

        self.tr_pin = QLineEdit()
        self.tr_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.tr_pin.setPlaceholderText("4-digit PIN")
        self.tr_pin.setMaxLength(4)
        layout.addRow("PIN:", self.tr_pin)

        # Bitunix Settings
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<b>Bitunix Futures</b>"))

        self.bitunix_broker_enabled = QCheckBox("Enable Bitunix for trading")
        layout.addRow(self.bitunix_broker_enabled)

        bitunix_note = QLabel(
            "<i>Note: Configure API keys in Market Data → Bitunix tab</i>"
        )
        bitunix_note.setWordWrap(True)
        layout.addRow(bitunix_note)

        return tab

    def _create_market_data_tab(self) -> QWidget:
        """Create market data settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.market_tabs = QTabWidget()
        layout.addWidget(self.market_tabs)
        self._add_market_provider_tabs()

        # Preferred data source behavior
        self.prefer_live_broker = QCheckBox(
            "Prefer live broker market data when connected"
        )
        layout.addWidget(self.prefer_live_broker)

        # Live data in paper mode
        self.enable_live_data_paper = QCheckBox(
            "Enable live market data in paper trading mode"
        )
        self.enable_live_data_paper.setToolTip(
            "When enabled, live market data from configured providers "
            "will be used even in paper trading mode"
        )
        layout.addWidget(self.enable_live_data_paper)

        layout.addStretch()

        return tab

    def _create_ai_tab(self) -> QWidget:
        """Create AI settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addLayout(self._build_general_ai_layout())
        layout.addWidget(self._build_ai_provider_tabs())

        # Task routing info
        routing_info = QLabel(
            "<b>Note:</b> Task routing is configured in config/ai_providers.yaml. "
            "Different tasks can use different models automatically."
        )
        routing_info.setWordWrap(True)
        layout.addWidget(routing_info)

        layout.addStretch()

        return tab

    def _add_market_provider_tabs(self) -> None:
        self.market_tabs.addTab(self._build_alpha_tab(), "Alpha Vantage")
        self.market_tabs.addTab(self._build_finnhub_tab(), "Finnhub")
        self.market_tabs.addTab(self._build_yahoo_tab(), "Yahoo Finance")
        self.market_tabs.addTab(self._build_alpaca_tab(), "Alpaca")
        self.market_tabs.addTab(self._build_bitunix_tab(), "Bitunix")

    def _build_alpha_tab(self) -> QWidget:
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
        return alpha_tab

    def _build_finnhub_tab(self) -> QWidget:
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
        return finnhub_tab

    def _build_yahoo_tab(self) -> QWidget:
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
        return yahoo_tab

    def _build_alpaca_tab(self) -> QWidget:
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
        return alpaca_tab

    def _build_bitunix_tab(self) -> QWidget:
        """Create Bitunix Futures settings tab."""
        bitunix_tab = QWidget()
        bitunix_layout = QFormLayout(bitunix_tab)

        self.bitunix_enabled = QCheckBox("Enable Bitunix Futures provider")
        bitunix_layout.addRow(self.bitunix_enabled)

        self.bitunix_api_key = QLineEdit()
        self.bitunix_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.bitunix_api_key.setPlaceholderText("Enter Bitunix API key")
        bitunix_layout.addRow("API Key:", self.bitunix_api_key)

        self.bitunix_api_secret = QLineEdit()
        self.bitunix_api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.bitunix_api_secret.setPlaceholderText("Enter Bitunix API secret")
        bitunix_layout.addRow("API Secret:", self.bitunix_api_secret)

        self.bitunix_testnet = QCheckBox("Use Testnet (Recommended for testing)")
        self.bitunix_testnet.setChecked(True)
        self.bitunix_testnet.setToolTip(
            "When enabled, uses Bitunix testnet environment for safe testing. "
            "Uncheck only when you want to trade with real money!"
        )
        bitunix_layout.addRow(self.bitunix_testnet)

        bitunix_info = QLabel(
            "<b>Bitunix Futures Trading</b><br>"
            "Provides crypto futures (perpetual contracts) trading and market data.<br>"
            "<br>"
            "<b>⚠️ IMPORTANT:</b><br>"
            "• Testnet is enabled by default for safety<br>"
            "• Get API keys from: <a href='https://www.bitunix.com/api'>https://www.bitunix.com/api</a><br>"
            "• Supports USDT-margined perpetual contracts<br>"
            "• Trading fees: 0.02% maker / 0.06% taker"
        )
        bitunix_info.setWordWrap(True)
        bitunix_info.setOpenExternalLinks(True)
        bitunix_layout.addRow(bitunix_info)

        return bitunix_tab

    def _build_general_ai_layout(self) -> QFormLayout:
        general_ai_layout = QFormLayout()

        self.ai_enabled = QCheckBox("Enable AI features")
        self.ai_enabled.setChecked(True)
        general_ai_layout.addRow(self.ai_enabled)

        self.ai_default_provider = QComboBox()
        self.ai_default_provider.addItems(["Anthropic", "OpenAI", "Gemini"])
        general_ai_layout.addRow("Default Provider:", self.ai_default_provider)

        self.ai_budget = QDoubleSpinBox()
        self.ai_budget.setRange(1, 1000)
        self.ai_budget.setValue(50)
        self.ai_budget.setPrefix("€")
        general_ai_layout.addRow("Monthly Budget:", self.ai_budget)
        return general_ai_layout

    def _build_ai_provider_tabs(self) -> QTabWidget:
        provider_tabs = QTabWidget()
        provider_tabs.addTab(self._build_openai_tab(), "OpenAI")
        provider_tabs.addTab(self._build_anthropic_tab(), "Anthropic")
        provider_tabs.addTab(self._build_gemini_tab(), "Gemini")
        return provider_tabs

    def _build_openai_tab(self) -> QWidget:
        openai_tab = QWidget()
        openai_layout = QFormLayout(openai_tab)

        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_api_key.setPlaceholderText("Enter OpenAI API Key")
        openai_layout.addRow("API Key:", self.openai_api_key)

        self.openai_model = QComboBox()
        self.openai_model.addItems(
            [
                "gpt-5.1 (Thinking Mode)",
                "gpt-5.1-chat-latest (Instant)",
                "gpt-4.1-2025-04-14 (GPT-4.1 Full)",
                "gpt-4.1-mini-2025-04-14 (GPT-4.1 Mini)",
                "gpt-4.1-nano-2025-04-14 (GPT-4.1 Nano - Fastest)",
            ]
        )
        openai_layout.addRow("Default Model:", self.openai_model)

        openai_info = QLabel(
            "GPT-5.1: Adaptive reasoning modes for complex tasks. "
            "GPT-4.1: 1M token context, excellent for coding. "
            "GPT-4.1 Nano: Fastest and cheapest for low-latency tasks. "
            "Set OPENAI_API_KEY environment variable for automatic configuration."
        )
        openai_info.setWordWrap(True)
        openai_layout.addRow(openai_info)
        return openai_tab

    def _build_anthropic_tab(self) -> QWidget:
        anthropic_tab = QWidget()
        anthropic_layout = QFormLayout(anthropic_tab)

        self.anthropic_api_key = QLineEdit()
        self.anthropic_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_api_key.setPlaceholderText("Enter Anthropic API Key")
        anthropic_layout.addRow("API Key:", self.anthropic_api_key)

        self.anthropic_model = QComboBox()
        self.anthropic_model.addItems(
            ["claude-sonnet-4-5-20250929 (Recommended)", "claude-sonnet-4-5 (Latest)"]
        )
        anthropic_layout.addRow("Default Model:", self.anthropic_model)

        anthropic_info = QLabel(
            "Anthropic Claude Sonnet 4.5 excels at complex reasoning, code analysis, "
            "and technical tasks. 1M token context window. "
            "Set ANTHROPIC_API_KEY environment variable for automatic configuration."
        )
        anthropic_info.setWordWrap(True)
        anthropic_layout.addRow(anthropic_info)
        return anthropic_tab

    def _build_gemini_tab(self) -> QWidget:
        gemini_tab = QWidget()
        gemini_layout = QFormLayout(gemini_tab)

        self.gemini_api_key = QLineEdit()
        self.gemini_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_api_key.setPlaceholderText("Enter Gemini API Key")
        gemini_layout.addRow("API Key:", self.gemini_api_key)

        self.gemini_model = QComboBox()
        self.gemini_model.addItems(
            [
                "gemini-2.0-flash-exp (Latest)",
                "gemini-1.5-pro (Most Capable)",
                "gemini-1.5-flash (Fast)",
            ]
        )
        gemini_layout.addRow("Default Model:", self.gemini_model)

        gemini_info = QLabel(
            "Google Gemini offers excellent performance at competitive pricing. "
            "gemini-2.0-flash-exp is the latest experimental model. "
            "gemini-1.5-pro has the largest context (2M tokens). "
            "Set GEMINI_API_KEY environment variable for automatic configuration."
        )
        gemini_info.setWordWrap(True)
        gemini_layout.addRow(gemini_info)
        return gemini_tab

    def _create_notifications_tab(self) -> QWidget:
        """Create notifications settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.order_filled_notif = QCheckBox("Notify on order fills")
        self.order_filled_notif.setChecked(True)
        layout.addRow(self.order_filled_notif)

        self.alert_notif = QCheckBox("Notify on alerts")
        self.alert_notif.setChecked(True)
        layout.addRow(self.alert_notif)

        self.connection_notif = QCheckBox("Notify on connection changes")
        self.connection_notif.setChecked(False)
        layout.addRow(self.connection_notif)

        return tab
