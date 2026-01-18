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
    MINUTE_10 = "10min"
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
    """Return symbol without prefix (source is stored in separate 'source' column).

    MIGRATION NOTE (2026-01-17):
    - Old behavior: Added prefix like "bitunix:BTCUSDT"
    - New behavior: Returns symbol as-is "BTCUSDT"
    - Source tracking: Now via 'source' column in database

    Args:
        symbol: Raw symbol (e.g., "BTC/USD", "BTCUSDT")
        source: Data source provider (stored separately in DB)

    Returns:
        Symbol without prefix (e.g., "BTC/USD", "BTCUSDT")

    Examples:
        >>> format_symbol_with_source("BTC/USD", DataSource.ALPACA_CRYPTO)
        "BTC/USD"
        >>> format_symbol_with_source("BTCUSDT", DataSource.BITUNIX)
        "BTCUSDT"
    """
    # Migration 2026-01-17: No longer add prefix, return symbol as-is
    # Source is tracked via separate 'source' column in database
    return symbol


def parse_symbol_with_source(formatted_symbol: str) -> tuple[str, str]:
    """Parse symbol and extract source prefix if present.

    MIGRATION NOTE (2026-01-17):
    - Old data: May have prefix like "bitunix:BTCUSDT"
    - New data: No prefix, just "BTCUSDT"
    - This function handles both formats for backwards compatibility

    Args:
        formatted_symbol: Symbol with or without source prefix

    Returns:
        Tuple of (symbol, source_name)
        If no prefix: (symbol, "unknown")

    Examples:
        >>> parse_symbol_with_source("bitunix:BTCUSDT")  # Old format
        ("BTCUSDT", "bitunix")
        >>> parse_symbol_with_source("BTCUSDT")  # New format
        ("BTCUSDT", "unknown")
        >>> parse_symbol_with_source("alpaca_crypto:BTC/USD")  # Old format
        ("BTC/USD", "alpaca_crypto")
    """
    if ":" in formatted_symbol:
        source, symbol = formatted_symbol.split(":", 1)
        return symbol, source
    # Fallback for legacy symbols without source prefix
    return formatted_symbol, "unknown"
