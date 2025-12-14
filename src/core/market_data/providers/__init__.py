"""Market Data Providers for OrderPilot-AI.

This package contains various historical data provider implementations.
All providers inherit from HistoricalDataProvider base class.

REFACTORED: Providers extracted from history_provider.py for better organization.
"""

from .base import HistoricalDataProvider
from .alpaca_stock_provider import AlpacaProvider
from .yahoo_provider import YahooFinanceProvider
from .alpha_vantage_provider import AlphaVantageProvider
from .finnhub_provider import FinnhubProvider
from .ibkr_provider import IBKRHistoricalProvider
from .database_provider import DatabaseProvider

__all__ = [
    "HistoricalDataProvider",
    "AlpacaProvider",
    "YahooFinanceProvider",
    "AlphaVantageProvider",
    "FinnhubProvider",
    "IBKRHistoricalProvider",
    "DatabaseProvider",
]
