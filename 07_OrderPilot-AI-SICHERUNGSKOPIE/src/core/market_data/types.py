"""Type Definitions for Historical Market Data.

Defines data sources, timeframes, and data structures for historical market data.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AssetClass(Enum):
    """Asset class types supported by the platform."""
    STOCK = "stock"
    CRYPTO = "crypto"
    OPTION = "option"
    FOREX = "forex"


class DataSource(Enum):
    """Available data sources."""
    IBKR = "ibkr"
    ALPACA = "alpaca"
    ALPACA_CRYPTO = "alpaca_crypto"  # Alpaca cryptocurrency data
    BITUNIX = "bitunix"  # Bitunix Futures (Crypto)
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    YAHOO = "yahoo"
    DATABASE = "database"  # Local database cache


class Timeframe(Enum):
    """Market data timeframes."""
    SECOND_1 = "1s"
    SECOND_5 = "5s"
    SECOND_30 = "30s"
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    HOUR_1 = "1h"
    HOUR_2 = "2h"  # Issue #42: Added 2-hour timeframe
    HOUR_4 = "4h"
    HOUR_8 = "8h"  # Issue #42: Added 8-hour timeframe
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1ME"


@dataclass
class HistoricalBar:
    """Historical market bar data."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    vwap: Decimal | None = None
    trades: int | None = None
    source: str = ""


@dataclass
class DataRequest:
    """Request for historical data."""
    symbol: str
    start_date: datetime
    end_date: datetime
    timeframe: Timeframe
    asset_class: AssetClass = AssetClass.STOCK  # Default to stock for backwards compatibility
    source: DataSource | None = None
    include_extended_hours: bool = False
    adjust_for_splits: bool = True


def format_symbol_with_source(symbol: str, source: DataSource) -> str:
    """Format symbol with source prefix for unique database storage.

    Args:
        symbol: Raw symbol (e.g., "BTC/USD", "BTCUSDT")
        source: Data source provider

    Returns:
        Formatted symbol with source prefix (e.g., "alpaca_crypto:BTC/USD", "bitunix:BTCUSDT")

    Examples:
        >>> format_symbol_with_source("BTC/USD", DataSource.ALPACA_CRYPTO)
        "alpaca_crypto:BTC/USD"
        >>> format_symbol_with_source("BTCUSDT", DataSource.BITUNIX)
        "bitunix:BTCUSDT"
    """
    return f"{source.value}:{symbol}"


def parse_symbol_with_source(formatted_symbol: str) -> tuple[str, str]:
    """Parse formatted symbol back to raw symbol and source.

    Args:
        formatted_symbol: Symbol with source prefix (e.g., "bitunix:BTCUSDT")

    Returns:
        Tuple of (symbol, source_name)

    Examples:
        >>> parse_symbol_with_source("bitunix:BTCUSDT")
        ("BTCUSDT", "bitunix")
        >>> parse_symbol_with_source("alpaca_crypto:BTC/USD")
        ("BTC/USD", "alpaca_crypto")
    """
    if ":" in formatted_symbol:
        source, symbol = formatted_symbol.split(":", 1)
        return symbol, source
    # Fallback for legacy symbols without source prefix
    return formatted_symbol, "unknown"
