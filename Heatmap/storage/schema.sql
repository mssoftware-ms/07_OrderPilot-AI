-- Binance Liquidation Events Table
-- Stores raw liquidation data for heatmap generation

CREATE TABLE IF NOT EXISTS liq_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,          -- Event timestamp in milliseconds
    symbol TEXT NOT NULL,             -- Trading pair (e.g., BTCUSDT)
    side TEXT NOT NULL,               -- BUY (long liq) or SELL (short liq)
    price REAL NOT NULL,              -- Liquidation price
    qty REAL NOT NULL,                -- Quantity liquidated
    notional REAL NOT NULL,           -- price * qty
    source TEXT NOT NULL,             -- Data source (e.g., BINANCE_USDM)
    raw_json TEXT NOT NULL            -- Original payload for debugging/replay
);

-- Index for time-based queries (most common: fetch events in time window)
CREATE INDEX IF NOT EXISTS idx_liq_events_ts ON liq_events(ts_ms);

-- Composite index for symbol + time queries (fetch specific symbol in window)
CREATE INDEX IF NOT EXISTS idx_liq_events_symbol_ts ON liq_events(symbol, ts_ms);

-- Index for side queries (analyze long vs short liquidations)
CREATE INDEX IF NOT EXISTS idx_liq_events_side ON liq_events(side);

-- Pragmas for optimal performance
-- These are set at runtime in sqlite_store.py:
-- PRAGMA journal_mode=WAL;         -- Write-Ahead Log for concurrent read/write
-- PRAGMA synchronous=NORMAL;        -- Balance safety vs performance
-- PRAGMA temp_store=MEMORY;         -- Store temp tables in memory
-- PRAGMA cache_size=-64000;         -- 64MB cache
-- PRAGMA mmap_size=268435456;       -- 256MB memory-mapped I/O
