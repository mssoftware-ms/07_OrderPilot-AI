# Binance Liquidation Heatmap - System Architecture

**Version:** 1.0
**Date:** 2026-01-13
**Status:** Design Document
**Author:** System Architecture Designer

---

## Executive Summary

This document defines the complete architecture for integrating a real-time Binance liquidation heatmap into the OrderPilot-AI trading platform. The heatmap operates as a background service that continuously ingests liquidation events from Binance USD-M Futures (`btcusdt@forceOrder` stream), persists them to SQLite, and renders them as a background layer on Lightweight Charts.

### Key Design Principles

1. **Always-On Background Service**: Data ingestion runs continuously, independent of UI state
2. **Persistence-First**: All events persisted to SQLite with WAL mode for concurrent access
3. **Load-On-Demand**: Heatmap grid built from historical data when activated
4. **Incremental Updates**: Live events incrementally update the rendered grid
5. **File Organization**: All new files under `root/Heatmap/`, max 600 lines per file
6. **Zero External Dependencies**: Uses existing libraries (websockets, aiohttp, PyQt6, qasync, numpy, SQLAlchemy)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OrderPilot-AI Application                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────┐         ┌─────────────────────────┐      │
│  │  Settings UI  │◄────────┤  Heatmap Settings Model │      │
│  │  (Heatmap Tab)│         │  (opacity, palette,     │      │
│  └───────┬───────┘         │   normalization, decay) │      │
│          │                 └──────────┬──────────────┘      │
│          │                            │                      │
│          ▼                            ▼                      │
│  ┌───────────────────────────────────────────────────┐      │
│  │         Heatmap Service (Orchestrator)            │      │
│  │  - Start/Stop/Status management                   │      │
│  │  - Coordinates ingestion, storage, aggregation    │      │
│  └───────┬───────────────────────────────────────────┘      │
│          │                                                   │
│  ┌───────┴───────┬───────────────┬──────────────────┐      │
│  │               │               │                  │      │
│  ▼               ▼               ▼                  ▼      │
│ ┌────────┐  ┌─────────┐  ┌──────────┐  ┌──────────────┐   │
│ │Ingestion│  │ Storage │  │Aggregation│  │   UI Bridge  │   │
│ │ Layer   │  │ Layer   │  │  Layer    │  │ (Python→JS)  │   │
│ └────────┘  └─────────┘  └──────────┘  └──────────────┘   │
│     │            │              │              │            │
└─────┼────────────┼──────────────┼──────────────┼───────────┘
      │            │              │              │
      ▼            ▼              │              ▼
┌──────────┐  ┌─────────┐        │    ┌──────────────────┐
│ Binance  │  │ SQLite  │        │    │ Lightweight      │
│ WebSocket│  │   DB    │        │    │ Charts           │
│  Stream  │  │  (WAL)  │        │    │ (QWebEngineView) │
└──────────┘  └─────────┘        │    └──────────────────┘
                                  │
                                  ▼
                            ┌──────────┐
                            │  Memory  │
                            │  Grid    │
                            └──────────┘
```

### 1.2 Component Responsibilities

| Component | Responsibility | Key Technologies |
|-----------|---------------|------------------|
| **Ingestion Layer** | WebSocket connection, event parsing, auto-reconnect | websockets, asyncio |
| **Storage Layer** | SQLite persistence, batched writes, retention policy | SQLAlchemy, sqlite3 |
| **Aggregation Layer** | Grid building, normalization, time decay | numpy, pandas |
| **UI Bridge** | Python-JavaScript communication, data serialization | QWebChannel, PyQt6 |
| **Settings Management** | Configuration persistence, validation | QSettings, Pydantic |

---

## 2. Component Architecture

### 2.1 Ingestion Layer

**Location**: `Heatmap/ingestion/`

#### 2.1.1 Binance WebSocket Client

**File**: `binance_forceorder_ws.py` (≤600 LOC)

**Responsibilities**:
- Connect to `wss://fstream.binance.com/ws/btcusdt@forceOrder`
- Parse incoming `forceOrder` events (snapshot every 1000ms)
- Handle connection lifecycle (connect/disconnect/shutdown)
- Implement keepalive (ping/pong) and 24h reconnection
- Emit parsed events to event queue

**Key Classes**:
```python
@dataclass
class LiquidationEvent:
    """Parsed liquidation event from Binance."""
    ts_ms: int              # Event timestamp in milliseconds
    symbol: str             # E.g., "BTCUSDT"
    side: str               # "BUY" or "SELL" (liquidation side)
    price: float            # Liquidation price
    qty: float              # Liquidation quantity
    notional: float         # price * qty (in USD)
    source: str = "BINANCE_USDM"
    raw_json: str = ""      # Original JSON payload for debugging

class BinanceForceOrderClient:
    """WebSocket client for Binance forceOrder stream."""

    async def connect(self) -> None:
        """Establish WebSocket connection with error handling."""

    async def _message_loop(self) -> None:
        """Main message processing loop with ping/pong."""

    async def _reconnect_with_backoff(self) -> None:
        """Exponential backoff reconnection (1s, 2s, 4s, ...max 60s)."""

    async def shutdown(self) -> None:
        """Graceful shutdown of WebSocket connection."""
```

**Connection Management**:
- **Backoff Strategy**: Exponential with jitter (1s → 2s → 4s → 8s → 16s → 32s → 60s max)
- **Keepalive**: Server pings periodically, client must respond with pong
- **24h Reconnect**: Preemptively reconnect at 23h 50m to avoid disconnection
- **Error Handling**: Log errors, emit metrics, continue reconnection loop

#### 2.1.2 Exchange Info Cache

**File**: `exchange_info.py` (≤600 LOC)

**Responsibilities**:
- Fetch `tickSize` from `GET /fapi/v1/exchangeInfo` endpoint
- Cache tickSize values (refresh every 6h or on error)
- Provide tickSize for price bin rounding

**Key Classes**:
```python
@dataclass
class SymbolInfo:
    """Symbol trading rules from exchange."""
    symbol: str
    tick_size: float
    min_price: float
    max_price: float
    last_updated: int  # Unix timestamp

class ExchangeInfoCache:
    """Cache for Binance exchange info (tickSize, filters)."""

    async def get_tick_size(self, symbol: str) -> float:
        """Get tickSize for symbol, refresh if stale."""

    async def refresh(self) -> None:
        """Fetch fresh exchange info from Binance API."""

    def _is_stale(self) -> bool:
        """Check if cache is older than 6 hours."""
```

**Cache Strategy**:
- **TTL**: 6 hours (tickSize rarely changes)
- **Fallback**: If API fails, use last known value or sensible default (0.01 for BTCUSDT)
- **Storage**: In-memory dict with optional SQLite persistence

---

### 2.2 Storage Layer

**Location**: `Heatmap/storage/`

#### 2.2.1 SQLite Schema

**File**: `schema.sql`

```sql
-- Liquidation events table
CREATE TABLE IF NOT EXISTS liq_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ms INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,           -- 'BUY' or 'SELL'
    price REAL NOT NULL,
    qty REAL NOT NULL,
    notional REAL NOT NULL,       -- price * qty
    source TEXT NOT NULL,          -- 'BINANCE_USDM'
    raw_json TEXT NOT NULL,        -- Full JSON for debugging
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Indices for fast queries
CREATE INDEX IF NOT EXISTS idx_liq_events_symbol_ts
    ON liq_events(symbol, ts_ms);
CREATE INDEX IF NOT EXISTS idx_liq_events_ts
    ON liq_events(ts_ms);
CREATE INDEX IF NOT EXISTS idx_liq_events_symbol_side_ts
    ON liq_events(symbol, side, ts_ms);

-- Pragmas for write optimization (set programmatically)
PRAGMA journal_mode=WAL;           -- Write-Ahead Logging (concurrent reads)
PRAGMA synchronous=NORMAL;         -- Balance safety/speed for market data
PRAGMA temp_store=MEMORY;          -- In-memory temp tables
PRAGMA cache_size=-64000;          -- 64MB cache
```

**Design Rationale**:
- **WAL Mode**: Allows concurrent reads while writing (critical for UI responsiveness)
- **Minimal Columns**: Only essential fields to keep size manageable
- **raw_json**: Enables replay/debugging without re-fetching data
- **Composite Index**: `(symbol, ts_ms)` optimizes time-window queries
- **No Deduplication**: Binance already sends snapshots; hash-based dedup unnecessary

#### 2.2.2 SQLite Store

**File**: `sqlite_store.py` (≤600 LOC)

**Responsibilities**:
- Initialize database schema
- Batch insert events (queue → flush every 50-200 events or 5s timeout)
- Query events for time windows (2h/8h/2d)
- Retention policy (delete events >14 days)
- Housekeeping (VACUUM, ANALYZE)

**Key Classes**:
```python
class SQLiteStore:
    """Persistent storage for liquidation events."""

    def __init__(self, db_path: str, batch_size: int = 100,
                 flush_interval: float = 5.0):
        """Initialize store with batching parameters."""
        self._queue: asyncio.Queue[LiquidationEvent] = asyncio.Queue()
        self._batch_size = batch_size
        self._flush_interval = flush_interval

    async def start(self) -> None:
        """Start background batch writer task."""

    async def enqueue(self, event: LiquidationEvent) -> None:
        """Add event to write queue (non-blocking)."""

    async def _batch_writer(self) -> None:
        """Background task: consume queue, batch insert."""

    async def query_window(self, symbol: str, start_ts: int,
                          end_ts: int) -> list[LiquidationEvent]:
        """Query events in time window [start_ts, end_ts)."""

    async def cleanup_old_events(self, retention_days: int = 14) -> int:
        """Delete events older than retention_days, return count."""

    async def get_stats(self) -> dict:
        """Return DB stats (row count, size, oldest/newest event)."""
```

**Batching Strategy**:
- **Queue-Based**: Non-blocking enqueue, background flush
- **Dual Trigger**: Flush when batch_size reached OR flush_interval elapsed
- **Error Handling**: Log failed inserts, continue processing (don't block ingestion)
- **Backpressure**: If queue grows >10k events, start dropping oldest events with warning

**Retention Policy**:
- **Default**: 14 days (configurable via settings)
- **Schedule**: Daily cleanup at 3 AM local time
- **VACUUM**: Monthly to reclaim disk space (runs during low-activity hours)

---

### 2.3 Aggregation Layer

**Location**: `Heatmap/aggregation/`

#### 2.3.1 Grid Builder

**File**: `grid_builder.py` (≤600 LOC)

**Responsibilities**:
- Calculate grid resolution (rows/cols) from window dimensions
- Bin events into (time_bin, price_bin) cells
- Accumulate intensity (notional value) per cell
- Support auto-resolution based on chart dimensions
- Handle TickSize rounding for price bins

**Key Classes**:
```python
@dataclass
class GridConfig:
    """Configuration for heatmap grid generation."""
    price_low: float           # Lower price bound (from chart)
    price_high: float          # Upper price bound (from chart)
    time_start: int            # Start timestamp (ms)
    time_end: int              # End timestamp (ms)
    tick_size: float           # From exchange info
    chart_width_px: int        # Chart width in pixels
    chart_height_px: int       # Chart height in pixels
    target_px_per_cell: float = 2.3  # Target cell density

    def calculate_rows(self) -> int:
        """Calculate number of price bins (rows)."""
        rows = int(self.chart_height_px / self.target_px_per_cell)
        return max(180, min(rows, 380))  # Clamp to sensible range

    def calculate_cols(self) -> int:
        """Calculate number of time bins (columns)."""
        cols = int(self.chart_width_px / 1.15)
        return max(800, min(cols, 1700))

    def price_bin_size(self) -> float:
        """Calculate price bin size, rounded to tickSize."""
        range_price = self.price_high - self.price_low
        raw_bin = range_price / self.calculate_rows()
        # Round up to nearest tick_size multiple
        return ceil(raw_bin / self.tick_size) * self.tick_size

    def time_bin_size(self) -> int:
        """Calculate time bin size in seconds."""
        window_seconds = (self.time_end - self.time_start) / 1000
        raw_bin = window_seconds / self.calculate_cols()
        # Round to standard intervals: 5, 10, 15, 30, 60, 120, 180s
        for interval in [5, 10, 15, 30, 60, 120, 180, 300, 600]:
            if raw_bin <= interval:
                return interval
        return 600  # Max 10min bins

@dataclass
class HeatmapCell:
    """Single cell in heatmap grid."""
    time_bin: int      # Time bin index (0 to cols-1)
    price_bin: int     # Price bin index (0 to rows-1)
    intensity: float   # Accumulated notional value
    count: int         # Number of liquidation events in this cell
    side: str          # "BUY", "SELL", or "MIXED"

class GridBuilder:
    """Build heatmap grid from liquidation events."""

    def build_grid(self, events: list[LiquidationEvent],
                   config: GridConfig) -> list[HeatmapCell]:
        """Build grid from events using config."""
        # 1. Initialize empty grid (numpy array for speed)
        # 2. For each event:
        #    - Calculate time_bin index
        #    - Calculate price_bin index
        #    - Accumulate intensity (notional)
        #    - Track side (BUY/SELL/MIXED)
        # 3. Filter out zero-intensity cells
        # 4. Return list of HeatmapCell objects

    def add_event_incremental(self, event: LiquidationEvent,
                             config: GridConfig,
                             existing_grid: dict) -> HeatmapCell | None:
        """Add single event to existing grid, return updated cell."""
        # Used for live updates after initial grid build
```

**Grid Resolution Algorithm**:
```python
# Auto-resolution calculation
chart_width = 1060   # px (start window)
chart_height = 550   # px
window = 2h          # 7200 seconds

# Rows (price bins)
rows_target = clamp(round(chart_height / 2.3), 180, 380)
# => rows_target = 239

# Price bin size
price_range = 105000.0 - 95000.0  # $10,000
raw_bin = 10000 / 239 = 41.84
tick_size = 0.1  # from exchangeInfo
price_bin = ceil(41.84 / 0.1) * 0.1 = 41.9

# Cols (time bins)
cols_target = clamp(round(chart_width / 1.15), 800, 1700)
# => cols_target = 922

# Time bin size
raw_time_bin = 7200 / 922 = 7.8 seconds
time_bin = 10 seconds  # Round to standard interval
```

**Performance Optimization**:
- Use `numpy` arrays for grid storage (fast indexing)
- Pre-allocate arrays based on calculated dimensions
- Vectorized operations for batch processing
- Return only non-zero cells to minimize data transfer

#### 2.3.2 Normalization

**File**: `normalization.py` (≤600 LOC)

**Responsibilities**:
- Normalize intensity values to [0, 1] range
- Support multiple normalization methods (linear, sqrt, log)
- Handle outliers (percentile clipping)
- Scale for opacity mapping

**Key Functions**:
```python
class NormalizationMethod(Enum):
    """Normalization methods for heatmap intensity."""
    LINEAR = "linear"
    SQRT = "sqrt"
    LOG = "log"

class Normalizer:
    """Normalize heatmap intensity values."""

    def normalize(self, cells: list[HeatmapCell],
                  method: NormalizationMethod = NormalizationMethod.SQRT,
                  clip_percentile: float = 99.0) -> list[HeatmapCell]:
        """Normalize cell intensities to [0, 1]."""
        # 1. Extract intensity values
        # 2. Clip outliers at percentile (e.g., 99th)
        # 3. Apply normalization method:
        #    - LINEAR: (x - min) / (max - min)
        #    - SQRT: sqrt(x) normalized
        #    - LOG: log(x + 1) normalized
        # 4. Return cells with updated intensity

    def _linear_norm(self, values: np.ndarray) -> np.ndarray:
        """Min-max normalization."""

    def _sqrt_norm(self, values: np.ndarray) -> np.ndarray:
        """Square root normalization (emphasizes medium values)."""

    def _log_norm(self, values: np.ndarray) -> np.ndarray:
        """Logarithmic normalization (emphasizes small values)."""
```

**Normalization Comparison**:

| Method | Use Case | Effect on Display |
|--------|----------|-------------------|
| **Linear** | Raw data, even distribution | Large events dominate, small events invisible |
| **Sqrt** | Balanced view (recommended) | Medium events visible, large events prominent |
| **Log** | Many small events | All events visible, large events less dominant |

**Example Values**:
```
Raw intensity:      [10, 100, 1000, 10000, 100000]
Linear normalized:  [0.00, 0.00, 0.01, 0.10, 1.00]  # Only largest visible
Sqrt normalized:    [0.10, 0.32, 1.00, 3.16, 10.00] => [0.03, 0.10, 0.32, 1.00]
Log normalized:     [1.04, 2.00, 3.00, 4.00, 5.00]  => [0.00, 0.26, 0.51, 0.77, 1.00]
```

#### 2.3.3 Time Decay

**File**: `decay.py` (≤600 LOC)

**Responsibilities**:
- Apply exponential time decay to older events
- Configurable half-life (20m, 60m, 6h, or disabled)
- Update decay coefficients on grid rebuild

**Key Functions**:
```python
class DecayConfig(Enum):
    """Time decay configurations."""
    DISABLED = None
    FAST = 1200      # 20 minutes half-life
    MEDIUM = 3600    # 60 minutes half-life
    SLOW = 21600     # 6 hours half-life

class TimeDecay:
    """Apply time-based decay to heatmap intensity."""

    def apply_decay(self, cells: list[HeatmapCell],
                    config: GridConfig,
                    decay_config: DecayConfig) -> list[HeatmapCell]:
        """Apply exponential decay based on event age."""
        # decay_factor = 0.5 ^ (age_seconds / half_life_seconds)
        # intensity_decayed = intensity * decay_factor

    def _calculate_decay_factor(self, event_ts: int, current_ts: int,
                               half_life: int) -> float:
        """Calculate decay factor for event."""
        age_seconds = (current_ts - event_ts) / 1000
        return 0.5 ** (age_seconds / half_life)
```

**Decay Visualization**:
```
Half-life = 60 minutes
Age (min)   Decay Factor   Effective Intensity
0           1.00           100%
30          0.71           71%
60          0.50           50%
120         0.25           25%
180         0.13           13%
```

---

### 2.4 UI Bridge Layer

**Location**: `Heatmap/ui/`

#### 2.4.1 Python-JavaScript Bridge

**File**: `bridge.py` (≤600 LOC)

**Responsibilities**:
- Expose Python API to JavaScript via QWebChannel
- Serialize grid data to JSON for JS consumption
- Handle async data loading without UI freezing
- Implement rate-limited live updates (250-1000ms)
- Coordinate with existing ChartBridge

**Key Classes**:
```python
class HeatmapBridge(QObject):
    """QWebChannel bridge for heatmap communication."""

    # Signals (Python → JavaScript)
    heatmapDataReady = pyqtSignal(str)      # Full grid data (JSON)
    heatmapDeltaReady = pyqtSignal(str)     # Incremental update (JSON)
    heatmapStatusChanged = pyqtSignal(str)  # Status messages
    heatmapError = pyqtSignal(str)          # Error messages

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._last_update_time = 0.0
        self._update_interval = 0.5  # 500ms rate limit
        self._pending_deltas: list[HeatmapCell] = []

    @pyqtSlot(str, str, int, int, int, int)
    def loadHeatmap(self, symbol: str, window: str,
                   chart_width: int, chart_height: int,
                   price_low: float, price_high: float) -> None:
        """Load heatmap for time window (called from JS).

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            window: Time window ("2h", "8h", "2d")
            chart_width: Chart width in pixels
            chart_height: Chart height in pixels
            price_low: Lower price bound
            price_high: Upper price bound
        """
        # 1. Query DB for events in window
        # 2. Build grid with GridBuilder
        # 3. Apply normalization and decay
        # 4. Serialize to JSON
        # 5. Emit heatmapDataReady signal

    def _add_live_event(self, event: LiquidationEvent) -> None:
        """Add live event to pending deltas (internal call)."""
        # 1. Convert event to grid cell
        # 2. Add to pending_deltas
        # 3. If rate limit elapsed, flush deltas to JS

    def _flush_deltas(self) -> None:
        """Flush pending deltas to JavaScript."""
        if not self._pending_deltas:
            return
        # 1. Serialize pending_deltas to JSON
        # 2. Emit heatmapDeltaReady signal
        # 3. Clear pending_deltas
        # 4. Update last_update_time

    @pyqtSlot()
    def clearHeatmap(self) -> None:
        """Clear heatmap from chart (called from JS)."""
        # Remove heatmap series from chart
```

**JSON Data Format**:
```json
{
  "symbol": "BTCUSDT",
  "window": "2h",
  "grid": {
    "rows": 239,
    "cols": 922,
    "price_low": 95000.0,
    "price_high": 105000.0,
    "time_start": 1736789400000,
    "time_end": 1736796600000,
    "price_bin_size": 41.9,
    "time_bin_size": 10
  },
  "cells": [
    {
      "time_bin": 0,
      "price_bin": 120,
      "intensity": 0.75,
      "count": 5,
      "side": "BUY"
    },
    // ... more cells (only non-zero intensity)
  ]
}
```

**Delta Update Format** (incremental):
```json
{
  "deltas": [
    {"time_bin": 920, "price_bin": 130, "intensity": 0.15, "count": 1, "side": "SELL"},
    {"time_bin": 921, "price_bin": 115, "intensity": 0.89, "count": 3, "side": "BUY"}
  ]
}
```

#### 2.4.2 JavaScript Heatmap Series

**File**: `js/heatmap_series.js`

**Responsibilities**:
- Custom series implementation for Lightweight Charts
- Render heatmap as background layer (behind candlesticks)
- Handle opacity and palette rendering
- Efficient delta updates (append without full rebuild)

**Key Implementation**:
```javascript
// Based on Lightweight Charts custom series plugin pattern
class HeatmapSeries {
  constructor(options) {
    this.options = {
      opacity: 0.5,
      palette: 'fire',  // 'fire', 'blue-red', 'mono'
      ...options
    };
    this._data = [];
    this._grid = null;
  }

  // Called by chart to render heatmap
  renderer() {
    return new HeatmapRenderer(this._data, this._grid, this.options);
  }

  // Set full heatmap data
  setData(heatmapData) {
    this._grid = heatmapData.grid;
    this._data = heatmapData.cells;
    this._invalidate();  // Trigger chart redraw
  }

  // Append incremental updates
  appendDeltas(deltas) {
    deltas.forEach(delta => {
      // Find existing cell or add new
      const idx = this._findCell(delta.time_bin, delta.price_bin);
      if (idx >= 0) {
        this._data[idx] = delta;  // Update existing
      } else {
        this._data.push(delta);   // Add new
      }
    });
    this._invalidate();
  }

  clear() {
    this._data = [];
    this._grid = null;
    this._invalidate();
  }
}

// Renderer: draws cells on canvas
class HeatmapRenderer {
  constructor(data, grid, options) {
    this._data = data;
    this._grid = grid;
    this._options = options;
  }

  draw(target, priceConverter, timeConverter) {
    const ctx = target.context;

    this._data.forEach(cell => {
      // Convert bin indices to canvas coordinates
      const x = timeConverter(this._grid.time_start +
                              cell.time_bin * this._grid.time_bin_size * 1000);
      const y = priceConverter(this._grid.price_low +
                               cell.price_bin * this._grid.price_bin_size);
      const width = timeConverter(this._grid.time_bin_size * 1000) - x;
      const height = y - priceConverter(this._grid.price_bin_size);

      // Get color from palette based on intensity
      const color = this._getColor(cell.intensity, cell.side);
      ctx.fillStyle = color;
      ctx.globalAlpha = this._options.opacity;
      ctx.fillRect(x, y, width, height);
    });

    ctx.globalAlpha = 1.0;  // Reset alpha
  }

  _getColor(intensity, side) {
    // Map intensity [0, 1] to color from palette
    // Different palettes for BUY (green/blue) vs SELL (red/orange)
  }
}

// Register series with Lightweight Charts
chart.addCustomSeries(new HeatmapSeries({
  opacity: 0.5,
  palette: 'fire'
}));
```

**Layer Ordering** (critical for background rendering):
```javascript
// 1. Create heatmap series FIRST (renders behind)
const heatmapSeries = chart.addCustomSeries(new HeatmapSeries(...));

// 2. Then create candlestick series (renders in front)
const candleSeries = chart.addCandlestickSeries({...});
```

#### 2.4.3 Color Palettes

**File**: `js/heatmap_palette.js`

**Palettes**:
```javascript
const PALETTES = {
  fire: {
    buy: [
      { stop: 0.0, color: 'rgba(0, 0, 0, 0)' },      // Transparent
      { stop: 0.2, color: 'rgba(0, 255, 0, 0.2)' },  // Dark green
      { stop: 0.5, color: 'rgba(0, 255, 0, 0.5)' },  // Green
      { stop: 0.8, color: 'rgba(0, 255, 0, 0.8)' },  // Bright green
      { stop: 1.0, color: 'rgba(0, 255, 0, 1.0)' }   // Full green
    ],
    sell: [
      { stop: 0.0, color: 'rgba(0, 0, 0, 0)' },      // Transparent
      { stop: 0.2, color: 'rgba(255, 0, 0, 0.2)' },  // Dark red
      { stop: 0.5, color: 'rgba(255, 100, 0, 0.5)' },// Orange
      { stop: 0.8, color: 'rgba(255, 50, 0, 0.8)' }, // Bright orange
      { stop: 1.0, color: 'rgba(255, 0, 0, 1.0)' }   // Full red
    ]
  },
  blueRed: {
    // Cool blue (buy) to hot red (sell)
  },
  mono: {
    // Single color (white) with varying alpha
  }
};
```

---

### 2.5 Settings Management

**Location**: `Heatmap/heatmap_settings.py` (≤600 LOC)

**Responsibilities**:
- Define settings data model with validation
- Provide default values
- Persist to QSettings
- Emit change events for live updates

**Settings Model**:
```python
from pydantic import BaseModel, Field, field_validator

class HeatmapSettings(BaseModel):
    """Heatmap configuration settings."""

    # Feature toggle
    enabled: bool = False

    # Data source
    source: str = "BINANCE_USDM"
    symbol: str = "BTCUSDT"

    # Time window
    window: str = Field(default="2h", pattern="^(2h|8h|2d)$")

    # Visual settings
    opacity: float = Field(default=0.5, ge=0.0, le=1.0)
    palette: str = Field(default="fire", pattern="^(fire|blueRed|mono)$")

    # Aggregation settings
    normalization: str = Field(default="sqrt", pattern="^(linear|sqrt|log)$")
    decay: str | None = Field(default="60m", pattern="^(20m|60m|6h)?$")

    # Resolution
    auto_resolution: bool = True
    manual_rows: int | None = Field(default=None, ge=50, le=1000)
    manual_cols: int | None = Field(default=None, ge=100, le=5000)

    # Storage
    retention_days: int = Field(default=14, ge=1, le=90)

    @field_validator('window')
    @classmethod
    def validate_window(cls, v: str) -> str:
        if v not in ['2h', '8h', '2d']:
            raise ValueError("Window must be 2h, 8h, or 2d")
        return v

class HeatmapSettingsManager:
    """Manage heatmap settings persistence."""

    def __init__(self, qsettings: QSettings):
        self._qsettings = qsettings
        self._settings = self.load()

    def load(self) -> HeatmapSettings:
        """Load settings from QSettings."""
        return HeatmapSettings(
            enabled=self._qsettings.value("heatmap/enabled", False, type=bool),
            opacity=self._qsettings.value("heatmap/opacity", 0.5, type=float),
            # ... load all settings
        )

    def save(self, settings: HeatmapSettings) -> None:
        """Save settings to QSettings."""
        self._qsettings.setValue("heatmap/enabled", settings.enabled)
        self._qsettings.setValue("heatmap/opacity", settings.opacity)
        # ... save all settings
        self._settings = settings

    def get(self) -> HeatmapSettings:
        """Get current settings."""
        return self._settings
```

**Settings UI Integration**:
- Add new tab "Heatmap" to `SettingsDialog` (extend `settings_tabs_mixin.py`)
- UI controls map directly to `HeatmapSettings` fields
- Live preview: Changes applied immediately via bridge signals

---

### 2.6 Orchestration Layer

**Location**: `Heatmap/heatmap_service.py` (≤600 LOC)

**Responsibilities**:
- Coordinate all components (ingestion, storage, aggregation, UI)
- Manage component lifecycle (start/stop/status)
- Handle errors and reconnections
- Provide status API for monitoring

**Key Classes**:
```python
class HeatmapServiceStatus(Enum):
    """Service status states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class HeatmapService:
    """Main orchestrator for heatmap feature."""

    def __init__(self, settings_manager: HeatmapSettingsManager,
                 bridge: HeatmapBridge):
        self._settings_manager = settings_manager
        self._bridge = bridge
        self._status = HeatmapServiceStatus.STOPPED

        # Components
        self._ws_client: BinanceForceOrderClient | None = None
        self._store: SQLiteStore | None = None
        self._exchange_info: ExchangeInfoCache | None = None

        # Background tasks
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start all components (called at app startup)."""
        if self._status == HeatmapServiceStatus.RUNNING:
            return

        self._status = HeatmapServiceStatus.STARTING
        logger.info("Starting heatmap service...")

        try:
            # 1. Initialize SQLite store
            self._store = SQLiteStore(
                db_path="data/liquidation_heatmap.db",
                batch_size=100,
                flush_interval=5.0
            )
            await self._store.start()

            # 2. Initialize exchange info cache
            self._exchange_info = ExchangeInfoCache()
            await self._exchange_info.refresh()

            # 3. Connect WebSocket client
            self._ws_client = BinanceForceOrderClient(
                symbol="BTCUSDT",
                on_event=self._handle_liquidation_event
            )
            self._tasks.append(asyncio.create_task(
                self._ws_client.connect()
            ))

            # 4. Start retention cleanup task
            self._tasks.append(asyncio.create_task(
                self._retention_cleanup_loop()
            ))

            self._status = HeatmapServiceStatus.RUNNING
            logger.info("Heatmap service started successfully")

        except Exception as e:
            self._status = HeatmapServiceStatus.ERROR
            logger.error(f"Failed to start heatmap service: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop all components (called at app shutdown)."""
        if self._status == HeatmapServiceStatus.STOPPED:
            return

        self._status = HeatmapServiceStatus.STOPPING
        logger.info("Stopping heatmap service...")

        # Cancel all background tasks
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Shutdown components
        if self._ws_client:
            await self._ws_client.shutdown()
        if self._store:
            await self._store.shutdown()

        self._status = HeatmapServiceStatus.STOPPED
        logger.info("Heatmap service stopped")

    def _handle_liquidation_event(self, event: LiquidationEvent) -> None:
        """Handle incoming liquidation event (callback from WS client)."""
        # 1. Enqueue to SQLite store (non-blocking)
        asyncio.create_task(self._store.enqueue(event))

        # 2. If heatmap is enabled, forward to bridge for live update
        if self._settings_manager.get().enabled:
            self._bridge._add_live_event(event)

    async def _retention_cleanup_loop(self) -> None:
        """Background task: daily cleanup of old events."""
        while True:
            await asyncio.sleep(86400)  # 24 hours
            try:
                retention_days = self._settings_manager.get().retention_days
                deleted = await self._store.cleanup_old_events(retention_days)
                logger.info(f"Retention cleanup: deleted {deleted} events")
            except Exception as e:
                logger.error(f"Retention cleanup failed: {e}")

    def get_status(self) -> dict:
        """Get service status for monitoring."""
        return {
            "status": self._status.value,
            "ws_connected": self._ws_client.is_connected if self._ws_client else False,
            "db_stats": self._store.get_stats() if self._store else {},
            "settings": self._settings_manager.get().model_dump()
        }
```

---

## 3. Data Flow Architecture

### 3.1 Startup Flow (Background Service)

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Startup                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ HeatmapService.start()│
            └──────────┬───────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌───────────────┐
   │ SQLite  │  │Exchange  │  │ WebSocket     │
   │ Store   │  │ Info     │  │ Client        │
   │ Init    │  │ Cache    │  │ Connect       │
   └────┬────┘  └────┬─────┘  └───────┬───────┘
        │            │                 │
        │            │                 ▼
        │            │        ┌─────────────────┐
        │            │        │ Connected to    │
        │            │        │ Binance Stream  │
        │            │        │ (btcusdt@       │
        │            │        │  forceOrder)    │
        │            │        └────────┬────────┘
        │            │                 │
        │            │                 ▼
        │            │        ┌─────────────────┐
        │            │        │ Events Start    │
        │            │        │ Flowing         │
        │            │        └────────┬────────┘
        │            │                 │
        └────────────┴─────────────────┘
                     │
                     ▼
           ┌──────────────────┐
           │ Service Running  │
           │ (Heatmap OFF)    │
           │ - WS: Receiving  │
           │ - DB: Writing    │
           │ - UI: Hidden     │
           └──────────────────┘
```

### 3.2 Heatmap Enable Flow (User Toggles ON)

```
┌────────────────────────────────────────────────────────────┐
│            User Toggles Heatmap ON in Settings              │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │ Settings Updated      │
           │ - enabled = True      │
           │ - window = "2h"       │
           │ - opacity = 0.5       │
           └──────────┬────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │ HeatmapBridge.loadHeatmap()│
         │ - symbol = "BTCUSDT"       │
         │ - window = "2h"            │
         │ - chart dimensions         │
         │ - price_low/high           │
         └──────────┬─────────────────┘
                    │
      ┌─────────────┴──────────────┐
      │                            │
      ▼                            ▼
┌──────────────┐          ┌────────────────┐
│ Query SQLite │          │ Get TickSize   │
│ for 2h window│          │ from Cache     │
└──────┬───────┘          └────────┬───────┘
       │                           │
       └───────────┬───────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ GridBuilder     │
          │ - Calculate     │
          │   rows/cols     │
          │ - Bin events    │
          │ - Accumulate    │
          │   intensity     │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Normalizer      │
          │ - Apply sqrt    │
          │ - Clip outliers │
          │ - Scale [0, 1]  │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ TimeDecay       │
          │ - Apply 60m     │
          │   decay         │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Serialize to    │
          │ JSON            │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────────┐
          │ Emit Signal:        │
          │ heatmapDataReady    │
          └────────┬────────────┘
                   │
                   ▼
          ┌─────────────────────┐
          │ JavaScript Receives │
          │ - Parse JSON        │
          │ - Create cells      │
          │ - Render on canvas  │
          └────────┬────────────┘
                   │
                   ▼
          ┌─────────────────────┐
          │ Heatmap Visible     │
          │ (Background Layer)  │
          │ - Candles in front  │
          │ - Live updates ON   │
          └─────────────────────┘
```

### 3.3 Live Update Flow (Event Arrives)

```
┌────────────────────────────────────────────────────────────┐
│     Binance WebSocket: New Liquidation Event Arrives        │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │ BinanceForceOrderClient│
           │ - Parse JSON          │
           │ - Validate fields     │
           │ - Create Event object │
           └──────────┬────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │ HeatmapService._handle_     │
        │ liquidation_event()         │
        └──────────┬──────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
┌─────────────────┐   ┌──────────────────┐
│ SQLiteStore     │   │ HeatmapBridge    │
│ - Enqueue event │   │ - Check enabled  │
│ - Batched write │   │ - Add to pending │
│   (100 events   │   │   deltas         │
│    or 5s)       │   └────────┬─────────┘
└─────────────────┘            │
                               ▼
                    ┌──────────────────────┐
                    │ Rate Limit Check     │
                    │ (500ms since last)   │
                    └──────────┬───────────┘
                               │
                               ▼ (if elapsed)
                    ┌──────────────────────┐
                    │ Flush Pending Deltas │
                    │ - Serialize to JSON  │
                    │ - Emit signal:       │
                    │   heatmapDeltaReady  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ JavaScript Receives  │
                    │ - Parse delta JSON   │
                    │ - Update affected    │
                    │   cells              │
                    │ - Redraw canvas      │
                    └──────────────────────┘
```

### 3.4 Heatmap Disable Flow (User Toggles OFF)

```
┌────────────────────────────────────────────────────────────┐
│            User Toggles Heatmap OFF in Settings             │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │ Settings Updated      │
           │ - enabled = False     │
           └──────────┬────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │ HeatmapBridge.clearHeatmap()│
         └──────────┬─────────────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │ JavaScript:         │
          │ - Remove heatmap    │
          │   series from chart │
          │ - Clear data arrays │
          └─────────────────────┘

IMPORTANT: WebSocket and SQLite continue running!
           Only rendering is disabled.
```

---

## 4. Integration Points

### 4.1 PyQt6 Application Integration

**File**: `src/ui/widgets/embedded_tradingview_chart.py`

**Changes Required** (all in existing mixin pattern):

1. **Add Heatmap Mixin** (new file: `chart_mixins/heatmap_mixin.py`):
```python
class HeatmapMixin:
    """Mixin for heatmap functionality in chart widget."""

    def _init_heatmap(self):
        """Initialize heatmap components (called in __init__)."""
        self._heatmap_bridge = HeatmapBridge(self)
        self._heatmap_service = None  # Set by main app

        # Register bridge with QWebChannel
        if hasattr(self, 'channel'):
            self.channel.registerObject("heatmapBridge", self._heatmap_bridge)

    def set_heatmap_service(self, service: HeatmapService):
        """Set heatmap service reference (called after chart init)."""
        self._heatmap_service = service

    def reload_heatmap(self):
        """Reload heatmap with current chart state."""
        if not self._heatmap_service:
            return

        settings = self._heatmap_service.get_settings()
        if not settings.enabled:
            return

        # Get current chart bounds
        visible_range = self._get_visible_price_range()
        chart_size = self.size()

        # Trigger load via bridge
        self._heatmap_bridge.loadHeatmap(
            symbol=settings.symbol,
            window=settings.window,
            chart_width=chart_size.width(),
            chart_height=chart_size.height(),
            price_low=visible_range['low'],
            price_high=visible_range['high']
        )
```

2. **Update Chart Mixin Chain**:
```python
class EmbeddedTradingViewChart(
    HeatmapMixin,         # NEW: Add heatmap support
    EntryAnalyzerMixin,
    ChartAIMarkingsMixin,
    # ... existing mixins
    QWidget,
):
    def __init__(self, history_manager=None):
        super().__init__()
        # ... existing init
        self._init_heatmap()  # NEW: Initialize heatmap
```

3. **Update HTML Template** (`chart_js_template.py`):
```python
def get_chart_html_template() -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script src="https://unpkg.com/lightweight-charts@4.0.0/dist/lightweight-charts.standalone.production.js"></script>
        <script>
            // ... existing code

            // NEW: Heatmap integration
            let heatmapSeries = null;

            new QWebChannel(qt.webChannelTransport, function(channel) {{
                window.chartBridge = channel.objects.chartBridge;
                window.heatmapBridge = channel.objects.heatmapBridge;  // NEW

                // Listen for heatmap data
                heatmapBridge.heatmapDataReady.connect(function(jsonData) {{
                    const data = JSON.parse(jsonData);

                    // Create heatmap series if not exists
                    if (!heatmapSeries) {{
                        heatmapSeries = chart.addCustomSeries(new HeatmapSeries({{
                            opacity: data.opacity,
                            palette: data.palette
                        }}));
                    }}

                    heatmapSeries.setData(data);
                }});

                // Listen for delta updates
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

### 4.2 Settings Dialog Integration

**File**: `src/ui/dialogs/settings_tabs_mixin.py`

**Add New Method**:
```python
def _create_heatmap_tab(self) -> QWidget:
    """Create heatmap settings tab."""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # Enable/Disable
    self.heatmap_enabled_cb = QCheckBox("Enable Liquidation Heatmap")
    layout.addWidget(self.heatmap_enabled_cb)

    # Data Source (read-only for now)
    source_layout = QHBoxLayout()
    source_layout.addWidget(QLabel("Data Source:"))
    self.heatmap_source_label = QLabel("Binance USD-M Futures (BTCUSDT)")
    source_layout.addWidget(self.heatmap_source_label)
    layout.addLayout(source_layout)

    # Time Window
    window_layout = QHBoxLayout()
    window_layout.addWidget(QLabel("Time Window:"))
    self.heatmap_window_combo = QComboBox()
    self.heatmap_window_combo.addItems(["2h", "8h", "2d"])
    window_layout.addWidget(self.heatmap_window_combo)
    layout.addLayout(window_layout)

    # Opacity
    opacity_layout = QHBoxLayout()
    opacity_layout.addWidget(QLabel("Opacity:"))
    self.heatmap_opacity_slider = QSlider(Qt.Orientation.Horizontal)
    self.heatmap_opacity_slider.setRange(0, 100)
    self.heatmap_opacity_slider.setValue(50)
    self.heatmap_opacity_label = QLabel("50%")
    self.heatmap_opacity_slider.valueChanged.connect(
        lambda v: self.heatmap_opacity_label.setText(f"{v}%")
    )
    opacity_layout.addWidget(self.heatmap_opacity_slider)
    opacity_layout.addWidget(self.heatmap_opacity_label)
    layout.addLayout(opacity_layout)

    # Palette
    palette_layout = QHBoxLayout()
    palette_layout.addWidget(QLabel("Color Palette:"))
    self.heatmap_palette_combo = QComboBox()
    self.heatmap_palette_combo.addItems(["Fire (Red/Green)", "Blue-Red", "Monochrome"])
    palette_layout.addWidget(self.heatmap_palette_combo)
    layout.addLayout(palette_layout)

    # Normalization
    norm_layout = QHBoxLayout()
    norm_layout.addWidget(QLabel("Normalization:"))
    self.heatmap_norm_combo = QComboBox()
    self.heatmap_norm_combo.addItems(["Linear", "Square Root", "Logarithmic"])
    self.heatmap_norm_combo.setCurrentIndex(1)  # sqrt default
    norm_layout.addWidget(self.heatmap_norm_combo)
    layout.addLayout(norm_layout)

    # Time Decay
    decay_layout = QHBoxLayout()
    decay_layout.addWidget(QLabel("Time Decay:"))
    self.heatmap_decay_combo = QComboBox()
    self.heatmap_decay_combo.addItems(["Disabled", "Fast (20m)", "Medium (60m)", "Slow (6h)"])
    self.heatmap_decay_combo.setCurrentIndex(2)  # 60m default
    decay_layout.addWidget(self.heatmap_decay_combo)
    layout.addLayout(decay_layout)

    # Resolution
    resolution_group = QGroupBox("Grid Resolution")
    resolution_layout = QVBoxLayout()
    self.heatmap_auto_res_rb = QRadioButton("Auto (Based on Chart Size)")
    self.heatmap_auto_res_rb.setChecked(True)
    self.heatmap_manual_res_rb = QRadioButton("Manual")
    resolution_layout.addWidget(self.heatmap_auto_res_rb)
    resolution_layout.addWidget(self.heatmap_manual_res_rb)
    resolution_group.setLayout(resolution_layout)
    layout.addWidget(resolution_group)

    # Retention
    retention_layout = QHBoxLayout()
    retention_layout.addWidget(QLabel("Data Retention:"))
    self.heatmap_retention_spin = QSpinBox()
    self.heatmap_retention_spin.setRange(1, 90)
    self.heatmap_retention_spin.setValue(14)
    self.heatmap_retention_spin.setSuffix(" days")
    retention_layout.addWidget(self.heatmap_retention_spin)
    layout.addLayout(retention_layout)

    layout.addStretch()
    return widget
```

**Update tab creation**:
```python
def init_ui(self):
    # ... existing tabs
    tabs.addTab(self._create_heatmap_tab(), "Heatmap")  # NEW
```

### 4.3 Application Startup Integration

**File**: `main.py` (or equivalent app entry point)

```python
async def main():
    # ... existing app setup

    # Initialize heatmap service
    heatmap_settings = HeatmapSettingsManager(app.settings)
    heatmap_bridge = HeatmapBridge()
    heatmap_service = HeatmapService(heatmap_settings, heatmap_bridge)

    # Start background service (always on)
    await heatmap_service.start()

    # Connect to chart
    chart_widget.set_heatmap_service(heatmap_service)

    # ... existing app logic

    # On shutdown
    await heatmap_service.stop()
```

---

## 5. Performance Considerations

### 5.1 Database Performance

**Write Throughput**:
- Target: 1000 events/second peak load
- Batching: 100 events or 5s timeout
- SQLite WAL: Concurrent reads during writes
- Index optimization: Composite index on (symbol, ts_ms)

**Read Performance**:
- 2h window query: ~7200 events (1 event/second avg)
- Query time: <50ms with proper indexing
- Grid building: <100ms (numpy vectorization)

**Storage**:
- Event size: ~200 bytes per row
- 1 million events: ~200 MB
- 14-day retention: ~2 GB (assuming 100 events/sec avg)

### 5.2 Rendering Performance

**Grid Size**:
- Target: 2-3 pixels per cell
- 1060×550 chart: 239 rows × 922 cols = 220,358 cells (max)
- Non-zero cells: Typically 5-15% (11,000-33,000 cells)

**Canvas Drawing**:
- Lightweight Charts: Hardware-accelerated canvas
- Delta updates: Only redraw affected cells (via bounding box)
- Rate limiting: Max 2 updates/second (500ms)

**Memory Usage**:
- Grid in memory: ~2 MB (220k cells × 8 bytes)
- JS serialization: ~500 KB JSON payload
- Delta updates: ~5 KB per update

### 5.3 Network Performance

**WebSocket Bandwidth**:
- Event frequency: 1 event per 1000ms (snapshot)
- Average payload: 250 bytes
- Bandwidth: <1 KB/second

**Reconnection Impact**:
- Backoff prevents connection storms
- Max reconnect delay: 60 seconds
- No data loss: Events written to DB immediately

---

## 6. Error Handling & Resilience

### 6.1 WebSocket Failures

| Failure Type | Detection | Recovery | User Impact |
|--------------|-----------|----------|-------------|
| Connection timeout | No pong response (30s) | Auto-reconnect with backoff | Brief gap in live data |
| Network loss | Socket error | Immediate reconnect attempt | Brief gap in live data |
| Server disconnection | Close frame | Auto-reconnect | Brief gap in live data |
| Invalid message | JSON parse error | Log and skip | Single event lost |
| 24h timeout | Timer expiry | Preemptive reconnect | Seamless (no gap) |

### 6.2 Database Failures

| Failure Type | Detection | Recovery | User Impact |
|--------------|-----------|----------|-------------|
| Disk full | SQLITE_FULL error | Log critical error, pause writes | No live updates |
| Corruption | SQLITE_CORRUPT error | Attempt repair, else recreate | Historical data loss |
| Lock timeout | SQLITE_BUSY error | Retry with backoff (max 3) | Delayed writes |
| Query timeout | Long-running query | Cancel and log | Heatmap load failure |

### 6.3 UI Failures

| Failure Type | Detection | Recovery | User Impact |
|--------------|-----------|----------|-------------|
| Bridge disconnect | Signal not received | Reload page | Heatmap disappears |
| JS exception | Console error | Show error message | Heatmap not rendered |
| OOM (JavaScript) | Heap limit | Reduce grid resolution | Lower quality heatmap |
| Canvas overflow | Draw error | Skip problematic cells | Partial rendering |

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Ingestion Layer** (`test_ws_parse.py`):
- Parse valid forceOrder payloads
- Handle malformed JSON
- Validate event fields

**Storage Layer** (`test_sqlite_store.py`):
- Insert events
- Query time windows
- Retention cleanup
- Batch flush timing

**Aggregation Layer** (`test_grid_builder.py`):
- Grid dimension calculations
- Event binning accuracy
- Normalization algorithms
- Decay calculations

### 7.2 Integration Tests

**End-to-End Flow**:
1. Mock WebSocket connection
2. Inject test events
3. Verify SQLite writes
4. Query and build grid
5. Verify JSON output format

**UI Integration**:
1. Toggle heatmap ON/OFF
2. Change settings (opacity, palette)
3. Resize chart window
4. Verify grid rebuilds

### 7.3 Performance Tests

**Load Test**:
- Simulate 1000 events/second for 1 hour
- Monitor DB write latency
- Check memory usage growth

**Stress Test**:
- Large time windows (2 days)
- High event density (5 events/second sustained)
- Verify UI responsiveness

---

## 8. Deployment Checklist

- [ ] All files under `Heatmap/` ≤600 LOC
- [ ] No new dependencies added (use existing libs)
- [ ] SQLite database created at `data/liquidation_heatmap.db`
- [ ] Service starts automatically with app
- [ ] Heatmap tab visible in Settings
- [ ] Toggle ON/OFF works without restart
- [ ] WebSocket reconnects automatically
- [ ] Retention policy runs daily
- [ ] Error logging configured
- [ ] Performance metrics logged

---

## 9. Future Enhancements (Out of Scope)

1. **Multi-Symbol Support**: Extend to ETH, BNB, etc.
2. **Order Book Integration**: Combine liquidations with order book depth
3. **Alert System**: Notify on large liquidations (>$1M)
4. **Historical Playback**: Replay past liquidation events
5. **Export Functionality**: Export heatmap data to CSV
6. **Advanced Analytics**: Liquidation cascades, correlation analysis
7. **Custom Palettes**: User-defined color schemes
8. **Volume Profile Overlay**: Combine liquidations with volume profile

---

## 10. Architecture Decision Records (ADRs)

### ADR-001: Why SQLite Instead of Time-Series DB?

**Status**: Accepted

**Context**: Need persistent storage for liquidation events with time-range queries.

**Decision**: Use SQLite with WAL mode.

**Rationale**:
- Already in use (`data/orderpilot.db`)
- Zero configuration
- Sufficient performance for 100 events/sec
- Cross-platform compatibility
- No additional dependencies

**Alternatives Considered**:
- InfluxDB: Overkill for single-symbol data
- PostgreSQL: Too heavy for market data
- Redis TimeSeries: Requires separate service

### ADR-002: Why Background Service Always Running?

**Status**: Accepted

**Context**: User may toggle heatmap ON at any time.

**Decision**: WebSocket and DB ingestion run continuously, independent of UI state.

**Rationale**:
- Instant heatmap activation (no wait for data collection)
- Historical data available for any window
- Resilient to UI crashes (data still collected)

**Trade-offs**:
- Minimal resource usage (~1 MB RAM, <1 KB/s network)
- Acceptable for feature value

### ADR-003: Why Rate-Limited Live Updates?

**Status**: Accepted

**Context**: Binance sends snapshots every 1000ms; excessive UI updates waste CPU.

**Decision**: Rate-limit delta updates to 500ms minimum interval.

**Rationale**:
- Human eye can't perceive <500ms changes
- Reduces canvas redraws (CPU savings)
- Batches multiple events per update

### ADR-004: Why TickSize Rounding?

**Status**: Accepted

**Context**: Grid price bins must align with exchange tick sizes.

**Decision**: Round price bin sizes to tickSize multiples.

**Rationale**:
- Prevents misalignment with price levels
- Ensures accurate price display
- Required by Binance trading rules

### ADR-005: Why Custom Series Instead of Overlay?

**Status**: Accepted

**Context**: Need heatmap as background layer behind candlesticks.

**Decision**: Use Lightweight Charts custom series plugin.

**Rationale**:
- Native support for background rendering
- Full control over drawing order
- Efficient canvas-based rendering
- Official TradingView example available

---

## Appendix A: File Checklist

| File Path | Max LOC | Description |
|-----------|---------|-------------|
| `Heatmap/README.md` | N/A | Project documentation |
| `Heatmap/__init__.py` | <50 | Package init |
| `Heatmap/heatmap_service.py` | 600 | Service orchestrator |
| `Heatmap/heatmap_settings.py` | 600 | Settings model |
| `Heatmap/ingestion/__init__.py` | <50 | Package init |
| `Heatmap/ingestion/binance_forceorder_ws.py` | 600 | WebSocket client |
| `Heatmap/ingestion/exchange_info.py` | 600 | TickSize cache |
| `Heatmap/storage/__init__.py` | <50 | Package init |
| `Heatmap/storage/sqlite_store.py` | 600 | SQLite persistence |
| `Heatmap/storage/schema.sql` | <100 | Database schema |
| `Heatmap/aggregation/__init__.py` | <50 | Package init |
| `Heatmap/aggregation/grid_builder.py` | 600 | Grid generation |
| `Heatmap/aggregation/normalization.py` | 600 | Intensity normalization |
| `Heatmap/aggregation/decay.py` | 600 | Time decay |
| `Heatmap/ui/__init__.py` | <50 | Package init |
| `Heatmap/ui/bridge.py` | 600 | Python-JS bridge |
| `Heatmap/ui/js/heatmap_series.js` | <800 | Custom series |
| `Heatmap/ui/js/heatmap_palette.js` | <300 | Color palettes |
| `Heatmap/tests/test_ws_parse.py` | <500 | WS tests |
| `Heatmap/tests/test_sqlite_store.py` | <500 | Storage tests |
| `Heatmap/tests/test_grid_builder.py` | <500 | Grid tests |

**Total New Files**: 21
**Total New LOC**: ~7,500 (estimated)

---

## Appendix B: Memory Architecture Patterns

Storing architecture patterns for future reference:

**Pattern 1: Always-On Background Service**
- Service lifecycle independent of UI state
- Enables instant feature activation
- Resilient to UI crashes

**Pattern 2: Queue-Based Batched Writes**
- Non-blocking enqueue
- Dual-trigger flush (size + time)
- Backpressure handling

**Pattern 3: Grid-Based Aggregation**
- Two-dimensional binning (time, price)
- Numpy for performance
- Sparse storage (only non-zero cells)

**Pattern 4: Rate-Limited Live Updates**
- Accumulate deltas in buffer
- Flush at fixed intervals
- Prevents UI thrashing

**Pattern 5: QWebChannel Bridge Pattern**
- Python signals → JavaScript slots
- JSON serialization for complex data
- Async loading without UI freeze

---

*End of Architecture Document*
