"""Alpaca Cryptocurrency Historical Data Provider.

Provides historical crypto market data using Alpaca's Crypto Data API.
Endpoint: /v1beta3/crypto/us/*
"""

import asyncio
import importlib.util
import logging
from datetime import datetime, timezone

import pandas as pd

from src.core.market_data.history_provider import (
    HistoricalBar,
    HistoricalDataProvider,
    Timeframe
)

logger = logging.getLogger(__name__)


class AlpacaCryptoProvider(HistoricalDataProvider):
    """Alpaca cryptocurrency historical data provider.

    Uses Alpaca's Crypto Data API:
    - Endpoint: https://data.alpaca.markets/v1beta3/crypto/us/
    - Supported trading pairs: BTC/USD, ETH/USD, ETH/BTC, SOL/USDT, etc.
    - Free tier: 200 API calls/minute
    - Real-time data available via WebSocket (see AlpacaCryptoStreamClient)
    """

    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        """Initialize Alpaca crypto provider.

        Args:
            api_key: Alpaca API key (optional for crypto market data)
            api_secret: Alpaca API secret (optional for crypto market data)

        Note:
            For pure crypto market data, API keys are NOT required.
            Keys are only needed for trading operations.
        """
        super().__init__("AlpacaCrypto")
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit_delay = 0.3  # 200 calls/min = 3.33 calls/sec
        self._sdk_available = self._check_sdk()
        self.auth_failed = False
        self.last_error: str | None = None

        if not self._sdk_available:
            logger.warning("Alpaca SDK not available. Crypto provider will be disabled.")
        else:
            logger.info("AlpacaCryptoProvider initialized")

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical crypto bars from Alpaca.

        Args:
            symbol: Crypto trading pair (e.g., "BTC/USD", "ETH/USD", "SOL/USDT")
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe

        Returns:
            List of historical bars
        """
        if not self._sdk_available:
            logger.debug("Skipping Alpaca crypto fetch - SDK not installed")
            return []

        try:
            from alpaca.data.historical import CryptoHistoricalDataClient
            from alpaca.data.requests import CryptoBarsRequest
            from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame
            from dateutil.relativedelta import relativedelta

            # Create client (keys are optional for crypto market data)
            if self.api_key and self.api_secret:
                client = CryptoHistoricalDataClient(
                    api_key=self.api_key,
                    secret_key=self.api_secret
                )
                logger.debug("Alpaca crypto client created with API keys")
            else:
                client = CryptoHistoricalDataClient()
                logger.debug("Alpaca crypto client created without API keys (market data only)")

            # Convert timeframe
            alpaca_timeframe = self._timeframe_to_alpaca(timeframe)

            # Convert to UTC if timezone-aware
            start_date_utc = self._ensure_utc_naive(start_date)
            end_date_utc = self._ensure_utc_naive(end_date)

            # Calculate time span to determine if chunking is needed
            time_span = end_date_utc - start_date_utc
            needs_chunking = time_span.days > 31  # Chunk if more than 1 month

            logger.info(
                f"Alpaca crypto request: {symbol}, "
                f"timeframe={timeframe.value}, "
                f"start={start_date_utc}, "
                f"end={end_date_utc}, "
                f"span={time_span.days} days, "
                f"chunking={'yes' if needs_chunking else 'no'}"
            )

            all_bars = []

            if needs_chunking:
                # Chunk requests by month to avoid hitting limits
                current_start = start_date_utc
                chunk_num = 0

                while current_start < end_date_utc:
                    current_end = min(
                        current_start + relativedelta(months=1),
                        end_date_utc
                    )

                    chunk_num += 1
                    logger.debug(
                        f"Chunk {chunk_num}: {current_start.date()} to {current_end.date()}"
                    )

                    request = CryptoBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=alpaca_timeframe,
                        start=current_start,
                        end=current_end
                    )

                    # Fetch chunk
                    bars_response = await asyncio.to_thread(
                        client.get_crypto_bars, request
                    )

                    # Convert chunk to HistoricalBar objects
                    if hasattr(bars_response, 'data') and symbol in bars_response.data:
                        for bar in bars_response.data[symbol]:
                            hist_bar = HistoricalBar(
                                timestamp=bar.timestamp,
                                open=bar.open,
                                high=bar.high,
                                low=bar.low,
                                close=bar.close,
                                volume=int(bar.volume) if bar.volume else 0,
                                vwap=bar.vwap if hasattr(bar, 'vwap') else None,
                                trades=bar.trade_count if hasattr(bar, 'trade_count') else None,
                                source="alpaca_crypto"
                            )
                            all_bars.append(hist_bar)

                    # Move to next chunk
                    current_start = current_end

                    # Rate limiting between chunks
                    if current_start < end_date_utc:
                        await asyncio.sleep(self.rate_limit_delay)

                logger.info(
                    f"Fetched {len(all_bars)} crypto bars from Alpaca for {symbol} "
                    f"({chunk_num} chunks)"
                )
            else:
                # Single request for short time spans
                request = CryptoBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=alpaca_timeframe,
                    start=start_date_utc,
                    end=end_date_utc
                )

                bars_response = await asyncio.to_thread(client.get_crypto_bars, request)

                # Check response
                if not hasattr(bars_response, 'data') or symbol not in bars_response.data:
                    logger.warning(f"No crypto data found for {symbol} from Alpaca")
                    if hasattr(bars_response, 'data'):
                        logger.debug(f"Available symbols: {list(bars_response.data.keys())}")
                    return []

                # Convert to HistoricalBar objects
                for bar in bars_response.data[symbol]:
                    hist_bar = HistoricalBar(
                        timestamp=bar.timestamp,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=int(bar.volume) if bar.volume else 0,
                        vwap=bar.vwap if hasattr(bar, 'vwap') else None,
                        trades=bar.trade_count if hasattr(bar, 'trade_count') else None,
                        source="alpaca_crypto"
                    )
                    all_bars.append(hist_bar)

                logger.info(f"Fetched {len(all_bars)} crypto bars from Alpaca for {symbol}")

            return all_bars

        except Exception as e:
            error_str = str(e)
            self.last_error = error_str
            if "401" in error_str or "authorization" in error_str.lower():
                self.auth_failed = True
            logger.error(f"Error fetching Alpaca crypto data: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if Alpaca crypto provider is available.

        Returns:
            True if provider is available (SDK is sufficient, keys are optional for market data)
        """
        return self._sdk_available

    def _ensure_utc_naive(self, dt: datetime) -> datetime:
        """Convert datetime to UTC naive datetime.

        Args:
            dt: Datetime to convert

        Returns:
            UTC naive datetime
        """
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

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
        """Check whether the Alpaca SDK is installed.

        Returns:
            True if SDK is available
        """
        try:
            return importlib.util.find_spec("alpaca") is not None
        except Exception:
            return False
