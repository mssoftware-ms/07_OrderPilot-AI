# Binance Liquidation Heatmap - Implementation Plan

**Version:** 1.0
**Date:** 2026-01-13
**Estimated Duration:** 6-8 weeks
**Team Size:** 2-3 developers

---

## Overview

This document provides a detailed, week-by-week implementation plan for the Binance Liquidation Heatmap feature. The plan is organized into 8 phases following the checklist in the project specification, with clear deliverables and dependencies.

---

## Phase 0: Preparation & Repository Structure (Week 1)

**Goal**: Set up project structure and establish development standards.

**Duration**: 3-5 days

### Tasks

#### 0.1 Create Directory Structure
```bash
mkdir -p Heatmap/{ingestion,storage,aggregation,ui/js,tests}
touch Heatmap/{__init__.py,README.md}
touch Heatmap/ingestion/__init__.py
touch Heatmap/storage/{__init__.py,schema.sql}
touch Heatmap/aggregation/__init__.py
touch Heatmap/ui/__init__.py
touch Heatmap/tests/{test_ws_parse.py,test_sqlite_store.py,test_grid_builder.py}
```

**Deliverables**:
- ✅ Complete directory tree under `Heatmap/`
- ✅ Empty `__init__.py` files in all packages
- ✅ README skeleton with project overview

**Time**: 1 hour

#### 0.2 Verify Dependencies
```bash
# Check existing requirements.txt includes:
# - websockets==15.0.1
# - aiohttp==3.13.2
# - PyQt6==6.10.0
# - PyQt6-WebEngine>=6.7.0
# - qasync==0.28.0
# - numpy==2.2.6
# - SQLAlchemy==2.0.44

python -c "import websockets; import aiohttp; import PyQt6; import qasync; import numpy; import sqlalchemy; print('All dependencies available')"
```

**Deliverables**:
- ✅ Confirmation all libraries installed
- ✅ No new dependencies needed

**Time**: 30 minutes

#### 0.3 Document Coding Standards

Create `Heatmap/README.md` with:
- File size limit: ≤600 LOC (mandatory split if exceeded)
- Logging: Use Python `logging` module with DEBUG/INFO/WARN/ERROR levels
- Type hints: All functions must have type annotations
- Docstrings: Google-style docstrings for all public functions
- Testing: Minimum 80% coverage for critical paths
- Async style: Use `async`/`await` for I/O operations
- Error handling: Never swallow exceptions silently

**Deliverables**:
- ✅ README.md with coding standards
- ✅ Example code snippets for team reference

**Time**: 2 hours

#### 0.4 Set Up Logging Configuration

Create `Heatmap/logging_config.py`:
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_file: str = "logs/heatmap.log", level: int = logging.INFO):
    """Configure logging for heatmap module."""
    logger = logging.getLogger("Heatmap")
    logger.setLevel(level)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    console.setFormatter(console_fmt)

    # File handler (rotating)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger
```

**Deliverables**:
- ✅ Centralized logging configuration
- ✅ Rotating log files (10 MB max)

**Time**: 1 hour

### Phase 0 Completion Criteria
- [ ] Directory structure matches specification
- [ ] All dependencies verified
- [ ] Coding standards documented
- [ ] Logging configured

**Total Time**: 1 day

---

## Phase 1: Binance Ingestion Layer (Week 1-2)

**Goal**: Establish reliable WebSocket connection to Binance with auto-reconnect.

**Duration**: 5-7 days

### Tasks

#### 1.1 WebSocket Client - Basic Connection

**File**: `Heatmap/ingestion/binance_forceorder_ws.py` (≤600 LOC)

**Implementation Steps**:
1. Create `LiquidationEvent` dataclass
2. Implement `BinanceForceOrderClient` class
3. Add `connect()` method with basic error handling
4. Add `_message_loop()` for receiving messages
5. Add `shutdown()` for graceful cleanup

**Code Skeleton**:
```python
from dataclasses import dataclass
import asyncio
import json
import logging
import websockets
from typing import Callable, Optional

logger = logging.getLogger("Heatmap.ingestion")

@dataclass
class LiquidationEvent:
    """Parsed liquidation event from Binance forceOrder stream."""
    ts_ms: int
    symbol: str
    side: str
    price: float
    qty: float
    notional: float
    source: str = "BINANCE_USDM"
    raw_json: str = ""

class BinanceForceOrderClient:
    """WebSocket client for Binance BTCUSDT forceOrder stream."""

    BASE_URL = "wss://fstream.binance.com/ws"

    def __init__(self, symbol: str = "btcusdt",
                 on_event: Optional[Callable[[LiquidationEvent], None]] = None):
        self._symbol = symbol.lower()
        self._stream = f"{self._symbol}@forceOrder"
        self._ws_url = f"{self.BASE_URL}/{self._stream}"
        self._on_event = on_event
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False

    async def connect(self) -> None:
        """Connect to Binance WebSocket."""
        self._running = True
        while self._running:
            try:
                async with websockets.connect(self._ws_url) as ws:
                    self._ws = ws
                    logger.info(f"Connected to {self._ws_url}")
                    await self._message_loop()
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)  # Basic retry delay

    async def _message_loop(self) -> None:
        """Main message processing loop."""
        while self._running:
            try:
                raw_msg = await self._ws.recv()
                event = self._parse_event(raw_msg)
                if event and self._on_event:
                    self._on_event(event)
            except websockets.ConnectionClosed:
                logger.warning("Connection closed")
                break
            except Exception as e:
                logger.error(f"Message processing error: {e}")

    def _parse_event(self, raw_msg: str) -> Optional[LiquidationEvent]:
        """Parse forceOrder event JSON."""
        try:
            data = json.loads(raw_msg)
            # ... parse logic (implement based on Binance docs)
            return LiquidationEvent(...)
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        self._running = False
        if self._ws:
            await self._ws.close()
```

**Deliverables**:
- ✅ WebSocket connects to Binance
- ✅ Receives and parses forceOrder messages
- ✅ Callbacks fire with `LiquidationEvent` objects

**Time**: 2 days

**Testing**:
```python
# Heatmap/tests/test_ws_parse.py
import pytest
from Heatmap.ingestion.binance_forceorder_ws import BinanceForceOrderClient, LiquidationEvent

@pytest.mark.asyncio
async def test_connection():
    """Test basic WebSocket connection."""
    events = []
    client = BinanceForceOrderClient(on_event=lambda e: events.append(e))

    # Run for 10 seconds
    task = asyncio.create_task(client.connect())
    await asyncio.sleep(10)
    await client.shutdown()
    task.cancel()

    assert len(events) > 0, "Should receive at least one event"
    assert isinstance(events[0], LiquidationEvent)
```

#### 1.2 Parse forceOrder Payload

**Implementation**:
Implement `_parse_event()` method based on Binance API docs:

```json
{
  "e": "forceOrder",
  "E": 1736789412345,
  "o": {
    "s": "BTCUSDT",
    "S": "SELL",
    "o": "LIMIT",
    "f": "IOC",
    "q": "0.5",
    "p": "95000.0",
    "ap": "95000.0",
    "X": "FILLED",
    "l": "0.5",
    "z": "0.5",
    "T": 1736789412340
  }
}
```

**Parsing Logic**:
```python
def _parse_event(self, raw_msg: str) -> Optional[LiquidationEvent]:
    """Parse forceOrder event JSON."""
    try:
        data = json.loads(raw_msg)
        if data.get('e') != 'forceOrder':
            return None

        order = data.get('o', {})
        symbol = order.get('s')
        side = order.get('S')  # BUY or SELL
        price = float(order.get('ap', 0))  # Average price
        qty = float(order.get('z', 0))     # Filled quantity
        ts_ms = order.get('T', data.get('E'))  # Trade time or event time

        if not all([symbol, side, price, qty, ts_ms]):
            logger.warning(f"Missing fields in event: {data}")
            return None

        return LiquidationEvent(
            ts_ms=ts_ms,
            symbol=symbol,
            side=side,
            price=price,
            qty=qty,
            notional=price * qty,
            source="BINANCE_USDM",
            raw_json=raw_msg
        )
    except Exception as e:
        logger.error(f"Parse error: {e}, msg: {raw_msg}")
        return None
```

**Deliverables**:
- ✅ Correct parsing of all required fields
- ✅ Validation: reject events with missing data
- ✅ Store raw JSON for debugging

**Time**: 1 day

#### 1.3 Reconnect Policy + Backoff

**Implementation**:
Replace basic retry with exponential backoff:

```python
import random

class BinanceForceOrderClient:
    MAX_BACKOFF = 60  # Max 60 seconds

    def __init__(self, ...):
        # ... existing init
        self._backoff = 1  # Start at 1 second

    async def connect(self) -> None:
        """Connect with exponential backoff."""
        self._running = True
        while self._running:
            try:
                async with websockets.connect(self._ws_url) as ws:
                    self._ws = ws
                    self._backoff = 1  # Reset on successful connect
                    logger.info(f"Connected to {self._ws_url}")
                    await self._message_loop()
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await self._reconnect_with_backoff()

    async def _reconnect_with_backoff(self) -> None:
        """Exponential backoff with jitter."""
        jitter = random.uniform(0, 0.3 * self._backoff)
        delay = min(self._backoff + jitter, self.MAX_BACKOFF)
        logger.info(f"Reconnecting in {delay:.1f}s...")
        await asyncio.sleep(delay)
        self._backoff = min(self._backoff * 2, self.MAX_BACKOFF)
```

**Deliverables**:
- ✅ Exponential backoff: 1s → 2s → 4s → 8s → 16s → 32s → 60s (max)
- ✅ Jitter prevents thundering herd
- ✅ Reset backoff on successful connection

**Time**: 0.5 days

#### 1.4 Keepalive/Ping/Pong + 24h Reconnect

**Implementation**:
Add ping/pong handling and 24h timer:

```python
class BinanceForceOrderClient:
    PING_INTERVAL = 180  # 3 minutes
    PONG_TIMEOUT = 30    # 30 seconds
    RECONNECT_INTERVAL = 23 * 3600 + 50 * 60  # 23h 50m

    async def _message_loop(self) -> None:
        """Message loop with keepalive."""
        ping_task = asyncio.create_task(self._keepalive())
        reconnect_task = asyncio.create_task(self._scheduled_reconnect())

        try:
            while self._running:
                try:
                    raw_msg = await asyncio.wait_for(
                        self._ws.recv(),
                        timeout=self.PONG_TIMEOUT
                    )
                    event = self._parse_event(raw_msg)
                    if event and self._on_event:
                        self._on_event(event)
                except asyncio.TimeoutError:
                    logger.error("Pong timeout - connection dead")
                    break
        finally:
            ping_task.cancel()
            reconnect_task.cancel()

    async def _keepalive(self) -> None:
        """Send periodic pings."""
        while self._running:
            await asyncio.sleep(self.PING_INTERVAL)
            try:
                await self._ws.ping()
            except Exception as e:
                logger.error(f"Ping failed: {e}")
                break

    async def _scheduled_reconnect(self) -> None:
        """Reconnect before 24h timeout."""
        await asyncio.sleep(self.RECONNECT_INTERVAL)
        logger.info("Scheduled 24h reconnect")
        self._running = False  # Trigger reconnect
```

**Deliverables**:
- ✅ Ping every 3 minutes
- ✅ Detect dead connections (no pong)
- ✅ Preemptive reconnect at 23h 50m

**Time**: 1 day

#### 1.5 TickSize Cache

**File**: `Heatmap/ingestion/exchange_info.py` (≤600 LOC)

**Implementation**:
```python
import aiohttp
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class SymbolInfo:
    symbol: str
    tick_size: float
    min_price: float
    max_price: float
    last_updated: int

class ExchangeInfoCache:
    """Cache for Binance exchange info (tickSize)."""

    API_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    TTL = 6 * 3600  # 6 hours

    def __init__(self):
        self._cache: dict[str, SymbolInfo] = {}

    async def get_tick_size(self, symbol: str) -> float:
        """Get tickSize for symbol, refresh if stale."""
        if symbol in self._cache and not self._is_stale(symbol):
            return self._cache[symbol].tick_size

        await self.refresh()
        return self._cache.get(symbol, SymbolInfo(
            symbol=symbol,
            tick_size=0.1,  # Default fallback for BTCUSDT
            min_price=0.0,
            max_price=1e9,
            last_updated=int(time.time())
        )).tick_size

    async def refresh(self) -> None:
        """Fetch fresh exchange info."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_URL) as resp:
                    data = await resp.json()
                    for symbol_data in data.get('symbols', []):
                        self._parse_symbol(symbol_data)
        except Exception as e:
            logger.error(f"Failed to refresh exchange info: {e}")

    def _parse_symbol(self, symbol_data: dict) -> None:
        """Parse symbol info from exchangeInfo response."""
        symbol = symbol_data.get('symbol')
        if not symbol:
            return

        # Extract PRICE_FILTER
        tick_size = 0.1
        min_price = 0.0
        max_price = 1e9
        for filter_item in symbol_data.get('filters', []):
            if filter_item.get('filterType') == 'PRICE_FILTER':
                tick_size = float(filter_item.get('tickSize', 0.1))
                min_price = float(filter_item.get('minPrice', 0))
                max_price = float(filter_item.get('maxPrice', 1e9))
                break

        self._cache[symbol] = SymbolInfo(
            symbol=symbol,
            tick_size=tick_size,
            min_price=min_price,
            max_price=max_price,
            last_updated=int(time.time())
        )

    def _is_stale(self, symbol: str) -> bool:
        """Check if cache entry is stale."""
        if symbol not in self._cache:
            return True
        age = int(time.time()) - self._cache[symbol].last_updated
        return age > self.TTL
```

**Deliverables**:
- ✅ Fetch tickSize from Binance API
- ✅ Cache with 6h TTL
- ✅ Fallback to sensible defaults

**Time**: 1 day

### Phase 1 Completion Criteria
- [ ] WebSocket connects reliably
- [ ] forceOrder events parsed correctly
- [ ] Reconnect with exponential backoff
- [ ] Keepalive prevents timeouts
- [ ] TickSize cached and refreshed
- [ ] Tests pass for parsing and connection

**Total Time**: 1.5 weeks

---

## Phase 2: SQLite Storage Layer (Week 2-3)

**Goal**: Persistent storage with batched writes and retention policy.

**Duration**: 5-7 days

### Tasks

#### 2.1 Database Schema + Migration

**File**: `Heatmap/storage/schema.sql`

```sql
-- Liquidation events table
CREATE TABLE IF NOT EXISTS liq_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    price REAL NOT NULL,
    qty REAL NOT NULL,
    notional REAL NOT NULL,
    source TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Indices for fast queries
CREATE INDEX IF NOT EXISTS idx_liq_events_symbol_ts
    ON liq_events(symbol, ts_ms);
CREATE INDEX IF NOT EXISTS idx_liq_events_ts
    ON liq_events(ts_ms);
CREATE INDEX IF NOT EXISTS idx_liq_events_symbol_side_ts
    ON liq_events(symbol, side, ts_ms);
```

**File**: `Heatmap/storage/sqlite_store.py` (initial setup)

```python
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger("Heatmap.storage")

class SQLiteStore:
    """Persistent storage for liquidation events."""

    def __init__(self, db_path: str):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def _init_schema(self) -> None:
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        self._conn.executescript(schema_sql)
        self._conn.commit()
        logger.info("Schema initialized")

    def connect(self) -> None:
        """Connect to database and initialize."""
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row

        # Set pragmas
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute("PRAGMA cache_size=-64000")  # 64MB

        self._init_schema()
        logger.info(f"Connected to {self._db_path}")
```

**Deliverables**:
- ✅ Schema created with proper indices
- ✅ WAL mode enabled
- ✅ Pragmas configured for performance

**Time**: 1 day

#### 2.2 Batched Inserts

**Implementation** (add to `sqlite_store.py`):

```python
import asyncio
from typing import Optional
from queue import Queue
import threading

class SQLiteStore:
    def __init__(self, db_path: str, batch_size: int = 100,
                 flush_interval: float = 5.0):
        # ... existing init
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._queue: Queue = Queue()
        self._writer_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start background batch writer."""
        self.connect()
        self._running = True
        self._writer_thread = threading.Thread(target=self._batch_writer, daemon=True)
        self._writer_thread.start()
        logger.info("Batch writer started")

    def enqueue(self, event: LiquidationEvent) -> None:
        """Add event to write queue (non-blocking)."""
        self._queue.put(event)

    def _batch_writer(self) -> None:
        """Background thread: consume queue and batch insert."""
        batch = []
        last_flush = time.time()

        while self._running:
            try:
                # Try to get event with timeout
                timeout = max(0.1, self._flush_interval - (time.time() - last_flush))
                event = self._queue.get(timeout=timeout)
                batch.append(event)

                # Flush if batch full or interval elapsed
                if len(batch) >= self._batch_size or \
                   (time.time() - last_flush) >= self._flush_interval:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()

            except Empty:
                # Timeout - flush if any pending
                if batch:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()

    def _flush_batch(self, batch: list[LiquidationEvent]) -> None:
        """Insert batch of events."""
        if not batch:
            return

        try:
            self._conn.executemany(
                """INSERT INTO liq_events
                   (ts_ms, symbol, side, price, qty, notional, source, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [(e.ts_ms, e.symbol, e.side, e.price, e.qty, e.notional, e.source, e.raw_json)
                 for e in batch]
            )
            self._conn.commit()
            logger.debug(f"Flushed {len(batch)} events")
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
```

**Deliverables**:
- ✅ Non-blocking enqueue
- ✅ Background thread batches writes
- ✅ Dual trigger: batch_size OR flush_interval

**Time**: 2 days

#### 2.3 Query Time Windows

**Implementation**:

```python
class SQLiteStore:
    def query_window(self, symbol: str, start_ts: int,
                    end_ts: int) -> list[LiquidationEvent]:
        """Query events in time window [start_ts, end_ts)."""
        cursor = self._conn.execute(
            """SELECT ts_ms, symbol, side, price, qty, notional, source, raw_json
               FROM liq_events
               WHERE symbol = ? AND ts_ms >= ? AND ts_ms < ?
               ORDER BY ts_ms ASC""",
            (symbol, start_ts, end_ts)
        )

        events = []
        for row in cursor:
            events.append(LiquidationEvent(
                ts_ms=row['ts_ms'],
                symbol=row['symbol'],
                side=row['side'],
                price=row['price'],
                qty=row['qty'],
                notional=row['notional'],
                source=row['source'],
                raw_json=row['raw_json']
            ))

        logger.info(f"Queried {len(events)} events for {symbol} [{start_ts}, {end_ts})")
        return events
```

**Deliverables**:
- ✅ Efficient time-range queries
- ✅ Indexed query (uses idx_liq_events_symbol_ts)

**Time**: 0.5 days

#### 2.4 Retention Policy

**Implementation**:

```python
class SQLiteStore:
    def cleanup_old_events(self, retention_days: int = 14) -> int:
        """Delete events older than retention_days."""
        cutoff_ts = int(time.time() * 1000) - (retention_days * 86400 * 1000)

        cursor = self._conn.execute(
            "DELETE FROM liq_events WHERE ts_ms < ?",
            (cutoff_ts,)
        )
        self._conn.commit()
        deleted = cursor.rowcount

        logger.info(f"Retention cleanup: deleted {deleted} events older than {retention_days} days")
        return deleted

    def vacuum(self) -> None:
        """Reclaim disk space (run during low-activity hours)."""
        logger.info("Running VACUUM...")
        self._conn.execute("VACUUM")
        logger.info("VACUUM complete")
```

**Deliverables**:
- ✅ Delete events older than N days
- ✅ VACUUM for disk reclamation

**Time**: 0.5 days

#### 2.5 Tests

**File**: `Heatmap/tests/test_sqlite_store.py`

```python
import pytest
from Heatmap.storage.sqlite_store import SQLiteStore
from Heatmap.ingestion.binance_forceorder_ws import LiquidationEvent
import time

def test_insert_and_query(tmp_path):
    """Test insert and query operations."""
    db_path = tmp_path / "test.db"
    store = SQLiteStore(str(db_path), batch_size=10, flush_interval=1.0)
    store.start()

    # Insert test events
    events = [
        LiquidationEvent(
            ts_ms=1736789400000 + i * 1000,
            symbol="BTCUSDT",
            side="BUY" if i % 2 == 0 else "SELL",
            price=95000.0 + i,
            qty=0.1,
            notional=(95000.0 + i) * 0.1,
            source="TEST"
        )
        for i in range(100)
    ]

    for event in events:
        store.enqueue(event)

    # Wait for flush
    time.sleep(2)

    # Query
    results = store.query_window("BTCUSDT", 1736789400000, 1736789500000)
    assert len(results) == 100

def test_retention(tmp_path):
    """Test retention cleanup."""
    db_path = tmp_path / "test.db"
    store = SQLiteStore(str(db_path))
    store.start()

    # Insert old events
    old_ts = int(time.time() * 1000) - (30 * 86400 * 1000)  # 30 days ago
    for i in range(50):
        store.enqueue(LiquidationEvent(
            ts_ms=old_ts + i * 1000,
            symbol="BTCUSDT",
            side="BUY",
            price=95000.0,
            qty=0.1,
            notional=9500.0,
            source="TEST"
        ))

    time.sleep(2)

    # Cleanup (14 day retention)
    deleted = store.cleanup_old_events(retention_days=14)
    assert deleted == 50
```

**Deliverables**:
- ✅ Test insert and query
- ✅ Test retention cleanup
- ✅ Test batch flush timing

**Time**: 1 day

### Phase 2 Completion Criteria
- [ ] Schema created with indices
- [ ] Batched writes working (100 events or 5s)
- [ ] Query time windows efficiently
- [ ] Retention policy deletes old events
- [ ] All tests pass

**Total Time**: 1 week

---

## Phase 3: Aggregation Layer (Week 3-4)

**Goal**: Build heatmap grid from events with normalization and decay.

**Duration**: 5-7 days

### Tasks

#### 3.1 Grid Builder - Resolution Calculation

**File**: `Heatmap/aggregation/grid_builder.py` (≤600 LOC)

```python
from dataclasses import dataclass
import numpy as np
from math import ceil, floor
import logging

logger = logging.getLogger("Heatmap.aggregation")

@dataclass
class GridConfig:
    """Configuration for heatmap grid generation."""
    price_low: float
    price_high: float
    time_start: int
    time_end: int
    tick_size: float
    chart_width_px: int
    chart_height_px: int
    target_px_per_cell: float = 2.3

    def calculate_rows(self) -> int:
        """Calculate number of price bins (rows)."""
        rows = int(self.chart_height_px / self.target_px_per_cell)
        return max(180, min(rows, 380))

    def calculate_cols(self) -> int:
        """Calculate number of time bins (columns)."""
        cols = int(self.chart_width_px / 1.15)
        return max(800, min(cols, 1700))

    def price_bin_size(self) -> float:
        """Calculate price bin size, rounded to tickSize."""
        range_price = self.price_high - self.price_low
        raw_bin = range_price / self.calculate_rows()
        return ceil(raw_bin / self.tick_size) * self.tick_size

    def time_bin_size(self) -> int:
        """Calculate time bin size in seconds."""
        window_seconds = (self.time_end - self.time_start) / 1000
        raw_bin = window_seconds / self.calculate_cols()

        # Round to standard intervals
        for interval in [5, 10, 15, 30, 60, 120, 180, 300, 600]:
            if raw_bin <= interval:
                return interval
        return 600
```

**Deliverables**:
- ✅ Auto-resolution based on chart dimensions
- ✅ TickSize rounding
- ✅ Configurable target cell size

**Time**: 1 day

#### 3.2 Grid Builder - Event Binning

**Implementation** (continue `grid_builder.py`):

```python
@dataclass
class HeatmapCell:
    """Single cell in heatmap grid."""
    time_bin: int
    price_bin: int
    intensity: float
    count: int
    side: str

class GridBuilder:
    """Build heatmap grid from liquidation events."""

    def build_grid(self, events: list[LiquidationEvent],
                   config: GridConfig) -> list[HeatmapCell]:
        """Build grid from events using config."""
        rows = config.calculate_rows()
        cols = config.calculate_cols()
        price_bin_size = config.price_bin_size()
        time_bin_size = config.time_bin_size()

        # Initialize grid arrays (numpy for speed)
        intensity_buy = np.zeros((rows, cols), dtype=np.float32)
        intensity_sell = np.zeros((rows, cols), dtype=np.float32)
        counts = np.zeros((rows, cols), dtype=np.int32)

        # Bin events
        for event in events:
            # Calculate bin indices
            time_bin = int((event.ts_ms - config.time_start) / (time_bin_size * 1000))
            price_bin = int((event.price - config.price_low) / price_bin_size)

            # Bounds check
            if not (0 <= time_bin < cols and 0 <= price_bin < rows):
                continue

            # Accumulate intensity
            if event.side == "BUY":
                intensity_buy[price_bin, time_bin] += event.notional
            else:
                intensity_sell[price_bin, time_bin] += event.notional
            counts[price_bin, time_bin] += 1

        # Convert to cell list (only non-zero)
        cells = []
        for row in range(rows):
            for col in range(cols):
                if counts[row, col] == 0:
                    continue

                buy_val = intensity_buy[row, col]
                sell_val = intensity_sell[row, col]
                total = buy_val + sell_val

                if buy_val > sell_val:
                    side = "BUY"
                elif sell_val > buy_val:
                    side = "SELL"
                else:
                    side = "MIXED"

                cells.append(HeatmapCell(
                    time_bin=col,
                    price_bin=row,
                    intensity=total,
                    count=counts[row, col],
                    side=side
                ))

        logger.info(f"Built grid: {rows}x{cols}, {len(cells)} non-zero cells")
        return cells
```

**Deliverables**:
- ✅ Numpy-based grid for performance
- ✅ Separate BUY/SELL tracking
- ✅ Return only non-zero cells (sparse)

**Time**: 2 days

#### 3.3 Normalization

**File**: `Heatmap/aggregation/normalization.py` (≤600 LOC)

```python
from enum import Enum
import numpy as np

class NormalizationMethod(Enum):
    LINEAR = "linear"
    SQRT = "sqrt"
    LOG = "log"

class Normalizer:
    """Normalize heatmap intensity values."""

    def normalize(self, cells: list[HeatmapCell],
                  method: NormalizationMethod = NormalizationMethod.SQRT,
                  clip_percentile: float = 99.0) -> list[HeatmapCell]:
        """Normalize cell intensities to [0, 1]."""
        if not cells:
            return cells

        # Extract intensities
        intensities = np.array([c.intensity for c in cells])

        # Clip outliers
        if clip_percentile < 100:
            threshold = np.percentile(intensities, clip_percentile)
            intensities = np.clip(intensities, 0, threshold)

        # Normalize
        if method == NormalizationMethod.LINEAR:
            normalized = self._linear_norm(intensities)
        elif method == NormalizationMethod.SQRT:
            normalized = self._sqrt_norm(intensities)
        elif method == NormalizationMethod.LOG:
            normalized = self._log_norm(intensities)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Update cells
        for cell, norm_val in zip(cells, normalized):
            cell.intensity = float(norm_val)

        return cells

    def _linear_norm(self, values: np.ndarray) -> np.ndarray:
        """Min-max normalization."""
        min_val = values.min()
        max_val = values.max()
        if max_val == min_val:
            return np.ones_like(values)
        return (values - min_val) / (max_val - min_val)

    def _sqrt_norm(self, values: np.ndarray) -> np.ndarray:
        """Square root normalization."""
        sqrt_vals = np.sqrt(values)
        return self._linear_norm(sqrt_vals)

    def _log_norm(self, values: np.ndarray) -> np.ndarray:
        """Logarithmic normalization."""
        log_vals = np.log(values + 1)
        return self._linear_norm(log_vals)
```

**Deliverables**:
- ✅ Three normalization methods
- ✅ Percentile clipping for outliers
- ✅ In-place cell updates

**Time**: 1 day

#### 3.4 Time Decay

**File**: `Heatmap/aggregation/decay.py` (≤600 LOC)

```python
from enum import Enum
import time

class DecayConfig(Enum):
    DISABLED = None
    FAST = 1200      # 20 minutes
    MEDIUM = 3600    # 60 minutes
    SLOW = 21600     # 6 hours

class TimeDecay:
    """Apply time-based decay to heatmap intensity."""

    def apply_decay(self, cells: list[HeatmapCell],
                   config: GridConfig,
                   decay_config: DecayConfig) -> list[HeatmapCell]:
        """Apply exponential decay based on event age."""
        if decay_config == DecayConfig.DISABLED:
            return cells

        current_ts = int(time.time() * 1000)
        half_life = decay_config.value

        for cell in cells:
            # Calculate event timestamp from bin index
            event_ts = config.time_start + (cell.time_bin * config.time_bin_size() * 1000)
            decay_factor = self._calculate_decay_factor(event_ts, current_ts, half_life)
            cell.intensity *= decay_factor

        return cells

    def _calculate_decay_factor(self, event_ts: int, current_ts: int,
                               half_life: int) -> float:
        """Calculate decay factor: 0.5 ^ (age / half_life)."""
        age_seconds = (current_ts - event_ts) / 1000
        if age_seconds <= 0:
            return 1.0
        return 0.5 ** (age_seconds / half_life)
```

**Deliverables**:
- ✅ Exponential decay with configurable half-life
- ✅ Optional (can be disabled)

**Time**: 0.5 days

#### 3.5 Tests

**File**: `Heatmap/tests/test_grid_builder.py`

```python
import pytest
from Heatmap.aggregation.grid_builder import GridBuilder, GridConfig
from Heatmap.ingestion.binance_forceorder_ws import LiquidationEvent

def test_grid_resolution():
    """Test grid resolution calculations."""
    config = GridConfig(
        price_low=95000.0,
        price_high=105000.0,
        time_start=1736789400000,
        time_end=1736796600000,  # 2 hours
        tick_size=0.1,
        chart_width_px=1060,
        chart_height_px=550
    )

    assert 180 <= config.calculate_rows() <= 380
    assert 800 <= config.calculate_cols() <= 1700
    assert config.price_bin_size() % config.tick_size < 1e-6  # Rounded correctly

def test_build_grid():
    """Test grid building from events."""
    config = GridConfig(
        price_low=95000.0,
        price_high=95100.0,
        time_start=1736789400000,
        time_end=1736789460000,  # 1 minute
        tick_size=0.1,
        chart_width_px=1000,
        chart_height_px=500
    )

    events = [
        LiquidationEvent(
            ts_ms=1736789420000,
            symbol="BTCUSDT",
            side="BUY",
            price=95050.0,
            qty=1.0,
            notional=95050.0
        ),
        # ... more test events
    ]

    builder = GridBuilder()
    cells = builder.build_grid(events, config)

    assert len(cells) > 0
    assert all(0 <= c.time_bin < config.calculate_cols() for c in cells)
    assert all(0 <= c.price_bin < config.calculate_rows() for c in cells)
```

**Deliverables**:
- ✅ Test resolution calculations
- ✅ Test event binning accuracy
- ✅ Test normalization determinism

**Time**: 1 day

### Phase 3 Completion Criteria
- [ ] Grid builder generates correct dimensions
- [ ] Events binned accurately (no off-by-one errors)
- [ ] Normalization methods work correctly
- [ ] Time decay applies exponential falloff
- [ ] All tests pass

**Total Time**: 1 week

---

## Phase 4: UI Integration (Week 4-5)

**Goal**: Render heatmap as background layer in Lightweight Charts.

**Duration**: 7-10 days

### Tasks

#### 4.1 JavaScript Heatmap Series

**File**: `Heatmap/ui/js/heatmap_series.js`

```javascript
// Heatmap custom series for Lightweight Charts
class HeatmapSeries {
  constructor(options = {}) {
    this.options = {
      opacity: options.opacity || 0.5,
      palette: options.palette || 'fire',
      ...options
    };
    this._data = [];
    this._grid = null;
  }

  // Required by Lightweight Charts plugin API
  renderer() {
    return new HeatmapRenderer(this._data, this._grid, this.options);
  }

  priceAxisViews() {
    return [];
  }

  timeAxisViews() {
    return [];
  }

  // Public API
  setData(heatmapData) {
    this._grid = heatmapData.grid;
    this._data = heatmapData.cells;
    this._invalidate();
  }

  appendDeltas(deltas) {
    deltas.forEach(delta => {
      const idx = this._findCellIndex(delta.time_bin, delta.price_bin);
      if (idx >= 0) {
        this._data[idx] = delta;
      } else {
        this._data.push(delta);
      }
    });
    this._invalidate();
  }

  clear() {
    this._data = [];
    this._grid = null;
    this._invalidate();
  }

  _findCellIndex(timeBin, priceBin) {
    return this._data.findIndex(
      c => c.time_bin === timeBin && c.price_bin === priceBin
    );
  }

  _invalidate() {
    if (this._chart) {
      this._chart.requestUpdate();
    }
  }

  attached(param) {
    this._chart = param.chart;
  }
}

// Renderer: draws cells on canvas
class HeatmapRenderer {
  constructor(data, grid, options) {
    this._data = data;
    this._grid = grid;
    this._options = options;
  }

  draw(target) {
    if (!this._grid || !this._data.length) return;

    const ctx = target.context;
    const timeToCoordinate = target.timeToCoordinate.bind(target);
    const priceToCoordinate = target.priceToCoordinate.bind(target);

    this._data.forEach(cell => {
      // Convert bin indices to canvas coordinates
      const timeStart = this._grid.time_start + (cell.time_bin * this._grid.time_bin_size * 1000);
      const timeEnd = timeStart + (this._grid.time_bin_size * 1000);
      const priceStart = this._grid.price_low + (cell.price_bin * this._grid.price_bin_size);
      const priceEnd = priceStart + this._grid.price_bin_size;

      const x1 = timeToCoordinate(timeStart);
      const x2 = timeToCoordinate(timeEnd);
      const y1 = priceToCoordinate(priceEnd);  // Note: inverted Y axis
      const y2 = priceToCoordinate(priceStart);

      if (x1 === null || x2 === null || y1 === null || y2 === null) {
        return;  // Off-screen
      }

      const width = x2 - x1;
      const height = y2 - y1;

      // Get color from palette
      const color = this._getColor(cell.intensity, cell.side);

      ctx.fillStyle = color;
      ctx.globalAlpha = this._options.opacity;
      ctx.fillRect(x1, y1, width, height);
    });

    ctx.globalAlpha = 1.0;  // Reset
  }

  _getColor(intensity, side) {
    // Map intensity to color (implementation in heatmap_palette.js)
    return getColorFromPalette(intensity, side, this._options.palette);
  }
}

// Export for use in main chart
window.HeatmapSeries = HeatmapSeries;
```

**Deliverables**:
- ✅ Custom series plugin
- ✅ Canvas-based rendering
- ✅ Delta update support

**Time**: 3 days

#### 4.2 Python-JS Bridge

**File**: `Heatmap/ui/bridge.py` (≤600 LOC)

```python
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import json
import asyncio
import time
import logging

logger = logging.getLogger("Heatmap.ui")

class HeatmapBridge(QObject):
    """QWebChannel bridge for heatmap communication."""

    # Signals (Python → JavaScript)
    heatmapDataReady = pyqtSignal(str)
    heatmapDeltaReady = pyqtSignal(str)
    heatmapStatusChanged = pyqtSignal(str)
    heatmapError = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._last_update_time = 0.0
        self._update_interval = 0.5  # 500ms rate limit
        self._pending_deltas: list[HeatmapCell] = []

    @pyqtSlot(str, str, int, int, float, float)
    def loadHeatmap(self, symbol: str, window: str,
                   chart_width: int, chart_height: int,
                   price_low: float, price_high: float) -> None:
        """Load heatmap for time window (called from JS)."""
        try:
            logger.info(f"Loading heatmap: {symbol} {window}")

            # Calculate time range
            now_ms = int(time.time() * 1000)
            window_ms = self._parse_window(window)
            start_ts = now_ms - window_ms
            end_ts = now_ms

            # Query DB for events
            store = self._get_store()
            events = store.query_window(symbol, start_ts, end_ts)

            # Get tickSize
            exchange_info = self._get_exchange_info()
            tick_size = asyncio.run(exchange_info.get_tick_size(symbol))

            # Build grid
            config = GridConfig(
                price_low=price_low,
                price_high=price_high,
                time_start=start_ts,
                time_end=end_ts,
                tick_size=tick_size,
                chart_width_px=chart_width,
                chart_height_px=chart_height
            )

            builder = GridBuilder()
            cells = builder.build_grid(events, config)

            # Normalize
            normalizer = Normalizer()
            cells = normalizer.normalize(cells, method=self._get_normalization_method())

            # Apply decay
            decay = TimeDecay()
            cells = decay.apply_decay(cells, config, self._get_decay_config())

            # Serialize to JSON
            data = {
                "symbol": symbol,
                "window": window,
                "grid": {
                    "rows": config.calculate_rows(),
                    "cols": config.calculate_cols(),
                    "price_low": price_low,
                    "price_high": price_high,
                    "time_start": start_ts,
                    "time_end": end_ts,
                    "price_bin_size": config.price_bin_size(),
                    "time_bin_size": config.time_bin_size()
                },
                "cells": [
                    {
                        "time_bin": c.time_bin,
                        "price_bin": c.price_bin,
                        "intensity": c.intensity,
                        "count": c.count,
                        "side": c.side
                    }
                    for c in cells
                ]
            }

            json_data = json.dumps(data)
            self.heatmapDataReady.emit(json_data)
            logger.info(f"Heatmap loaded: {len(cells)} cells")

        except Exception as e:
            logger.error(f"Failed to load heatmap: {e}")
            self.heatmapError.emit(str(e))

    def _add_live_event(self, event: LiquidationEvent) -> None:
        """Add live event to pending deltas (internal)."""
        # Convert to cell (simplified - would need current grid config)
        # ... implementation
        self._pending_deltas.append(cell)

        # Flush if rate limit elapsed
        if time.time() - self._last_update_time > self._update_interval:
            self._flush_deltas()

    def _flush_deltas(self) -> None:
        """Flush pending deltas to JavaScript."""
        if not self._pending_deltas:
            return

        try:
            data = {
                "deltas": [
                    {
                        "time_bin": c.time_bin,
                        "price_bin": c.price_bin,
                        "intensity": c.intensity,
                        "count": c.count,
                        "side": c.side
                    }
                    for c in self._pending_deltas
                ]
            }

            json_data = json.dumps(data)
            self.heatmapDeltaReady.emit(json_data)
            self._pending_deltas = []
            self._last_update_time = time.time()
            logger.debug(f"Flushed {len(data['deltas'])} delta cells")

        except Exception as e:
            logger.error(f"Failed to flush deltas: {e}")

    def _parse_window(self, window: str) -> int:
        """Parse window string to milliseconds."""
        if window == "2h":
            return 2 * 3600 * 1000
        elif window == "8h":
            return 8 * 3600 * 1000
        elif window == "2d":
            return 2 * 86400 * 1000
        else:
            raise ValueError(f"Invalid window: {window}")
```

**Deliverables**:
- ✅ QWebChannel bridge
- ✅ Async data loading
- ✅ Rate-limited delta updates

**Time**: 2 days

#### 4.3 Chart Integration

**File**: `src/ui/widgets/chart_mixins/heatmap_mixin.py` (new)

```python
class HeatmapMixin:
    """Mixin for heatmap functionality in chart widget."""

    def _init_heatmap(self):
        """Initialize heatmap components."""
        from Heatmap.ui.bridge import HeatmapBridge

        self._heatmap_bridge = HeatmapBridge(self)
        self._heatmap_service = None

        # Register with QWebChannel
        if hasattr(self, 'channel'):
            self.channel.registerObject("heatmapBridge", self._heatmap_bridge)

    def set_heatmap_service(self, service):
        """Set heatmap service reference."""
        from Heatmap.heatmap_service import HeatmapService
        self._heatmap_service = service

    def reload_heatmap(self):
        """Reload heatmap with current chart state."""
        # Implementation: get visible range, trigger bridge load
```

**Update**: `src/ui/widgets/embedded_tradingview_chart.py`
```python
class EmbeddedTradingViewChart(
    HeatmapMixin,  # NEW
    EntryAnalyzerMixin,
    # ... rest
):
    def __init__(self, history_manager=None):
        super().__init__()
        # ... existing
        self._init_heatmap()  # NEW
```

**Deliverables**:
- ✅ Mixin integrated into chart widget
- ✅ Service reference passed from app

**Time**: 1 day

#### 4.4 HTML Template Update

**File**: `src/ui/widgets/chart_js_template.py`

Add heatmap JavaScript to template:
```python
def get_chart_html_template() -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <script>
            let chart = null;
            let heatmapSeries = null;

            new QWebChannel(qt.webChannelTransport, function(channel) {{
                window.chartBridge = channel.objects.chartBridge;
                window.heatmapBridge = channel.objects.heatmapBridge;

                // Heatmap data ready
                heatmapBridge.heatmapDataReady.connect(function(jsonData) {{
                    const data = JSON.parse(jsonData);

                    if (!heatmapSeries) {{
                        heatmapSeries = chart.addCustomSeries(new HeatmapSeries({{
                            opacity: 0.5,
                            palette: 'fire'
                        }}));
                    }}

                    heatmapSeries.setData(data);
                }});

                // Delta updates
                heatmapBridge.heatmapDeltaReady.connect(function(jsonData) {{
                    const delta = JSON.parse(jsonData);
                    if (heatmapSeries) {{
                        heatmapSeries.appendDeltas(delta.deltas);
                    }}
                }});
            }});
        </script>
        <script src="qrc:///heatmap_series.js"></script>
        <script src="qrc:///heatmap_palette.js"></script>
    </head>
    <body>
        <div id="chart"></div>
    </body>
    </html>
    """
```

**Deliverables**:
- ✅ Heatmap series loaded in HTML
- ✅ Bridge signals connected

**Time**: 1 day

#### 4.5 Toggle ON/OFF

Handled via settings (Phase 5).

### Phase 4 Completion Criteria
- [ ] Heatmap renders as background layer
- [ ] Candles remain readable (in front)
- [ ] Toggle ON loads from DB
- [ ] Live updates work without lag
- [ ] Toggle OFF removes series

**Total Time**: 1.5 weeks

---

## Phase 5: Settings Tab (Week 5-6)

**Goal**: Add heatmap settings tab to main settings dialog.

**Duration**: 3-5 days

### Tasks

#### 5.1 Settings Model

**File**: `Heatmap/heatmap_settings.py` (≤600 LOC)

Already defined in architecture. Implement Pydantic model and manager.

**Time**: 1 day

#### 5.2 Settings UI Tab

**File**: `src/ui/dialogs/settings_tabs_mixin.py`

Add `_create_heatmap_tab()` method as defined in architecture.

**Time**: 1 day

#### 5.3 Settings Persistence

Connect UI controls to QSettings and HeatmapSettingsManager.

**Time**: 0.5 days

#### 5.4 Live Preview

Changes in settings trigger immediate heatmap reload.

**Time**: 0.5 days

### Phase 5 Completion Criteria
- [ ] Heatmap tab visible in Settings
- [ ] All controls functional
- [ ] Settings persist across sessions
- [ ] Live preview works

**Total Time**: 3 days

---

## Phase 6: Quality & Performance (Week 6-7)

**Goal**: Ensure stability, performance, and documentation.

**Duration**: 5-7 days

### Tasks

#### 6.1 Logging & Debug

- Add comprehensive logging
- Debug-level raw payload storage
- Performance timers

**Time**: 1 day

#### 6.2 Performance Metrics

- Measure DB insert rate
- Measure grid build time
- Measure render FPS

**Time**: 1 day

#### 6.3 Stability Testing

- Reconnect torture test (network on/off)
- Memory leak detection
- Long-running test (24h+)

**Time**: 2 days

#### 6.4 Documentation

- Update `Heatmap/README.md` with setup instructions
- Document limitations (snapshot behavior)
- Troubleshooting guide

**Time**: 1 day

### Phase 6 Completion Criteria
- [ ] All logging in place
- [ ] Performance metrics logged
- [ ] Stability tests pass
- [ ] Documentation complete

**Total Time**: 1 week

---

## Phase 7: Integration Testing (Week 7-8)

**Goal**: End-to-end testing in production-like environment.

**Duration**: 3-5 days

### Tasks

#### 7.1 Full Integration Test

- Start app, verify service starts
- Toggle heatmap ON, verify rendering
- Resize window, verify grid rebuilds
- Toggle OFF, verify removal
- Restart app, verify persistence

**Time**: 2 days

#### 7.2 Load Testing

- Simulate high event rate (1000 events/sec)
- Monitor DB performance
- Monitor UI responsiveness

**Time**: 1 day

#### 7.3 User Acceptance

- Internal testing with real Binance data
- Collect feedback
- Fix critical issues

**Time**: 1 day

### Phase 7 Completion Criteria
- [ ] All integration tests pass
- [ ] Load tests meet targets
- [ ] User feedback addressed

**Total Time**: 4 days

---

## Phase 8: Deployment (Week 8)

**Goal**: Deploy to production.

**Duration**: 1-2 days

### Tasks

#### 8.1 Final Review

- Code review all files
- Check file sizes (≤600 LOC)
- Verify no root-level files created

**Time**: 0.5 days

#### 8.2 Merge to Main

- Create PR with full changelog
- Review and merge
- Tag release

**Time**: 0.5 days

#### 8.3 Deployment

- Deploy to production environment
- Monitor for issues
- Document release notes

**Time**: 0.5 days

### Phase 8 Completion Criteria
- [ ] Code reviewed and merged
- [ ] Deployed to production
- [ ] Monitoring active

**Total Time**: 1.5 days

---

## Summary Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 0: Preparation | 1 day | Directory structure, standards |
| 1: Ingestion | 1.5 weeks | WebSocket client, reconnect, tickSize |
| 2: Storage | 1 week | SQLite schema, batched writes, retention |
| 3: Aggregation | 1 week | Grid builder, normalization, decay |
| 4: UI Integration | 1.5 weeks | JS series, bridge, rendering |
| 5: Settings | 3 days | Settings tab, persistence |
| 6: Quality | 1 week | Logging, performance, docs |
| 7: Integration Testing | 4 days | End-to-end testing |
| 8: Deployment | 1.5 days | Review, merge, deploy |

**Total Duration**: 6-8 weeks (depending on team size and complexity)

---

## Risk Mitigation

### High-Risk Areas

1. **WebSocket Stability**
   - Risk: Frequent disconnections
   - Mitigation: Robust reconnect logic, extensive testing

2. **Performance at Scale**
   - Risk: DB writes block UI
   - Mitigation: Batching, WAL mode, background threads

3. **Canvas Rendering Performance**
   - Risk: Large grids cause lag
   - Mitigation: Sparse cell storage, rate-limited updates

### Contingency Plans

- If performance issues arise: Reduce grid resolution
- If reconnect issues persist: Add circuit breaker pattern
- If UI lag occurs: Increase rate limit interval

---

## Success Metrics

- [ ] WebSocket uptime >99.5%
- [ ] DB write latency <50ms (p95)
- [ ] Heatmap load time <200ms (2h window)
- [ ] UI responsiveness maintained (no freezes >100ms)
- [ ] Memory usage <100 MB additional
- [ ] Zero data loss during reconnections

---

*End of Implementation Plan*
