"""Database Build Worker for Pattern Database Dialog.

QThread worker for building the pattern database in the background.
"""

from __future__ import annotations

import asyncio
import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

class DatabaseBuildWorker(QThread):
    """Worker thread for building the pattern database."""

    progress = pyqtSignal(str)  # Log message
    progress_value = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(
        self,
        symbols: list[str],
        timeframes: list[str],
        days_back: int,
        is_crypto: bool,
        window_size: int = 20,
        step_size: int = 5,
    ):
        super().__init__()
        self.symbols = symbols
        self.timeframes = timeframes
        self.days_back = days_back
        self.is_crypto = is_crypto
        self.window_size = window_size
        self.step_size = step_size
        self._cancelled = False

    def cancel(self):
        """Cancel the build process."""
        self._cancelled = True

    def run(self):
        """Run the database build in a separate thread."""
        try:
            # Run async build in this thread
            asyncio.run(self._build_async())
        except Exception as e:
            self.finished.emit(False, str(e))

    async def _build_async(self):
        """Async build process."""
        from src.core.market_data.types import Timeframe, AssetClass
        from src.core.pattern_db.fetcher import PatternDataFetcher, resolve_symbol
        from src.core.pattern_db.extractor import PatternExtractor
        from src.core.pattern_db.qdrant_client import TradingPatternDB

        try:
            self.progress.emit("Initializing components...")

            fetcher = PatternDataFetcher()
            extractor = PatternExtractor(
                window_size=self.window_size,
                step_size=self.step_size,
            )
            db = TradingPatternDB()

            # Initialize Qdrant
            self.progress.emit("Connecting to Qdrant...")
            if not await db.initialize():
                details = db.get_last_error() if hasattr(db, "get_last_error") else None
                msg = "Failed to connect to Qdrant."
                if details:
                    msg = f"{msg} {details}"
                    if "qdrant_client" in details.lower():
                        msg += " (Install: pip install qdrant-client)"
                self.finished.emit(False, msg)
                return

            # Map timeframe strings to enum
            tf_map = {
                "1Min": Timeframe.MINUTE_1,
                "5Min": Timeframe.MINUTE_5,
                "15Min": Timeframe.MINUTE_15,
                "30Min": Timeframe.MINUTE_30,
                "1Hour": Timeframe.HOUR_1,
                "4Hour": Timeframe.HOUR_4,
                "1Day": Timeframe.DAY_1,
            }

            timeframe_enums = [tf_map.get(tf, Timeframe.MINUTE_1) for tf in self.timeframes]
            asset_class = AssetClass.CRYPTO if self.is_crypto else AssetClass.STOCK

            total_tasks = len(self.symbols) * len(timeframe_enums)
            completed = 0
            total_patterns = 0

            for symbol in self.symbols:
                if self._cancelled:
                    self.finished.emit(False, "Build cancelled by user")
                    return

                for tf_enum in timeframe_enums:
                    if self._cancelled:
                        self.finished.emit(False, "Build cancelled by user")
                        return

                    fetch_symbol = resolve_symbol(symbol, asset_class)
                    if fetch_symbol != symbol:
                        self.progress.emit(f"Using proxy for {symbol}: {fetch_symbol}")

                    self.progress.emit(f"Fetching {fetch_symbol} ({tf_enum.value})...")

                    # Fetch bars
                    bars = await fetcher.fetch_symbol_data(
                        symbol=fetch_symbol,
                        timeframe=tf_enum,
                        days_back=self.days_back,
                        asset_class=asset_class,
                    )

                    if bars:
                        self.progress.emit(f"  Got {len(bars)} bars, extracting patterns...")

                        # Extract patterns
                        patterns = list(extractor.extract_patterns(
                            bars=bars,
                            symbol=symbol,
                            timeframe=tf_enum.value,
                        ))
                        if fetch_symbol != symbol:
                            for p in patterns:
                                p.metadata["proxy_symbol"] = fetch_symbol

                        if patterns:
                            self.progress.emit(f"  Inserting {len(patterns)} patterns...")
                            inserted = await db.insert_patterns_batch(patterns, batch_size=500)
                            total_patterns += inserted
                    else:
                        self.progress.emit(f"  No data for {symbol}")

                    completed += 1
                    self.progress_value.emit(completed, total_tasks)

                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.3)

            # Get final stats
            info = await db.get_collection_info()
            msg = f"Build complete! Added {total_patterns:,} patterns. Total: {info.get('points_count', 0):,}"
            self.progress.emit(msg)
            self.finished.emit(True, msg)

        except Exception as e:
            logger.error(f"Build error: {e}", exc_info=True)
            self.finished.emit(False, str(e))
