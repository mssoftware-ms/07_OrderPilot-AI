"""History Provider Config - Provider configuration and initialization.

Refactored from 700 LOC monolith using composition pattern.

Module 1/3 of history_provider.py split.

Contains:
- configure_priority(): Configure provider priority order
- initialize_providers_from_config(): Register all providers from config
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config.loader import config_manager
from src.core.market_data.types import DataSource

if TYPE_CHECKING:
    from src.core.broker import BrokerAdapter
    from src.core.market_data.providers import (
        AlpacaProvider,
        BitunixProvider,
        YahooFinanceProvider,
        AlphaVantageProvider,
        FinnhubProvider,
        IBKRHistoricalProvider,
    )

logger = logging.getLogger(__name__)


class HistoryProviderConfig:
    """Helper für HistoryManager Config (Priority, Provider Initialization)."""

    def __init__(self, parent):
        """
        Args:
            parent: HistoryManager Instanz
        """
        self.parent = parent

    def configure_priority(self) -> None:
        """Configure provider priority order from settings."""
        profile = config_manager.load_profile()
        market_config = profile.market_data

        live_first = market_config.prefer_live_broker

        if live_first:
            self.parent.priority_order = [
                DataSource.DATABASE,
                DataSource.IBKR,
                DataSource.ALPACA,
                DataSource.ALPACA_CRYPTO,
                DataSource.BITUNIX,
                DataSource.ALPHA_VANTAGE,
                DataSource.FINNHUB,
                DataSource.YAHOO
            ]
        else:
            self.parent.priority_order = [
                DataSource.DATABASE,
                DataSource.ALPACA,
                DataSource.ALPACA_CRYPTO,
                DataSource.BITUNIX,
                DataSource.ALPHA_VANTAGE,
                DataSource.FINNHUB,
                DataSource.YAHOO,
                DataSource.IBKR
            ]

    def initialize_providers_from_config(self, ibkr_adapter: BrokerAdapter | None) -> None:
        """Register providers according to configuration and credentials."""
        profile = config_manager.load_profile()
        market_config = profile.market_data

        # Register IBKR if adapter supplied
        if ibkr_adapter:
            from src.core.market_data.providers import IBKRHistoricalProvider
            self.parent.register_provider(DataSource.IBKR, IBKRHistoricalProvider(ibkr_adapter))

        # Alpaca (Stocks)
        if market_config.alpaca_enabled:
            api_key = config_manager.get_credential("alpaca_api_key")
            api_secret = config_manager.get_credential("alpaca_api_secret")
            if api_key and api_secret:
                from src.core.market_data.providers import AlpacaProvider
                self.parent.register_provider(DataSource.ALPACA, AlpacaProvider(api_key, api_secret))
                logger.info(f"Registered Alpaca stock provider (key: {api_key[:8]}...)")

                # Also register Alpaca Crypto provider with same credentials
                from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
                self.parent.register_provider(DataSource.ALPACA_CRYPTO, AlpacaCryptoProvider(api_key, api_secret))
                logger.info(f"Registered Alpaca crypto provider (key: {api_key[:8]}...)")
            else:
                logger.warning("Alpaca provider enabled but API credentials not found")
        else:
            logger.warning("Alpaca provider is DISABLED in config")

        # Alpha Vantage
        if market_config.alpha_vantage_enabled:
            api_key = config_manager.get_credential("alpha_vantage_api_key")
            if api_key:
                from src.core.market_data.providers import AlphaVantageProvider
                self.parent.register_provider(DataSource.ALPHA_VANTAGE, AlphaVantageProvider(api_key))
            else:
                logger.warning("Alpha Vantage provider enabled but API key not found")

        # Finnhub
        if market_config.finnhub_enabled:
            api_key = config_manager.get_credential("finnhub_api_key")
            if api_key:
                from src.core.market_data.providers import FinnhubProvider
                self.parent.register_provider(DataSource.FINNHUB, FinnhubProvider(api_key))
            else:
                logger.warning("Finnhub provider enabled but API key not found")

        # Bitunix Futures
        if market_config.bitunix_enabled:
            api_key = config_manager.get_credential("bitunix_api_key")
            api_secret = config_manager.get_credential("bitunix_api_secret")
            if api_key and api_secret:
                from src.core.market_data.providers import BitunixProvider
                use_testnet = market_config.bitunix_testnet
                max_bars = market_config.bitunix_max_bars
                max_batches = market_config.bitunix_max_batches
                self.parent.register_provider(
                    DataSource.BITUNIX,
                    BitunixProvider(
                        api_key,
                        api_secret,
                        use_testnet=use_testnet,
                        max_bars=max_bars,
                        max_batches=max_batches
                    )
                )
                logger.info(f"Registered Bitunix Futures provider (testnet: {use_testnet}, key: {api_key[:8]}...)")
            else:
                logger.warning("Bitunix provider enabled but API credentials not found")

        # Yahoo Finance (no API key required)
        if market_config.yahoo_enabled:
            from src.core.market_data.providers import YahooFinanceProvider
            self.parent.register_provider(DataSource.YAHOO, YahooFinanceProvider())
