"""Database Historical Data Provider.

Provides historical market data from local database cache.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.core.market_data.types import HistoricalBar, Timeframe
from src.database import get_db_manager
from src.database.models import MarketBar
from src.analysis.data_cleaning import ZScoreVolatilityFilter

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


class DatabaseProvider(HistoricalDataProvider):
    """Database historical data provider (local cache)."""

    def __init__(self):
        """Initialize database provider."""
        super().__init__("Database")
        self.db_manager = get_db_manager()

        # Initialize Z-Score Volatility Filter
        # REPLACES extreme High/Low values inline (no gaps in data!)
        # Prevents EMAs from being destroyed by fat-finger errors
        self.bad_tick_filter = ZScoreVolatilityFilter(
            volatility_window=20,  # 20-bar volatility window
            z_threshold=4.0,  # Z-Score > 4 = statistically extreme
            median_window=3,  # Replace with 3-bar median
            min_volume=0.0001,  # Abort if volume <= 0.0001
        )
        logger.info("🛡️  DatabaseProvider initialized with Z-Score Volatility Filter (vol_window=20, z_threshold=4.0)")

    async def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Fetch historical bars from database."""
        try:
            # Run database query in thread to avoid blocking event loop
            bars = await asyncio.to_thread(
                self._fetch_bars_sync, symbol, start_date, end_date, timeframe
            )
            return bars

        except Exception as e:
            logger.error(f"Error fetching database bars: {e}")
            return []

    def _fetch_bars_sync(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Synchronous database fetch (runs in thread)."""
        with self.db_manager.session() as session:
            bars_db = session.query(MarketBar).filter(
                MarketBar.symbol == symbol,
                MarketBar.timestamp >= start_date,
                MarketBar.timestamp <= end_date
            ).order_by(MarketBar.timestamp).all()

            bars = []
            for bar_db in bars_db:
                bar = HistoricalBar(
                    timestamp=bar_db.timestamp,
                    open=bar_db.open,
                    high=bar_db.high,
                    low=bar_db.low,
                    close=bar_db.close,
                    volume=bar_db.volume,
                    vwap=bar_db.vwap,
                    source="database"
                )
                bars.append(bar)

            # Apply bad tick filtering BEFORE resampling
            if bars:
                bars = self._filter_bad_ticks(bars)

            # Resample if needed
            if bars and timeframe != Timeframe.SECOND_1:
                bars = self._resample_bars(bars, timeframe)

            logger.info(f"Fetched {len(bars)} bars from database for {symbol}")
            return bars

    async def is_available(self) -> bool:
        """Check if database is available."""
        return True  # Always available

    def _filter_bad_ticks(self, bars: list[HistoricalBar]) -> list[HistoricalBar]:
        """Filter out bad ticks from bar data.

        Args:
            bars: List of historical bars

        Returns:
            Filtered list with bad ticks removed
        """
        if not bars:
            return bars

        # Convert to DataFrame for cleaning
        df = pd.DataFrame([{
            'timestamp': b.timestamp,
            'open': float(b.open),
            'high': float(b.high),
            'low': float(b.low),
            'close': float(b.close),
            'volume': b.volume if b.volume else 0
        } for b in bars])

        # Clean data inline - REPLACES extreme values (NO gaps!)
        try:
            df_cleaned = self.bad_tick_filter.clean_data_inline(df)
        except ValueError as e:
            # Null volume detected - data leak
            logger.error(f"❌ Data cleaning failed: {e}")
            return []  # Return empty list on critical error

        # Convert cleaned DataFrame back to HistoricalBar objects
        cleaned_bars = []
        for _, row in df_cleaned.iterrows():
            cleaned_bars.append(HistoricalBar(
                timestamp=row['timestamp'],
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=row['volume']
            ))

        return cleaned_bars

    def _resample_bars(
        self,
        bars: list[HistoricalBar],
        timeframe: Timeframe
    ) -> list[HistoricalBar]:
        """Resample bars to different timeframe."""
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': b.timestamp,
            'open': float(b.open),
            'high': float(b.high),
            'low': float(b.low),
            'close': float(b.close),
            'volume': b.volume
        } for b in bars])

        df.set_index('timestamp', inplace=True)

        # Resample
        resampled = df.resample(timeframe.value).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        # Convert back to bars
        resampled_bars = []
        for timestamp, row in resampled.iterrows():
            bar = HistoricalBar(
                timestamp=timestamp,
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=int(row['volume']),
                source="database"
            )
            resampled_bars.append(bar)

        return resampled_bars
