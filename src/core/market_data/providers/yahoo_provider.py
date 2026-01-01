"""Yahoo Finance Historical Data Provider.

Provides free historical market data from Yahoo Finance.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import aiohttp

from src.core.market_data.types import HistoricalBar, Timeframe

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


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
        effective_start, effective_end = self._clamp_date_range_yahoo(
            start_date,
            end_date,
            timeframe
        )

        cache_key = self._cache_key(symbol, effective_start, effective_end, timeframe)
        if cache_key in self.cache:
            return self._df_to_bars(self.cache[cache_key])

        interval = self._timeframe_to_yahoo(timeframe)

        params = self._build_params(effective_start, effective_end, interval)
        endpoint = f"{self.base_url}/{symbol}"

        try:
            data = await self._fetch_yahoo_data(endpoint, params, symbol)
            if not data:
                return []

            parsed = self._parse_chart_response(data, symbol)
            if not parsed:
                return []

            timestamps, opens, highs, lows, closes, volumes = parsed
            bars = self._build_bars(
                timestamps,
                opens,
                highs,
                lows,
                closes,
                volumes,
                effective_start,
                effective_end,
            )

            if not bars:
                logger.warning(f"Yahoo Finance returned empty dataset for {symbol}")
                return []

            logger.info(f"Fetched {len(bars)} bars from Yahoo Finance for {symbol}")
            return bars

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data: {e}")
            return []

    def _build_params(self, start: datetime, end: datetime, interval: str) -> dict[str, str | int]:
        return {
            "period1": self._to_unix(start),
            "period2": self._to_unix(end),
            "interval": interval,
            "includePrePost": "false",
            "events": "div,splits",
        }

    async def _fetch_yahoo_data(
        self,
        endpoint: str,
        params: dict[str, str | int],
        symbol: str,
    ) -> dict | None:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            backoff = 1.5
            last_error_status = None

            for attempt in range(self.max_retries):
                async with session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        return await response.json()

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
                            retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        backoff *= 2
                        continue

                    logger.error(f"Yahoo Finance API error ({response.status}) for {symbol}")
                    return None

            logger.error(f"Yahoo Finance API error ({last_error_status}) for {symbol}")
            return None

    def _parse_chart_response(self, data: dict, symbol: str):
        chart_data = data.get("chart", {})
        results = chart_data.get("result", [])
        if not results:
            logger.error(f"Yahoo Finance returned no data for {symbol}")
            return None

        result = results[0]
        timestamps = result.get("timestamp", [])
        indicators = result.get("indicators", {})
        quote_data = indicators.get("quote", [])

        if not timestamps or not quote_data:
            logger.error(f"Incomplete Yahoo Finance data for {symbol}")
            return None

        quote = quote_data[0]
        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        closes = quote.get("close", [])
        volumes = quote.get("volume", [])
        return timestamps, opens, highs, lows, closes, volumes

    def _build_bars(
        self,
        timestamps: list,
        opens: list,
        highs: list,
        lows: list,
        closes: list,
        volumes: list,
        effective_start: datetime,
        effective_end: datetime,
    ) -> list[HistoricalBar]:
        bars: list[HistoricalBar] = []
        for idx, ts in enumerate(timestamps):
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

            bars.append(
                HistoricalBar(
                    timestamp=timestamp,
                    open=Decimal(str(bar_open)),
                    high=Decimal(str(bar_high)),
                    low=Decimal(str(bar_low)),
                    close=Decimal(str(bar_close)),
                    volume=bar_volume,
                    source="yahoo",
                )
            )
        return bars

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

    def _to_unix(self, value: datetime) -> int:
        """Convert datetime to UTC UNIX timestamp."""
        if value.tzinfo is None:
            return int(value.replace(tzinfo=timezone.utc).timestamp())
        return int(value.astimezone(timezone.utc).timestamp())

    def _clamp_date_range_yahoo(
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
