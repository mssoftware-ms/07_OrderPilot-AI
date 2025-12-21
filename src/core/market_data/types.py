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
    HOUR_4 = "4h"
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
