"""IBKR Historical Data Provider.

Provides historical market data from Interactive Brokers.
"""

import logging
from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.core.broker import BrokerAdapter
from src.core.market_data.types import HistoricalBar, Timeframe

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


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
        """Fetch historical bars from IBKR."""
        # Check cache first
        cache_key = self._cache_key(symbol, start_date, end_date, timeframe)
        if cache_key in self.cache:
            logger.debug(f"Using cached data for {symbol}")
            return self._df_to_bars(self.cache[cache_key])

        # Convert timeframe to IBKR format
        duration = self._calculate_duration(start_date, end_date)
        bar_size = self._timeframe_to_ibkr(timeframe)

        try:
            bars_data = await self.adapter.get_historical_bars(
                symbol=symbol,
                duration=duration,
                bar_size=bar_size
            )

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
        """Calculate IBKR duration string."""
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
        """Convert timeframe to IBKR format."""
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
