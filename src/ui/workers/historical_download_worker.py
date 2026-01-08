"""Historical Data Download Worker.

Background worker for downloading historical market data without blocking the UI.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class HistoricalDownloadWorker(QObject):
    """Worker for downloading historical market data in background."""

    # Signals
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    finished = pyqtSignal(bool, str, dict)  # (success, message, results)
    error = pyqtSignal(str)  # error_message

    def __init__(
        self,
        provider_type: str,  # "alpaca" or "bitunix"
        symbols: list[str],
        days: int,
        timeframe: str,
    ):
        """Initialize download worker.

        Args:
            provider_type: "alpaca" or "bitunix"
            symbols: List of symbols to download
            days: Number of days of history
            timeframe: Timeframe string (1min, 5min, 15min, 1h, 4h, 1d)
        """
        super().__init__()
        self.provider_type = provider_type
        self.symbols = symbols
        self.days = days
        self.timeframe = timeframe
        self._cancelled = False

    def cancel(self):
        """Cancel the download."""
        self._cancelled = True

    def run(self):
        """Execute the download in background thread."""
        try:
            # Run async download in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._download())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Download worker error: {e}", exc_info=True)
            self.error.emit(str(e))

    async def _download(self):
        """Async download implementation."""
        from src.config.loader import config_manager
        from src.core.market_data.historical_data_manager import HistoricalDataManager
        from src.core.market_data.types import DataSource, Timeframe
        from src.database import initialize_database

        # Map timeframe string to enum
        timeframe_map = {
            "1min": Timeframe.MINUTE_1,
            "5min": Timeframe.MINUTE_5,
            "15min": Timeframe.MINUTE_15,
            "1h": Timeframe.HOUR_1,
            "4h": Timeframe.HOUR_4,
            "1d": Timeframe.DAY_1,
        }
        tf = timeframe_map.get(self.timeframe, Timeframe.MINUTE_1)

        self.progress.emit(5, "Initializing database...")

        # Initialize database
        try:
            profile = config_manager.load_profile()
            initialize_database(profile.database)
        except Exception as e:
            logger.warning(f"Database init issue: {e}, trying SQLite fallback")
            # Fallback to SQLite
            profile = config_manager.load_profile()
            profile.database.engine = "sqlite"
            profile.database.path = "./data/orderpilot_historical.db"
            initialize_database(profile.database)

        if self._cancelled:
            self.finished.emit(False, "Download cancelled", {})
            return

        self.progress.emit(10, f"Creating {self.provider_type} provider...")

        results = {}
        total_bars = 0

        if self.provider_type == "alpaca":
            results = await self._download_alpaca(tf)
        elif self.provider_type == "bitunix":
            results = await self._download_bitunix(tf)

        if self._cancelled:
            self.finished.emit(False, "Download cancelled", {})
            return

        # Calculate total bars
        for symbol, count in results.items():
            total_bars += count

        self.progress.emit(100, "Download complete!")
        self.finished.emit(
            True,
            f"Downloaded {total_bars:,} bars for {len(self.symbols)} symbol(s)",
            results
        )

    async def _download_alpaca(self, timeframe) -> dict:
        """Download from Alpaca."""
        from src.config.loader import config_manager
        from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
        from src.core.market_data.historical_data_manager import HistoricalDataManager
        from src.core.market_data.types import DataSource

        # Get credentials (optional for crypto)
        api_key = config_manager.get_credential("alpaca_api_key")
        api_secret = config_manager.get_credential("alpaca_api_secret")

        if api_key and api_secret:
            self.progress.emit(15, "Using authenticated Alpaca client...")
            provider = AlpacaCryptoProvider(api_key, api_secret)
        else:
            self.progress.emit(15, "Using public Alpaca crypto API...")
            provider = AlpacaCryptoProvider()

        manager = HistoricalDataManager()

        self.progress.emit(20, f"Downloading {', '.join(self.symbols)}...")

        # Custom progress tracking
        results = {}
        for i, symbol in enumerate(self.symbols):
            if self._cancelled:
                break

            progress_pct = 20 + int((i / len(self.symbols)) * 70)
            self.progress.emit(progress_pct, f"Deleting old data & downloading {symbol}...")

            try:
                symbol_results = await manager.bulk_download(
                    provider=provider,
                    symbols=[symbol],
                    days_back=self.days,
                    timeframe=timeframe,
                    source=DataSource.ALPACA_CRYPTO,
                    batch_size=100,
                    replace_existing=True,  # Delete old data first (removes bad ticks)
                )
                results.update(symbol_results)
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                self.progress.emit(progress_pct, f"Error downloading {symbol}: {e}")

        return results

    async def _download_bitunix(self, timeframe) -> dict:
        """Download from Bitunix."""
        from src.core.market_data.historical_data_manager import HistoricalDataManager
        from src.core.market_data.providers.bitunix_provider import BitunixProvider
        from src.core.market_data.types import DataSource

        self.progress.emit(15, "Using public Bitunix API (no keys required)...")

        # Bitunix public API - no keys needed for kline data
        provider = BitunixProvider(
            api_key=None,
            api_secret=None,
            use_testnet=False,
            max_bars=525600,  # 1 year of 1min bars
            max_batches=3000,
        )

        manager = HistoricalDataManager()

        self.progress.emit(20, f"Downloading {', '.join(self.symbols)}...")

        results = {}
        for i, symbol in enumerate(self.symbols):
            if self._cancelled:
                break

            progress_pct = 20 + int((i / len(self.symbols)) * 70)
            self.progress.emit(progress_pct, f"Deleting old data & downloading {symbol}...")

            try:
                symbol_results = await manager.bulk_download(
                    provider=provider,
                    symbols=[symbol],
                    days_back=self.days,
                    timeframe=timeframe,
                    source=DataSource.BITUNIX,
                    batch_size=100,
                    replace_existing=True,  # Delete old data first (removes bad ticks)
                )
                results.update(symbol_results)
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                self.progress.emit(progress_pct, f"Error downloading {symbol}: {e}")

        return results


class DownloadThread(QThread):
    """Thread wrapper for download worker."""

    def __init__(self, worker: HistoricalDownloadWorker):
        super().__init__()
        self.worker = worker

    def run(self):
        """Run the worker."""
        self.worker.run()
