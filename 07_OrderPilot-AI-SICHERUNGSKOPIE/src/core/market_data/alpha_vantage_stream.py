"""Alpha Vantage Real-Time Stream Client.

Provides real-time market data and technical indicators via polling
since Alpha Vantage doesn't offer WebSocket support on free tier.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

import aiohttp
import pandas as pd

from src.common.event_bus import Event, EventType, event_bus
from src.core.market_data.stream_client import MarketTick, StreamClient, StreamStatus

logger = logging.getLogger(__name__)


class AlphaVantageStreamClient(StreamClient):
    """Real-time market data client for Alpha Vantage using polling."""

    def __init__(
        self,
        api_key: str,
        poll_interval: int = 60,  # Poll every 60 seconds (free tier limit)
        buffer_size: int = 1000,
        enable_indicators: bool = True
    ):
        """Initialize Alpha Vantage stream client.

        Args:
            api_key: Alpha Vantage API key
            poll_interval: Polling interval in seconds (min 60 for free tier)
            buffer_size: Size of the data buffer
            enable_indicators: Enable real-time indicator calculations
        """
        super().__init__(
            name="AlphaVantageStream",
            buffer_size=buffer_size,
            heartbeat_interval=poll_interval,
            reconnect_attempts=3,
            max_lag_ms=poll_interval * 1000
        )

        self.api_key = api_key
        self.poll_interval = max(poll_interval, 60)  # Enforce minimum for free tier
        self.base_url = "https://www.alphavantage.co/query"
        self.enable_indicators = enable_indicators

        # Polling state
        self._poll_task = None
        self._stop_event = asyncio.Event()

        # Cache for indicator data
        self._indicator_cache = {}

        logger.info(
            f"Alpha Vantage stream client initialized "
            f"(poll interval: {self.poll_interval}s)"
        )

    async def connect(self) -> bool:
        """Start the polling loop.

        Returns:
            True if connection successful
        """
        if self.connected:
            logger.warning("Already connected")
            return True

        try:
            # Test API key with a simple call
            test_params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "AAPL",
                "apikey": self.api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=test_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "Error Message" in data or "Note" in data:
                            logger.error(f"API key validation failed: {data}")
                            return False

            self.connected = True
            self.metrics.status = StreamStatus.CONNECTED
            self.metrics.connected_at = datetime.utcnow()

            # Start polling task
            self._stop_event.clear()
            self._poll_task = asyncio.create_task(self._poll_loop())

            logger.info("Alpha Vantage stream connected")

            # Emit connection event
            event_bus.emit(Event(
                type=EventType.MARKET_DATA_CONNECTED,
                timestamp=datetime.utcnow(),
                data={"source": self.name}
            ))

            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.metrics.status = StreamStatus.ERROR
            return False

    async def disconnect(self):
        """Stop the polling loop."""
        if not self.connected:
            return

        self._stop_event.set()

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        self.connected = False
        self.metrics.status = StreamStatus.DISCONNECTED

        logger.info("Alpha Vantage stream disconnected")

        # Emit disconnection event
        event_bus.emit(Event(
            type=EventType.MARKET_DATA_DISCONNECTED,
            timestamp=datetime.utcnow(),
            data={"source": self.name}
        ))

    async def subscribe(self, symbols: list[str]):
        """Subscribe to symbols.

        Args:
            symbols: List of symbols to subscribe to
        """
        for symbol in symbols:
            if symbol not in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.add(symbol)
                logger.info(f"Subscribed to {symbol}")

    async def unsubscribe(self, symbols: list[str]):
        """Unsubscribe from symbols.

        Args:
            symbols: List of symbols to unsubscribe from
        """
        for symbol in symbols:
            if symbol in self.metrics.subscribed_symbols:
                self.metrics.subscribed_symbols.remove(symbol)
                logger.info(f"Unsubscribed from {symbol}")

    async def _poll_loop(self):
        """Main polling loop."""
        while not self._stop_event.is_set():
            try:
                # Poll all subscribed symbols
                for symbol in list(self.metrics.subscribed_symbols):
                    await self._poll_symbol(symbol)

                    # Small delay between symbols to avoid rate limiting
                    await asyncio.sleep(1)

                # Wait for next poll interval
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def _poll_symbol(self, symbol: str):
        """Poll data for a single symbol.

        Args:
            symbol: Symbol to poll
        """
        try:
            # Fetch global quote (latest price)
            tick = await self._fetch_global_quote(symbol)

            if tick:
                # Add to buffer
                self.buffer.append(tick)
                self.metrics.messages_received += 1
                self.metrics.last_message_at = datetime.utcnow()

                # Emit tick event
                event_bus.emit(Event(
                    type=EventType.MARKET_DATA_TICK,
                    timestamp=tick.timestamp or datetime.utcnow(),
                    data={
                        "symbol": symbol,
                        "price": float(tick.last) if tick.last else None,
                        "volume": tick.volume,
                        "source": self.name
                    }
                ))

            # Fetch indicators if enabled
            if self.enable_indicators:
                await self._fetch_indicators(symbol)

        except Exception as e:
            logger.error(f"Error polling {symbol}: {e}")

    async def _fetch_global_quote(self, symbol: str) -> MarketTick | None:
        """Fetch global quote for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            MarketTick or None if failed
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }

        try:
            request_time = datetime.utcnow()

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Global Quote" not in data:
                            logger.warning(f"No quote data for {symbol}")
                            return None

                        quote = data["Global Quote"]

                        if not quote:
                            return None

                        # Calculate latency
                        response_time = datetime.utcnow()
                        latency_ms = (response_time - request_time).total_seconds() * 1000
                        self.metrics.update_latency(latency_ms)

                        # Parse quote
                        tick = MarketTick(
                            symbol=symbol,
                            last=Decimal(quote.get("05. price", "0")),
                            volume=int(quote.get("06. volume", "0")),
                            timestamp=datetime.utcnow(),
                            source=self.name,
                            latency_ms=latency_ms
                        )

                        return tick
                    else:
                        logger.error(f"API error {response.status} for {symbol}")
                        return None

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    async def _fetch_indicators(self, symbol: str):
        """Fetch technical indicators for a symbol.

        Args:
            symbol: Trading symbol
        """
        # Throttle indicator requests (max once per 5 minutes per symbol)
        cache_key = f"{symbol}_indicators"
        last_fetch = self._indicator_cache.get(cache_key)

        if last_fetch and (datetime.utcnow() - last_fetch) < timedelta(minutes=5):
            return

        try:
            # Fetch RSI
            rsi_data = await self._fetch_rsi(symbol)

            # Fetch MACD
            macd_data = await self._fetch_macd(symbol)

            # Update cache
            self._indicator_cache[cache_key] = datetime.utcnow()

            # Emit indicator event
            if not rsi_data.empty or not macd_data.empty:
                event_bus.emit(Event(
                    type=EventType.INDICATOR_CALCULATED,
                    timestamp=datetime.utcnow(),
                    data={
                        "symbol": symbol,
                        "source": self.name,
                        "rsi": rsi_data.iloc[-1] if not rsi_data.empty else None,
                        "macd": macd_data.iloc[-1].to_dict() if not macd_data.empty else None
                    }
                ))

        except Exception as e:
            logger.error(f"Error fetching indicators for {symbol}: {e}")

    async def _fetch_rsi(self, symbol: str, interval: str = "1min") -> pd.Series:
        """Fetch RSI indicator.

        Args:
            symbol: Trading symbol
            interval: Time interval

        Returns:
            Pandas Series with RSI values
        """
        params = {
            "function": "RSI",
            "symbol": symbol,
            "interval": interval,
            "time_period": 14,
            "series_type": "close",
            "apikey": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Technical Analysis: RSI" not in data:
                            return pd.Series()

                        rsi_data = {}
                        for ts, values in data["Technical Analysis: RSI"].items():
                            rsi_data[datetime.fromisoformat(ts)] = float(values["RSI"])

                        return pd.Series(rsi_data).sort_index()
                    else:
                        return pd.Series()

        except Exception as e:
            logger.error(f"Error fetching RSI: {e}")
            return pd.Series()

    async def _fetch_macd(self, symbol: str, interval: str = "1min") -> pd.DataFrame:
        """Fetch MACD indicator.

        Args:
            symbol: Trading symbol
            interval: Time interval

        Returns:
            DataFrame with MACD values
        """
        params = {
            "function": "MACD",
            "symbol": symbol,
            "interval": interval,
            "series_type": "close",
            "apikey": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Technical Analysis: MACD" not in data:
                            return pd.DataFrame()

                        macd_data = []
                        for ts, values in data["Technical Analysis: MACD"].items():
                            macd_data.append({
                                "timestamp": datetime.fromisoformat(ts),
                                "macd": float(values["MACD"]),
                                "signal": float(values["MACD_Signal"]),
                                "histogram": float(values["MACD_Hist"])
                            })

                        df = pd.DataFrame(macd_data)
                        df.set_index("timestamp", inplace=True)
                        return df.sort_index()
                    else:
                        return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching MACD: {e}")
            return pd.DataFrame()

    def get_latest_tick(self, symbol: str) -> MarketTick | None:
        """Get the latest tick for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest MarketTick or None
        """
        for tick in reversed(self.buffer):
            if tick.symbol == symbol:
                return tick
        return None

    def get_metrics(self) -> dict:
        """Get stream metrics.

        Returns:
            Dictionary with metrics
        """
        return {
            "status": self.metrics.status.value,
            "connected_at": self.metrics.connected_at.isoformat() if self.metrics.connected_at else None,
            "last_message_at": self.metrics.last_message_at.isoformat() if self.metrics.last_message_at else None,
            "messages_received": self.metrics.messages_received,
            "average_latency_ms": self.metrics.average_latency_ms,
            "subscribed_symbols": list(self.metrics.subscribed_symbols),
            "poll_interval": self.poll_interval
        }
