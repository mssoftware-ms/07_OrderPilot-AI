"""Alpaca Historical Data Provider for Stocks.

Provides historical market data from Alpaca Markets API.
"""

import asyncio
import importlib.util
import logging
from datetime import datetime, timezone
from decimal import Decimal

from src.core.market_data.types import HistoricalBar, Timeframe

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


class AlpacaProvider(HistoricalDataProvider):
    """Alpaca historical data provider for stocks."""

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

            # Convert timezone-aware datetimes to UTC if needed
            if start_date.tzinfo is not None:
                start_date_utc = start_date.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                start_date_utc = start_date

            if end_date.tzinfo is not None:
                end_date_utc = end_date.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                end_date_utc = end_date

            logger.info(f"Alpaca request: {symbol}, timeframe={timeframe.value}, start={start_date_utc}, end={end_date_utc}")

            # Create request - USE IEX FEED (FREE TIER)
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_timeframe,
                start=start_date_utc,
                end=end_date_utc,
                feed="iex"  # IEX feed - free tier compatible
            )
            logger.debug(f"Using IEX feed for {symbol} (free tier compatible)")

            # Fetch data - run in thread to avoid blocking event loop
            bars_response = await asyncio.to_thread(client.get_stock_bars, request)

            # BarSet.data is a Dict[str, List[Bar]]
            if not hasattr(bars_response, 'data') or symbol not in bars_response.data:
                logger.warning(f"No data found for {symbol} from Alpaca")
                logger.debug(f"Response type: {type(bars_response)}")
                if hasattr(bars_response, 'data'):
                    logger.debug(f"Available symbols: {list(bars_response.data.keys())}")
                return []

            # Convert to HistoricalBar objects
            bars = []
            for bar in bars_response.data[symbol]:
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
            Timeframe.MINUTE_10: AlpacaTimeFrame(10, TimeFrameUnit.Minute),
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
