# Binance BTCUSDT Liquidation Heatmap

## Overview

Real-time liquidation heatmap overlay for BTCUSDT futures, rendering as a background layer in Lightweight Charts.

## Features

- **Continuous Ingestion**: WebSocket streams liquidations to SQLite 24/7
- **Historical Replay**: Load 2h/8h/2d windows from database on activation
- **Background Rendering**: Heatmap displays behind candlesticks
- **Auto Resolution**: Grid adapts to window size and price range
- **Multiple Normalizations**: Linear, sqrt, log scaling options

## Architecture

### Components

1. **Ingestion** (`ingestion/`)
   - `binance_forceorder_ws.py`: WebSocket client with auto-reconnect
   - `exchange_info.py`: TickSize fetching and caching

2. **Storage** (`storage/`)
   - `sqlite_store.py`: WAL-mode database with batched writes
   - `schema.sql`: Event table schema with indices

3. **Aggregation** (`aggregation/`)
   - `grid_builder.py`: Build heatmap grid from events
   - `normalization.py`: Intensity scaling functions

4. **UI Bridge** (`ui/`)
   - `bridge.py`: PyQt6 ↔ JavaScript communication
   - `js/heatmap_series.js`: Custom Lightweight Charts series

5. **Service** (root level)
   - `heatmap_service.py`: Orchestrates lifecycle
   - `heatmap_settings.py`: Configuration model

## Data Flow

```
Binance WS → Parser → SQLite (continuous)
                         ↓
           User toggles ON
                         ↓
         Query DB window → Build Grid
                         ↓
            Python → JS Bridge → Render
                         ↓
       Live events → Incremental updates
```

## Coding Standards

- **Max file size**: 600 lines per .py file
- **Logging**: Use standard logging module
- **Type hints**: All public functions
- **Tests**: Unit tests for core logic
- **Error handling**: Graceful degradation

## Important Notes

### Binance Snapshot Behavior

The `forceOrder` stream sends **snapshots** - only the last liquidation within 1000ms per symbol. This means:
- No message if no liquidation occurred in that window
- Multiple small liquidations may appear as one aggregated event
- Suitable for visualization, not tick-perfect accounting

### Connection Lifecycle

- Max connection lifetime: 24 hours
- Server sends periodic pings → client must pong
- Auto-reconnect before 24h mark with exponential backoff

### TickSize Changes

TickSize can change; always fetch from `/fapi/v1/exchangeInfo` and refresh periodically or on errors.

## Setup

All dependencies are already in `requirements.txt`:
- `websockets==15.0.1`
- `aiohttp==3.13.2`
- `PyQt6==6.10.0`
- `PyQt6-WebEngine>=6.7.0`
- `qasync==0.28.0`
- `numpy==2.2.6`
- `SQLAlchemy==2.0.44`

## Usage

```python
from Heatmap import HeatmapService, HeatmapSettings

# Initialize service
settings = HeatmapSettings(
    enabled=True,
    window="2h",
    opacity=0.5,
    normalization="sqrt"
)

service = HeatmapService(settings)
await service.start()

# Service runs in background, UI toggles rendering only
```

## Troubleshooting

### WebSocket keeps disconnecting
- Check network stability
- Verify Binance API is accessible
- Review reconnect backoff settings

### Heatmap not showing
- Ensure service is running (`service.is_running()`)
- Check if events are being stored (`SELECT COUNT(*) FROM liq_events`)
- Verify window range has data

### Performance issues
- Reduce grid resolution
- Increase update rate limit (e.g., 500ms → 1000ms)
- Enable time decay to reduce older cell intensity

## License

Part of OrderPilot-AI trading software.
