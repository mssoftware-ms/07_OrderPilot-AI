# E2E Test Architecture

## Overview

The E2E test suite validates the complete 2-stage optimization workflow:
1. **Stage 1:** Regime detection parameter optimization (ADX, SMA, RSI, BB)
2. **Stage 2:** Indicator-based signal optimization per regime
3. **Handoff:** Validating Stage 1 output is valid Stage 2 input

## Test Structure

```
tests/integration/
├── test_regime_optimization_e2e.py  ← Main test file (9 test classes)
├── conftest.py                       ← Shared fixtures & pytest config
├── pytest.ini                        ← Pytest configuration
├── run_e2e_tests.sh                  ← Bash test runner
├── run_e2e_tests.ps1                 ← PowerShell test runner
├── README_E2E_TESTS.md               ← User guide
└── TEST_ARCHITECTURE.md              ← This file

tests/fixtures/
├── regime_optimization/
│   ├── regime_optimization_results_BTCUSDT_5m.json
│   └── optimized_regime_BTCUSDT_5m.json
├── indicator_optimization/
│   ├── indicator_optimization_results_*.json (3 regimes)
│   └── indicator_sets_*.json (3 regimes)
└── generate_test_data.py             ← Fixture generator
```

## Test Classes & Methods

### 1. TestStage1RegimeOptimization
**Purpose:** Validate complete Stage 1 workflow

**Methods:**
- `test_regime_optimization_e2e()` - Full workflow end-to-end
  - Load 1000 bars sample data
  - Configure optimization (quick: 50 trials)
  - Run RegimeOptimizer.optimize()
  - Verify results structure
  - Export regime_optimization_results.json
  - Extract regime periods with bar_indices
  - Export optimized_regime.json with bar_indices

**Assertions:**
```python
✓ len(results) <= 50
✓ results[0].rank == 1
✓ results sorted by score descending
✓ Best params valid (sma_fast < sma_slow)
✓ Metrics normalized (0-1 range)
✓ regime_periods extracted with bar_indices
✓ bar_indices: [start_idx ... end_idx]
✓ JSON exports match schema v2.0
```

### 2. TestStage2IndicatorOptimization
**Purpose:** Validate complete Stage 2 workflow

**Methods:**
- `test_indicator_optimization_e2e()` - Full workflow end-to-end
  - Load Stage 1 output (optimized_regime.json)
  - Extract BULL regime bar_indices
  - Filter data to BULL-regime bars
  - Simulate indicator optimization (RSI entry, MACD exit)
  - Run signal backtest with slippage/fees
  - Verify metrics realistic
  - Export indicator_optimization_results.json
  - Export indicator_sets.json

**Assertions:**
```python
✓ bull_periods extracted
✓ bull_indices valid range [0, 1000)
✓ data_bull filtered correctly
✓ len(data_bull) > 50
✓ Signal metrics calculated
✓ win_rate in [0, 1]
✓ profit_factor >= 0
✓ sharpe_ratio calculated
✓ JSON exports match schema
```

### 3. TestStage1ToStage2Handoff
**Purpose:** Validate Stage 1→2 data flow

**Methods:**
- `test_stage1_to_stage2_handoff()` - Verify handoff mechanism
  - Run Stage 1 optimization (20 quick trials)
  - Extract regime periods
  - Build Stage 1 export with bar_indices
  - For each regime (BULL/BEAR/SIDEWAYS):
    - Verify bar_indices field present
    - Verify indices sequential
    - Filter data using indices
    - Verify filtered data valid for Stage 2

**Assertions:**
```python
✓ regime_periods extracted
✓ "bar_indices" in each period
✓ bar_indices[0] == start_idx
✓ bar_indices[-1] == end_idx
✓ len(bar_indices) == bars
✓ Filtered data has OHLCV columns
✓ len(filtered_data) >= 50
✓ All regimes have valid indices
```

### 4. TestJSONSchemaCompliance
**Purpose:** Validate JSON format compliance

**Sub-tests:**
- `test_regime_optimization_results_schema()` - regime_optimization_results.json
- `test_optimized_regime_schema()` - optimized_regime.json (with bar_indices)
- `test_indicator_optimization_results_schema()` - indicator_optimization_results.json
- `test_indicator_sets_schema()` - indicator_sets.json

**Schema Checks:**
```
regime_optimization_results.json:
  ✓ version: "2.0"
  ✓ meta: {stage, method, created_at, total_combinations}
  ✓ results[]: {rank, score, params, metrics}
  ✓ score: [0, 100]
  ✓ params: {adx_period, adx_threshold, ...}
  ✓ metrics: {f1_bull, f1_bear, f1_sideways, ...}

optimized_regime.json:
  ✓ version: "2.0"
  ✓ meta: {stage: regime_optimization_exported}
  ✓ parameters: {adx_period, ...}
  ✓ regime_periods[]: {regime, start_idx, end_idx, bars, bar_indices}
  ✓ bar_indices: [int] with proper range

indicator_optimization_results.json:
  ✓ version: "2.0"
  ✓ meta: {stage: indicator_optimization, regime}
  ✓ results[]: {rank, signal_type, indicator, score, metrics}
  ✓ indicator in [RSI, MACD, STOCH, BB, ATR, EMA, CCI]

indicator_sets.json:
  ✓ version: "2.0"
  ✓ meta: {stage: indicator_optimization_exported, regime}
  ✓ signal_sets: {signal_type: {indicator, params, score, metrics}}
```

### 5. TestPerformanceBenchmark
**Purpose:** Verify TPE optimization efficiency

**Methods:**
- `test_tpe_speedup_vs_grid_search()` - Performance comparison
  - Calculate grid search combinations: 303,750
  - Run TPE with 50 trials
  - Measure execution time
  - Calculate speedup: estimated_grid_time / tpe_time

**Assertions:**
```python
✓ tpe_time < 180 seconds
✓ speedup > 100x (vs estimated grid search)
✓ All 50 trials produce valid results
```

**Calculation:**
```
Grid Space: 11×11×11×7×6×6×6×6×6×5 = 303,750
TPE Trials: 50
Estimated Grid Time: (tpe_time / 50) × 303,750
Speedup: estimated_grid_time / tpe_time
```

### 6. TestEntryAnalyzerUIIntegration
**Purpose:** Validate UI tabs & threads

**Methods:**
- `test_entry_analyzer_ui_tabs_exist()` - Verify 6 tabs
  - Create EntryAnalyzerPopup
  - Get tab names
  - Verify: Regime Setup, Regime Optimization, Regime Results,
    Indicator Setup, Indicator Optimization, Indicator Results
  - Verify Indicator Setup disabled initially

- `test_regime_optimization_thread_integration()` - RegimeOptimizationThread
  - Initialize thread
  - Verify not None

- `test_indicator_optimization_thread_integration()` - IndicatorOptimizationThread
  - Initialize thread
  - Verify not None

**Assertions:**
```python
✓ All 6 tabs present
✓ Tab order correct
✓ Indicator Setup disabled initially
✓ Threads initialize without errors
```

## Fixture Architecture

### Auto-Generated Fixtures
File: `tests/fixtures/generate_test_data.py`

**Function:** `generate_sample_ohlcv()`
- Generates 1000 bars BTCUSDT 5m
- Realistic OHLCV with proper relationships
- DatetimeIndex

**Function:** `create_test_fixtures()`
- Generates all JSON fixtures
- Creates regime periods with bar_indices
- Creates indicator optimization results
- Stores in appropriate subdirectories

**Fixture Files:**
```
regime_optimization_results_BTCUSDT_5m.json
├── 50 trial results (rank 1-50)
├── Ranked by composite score
└── All with params & metrics

optimized_regime_BTCUSDT_5m.json
├── Best result (rank 1)
├── 6 regime periods: 3×BULL, 2×BEAR, 1×SIDEWAYS
└── Each period has bar_indices array

indicator_optimization_results_{REGIME}_BTCUSDT_5m.json
├── 40 trial results per regime
├── Signal types: entry_long, exit_long
└── Metrics: win_rate, profit_factor, sharpe

indicator_sets_{REGIME}_BTCUSDT_5m.json
├── Best indicators per regime
├── One entry_long, one exit_long
└── Complete metrics & conditions
```

### Fixture Loading
```python
@pytest.fixture(scope="session")
def sample_data() -> pd.DataFrame:
    """Auto-generate 1000 bars sample data"""
    return generate_sample_ohlcv("BTCUSDT", "5m", 1000)

@pytest.fixture(scope="session")
def regime_results_fixture(fixtures_dir) -> dict:
    """Load pre-generated regime results"""
    path = fixtures_dir / "regime_optimization" / "..."
    return json.load(open(path))
```

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│ Stage 1: Regime Optimization                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Input: 1000 bars OHLCV (sample_data fixture)          │
│    ↓                                                    │
│  RegimeOptimizer.optimize()                            │
│    • Calculate indicators (ADX, SMA, RSI, BB)          │
│    • Classify regimes (BULL/BEAR/SIDEWAYS)            │
│    • Optuna TPE: 50 trials                            │
│    ↓                                                    │
│  Results: 50 OptimizationResult                        │
│    • params, metrics, score for each trial             │
│    • Ranked 1-50 by composite score                   │
│    ↓                                                    │
│  Export regime_optimization_results.json               │
│    • All 50 trials for analysis                        │
│    ↓                                                    │
│  Best Result + RegimePeriods                           │
│    • Extract regime periods (BULL/BEAR/SIDEWAYS)      │
│    • Calculate bar_indices for each period             │
│    ↓                                                    │
│  Export optimized_regime.json                          │
│    • Best params + regime periods                      │
│    • **Critical:** bar_indices for Stage 2             │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
                    HANDOFF POINT
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 2: Indicator Optimization                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Input: optimized_regime.json + original OHLCV         │
│    ↓                                                    │
│  For each regime (BULL/BEAR/SIDEWAYS):                 │
│    ↓                                                    │
│  Extract bar_indices from regime_periods               │
│    ↓                                                    │
│  Filter OHLCV data: data.iloc[bar_indices]             │
│    ↓                                                    │
│  IndicatorSetOptimizer.optimize()                      │
│    • 7 indicators: RSI, MACD, STOCH, BB, ATR, EMA, CCI│
│    • Signal types: entry_long, exit_long               │
│    • Optuna TPE: 40 trials per indicator              │
│    • Signal backtest with metrics                     │
│    ↓                                                    │
│  Results: {signal_type: OptimizationResult}           │
│    • Best indicator per signal type                    │
│    ↓                                                    │
│  Export indicator_optimization_results.json            │
│    • All 40 trials per signal type                     │
│    ↓                                                    │
│  Export indicator_sets.json                            │
│    • Best indicators for regime                        │
│    • Final trading signal parameters                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Execution Modes

### Mode: `all`
Runs all tests with coverage:
```bash
pytest tests/integration/test_regime_optimization_e2e.py \
  -v --cov=src --cov-report=html
```

**Coverage:** 95%+ target for:
- RegimeOptimizer (all methods)
- IndicatorSetOptimizer (signal backtest)
- JSON export/import
- bar_indices extraction

### Mode: `quick`
Fast tests excluding slow/UI:
```bash
pytest tests/integration/test_regime_optimization_e2e.py \
  -v -m "not slow and not ui" --timeout=60
```

Time: ~2-3 minutes

### Mode: `stage1` / `stage2`
Targeted tests:
```bash
pytest tests/integration/test_regime_optimization_e2e.py::TestStage1RegimeOptimization -v
pytest tests/integration/test_regime_optimization_e2e.py::TestStage2IndicatorOptimization -v
```

### Mode: `ui`
UI tests (requires PyQt6):
```bash
pytest tests/integration/test_regime_optimization_e2e.py::TestEntryAnalyzerUIIntegration -v -m ui
```

## Key Testing Patterns

### 1. Fixture Generators
```python
@pytest.fixture(scope="session")
def sample_data():
    """Auto-generate test data once per session"""
    return generate_sample_ohlcv(...)
```

### 2. Temporary Output
```python
@pytest.fixture
def tmp_output_dir(tmp_path):
    """Isolated output directory per test"""
    return tmp_path / "outputs"
```

### 3. Schema Validation
```python
# Verify JSON matches expected structure
assert exported["version"] == "2.0"
assert "bar_indices" in period  # Critical!
assert len(period["bar_indices"]) == period["bars"]
```

### 4. Data Flow Testing
```python
# Test Stage 1 → Stage 2 handoff
indices = stage1_output["regime_periods"][0]["bar_indices"]
data_filtered = full_data.iloc[indices]
assert len(data_filtered) > 50  # Valid for Stage 2
```

### 5. Performance Measurement
```python
start = time.time()
result = optimizer.optimize(n_trials=50)
duration = time.time() - start
assert duration < 180  # Performance assertion
```

## Error Handling

### Fixture Missing
```
pytest.skip("Fixture not found: ...")
```
Auto-generates on next run.

### Import Error
```
pytest.skip("PyQt6 not available")
```
UI tests skipped if PyQt6 not installed.

### Assertion Failure
```
AssertionError: bar_indices missing in regime BULL
```
Indicates Stage 1 export missing critical data.

## Logging

Tests use Python logging:
```python
logger = logging.getLogger(__name__)

logger.info(f"✓ Stage 1 E2E: {len(results)} results, best: {score:.2f}")
logger.error(f"Trial {trial.number} failed: {e}")
```

View with:
```bash
pytest tests/integration/test_regime_optimization_e2e.py -v -s
```

## Test Maintenance

### Adding New Test
1. Create `test_new_feature()` in appropriate TestClass
2. Add fixtures if needed to conftest.py
3. Add docstring explaining test purpose
4. Run: `pytest tests/integration/test_regime_optimization_e2e.py::TestClass::test_new -v`

### Updating Fixtures
```bash
python tests/fixtures/generate_test_data.py
```

Regenerates all fixture JSON files.

### Debugging Failed Test
```bash
pytest tests/integration/test_regime_optimization_e2e.py::TestClass::test_method -vv -s --tb=long
```

## Success Criteria

✓ All 9 test classes pass
✓ Coverage >95% for src/core and src/ui
✓ No skipped tests (fixtures available)
✓ Performance: TPE <180s for 50 trials
✓ JSON exports validate against schema v2.0
✓ bar_indices present and correct in optimized_regime.json

---

**Framework:** pytest 7.x+
**Coverage Tool:** coverage.py
**Markers:** ui, slow, performance, stage1, stage2, handoff, schema
**Timeout:** 300s per test
**Python:** 3.10+
