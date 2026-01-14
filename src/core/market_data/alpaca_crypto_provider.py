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
        timeframe: Timeframe,
        progress_callback: callable = None,
    ) -> list[HistoricalBar]:
        """Fetch historical crypto bars from Alpaca.

        Args:
            symbol: Crypto trading pair (e.g., "BTC/USD", "ETH/USD", "SOL/USDT")
            start_date: Start date for data
            end_date: End date for data
            timeframe: Bar timeframe
            progress_callback: Optional callback(batch_num, total_bars, status_msg) for progress updates

        Returns:
            List of historical bars
        """
        if not self._sdk_available:
            logger.debug("Skipping Alpaca crypto fetch - SDK not installed")
            return []

        try:
            # Import required modules
            from alpaca.data.historical import CryptoHistoricalDataClient
            from alpaca.data.requests import CryptoBarsRequest
            from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame

            # Create client
            client = self._create_crypto_client(CryptoHistoricalDataClient)

            # Prepare request parameters
            alpaca_symbol, alpaca_timeframe, start_utc, end_utc, needs_chunking = (
                self._prepare_fetch_parameters(symbol, timeframe, start_date, end_date)
            )

            # Fetch bars (chunked or single request)
            if needs_chunking:
                all_bars = await self._fetch_bars_chunked(
                    client, CryptoBarsRequest, alpaca_symbol,
                    alpaca_timeframe, start_utc, end_utc,
                    progress_callback, symbol
                )
            else:
                all_bars = await self._fetch_bars_single(
                    client, CryptoBarsRequest, alpaca_symbol,
                    alpaca_timeframe, start_utc, end_utc, symbol
                )

            return all_bars

        except Exception as e:
            return self._handle_fetch_error(e)

    def _create_crypto_client(self, ClientClass):
        """Create Alpaca crypto client with or without API keys.

        Args:
            ClientClass: CryptoHistoricalDataClient class.

        Returns:
            Configured client instance.
        """
        if self.api_key and self.api_secret:
            client = ClientClass(api_key=self.api_key, secret_key=self.api_secret)
            logger.debug("Alpaca crypto client created with API keys")
        else:
            client = ClientClass()
            logger.debug("Alpaca crypto client created without API keys (market data only)")
        return client

    def _prepare_fetch_parameters(
        self, symbol: str, timeframe: Timeframe,
        start_date: datetime, end_date: datetime
    ) -> tuple:
        """Prepare fetch parameters (symbol, timeframe, dates, chunking flag).

        Args:
            symbol: Original symbol.
            timeframe: Timeframe.
            start_date: Start date.
            end_date: End date.

        Returns:
            Tuple of (alpaca_symbol, alpaca_timeframe, start_utc, end_utc, needs_chunking).
        """
        # Convert timeframe and symbol
        alpaca_timeframe = self._timeframe_to_alpaca(timeframe)
        alpaca_symbol = self._convert_symbol_to_alpaca_format(symbol)

        # Convert to UTC if timezone-aware
        start_utc = self._ensure_utc_naive(start_date)
        end_utc = self._ensure_utc_naive(end_date)

        # Calculate time span to determine if chunking is needed
        time_span = end_utc - start_utc
        needs_chunking = time_span.days > 31  # Chunk if more than 1 month

        logger.info(
            f"Alpaca crypto request: {alpaca_symbol} (from {symbol}), "
            f"timeframe={timeframe.value}, "
            f"start={start_utc}, "
            f"end={end_utc}, "
            f"span={time_span.days} days, "
            f"chunking={'yes' if needs_chunking else 'no'}"
        )

        return alpaca_symbol, alpaca_timeframe, start_utc, end_utc, needs_chunking

    async def _fetch_bars_chunked(
        self, client, RequestClass, alpaca_symbol: str,
        alpaca_timeframe, start_utc: datetime, end_utc: datetime,
        progress_callback, original_symbol: str
    ) -> list[HistoricalBar]:
        """Fetch bars in chunks for long time periods.

        Args:
            client: Alpaca client.
            RequestClass: CryptoBarsRequest class.
            alpaca_symbol: Converted Alpaca symbol.
            alpaca_timeframe: Converted timeframe.
            start_utc: Start date UTC.
            end_utc: End date UTC.
            progress_callback: Progress callback function.
            original_symbol: Original symbol for logging.

        Returns:
            List of HistoricalBar objects.
        """
        from dateutil.relativedelta import relativedelta

        all_bars = []
        current_start = start_utc
        chunk_num = 0

        while current_start < end_utc:
            current_end = min(
                current_start + relativedelta(months=1),
                end_utc
            )

            chunk_num += 1
            logger.debug(f"Chunk {chunk_num}: {current_start.date()} to {current_end.date()}")

            # Progress callback with detailed info
            if progress_callback:
                progress_callback(
                    chunk_num,
                    len(all_bars),
                    f"Chunk {chunk_num}: {len(all_bars):,} Bars geladen, "
                    f"aktuell bei {current_end.strftime('%d.%m.%Y')}"
                )

            # Fetch chunk
            request = RequestClass(
                symbol_or_symbols=alpaca_symbol,
                timeframe=alpaca_timeframe,
                start=current_start,
                end=current_end
            )

            bars_response = await asyncio.to_thread(client.get_crypto_bars, request)

            # Convert chunk to HistoricalBar objects
            chunk_bars = self._convert_bars_to_historical(bars_response, alpaca_symbol)
            all_bars.extend(chunk_bars)

            # Move to next chunk
            current_start = current_end

            # Rate limiting between chunks
            if current_start < end_utc:
                await asyncio.sleep(self.rate_limit_delay)

        logger.info(
            f"Fetched {len(all_bars)} crypto bars from Alpaca for {original_symbol} "
            f"({chunk_num} chunks)"
        )
        return all_bars

    async def _fetch_bars_single(
        self, client, RequestClass, alpaca_symbol: str,
        alpaca_timeframe, start_utc: datetime, end_utc: datetime,
        original_symbol: str
    ) -> list[HistoricalBar]:
        """Fetch bars with single request for short time periods.

        Args:
            client: Alpaca client.
            RequestClass: CryptoBarsRequest class.
            alpaca_symbol: Converted Alpaca symbol.
            alpaca_timeframe: Converted timeframe.
            start_utc: Start date UTC.
            end_utc: End date UTC.
            original_symbol: Original symbol for logging.

        Returns:
            List of HistoricalBar objects.
        """
        request = RequestClass(
            symbol_or_symbols=alpaca_symbol,
            timeframe=alpaca_timeframe,
            start=start_utc,
            end=end_utc
        )

        bars_response = await asyncio.to_thread(client.get_crypto_bars, request)

        # Check response (use alpaca_symbol to access data)
        if not hasattr(bars_response, 'data') or alpaca_symbol not in bars_response.data:
            logger.warning(f"No crypto data found for {alpaca_symbol} (from {original_symbol}) from Alpaca")
            if hasattr(bars_response, 'data'):
                logger.debug(f"Available symbols: {list(bars_response.data.keys())}")
            return []

        # Convert to HistoricalBar objects
        all_bars = self._convert_bars_to_historical(bars_response, alpaca_symbol)

        logger.info(f"Fetched {len(all_bars)} crypto bars from Alpaca for {original_symbol}")
        return all_bars

    def _convert_bars_to_historical(
        self, bars_response, alpaca_symbol: str
    ) -> list[HistoricalBar]:
        """Convert Alpaca bar response to HistoricalBar objects.

        Args:
            bars_response: Response from Alpaca API.
            alpaca_symbol: Symbol used in request.

        Returns:
            List of HistoricalBar objects.
        """
        hist_bars = []

        if hasattr(bars_response, 'data') and alpaca_symbol in bars_response.data:
            for bar in bars_response.data[alpaca_symbol]:
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
                hist_bars.append(hist_bar)

        return hist_bars

    def _handle_fetch_error(self, error: Exception) -> list[HistoricalBar]:
        """Handle fetch error and return empty list.

        Args:
            error: Exception that occurred.

        Returns:
            Empty list.
        """
        error_str = str(error)
        self.last_error = error_str
        if "401" in error_str or "authorization" in error_str.lower():
            self.auth_failed = True
        logger.error(f"Error fetching Alpaca crypto data: {error}")
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

    def _convert_symbol_to_alpaca_format(self, symbol: str) -> str:
        """Convert symbol to Alpaca Crypto format.

        Alpaca Crypto expects format: BASE/QUOTE (e.g., "BTC/USDT", "ETH/USD")
        Our internal format may be: BASEUSDT (e.g., "BTCUSDT", "ETHUSD")

        Args:
            symbol: Symbol in internal format (e.g., "BTCUSDT")

        Returns:
            Symbol in Alpaca format (e.g., "BTC/USDT")
        """
        # If already has slash, return as-is
        if "/" in symbol:
            return symbol

        # Try to split common quote currencies
        for quote in ["USDT", "USD", "EUR", "BTC", "ETH"]:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"

        # If no known quote currency found, return as-is and let API handle it
        logger.warning(f"Could not convert symbol to Alpaca format: {symbol}")
        return symbol

    def _check_sdk(self) -> bool:
        """Check whether the Alpaca SDK is installed.

        Returns:
            True if SDK is available
        """
        try:
            return importlib.util.find_spec("alpaca") is not None
        except Exception:
            return False
