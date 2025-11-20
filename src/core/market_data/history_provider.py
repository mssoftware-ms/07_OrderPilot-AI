"""Historical Market Data Provider.

Fetches historical market data from various sources for backtesting and analysis.
Primary source: IBKR, with fallbacks to Alpha Vantage and Finnhub.
"""

import asyncio
import importlib.util
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum

import aiohttp
import pandas as pd

from src.common.event_bus import Event, EventType, event_bus
from src.config.loader import config_manager
from src.core.broker import BrokerAdapter
from src.database import get_db_manager
from src.database.models import MarketBar

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Available data sources."""
    IBKR = "ibkr"
    ALPACA = "alpaca"
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

    async def fetch_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close"
    ) -> dict:
        """Fetch technical indicator from Alpha Vantage.

        Args:
            symbol: Trading symbol
            indicator: Indicator name (RSI, MACD, EMA, SMA, etc.)
            interval: Time interval (1min, 5min, 15min, 30min, 60min, daily, weekly, monthly)
            time_period: Time period for indicator calculation
            series_type: Price series type (close, open, high, low)

        Returns:
            Dictionary with indicator data
        """
        params = {
            "function": indicator.upper(),
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type,
            "apikey": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Error Message" in data:
                            logger.error(f"Alpha Vantage error: {data['Error Message']}")
                            return {}

                        # Find the technical analysis key
                        ta_key = None
                        for key in data.keys():
                            if "Technical Analysis" in key:
                                ta_key = key
                                break

                        if not ta_key:
                            logger.error(f"No technical analysis data found for {symbol}")
                            return {}

                        logger.info(f"Fetched {indicator} for {symbol} from Alpha Vantage")
                        return data[ta_key]
                    else:
                        logger.error(f"Alpha Vantage API error: {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage indicator: {e}")
            return {}

    async def fetch_rsi(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close"
    ) -> pd.Series:
        """Fetch RSI (Relative Strength Index) from Alpha Vantage.

        Args:
            symbol: Trading symbol
            interval: Time interval
            time_period: RSI period (default: 14)
            series_type: Price series type

        Returns:
            Pandas Series with RSI values
        """
        data = await self.fetch_technical_indicator(
            symbol, "RSI", interval, time_period, series_type
        )

        if not data:
            return pd.Series()

        # Convert to pandas Series
        rsi_data = {}
        for timestamp_str, values in data.items():
            timestamp = datetime.fromisoformat(timestamp_str)
            rsi_data[timestamp] = float(values["RSI"])

        return pd.Series(rsi_data).sort_index()

    async def fetch_macd(
        self,
        symbol: str,
        interval: str = "daily",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        series_type: str = "close"
    ) -> pd.DataFrame:
        """Fetch MACD (Moving Average Convergence Divergence) from Alpha Vantage.

        Args:
            symbol: Trading symbol
            interval: Time interval
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            series_type: Price series type

        Returns:
            DataFrame with MACD, signal, and histogram values
        """
        params = {
            "function": "MACD",
            "symbol": symbol,
            "interval": interval,
            "series_type": series_type,
            "fastperiod": fast_period,
            "slowperiod": slow_period,
            "signalperiod": signal_period,
            "apikey": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Error Message" in data:
                            logger.error(f"Alpha Vantage error: {data['Error Message']}")
                            return pd.DataFrame()

                        if "Technical Analysis: MACD" not in data:
                            logger.error(f"No MACD data found for {symbol}")
                            return pd.DataFrame()

                        # Convert to DataFrame
                        macd_data = []
                        for timestamp_str, values in data["Technical Analysis: MACD"].items():
                            timestamp = datetime.fromisoformat(timestamp_str)
                            macd_data.append({
                                "timestamp": timestamp,
                                "macd": float(values["MACD"]),
                                "signal": float(values["MACD_Signal"]),
                                "histogram": float(values["MACD_Hist"])
                            })

                        df = pd.DataFrame(macd_data)
                        df.set_index("timestamp", inplace=True)
                        df.sort_index(inplace=True)

                        logger.info(f"Fetched MACD for {symbol} from Alpha Vantage")
                        return df
                    else:
                        logger.error(f"Alpha Vantage API error: {response.status}")
                        return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching MACD: {e}")
            return pd.DataFrame()


class YahooFinanceProvider(HistoricalDataProvider):
    """Yahoo Finance historical data provider."""

    def __init__(self):
        super().__init__("YahooFinance")
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.rate_limit_delay = 1.0  # Avoid hammering public endpoint
        self.max_retries = 3
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars from Yahoo Finance."""
        effective_start, effective_end = self._clamp_date_range(
            start_date,
            end_date,
            timeframe
        )

        cache_key = self._cache_key(symbol, effective_start, effective_end, timeframe)
        if cache_key in self.cache:
            return self._df_to_bars(self.cache[cache_key])

        interval = self._timeframe_to_yahoo(timeframe)

        params = {
            "period1": self._to_unix(effective_start),
            "period2": self._to_unix(effective_end),
            "interval": interval,
            "includePrePost": "false",
            "events": "div,splits"
        }

        endpoint = f"{self.base_url}/{symbol}"

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                backoff = 1.5
                last_error_status = None

                for attempt in range(self.max_retries):
                    async with session.get(endpoint, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            break

                        last_error_status = response.status

                        if response.status == 429 and attempt < self.max_retries - 1:
                            retry_after_header = response.headers.get("Retry-After")
                            try:
                                retry_after = float(retry_after_header) if retry_after_header else backoff
                            except ValueError:
                                retry_after = backoff

                            logger.warning(
                                "Yahoo Finance rate limit for %s (attempt %s/%s). Retrying in %.1fs",
                                symbol,
                                attempt + 1,
                                self.max_retries,
                                retry_after
                            )
                            await asyncio.sleep(retry_after)
                            backoff *= 2
                            continue

                        logger.error(f"Yahoo Finance API error ({response.status}) for {symbol}")
                        return []
                else:
                    # Retries exhausted without success
                    logger.error(f"Yahoo Finance API error ({last_error_status}) for {symbol}")
                    return []

            chart_data = data.get("chart", {})
            results = chart_data.get("result", [])
            if not results:
                logger.error(f"Yahoo Finance returned no data for {symbol}")
                return []

            result = results[0]
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {})
            quote_data = indicators.get("quote", [])

            if not timestamps or not quote_data:
                logger.error(f"Incomplete Yahoo Finance data for {symbol}")
                return []

            quote = quote_data[0]
            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            bars: list[HistoricalBar] = []

            for idx, ts in enumerate(timestamps):
                # Yahoo can return None for non-trading periods
                try:
                    bar_open = opens[idx]
                    bar_high = highs[idx]
                    bar_low = lows[idx]
                    bar_close = closes[idx]
                except IndexError:
                    break

                if None in (bar_open, bar_high, bar_low, bar_close):
                    continue

                bar_volume = 0
                if idx < len(volumes) and volumes[idx] is not None:
                    bar_volume = int(volumes[idx])

                timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)

                if timestamp < effective_start or timestamp > effective_end:
                    continue

                bar = HistoricalBar(
                    timestamp=timestamp,
                    open=Decimal(str(bar_open)),
                    high=Decimal(str(bar_high)),
                    low=Decimal(str(bar_low)),
                    close=Decimal(str(bar_close)),
                    volume=bar_volume,
                    source="yahoo"
                )
                bars.append(bar)

            if not bars:
                logger.warning(f"Yahoo Finance returned empty dataset for {symbol}")
                return []

            # Cache dataframe for future requests
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

            logger.info(f"Fetched {len(bars)} bars from Yahoo Finance for {symbol}")
            return bars

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data: {e}")
            return []

    async def is_available(self) -> bool:
        """Yahoo Finance is always available (no API key required)."""
        return True

    def _timeframe_to_yahoo(self, timeframe: Timeframe) -> str:
        """Convert timeframe enum to Yahoo Finance interval string."""
        mapping = {
            Timeframe.SECOND_1: "1m",
            Timeframe.SECOND_5: "1m",
            Timeframe.SECOND_30: "1m",
            Timeframe.MINUTE_1: "1m",
            Timeframe.MINUTE_5: "5m",
            Timeframe.MINUTE_15: "15m",
            Timeframe.MINUTE_30: "30m",
            Timeframe.HOUR_1: "60m",
            Timeframe.HOUR_4: "1h",
            Timeframe.DAY_1: "1d",
            Timeframe.WEEK_1: "1wk",
            Timeframe.MONTH_1: "1mo"
        }
        return mapping.get(timeframe, "1d")

    def _df_to_bars(self, df: pd.DataFrame) -> list[HistoricalBar]:
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

    def _to_unix(self, value: datetime) -> int:
        """Convert datetime to UTC UNIX timestamp."""
        if value.tzinfo is None:
            return int(value.replace(tzinfo=timezone.utc).timestamp())
        return int(value.astimezone(timezone.utc).timestamp())

    def _clamp_date_range(
        self,
        requested_start: datetime,
        requested_end: datetime,
        timeframe: Timeframe
    ) -> tuple[datetime, datetime]:
        """Ensure Yahoo intraday requests stay within supported lookback windows."""
        limit = self._get_lookback_limit(timeframe)
        if not limit:
            return requested_start, requested_end

        earliest_supported = requested_end - limit
        if requested_start < earliest_supported:
            logger.debug(
                "Yahoo Finance timeframe %s limited to %s days. Adjusted start from %s to %s.",
                timeframe.value,
                limit.days,
                requested_start,
                earliest_supported
            )
            return earliest_supported, requested_end

        return requested_start, requested_end

    def _get_lookback_limit(self, timeframe: Timeframe) -> timedelta | None:
        """Return maximum supported lookback window for a timeframe."""
        mapping = {
            Timeframe.SECOND_1: timedelta(days=7),
            Timeframe.SECOND_5: timedelta(days=7),
            Timeframe.SECOND_30: timedelta(days=7),
            Timeframe.MINUTE_1: timedelta(days=30),
            Timeframe.MINUTE_5: timedelta(days=60),
            Timeframe.MINUTE_15: timedelta(days=60),
            Timeframe.MINUTE_30: timedelta(days=60),
            Timeframe.HOUR_1: timedelta(days=730),  # ~2 years
            Timeframe.HOUR_4: timedelta(days=730),
        }
        return mapping.get(timeframe)


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


class AlpacaProvider(HistoricalDataProvider):
    """Alpaca historical data provider."""

    def __init__(self, api_key: str, api_secret: str):
        """Initialize Alpaca provider.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
        """
        super().__init__("Alpaca")
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit_delay = 0.3  # 200 calls/min = 3.33 calls/sec
        self._sdk_available = self._check_sdk()
        if not self._sdk_available:
            logger.warning("Alpaca SDK not available. Alpaca provider will be disabled.")

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars from Alpaca.

        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe

        Returns:
            List of historical bars
        """
        if not self._sdk_available:
            logger.debug("Skipping Alpaca fetch because Alpaca SDK is not installed.")
            return []

        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame

            # Create client
            client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.api_secret
            )

            # Convert timeframe
            alpaca_timeframe = self._timeframe_to_alpaca(timeframe)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_timeframe,
                start=start_date,
                end=end_date
            )

            # Fetch data
            bars_dict = client.get_stock_bars(request)

            if symbol not in bars_dict:
                logger.warning(f"No data found for {symbol}")
                return []

            # Convert to HistoricalBar objects
            bars = []
            for bar in bars_dict[symbol]:
                hist_bar = HistoricalBar(
                    timestamp=bar.timestamp,
                    open=Decimal(str(bar.open)),
                    high=Decimal(str(bar.high)),
                    low=Decimal(str(bar.low)),
                    close=Decimal(str(bar.close)),
                    volume=int(bar.volume),
                    source="alpaca"
                )
                bars.append(hist_bar)

            logger.info(f"Fetched {len(bars)} bars from Alpaca for {symbol}")
            return bars

        except Exception as e:
            logger.error(f"Error fetching Alpaca data: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if Alpaca is available."""
        return bool(self.api_key and self.api_secret and self._sdk_available)

    def _timeframe_to_alpaca(self, timeframe: Timeframe):
        """Convert timeframe to Alpaca format.

        Args:
            timeframe: Internal timeframe

        Returns:
            Alpaca TimeFrame object
        """
        from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame, TimeFrameUnit

        mapping = {
            Timeframe.MINUTE_1: AlpacaTimeFrame(1, TimeFrameUnit.Minute),
            Timeframe.MINUTE_5: AlpacaTimeFrame(5, TimeFrameUnit.Minute),
            Timeframe.MINUTE_15: AlpacaTimeFrame(15, TimeFrameUnit.Minute),
            Timeframe.MINUTE_30: AlpacaTimeFrame(30, TimeFrameUnit.Minute),
            Timeframe.HOUR_1: AlpacaTimeFrame(1, TimeFrameUnit.Hour),
            Timeframe.HOUR_4: AlpacaTimeFrame(4, TimeFrameUnit.Hour),
            Timeframe.DAY_1: AlpacaTimeFrame(1, TimeFrameUnit.Day),
            Timeframe.WEEK_1: AlpacaTimeFrame(1, TimeFrameUnit.Week),
            Timeframe.MONTH_1: AlpacaTimeFrame(1, TimeFrameUnit.Month),
        }
        return mapping.get(timeframe, AlpacaTimeFrame(1, TimeFrameUnit.Minute))

    def _check_sdk(self) -> bool:
        """Check whether the Alpaca SDK is installed."""
        try:
            return importlib.util.find_spec("alpaca") is not None
        except Exception:
            return False


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

    def __init__(self, ibkr_adapter: BrokerAdapter | None = None):
        """Initialize history manager.

        Args:
            ibkr_adapter: Optional broker adapter for live IBKR data
        """
        self.providers: dict[DataSource, HistoricalDataProvider] = {}
        self.priority_order = []
        self.stream_client = None  # Real-time stream client

        # Initialize database provider (always available)
        self.providers[DataSource.DATABASE] = DatabaseProvider()
        self._configure_priority()
        self._initialize_providers_from_config(ibkr_adapter)

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

    def set_ibkr_adapter(self, adapter: BrokerAdapter) -> None:
        """Register or update the IBKR provider on-demand."""
        self.register_provider(DataSource.IBKR, IBKRHistoricalProvider(adapter))

    def _configure_priority(self) -> None:
        """Configure provider priority order from settings."""
        profile = config_manager.load_profile()
        market_config = profile.market_data

        live_first = market_config.prefer_live_broker

        if live_first:
            self.priority_order = [
                DataSource.DATABASE,
                DataSource.IBKR,
                DataSource.ALPACA,
                DataSource.ALPHA_VANTAGE,
                DataSource.FINNHUB,
                DataSource.YAHOO
            ]
        else:
            self.priority_order = [
                DataSource.DATABASE,
                DataSource.ALPACA,
                DataSource.ALPHA_VANTAGE,
                DataSource.FINNHUB,
                DataSource.YAHOO,
                DataSource.IBKR
            ]

    def _initialize_providers_from_config(self, ibkr_adapter: BrokerAdapter | None) -> None:
        """Register providers according to configuration and credentials."""
        profile = config_manager.load_profile()
        market_config = profile.market_data

        # Register IBKR if adapter supplied
        if ibkr_adapter:
            self.register_provider(DataSource.IBKR, IBKRHistoricalProvider(ibkr_adapter))

        # Alpaca
        if market_config.alpaca_enabled:
            api_key = config_manager.get_credential("alpaca_api_key")
            api_secret = config_manager.get_credential("alpaca_api_secret")
            if api_key and api_secret:
                self.register_provider(DataSource.ALPACA, AlpacaProvider(api_key, api_secret))
            else:
                logger.warning("Alpaca provider enabled but API credentials not found")

        # Alpha Vantage
        if market_config.alpha_vantage_enabled:
            api_key = config_manager.get_credential("alpha_vantage_api_key")
            if api_key:
                self.register_provider(DataSource.ALPHA_VANTAGE, AlphaVantageProvider(api_key))
            else:
                logger.warning("Alpha Vantage provider enabled but API key not found")

        # Finnhub
        if market_config.finnhub_enabled:
            api_key = config_manager.get_credential("finnhub_api_key")
            if api_key:
                self.register_provider(DataSource.FINNHUB, FinnhubProvider(api_key))
            else:
                logger.warning("Finnhub provider enabled but API key not found")

        # Yahoo Finance (no API key required)
        if market_config.yahoo_enabled:
            self.register_provider(DataSource.YAHOO, YahooFinanceProvider())

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
        if not bars:
            return

        try:
            db_manager = get_db_manager()
            with db_manager.session() as session:
                timestamps = [bar.timestamp for bar in bars]
                min_ts = min(timestamps)
                max_ts = max(timestamps)

                existing_rows = session.query(MarketBar.timestamp).filter(
                    MarketBar.symbol == symbol,
                    MarketBar.timestamp >= min_ts,
                    MarketBar.timestamp <= max_ts
                ).all()
                existing_timestamps = {row[0] for row in existing_rows}

                new_bars = []
                for bar in bars:
                    if bar.timestamp in existing_timestamps:
                        continue
                    new_bars.append(MarketBar(
                        symbol=symbol,
                        timestamp=bar.timestamp,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=bar.volume,
                        vwap=bar.vwap,
                        source=bar.source
                    ))

                if new_bars:
                    session.bulk_save_objects(new_bars)
                    session.commit()
                    logger.debug(f"Stored {len(new_bars)} bars to database")
                else:
                    logger.debug("All fetched bars already cached locally")

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

    async def start_realtime_stream(
        self,
        symbols: list[str],
        enable_indicators: bool = True
    ) -> bool:
        """Start real-time market data streaming.

        Args:
            symbols: List of symbols to stream
            enable_indicators: Enable real-time indicator calculations

        Returns:
            True if stream started successfully
        """
        # Check if Alpha Vantage is available
        if DataSource.ALPHA_VANTAGE not in self.providers:
            logger.error("Alpha Vantage provider not available for streaming")
            return False

        # Get API key from provider
        av_provider = self.providers[DataSource.ALPHA_VANTAGE]
        if not isinstance(av_provider, AlphaVantageProvider):
            logger.error("Invalid Alpha Vantage provider")
            return False

        try:
            # Import stream client (lazy import to avoid circular deps)
            from src.core.market_data.alpha_vantage_stream import AlphaVantageStreamClient

            # Create stream client if not exists
            if not self.stream_client:
                self.stream_client = AlphaVantageStreamClient(
                    api_key=av_provider.api_key,
                    enable_indicators=enable_indicators
                )

            # Connect and subscribe
            connected = await self.stream_client.connect()
            if connected:
                await self.stream_client.subscribe(symbols)
                logger.info(f"Started real-time stream for {len(symbols)} symbols")
                return True
            else:
                logger.error("Failed to connect stream client")
                return False

        except Exception as e:
            logger.error(f"Error starting real-time stream: {e}")
            return False

    async def stop_realtime_stream(self):
        """Stop real-time market data streaming."""
        if self.stream_client:
            await self.stream_client.disconnect()
            logger.info("Stopped real-time stream")

    def get_realtime_tick(self, symbol: str):
        """Get latest real-time tick for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest tick data or None
        """
        if self.stream_client:
            return self.stream_client.get_latest_tick(symbol)
        return None

    def get_stream_metrics(self) -> dict | None:
        """Get real-time stream metrics.

        Returns:
            Dictionary with metrics or None if stream not active
        """
        if self.stream_client:
            return self.stream_client.get_metrics()
        return None

    async def fetch_realtime_indicators(
        self,
        symbol: str,
        interval: str = "1min"
    ) -> dict:
        """Fetch real-time technical indicators.

        Args:
            symbol: Trading symbol
            interval: Time interval

        Returns:
            Dictionary with RSI and MACD data
        """
        if DataSource.ALPHA_VANTAGE not in self.providers:
            return {}

        av_provider = self.providers[DataSource.ALPHA_VANTAGE]
        if not isinstance(av_provider, AlphaVantageProvider):
            return {}

        try:
            # Fetch both indicators in parallel
            rsi_task = av_provider.fetch_rsi(symbol, interval)
            macd_task = av_provider.fetch_macd(symbol, interval)

            rsi_data, macd_data = await asyncio.gather(rsi_task, macd_task)

            result = {}

            # Add RSI if available
            if not rsi_data.empty:
                result["rsi"] = {
                    "value": float(rsi_data.iloc[-1]),
                    "timestamp": rsi_data.index[-1].isoformat(),
                    "series": rsi_data.tail(50).to_dict()  # Last 50 points
                }

            # Add MACD if available
            if not macd_data.empty:
                latest_macd = macd_data.iloc[-1]
                result["macd"] = {
                    "macd": float(latest_macd["macd"]),
                    "signal": float(latest_macd["signal"]),
                    "histogram": float(latest_macd["histogram"]),
                    "timestamp": macd_data.index[-1].isoformat(),
                    "series": macd_data.tail(50).to_dict("index")  # Last 50 points
                }

            return result

        except Exception as e:
            logger.error(f"Error fetching realtime indicators: {e}")
            return {}
