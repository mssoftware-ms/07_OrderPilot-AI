"""Finnhub Historical Data Provider.

Provides historical market data from Finnhub API.
"""

import logging
from datetime import datetime
from decimal import Decimal

import aiohttp

from src.core.market_data.types import HistoricalBar, Timeframe

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


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
        """Fetch historical bars from Finnhub."""
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
        """Convert timeframe to Finnhub format."""
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
