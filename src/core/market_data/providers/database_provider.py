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

from .base import HistoricalDataProvider

logger = logging.getLogger(__name__)


class DatabaseProvider(HistoricalDataProvider):
    """Database historical data provider (local cache)."""

    def __init__(self):
        """Initialize database provider."""
        super().__init__("Database")
        self.db_manager = get_db_manager()
        logger.info("DatabaseProvider initialized")

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
        """Synchronous database fetch (runs in thread).

        Checks both market_bars (SQLAlchemy) and historical_bars (raw SQL) tables.
        """
        bars = []

        # 1. Try SQLAlchemy market_bars table first
        with self.db_manager.session() as session:
            bars_db = session.query(MarketBar).filter(
                MarketBar.symbol == symbol,
                MarketBar.timestamp >= start_date,
                MarketBar.timestamp <= end_date
            ).order_by(MarketBar.timestamp).all()

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

        # 2. If no bars from market_bars, try historical_bars table (bulk download storage)
        if not bars:
            bars = self._fetch_from_historical_bars(symbol, start_date, end_date)

        # Resample if needed
        if bars and timeframe != Timeframe.SECOND_1:
            bars = self._resample_bars(bars, timeframe)

        logger.info(f"Fetched {len(bars)} bars from database for {symbol}")
        return bars

    def _fetch_from_historical_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> list[HistoricalBar]:
        """Fetch from historical_bars table (raw SQL - backup compatibility)."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, open, high, low, close, volume, source
                    FROM historical_bars
                    WHERE symbol = ?
                    AND timestamp >= ?
                    AND timestamp <= ?
                    ORDER BY timestamp
                """, (symbol, start_date.isoformat(), end_date.isoformat()))

                rows = cursor.fetchall()
                bars = []
                for row in rows:
                    ts = row[0]
                    # Parse timestamp (can be string or datetime)
                    if isinstance(ts, str):
                        ts = pd.to_datetime(ts)

                    bar = HistoricalBar(
                        timestamp=ts,
                        open=Decimal(str(row[1])),
                        high=Decimal(str(row[2])),
                        low=Decimal(str(row[3])),
                        close=Decimal(str(row[4])),
                        volume=int(row[5]) if row[5] else 0,
                        source=row[6] if len(row) > 6 else "historical_bars"
                    )
                    bars.append(bar)

                logger.info(f"Fetched {len(bars)} bars from historical_bars for {symbol}")
                return bars

        except Exception as e:
            logger.debug(f"historical_bars table not available or error: {e}")
            return []

    async def is_available(self) -> bool:
        """Check if database is available."""
        return True  # Always available

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
