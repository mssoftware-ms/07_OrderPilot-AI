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
    """Mixin providing toolbar functionality for TradingApplication.
    
    REFACTORED for Workspace Manager:
    - Single toolbar row (removed Row 2)
    - Live Data toggle moved to Row 1
    - Quick Actions moved to Menu
    """

    def create_toolbar(self):
        """Create the application toolbar (single row for Workspace Manager)."""
        self._build_toolbar_row1()
        # Row 2 removed - Pre-Trade and Quick Actions are now in Menu
        # self._build_toolbar_row2()  # REMOVED

    def _build_toolbar_row1(self) -> None:
        toolbar1 = QToolBar("Main Toolbar")
        toolbar1.setObjectName("mainToolbar")
        toolbar1.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar1)

        self._add_connection_actions(toolbar1)
        toolbar1.addSeparator()
        self._add_broker_selector(toolbar1)
        toolbar1.addSeparator()
        self._add_trading_mode_selector(toolbar1)
        toolbar1.addSeparator()
        self._add_data_provider_selector(toolbar1)
        toolbar1.addAction(self._build_refresh_action())
        toolbar1.addSeparator()
        # Live Data toggle moved from Row 2
        self._add_live_data_toggle(toolbar1)
        toolbar1.addSeparator()
        self._add_status_indicators(toolbar1)

    def _build_toolbar_row2(self) -> None:
        """REMOVED - Row 2 items moved to Menu.
        
        Kept as stub for backward compatibility.
        Pre-Trade button -> Trading Menu
        Quick Actions -> Tools Menu
        """
        pass


    def _add_connection_actions(self, toolbar: QToolBar) -> None:
        connect_action = QAction(get_icon("connect"), "Connect", self)
        connect_action.setToolTip("Connect to broker")
        connect_action.triggered.connect(self.connect_broker)
        toolbar.addAction(connect_action)

        disconnect_action = QAction(get_icon("disconnect"), "Disconnect", self)
        disconnect_action.setToolTip("Disconnect from broker")
        disconnect_action.triggered.connect(self.disconnect_broker)
        toolbar.addAction(disconnect_action)

    def _add_broker_selector(self, toolbar: QToolBar) -> None:
        broker_label = QLabel("Broker: ")
        broker_label.setToolTip("Select your broker for trading")
        toolbar.addWidget(broker_label)

        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["Mock Broker", "IBKR", "Trade Republic"])
        self.broker_combo.setToolTip(
            "Choose broker:\n"
            "• Mock Broker - Testing with simulated trading\n"
            "• IBKR - Interactive Brokers (TWS/Gateway required)\n"
            "• Trade Republic - Mobile trading platform"
        )
        toolbar.addWidget(self.broker_combo)

    def _add_trading_mode_selector(self, toolbar: QToolBar) -> None:
        mode_label = QLabel("Mode: ")
        mode_label.setToolTip("Trading Mode - CRITICAL safety setting!")
        mode_label.setStyleSheet("font-weight: bold; color: #FFA500;")
        toolbar.addWidget(mode_label)

        self.trading_mode_combo = QComboBox()
        self.trading_mode_combo.addItems(["Backtest", "Paper", "Live"])
        self.trading_mode_combo.setCurrentText("Backtest")
        self.trading_mode_combo.setToolTip(
            "CRITICAL SAFETY SETTING\n\n"
            "• Backtest - Historical simulation (NO real orders)\n"
            "• Paper - Real-time simulation (NO real money)\n"
            "• Live - REAL TRADING with REAL MONEY!"
        )
        self.trading_mode_combo.setStyleSheet(
            """
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
        """
        )
        self.trading_mode_combo.currentTextChanged.connect(self._on_trading_mode_changed)
        toolbar.addWidget(self.trading_mode_combo)

        self.current_trading_mode = "Backtest"

    def _add_data_provider_selector(self, toolbar: QToolBar) -> None:
        data_provider_label = QLabel("Market Data: ")
        data_provider_label.setToolTip("Select market data provider")
        toolbar.addWidget(data_provider_label)

        self.data_provider_combo = QComboBox()
        self.data_provider_combo.setToolTip(
            "Select market data source:\n"
            "• Auto - Use priority order from settings\n"
            "• Database - Cached historical data\n"
            "• Alpaca - US stocks (free tier: IEX data)\n"
            "• Yahoo Finance - Free historical data"
        )
        self.data_provider_combo.currentTextChanged.connect(self.on_data_provider_changed)
        toolbar.addWidget(self.data_provider_combo)

    def _build_refresh_action(self) -> QAction:
        refresh_action = QAction(get_icon("refresh"), "Refresh", self)
        refresh_action.setToolTip("Refresh market data")
        refresh_action.triggered.connect(self.refresh_market_data)
        return refresh_action

    def _add_status_indicators(self, toolbar: QToolBar) -> None:
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        self.connection_status.setToolTip("Broker connection status")
        toolbar.addWidget(self.connection_status)

        self.ai_status = QLabel("AI: Ready")
        self.ai_status.setToolTip("AI service status")
        toolbar.addWidget(self.ai_status)

        self.crypto_status = QLabel("Crypto: Off")
        self.crypto_status.setStyleSheet("color: gray;")
        self.crypto_status.setToolTip("Live Crypto Data Stream Status")
        toolbar.addWidget(self.crypto_status)

    def _add_live_data_toggle(self, toolbar: QToolBar) -> None:
        self.live_data_toggle = QPushButton("Live Data: OFF")
        self.live_data_toggle.setCheckable(True)
        self.live_data_toggle.setToolTip(
            "Toggle live market data in paper mode\n"
            "• ON: Use real-time market data from providers\n"
            "• OFF: Use cached/simulated data"
        )
        self.live_data_toggle.clicked.connect(self.toggle_live_data)
        toolbar.addWidget(self.live_data_toggle)

    def _add_pre_trade_button(self, toolbar: QToolBar) -> None:
        self.pre_trade_button = QPushButton("🎯 Pre-Trade")
        self.pre_trade_button.setToolTip(
            "Pre-Trade Analyse\n\n"
            "Öffnet Multi-Timeframe Charts für die Analyse\n"
            "des übergeordneten Trends VOR dem Trade.\n\n"
            "Shortcut: Ctrl+Shift+T"
        )
        self.pre_trade_button.setStyleSheet(
            """
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
        """
        )
        self.pre_trade_button.clicked.connect(self._on_open_pre_trade_analysis)
        toolbar.addWidget(self.pre_trade_button)

    def _add_quick_actions(self, toolbar: QToolBar) -> None:
        new_order_action = QAction(get_icon("order"), "New Order", self)
        new_order_action.setToolTip("Place new order")
        new_order_action.triggered.connect(self.show_order_dialog)
        toolbar.addAction(new_order_action)

        backtest_action = QAction(get_icon("backtest"), "Backtest", self)
        backtest_action.setToolTip("Run backtest")
        backtest_action.triggered.connect(self.show_backtest_dialog)
        toolbar.addAction(backtest_action)

        ai_backtest_action = QAction(get_icon("ai"), "AI Backtest", self)
        ai_backtest_action.setToolTip("AI-powered backtest analysis")
        ai_backtest_action.triggered.connect(self.show_ai_backtest_dialog)
        toolbar.addAction(ai_backtest_action)

        param_opt_action = QAction(get_icon("optimize"), "Optimize", self)
        param_opt_action.setToolTip("Parameter optimization")
        param_opt_action.triggered.connect(self.show_parameter_optimization_dialog)
        toolbar.addAction(param_opt_action)

        settings_action = QAction(get_icon("settings"), "Settings", self)
        settings_action.setToolTip("Open settings")
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)

    def update_data_provider_list(self):
        """Update the list of available market data providers (refactored)."""
        try:
            # Get and filter available sources
            filtered_sources = self._get_filtered_sources()

            # Preserve current selection
            previous_key = self._get_current_provider_key()

            # Rebuild combo box
            self.data_provider_combo.blockSignals(True)
            self.data_provider_combo.clear()
            self._populate_provider_combo(filtered_sources)

            # Restore selection
            self._restore_provider_selection(previous_key)

            self.data_provider_combo.blockSignals(False)
            logger.info(f"Available market data providers: {filtered_sources}")

        except Exception as e:
            logger.error(f"Failed to update data provider list: {e}")

    def _get_filtered_sources(self):
        """Get available sources with Alpaca variants collapsed."""
        available_sources = self.history_manager.get_available_sources()

        # Collapse Alpaca variants
        alpaca_available = "alpaca" in available_sources or "alpaca_crypto" in available_sources
        filtered_sources = [s for s in available_sources if s not in ("alpaca_crypto",)]

        if alpaca_available and "alpaca" not in filtered_sources:
            filtered_sources.append("alpaca")

        return filtered_sources

    def _get_current_provider_key(self):
        """Get current provider key to preserve selection."""
        if self.data_provider_combo.count() > 0:
            current_index = self.data_provider_combo.currentIndex()
            if current_index >= 0:
                return self.data_provider_combo.itemData(current_index)
        return None

    def _populate_provider_combo(self, filtered_sources):
        """Populate combo box with available and disabled providers."""
        # Add "Auto" option
        self.data_provider_combo.addItem("Auto (Priority Order)", None)

        # Display names mapping
        provider_display_names = {
            "database": "Database (Cache)",
            "ibkr": "Interactive Brokers",
            "alpaca": "Alpaca (Stocks & Crypto)",
            "bitunix": "Bitunix Futures",
            "alpha_vantage": "Alpha Vantage",
            "finnhub": "Finnhub",
            "yahoo": "Yahoo Finance"
        }

        # Add available providers
        for source in filtered_sources:
            display_name = provider_display_names.get(source, source.title())
            self.data_provider_combo.addItem(f"{display_name}", source)

        # Add disabled providers
        self._add_disabled_providers(filtered_sources)

    def _add_disabled_providers(self, available_sources):
        """Add disabled providers with configuration prompts."""
        profile = config_manager.load_profile()
        market_config = profile.market_data

        # Alpaca
        if market_config.alpaca_enabled and "alpaca" not in available_sources:
            self.data_provider_combo.addItem(
                "Alpaca (Configure API Keys)",
                "alpaca_disabled"
            )

        # Alpha Vantage
        if market_config.alpha_vantage_enabled and "alpha_vantage" not in available_sources:
            self.data_provider_combo.addItem(
                "Alpha Vantage (Configure API Key)",
                "alpha_vantage_disabled"
            )

        # Finnhub
        if market_config.finnhub_enabled and "finnhub" not in available_sources:
            self.data_provider_combo.addItem(
                "Finnhub (Configure API Key)",
                "finnhub_disabled"
            )

        # Bitunix
        if market_config.bitunix_enabled and "bitunix" not in available_sources:
            self.data_provider_combo.addItem(
                "Bitunix Futures (Configure API Keys)",
                "bitunix_disabled"
            )

        # Yahoo (always available fallback)
        if market_config.yahoo_enabled and "yahoo" not in available_sources:
            from src.core.market_data.history_provider import DataSource, YahooFinanceProvider
            self.history_manager.register_provider(DataSource.YAHOO, YahooFinanceProvider())
            self.data_provider_combo.addItem("Yahoo Finance", "yahoo")
            logger.info("Registered Yahoo Finance provider")

    def _restore_provider_selection(self, previous_key):
        """Restore provider selection with fallback chain."""
        # Load saved preferences
        saved_key_raw = self.settings.value("market_data_provider_key", None)
        saved_text = self.settings.value("market_data_provider", "Auto (Priority Order)")
        saved_key = str(saved_key_raw) if saved_key_raw not in (None, "") else None

        # Try selection methods in order of priority
        if self._select_by_key(saved_key):  # 1. Saved key
            return
        if self._select_by_text(saved_text):  # 2. Saved text
            return
        if self._select_by_key(previous_key):  # 3. Previous runtime selection
            return
        # 4. Fallback to Auto
        if self.data_provider_combo.count() > 0:
            self.data_provider_combo.setCurrentIndex(0)

    def _select_by_key(self, key):
        """Select provider by key, return True if found."""
        if key is None:
            return False
        for i in range(self.data_provider_combo.count()):
            if self.data_provider_combo.itemData(i) == key:
                self.data_provider_combo.setCurrentIndex(i)
                return True
        return False

    def _select_by_text(self, text):
        """Select provider by display text, return True if found."""
        idx = self.data_provider_combo.findText(text)
        if idx >= 0:
            self.data_provider_combo.setCurrentIndex(idx)
            return True
        return False

    def on_data_provider_changed(self, _provider_name: str):
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
                self.settings.setValue("market_data_provider_key", provider_key)

            logger.info(f"Selected market data provider: {provider_key}")

        except Exception as e:
            logger.error(f"Failed to handle data provider change: {e}", exc_info=True)
