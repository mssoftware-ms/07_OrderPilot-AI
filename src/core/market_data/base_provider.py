"""Base Historical Data Provider.

Abstract base class for historical market data providers with template methods.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pandas as pd

from .types import HistoricalBar, Timeframe

logger = logging.getLogger(__name__)


class HistoricalDataProvider(ABC):
    """Abstract base class for historical data providers with template methods.

    Provides common functionality for data providers:
    - Caching support
    - Data conversion helpers
    - Rate limiting
    - Template method pattern for fetch operation

    Subclasses should implement:
    - _fetch_data_from_source() - provider-specific data fetching
    - is_available() - check provider availability
    """

    def __init__(self, name: str, enable_cache: bool = True):
        """Initialize provider.

        Args:
            name: Provider name
            enable_cache: Enable response caching
        """
        self.name = name
        self.cache: dict[str, pd.DataFrame] = {}
        self.enable_cache = enable_cache
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

    # ==================== Template Method Pattern (Optional) ====================

    async def fetch_bars_with_cache(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch bars with caching support (template method).

        This provides a standard fetch pattern:
        1. Check cache
        2. Fetch from source if not cached
        3. Convert to bars
        4. Cache results

        Providers can optionally use this instead of fetch_bars for caching support.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe

        Returns:
            List of historical bars
        """
        # Step 1: Check cache
        cache_key = self._cache_key(symbol, start_date, end_date, timeframe)
        if self.enable_cache and cache_key in self.cache:
            logger.debug(f"Cache hit for {symbol} from {self.name}")
            return self._df_to_bars(self.cache[cache_key])

        # Step 2: Fetch from source (provider-specific)
        df = await self._fetch_data_from_source(symbol, start_date, end_date, timeframe)

        # Step 3: Cache results
        if self.enable_cache and not df.empty:
            self.cache[cache_key] = df

        # Step 4: Convert to bars
        return self._df_to_bars(df)

    async def _fetch_data_from_source(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> pd.DataFrame:
        """Fetch data from provider source.

        Subclasses should implement this to provide provider-specific logic
        when using the fetch_bars_with_cache template method.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe

        Returns:
            DataFrame with OHLCV data and timestamp index

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _fetch_data_from_source() "
            "to use fetch_bars_with_cache() template method"
        )

    # ==================== Shared Helper Methods ====================

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

    def _df_to_bars(self, df: pd.DataFrame) -> list[HistoricalBar]:
        """Convert DataFrame to HistoricalBar list.

        Standard conversion method shared across all providers.

        Args:
            df: DataFrame with OHLCV data and timestamp index

        Returns:
            List of HistoricalBar objects
        """
        if df.empty:
            return []

        bars = []
        for timestamp, row in df.iterrows():
            try:
                bar = HistoricalBar(
                    timestamp=timestamp if isinstance(timestamp, datetime) else pd.Timestamp(timestamp).to_pydatetime(),
                    open=Decimal(str(row['open'])),
                    high=Decimal(str(row['high'])),
                    low=Decimal(str(row['low'])),
                    close=Decimal(str(row['close'])),
                    volume=int(row['volume']),
                    source=self.name.lower()
                )
                bars.append(bar)
            except (KeyError, ValueError, TypeError) as e:
                logger.debug(f"Skipping invalid bar at {timestamp}: {e}")
                continue

        return bars

    def _to_unix_timestamp(self, dt: datetime) -> int:
        """Convert datetime to UTC UNIX timestamp.

        Args:
            dt: Datetime to convert

        Returns:
            UNIX timestamp as integer
        """
        if dt.tzinfo is None:
            return int(dt.replace(tzinfo=timezone.utc).timestamp())
        return int(dt.astimezone(timezone.utc).timestamp())

    def _clamp_date_range(
        self,
        requested_start: datetime,
        requested_end: datetime,
        max_lookback_days: int | None = None
    ) -> tuple[datetime, datetime]:
        """Clamp date range to provider limits.

        Args:
            requested_start: Requested start date
            requested_end: Requested end date
            max_lookback_days: Maximum lookback in days (None for unlimited)

        Returns:
            Tuple of (clamped_start, clamped_end)
        """
        if max_lookback_days is None:
            return requested_start, requested_end

        max_lookback = timedelta(days=max_lookback_days)
        earliest_supported = requested_end - max_lookback

        if requested_start < earliest_supported:
            logger.debug(
                f"{self.name}: Start date {requested_start.date()} adjusted to "
                f"{earliest_supported.date()} (max lookback: {max_lookback_days} days)"
            )
            return earliest_supported, requested_end

        return requested_start, requested_end
