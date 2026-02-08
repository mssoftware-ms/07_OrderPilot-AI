"""Historical Data Download Worker.

Background worker for downloading historical market data without blocking the UI.
"""

import logging
from datetime import datetime, timedelta, timezone

from src.ui.workers.base_worker import AsyncBaseWorker

logger = logging.getLogger(__name__)


class HistoricalDownloadWorker(AsyncBaseWorker):
    """Worker for downloading historical market data in background."""

    def __init__(
        self,
        provider_type: str,  # "alpaca" or "bitunix"
        symbols: list[str],
        days: int,
        timeframe: str,
        mode: str = "download",  # "download" or "sync"
        enable_bad_tick_filter: bool = True,  # Enable/disable bad tick filtering
        enable_ohlc_validation: bool = True,  # Enable/disable OHLC validation during download
    ):
        """Initialize download worker.

        Args:
            provider_type: "alpaca" or "bitunix"
            symbols: List of symbols to download
            days: Number of days of history (ignored in sync mode)
            timeframe: Timeframe string (1min, 5min, 15min, 1h, 4h, 1d)
            mode: "download" (replace existing) or "sync" (update missing)
            enable_bad_tick_filter: Enable/disable bad tick filtering
            enable_ohlc_validation: Enable/disable OHLC validation during download

        Note:
            For Bitunix: enable_ohlc_validation controls provider-level validation during parsing.
            When disabled, raw OHLC data is stored (may have rendering issues).
            Manual validation can be triggered later via Settings button.
        """
        super().__init__()
        self.provider_type = provider_type
        self.symbols = symbols
        self.days = days
        self.timeframe = timeframe
        self.mode = mode
        self.enable_bad_tick_filter = enable_bad_tick_filter
        self.enable_ohlc_validation = enable_ohlc_validation

    async def _execute_async(self):
        """Async download implementation."""
        from src.config.loader import config_manager
        from src.core.market_data.types import DataSource, Timeframe
        from src.database import initialize_database

        # CRITICAL DEBUG: Log the timeframe being used
        logger.info("=" * 80)
        logger.info("🚀 DOWNLOAD WORKER STARTED")
        logger.info("=" * 80)
        logger.info(f"📊 Provider:        {self.provider_type}")
        logger.info(f"📊 Symbols:         {', '.join(self.symbols)}")
        logger.info(f"📊 Timeframe STR:   '{self.timeframe}' (from Settings UI)")
        logger.info(f"📊 Days back:       {self.days}")
        logger.info(f"📊 Mode:            {self.mode}")
        logger.info(f"📊 Bad tick filter: {self.enable_bad_tick_filter}")
        logger.info(f"📊 OHLC validation: {self.enable_ohlc_validation}")
        logger.info("=" * 80)

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

        logger.info(f"📊 Timeframe ENUM:  {tf.value} (mapped from '{self.timeframe}')")
        if self.timeframe not in timeframe_map:
            logger.warning(f"⚠️ Unknown timeframe '{self.timeframe}', defaulting to 1min!")
        logger.info("=" * 80)

        status_msg = "📂 Initializing database..."
        logger.info(status_msg)
        self.progress.emit(5, status_msg)

        # Initialize database - use same SQLite DB as main app
        profile = config_manager.load_profile()
        profile.database.engine = "sqlite"
        profile.database.path = "./data/orderpilot.db"  # Same as main app!
        initialize_database(profile.database)

        status_msg = "✅ Database ready"
        logger.info(status_msg)
        self.progress.emit(8, status_msg)

        if self.is_cancelled():
            self.emit_cancellation_result("Download cancelled")
            return

        status_msg = f"🔧 Creating {self.provider_type} provider..."
        logger.info(status_msg)
        self.progress.emit(10, status_msg)

        results = {}
        total_bars = 0

        if self.provider_type == "alpaca":
            results = await self._download_alpaca(tf)
        elif self.provider_type == "bitunix":
            results = await self._download_bitunix(tf)

        if self.is_cancelled():
            self.emit_cancellation_result("Download cancelled")
            return

        # Calculate total bars
        for symbol, count in results.items():
            total_bars += count

        status_msg = "🎉 Finalizing..."
        logger.info(status_msg)
        self.progress.emit(95, status_msg)

        status_msg = "✅ Download complete!"
        logger.info(status_msg)
        self.progress.emit(100, status_msg)

        # Build completion message
        message = f"Downloaded {total_bars:,} bars for {len(self.symbols)} symbol(s)"

        self.finished.emit(True, message, results)

    async def _download_alpaca(self, timeframe) -> dict:
        """Download from Alpaca - COMPLETELY SEPARATE from Bitunix workflow."""
        from src.config.loader import config_manager
        from src.core.market_data.alpaca_crypto_provider import AlpacaCryptoProvider
        from src.core.market_data.alpaca_historical_data_manager import AlpacaHistoricalDataManager
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

        # Alpaca-specific manager (NO shared code with Bitunix)
        manager = AlpacaHistoricalDataManager()

        self.progress.emit(20, f"Downloading {', '.join(self.symbols)}...")

        # Custom progress tracking
        results = {}
        for i, symbol in enumerate(self.symbols):
            if self.is_cancelled():
                break

            progress_pct = 20 + int((i / len(self.symbols)) * 70)
            self.progress.emit(progress_pct, f"Deleting old data & downloading {symbol}...")

            # Create progress callback that emits detailed updates
            def make_progress_callback(sym: str, base_pct: int):
                def callback(batch_num: int, total_bars: int, status_msg: str):
                    # Emit detailed progress with batch info
                    self.progress.emit(base_pct, f"{sym}: {status_msg}")
                return callback

            try:
                symbol_results = await manager.bulk_download(
                    provider=provider,
                    symbols=[symbol],
                    days_back=self.days,
                    timeframe=timeframe,
                    source=DataSource.ALPACA_CRYPTO,
                    batch_size=100,
                    replace_existing=True,  # Delete old data first (removes bad ticks)
                    progress_callback=make_progress_callback(symbol, progress_pct),
                )
                results.update(symbol_results)
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                self.progress.emit(progress_pct, f"Error downloading {symbol}: {e}")

        return results

    async def _download_bitunix(self, timeframe) -> dict:
        """Download from Bitunix - COMPLETELY SEPARATE from Alpaca workflow."""
        from src.core.market_data.bitunix_historical_data_manager import BitunixHistoricalDataManager
        from src.core.market_data.providers.bitunix_provider import BitunixProvider
        from src.core.market_data.types import DataSource

        status_msg = "🌐 Using public Bitunix API (no keys required)..."
        logger.info(status_msg)
        self.progress.emit(15, status_msg)

        # Calculate requirements based on user request
        # Bitunix returns ~1440 bars per day for 1min timeframe
        # We need to ensure max_bars covers the entire requested period plus a buffer

        # Calculate expected bars per day for this timeframe
        bars_per_day_map = {
            "1min": 1440,
            "5min": 288,
            "15min": 96,
            "1h": 24,
            "4h": 6,
            "1d": 1,
        }
        bpd = bars_per_day_map.get(self.timeframe, 1440)

        # Calculate total bars needed + 10% buffer for safety
        total_bars_needed = int(self.days * bpd * 1.1)

        # Calculate max batches (200 bars per batch) + buffer
        # Bitunix limit is 200 bars per request
        max_batches_needed = int((total_bars_needed / 200) * 1.1) + 10

        logger.info(f"📊 Dynamic Download Config:")
        logger.info(f"   Requested Days: {self.days}")
        logger.info(f"   Timeframe: {self.timeframe} (approx {bpd} bars/day)")
        logger.info(f"   Calculated Max Bars: {total_bars_needed:,}")
        logger.info(f"   Calculated Max Batches: {max_batches_needed:,}")

        # Bitunix public API - no keys needed for kline data
        provider = BitunixProvider(
            api_key=None,
            api_secret=None,
            use_testnet=False,
            max_bars=total_bars_needed,  # Dynamic limit
            max_batches=max_batches_needed, # Dynamic limit
            validate_ohlc=self.enable_ohlc_validation,  # User-controlled OHLC validation
        )

        # Bitunix-specific manager (NO shared code with Alpaca)
        # Create FilterConfig based on checkbox setting
        from src.core.market_data.bitunix_historical_data_config import FilterConfig
        filter_config = FilterConfig(enabled=self.enable_bad_tick_filter)
        manager = BitunixHistoricalDataManager(filter_config=filter_config)

        status_msg = f"📊 Preparing download for {', '.join(self.symbols)}..."
        logger.info(status_msg)
        self.progress.emit(20, status_msg)

        # Use previously calculated values for progress estimation
        total_bars_estimated = total_bars_needed
        estimated_batches = max_batches_needed

        logger.info(f"📊 Download estimates: {total_bars_estimated:,} bars, ~{estimated_batches:,} batches")

        results = {}
        for i, symbol in enumerate(self.symbols):
            if self.is_cancelled():
                break

            # Calculate progress range for this symbol (20-90% for downloads)
            symbol_progress_start = 20 + int((i / len(self.symbols)) * 70)
            symbol_progress_range = int(70 / len(self.symbols))

            status_msg = f"🚀 Starting download for {symbol}..."
            logger.info(status_msg)
            self.progress.emit(symbol_progress_start, status_msg)

            # Create progress callback that calculates real progress based on batch_num
            def make_progress_callback(sym: str, start_pct: int, pct_range: int, est_batches: int):
                def callback(batch_num: int, total_bars: int, status_msg: str):
                    if self.is_cancelled():
                        return
                    # Calculate progress within this symbol's range
                    batch_progress = min(99, int((batch_num / est_batches) * pct_range))
                    current_pct = start_pct + batch_progress
                    full_msg = f"{sym}: {status_msg}"
                    # Log every 100th batch to avoid spam
                    if batch_num % 100 == 0 or batch_num == 1:
                        logger.info(f"[{current_pct:3d}%] {full_msg}")
                    self.progress.emit(current_pct, full_msg)
                return callback

            try:
                if self.mode == "sync":
                    # Smart Sync: Check coverage and download only missing data
                    self.progress.emit(symbol_progress_start, f"Syncing {symbol} (filling gaps)...")

                    symbol_results = await manager.sync_history_to_now(
                        provider=provider,
                        symbols=[symbol],
                        timeframe=timeframe,
                        source=DataSource.BITUNIX,
                        batch_size=100,
                        filter_config=None, # Use default
                        progress_callback=make_progress_callback(symbol, symbol_progress_start, symbol_progress_range, estimated_batches)
                    )
                else:
                    # Full Download: Replace existing data
                    logger.info(f"📥 Starting full download for {symbol}")
                    logger.info(f"   Timeframe: {self.timeframe} → {timeframe.value}")
                    logger.info(f"   Days back: {self.days}")
                    logger.info(f"   Estimated batches: ~{estimated_batches:,}")

                    symbol_results = await manager.bulk_download(
                        provider=provider,
                        symbols=[symbol],
                        days_back=self.days,
                        timeframe=timeframe,
                        source=DataSource.BITUNIX,
                        batch_size=100,
                        replace_existing=True,  # Delete old data first (removes bad ticks)
                        progress_callback=make_progress_callback(symbol, symbol_progress_start, symbol_progress_range, estimated_batches),
                    )
                results.update(symbol_results)
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                self.progress.emit(symbol_progress_start, f"Error downloading {symbol}: {e}")

        return results

    async def _auto_validate_ohlc(self) -> dict:
        """Auto-validate and fix OHLC data after download.

        Returns:
            Validation results dictionary
        """
        try:
            from src.database.ohlc_validator import validate_and_fix_ohlc

            # Validate only the symbols we just downloaded
            # For now, validate all symbols (could be optimized to validate only downloaded symbols)
            results = validate_and_fix_ohlc(
                symbol=None,  # Validate all
                dry_run=False,  # Apply fixes
                progress_callback=None  # No UI updates during auto-validation
            )

            return results
        except Exception as e:
            logger.error(f"Auto-validation error: {e}", exc_info=True)
            return {}


# Use WorkerThread from base_worker module instead of custom thread wrapper
from src.ui.workers.base_worker import WorkerThread

# Alias for backward compatibility
DownloadThread = WorkerThread
