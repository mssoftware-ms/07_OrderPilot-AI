"""Historical Data Fetcher for Pattern Database.

Fetches bulk historical data from Alpaca for building the pattern database.
Supports stocks (NASDAQ-100) and crypto (BTC, ETH).
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

from src.config.loader import config_manager
from src.core.market_data.types import DataRequest, DataSource, HistoricalBar, Timeframe, AssetClass

logger = logging.getLogger(__name__)


# NASDAQ-100 symbols (top components by weight)
NASDAQ_100_TOP = [
    "AAPL", "MSFT", "AMZN", "NVDA", "META", "GOOGL", "GOOG", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "ADBE", "PEP", "CSCO", "TMUS", "INTC", "CMCSA", "INTU", "QCOM",
    "TXN", "AMGN", "HON", "AMAT", "ISRG", "BKNG", "SBUX", "VRTX", "LRCX", "ADP",
    "MDLZ", "GILD", "ADI", "REGN", "PANW", "MU", "KLAC", "SNPS", "CDNS", "PYPL",
    "MELI", "CRWD", "MAR", "ASML", "ORLY", "CSX", "ABNB", "CTAS", "MNST", "WDAY",
]

# Crypto symbols for Alpaca
CRYPTO_SYMBOLS = ["BTC/USD", "ETH/USD"]

# Index proxies (Alpaca does not provide index bars; use ETF proxies)
INDEX_PROXY_MAP = {
    "NDX": "QQQ",   # Nasdaq-100 proxy
    "^NDX": "QQQ",
}


def resolve_symbol(symbol: str, asset_class: AssetClass) -> str:
    """Resolve symbol to a provider-supported proxy when needed."""
    if asset_class == AssetClass.STOCK:
        return INDEX_PROXY_MAP.get(symbol.upper(), symbol)
    return symbol

# Daytrading timeframes
DAYTRADING_TIMEFRAMES = [
    Timeframe.MINUTE_1,
    Timeframe.MINUTE_5,
    Timeframe.MINUTE_15,
]


@dataclass
class FetchConfig:
    """Configuration for data fetching."""
    symbols: list[str]
    timeframes: list[Timeframe]
    days_back: int = 365  # 1 year default
    asset_class: AssetClass = AssetClass.STOCK
    batch_size: int = 10  # Symbols per batch
    delay_between_batches: float = 1.0  # Seconds


class PatternDataFetcher:
    """Fetches historical data for pattern database construction."""

    def __init__(self):
        """Initialize the fetcher."""
        self._history_manager = None
        self._initialized = False

    async def _ensure_initialized(self) -> bool:
        """Ensure history manager is initialized."""
        if self._initialized:
            return True

        try:
            from src.core.market_data.history_provider import HistoryManager
            self._history_manager = HistoryManager()
            self._initialized = True
            logger.info("PatternDataFetcher initialized with HistoryManager")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize HistoryManager: {e}")
            return False

    def get_default_stock_config(self, days_back: int = 365) -> FetchConfig:
        """Get default config for NASDAQ-100 stocks.

        Args:
            days_back: Number of days of historical data

        Returns:
            FetchConfig for stocks
        """
        return FetchConfig(
            symbols=NASDAQ_100_TOP,
            timeframes=DAYTRADING_TIMEFRAMES,
            days_back=days_back,
            asset_class=AssetClass.STOCK,
        )

    def get_default_crypto_config(self, days_back: int = 365) -> FetchConfig:
        """Get default config for crypto (BTC, ETH).

        Args:
            days_back: Number of days of historical data

        Returns:
            FetchConfig for crypto
        """
        return FetchConfig(
            symbols=CRYPTO_SYMBOLS,
            timeframes=DAYTRADING_TIMEFRAMES,
            days_back=days_back,
            asset_class=AssetClass.CRYPTO,
        )

    async def fetch_symbol_data(
        self,
        symbol: str,
        timeframe: Timeframe,
        days_back: int,
        asset_class: AssetClass = AssetClass.STOCK,
    ) -> list[HistoricalBar]:
        """Fetch historical data for a single symbol.

        Args:
            symbol: Trading symbol (e.g., "AAPL" or "BTC/USD")
            timeframe: Bar timeframe
            days_back: Number of days of historical data
            asset_class: Asset class (STOCK or CRYPTO)

        Returns:
            List of historical bars
        """
        if not await self._ensure_initialized():
            return []

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        # Determine data source based on asset class
        if asset_class == AssetClass.CRYPTO:
            source = DataSource.ALPACA_CRYPTO
        else:
            source = DataSource.ALPACA

        request = DataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            source=source,
            asset_class=asset_class,
        )

        try:
            bars, source_used = await self._history_manager.fetch_data(request)
            logger.info(f"Fetched {len(bars)} bars for {symbol} ({timeframe.value}) from {source_used}")
            return bars
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return []

    async def fetch_batch(
        self,
        config: FetchConfig,
        progress_callback: callable = None,
    ) -> AsyncIterator[tuple[str, Timeframe, list[HistoricalBar]]]:
        """Fetch data for multiple symbols with progress tracking.

        Args:
            config: Fetch configuration
            progress_callback: Optional callback(symbol, timeframe, bars_count)

        Yields:
            Tuple of (symbol, timeframe, bars)
        """
        total_tasks = len(config.symbols) * len(config.timeframes)
        completed = 0

        for i in range(0, len(config.symbols), config.batch_size):
            batch_symbols = config.symbols[i:i + config.batch_size]

            for symbol in batch_symbols:
                for timeframe in config.timeframes:
                    bars = await self.fetch_symbol_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        days_back=config.days_back,
                        asset_class=config.asset_class,
                    )

                    completed += 1
                    if progress_callback:
                        progress_callback(symbol, timeframe, len(bars), completed, total_tasks)

                    yield symbol, timeframe, bars

                    # Small delay between requests to respect rate limits
                    await asyncio.sleep(0.3)

            # Larger delay between batches
            if i + config.batch_size < len(config.symbols):
                logger.info(f"Batch complete. Waiting {config.delay_between_batches}s before next batch...")
                await asyncio.sleep(config.delay_between_batches)

    async def fetch_all(
        self,
        config: FetchConfig,
        progress_callback: callable = None,
    ) -> dict[str, dict[str, list[HistoricalBar]]]:
        """Fetch all data according to config.

        Args:
            config: Fetch configuration
            progress_callback: Optional callback(symbol, timeframe, bars_count, completed, total)

        Returns:
            Dict mapping symbol -> timeframe -> bars
        """
        result = {}

        async for symbol, timeframe, bars in self.fetch_batch(config, progress_callback):
            if symbol not in result:
                result[symbol] = {}
            result[symbol][timeframe.value] = bars

        # Log summary
        total_bars = sum(
            len(bars)
            for symbol_data in result.values()
            for bars in symbol_data.values()
        )
        logger.info(f"Fetch complete: {len(result)} symbols, {total_bars:,} total bars")

        return result


# Convenience function for CLI usage
async def fetch_daytrading_data(
    include_stocks: bool = True,
    include_crypto: bool = True,
    days_back: int = 365,
    progress_callback: callable = None,
) -> dict[str, dict[str, list[HistoricalBar]]]:
    """Fetch all daytrading data for pattern database.

    Args:
        include_stocks: Include NASDAQ-100 stocks
        include_crypto: Include BTC/ETH
        days_back: Days of historical data
        progress_callback: Progress callback

    Returns:
        Combined data dict
    """
    fetcher = PatternDataFetcher()
    result = {}

    if include_stocks:
        stock_config = fetcher.get_default_stock_config(days_back)
        stock_data = await fetcher.fetch_all(stock_config, progress_callback)
        result.update(stock_data)

    if include_crypto:
        crypto_config = fetcher.get_default_crypto_config(days_back)
        crypto_data = await fetcher.fetch_all(crypto_config, progress_callback)
        result.update(crypto_data)

    return result
