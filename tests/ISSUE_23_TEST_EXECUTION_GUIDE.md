# Issue #23 Test Execution Guide

## Quick Start

### Run All Tests
```bash
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
python -m pytest tests/test_issue_23_*.py -v -s
```

**Expected Result:**
```
20 passed in ~16-27 seconds
✅ All tests PASS
```

---

## Test Suite Organization

### 1. Basic Fix Validation Tests
**File:** `tests/test_issue_23_regime_fix_simple.py`

Tests the core fix for Issue #23:
- Field name correction from "macd" to "MACD_12_26_9"
- Regime detection functionality

**Run:**
```bash
pytest tests/test_issue_23_regime_fix_simple.py -v -s
```

**Expected Output:**
```
test_config_has_correct_macd_field_names ✅ PASSED
  ✅ Both regimes now use correct MACD field name: 'MACD_12_26_9'

test_regime_detector_with_manual_values ✅ PASSED
  ✅ Regime detection working! Found: ['strong_uptrend']
  ✅ Downtrend also detected correctly: ['strong_downtrend']
  ✅ Range regimes also work: ['range_overbought']
  ✅ All regime types detected successfully! Issue #23 is FIXED.

2 passed in 16.35s
```

### 2. Comprehensive Test Suite
**File:** `tests/test_issue_23_comprehensive.py`

Extensive testing including:
- Edge case boundary conditions
- Performance benchmarking
- Regime completeness validation
- Error handling robustness

**Run:**
```bash
pytest tests/test_issue_23_comprehensive.py -v -s
```

**Expected Output:**
```
TestEdgeCases (10 tests)
  ✅ test_macd_exactly_at_zero PASSED
  ✅ test_macd_just_above_zero PASSED
  ✅ test_macd_just_below_zero PASSED
  ✅ test_adx_exactly_at_25_threshold PASSED
  ✅ test_adx_just_above_25_threshold PASSED
  ✅ test_rsi_at_30_boundary PASSED
  ✅ test_rsi_at_70_boundary PASSED
  ✅ test_extreme_positive_macd PASSED
  ✅ test_extreme_negative_macd PASSED
  ✅ test_all_indicator_fields_present PASSED

TestPerformance (2 tests)
  ✅ test_performance_1000_bars PASSED
    📊 Average: 0.045ms (Requirement: <100ms)
  ✅ test_performance_rapid_regimes PASSED
    📊 Average: 0.027ms (Requirement: <100ms)

TestRegimeCompleteness (3 tests)
  ✅ test_all_regime_types_defined PASSED
  ✅ test_macd_field_consistency PASSED
  ✅ test_indicator_configuration PASSED

TestErrorHandling (3 tests)
  ✅ test_missing_indicator_field PASSED
  ✅ test_empty_indicator_values PASSED
  ✅ test_none_values PASSED

18 passed in 15.85s
```

---

## Detailed Test Commands

### Run Tests with Different Verbosity Levels

#### High Verbosity (Show all details)
```bash
pytest tests/test_issue_23_*.py -vv -s --tb=long
```

#### Standard Verbosity
```bash
pytest tests/test_issue_23_*.py -v -s
```

#### Quiet Mode
```bash
pytest tests/test_issue_23_*.py -q
```

---

### Performance Profiling

#### Run Performance Tests Only
```bash
pytest tests/test_issue_23_comprehensive.py::TestPerformance -v -s
```

#### Run with Timing Information
```bash
pytest tests/test_issue_23_*.py -v --durations=10
```

**Shows:** Top 10 slowest tests

---

### Code Coverage Analysis

#### Full Coverage Report
```bash
pytest tests/test_issue_23_*.py \
  --cov=src/core/tradingbot/config \
  --cov-report=term-missing \
  -v
```

#### HTML Coverage Report
```bash
pytest tests/test_issue_23_*.py \
  --cov=src/core/tradingbot/config \
  --cov-report=html \
  -v

# Open report in browser:
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

### Run Specific Test Categories

#### Edge Case Tests Only
```bash
pytest tests/test_issue_23_comprehensive.py::TestEdgeCases -v -s
```

#### Performance Tests Only
```bash
pytest tests/test_issue_23_comprehensive.py::TestPerformance -v -s
```

#### Error Handling Tests Only
```bash
pytest tests/test_issue_23_comprehensive.py::TestErrorHandling -v -s
```

#### Regime Completeness Tests Only
```bash
pytest tests/test_issue_23_comprehensive.py::TestRegimeCompleteness -v -s
```

---

### Run Individual Tests

#### Single Test
```bash
pytest tests/test_issue_23_comprehensive.py::TestEdgeCases::test_macd_exactly_at_zero -v -s
```

#### Multiple Specific Tests
```bash
pytest \
  tests/test_issue_23_comprehensive.py::TestEdgeCases::test_macd_exactly_at_zero \
  tests/test_issue_23_comprehensive.py::TestEdgeCases::test_adx_exactly_at_25_threshold \
  -v -s
```

---

## Test Output Interpretation

### Success Indicators ✅

```
20 passed in 26.51s

- All tests passed
- No failures or errors
- Performance requirements met
- Error handling verified
```

### Warning Handling ⚠️

```
33m====================== 32m20 passed[0m, [33m1441 warnings[0m[1m

- Warnings are expected from PyQt6 and other dependencies
- No failures or errors means tests passed
- Can be ignored for this test suite
```

### Expected Log Messages (Intentional)

During error handling tests, you'll see:

```
2026-01-22 10:52:27 [ERROR] Error evaluating regime 'strong_uptrend': Field 'MACD_12_26_9' not found...
```

**This is expected and correct behavior** - tests intentionally trigger errors to verify graceful handling.

---

## Performance Test Results

### Benchmark Results from Test Suite

```
📊 Performance Results (1000 bars):
   Average: 0.045ms per detection
   Min: 0.019ms
   Max: 0.796ms
   Total: 45.1ms

📊 Rapid Regime Changes (500 bars):
   Average: 0.027ms per detection
   Max: 0.103ms
```

### Performance Requirements
- ✅ Average detection: **<100ms** (Exceeds by 2222x)
- ✅ Max detection: **<200ms** (Exceeds by 251x)
- ✅ Suitable for: Real-time and high-frequency trading

---

## Test Failure Troubleshooting

### If Tests Fail

#### Step 1: Verify Config File Exists
```bash
ls -la 03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json
```

**Expected:** File should exist and be readable

#### Step 2: Verify Python Path
```bash
python -c "import src.core.tradingbot.config; print('✅ Config module found')"
```

**Expected:** No import errors

#### Step 3: Check for Missing Dependencies
```bash
python -m pip check
```

**Expected:** No issues

#### Step 4: Run with Full Traceback
```bash
pytest tests/test_issue_23_*.py -v -s --tb=long
```

**Will show:** Complete error details and stack trace

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: src not found` | Run pytest from project root directory |
| `FileNotFoundError: 03_JSON/...` | Check config file path is relative to project root |
| `ImportError: cannot import RegimeDetector` | Ensure `.wsl_venv` is activated |
| `TypeError: unsupported operand type` | Expected in None value tests (handled gracefully) |

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Issue #23
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/test_issue_23_*.py -v
```

### Pre-commit Hook
```bash
#!/bin/bash
pytest tests/test_issue_23_*.py -q
if [ $? -ne 0 ]; then
  echo "Issue #23 tests failed"
  exit 1
fi
```

---

## Continuous Monitoring

### Scheduled Regression Testing
```bash
# Run daily
0 2 * * * cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI && pytest tests/test_issue_23_*.py --tb=short
```

### Watch Mode (Auto-run on file changes)
```bash
pytest-watch tests/test_issue_23_*.py -v -s
```

Install: `pip install pytest-watch`

---

## Test Data

### Indicator Value Ranges Used in Tests

```
ADX14:        15.0 - 35.0
MACD_12_26_9: -10.5 to +10.5
RSI14:        25.0 - 75.0
ATR14:        1.5 - 2.0
BB20:         Upper: 105.0, Middle: 100.0, Lower: 95.0
```

### Regime Triggers Tested

```
Strong Uptrend:
  - ADX > 25 AND MACD > 0

Strong Downtrend:
  - ADX > 25 AND MACD < 0

Range Overbought:
  - ADX < 25 AND RSI > 70

Range Oversold:
  - ADX < 25 AND RSI < 30

Range:
  - ADX < 25 AND RSI between 30-70
```

---

## Related Documentation

- **Main Report:** `tests/ISSUE_23_TEST_REPORT.md`
- **Config File:** `03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json`
- **Simple Tests:** `tests/test_issue_23_regime_fix_simple.py`
- **Comprehensive Tests:** `tests/test_issue_23_comprehensive.py`

---

## Test Maintenance

### Adding New Tests
```python
def test_new_scenario(self, setup_detector):
    """Describe the test scenario."""
    detector = setup_detector

    indicator_values = {
        'adx14': {'value': 30.0},
        'macd_12_26_9': {'MACD_12_26_9': 1.0, ...},
        # ... more indicators
    }

    active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")
    assert 'expected_regime' in [r.id for r in active_regimes]
```

### Updating Test Expectations
1. Edit test expectations in `.py` file
2. Run test to verify new expectation
3. Document why expectation changed
4. Update this guide if behavior changed

---

## Support & Contact

For issues with tests:
1. Check this guide first
2. Review test source files
3. Check config file syntax
4. Review error logs with full traceback (`--tb=long`)
5. Verify project structure matches documentation

---

## Final Verification Checklist

Before considering Issue #23 resolved:

- [ ] Basic tests (2/2) pass
- [ ] Comprehensive tests (18/18) pass
- [ ] Performance tests show <1ms average
- [ ] No "cel-python" errors in logs
- [ ] All field name corrections verified
- [ ] Error handling graceful
- [ ] Coverage report shows 70%+ on detector
- [ ] No other tests broken

---

*Last Updated: 2026-01-22*
*Test Suite Version: 1.0*
*Python: 3.12.3*
*pytest: 9.0.2*
