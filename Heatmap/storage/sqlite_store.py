"""
SQLite Storage for Liquidation Events

Provides optimized write performance with batched inserts and WAL mode.
Implements retention policies and query helpers for heatmap generation.
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
from collections import deque

from ..ingestion.binance_forceorder_ws import LiquidationEvent


logger = logging.getLogger(__name__)


@dataclass
class QueryWindow:
    """Time window for querying events."""

    start_ms: int  # Start timestamp in milliseconds
    end_ms: int    # End timestamp in milliseconds
    symbol: Optional[str] = None  # Optional symbol filter

    @classmethod
    def from_duration(
        cls,
        duration: timedelta,
        symbol: Optional[str] = None
    ) -> "QueryWindow":
        """Create window from duration (ending now)."""
        end_ms = int(datetime.now().timestamp() * 1000)
        start_ms = int((datetime.now() - duration).timestamp() * 1000)
        return cls(start_ms=start_ms, end_ms=end_ms, symbol=symbol)

    @classmethod
    def from_hours(cls, hours: float, symbol: Optional[str] = None) -> "QueryWindow":
        """Create window from hours (ending now)."""
        return cls.from_duration(timedelta(hours=hours), symbol)


class LiquidationStore:
    """
    SQLite storage for liquidation events with optimized writes.

    Features:
    - WAL mode for concurrent read/write
    - Batched inserts with configurable flush interval
    - Automatic retention cleanup
    - Query helpers for heatmap generation
    """

    SCHEMA_FILE = Path(__file__).parent / "schema.sql"
    DEFAULT_BATCH_SIZE = 100
    DEFAULT_FLUSH_INTERVAL = 1.0  # seconds
    DEFAULT_RETENTION_DAYS = 14

    def __init__(
        self,
        db_path: str | Path,
        batch_size: int = DEFAULT_BATCH_SIZE,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ):
        """
        Initialize liquidation store.

        Args:
            db_path: Path to SQLite database file
            batch_size: Number of events to batch before insert
            flush_interval: Maximum seconds between flushes
            retention_days: Days to retain events (0 = no cleanup)
        """
        self.db_path = Path(db_path)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.retention_days = retention_days

        self._conn: Optional[sqlite3.Connection] = None
        self._write_queue: deque[LiquidationEvent] = deque()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

    def connect(self) -> None:
        """Open database connection and initialize schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # We handle threading with asyncio
        )

        # Enable WAL mode and optimize pragmas
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        self._conn.execute("PRAGMA mmap_size=268435456")  # 256MB mmap

        # Load and execute schema
        if self.SCHEMA_FILE.exists():
            schema_sql = self.SCHEMA_FILE.read_text()
            self._conn.executescript(schema_sql)
        else:
            logger.warning(f"Schema file not found: {self.SCHEMA_FILE}")

        self._conn.commit()
        logger.info(f"Connected to database: {self.db_path}")

    def disconnect(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    async def start(self) -> None:
        """Start background flush task."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("Started store flush task")

    async def stop(self) -> None:
        """Stop background flush task and flush pending events."""
        if not self._running:
            return

        logger.info("Stopping store...")
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_batch()
        logger.info("Store stopped")

    async def add_event(self, event: LiquidationEvent) -> None:
        """Add event to write queue (non-blocking)."""
        async with self._lock:
            self._write_queue.append(event)

            # Flush if batch full
            if len(self._write_queue) >= self.batch_size:
                await self._flush_batch()

    async def _flush_loop(self) -> None:
        """Background task to flush queue periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}", exc_info=True)

    async def _flush_batch(self) -> None:
        """Flush queued events to database."""
        async with self._lock:
            if not self._write_queue:
                return

            events = list(self._write_queue)
            self._write_queue.clear()

        try:
            # Execute in thread pool to avoid blocking asyncio
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._insert_batch,
                events
            )
            logger.debug(f"Flushed {len(events)} events to database")
        except Exception as e:
            logger.error(f"Failed to flush batch: {e}", exc_info=True)
            # Re-queue events on failure
            async with self._lock:
                self._write_queue.extendleft(reversed(events))

    def _insert_batch(self, events: List[LiquidationEvent]) -> None:
        """Insert batch of events (blocking, run in executor)."""
        if not self._conn:
            raise RuntimeError("Database not connected")

        cursor = self._conn.cursor()
        cursor.executemany(
            """
            INSERT INTO liq_events (ts_ms, symbol, side, price, qty, notional, source, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    e.ts_ms,
                    e.symbol,
                    e.side,
                    e.price,
                    e.qty,
                    e.notional,
                    e.source,
                    e.raw_json,
                )
                for e in events
            ],
        )
        self._conn.commit()

    def query_events(
        self,
        window: QueryWindow,
        limit: Optional[int] = None
    ) -> List[Tuple]:
        """
        Query events within time window.

        Returns:
            List of tuples: (ts_ms, symbol, side, price, qty, notional)
        """
        if not self._conn:
            raise RuntimeError("Database not connected")

        query = """
            SELECT ts_ms, symbol, side, price, qty, notional
            FROM liq_events
            WHERE ts_ms >= ? AND ts_ms <= ?
        """
        params = [window.start_ms, window.end_ms]

        if window.symbol:
            query += " AND symbol = ?"
            params.append(window.symbol)

        query += " ORDER BY ts_ms ASC"

        if limit:
            query += f" LIMIT {limit}"

        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_price_range(self, window: QueryWindow) -> Tuple[float, float]:
        """
        Get price range (min, max) for events in window.

        Returns:
            (min_price, max_price) or (0.0, 0.0) if no events
        """
        if not self._conn:
            raise RuntimeError("Database not connected")

        query = """
            SELECT MIN(price), MAX(price)
            FROM liq_events
            WHERE ts_ms >= ? AND ts_ms <= ?
        """
        params = [window.start_ms, window.end_ms]

        if window.symbol:
            query += " AND symbol = ?"
            params.append(window.symbol)

        cursor = self._conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()

        if result and result[0] is not None:
            return (result[0], result[1])
        return (0.0, 0.0)

    def cleanup_old_events(self) -> int:
        """
        Delete events older than retention period.

        Returns:
            Number of rows deleted
        """
        if not self._conn or self.retention_days <= 0:
            return 0

        cutoff_ms = int((datetime.now() - timedelta(days=self.retention_days)).timestamp() * 1000)

        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM liq_events WHERE ts_ms < ?", (cutoff_ms,))
        self._conn.commit()

        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"Deleted {deleted} events older than {self.retention_days} days")

            # Run VACUUM to reclaim space (blocking operation)
            cursor.execute("VACUUM")

        return deleted

    def get_stats(self) -> dict:
        """Get database statistics."""
        if not self._conn:
            return {}

        cursor = self._conn.cursor()

        # Total events
        cursor.execute("SELECT COUNT(*) FROM liq_events")
        total_count = cursor.fetchone()[0]

        # Oldest and newest timestamps
        cursor.execute("SELECT MIN(ts_ms), MAX(ts_ms) FROM liq_events")
        min_ts, max_ts = cursor.fetchone()

        # Database file size
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            "total_events": total_count,
            "oldest_event": datetime.fromtimestamp(min_ts / 1000) if min_ts else None,
            "newest_event": datetime.fromtimestamp(max_ts / 1000) if max_ts else None,
            "db_size_mb": db_size / (1024 * 1024),
            "pending_writes": len(self._write_queue),
        }


# Example usage
async def _example():
    """Example usage of LiquidationStore."""
    store = LiquidationStore(db_path="test_liq.db")
    store.connect()
    await store.start()

    try:
        # Simulate events
        for i in range(10):
            event = LiquidationEvent(
                ts_ms=int(datetime.now().timestamp() * 1000),
                symbol="BTCUSDT",
                side="SELL" if i % 2 else "BUY",
                price=50000 + i * 10,
                qty=0.1,
                notional=5000,
                source="BINANCE_USDM",
                raw_json="{}",
            )
            await store.add_event(event)
            await asyncio.sleep(0.1)

        # Wait for flush
        await asyncio.sleep(2)

        # Query
        window = QueryWindow.from_hours(1, symbol="BTCUSDT")
        events = store.query_events(window)
        print(f"Found {len(events)} events")

        # Stats
        stats = store.get_stats()
        print(f"Stats: {stats}")

    finally:
        await store.stop()
        store.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_example())
