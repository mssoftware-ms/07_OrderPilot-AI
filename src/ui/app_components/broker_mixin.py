"""Broker Connection Mixin for TradingApplication.

Contains broker connection, trading mode, and streaming functionality.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

import qasync
from PyQt6.QtWidgets import QMessageBox

from src.common.event_bus import Event, EventType, event_bus
from src.config.loader import config_manager
from src.core.broker import MockBroker
from src.core.broker.ibkr_adapter import IBKRAdapter
from src.core.broker.trade_republic_adapter import TradeRepublicAdapter

logger = logging.getLogger(__name__)


class BrokerMixin:
    """Mixin providing broker connection functionality for TradingApplication."""

    async def connect_broker(self):
        """Connect to the selected broker."""
        try:
            broker_type = self.broker_combo.currentText()

            if broker_type == "Mock Broker":
                self.broker = MockBroker(initial_cash=Decimal("10000"))

            elif broker_type == "Interactive Brokers":
                ibkr_host = self.settings.value("ibkr_host", "localhost")
                ibkr_port_text = self.settings.value("ibkr_port", "7497 (Paper)")
                ibkr_port = int(ibkr_port_text.split()[0])
                ibkr_client_id = int(self.settings.value("ibkr_client_id", "1"))

                self.broker = IBKRAdapter(
                    host=ibkr_host,
                    port=ibkr_port,
                    client_id=ibkr_client_id
                )

                self.history_manager.set_ibkr_adapter(self.broker)
                logger.info(f"Connecting to IBKR at {ibkr_host}:{ibkr_port}")

            elif broker_type == "Trade Republic":
                tr_phone = self.settings.value("tr_phone", "")
                tr_pin = config_manager.get_credential("tr_pin")

                if not tr_phone:
                    QMessageBox.warning(
                        self, "Missing Settings",
                        "Trade Republic phone number not configured."
                    )
                    return

                if not tr_pin:
                    QMessageBox.warning(
                        self, "Missing PIN",
                        "Trade Republic PIN not found."
                    )
                    return

                self.broker = TradeRepublicAdapter(
                    phone_number=tr_phone,
                    pin=tr_pin
                )

                logger.info(f"Connecting to Trade Republic with phone {tr_phone}")

            else:
                QMessageBox.warning(
                    self, "Unknown Broker",
                    f"Broker type '{broker_type}' is not recognized."
                )
                return

            # Set AI hook if available
            if self.ai_service:
                self.broker.ai_hook = self.analyze_order_with_ai

            await self.broker.connect()

            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: green;")

            event_bus.emit(Event(
                type=EventType.MARKET_CONNECTED,
                timestamp=datetime.now(),
                data={"broker": broker_type}
            ))

            self.status_bar.showMessage(f"Connected to {broker_type}", 3000)
            await self.update_account_info()

            logger.info(f"Successfully connected to {broker_type}")

        except Exception as e:
            logger.error(f"Failed to connect broker: {e}")
            QMessageBox.critical(
                self, "Connection Error",
                f"Failed to connect to {broker_type}:\n\n{str(e)}"
            )

    @qasync.asyncSlot()
    async def disconnect_broker(self):
        """Disconnect from the broker."""
        if self.broker:
            try:
                await self.broker.disconnect()
                self.broker = None

                self.connection_status.setText("Disconnected")
                self.connection_status.setStyleSheet("color: red;")

                event_bus.emit(Event(
                    type=EventType.MARKET_DISCONNECTED,
                    timestamp=datetime.now(),
                    data={}
                ))

                self.status_bar.showMessage("Disconnected from broker", 3000)

            except Exception as e:
                logger.error(f"Failed to disconnect broker: {e}")

    @qasync.asyncSlot()
    def _on_trading_mode_changed(self, mode: str):
        """Handle trading mode changes."""
        logger.info(f"Trading mode changed: {self.current_trading_mode} -> {mode}")

        # Live mode warning
        if mode == "Live":
            reply = QMessageBox.warning(
                self,
                "LIVE TRADING MODE",
                "<b>WARNING: You are switching to LIVE TRADING mode!</b><br><br>"
                "This will place <b>REAL ORDERS</b> with <b>REAL MONEY</b>!<br><br>"
                "Are you absolutely sure you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                logger.info("User cancelled Live mode switch")
                self.trading_mode_combo.blockSignals(True)
                self.trading_mode_combo.setCurrentText(self.current_trading_mode)
                self.trading_mode_combo.blockSignals(False)
                return

            logger.warning("USER CONFIRMED LIVE MODE - REAL TRADING ENABLED!")

        old_mode = self.current_trading_mode
        self.current_trading_mode = mode

        # Update UI styling
        if mode == "Backtest":
            self.trading_mode_combo.setStyleSheet("""
                QComboBox {
                    font-weight: bold;
                    padding: 5px 10px;
                    border: 2px solid #26a69a;
                    border-radius: 3px;
                    background-color: #2a2a2a;
                    color: #26a69a;
                }
                QComboBox:hover { background-color: #3a3a3a; border-color: #4CAF50; }
            """)
        elif mode == "Paper":
            self.trading_mode_combo.setStyleSheet("""
                QComboBox {
                    font-weight: bold;
                    padding: 5px 10px;
                    border: 2px solid #FFA500;
                    border-radius: 3px;
                    background-color: #2a2a2a;
                    color: #FFA500;
                }
                QComboBox:hover { background-color: #3a3a3a; border-color: #FFD700; }
            """)
        elif mode == "Live":
            self.trading_mode_combo.setStyleSheet("""
                QComboBox {
                    font-weight: bold;
                    padding: 5px 10px;
                    border: 2px solid #ef5350;
                    border-radius: 3px;
                    background-color: #2a2a2a;
                    color: #ef5350;
                }
                QComboBox:hover { background-color: #3a3a3a; border-color: #ff0000; }
            """)

        status_messages = {
            "Backtest": "Backtest Mode - Historical simulation (SAFE)",
            "Paper": "Paper Mode - Real-time simulation (NO real money)",
            "Live": "LIVE MODE - REAL TRADING ACTIVE!"
        }
        self.status_bar.showMessage(status_messages[mode], 10000)

        event_bus.emit(Event(
            EventType.SYSTEM_EVENT,
            {
                "type": "trading_mode_changed",
                "old_mode": old_mode,
                "new_mode": mode,
                "timestamp": datetime.now()
            }
        ))

        logger.info(f"Trading mode changed to: {mode}")

    async def initialize_realtime_streaming(self):
        """Initialize real-time market data streaming."""
        try:
            profile = config_manager.load_profile()

            alpaca_api_key = config_manager.get_credential("alpaca_api_key")
            alpaca_api_secret = config_manager.get_credential("alpaca_api_secret")

            if not alpaca_api_key or not alpaca_api_secret:
                logger.warning("Alpaca API keys not found - live streaming disabled")
                self.crypto_status.setText("Live Data: No Keys")
                self.crypto_status.setStyleSheet("color: orange;")
                return

            stock_symbols = []
            crypto_symbols = []

            for symbol in self.watchlist_widget.get_symbols():
                if self._is_crypto_symbol(symbol):
                    crypto_symbols.append(symbol)
                else:
                    stock_symbols.append(symbol)

            logger.info("Starting stock streaming via HistoryManager...")
            stock_stream_started = await self.history_manager.start_realtime_stream(
                stock_symbols if stock_symbols else []
            )

            if stock_stream_started:
                logger.info(f"Stock streaming started - subscribed to {len(stock_symbols)} symbols")
            else:
                logger.warning("Failed to start stock streaming")

            if profile.features.crypto_trading:
                logger.info("Starting crypto streaming via HistoryManager...")
                crypto_stream_started = await self.history_manager.start_crypto_realtime_stream(
                    crypto_symbols if crypto_symbols else ["BTC/USD", "ETH/USD"]
                )

                if crypto_stream_started:
                    self.crypto_status.setText("Live Data: Active")
                    self.crypto_status.setStyleSheet("color: #2ECC71; font-weight: bold;")
                    logger.info(f"Crypto streaming started")
                else:
                    self.crypto_status.setText("Live Data: Error")
                    self.crypto_status.setStyleSheet("color: orange;")
                    logger.error("Failed to start crypto streaming")
            else:
                logger.info("Crypto trading disabled in configuration")

        except Exception as e:
            logger.error(f"Failed to initialize real-time streaming: {e}")
            self.crypto_status.setText("Live Data: Error")
            self.crypto_status.setStyleSheet("color: orange;")

    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency pair."""
        return "/" in symbol

<<<<<<< HEAD
    def toggle_live_data(self):
        """Toggle live market data on/off."""
        try:
            is_live = self.live_data_toggle.isChecked()

            if is_live:
                self.live_data_toggle.setText("Live Data: ON")
                self.live_data_toggle.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
                self.status_bar.showMessage("Live market data enabled", 3000)
                logger.info("Live market data enabled")

                current_index = self.data_provider_combo.currentIndex()
                current_source = self.data_provider_combo.itemData(current_index)

                if current_source == "database" or current_source is None:
                    for i in range(self.data_provider_combo.count()):
                        source = self.data_provider_combo.itemData(i)
                        if source and source not in ["database", None] and not source.endswith("_disabled"):
                            self.data_provider_combo.setCurrentIndex(i)
                            break

                # Start streaming when live data is enabled
                asyncio.create_task(self.initialize_realtime_streaming())
            else:
                self.live_data_toggle.setText("Live Data: OFF")
                self.live_data_toggle.setStyleSheet("")
                self.status_bar.showMessage("Live market data disabled - using cached data", 3000)
                logger.info("Live market data disabled")

                for i in range(self.data_provider_combo.count()):
                    source = self.data_provider_combo.itemData(i)
                    if source == "database" or source is None:
                        self.data_provider_combo.setCurrentIndex(i)
                        break

                # Stop all live streams when disabled
                asyncio.create_task(self._stop_live_data_streams())

            self.settings.setValue("live_data_enabled", is_live)

        except Exception as e:
            logger.error(f"Failed to toggle live data: {e}")

    async def _stop_live_data_streams(self) -> None:
        """Stop all real-time streaming clients and sync open charts."""
        tasks = []

        if getattr(self, "history_manager", None):
            if hasattr(self.history_manager, "stop_realtime_stream"):
                tasks.append(self.history_manager.stop_realtime_stream())
            if hasattr(self.history_manager, "stop_crypto_realtime_stream"):
                tasks.append(self.history_manager.stop_crypto_realtime_stream())

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error("Error stopping live stream: %s", result)

        if hasattr(self, "crypto_status"):
            self.crypto_status.setText("Live Data: OFF")
            self.crypto_status.setStyleSheet("color: #888;")

        # Update any open chart windows to reflect stopped streams
        if hasattr(self, "chart_window_manager"):
            for window in list(self.chart_window_manager.windows.values()):
                try:
                    chart = window.chart_widget
                    if getattr(chart, "live_streaming_enabled", False):
                        chart.live_streaming_enabled = False
                        if hasattr(chart, "live_stream_button"):
                            chart.live_stream_button.setChecked(False)
                        if hasattr(chart, "_stop_live_stream_async"):
                            asyncio.create_task(chart._stop_live_stream_async())
                except Exception as e:
                    logger.debug("Failed to stop chart stream: %s", e)
=======
    def toggle_live_data(self):
        """Toggle live market data on/off."""
        try:
            is_live = self.live_data_toggle.isChecked()

            if is_live:
                self.live_data_toggle.setText("Live Data: ON")
                self.live_data_toggle.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
                self.status_bar.showMessage("Live market data enabled", 3000)
                logger.info("Live market data enabled")

                current_index = self.data_provider_combo.currentIndex()
                current_source = self.data_provider_combo.itemData(current_index)

                if current_source == "database" or current_source is None:
                    for i in range(self.data_provider_combo.count()):
                        source = self.data_provider_combo.itemData(i)
                        if source and source not in ["database", None] and not source.endswith("_disabled"):
                            self.data_provider_combo.setCurrentIndex(i)
                            break
            else:
                self.live_data_toggle.setText("Live Data: OFF")
                self.live_data_toggle.setStyleSheet("")
                self.status_bar.showMessage("Live market data disabled - using cached data", 3000)
                logger.info("Live market data disabled")

                for i in range(self.data_provider_combo.count()):
                    source = self.data_provider_combo.itemData(i)
                    if source == "database" or source is None:
                        self.data_provider_combo.setCurrentIndex(i)
                        break

            self.settings.setValue("live_data_enabled", is_live)

        except Exception as e:
            logger.error(f"Failed to toggle live data: {e}")
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268

    def analyze_order_with_ai(self, analysis_request):
        """AI hook for order analysis."""
        from core.broker import AIAnalysisResult

        return AIAnalysisResult(
            approved=True,
            confidence=0.8,
            reasoning="Mock analysis for testing",
            risks_identified=[],
            opportunities_identified=["Test opportunity"],
            fee_impact_warning=None,
            display_data={}
        )

    async def _subscribe_symbol_to_stream(self, symbol: str):
        """Subscribe a symbol to the appropriate real-time stream."""
        try:
            if self._is_crypto_symbol(symbol):
                if hasattr(self.history_manager, 'crypto_stream_client') and self.history_manager.crypto_stream_client:
                    await self.history_manager.crypto_stream_client.subscribe([symbol])
                    logger.info(f"Subscribed {symbol} to crypto stream")
                else:
                    logger.warning(f"Crypto stream not available for {symbol}")
            else:
                if hasattr(self.history_manager, 'stream_client') and self.history_manager.stream_client:
                    await self.history_manager.stream_client.subscribe([symbol])
                    logger.info(f"Subscribed {symbol} to stock stream")
                else:
                    logger.warning(f"Stock stream not available for {symbol}")

        except Exception as e:
            logger.error(f"Failed to subscribe {symbol} to stream: {e}")
