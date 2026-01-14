# Heatmap Tests - Quick Start Guide

## Installation

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio

# Verify installation
pytest --version
```

## Running Tests

### Quick Run (All Tests)
```bash
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI
pytest Heatmap/tests/ -v
```

### Run by Component

```bash
# WebSocket parsing & reconnect
pytest Heatmap/tests/test_ws_parse.py -v

# Database operations
pytest Heatmap/tests/test_sqlite_store.py -v

# Grid building & normalization
pytest Heatmap/tests/test_grid_builder.py -v

# End-to-end integration
pytest Heatmap/tests/test_integration.py -v
```

### Run Specific Test Class
```bash
# Price mapping tests
pytest Heatmap/tests/test_grid_builder.py::TestPriceToRowMapping -v

# Toggle behavior tests
pytest Heatmap/tests/test_integration.py::TestHeatmapToggle -v
```

### Run Single Test
```bash
pytest Heatmap/tests/test_ws_parse.py::TestWebSocketPayloadParsing::test_parse_valid_forceorder_payload -v
```

## Test Coverage

### WebSocket (36 tests)
Payload parsing, connection lifecycle, reconnect logic, ping/pong, error cases

```bash
pytest Heatmap/tests/test_ws_parse.py -v
```

Key tests:
- `test_parse_valid_forceorder_payload`: Validates Binance event structure
- `test_backoff_sequence`: Exponential backoff (1, 2, 4, 8, 16, 32, 60s)
- `test_connection_lifetime_24h_limit`: 24-hour connection refresh

### Database (33 tests)
Schema, inserts, queries, retention, WAL mode, performance

```bash
pytest Heatmap/tests/test_sqlite_store.py -v
```

Key tests:
- `test_schema_table_creation`: Table with 9 columns
- `test_insert_batch`: Batch insert 50 events
- `test_query_by_time_window`: Query 2h/8h/2d windows
- `test_delete_old_records`: 14-day retention

### Grid Building (44 tests)
Price/time mapping, normalization, auto-resolution, edge cases

```bash
pytest Heatmap/tests/test_grid_builder.py -v
```

Key tests:
- `test_price_to_row_basic`: Price → row mapping
- `test_tick_size_bin_rounding`: Bin respects TickSize
- `test_linear_normalization`: Linear scaling to [0, 1]
- `test_sqrt_normalization`: Square root scaling
- `test_empty_event_list`: No data → all zeros
- `test_outlier_price_clamped`: Out-of-range clamping

### Integration (21 tests)
End-to-end flows, toggles, window switching, settings, error handling

```bash
pytest Heatmap/tests/test_integration.py -v
```

Key tests:
- `test_ws_to_db_to_grid_flow`: Complete pipeline
- `test_toggle_on_loads_db_data`: Load DB when enabled
- `test_toggle_off_preserves_db_stream`: DB continues when OFF
- `test_switch_window_2h_to_8h`: Switch time windows

## Fixtures Overview

### Event Data
```python
def test_example(sample_liq_event, bulk_liq_events):
    # sample_liq_event: single liquidation event
    # bulk_liq_events: 50 realistic events
    assert sample_liq_event["symbol"] == "BTCUSDT"
    assert len(bulk_liq_events) == 50
```

### Binance Payloads
```python
def test_example(sample_binance_forceorder_payload, bulk_forceorder_payloads):
    # sample_binance_forceorder_payload: raw Binance event
    # bulk_forceorder_payloads: 100 realistic events
    assert sample_binance_forceorder_payload["e"] == "forceOrder"
```

### Database
```python
def test_example(temp_db_path):
    # Temporary SQLite database for testing
    import sqlite3
    conn = sqlite3.connect(str(temp_db_path))
    # ... test operations
```

### Grid Parameters
```python
def test_example(sample_window_params, time_window_2h):
    # sample_window_params: resolution settings
    # time_window_2h: (start_ms, end_ms) tuple
    assert sample_window_params["rows_target"] == 200
    assert sample_window_params["cols_target"] == 900
```

## Common Test Scenarios

### Test Payload Parsing
```bash
pytest Heatmap/tests/test_ws_parse.py::TestWebSocketPayloadParsing -v
```
Tests: valid events, field extraction, error cases

### Test Database Operations
```bash
pytest Heatmap/tests/test_sqlite_store.py::TestSQLiteInsertOperations -v
```
Tests: single insert, batch insert, order preservation

### Test Grid Construction
```bash
pytest Heatmap/tests/test_grid_builder.py::TestGridBuilding -v
pytest Heatmap/tests/test_grid_builder.py::TestPriceToRowMapping -v
pytest Heatmap/tests/test_grid_builder.py::TestTimeToColumnMapping -v
```
Tests: grid initialization, price mapping, time mapping

### Test Normalization
```bash
pytest Heatmap/tests/test_grid_builder.py::TestNormalization -v
```
Tests: linear, sqrt, log normalization with clipping

### Test Toggle Behavior
```bash
pytest Heatmap/tests/test_integration.py::TestHeatmapToggle -v
```
Tests: ON loads data, OFF hides rendering, DB continues

## Debugging Failed Tests

### Verbose Output
```bash
pytest Heatmap/tests/test_ws_parse.py -v -s
```
`-s` prints captured output (print statements, logging)

### Show Local Variables
```bash
pytest Heatmap/tests/test_ws_parse.py -v -l
```
Shows local variable values in tracebacks

### Drop into Debugger on Failure
```bash
pytest Heatmap/tests/test_ws_parse.py --pdb
```
Opens Python debugger on test failure

### Run Only Failed Tests
```bash
pytest Heatmap/tests/ --lf
```
Runs only tests that failed in last run

### Show Slowest Tests
```bash
pytest Heatmap/tests/ --durations=10
```
Shows 10 slowest tests

## Test Organization

```
Heatmap/tests/
├── conftest.py                # Fixtures (40+)
├── test_ws_parse.py          # WebSocket tests (36)
├── test_sqlite_store.py      # Database tests (33)
├── test_grid_builder.py      # Grid tests (44)
├── test_integration.py       # Integration tests (21)
├── README_TESTS.md           # Full documentation
└── QUICKSTART.md             # This file
```

Total: 106 tests across 4 test files

## Expected Test Output

```
collected 106 items

test_ws_parse.py::TestWebSocketPayloadParsing::test_parse_valid_forceorder_payload PASSED
test_ws_parse.py::TestWebSocketPayloadParsing::test_parse_buy_side_liquidation PASSED
...
test_sqlite_store.py::TestSQLiteSchemaInitialization::test_schema_table_creation PASSED
...
test_grid_builder.py::TestPriceToRowMapping::test_price_to_row_basic PASSED
...
test_integration.py::TestEndToEndHeatmapFlow::test_ws_to_db_to_grid_flow PASSED
...

====== 106 passed in 2.5s ======
```

## Coverage Analysis

```bash
# Generate coverage report
pytest Heatmap/tests/ --cov=Heatmap --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
# or
start htmlcov/index.html  # Windows
```

## Writing New Tests

When adding new tests, use existing fixtures:

```python
import pytest

def test_my_feature(sample_liq_event, bulk_liq_events, temp_db_path):
    """Test my new feature."""
    # Use fixtures instead of creating test data
    assert sample_liq_event["price"] > 0

    # Can mix multiple fixtures
    for event in bulk_liq_events:
        assert event["symbol"] == "BTCUSDT"
```

See `conftest.py` for all available fixtures.

## Key Test Values

### Default Window (2h)
- Duration: 7,200,000 ms
- Grid size: 200 rows × 900 cols
- Time bin: ~8 seconds
- Price range: 40,000 - 50,000 USDT
- Price bin: ~50 USDT

### Binance Event (Sample)
- Symbol: BTCUSDT
- Qty: 1.5 BTC
- Price: 42,500.50 USDT
- Side: SELL (liquidation)
- Notional: 63,750.75 USDT

### Database Schema
```sql
CREATE TABLE liq_events (
    id INTEGER PRIMARY KEY,
    ts_ms INTEGER NOT NULL,        -- Timestamp in ms
    symbol TEXT NOT NULL,          -- "BTCUSDT"
    side TEXT NOT NULL,            -- "BUY" or "SELL"
    price REAL NOT NULL,           -- 42500.50
    qty REAL NOT NULL,             -- 1.5
    notional REAL NOT NULL,        -- 63750.75
    source TEXT NOT NULL,          -- "BINANCE_USDM"
    raw_json TEXT NOT NULL         -- Full payload
)
-- Indexes:
CREATE INDEX idx_liq_events_symbol_ts ON liq_events(symbol, ts_ms)
CREATE INDEX idx_liq_events_ts ON liq_events(ts_ms)
```

## Troubleshooting

### ModuleNotFoundError: No module named 'pytest'
```bash
pip install pytest pytest-asyncio
```

### Database locked error
- Use temporary DB path from fixture
- Tests don't share DB connections
- WAL mode handles concurrent access

### Async test errors
```bash
# Install async support
pip install pytest-asyncio

# Or mark tests with decorator
@pytest.mark.asyncio
async def test_my_async():
    ...
```

### Import errors
```bash
# Ensure you're in project root
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI

# Run pytest from project root
pytest Heatmap/tests/ -v
```

## Further Reading

- **Full Test Documentation**: `Heatmap/tests/README_TESTS.md`
- **Test Summary**: `HEATMAP_TESTS_SUMMARY.md`
- **Feature README**: `Heatmap/README.md`
- **Project Plan**: `01_Projectplan/Heatmap/Heatmap_Umsetzungsplan_Checkliste.md`

---

Ready to implement? Use these tests as TDD guide!
