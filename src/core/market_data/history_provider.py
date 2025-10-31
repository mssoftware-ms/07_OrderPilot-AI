"""Historical Market Data Provider.

Fetches historical market data from various sources for backtesting and analysis.
Primary source: IBKR, with fallbacks to Alpha Vantage and Finnhub.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

import aiohttp
import pandas as pd

from src.common.event_bus import Event, EventType, event_bus
from src.core.broker import BrokerAdapter
from src.database import get_db_manager
from src.database.models import MarketBar

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Available data sources."""
    IBKR = "ibkr"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    YAHOO = "yahoo"
    DATABASE = "database"  # Local database cache


class Timeframe(Enum):
    """Market data timeframes."""
    SECOND_1 = "1S"
    SECOND_5 = "5S"
    SECOND_30 = "30S"
    MINUTE_1 = "1T"
    MINUTE_5 = "5T"
    MINUTE_15 = "15T"
    MINUTE_30 = "30T"
    HOUR_1 = "1H"
    HOUR_4 = "4H"
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1M"


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
    source: DataSource | None = None
    include_extended_hours: bool = False
    adjust_for_splits: bool = True


class HistoricalDataProvider(ABC):
    """Abstract base class for historical data providers."""

    def __init__(self, name: str):
        """Initialize provider.

        Args:
            name: Provider name
        """
        self.name = name
        self.cache: dict[str, pd.DataFrame] = {}
        self.rate_limit_delay = 0.1  # Default rate limiting

    @abstractmethod
    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars.

        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe

        Returns:
            List of historical bars
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if provider is available
        """
        pass

    def _cache_key(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> str:
        """Generate cache key.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe

        Returns:
            Cache key string
        """
        return f"{symbol}_{start_date.date()}_{end_date.date()}_{timeframe.value}"


class IBKRHistoricalProvider(HistoricalDataProvider):
    """IBKR historical data provider."""

    def __init__(self, ibkr_adapter: BrokerAdapter):
        """Initialize IBKR provider.

        Args:
            ibkr_adapter: IBKR broker adapter instance
        """
        super().__init__("IBKR")
        self.adapter = ibkr_adapter
        self.rate_limit_delay = 0.5  # IBKR rate limiting

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars from IBKR.

        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe

        Returns:
            List of historical bars
        """
        # Check cache first
        cache_key = self._cache_key(symbol, start_date, end_date, timeframe)
        if cache_key in self.cache:
            logger.debug(f"Using cached data for {symbol}")
            return self._df_to_bars(self.cache[cache_key])

        # Convert timeframe to IBKR format
        duration = self._calculate_duration(start_date, end_date)
        bar_size = self._timeframe_to_ibkr(timeframe)

        try:
            # Fetch from IBKR
            bars_data = await self.adapter.get_historical_bars(
                symbol=symbol,
                duration=duration,
                bar_size=bar_size
            )

            # Convert to HistoricalBar objects
            bars = []
            for bar_dict in bars_data:
                bar = HistoricalBar(
                    timestamp=datetime.fromisoformat(bar_dict['timestamp']),
                    open=Decimal(str(bar_dict['open'])),
                    high=Decimal(str(bar_dict['high'])),
                    low=Decimal(str(bar_dict['low'])),
                    close=Decimal(str(bar_dict['close'])),
                    volume=bar_dict['volume'],
                    vwap=Decimal(str(bar_dict.get('vwap', 0))) if bar_dict.get('vwap') else None,
                    source="ibkr"
                )
                bars.append(bar)

            # Cache the data
            if bars:
                df = pd.DataFrame([{
                    'timestamp': b.timestamp,
                    'open': float(b.open),
                    'high': float(b.high),
                    'low': float(b.low),
                    'close': float(b.close),
                    'volume': b.volume
                } for b in bars])
                df.set_index('timestamp', inplace=True)
                self.cache[cache_key] = df

            logger.info(f"Fetched {len(bars)} bars from IBKR for {symbol}")
            return bars

        except Exception as e:
            logger.error(f"Error fetching IBKR data: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if IBKR is available."""
        return await self.adapter.is_connected()

    def _calculate_duration(self, start_date: datetime, end_date: datetime) -> str:
        """Calculate IBKR duration string.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            IBKR duration string (e.g., "1 D", "1 W")
        """
        delta = end_date - start_date
        days = delta.days

        if days <= 1:
            return "1 D"
        elif days <= 7:
            return f"{days} D"
        elif days <= 30:
            weeks = (days + 6) // 7
            return f"{weeks} W"
        else:
            months = (days + 29) // 30
            return f"{months} M"

    def _timeframe_to_ibkr(self, timeframe: Timeframe) -> str:
        """Convert timeframe to IBKR format.

        Args:
            timeframe: Internal timeframe

        Returns:
            IBKR bar size string
        """
        mapping = {
            Timeframe.SECOND_1: "1 secs",
            Timeframe.SECOND_5: "5 secs",
            Timeframe.SECOND_30: "30 secs",
            Timeframe.MINUTE_1: "1 min",
            Timeframe.MINUTE_5: "5 mins",
            Timeframe.MINUTE_15: "15 mins",
            Timeframe.MINUTE_30: "30 mins",
            Timeframe.HOUR_1: "1 hour",
            Timeframe.HOUR_4: "4 hours",
            Timeframe.DAY_1: "1 day",
            Timeframe.WEEK_1: "1 week",
            Timeframe.MONTH_1: "1 month"
        }
        return mapping.get(timeframe, "1 min")

    def _df_to_bars(self, df: pd.DataFrame) -> list[HistoricalBar]:
        """Convert DataFrame to bars.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            List of HistoricalBar objects
        """
        bars = []
        for timestamp, row in df.iterrows():
            bar = HistoricalBar(
                timestamp=timestamp,
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=int(row['volume']),
                source=self.name.lower()
            )
            bars.append(bar)
        return bars


class AlphaVantageProvider(HistoricalDataProvider):
    """Alpha Vantage historical data provider."""

    def __init__(self, api_key: str):
        """Initialize Alpha Vantage provider.

        Args:
            api_key: Alpha Vantage API key
        """
        super().__init__("AlphaVantage")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12.0  # Free tier: 5 calls/minute

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars from Alpha Vantage.

        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe

        Returns:
            List of historical bars
        """
        # Check cache
        cache_key = self._cache_key(symbol, start_date, end_date, timeframe)
        if cache_key in self.cache:
            return self._df_to_bars(self.cache[cache_key])

        # Determine function based on timeframe
        if timeframe in [Timeframe.DAY_1, Timeframe.WEEK_1, Timeframe.MONTH_1]:
            function = "TIME_SERIES_DAILY"
            time_key = "Time Series (Daily)"
        else:
            function = "TIME_SERIES_INTRADAY"
            time_key = "Time Series (1min)"  # Default to 1min for intraday

        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "full"
        }

        if function == "TIME_SERIES_INTRADAY":
            params["interval"] = self._timeframe_to_av(timeframe)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Error Message" in data:
                            logger.error(f"Alpha Vantage error: {data['Error Message']}")
                            return []

                        if time_key not in data:
                            logger.error(f"No data found for {symbol}")
                            return []

                        # Parse time series data
                        bars = []
                        time_series = data[time_key]

                        for timestamp_str, ohlcv in time_series.items():
                            timestamp = datetime.fromisoformat(timestamp_str)

                            # Filter by date range
                            if timestamp < start_date or timestamp > end_date:
                                continue

                            bar = HistoricalBar(
                                timestamp=timestamp,
                                open=Decimal(ohlcv["1. open"]),
                                high=Decimal(ohlcv["2. high"]),
                                low=Decimal(ohlcv["3. low"]),
                                close=Decimal(ohlcv["4. close"]),
                                volume=int(ohlcv["5. volume"]),
                                source="alpha_vantage"
                            )
                            bars.append(bar)

                        # Sort by timestamp
                        bars.sort(key=lambda x: x.timestamp)

                        logger.info(f"Fetched {len(bars)} bars from Alpha Vantage for {symbol}")
                        return bars
                    else:
                        logger.error(f"Alpha Vantage API error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if Alpha Vantage is available."""
        return bool(self.api_key)

    def _timeframe_to_av(self, timeframe: Timeframe) -> str:
        """Convert timeframe to Alpha Vantage format.

        Args:
            timeframe: Internal timeframe

        Returns:
            Alpha Vantage interval string
        """
        mapping = {
            Timeframe.MINUTE_1: "1min",
            Timeframe.MINUTE_5: "5min",
            Timeframe.MINUTE_15: "15min",
            Timeframe.MINUTE_30: "30min",
            Timeframe.HOUR_1: "60min"
        }
        return mapping.get(timeframe, "1min")

    def _df_to_bars(self, df: pd.DataFrame) -> list[HistoricalBar]:
        """Convert DataFrame to bars."""
        bars = []
        for timestamp, row in df.iterrows():
            bar = HistoricalBar(
                timestamp=timestamp,
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=int(row['volume']),
                source=self.name.lower()
            )
            bars.append(bar)
        return bars


class FinnhubProvider(HistoricalDataProvider):
    """Finnhub historical data provider."""

    def __init__(self, api_key: str):
        """Initialize Finnhub provider.

        Args:
            api_key: Finnhub API key
        """
        super().__init__("Finnhub")
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.rate_limit_delay = 1.0  # Free tier: 60 calls/minute

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars from Finnhub.

        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe

        Returns:
            List of historical bars
        """
        # Finnhub candle endpoint
        endpoint = f"{self.base_url}/stock/candle"

        params = {
            "symbol": symbol,
            "resolution": self._timeframe_to_finnhub(timeframe),
            "from": int(start_date.timestamp()),
            "to": int(end_date.timestamp()),
            "token": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("s") != "ok":
                            logger.error(f"Finnhub returned no data for {symbol}")
                            return []

                        # Parse candle data
                        bars = []
                        timestamps = data.get("t", [])
                        opens = data.get("o", [])
                        highs = data.get("h", [])
                        lows = data.get("l", [])
                        closes = data.get("c", [])
                        volumes = data.get("v", [])

                        for i in range(len(timestamps)):
                            bar = HistoricalBar(
                                timestamp=datetime.fromtimestamp(timestamps[i]),
                                open=Decimal(str(opens[i])),
                                high=Decimal(str(highs[i])),
                                low=Decimal(str(lows[i])),
                                close=Decimal(str(closes[i])),
                                volume=int(volumes[i]) if i < len(volumes) else 0,
                                source="finnhub"
                            )
                            bars.append(bar)

                        logger.info(f"Fetched {len(bars)} bars from Finnhub for {symbol}")
                        return bars
                    else:
                        logger.error(f"Finnhub API error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error fetching Finnhub data: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if Finnhub is available."""
        return bool(self.api_key)

    def _timeframe_to_finnhub(self, timeframe: Timeframe) -> str:
        """Convert timeframe to Finnhub format.

        Args:
            timeframe: Internal timeframe

        Returns:
            Finnhub resolution string
        """
        mapping = {
            Timeframe.MINUTE_1: "1",
            Timeframe.MINUTE_5: "5",
            Timeframe.MINUTE_15: "15",
            Timeframe.MINUTE_30: "30",
            Timeframe.HOUR_1: "60",
            Timeframe.DAY_1: "D",
            Timeframe.WEEK_1: "W",
            Timeframe.MONTH_1: "M"
        }
        return mapping.get(timeframe, "1")


class DatabaseProvider(HistoricalDataProvider):
    """Database historical data provider (local cache)."""

    def __init__(self):
        """Initialize database provider."""
        super().__init__("Database")
        self.db_manager = get_db_manager()

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars from database.

        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe

        Returns:
            List of historical bars
        """
        try:
            with self.db_manager.session() as session:
                # Query market bars from database
                bars_db = session.query(MarketBar).filter(
                    MarketBar.symbol == symbol,
                    MarketBar.timestamp >= start_date,
                    MarketBar.timestamp <= end_date
                ).order_by(MarketBar.timestamp).all()

                # Convert to HistoricalBar objects
                bars = []
                for bar_db in bars_db:
                    bar = HistoricalBar(
                        timestamp=bar_db.timestamp,
                        open=bar_db.open,
                        high=bar_db.high,
                        low=bar_db.low,
                        close=bar_db.close,
                        volume=bar_db.volume,
                        vwap=bar_db.vwap,
                        source="database"
                    )
                    bars.append(bar)

                # Resample if needed
                if bars and timeframe != Timeframe.SECOND_1:
                    bars = self._resample_bars(bars, timeframe)

                logger.info(f"Fetched {len(bars)} bars from database for {symbol}")
                return bars

        except Exception as e:
            logger.error(f"Error fetching database bars: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if database is available."""
        return True  # Always available

    def _resample_bars(
        self,
        bars: list[HistoricalBar],
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Resample bars to different timeframe.

        Args:
            bars: Original bars
            timeframe: Target timeframe

        Returns:
            Resampled bars
        """
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': b.timestamp,
            'open': float(b.open),
            'high': float(b.high),
            'low': float(b.low),
            'close': float(b.close),
            'volume': b.volume
        } for b in bars])

        df.set_index('timestamp', inplace=True)

        # Resample
        resampled = df.resample(timeframe.value).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        # Convert back to bars
        resampled_bars = []
        for timestamp, row in resampled.iterrows():
            bar = HistoricalBar(
                timestamp=timestamp,
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=int(row['volume']),
                source="database"
            )
            resampled_bars.append(bar)

        return resampled_bars


class HistoryManager:
    """Manager for historical data with fallback support."""

    def __init__(self):
        """Initialize history manager."""
        self.providers: dict[DataSource, HistoricalDataProvider] = {}
        self.priority_order = [
            DataSource.DATABASE,
            DataSource.IBKR,
            DataSource.ALPHA_VANTAGE,
            DataSource.FINNHUB
        ]

        # Initialize database provider (always available)
        self.providers[DataSource.DATABASE] = DatabaseProvider()

        logger.info("History manager initialized")

    def register_provider(
        self,
        source: DataSource,
        provider: HistoricalDataProvider
    ) -> None:
        """Register a data provider.

        Args:
            source: Data source type
            provider: Provider instance
        """
        self.providers[source] = provider
        logger.info(f"Registered {source.value} provider")

    async def fetch_data(
        self,
        request: DataRequest
    ) -> tuple[list[HistoricalBar], str]:
        """Fetch historical data with fallback.

        Args:
            request: Data request

        Returns:
            Tuple of (bars, source_used)
        """
        # Try specific source if requested
        if request.source and request.source in self.providers:
            provider = self.providers[request.source]
            if await provider.is_available():
                bars = await provider.fetch_bars(
                    request.symbol,
                    request.start_date,
                    request.end_date,
                    request.timeframe
                )
                if bars:
                    await self._store_to_database(bars, request.symbol)
                    return bars, request.source.value

        # Try providers in priority order
        for source in self.priority_order:
            if source not in self.providers:
                continue

            provider = self.providers[source]
            if not await provider.is_available():
                continue

            try:
                # Apply rate limiting
                await asyncio.sleep(provider.rate_limit_delay)

                bars = await provider.fetch_bars(
                    request.symbol,
                    request.start_date,
                    request.end_date,
                    request.timeframe
                )

                if bars:
                    # Store to database for caching
                    if source != DataSource.DATABASE:
                        await self._store_to_database(bars, request.symbol)

                    # Emit event
                    event_bus.emit(Event(
                        type=EventType.MARKET_DATA_FETCHED,
                        timestamp=datetime.utcnow(),
                        data={
                            "symbol": request.symbol,
                            "source": source.value,
                            "bars_count": len(bars),
                            "timeframe": request.timeframe.value
                        },
                        source="history_manager"
                    ))

                    logger.info(f"Fetched {len(bars)} bars from {source.value}")
                    return bars, source.value

            except Exception as e:
                logger.error(f"Error with {source.value} provider: {e}")
                continue

        logger.warning(f"No data available for {request.symbol}")
        return [], "none"

    async def _store_to_database(
        self,
        bars: list[HistoricalBar],
        symbol: str
    ) -> None:
        """Store bars to database for caching.

        Args:
            bars: Bars to store
            symbol: Trading symbol
        """
        try:
            db_manager = get_db_manager()
            with db_manager.session() as session:
                for bar in bars:
                    # Check if bar already exists
                    existing = session.query(MarketBar).filter(
                        MarketBar.symbol == symbol,
                        MarketBar.timestamp == bar.timestamp
                    ).first()

                    if not existing:
                        db_bar = MarketBar(
                            symbol=symbol,
                            timestamp=bar.timestamp,
                            open=bar.open,
                            high=bar.high,
                            low=bar.low,
                            close=bar.close,
                            volume=bar.volume,
                            vwap=bar.vwap,
                            source=bar.source
                        )
                        session.add(db_bar)

                session.commit()
                logger.debug(f"Stored {len(bars)} bars to database")

        except Exception as e:
            logger.error(f"Failed to store bars to database: {e}")

    async def get_latest_price(self, symbol: str) -> Decimal | None:
        """Get latest price for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest price or None
        """
        # Try to get most recent bar
        request = DataRequest(
            symbol=symbol,
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            timeframe=Timeframe.MINUTE_1
        )

        bars, _ = await self.fetch_data(request)

        if bars:
            return bars[-1].close

        return None

    def get_available_sources(self) -> list[str]:
        """Get list of available data sources.

        Returns:
            List of available source names
        """
        return [source.value for source in self.providers.keys()]