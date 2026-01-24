# Quick Start: E2E Integration Tests

Get up and running in 2 minutes!

## 1. Run All Tests

### Linux / macOS
```bash
cd /path/to/OrderPilot-AI
chmod +x tests/integration/run_e2e_tests.sh
./tests/integration/run_e2e_tests.sh all
```

### Windows (PowerShell)
```powershell
cd C:\path\to\OrderPilot-AI
.\tests\integration\run_e2e_tests.ps1 -Mode all
```

### Direct Pytest
```bash
pytest tests/integration/test_regime_optimization_e2e.py -v --cov=src
```

## 2. Verify Installation

```bash
# Check pytest installed
pytest --version

# Check key dependencies
python -c "import optuna; print('Optuna OK')"
python -c "import pandas; print('Pandas OK')"
python -c "import numpy; print('Numpy OK')"
```

## 3. Run Specific Test

```bash
# Stage 1 only
pytest tests/integration/test_regime_optimization_e2e.py::TestStage1RegimeOptimization -v

# Stage 2 only
pytest tests/integration/test_regime_optimization_e2e.py::TestStage2IndicatorOptimization -v

# Handoff validation
pytest tests/integration/test_regime_optimization_e2e.py::TestStage1ToStage2Handoff -v
```

## 4. Quick Tests (2 min)

```bash
pytest tests/integration/test_regime_optimization_e2e.py -v -m "not slow and not ui" --timeout=60
```

## 5. With Coverage Report

```bash
pytest tests/integration/test_regime_optimization_e2e.py -v --cov=src --cov-report=html
open htmlcov/index.html
```

## 6. Expected Output

```
tests/integration/test_regime_optimization_e2e.py::TestStage1RegimeOptimization::test_regime_optimization_e2e PASSED    [11%]
tests/integration/test_regime_optimization_e2e.py::TestStage2IndicatorOptimization::test_indicator_optimization_e2e PASSED    [22%]
tests/integration/test_regime_optimization_e2e.py::TestStage1ToStage2Handoff::test_stage1_to_stage2_handoff PASSED    [33%]
tests/integration/test_regime_optimization_e2e.py::TestJSONSchemaCompliance::test_regime_optimization_results_schema PASSED    [44%]
tests/integration/test_regime_optimization_e2e.py::TestJSONSchemaCompliance::test_optimized_regime_schema PASSED    [55%]
tests/integration/test_regime_optimization_e2e.py::TestJSONSchemaCompliance::test_indicator_optimization_results_schema PASSED    [66%]
tests/integration/test_regime_optimization_e2e.py::TestJSONSchemaCompliance::test_indicator_sets_schema PASSED    [77%]
tests/integration/test_regime_optimization_e2e.py::TestPerformanceBenchmark::test_tpe_speedup_vs_grid_search PASSED    [88%]
tests/integration/test_regime_optimization_e2e.py::TestEntryAnalyzerUIIntegration::test_entry_analyzer_ui_tabs_exist SKIPPED    [99%]

========================= 8 passed, 1 skipped in 45.23s =========================
```

## 7. Troubleshooting

### No tests found
```bash
# Ensure conftest.py is present
ls tests/conftest.py tests/integration/conftest.py

# Regenerate fixtures
python tests/fixtures/generate_test_data.py
```

### Import errors
```bash
# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/OrderPilot-AI
pytest tests/integration/test_regime_optimization_e2e.py -v
```

### Timeout errors
Adjust timeout for slow machines:
```bash
pytest tests/integration/test_regime_optimization_e2e.py -v --timeout=600
```

### PyQt6 tests skip
```bash
# Install PyQt6 to run UI tests
pip install PyQt6

# Run UI tests
pytest tests/integration/test_regime_optimization_e2e.py -v -m ui
```

## 8. Test Coverage

Expected coverage:
- `src/core/regime_optimizer.py`: 95%+
- `src/core/indicator_set_optimizer.py`: 90%+
- `src/core/regime_results_manager.py`: 95%+
- **Overall:** 95%+

View coverage:
```bash
pytest tests/integration/test_regime_optimization_e2e.py --cov=src --cov-report=term-missing
```

## 9. Files Created

```
tests/
├── integration/
│   ├── test_regime_optimization_e2e.py      ← Main test file (9 tests)
│   ├── conftest.py                          ← Fixtures & config
│   ├── pytest.ini                           ← Pytest settings
│   ├── run_e2e_tests.sh                     ← Bash runner
│   ├── run_e2e_tests.ps1                    ← PowerShell runner
│   ├── README_E2E_TESTS.md                  ← Full documentation
│   ├── TEST_ARCHITECTURE.md                 ← Architecture guide
│   └── QUICK_START.md                       ← This file
│
├── fixtures/
│   ├── generate_test_data.py                ← Fixture generator
│   ├── regime_optimization/
│   │   ├── regime_optimization_results_BTCUSDT_5m.json
│   │   └── optimized_regime_BTCUSDT_5m.json
│   └── indicator_optimization/
│       ├── indicator_optimization_results_{REGIME}_BTCUSDT_5m.json (3)
│       └── indicator_sets_{REGIME}_BTCUSDT_5m.json (3)
```

## 10. Key Test Features

✓ **Stage 1 Validation**
- Regime optimization with 50 trials
- bar_indices extraction
- JSON export compliance

✓ **Stage 2 Validation**
- Indicator optimization per regime
- Signal backtest with metrics
- Regime-specific bar filtering

✓ **Handoff Validation**
- Stage 1 output → Stage 2 input
- bar_indices usage verification
- Data filtering validation

✓ **Performance**
- TPE vs Grid Search speedup (>100x)
- Execution time <180s for 50 trials

✓ **Schema Compliance**
- All 4 JSON formats validated
- Version 2.0 compliance
- bar_indices field verification

✓ **UI Integration** (optional)
- 6 Entry Analyzer tabs
- Thread initialization

## 11. Next Steps

1. **Review results:** Check test output for failures
2. **Analyze coverage:** Open `htmlcov/index.html` for coverage report
3. **Examine fixtures:** Look at JSON files in `tests/fixtures/`
4. **Run specific test:** Use pytest filter for targeted testing
5. **Check logs:** Review detailed output with `pytest -vv -s`

## 12. Common Commands

```bash
# Full suite with coverage
pytest tests/integration/test_regime_optimization_e2e.py -v --cov=src --cov-report=html

# Stage 1 tests
pytest tests/integration/test_regime_optimization_e2e.py::TestStage1RegimeOptimization -v

# Performance benchmark
pytest tests/integration/test_regime_optimization_e2e.py::TestPerformanceBenchmark -v

# With print output
pytest tests/integration/test_regime_optimization_e2e.py -v -s

# Stop on first failure
pytest tests/integration/test_regime_optimization_e2e.py -v -x

# Show slowest tests
pytest tests/integration/test_regime_optimization_e2e.py --durations=10
```

---

**Estimated Runtime:** 5-10 minutes
**Tests Count:** 9 test classes
**Coverage Target:** 95%+
**Python:** 3.10+
