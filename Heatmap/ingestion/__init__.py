"""
Ingestion module for Binance liquidation data.

Handles WebSocket connections, event parsing, and exchange metadata.
"""

from .binance_forceorder_ws import BinanceForceOrderClient
from .exchange_info import ExchangeInfoFetcher

__all__ = [
    "BinanceForceOrderClient",
    "ExchangeInfoFetcher",
]
