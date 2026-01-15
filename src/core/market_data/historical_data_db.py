"""Historical Data Database Handler.

Handles all database operations for historical data:
- Saving bars in batches
- Deleting symbol data
- Coverage and integrity queries

Module 3/4 of historical_data_manager.py split (Lines 683-870).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from src.database.database import Database

logger = logging.getLogger(__name__)


class HistoricalDataDB:
    """Database handler for historical data operations.

    Manages persistence of historical bars with batching and cleanup.
    """

    def __init__(self, db: Database):
        """
        Initialize database handler.

        Args:
            db: Database instance
        """
        self.db = db
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Create historical_bars table if it doesn't exist."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS historical_bars (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL DEFAULT 0,
                        source TEXT,
                        UNIQUE(symbol, timestamp)
                    )
                """)
                # Create index for fast lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_historical_bars_symbol_timestamp
                    ON historical_bars(symbol, timestamp)
                """)
                conn.commit()
                logger.debug("historical_bars table ensured")
        except Exception as e:
            logger.error(f"Failed to create historical_bars table: {e}")

    async def delete_symbol_data(self, db_symbol: str) -> None:
        """
        Delete all data for a symbol (async).

        Args:
            db_symbol: Database symbol identifier
        """
        await self.db.run_in_executor(self._delete_symbol_data_sync, db_symbol)

    def _delete_symbol_data_sync(self, db_symbol: str) -> None:
        """
        Delete all data for a symbol (sync).

        Args:
            db_symbol: Database symbol identifier
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM historical_bars WHERE symbol = ?", (db_symbol,)
                )
                conn.commit()
                deleted = cursor.rowcount
                logger.info(f"🗑️  Deleted {deleted} existing bars for {db_symbol}")
        except Exception as e:
            logger.error(f"Error deleting data for {db_symbol}: {e}")
            raise

    async def save_bars_batched(
        self,
        bars: list,
        db_symbol: str,
        source: str,
        batch_size: int = 1000,
    ) -> None:
        """
        Save bars to database in batches (async).

        Args:
            bars: List of Bar objects
            db_symbol: Database symbol identifier
            source: Data source name
            batch_size: Number of bars per batch
        """
        if not bars:
            return

        batches = [bars[i : i + batch_size] for i in range(0, len(bars), batch_size)]

        for i, batch in enumerate(batches):
            await self.db.run_in_executor(
                self._save_batch_sync, batch, db_symbol, source
            )
            if i % 10 == 0 and i > 0:
                logger.debug(f"Saved batch {i + 1}/{len(batches)} for {db_symbol}")

    def _save_batch_sync(self, batch: list, db_symbol: str, source: str) -> None:
        """
        Save a batch of bars synchronously.

        Args:
            batch: List of Bar objects
            db_symbol: Database symbol identifier
            source: Data source name
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                for bar in batch:
                    ts = bar.timestamp
                    if isinstance(ts, datetime):
                        ts = ts.isoformat()

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO historical_bars
                        (symbol, timestamp, open, high, low, close, volume, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            db_symbol,
                            ts,
                            float(bar.open),
                            float(bar.high),
                            float(bar.low),
                            float(bar.close),
                            float(bar.volume),
                            source,
                        ),
                    )

                conn.commit()
        except Exception as e:
            logger.error(f"Error saving batch for {db_symbol}: {e}")
            raise

    async def get_data_coverage(self, db_symbol: str) -> dict | None:
        """
        Get data coverage info for a symbol (async).

        Args:
            db_symbol: Database symbol identifier

        Returns:
            Dict with coverage info or None
        """
        return await self.db.run_in_executor(self._get_coverage_sync, db_symbol)

    def _get_coverage_sync(self, db_symbol: str) -> dict | None:
        """
        Get data coverage info for a symbol (sync).

        Args:
            db_symbol: Database symbol identifier

        Returns:
            Dict with first_date, last_date, total_bars, date_range_days
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        MIN(timestamp) as first_date,
                        MAX(timestamp) as last_date,
                        COUNT(*) as total_bars
                    FROM historical_bars
                    WHERE symbol = ?
                    """,
                    (db_symbol,),
                )

                row = cursor.fetchone()
                if not row or row[0] is None:
                    return None

                first_date = pd.to_datetime(row[0])
                last_date = pd.to_datetime(row[1])
                total_bars = row[2]
                date_range_days = (last_date - first_date).days

                return {
                    "first_date": first_date,
                    "last_date": last_date,
                    "total_bars": total_bars,
                    "date_range_days": date_range_days,
                }
        except Exception as e:
            logger.error(f"Error getting coverage for {db_symbol}: {e}")
            return None

    async def verify_data_integrity(self, db_symbol: str) -> dict:
        """
        Verify data integrity for a symbol (async).

        Args:
            db_symbol: Database symbol identifier

        Returns:
            Dict with integrity check results
        """
        return await self.db.run_in_executor(self._verify_integrity_sync, db_symbol)

    def _verify_integrity_sync(self, db_symbol: str) -> dict:
        """
        Verify data integrity for a symbol (sync).

        Checks:
        - Duplicate timestamps
        - OHLC consistency
        - Missing data gaps

        Args:
            db_symbol: Database symbol identifier

        Returns:
            Dict with has_issues, duplicate_count, ohlc_issues, gap_count
        """
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql_query(
                    """
                    SELECT timestamp, open, high, low, close, volume
                    FROM historical_bars
                    WHERE symbol = ?
                    ORDER BY timestamp
                    """,
                    conn,
                    params=(db_symbol,),
                )

            if df.empty:
                return {"has_issues": False, "message": "No data"}

            # Check duplicates
            duplicate_count = df["timestamp"].duplicated().sum()

            # Check OHLC consistency
            ohlc_issues = 0
            if all(col in df.columns for col in ["open", "high", "low", "close"]):
                ohlc_issues += (df["high"] < df["low"]).sum()
                ohlc_issues += (df["close"] > df["high"]).sum()
                ohlc_issues += (df["close"] < df["low"]).sum()

            # Check for gaps (more than 2x expected interval)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            time_diffs = df["timestamp"].diff()
            median_diff = time_diffs.median()
            gap_count = (time_diffs > median_diff * 2).sum()

            has_issues = duplicate_count > 0 or ohlc_issues > 0 or gap_count > 5

            return {
                "has_issues": has_issues,
                "duplicate_count": int(duplicate_count),
                "ohlc_issues": int(ohlc_issues),
                "gap_count": int(gap_count),
                "total_bars": len(df),
            }

        except Exception as e:
            logger.error(f"Error verifying integrity for {db_symbol}: {e}")
            return {"has_issues": True, "error": str(e)}
