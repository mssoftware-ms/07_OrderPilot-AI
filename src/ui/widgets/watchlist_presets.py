"""Watchlist Presets and Quick-Add Definitions.

Contains predefined symbol lists for quick watchlist population.
"""

from __future__ import annotations

from typing import TypedDict


class SymbolInfo(TypedDict, total=False):
    """Type definition for symbol information."""
    symbol: str
    name: str
    wkn: str


# Market indices ETFs
INDICES_PRESETS: list[SymbolInfo] = [
    {"symbol": "QQQ", "name": "NASDAQ 100 ETF"},
    {"symbol": "DIA", "name": "Dow Jones ETF"},
    {"symbol": "SPY", "name": "S&P 500 ETF"},
    {"symbol": "IWM", "name": "Russell 2000 ETF"},
    {"symbol": "VTI", "name": "Total Stock Market ETF"},
]

# Major tech stocks
TECH_STOCKS_PRESETS: list[SymbolInfo] = [
    {"symbol": "AAPL", "name": "Apple Inc."},
    {"symbol": "MSFT", "name": "Microsoft Corp."},
    {"symbol": "GOOGL", "name": "Alphabet Inc."},
    {"symbol": "AMZN", "name": "Amazon.com Inc."},
    {"symbol": "META", "name": "Meta Platforms Inc."},
    {"symbol": "NVDA", "name": "NVIDIA Corp."},
    {"symbol": "TSLA", "name": "Tesla Inc."},
]

# Major cryptocurrency trading pairs
CRYPTO_PRESETS: list[SymbolInfo] = [
    {"symbol": "BTC/USD", "name": "Bitcoin", "wkn": ""},
    {"symbol": "ETH/USD", "name": "Ethereum", "wkn": ""},
    {"symbol": "SOL/USD", "name": "Solana", "wkn": ""},
    {"symbol": "AVAX/USD", "name": "Avalanche", "wkn": ""},
    {"symbol": "MATIC/USD", "name": "Polygon", "wkn": ""},
]

# Default watchlist symbols
DEFAULT_WATCHLIST: list[SymbolInfo] = [
    {"symbol": "AAPL", "name": "Apple Inc.", "wkn": "865985"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "wkn": "870747"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "wkn": "A14Y6F"},
    {"symbol": "QQQ", "name": "NASDAQ 100 ETF", "wkn": "A0AE1X"},
    {"symbol": "SPY", "name": "S&P 500 ETF", "wkn": "A1JULM"},
]


def format_volume(volume: int) -> str:
    """Format volume for display."""
    if volume >= 1_000_000:
        return f"{volume / 1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume / 1_000:.1f}K"
    return str(volume)


# Market status display configuration
MARKET_STATUS_WEEKEND = {
    "text": "⚠ Market Closed (Weekend) - Showing last available data",
    "style": "background-color: #4A3000; color: #FFA500; padding: 5px; border-radius: 3px; font-weight: bold;"
}
MARKET_STATUS_AFTER_HOURS = {
    "text": "⚠ After Hours - Data may be delayed",
    "style": "background-color: #3A3000; color: #FFD700; padding: 5px; border-radius: 3px; font-weight: bold;"
}
MARKET_STATUS_OPEN = {
    "text": "✓ Market Open - Live Data",
    "style": "background-color: #003A00; color: #00FF00; padding: 5px; border-radius: 3px; font-weight: bold;"
}
