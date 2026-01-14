"""
Binance Exchange Info Fetcher

Fetches and caches trading pair metadata like tickSize from Binance API.
Implements periodic refresh and error recovery.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import aiohttp


logger = logging.getLogger(__name__)


@dataclass
class SymbolInfo:
    """Trading symbol metadata from Binance."""

    symbol: str
    tick_size: float  # Minimum price increment
    step_size: float  # Minimum quantity increment
    min_qty: float    # Minimum order quantity
    max_qty: float    # Maximum order quantity
    min_notional: float  # Minimum order notional value

    def round_price(self, price: float) -> float:
        """Round price to valid tick size."""
        if self.tick_size <= 0:
            return price
        return round(price / self.tick_size) * self.tick_size

    def round_quantity(self, qty: float) -> float:
        """Round quantity to valid step size."""
        if self.step_size <= 0:
            return qty
        return round(qty / self.step_size) * self.step_size


class ExchangeInfoFetcher:
    """
    Fetches and caches trading symbol metadata from Binance.

    Features:
    - Caches exchangeInfo to reduce API calls
    - Automatic refresh on expiry or error
    - Fallback defaults if API unavailable
    """

    BASE_URL = "https://fapi.binance.com"
    ENDPOINT = "/fapi/v1/exchangeInfo"
    CACHE_TTL = timedelta(hours=12)  # Refresh every 12 hours
    REQUEST_TIMEOUT = 10.0  # seconds

    def __init__(self):
        """Initialize exchange info fetcher."""
        self._cache: Dict[str, SymbolInfo] = {}
        self._last_fetch: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._fetch_lock = asyncio.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def get_symbol_info(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Optional[SymbolInfo]:
        """
        Get symbol metadata, fetching from API if cache expired.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            force_refresh: Force API fetch even if cache valid

        Returns:
            SymbolInfo or None if symbol not found
        """
        symbol = symbol.upper()

        # Check cache
        if not force_refresh and self._is_cache_valid():
            if symbol in self._cache:
                logger.debug(f"Cache hit for {symbol}")
                return self._cache[symbol]

        # Fetch from API
        async with self._fetch_lock:
            # Double-check after acquiring lock
            if not force_refresh and self._is_cache_valid():
                if symbol in self._cache:
                    return self._cache[symbol]

            await self._fetch_exchange_info()
            return self._cache.get(symbol)

    async def get_tick_size(
        self,
        symbol: str,
        default: float = 0.01
    ) -> float:
        """
        Get tick size for symbol, with fallback default.

        Args:
            symbol: Trading pair symbol
            default: Default tick size if not found

        Returns:
            Tick size as float
        """
        info = await self.get_symbol_info(symbol)
        return info.tick_size if info else default

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._last_fetch is None:
            return False
        age = datetime.now() - self._last_fetch
        return age < self.CACHE_TTL

    async def _fetch_exchange_info(self) -> None:
        """Fetch exchange info from Binance API and update cache."""
        url = f"{self.BASE_URL}{self.ENDPOINT}"

        logger.info(f"Fetching exchange info from {url}...")

        try:
            # Create session if not exists
            if self._session is None:
                self._session = aiohttp.ClientSession()

            async with self._session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(
                        f"Failed to fetch exchange info: "
                        f"status={resp.status}, body={text}"
                    )
                    return

                data = await resp.json()
                self._parse_and_cache(data)
                self._last_fetch = datetime.now()

                logger.info(f"Cached info for {len(self._cache)} symbols")

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching exchange info after {self.REQUEST_TIMEOUT}s")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching exchange info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching exchange info: {e}", exc_info=True)

    def _parse_and_cache(self, data: Dict[str, Any]) -> None:
        """Parse exchange info response and update cache."""
        symbols = data.get("symbols", [])

        for symbol_data in symbols:
            try:
                symbol = symbol_data.get("symbol")
                if not symbol:
                    continue

                # Extract filters
                filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}

                price_filter = filters.get("PRICE_FILTER", {})
                lot_size_filter = filters.get("LOT_SIZE", {})
                min_notional_filter = filters.get("MIN_NOTIONAL", {})

                info = SymbolInfo(
                    symbol=symbol,
                    tick_size=float(price_filter.get("tickSize", 0.01)),
                    step_size=float(lot_size_filter.get("stepSize", 0.001)),
                    min_qty=float(lot_size_filter.get("minQty", 0)),
                    max_qty=float(lot_size_filter.get("maxQty", float("inf"))),
                    min_notional=float(min_notional_filter.get("notional", 0)),
                )

                self._cache[symbol] = info

            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse symbol {symbol_data.get('symbol')}: {e}")
                continue

    def get_cached_symbols(self) -> list[str]:
        """Get list of all cached symbols."""
        return list(self._cache.keys())

    def clear_cache(self) -> None:
        """Clear the cache (forces next fetch)."""
        self._cache.clear()
        self._last_fetch = None
        logger.info("Exchange info cache cleared")


# Example usage
async def _example():
    """Example usage of ExchangeInfoFetcher."""

    async with ExchangeInfoFetcher() as fetcher:
        # Get symbol info
        info = await fetcher.get_symbol_info("BTCUSDT")
        if info:
            print(f"BTCUSDT tick size: {info.tick_size}")
            print(f"Rounded price 50123.456: {info.round_price(50123.456)}")

        # Get just tick size
        tick = await fetcher.get_tick_size("BTCUSDT")
        print(f"Quick tick lookup: {tick}")

        # List all symbols
        symbols = fetcher.get_cached_symbols()
        print(f"Cached {len(symbols)} symbols")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    asyncio.run(_example())
