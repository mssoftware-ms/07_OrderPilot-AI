# Running Comprehensive Unit Tests

Quick reference guide for executing the test suite.

## Setup

### 1. Install Dependencies
```bash
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI

# Using existing venv
source .venv/bin/activate

# Or create new one
python -m venv .venv
source .venv/bin/activate

# Install test requirements
pip install pytest pytest-cov jsonschema pandas numpy
```

### 2. Verify Installation
```bash
pytest --version
python -c "import jsonschema; print('jsonschema OK')"
```

---

## Running Tests

### All Tests (Complete Suite)
```bash
# Run all tests with verbose output
pytest tests/core/tradingbot/test_*.py -v

# Expected output: 150+ tests, ~30-45 seconds
```

### Individual Test Files

#### Test IndicatorOptimizer (40 tests, ~10s)
```bash
pytest tests/core/tradingbot/test_indicator_optimizer.py -v

# Run specific test class
pytest tests/core/tradingbot/test_indicator_optimizer.py::TestIndicatorOptimizerOptimization -v

# Run single test
pytest tests/core/tradingbot/test_indicator_optimizer.py::TestIndicatorOptimizerOptimization::test_optimize_indicator_basic -v
```

#### Test RegimeEngineJSON (50 tests, ~15s)
```bash
pytest tests/core/tradingbot/test_regime_engine_json.py -v

# Run specific scope tests
pytest tests/core/tradingbot/test_regime_engine_json.py::TestRegimeDetectorScopeFiltering -v
```

#### Test JSON Schemas (60 tests, ~15s)
```bash
pytest tests/core/tradingbot/test_json_schema_validation.py -v

# Test Stufe 1 schema only
pytest tests/core/tradingbot/test_json_schema_validation.py::TestRegimeOptimizationResultsSchema -v

# Test Stufe 2 indicator schema
pytest tests/core/tradingbot/test_json_schema_validation.py::TestIndicatorOptimizationResultsSchema -v
```

---

## Coverage Reports

### Generate HTML Coverage Report
```bash
pytest tests/core/tradingbot/ \
    --cov=src/core/tradingbot/indicator_optimizer \
    --cov=src/core/tradingbot/regime_engine_json \
    --cov=src/core/tradingbot/config/detector \
    --cov-report=html \
    --cov-report=term-missing

# Open report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage by Module
```bash
# Show coverage for each module
pytest tests/core/tradingbot/ --cov=src/core/tradingbot --cov-report=term-missing

# Expected output:
# src/core/tradingbot/indicator_optimizer.py  88%
# src/core/tradingbot/regime_engine_json.py   85%
# src/core/tradingbot/config/detector.py      92%
```

---

## Filtering & Markers

### Run Tests by Pattern
```bash
# Run initialization tests
pytest tests/core/tradingbot/ -k "initialization" -v

# Run optimization tests
pytest tests/core/tradingbot/ -k "optimize" -v

# Run regime tests (not indicator)
pytest tests/core/tradingbot/ -k "regime" -v

# Run schema tests
pytest tests/core/tradingbot/ -k "schema" -v
```

### Run Tests by Marker
```bash
# Run only unit tests
pytest tests/core/tradingbot/ -m "unit" -v

# Run integration tests
pytest tests/core/tradingbot/ -m "integration" -v

# Skip slow tests
pytest tests/core/tradingbot/ -m "not slow" -v
```

---

## Output Options

### Verbose Output (show all tests)
```bash
pytest tests/core/tradingbot/ -v
```

### Very Verbose (show assertions)
```bash
pytest tests/core/tradingbot/ -vv
```

### With Print Output (no capture)
```bash
pytest tests/core/tradingbot/ -s

# Use print() in tests
def test_example():
    print("Debug info")  # Will show with -s
    assert True
```

### With Traceback Information
```bash
# Short traceback
pytest tests/core/tradingbot/ --tb=short

# Long traceback
pytest tests/core/tradingbot/ --tb=long

# No traceback
pytest tests/core/tradingbot/ --tb=no

# Local variable info
pytest tests/core/tradingbot/ --tb=line
```

---

## Performance Testing

### Time Tests
```bash
# Show slowest 10 tests
pytest tests/core/tradingbot/ --durations=10

# Show duration for all tests
pytest tests/core/tradingbot/ -v --durations=0
```

### Parallel Execution (faster)
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest tests/core/tradingbot/ -n 4

# Auto-detect CPU count
pytest tests/core/tradingbot/ -n auto
```

---

## Parametrized Tests

### Run Specific Parameter Combinations
```bash
# Run all RSI period tests
pytest tests/core/tradingbot/test_indicator_optimizer.py -k "14" -v

# Run BULL regime tests
pytest tests/core/tradingbot/test_json_schema_validation.py -k "BULL" -v

# Run tpe method tests
pytest tests/core/tradingbot/test_json_schema_validation.py -k "tpe" -v
```

### List All Parameter Combinations
```bash
# Show what would run without executing
pytest tests/core/tradingbot/test_json_schema_validation.py --collect-only -q

# With parameter details
pytest tests/core/tradingbot/test_json_schema_validation.py --collect-only
```

---

## Test Report Generation

### JUnit XML Report (for CI/CD)
```bash
pytest tests/core/tradingbot/ --junit-xml=test_results.xml

# View results
cat test_results.xml
```

### JSON Report
```bash
# Install plugin
pip install pytest-json-report

# Generate report
pytest tests/core/tradingbot/ --json-report --json-report-file=report.json
```

### HTML Report
```bash
# Install plugin
pip install pytest-html

# Generate report
pytest tests/core/tradingbot/ --html=report.html --self-contained-html

# Open in browser
open report.html
```

---

## Debugging Failed Tests

### Run Failed Tests Again
```bash
# Save failed test nodeids
pytest tests/core/tradingbot/ --lf

# Run only failed tests from last run
pytest tests/core/tradingbot/ --lf -v

# Show exact failure
pytest tests/core/tradingbot/ -vv -x
```

### Enter Debugger on Failure
```bash
# Drop into pdb on failure
pytest tests/core/tradingbot/ --pdb

# Drop into pdb on error (not failure)
pytest tests/core/tradingbot/ --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Capture Logs
```bash
pytest tests/core/tradingbot/ --log-cli-level=DEBUG

# Capture logs to file
pytest tests/core/tradingbot/ --log-file=test.log --log-level=DEBUG
```

---

## Common Tasks

### Quick Sanity Check (2 minutes)
```bash
# Run fast tests only
pytest tests/core/tradingbot/test_indicator_optimizer.py::TestIndicatorOptimizerInitialization -v
pytest tests/core/tradingbot/test_regime_engine_json.py::TestRegimeEngineJSONInitialization -v
```

### Full Test Suite (5 minutes)
```bash
pytest tests/core/tradingbot/test_*.py -v --tb=short
```

### With Coverage Report (7 minutes)
```bash
pytest tests/core/tradingbot/ \
    --cov=src/core/tradingbot \
    --cov-report=html \
    --cov-report=term-missing \
    -v
```

### Pre-Commit Check
```bash
# Run before git commit
pytest tests/core/tradingbot/ -q

# Add to .git/hooks/pre-commit for automation
```

---

## Troubleshooting

### Import Errors
```bash
# Add project root to PYTHONPATH
export PYTHONPATH=/mnt/d/03_GIT/02_Python/07_OrderPilot-AI:$PYTHONPATH

# Or use pytest with python path
pytest --pythonpath /mnt/d/03_GIT/02_Python/07_OrderPilot-AI tests/core/tradingbot/
```

### Missing Fixtures
```bash
# List all available fixtures
pytest --fixtures tests/core/tradingbot/conftest_regime_tests.py

# Use fixtures in tests
def test_example(sample_ohlcv_data):
    assert len(sample_ohlcv_data) == 100
```

### Schema File Not Found
```bash
# Verify schema paths exist
ls -la /mnt/d/03_GIT/02_Python/07_OrderPilot-AI/01_Projectplan/260124*/schemas/

# Or run from project root
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
pytest tests/core/tradingbot/test_json_schema_validation.py -v
```

### Performance Issues
```bash
# Run tests in parallel
pip install pytest-xdist
pytest tests/core/tradingbot/ -n auto

# Skip slow tests
pytest tests/core/tradingbot/ -m "not slow"

# Check test duration
pytest tests/core/tradingbot/ --durations=10
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/core/tradingbot/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
pytest tests/core/tradingbot/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

---

## Test Organization

### Directory Structure
```
tests/core/tradingbot/
├── test_indicator_optimizer.py        # 40 tests
├── test_regime_engine_json.py          # 50 tests
├── test_json_schema_validation.py      # 60 tests
├── conftest_regime_tests.py            # Fixtures
├── TEST_COVERAGE_SUMMARY.md            # This guide
└── RUNNING_TESTS.md                    # This file
```

### Import Order
```python
# 1. Standard library
import logging
import numpy as np
import pandas as pd

# 2. Third-party
import pytest
from unittest.mock import Mock, patch

# 3. Project modules
from src.core.tradingbot.indicator_optimizer import IndicatorOptimizer
from src.core.tradingbot.regime_engine_json import RegimeEngineJSON
```

---

## References

- **Pytest Docs:** https://docs.pytest.org/
- **Test Coverage:** https://coverage.readthedocs.io/
- **JSON Schema:** https://json-schema.org/
- **unittest.mock:** https://docs.python.org/3/library/unittest.mock.html

---

## Quick Reference Commands

```bash
# All tests, verbose
pytest tests/core/tradingbot/ -v

# With coverage
pytest tests/core/tradingbot/ --cov=src/core/tradingbot --cov-report=html

# Fast mode (no slow tests)
pytest tests/core/tradingbot/ -m "not slow"

# Parallel execution
pytest tests/core/tradingbot/ -n auto

# Specific test class
pytest tests/core/tradingbot/test_indicator_optimizer.py::TestIndicatorOptimizerOptimization -v

# Show slowest tests
pytest tests/core/tradingbot/ --durations=10

# Debug failed tests
pytest tests/core/tradingbot/ --lf --pdb

# Generate HTML report
pytest tests/core/tradingbot/ --html=report.html --self-contained-html
```

---

**Last Updated:** 2026-01-24
**Version:** 1.0
