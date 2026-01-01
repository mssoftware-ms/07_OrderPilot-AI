"""Toolbar Mixin for TradingApplication.

Contains toolbar creation and data provider list management.
"""

import logging

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QToolBar,
)

from src.config.loader import config_manager

from ..icons import get_icon

logger = logging.getLogger(__name__)


class ToolbarMixin:
    """Mixin providing toolbar functionality for TradingApplication."""

    def create_toolbar(self):
        """Create the application toolbar (two rows)."""
        # ========== ROW 1: Connection, Broker, Mode, Data Provider ==========
        toolbar1 = QToolBar("Main Toolbar - Row 1")
        toolbar1.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar1)

        # Connect/Disconnect actions
        connect_action = QAction(get_icon("connect"), "Connect", self)
        connect_action.setToolTip("Connect to broker")
        connect_action.triggered.connect(self.connect_broker)
        toolbar1.addAction(connect_action)

        disconnect_action = QAction(get_icon("disconnect"), "Disconnect", self)
        disconnect_action.setToolTip("Disconnect from broker")
        disconnect_action.triggered.connect(self.disconnect_broker)
        toolbar1.addAction(disconnect_action)

        toolbar1.addSeparator()

        # Broker selector
        broker_label = QLabel("Broker: ")
        broker_label.setToolTip("Select your broker for trading")
        toolbar1.addWidget(broker_label)

        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["Mock Broker", "IBKR", "Trade Republic"])
        self.broker_combo.setToolTip(
            "Choose broker:\n"
            "• Mock Broker - Testing with simulated trading\n"
            "• IBKR - Interactive Brokers (TWS/Gateway required)\n"
            "• Trade Republic - Mobile trading platform"
        )
        toolbar1.addWidget(self.broker_combo)

        toolbar1.addSeparator()

        # Trading Mode Selector
        mode_label = QLabel("Mode: ")
        mode_label.setToolTip("Trading Mode - CRITICAL safety setting!")
        mode_label.setStyleSheet("font-weight: bold; color: #FFA500;")
        toolbar1.addWidget(mode_label)

        self.trading_mode_combo = QComboBox()
        self.trading_mode_combo.addItems(["Backtest", "Paper", "Live"])
        self.trading_mode_combo.setCurrentText("Backtest")
        self.trading_mode_combo.setToolTip(
            "CRITICAL SAFETY SETTING\n\n"
            "• Backtest - Historical simulation (NO real orders)\n"
            "• Paper - Real-time simulation (NO real money)\n"
            "• Live - REAL TRADING with REAL MONEY!"
        )
        self.trading_mode_combo.setStyleSheet("""
            QComboBox {
                font-weight: bold;
                padding: 5px 10px;
                border: 2px solid #FFA500;
                border-radius: 3px;
                background-color: #2a2a2a;
                color: #FFA500;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox:hover { background-color: #3a3a3a; border-color: #FFD700; }
        """)
        self.trading_mode_combo.currentTextChanged.connect(self._on_trading_mode_changed)
        toolbar1.addWidget(self.trading_mode_combo)

        self.current_trading_mode = "Backtest"

        toolbar1.addSeparator()

        # Market Data Provider selector
        data_provider_label = QLabel("Market Data: ")
        data_provider_label.setToolTip("Select market data provider")
        toolbar1.addWidget(data_provider_label)

        self.data_provider_combo = QComboBox()
        self.data_provider_combo.setToolTip(
            "Select market data source:\n"
            "• Auto - Use priority order from settings\n"
            "• Database - Cached historical data\n"
            "• Alpaca - US stocks (free tier: IEX data)\n"
            "• Yahoo Finance - Free historical data"
        )
        self.data_provider_combo.currentTextChanged.connect(self.on_data_provider_changed)
        toolbar1.addWidget(self.data_provider_combo)

        # Refresh action
        refresh_action = QAction(get_icon("refresh"), "Refresh", self)
        refresh_action.setToolTip("Refresh market data")
        refresh_action.triggered.connect(self.refresh_market_data)
        toolbar1.addAction(refresh_action)

        toolbar1.addSeparator()

        # Status indicators (Row 1)
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        self.connection_status.setToolTip("Broker connection status")
        toolbar1.addWidget(self.connection_status)

        self.ai_status = QLabel("AI: Ready")
        self.ai_status.setToolTip("AI service status")
        toolbar1.addWidget(self.ai_status)

        self.crypto_status = QLabel("Crypto: Off")
        self.crypto_status.setStyleSheet("color: gray;")
        self.crypto_status.setToolTip("Live Crypto Data Stream Status")
        toolbar1.addWidget(self.crypto_status)

        # ========== ROW 2: Live Data, Pre-Trade, Quick Actions ==========
        toolbar2 = QToolBar("Main Toolbar - Row 2")
        toolbar2.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar2)

        # Live Data Toggle
        self.live_data_toggle = QPushButton("Live Data: OFF")
        self.live_data_toggle.setCheckable(True)
        self.live_data_toggle.setToolTip(
            "Toggle live market data in paper mode\n"
            "• ON: Use real-time market data from providers\n"
            "• OFF: Use cached/simulated data"
        )
        self.live_data_toggle.clicked.connect(self.toggle_live_data)
        toolbar2.addWidget(self.live_data_toggle)

        toolbar2.addSeparator()

        # ===== PRE-TRADE ANALYSIS BUTTON (KEY FEATURE!) =====
        self.pre_trade_button = QPushButton("🎯 Pre-Trade")
        self.pre_trade_button.setToolTip(
            "Pre-Trade Analyse\n\n"
            "Öffnet Multi-Timeframe Charts für die Analyse\n"
            "des übergeordneten Trends VOR dem Trade.\n\n"
            "Shortcut: Ctrl+Shift+T"
        )
        self.pre_trade_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.pre_trade_button.clicked.connect(self._on_open_pre_trade_analysis)
        toolbar2.addWidget(self.pre_trade_button)

        toolbar2.addSeparator()

        # Quick actions
        new_order_action = QAction(get_icon("order"), "New Order", self)
        new_order_action.setToolTip("Place new order")
        new_order_action.triggered.connect(self.show_order_dialog)
        toolbar2.addAction(new_order_action)

        backtest_action = QAction(get_icon("backtest"), "Backtest", self)
        backtest_action.setToolTip("Run backtest")
        backtest_action.triggered.connect(self.show_backtest_dialog)
        toolbar2.addAction(backtest_action)

        ai_backtest_action = QAction(get_icon("ai"), "AI Backtest", self)
        ai_backtest_action.setToolTip("AI-powered backtest analysis")
        ai_backtest_action.triggered.connect(self.show_ai_backtest_dialog)
        toolbar2.addAction(ai_backtest_action)

        param_opt_action = QAction(get_icon("optimize"), "Optimize", self)
        param_opt_action.setToolTip("Parameter optimization")
        param_opt_action.triggered.connect(self.show_parameter_optimization_dialog)
        toolbar2.addAction(param_opt_action)

        settings_action = QAction(get_icon("settings"), "Settings", self)
        settings_action.setToolTip("Open settings")
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar2.addAction(settings_action)

    def update_data_provider_list(self):
        """Update the list of available market data providers."""
        try:
            available_sources = self.history_manager.get_available_sources()

            # Collapse Alpaca variants
            alpaca_available = "alpaca" in available_sources or "alpaca_crypto" in available_sources
            filtered_sources = [
                s for s in available_sources
                if s not in ("alpaca_crypto",)
            ]
            if alpaca_available and "alpaca" not in filtered_sources:
                filtered_sources.append("alpaca")

            self.data_provider_combo.clear()

            # Add "Auto" option
            self.data_provider_combo.addItem("Auto (Priority Order)", None)

            provider_display_names = {
                "database": "Database (Cache)",
                "ibkr": "Interactive Brokers",
                "alpaca": "Alpaca (Stocks & Crypto)",
                "alpha_vantage": "Alpha Vantage",
                "finnhub": "Finnhub",
                "yahoo": "Yahoo Finance"
            }

            for source in filtered_sources:
                display_name = provider_display_names.get(source, source.title())
                self.data_provider_combo.addItem(f"{display_name}", source)

            # Check for disabled providers
            profile = config_manager.load_profile()
            market_config = profile.market_data

            if market_config.alpaca_enabled and "alpaca" not in filtered_sources:
                self.data_provider_combo.addItem(
                    "Alpaca (Configure API Keys)",
                    "alpaca_disabled"
                )

            if market_config.alpha_vantage_enabled and "alpha_vantage" not in available_sources:
                self.data_provider_combo.addItem(
                    "Alpha Vantage (Configure API Key)",
                    "alpha_vantage_disabled"
                )

            if market_config.finnhub_enabled and "finnhub" not in available_sources:
                self.data_provider_combo.addItem(
                    "Finnhub (Configure API Key)",
                    "finnhub_disabled"
                )

            # Yahoo should always be available
            if market_config.yahoo_enabled and "yahoo" not in available_sources:
                from src.core.market_data.history_provider import DataSource, YahooFinanceProvider
                self.history_manager.register_provider(DataSource.YAHOO, YahooFinanceProvider())
                self.data_provider_combo.addItem("Yahoo Finance", "yahoo")
                logger.info("Registered Yahoo Finance provider")

            # Load saved preference
            saved_provider = self.settings.value("market_data_provider", "Auto (Priority Order)")
            index = self.data_provider_combo.findText(saved_provider)
            if index >= 0:
                self.data_provider_combo.setCurrentIndex(index)

            logger.info(f"Available market data providers: {filtered_sources}")

        except Exception as e:
            logger.error(f"Failed to update data provider list: {e}")

    def on_data_provider_changed(self, provider_name: str):
        """Handle data provider selection changes."""
        try:
            index = self.data_provider_combo.currentIndex()
            provider_key = self.data_provider_combo.itemData(index)

            # Disabled providers prompt user to configure keys
            if isinstance(provider_key, str) and provider_key.endswith("_disabled"):
                if hasattr(self, "status_bar"):
                    self.status_bar.showMessage(
                        "Provider requires API keys. Open Settings -> Market Data.",
                        6000,
                    )
                logger.warning(f"Selected disabled provider: {provider_key}")
                if hasattr(self, "show_settings_dialog"):
                    self.show_settings_dialog()
                return

            # Persist selection for next start
            if hasattr(self, "settings"):
                self.settings.setValue("market_data_provider", self.data_provider_combo.currentText())

            logger.info(f"Selected market data provider: {provider_key}")

        except Exception as e:
            logger.error(f"Failed to handle data provider change: {e}", exc_info=True)
