"""Market Data Package.

Provides market data streaming and historical data retrieval for stocks and cryptocurrencies.
"""

from src.core.market_data.types import (
    AssetClass,
    DataSource,
    DataRequest,
    HistoricalBar,
    Timeframe
)
from src.core.market_data.history_provider import (
    HistoryManager,
    HistoricalDataProvider,
    AlpacaProvider
)
from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
from src.core.market_data.alpaca_stream import AlpacaStreamClient
from src.core.market_data.alpaca_crypto_stream import AlpacaCryptoStreamClient

__all__ = [
    # Types
    "AssetClass",
    "DataSource",
    "DataRequest",
    "HistoricalBar",
    "Timeframe",
    # Providers
    "HistoryManager",
    "HistoricalDataProvider",
    "AlpacaProvider",
    "AlpacaCryptoProvider",
    # Stream Clients
    "AlpacaStreamClient",
    "AlpacaCryptoStreamClient",
]
