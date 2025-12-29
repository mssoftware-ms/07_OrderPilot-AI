"""Alpha Vantage Historical Data Provider.

Provides historical market data and technical indicators from Alpha Vantage API.
"""

import logging
from datetime import datetime
from decimal import Decimal

import aiohttp
import pandas as pd

from src.core.market_data.types import HistoricalBar, Timeframe

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


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
        """Fetch historical bars from Alpha Vantage."""
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
            time_key = "Time Series (1min)"

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

                        bars = []
                        time_series = data[time_key]

                        for timestamp_str, ohlcv in time_series.items():
                            timestamp = datetime.fromisoformat(timestamp_str)

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
        """Convert timeframe to Alpha Vantage format."""
        mapping = {
            Timeframe.MINUTE_1: "1min",
            Timeframe.MINUTE_5: "5min",
            Timeframe.MINUTE_15: "15min",
            Timeframe.MINUTE_30: "30min",
            Timeframe.HOUR_1: "60min"
        }
        return mapping.get(timeframe, "1min")

    async def fetch_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close"
    ) -> dict:
        """Fetch technical indicator from Alpha Vantage."""
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
        """Fetch RSI (Relative Strength Index) from Alpha Vantage."""
        data = await self.fetch_technical_indicator(
            symbol, "RSI", interval, time_period, series_type
        )

        if not data:
            return pd.Series()

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
        """Fetch MACD from Alpha Vantage."""
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
