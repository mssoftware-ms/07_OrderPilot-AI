# End-to-End Integration Tests: 2-Stage Regime & Indicator Optimization

Complete test suite for the dual-stage optimization workflow:
- **Stage 1**: Regime detection parameter optimization
- **Stage 2**: Indicator-based signal optimization per regime

## 📋 Test Suite Overview

### Test 1: Stage 1 Complete Workflow (`test_regime_optimization_e2e`)
Tests the entire regime optimization pipeline:
1. Load 1000 bars of BTCUSDT 5m data
2. Run Optuna TPE optimization (50 trials, quick mode)
3. Calculate ADX, SMA, RSI, Bollinger Bands indicators
4. Classify bars into BULL/BEAR/SIDEWAYS regimes
5. Optimize parameters for maximum F1-scores and stability
6. Export `regime_optimization_results.json` (all 50 trials)
7. Export `optimized_regime.json` with bar_indices for each regime

**Verification Points:**
- ✓ Optimization produces 50 results sorted by score
- ✓ Best result has valid parameters and metrics
- ✓ Regime periods extracted with precise bar indices
- ✓ Bar indices span from start_idx to end_idx
- ✓ JSON exports validate against schema v2.0
- ✓ All results ranked correctly

### Test 2: Stage 2 Complete Workflow (`test_indicator_optimization_e2e`)
Tests indicator optimization for regime-specific signals:
1. Load Stage 1 output (optimized_regime.json)
2. Extract bar indices for BULL regime
3. Filter market data to BULL-regime bars only
4. Simulate indicator optimization (RSI for entry, MACD for exit)
5. Run signal backtest with slippage/fees
6. Calculate metrics (win rate, profit factor, sharpe, expectancy)
7. Export `indicator_optimization_results.json` (40 trials)
8. Export `indicator_sets.json` (best indicator per signal type)

**Verification Points:**
- ✓ Correct bars extracted using bar_indices from Stage 1
- ✓ Filtered data has valid OHLCV columns
- ✓ Signal backtest produces realistic metrics
- ✓ Win rate between 0-1, profit factor > 0
- ✓ Indicator types limited to: RSI, MACD, STOCH, BB, ATR, EMA, CCI

### Test 3: Stage 1 → Stage 2 Handoff (`test_stage1_to_stage2_handoff`)
Validates data flow between optimization stages:
1. Run Stage 1 optimization (20 quick trials)
2. Extract regime periods with bar_indices
3. Build Stage 1 export JSON
4. For each regime (BULL/BEAR/SIDEWAYS):
   - Extract all bar_indices from periods
   - Verify indices are sequential and valid
   - Filter sample data using indices
   - Verify filtered data has all required OHLCV columns
   - Confirm minimum 50 bars available for Stage 2

**Verification Points:**
- ✓ bar_indices field present in all periods
- ✓ bar_indices[0] == start_idx
- ✓ bar_indices[-1] == end_idx
- ✓ len(bar_indices) == bars count
- ✓ Filtered data valid for Stage 2 optimization
- ✓ No missing or duplicate indices

### Test 4: JSON Schema Compliance (`test_json_schema_compliance`)
Validates all 4 JSON output formats:

**regime_optimization_results.json**
```json
{
  "version": "2.0",
  "meta": {
    "stage": "regime_optimization",
    "method": "tpe_multivariate",
    "total_combinations": 50,
    "completed": 50
  },
  "results": [
    {
      "rank": 1,
      "score": 75.5,
      "params": { "adx_period": 14, ... },
      "metrics": { "f1_bull": 0.75, "f1_bear": 0.72, ... }
    }
  ]
}
```

**optimized_regime.json**
```json
{
  "version": "2.0",
  "meta": { "stage": "regime_optimization_exported" },
  "parameters": { "adx_period": 14, ... },
  "regime_periods": [
    {
      "regime": "BULL",
      "start_idx": 0,
      "end_idx": 175,
      "bars": 176,
      "bar_indices": [0, 1, 2, ..., 175]
    }
  ]
}
```

**indicator_optimization_results.json**
```json
{
  "version": "2.0",
  "meta": {
    "stage": "indicator_optimization",
    "regime": "BULL",
    "total_trials": 40
  },
  "results": [
    {
      "rank": 1,
      "signal_type": "entry_long",
      "indicator": "RSI",
      "score": 68.5,
      "metrics": { "win_rate": 0.65, "profit_factor": 1.45, ... }
    }
  ]
}
```

**indicator_sets.json**
```json
{
  "version": "2.0",
  "meta": { "stage": "indicator_optimization_exported", "regime": "BULL" },
  "signal_sets": {
    "entry_long": {
      "indicator": "RSI",
      "score": 68.5,
      "metrics": { "win_rate": 0.65, ... }
    }
  }
}
```

### Test 5: Performance Benchmark (`test_tpe_speedup_vs_grid_search`)
Verifies Optuna TPE optimization efficiency:

**Grid Search Complexity Analysis:**
- ADX period: 11 values (10-20, step 1)
- ADX threshold: 11 values (20-30, step 1)
- SMA Fast: 11 values (5-15, step 1)
- SMA Slow: 7 values (20-40, step 5)
- RSI period: 6 values (10-20, step 2)
- RSI low/high: 6×6 = 36 combinations
- BB (period/std/percentile): 6×6×5 = 180 combinations

**Total Grid Combinations:** 11×11×11×7×6×36×180 = 303,750

**TPE with 50 trials:**
- Expected: <180 seconds
- Grid Search equivalent: 303,750 trials ≈ 0.8+ hours
- Speedup: >100x

**Verification Points:**
- ✓ TPE optimization completes in <180s
- ✓ Speedup vs estimated grid search >100x
- ✓ All 50 trials produce valid results

### Test 6: UI Integration (`test_entry_analyzer_ui_tabs_exist`)
Tests Entry Analyzer popup UI tabs (requires PyQt6):

**6 New Tabs:**
1. ✓ Regime Setup
2. ✓ Regime Optimization
3. ✓ Regime Results
4. ✓ Indicator Setup (disabled until regime results loaded)
5. ✓ Indicator Optimization
6. ✓ Indicator Results

**Additional UI Tests:**
- RegimeOptimizationThread initialization
- IndicatorOptimizationThread initialization

## 🚀 Running the Tests

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio

# For UI tests (optional)
pip install PyQt6
```

### Quick Run (All Tests)
```bash
# Run all E2E tests with coverage
pytest tests/integration/test_regime_optimization_e2e.py -v --cov=src --cov-report=html

# Output:
# - Console: detailed test results
# - htmlcov/index.html: coverage report
```

### Run Specific Test
```bash
# Stage 1 only
pytest tests/integration/test_regime_optimization_e2e.py::TestStage1RegimeOptimization -v

# Stage 2 only
pytest tests/integration/test_regime_optimization_e2e.py::TestStage2IndicatorOptimization -v

# Handoff test
pytest tests/integration/test_regime_optimization_e2e.py::TestStage1ToStage2Handoff -v

# Schema validation
pytest tests/integration/test_regime_optimization_e2e.py::TestJSONSchemaCompliance -v

# Performance test
pytest tests/integration/test_regime_optimization_e2e.py::TestPerformanceBenchmark -v

# UI tests (requires PyQt6)
pytest tests/integration/test_regime_optimization_e2e.py::TestEntryAnalyzerUIIntegration -v -m ui
```

### Run with Markers
```bash
# Run only Stage 1 tests
pytest tests/integration/test_regime_optimization_e2e.py -v -m stage1

# Run only Stage 2 tests
pytest tests/integration/test_regime_optimization_e2e.py -v -m stage2

# Run UI tests
pytest tests/integration/test_regime_optimization_e2e.py -v -m ui

# Run performance tests
pytest tests/integration/test_regime_optimization_e2e.py -v -m performance

# Skip slow tests
pytest tests/integration/test_regime_optimization_e2e.py -v -m "not slow"
```

### Run with Options
```bash
# Verbose output + show print statements
pytest tests/integration/test_regime_optimization_e2e.py -vv -s

# Stop after first failure
pytest tests/integration/test_regime_optimization_e2e.py -x

# Run last failed tests
pytest tests/integration/test_regime_optimization_e2e.py --lf

# Show slowest 10 tests
pytest tests/integration/test_regime_optimization_e2e.py --durations=10

# Save detailed report
pytest tests/integration/test_regime_optimization_e2e.py -v --tb=long > test_report.txt
```

## 📊 Test Fixtures

Fixtures are auto-generated from sample data:

```
tests/
├── fixtures/
│   ├── regime_optimization/
│   │   ├── regime_optimization_results_BTCUSDT_5m.json      (50 trials)
│   │   └── optimized_regime_BTCUSDT_5m.json                 (with bar_indices)
│   └── indicator_optimization/
│       ├── indicator_optimization_results_BULL_BTCUSDT_5m.json
│       ├── indicator_optimization_results_BEAR_BTCUSDT_5m.json
│       ├── indicator_optimization_results_SIDEWAYS_BTCUSDT_5m.json
│       ├── indicator_sets_BULL_BTCUSDT_5m.json
│       ├── indicator_sets_BEAR_BTCUSDT_5m.json
│       └── indicator_sets_SIDEWAYS_BTCUSDT_5m.json
```

Generate fixtures manually:
```bash
python tests/fixtures/generate_test_data.py
```

## 📈 Coverage Target

**Target:** 95%+ code coverage for integration tests

**Coverage Areas:**
- ✓ RegimeOptimizer (all methods, objective function, parameter suggestion)
- ✓ IndicatorSetOptimizer (signal backtest, metrics calculation)
- ✓ RegimeResultsManager (selection, export)
- ✓ JSON export/import (all 4 formats)
- ✓ bar_indices extraction and usage
- ✓ UI thread integration

**View Coverage:**
```bash
# Generate coverage report
pytest tests/integration/test_regime_optimization_e2e.py --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🔍 Troubleshooting

### Test Fails: "Fixture not found"
```bash
# Generate fixtures
python tests/fixtures/generate_test_data.py
```

### Test Fails: "RegimeOptimizer import error"
```bash
# Ensure src is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

### UI Tests Skip
```bash
# Install PyQt6
pip install PyQt6

# Run with UI tests
pytest tests/integration/test_regime_optimization_e2e.py -v -m ui
```

### Performance Test Fails (Slow Machine)
Adjust timeout in test or reduce trials:
```python
# In test_tpe_speedup_vs_grid_search, increase timeout:
assert tpe_time < 300, f"TPE took {tpe_time:.1f}s (expected <300s)"
```

## 🎯 Key Metrics

### Stage 1 Optimization
- **Input:** 1000 bars BTCUSDT 5m
- **Parameters:** 10 tunable (ADX, SMA, RSI, BB)
- **Trials:** 50 (TPE)
- **Time:** ~2-3 minutes
- **Output:** regime_optimization_results.json (50 trials) + optimized_regime.json (best)

### Stage 2 Optimization (per Regime)
- **Input:** Regime-specific bars (from bar_indices in Stage 1 output)
- **Indicators:** 7 options (RSI, MACD, STOCH, BB, ATR, EMA, CCI)
- **Signal Types:** entry_long, exit_long (expandable)
- **Trials:** 40 (TPE per indicator)
- **Metrics:** Win rate, profit factor, sharpe ratio, expectancy

### Performance
- **TPE vs Grid Search:** >100x speedup
- **50 trials:** <180 seconds
- **Full workflow (Stage 1+2):** ~15-20 minutes

## 📝 JSON File Reference

### Version 2.0 Format

All JSON files use `"version": "2.0"` with `meta.created_at` timestamps.

**Critical Field:** `bar_indices`
- Present in optimized_regime.json regime_periods
- Array of integers from start_idx to end_idx
- Used by Stage 2 to filter data to regime-specific bars
- **MUST** be included for Stage 1→2 handoff to work

## 🔗 Related Files

- `src/core/regime_optimizer.py` - Stage 1 implementation
- `src/core/indicator_set_optimizer.py` - Stage 2 implementation
- `src/core/regime_results_manager.py` - Results management
- `src/ui/dialogs/entry_analyzer/` - UI implementation
- `src/ui/threads/regime_optimization_thread.py` - Threading
- `src/ui/threads/indicator_optimization_thread.py` - Threading

## 📚 Documentation

- See `docs/ai/change-workflow.md` for detailed change process
- See `CLAUDE.md` for project-wide coding standards
- See `ARCHITECTURE.md` for system design

## ✅ Checklist for Developers

Before committing changes:
- [ ] Run full E2E test suite: `pytest tests/integration/test_regime_optimization_e2e.py -v`
- [ ] Check coverage: `pytest tests/integration/test_regime_optimization_e2e.py --cov=src`
- [ ] All tests pass (no skips)
- [ ] Coverage >95%
- [ ] UI tests pass (if PyQt6 available)
- [ ] No test fixtures modified (auto-generated)
- [ ] Log output shows all 6 test sections

---

**Last Updated:** 2026-01-24
**Test Count:** 6 main tests + 3 sub-tests = 9 total test classes
**Estimated Runtime:** 5-10 minutes (without UI tests)
