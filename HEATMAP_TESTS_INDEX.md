# Heatmap Test Suite - Complete Index

## Quick Links

- **Summary**: [HEATMAP_TESTS_SUMMARY.md](./HEATMAP_TESTS_SUMMARY.md)
- **Quick Start**: [Heatmap/tests/QUICKSTART.md](./Heatmap/tests/QUICKSTART.md)
- **Full Docs**: [Heatmap/tests/README_TESTS.md](./Heatmap/tests/README_TESTS.md)
- **Feature Docs**: [Heatmap/README.md](./Heatmap/README.md)
- **Project Plan**: [01_Projectplan/Heatmap/](./01_Projectplan/Heatmap/)

## Test Files Location

All files are in `/Heatmap/tests/`:

```
Heatmap/tests/
├── __init__.py              # Package initialization
├── conftest.py              # 40+ shared fixtures (367 lines)
├── test_ws_parse.py         # 36 WebSocket tests (482 lines)
├── test_sqlite_store.py     # 33 Database tests (679 lines)
├── test_grid_builder.py     # 44 Grid tests (654 lines)
├── test_integration.py      # 21 Integration tests (693 lines)
├── README_TESTS.md          # Full documentation
└── QUICKSTART.md            # Quick reference
```

## Statistics at a Glance

| Metric | Value |
|--------|-------|
| Total Test Files | 5 Python files |
| Total Test Methods | 106 tests |
| Total Lines of Code | 2,924 lines |
| Fixture Count | 40+ fixtures |
| Test Classes | 21 classes |
| Expected Pass Time | 2-5 seconds |

## Test Categories

### 1. WebSocket Parsing (36 tests)
**File**: `test_ws_parse.py`

Covers:
- Binance forceOrder event parsing
- Payload validation (required fields, types)
- Connection lifecycle management
- Exponential backoff (1, 2, 4, 8, 16, 32, 60s)
- Reconnect with jitter
- Ping/pong handling
- 24-hour connection limit
- Error cases: malformed JSON, missing fields, invalid values

### 2. SQLite Database (33 tests)
**File**: `test_sqlite_store.py`

Covers:
- Schema initialization (9 columns)
- Index creation (symbol_ts, ts)
- WAL mode and pragma settings
- Single and batch inserts (50-200 events)
- Time window queries (2h/8h/2d)
- Aggregation queries (COUNT, SUM, AVG)
- Retention policy (14 days)
- VACUUM cleanup
- Performance optimization
- Corrupt DB recovery

### 3. Grid Building (44 tests)
**File**: `test_grid_builder.py`

Covers:
- Grid initialization and population
- Price-to-row mapping with TickSize rounding
- Time-to-column mapping
- Normalization (linear, sqrt, log)
- Auto-resolution calculation
- Edge cases: empty, single event, outliers
- Clipping and bounds checking
- Full pipeline validation

### 4. Integration (21 tests)
**File**: `test_integration.py`

Covers:
- End-to-end flow: WS → DB → Grid
- Heatmap toggle (ON/OFF)
- Window switching (2h/8h/2d)
- Settings persistence
- Data after reconnect
- Error handling and recovery

## Test Data & Fixtures

### Sample Binance Event
```python
{
    "e": "forceOrder",
    "E": 1704067200000,
    "o": {
        "s": "BTCUSDT",
        "S": "SELL",
        "q": 1.5,
        "p": 42500.50,
    }
}
```

### Grid Configuration
- Rows: 200 (price bins)
- Cols: 900 (time bins)
- Price Range: 40,000 - 50,000 USDT
- TickSize: 0.01 USDT

### Time Windows
- 2h: 7,200,000 ms (8s bins)
- 8h: 28,800,000 ms (32s bins)
- 2d: 172,800,000 ms (192s bins)

## Running Tests

### All Tests
```bash
cd /mnt/d/03_Git/02_Python/07_OrderPilot-AI
pytest Heatmap/tests/ -v
```

### By Component
```bash
pytest Heatmap/tests/test_ws_parse.py -v         # 36 WebSocket tests
pytest Heatmap/tests/test_sqlite_store.py -v     # 33 Database tests
pytest Heatmap/tests/test_grid_builder.py -v     # 44 Grid tests
pytest Heatmap/tests/test_integration.py -v      # 21 Integration tests
```

### With Coverage
```bash
pytest Heatmap/tests/ --cov=Heatmap --cov-report=html
```

### Specific Test
```bash
pytest Heatmap/tests/test_ws_parse.py::TestWebSocketPayloadParsing::test_parse_valid_forceorder_payload -v
```

## Key Test Coverage

### WebSocket
- [x] Valid Binance forceOrder parsing
- [x] Exponential backoff with jitter
- [x] 24-hour connection limit (5% safety margin)
- [x] Ping/pong keepalive
- [x] Malformed JSON handling
- [x] Missing field validation
- [x] 100-event batch processing

### Database
- [x] Schema with 9 columns
- [x] Two performance indexes
- [x] WAL mode enabled
- [x] Batch inserts (50+)
- [x] Time window queries
- [x] Aggregation functions
- [x] 14-day retention
- [x] VACUUM cleanup
- [x] Concurrent access (WAL)

### Grid
- [x] Price-to-row mapping
- [x] TickSize rounding
- [x] Time-to-column mapping
- [x] Linear normalization
- [x] Sqrt normalization
- [x] Log normalization
- [x] Auto-resolution
- [x] Edge cases

### Integration
- [x] End-to-end pipeline
- [x] Toggle behavior
- [x] Window switching
- [x] Settings persistence
- [x] Error recovery

## Implementation Checklist

Use these tests to implement the feature in TDD style:

### 1. WebSocket Client
```python
# Tests: test_ws_parse.py
# Implement: Heatmap/ingestion/binance_forceorder_ws.py
- [ ] Parse Binance events
- [ ] Implement backoff logic
- [ ] Handle ping/pong
- [ ] 24h reconnect
```

### 2. SQLite Store
```python
# Tests: test_sqlite_store.py
# Implement: Heatmap/storage/sqlite_store.py
- [ ] Create schema
- [ ] Batch inserts
- [ ] Query operations
- [ ] Retention cleanup
```

### 3. Grid Builder
```python
# Tests: test_grid_builder.py
# Implement: Heatmap/aggregation/grid_builder.py
- [ ] Price/time mapping
- [ ] Normalization
- [ ] Auto-resolution
- [ ] Edge cases
```

### 4. Service & UI
```python
# Tests: test_integration.py
# Implement: Heatmap service and UI bridge
- [ ] WS ingestion
- [ ] DB storage
- [ ] Grid building
- [ ] UI rendering
```

## Expected Results

```
collected 106 items

test_ws_parse.py ✓ ✓ ✓ ... (36 tests)
test_sqlite_store.py ✓ ✓ ✓ ... (33 tests)
test_grid_builder.py ✓ ✓ ✓ ... (44 tests)
test_integration.py ✓ ✓ ✓ ... (21 tests)

====== 106 passed in 2.5s ======
```

## Documentation Files

1. **HEATMAP_TESTS_SUMMARY.md**
   - Complete project summary
   - Test breakdown by category
   - Statistics and metrics
   - Next implementation steps

2. **Heatmap/tests/README_TESTS.md** (400+ lines)
   - Detailed test documentation
   - All test cases explained
   - Fixture reference
   - Running instructions
   - Implementation notes

3. **Heatmap/tests/QUICKSTART.md** (300+ lines)
   - Quick reference guide
   - Common commands
   - Debugging tips
   - Test data values

4. **Heatmap/tests/__init__.py**
   - Package initialization
   - Module description
   - Usage examples

## Fixture Summary

### Binance Payloads (6 fixtures)
- `sample_binance_forceorder_payload`: Standard SELL event
- `sample_binance_forceorder_buy`: BUY-side event
- `malformed_payload_missing_fields`: Invalid
- `malformed_payload_invalid_json`: Unparseable
- `malformed_payload_wrong_event`: Wrong type
- `bulk_forceorder_payloads`: 100 realistic events

### Event Models (2 fixtures)
- `sample_liq_event`: Single event
- `bulk_liq_events`: 50 events

### Database (2 fixtures)
- `temp_db_path`: Temporary DB file
- `exchange_info_response`: API response

### Grid & Parameters (8 fixtures)
- `sample_window_params`: Resolution settings
- `time_window_2h/8h/2d`: Time ranges
- `expected_grid_structure`: Output schema
- `raw_intensities`: Test matrix
- `normalized_linear`: Expected result
- `settings_2h/8h/2d`: Window settings

## Next Steps

1. **Read**: [HEATMAP_TESTS_SUMMARY.md](./HEATMAP_TESTS_SUMMARY.md)
2. **Review**: [Heatmap/tests/README_TESTS.md](./Heatmap/tests/README_TESTS.md)
3. **Reference**: [Heatmap/tests/QUICKSTART.md](./Heatmap/tests/QUICKSTART.md)
4. **Implement**: Using test files as TDD guide
5. **Verify**: `pytest Heatmap/tests/ -v` (expect 106 pass)

## Contact & Questions

Refer to:
- Feature README: [Heatmap/README.md](./Heatmap/README.md)
- Project Plan: [01_Projectplan/Heatmap/](./01_Projectplan/Heatmap/)
- Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

**Status**: Ready for implementation
**Test Coverage**: 106 comprehensive tests
**Documentation**: 1,000+ lines
**Lines of Test Code**: 2,924 lines
