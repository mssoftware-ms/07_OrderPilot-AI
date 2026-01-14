# Heatmap Test Suite Documentation

## Overview

Comprehensive test suite for the Binance BTCUSDT Liquidation Heatmap feature. Tests cover WebSocket ingestion, SQLite storage, grid building, normalization, and end-to-end integration flows.

**Total Tests**: 100+ test cases
**Lines of Code**: 2,900+ lines
**Coverage Areas**: WS parsing, database ops, grid building, integration, error handling

## Test Files

### 1. `conftest.py` (367 lines)
Shared pytest fixtures and test data generators.

**Fixture Categories**:
- **Binance Payloads**: Sample and bulk forceOrder events
  - `sample_binance_forceorder_payload`: Standard SELL liquidation
  - `sample_binance_forceorder_buy`: BUY-side liquidation
  - `bulk_forceorder_payloads`: 100 realistic events with price drift
  - `malformed_payload_*`: Error cases (missing fields, invalid JSON)

- **Event Models**: Internal event representation
  - `sample_liq_event`: Single liquidation event
  - `bulk_liq_events`: 50 realistic events with vary sides/prices

- **Database**: Temporary DB and test data
  - `temp_db_path`: Temp SQLite database file
  - `exchange_info_response`: Binance API response with TickSize

- **Grid Parameters**: Window and resolution settings
  - `sample_window_params`: 2h window with auto resolution
  - `time_window_*`: 2h/8h/2d windows in milliseconds
  - `expected_grid_structure`: Expected output schema

- **Normalization**: Intensity matrices and settings
  - `raw_intensities`: 4x4 test matrix
  - `normalized_linear`: Expected linear normalization result
  - `settings_*`: Settings for different windows

**Usage**:
```python
def test_example(sample_liq_event, bulk_liq_events, temp_db_path):
    # Fixtures are automatically injected by pytest
    assert sample_liq_event["symbol"] == "BTCUSDT"
    assert len(bulk_liq_events) == 50
```

### 2. `test_ws_parse.py` (482 lines)
WebSocket payload parsing and connection handling.

**Test Classes**:

#### `TestWebSocketPayloadParsing`
- `test_parse_valid_forceorder_payload`: Verify event structure
- `test_parse_buy_side_liquidation`: Buy vs sell detection
- `test_extract_event_fields`: Field extraction to internal model
- `test_calculate_notional_value`: Price × qty calculation
- `test_timestamp_is_milliseconds`: Timestamp format validation
- `test_parse_malformed_json_raises_error`: Invalid JSON handling
- `test_parse_missing_required_fields`: Required field validation
- `test_parse_wrong_event_type`: Event type filtering
- `test_parse_zero_quantity`: Zero quantity rejection
- `test_parse_negative_price`: Negative price rejection
- `test_parse_invalid_side`: Side validation (BUY/SELL only)

#### `TestWebSocketReconnectLogic`
- `test_backoff_sequence`: Exponential backoff (1, 2, 4, 8, 16, 32, 60s)
- `test_backoff_with_jitter`: Jitter prevents thundering herd
- `test_backoff_caps_at_maximum`: Max 60s delay
- `test_reconnect_attempt_counter`: Attempt tracking
- `test_reconnect_reset_on_success`: Counter resets after success
- `test_max_reconnect_attempts_exceeded`: Gives up after 3 attempts

#### `TestWebSocketPingPong`
- `test_parse_ping_message`: Ping frame detection
- `test_send_pong_response`: Pong response on ping
- `test_ping_timeout_triggers_reconnect`: Timeout handling (60s)
- `test_periodic_ping_interval`: Ping every 30s
- `test_connection_lifetime_24h_limit`: Reconnect before 24h
- `test_24h_reconnect_within_margin`: 5% safety margin (23h)

#### `TestWebSocketConnectionLifecycle`
- `test_connection_establishment`: Can connect
- `test_connection_closure`: Can disconnect cleanly
- `test_receive_message_flow`: Message reception
- `test_send_message`: Message sending

#### `TestBulkPayloadProcessing`
- `test_process_bulk_payloads`: Process 100 events
- `test_parse_bulk_extract_events`: Bulk extraction
- `test_bulk_payload_with_errors`: Error handling in batch

### 3. `test_sqlite_store.py` (679 lines)
Database schema, operations, retention, and performance.

**Test Classes**:

#### `TestSQLiteSchemaInitialization`
- `test_schema_table_creation`: Table exists
- `test_schema_column_definitions`: All columns with correct types
- `test_schema_index_creation`: Two indexes created
- `test_wal_mode_enabled`: WAL mode active
- `test_synchronous_pragma_normal`: `PRAGMA synchronous=NORMAL`
- `test_temp_store_memory`: Temp storage uses memory

**Schema Details**:
```sql
CREATE TABLE liq_events (
    id INTEGER PRIMARY KEY,
    ts_ms INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    price REAL NOT NULL,
    qty REAL NOT NULL,
    notional REAL NOT NULL,
    source TEXT NOT NULL,
    raw_json TEXT NOT NULL
)
-- Indexes:
CREATE INDEX idx_liq_events_symbol_ts ON liq_events(symbol, ts_ms)
CREATE INDEX idx_liq_events_ts ON liq_events(ts_ms)
```

#### `TestSQLiteInsertOperations`
- `test_insert_single_event`: Insert one event
- `test_insert_batch`: Batch insert 50 events
- `test_insert_preserves_order`: Timestamps are sorted

#### `TestSQLiteQueryOperations`
- `test_query_by_time_window`: Query 2h window
- `test_query_by_symbol`: Query BTCUSDT only
- `test_query_aggregation`: COUNT, SUM, AVG

#### `TestSQLiteRetentionPolicy`
- `test_delete_old_records`: Delete >14 day old events
- `test_vacuum_database`: VACUUM reclaims space
- `test_retention_configurable`: Support 7/14/30/60 day options

#### `TestSQLitePerformance`
- `test_batch_insert_performance`: Batch > individual
- `test_indexed_query_performance`: Indexes work

### 4. `test_grid_builder.py` (654 lines)
Grid construction, price/time mapping, normalization, and resolution.

**Test Classes**:

#### `TestGridBuilding`
- `test_grid_initialization`: Create empty grid
- `test_grid_accumulate_single_event`: Place one event
- `test_grid_accumulate_bulk_events`: Place 50 events
- `test_grid_clear`: Clear grid to zeros

#### `TestPriceToRowMapping`
- `test_price_to_row_basic`: Mid-range price → mid row
- `test_price_to_row_boundary_low`: Low price → row 0
- `test_price_to_row_boundary_high`: High price → row max
- `test_price_to_row_with_tick_size`: TickSize rounding
- `test_price_clamped_below_range`: OOB low clamped
- `test_price_clamped_above_range`: OOB high clamped
- `test_price_row_uniqueness`: Different prices → different rows
- `test_tick_size_bin_rounding`: Bins respect TickSize

#### `TestTimeToColumnMapping`
- `test_time_to_col_basic`: Mid-window time → mid column
- `test_time_to_col_start`: Start time → column 0
- `test_time_to_col_end`: End time → column max
- `test_time_clamped_before_window`: Before window clamped
- `test_time_clamped_after_window`: After window clamped
- `test_time_to_col_multiple_windows`: Across 2h/8h/2d

#### `TestNormalization`
- `test_linear_normalization`: 0-1 range, max=1
- `test_sqrt_normalization`: Square root scaling
- `test_log_normalization`: Logarithmic scaling
- `test_normalization_preserves_zero`: Zeros stay zero
- `test_normalization_with_empty_grid`: All-zero handling
- `test_normalization_clipping`: Clip to [0, 1]

#### `TestAutoResolution`
- `test_auto_rows_from_height`: Height → rows (100-400)
- `test_auto_cols_from_width`: Width → cols (600-1700)
- `test_auto_time_bin_from_window`: Window → time bin
- `test_auto_price_bin_with_tick_size`: Bin respects TickSize
- `test_resolution_scaling_to_window`: Wider/taller → more cells

#### `TestEdgeCases`
- `test_empty_event_list`: No events → all zeros
- `test_single_event`: One event → one cell populated
- `test_all_events_same_price`: All same price, different times
- `test_all_events_same_time`: All same time, different prices
- `test_outlier_price_clamped`: Extreme prices clamped
- `test_very_small_notional`: Small values preserved
- `test_very_large_notional`: Large values don't overflow

#### `TestGridIntegration`
- `test_build_grid_from_bulk_events`: Full pipeline
- `test_grid_with_normalization_pipeline`: Build → normalize → scale

### 5. `test_integration.py` (693 lines)
End-to-end flows, toggles, window switching, and error handling.

**Test Classes**:

#### `TestEndToEndHeatmapFlow`
- `test_ws_to_db_to_grid_flow`: Parse → Store → Build
- `test_data_persistence_after_reconnect`: Data survives reconnect

#### `TestHeatmapToggle`
- `test_toggle_on_loads_db_data`: ON loads from DB
- `test_toggle_off_hides_rendering`: OFF removes UI series
- `test_toggle_off_preserves_db_stream`: DB continues when OFF
- `test_toggle_on_after_off_uses_new_data`: ON after OFF uses latest

#### `TestWindowSwitching`
- `test_switch_window_2h_to_8h`: 8h ⊇ 2h
- `test_window_2h_resolution`: ~8s time bins
- `test_window_8h_resolution`: ~32s time bins
- `test_window_2d_resolution`: ~3min time bins
- `test_all_windows_supported`: 2h/8h/2d

#### `TestSettingsPersistence`
- `test_settings_defaults`: Default values
- `test_settings_different_windows`: Window options
- `test_settings_different_normalizations`: linear/sqrt/log
- `test_settings_opacity_range`: [0.0, 1.0]
- `test_settings_palettes`: hot/viridis/plasma/cool

#### `TestErrorHandling`
- `test_corrupted_db_file_recovery`: Handle corrupted DB
- `test_missing_db_creates_new`: Auto-create on missing
- `test_concurrent_writes_with_wal`: WAL handles concurrency
- `test_graceful_degradation_on_ws_error`: Continue on WS error
- `test_recovery_from_partial_insert`: Partial batch recovery

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest Heatmap/tests/

# Run specific file
pytest Heatmap/tests/test_ws_parse.py

# Run specific class
pytest Heatmap/tests/test_grid_builder.py::TestPriceToRowMapping

# Run specific test
pytest Heatmap/tests/test_ws_parse.py::TestWebSocketPayloadParsing::test_parse_valid_forceorder_payload

# Verbose output
pytest Heatmap/tests/ -v

# With logging
pytest Heatmap/tests/ -v -s

# Stop on first failure
pytest Heatmap/tests/ -x

# Run last failed
pytest Heatmap/tests/ --lf
```

### Coverage Reports

```bash
# Generate coverage report
pytest Heatmap/tests/ --cov=Heatmap --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Performance & Profiling

```bash
# Run with timing
pytest Heatmap/tests/ -v --durations=10

# Profile specific test
pytest Heatmap/tests/test_grid_builder.py -v --profile
```

## Test Data

All test data is generated via fixtures in `conftest.py`.

### Binance Payloads
- **SELL liquidation**: 1.5 BTC @ 42500.50 USDT
- **BUY liquidation**: 2.0 BTC @ 42600.00 USDT
- **Bulk**: 100 events, 500ms apart, prices drift 42500→42549

### Time Windows
- **2h**: 2 × 3600 × 1000 = 7,200,000 ms
- **8h**: 8 × 3600 × 1000 = 28,800,000 ms
- **2d**: 2 × 24 × 3600 × 1000 = 172,800,000 ms

### Grid Dimensions
- **Rows**: 100-400 (based on height)
- **Cols**: 600-1700 (based on width)
- **Default**: 200 rows × 900 cols

### Price Ranges
- **Range**: 40000 - 50000 USDT
- **TickSize**: 0.01 USDT
- **Bin size**: ~50 USDT (rounded to TickSize)

## Parametrized Tests

Several tests use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize("window,expected_bins", [
    ("2h", 8),  # 8-second bins
    ("8h", 32), # 32-second bins
    ("2d", 192),# 192-second (3-min) bins
])
def test_window_bins(window, expected_bins):
    ...
```

## Fixtures Used

### Parametrized Fixtures
- `sample_window_params`: Single set of default params
- `settings_2h`, `settings_8h`, `settings_2d`: Window-specific settings
- `time_window_2h`, `time_window_8h`, `time_window_2d`: Time ranges

### Factory Fixtures
- `bulk_forceorder_payloads`: Generates 100 random events
- `bulk_liq_events`: Generates 50 random liquidation events

### One-Time Fixtures (scope='session')
- `project_root`: Project root path
- `test_data_dir`: Test data directory

## Error Cases Tested

### WebSocket
- Malformed JSON
- Missing required fields
- Wrong event type
- Zero quantity
- Negative price
- Invalid side
- Connection timeout
- Ping/pong timeout (60s)
- 24h connection limit

### Database
- Corrupted DB file
- Missing database
- Concurrent writes (WAL)
- Partial batch failures
- Retention policy (14 days)

### Grid Building
- Empty event list
- Single event
- All events same price
- All events same time
- Outlier prices
- Very small notional
- Very large notional

### Integration
- Toggle ON/OFF
- Window switching
- Settings persistence
- Data after reconnect
- Graceful degradation

## Expected Test Results

When implementation is complete, all tests should pass:

```
collected 100+ items

Heatmap/tests/test_ws_parse.py ✓
Heatmap/tests/test_sqlite_store.py ✓
Heatmap/tests/test_grid_builder.py ✓
Heatmap/tests/test_integration.py ✓

====== 100+ passed in X.XXs ======
```

## Mocking & Patching

Tests use `unittest.mock` for external dependencies:

```python
from unittest.mock import patch, AsyncMock

# Mock WebSocket
with patch("websockets.connect") as mock_connect:
    mock_ws = AsyncMock()
    mock_connect.return_value = mock_ws
    # Test code

# Mock database
with patch("sqlite3.connect") as mock_db:
    mock_cursor = MagicMock()
    # Test code
```

## Notes for Implementation

When implementing the actual Heatmap components:

1. **WebSocket Parser** (`ingestion/binance_forceorder_ws.py`)
   - Ensure `forceOrder` event type filtering
   - Validate all required fields
   - Handle connection lifecycle (24h limit)
   - Implement exponential backoff with jitter

2. **SQLite Store** (`storage/sqlite_store.py`)
   - Enable WAL mode
   - Create both indexes
   - Batch inserts (50-200 events)
   - Implement retention cleanup

3. **Grid Builder** (`aggregation/grid_builder.py`)
   - Map prices to rows with TickSize rounding
   - Map timestamps to columns
   - Support linear/sqrt/log normalization
   - Calculate auto resolution from window size

4. **Integration** (Top-level service)
   - Continuous WS ingestion
   - Toggle rendering without stopping DB stream
   - Support window switching
   - Persist settings

## Further Reading

- Project Plan: `01_Projectplan/Heatmap/Heatmap_Umsetzungsplan_Checkliste.md`
- Feature README: `Heatmap/README.md`
- Architecture: `ARCHITECTURE.md`
