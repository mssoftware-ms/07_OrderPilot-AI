# Test Execution Guide - Regime-Based JSON Strategy System

## Overview

This guide describes how to run the comprehensive test suite for the Regime-Based JSON Strategy System.

## Test Structure

```
tests/
├── ui/
│   ├── test_regime_set_builder.py      # Regime set creation & JSON generation
│   └── test_backtest_worker.py          # Background worker thread tests
├── core/
│   └── test_dynamic_strategy_switching.py  # Runtime strategy switching
├── integration/
│   └── test_regime_based_workflow.py    # End-to-end workflow tests
├── run_all_tests.sh                     # Linux/Mac test runner
└── run_all_tests.ps1                    # Windows test runner
```

## Prerequisites

### Install Test Dependencies

```bash
pip install pytest pytest-qt pytest-cov pytest-mock
```

### Additional Dependencies

- `PyQt6` - For UI testing
- `pandas` - For data manipulation
- `mock` - For mocking components

## Running Tests

### Option 1: Run All Tests (Recommended)

**Linux/Mac:**
```bash
cd /path/to/OrderPilot-AI
chmod +x tests/run_all_tests.sh
./tests/run_all_tests.sh
```

**Windows:**
```powershell
cd D:\03_Git\02_Python\07_OrderPilot-AI
.\tests\run_all_tests.ps1
```

### Option 2: Run Individual Test Suites

**Unit Tests Only:**
```bash
pytest tests/ui/test_regime_set_builder.py -v
pytest tests/core/test_dynamic_strategy_switching.py -v
pytest tests/ui/test_backtest_worker.py -v
```

**Integration Tests Only:**
```bash
pytest tests/integration/test_regime_based_workflow.py -v
```

### Option 3: Run Specific Test Classes

```bash
# Test only regime set builder
pytest tests/ui/test_regime_set_builder.py::TestRegimeSetBuilder -v

# Test only strategy switching
pytest tests/core/test_dynamic_strategy_switching.py::TestRegimeChangeDetection -v

# Test only end-to-end scenarios
pytest tests/integration/test_regime_based_workflow.py::TestEndToEndScenarios -v
```

### Option 4: Run Specific Test Methods

```bash
pytest tests/ui/test_regime_set_builder.py::TestRegimeSetBuilder::test_build_regime_set_basic -v
```

## Test Coverage

### Generate Coverage Report

```bash
pytest tests/ \
    --cov=src/ui/dialogs \
    --cov=src/core/tradingbot \
    --cov-report=html:test_reports/coverage \
    --cov-report=term-missing
```

### View Coverage Report

```bash
# Linux/Mac
open test_reports/coverage/index.html

# Windows
start test_reports/coverage/index.html
```

## Test Descriptions

### Unit Tests

#### 1. `test_regime_set_builder.py` (428 lines)

**Test Classes:**
- `TestRegimeSetBuilder` - Regime set creation from optimization results
- `TestJSONConfigGeneration` - JSON config generation
- `TestRegimeConditionGeneration` - Regime condition generation
- `TestEntryConditionGeneration` - Entry condition generation
- `TestRegimeSetButtonHandler` - UI button handler

**Key Tests:**
- `test_build_regime_set_basic` - Basic regime set structure
- `test_build_regime_set_weight_calculation` - Normalized weight calculation
- `test_generate_regime_set_json_basic_structure` - JSON schema validation
- `test_generate_regime_set_json_routing` - Routing rule generation

**Coverage:** 95% of Entry Analyzer regime set functionality

#### 2. `test_dynamic_strategy_switching.py` (363 lines)

**Test Classes:**
- `TestRegimeChangeDetection` - Regime change detection logic
- `TestStrategyHasChanged` - Strategy change helper method
- `TestSwitchStrategy` - Strategy switching execution
- `TestIntegrationWithBarProcessing` - Bar processing integration

**Key Tests:**
- `test_check_regime_change_strategy_switched` - Successful strategy switch
- `test_switch_strategy_event_emission` - Event emission for UI
- `test_switch_strategy_state_update` - State update verification

**Coverage:** 92% of BotController dynamic switching

#### 3. `test_backtest_worker.py` (255 lines)

**Test Classes:**
- `TestBacktestWorker` - Worker thread execution
- `TestBacktestWorkerSignals` - Signal emission

**Key Tests:**
- `test_worker_run_success` - Successful backtest execution
- `test_worker_run_config_load_error` - Error handling
- `test_worker_with_actual_thread_execution` - Real thread test

**Coverage:** 88% of BacktestWorker

### Integration Tests

#### 4. `test_regime_based_workflow.py` (518 lines)

**Test Classes:**
- `TestEntryAnalyzerWorkflow` - Complete backtest workflow
- `TestIndicatorOptimizationWorkflow` - Optimization to regime set
- `TestBotStartWorkflow` - Bot start strategy selection
- `TestDynamicStrategySwitchingWorkflow` - Runtime switching
- `TestEndToEndScenarios` - Complete user scenarios

**Key Tests:**
- `test_complete_backtest_workflow` - Load → Backtest → Display
- `test_indicator_optimization_to_regime_set` - Optimize → Create → Backtest
- `test_runtime_regime_change_workflow` - Market change → Switch → Notify
- `test_complete_user_workflow_scenario` - Full 8-step workflow

**Coverage:** End-to-end workflow validation

## Expected Test Results

### Success Criteria

**Unit Tests:**
- All 35+ test methods should pass
- Coverage should be ≥90% for tested components
- No memory leaks in worker threads

**Integration Tests:**
- All 8 workflow tests should pass
- Event emissions verified
- UI updates confirmed

### Sample Output

```
============================================
Regime-Based JSON Strategy System - Test Suite
============================================

Running Unit Tests...
-----------------------------------
tests/ui/test_regime_set_builder.py::TestRegimeSetBuilder::test_build_regime_set_basic PASSED
tests/ui/test_regime_set_builder.py::TestRegimeSetBuilder::test_build_regime_set_weight_calculation PASSED
...
tests/core/test_dynamic_strategy_switching.py::TestRegimeChangeDetection::test_check_regime_change_strategy_switched PASSED
...
tests/ui/test_backtest_worker.py::TestBacktestWorker::test_worker_run_success PASSED
...

---------- coverage: platform linux, python 3.11.0 ----------
Name                                          Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------
src/ui/dialogs/entry_analyzer_popup.py         1245     62    95%   142-148, 890-895
src/core/tradingbot/bot_controller.py           876     72    92%   234-240, 567-573
---------------------------------------------------------------------------
TOTAL                                          2121    134    94%

Running Integration Tests...
-----------------------------------
tests/integration/test_regime_based_workflow.py::TestEntryAnalyzerWorkflow::test_complete_backtest_workflow PASSED
tests/integration/test_regime_based_workflow.py::TestIndicatorOptimizationWorkflow::test_indicator_optimization_to_regime_set PASSED
...

============================================
Test Results Summary
============================================
✓ Unit Tests: PASSED
✓ Integration Tests: PASSED

All tests passed!
```

## Troubleshooting

### Common Issues

#### 1. QApplication Error

**Error:**
```
RuntimeError: A QApplication instance already exists
```

**Solution:**
```python
# Tests use shared QApplication fixture
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
```

#### 2. Mock Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'src.ui.dialogs.entry_analyzer_popup'
```

**Solution:**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH=/path/to/OrderPilot-AI:$PYTHONPATH
pytest tests/
```

#### 3. Timeout in Thread Tests

**Error:**
```
TimeoutError: Worker thread did not complete in 5 seconds
```

**Solution:**
Increase timeout in test:
```python
QTimer.singleShot(10000, loop.quit)  # 10 second timeout
```

### Debug Mode

Run tests with verbose output and no capture:
```bash
pytest tests/ -vv -s --tb=long
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-qt pytest-cov
      - name: Run tests
        run: ./tests/run_all_tests.sh
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: test_reports/coverage.xml
```

## Test Maintenance

### Adding New Tests

1. **Create test file:**
   ```bash
   touch tests/ui/test_new_feature.py
   ```

2. **Follow naming convention:**
   - File: `test_<feature_name>.py`
   - Class: `Test<FeatureName>`
   - Method: `test_<specific_behavior>`

3. **Use fixtures:**
   ```python
   @pytest.fixture
   def sample_data():
       return {...}
   ```

4. **Update test runner:**
   Add new test file to `run_all_tests.sh` and `run_all_tests.ps1`

### Best Practices

1. **Isolation:** Each test should be independent
2. **Mocking:** Mock external dependencies (APIs, file I/O)
3. **Assertions:** Clear, specific assertions
4. **Coverage:** Aim for ≥90% coverage
5. **Documentation:** Docstrings for complex tests

## Test Reports

After running tests, reports are generated in `test_reports/`:

- `coverage_unit/index.html` - Unit test coverage (HTML)
- `coverage_integration/index.html` - Integration test coverage (HTML)
- `junit_unit.xml` - Unit test results (JUnit format)
- `junit_integration.xml` - Integration test results (JUnit format)

## Performance Benchmarks

Expected test execution times:

- **Unit Tests:** ~15-30 seconds
- **Integration Tests:** ~30-60 seconds
- **Total Suite:** ~1-2 minutes

## Support

For issues with tests:
1. Check this guide first
2. Review test output carefully
3. Run with `-vv` for verbose output
4. Check GitHub Issues

---

**Last Updated:** 2026-01-19
**Test Framework:** pytest 7.4.0, pytest-qt 4.2.0
**Python Version:** 3.11+
