# Migration Testing Quick Reference

Quick reference for running and interpreting migration tests.

---

## Quick Commands

### Run All Tests
```bash
pytest tests/core/tradingbot/test_migration_suite.py -v
```

### Run Specific Test Type
```bash
# Analysis tests only (should all pass)
pytest tests/core/tradingbot/test_migration_suite.py -k "test_strategy_can_be_analyzed" -v

# JSON generation tests (should all pass)
pytest tests/core/tradingbot/test_migration_suite.py -k "test_strategy_can_be_converted_to_json" -v

# Validation tests (6/9 pass)
pytest tests/core/tradingbot/test_migration_suite.py -k "test_generated_config_is_valid" -v

# Equivalence tests (0/9 pass - known issue)
pytest tests/core/tradingbot/test_migration_suite.py -k "test_converted_strategy_is_equivalent" -v
```

### Run Single Strategy
```bash
pytest tests/core/tradingbot/test_migration_suite.py::TestIndividualStrategyMigration::test_converted_strategy_is_equivalent[trend_following_conservative] -v
```

### Quick Summary
```bash
pytest tests/core/tradingbot/test_migration_suite.py -q --tb=no
```

---

## Understanding Test Results

### ✅ Expected Passes (29 tests)

1. **All Analysis Tests** (9/9)
   - All strategies can be analyzed
   - StrategyAnalyzer works correctly

2. **All JSON Generation Tests** (9/9)
   - All strategies generate valid JSON
   - JSONConfigGenerator works correctly

3. **Most Validation Tests** (6/9)
   - 6 strategies pass Pydantic validation
   - 3 fail due to unknown indicator types

### ❌ Expected Failures (17 tests)

1. **Validation Failures** (3/9)
   - mean_reversion_bb
   - breakout_volatility
   - sideways_range_bounce
   - **Reason:** Unknown custom indicator types

2. **All Equivalence Tests** (9/9)
   - **Reason:** Indicator ID mismatch (adx14 ≠ adx)

3. **Cascading Failures** (5)
   - Batch/metrics/report tests fail due to individual failures

---

## Quick Diagnosis

### If a strategy fails validation:
```
FAILED test_generated_config_is_valid[strategy_name]
  ConfigLoadError: Pydantic validation failed
```
**Cause:** Unknown custom indicator type
**Fix Needed:** Phase 5.1 - Add custom indicator support

### If a strategy fails equivalence:
```
FAILED test_converted_strategy_is_equivalent[strategy_name]
  Similarity: 61.0%
  Entry match: False
```
**Cause:** Indicator ID mismatch
**Fix Needed:** Phase 5.1 - Implement indicator ID mapping

### If analysis fails:
```
FAILED test_strategy_can_be_analyzed[strategy_name]
```
**Cause:** Bug in StrategyAnalyzer
**Fix Needed:** Immediate - Critical bug

---

## Test Status Summary

```
┌──────────────────────────────┬─────────┬─────────┬────────────────┐
│ Test Category                │ Passed  │ Failed  │ Status         │
├──────────────────────────────┼─────────┼─────────┼────────────────┤
│ Strategy Analysis            │  9/9    │   0/9   │ ✅ All Working │
│ JSON Generation              │  9/9    │   0/9   │ ✅ All Working │
│ Config Validation            │  6/9    │   3/9   │ ⚠️  67% Pass   │
│ Strategy Equivalence         │  0/9    │   9/9   │ ❌ 0% Pass     │
│ Batch/Metrics/Reports        │  5/10   │   5/10  │ ⚠️  50% Pass   │
├──────────────────────────────┼─────────┼─────────┼────────────────┤
│ TOTAL                        │ 29/46   │  17/46  │ ⚠️  63% Pass   │
└──────────────────────────────┴─────────┴─────────┴────────────────┘
```

---

## Known Issues

### Issue #1: Indicator ID Mismatch (All 9 Strategies)
**Impact:** Equivalence tests fail
**Severity:** Critical
**Examples:**
- JSON: `adx14` vs Hardcoded: `adx`
- JSON: `rsi14` vs Hardcoded: `rsi_14`
- JSON: `sma20` vs Hardcoded: `sma_20`

### Issue #2: Unknown Custom Indicators (3 Strategies)
**Impact:** Validation tests fail
**Severity:** Critical
**Affected:**
- mean_reversion_bb (bb_pct)
- breakout_volatility (atr_ratio)
- sideways_range_bounce (bb_pct, stoch_k)

### Issue #3: Regime Mapping (All Strategies)
**Impact:** Lower similarity scores
**Severity:** Minor
**Example:**
- JSON: `trend_following_regime`
- Hardcoded: `trend_up`, `trend_down`

---

## Success Criteria

### Phase 5.3 (Test Suite) - ✅ COMPLETE
- [x] 46 automated tests implemented
- [x] All 9 strategies tested
- [x] Bugs discovered and documented
- [x] <30s execution time

### Phase 5.4 (Bug Fixes) - ⏳ PENDING
- [ ] All validation tests pass (9/9)
- [ ] All equivalence tests pass (9/9)
- [ ] >95% similarity for all strategies
- [ ] 46/46 tests pass

---

## Quick Troubleshooting

### Tests fail with import errors
```bash
# Ensure virtual environment is activated
source .wsl_venv/bin/activate  # WSL
source .venv/bin/activate       # Native Linux/Mac
.venv\Scripts\activate          # Windows
```

### Tests fail with "module not found"
```bash
# Install test dependencies
pip install pytest pytest-cov
```

### Want to see detailed comparison results
```bash
# Run with verbose output and short traceback
pytest tests/core/tradingbot/test_migration_suite.py -v --tb=short

# Or use the CLI compare command directly
tradingbot-config compare configs/trend.json trend_following_conservative -v
```

### Want to generate a migration report
```python
# See TestMigrationReports class in test_migration_suite.py
# Example output format:
{
    "timestamp": "2024-01-18T00:00:00",
    "strategies": {
        "trend_following_conservative": {
            "equivalent": false,
            "similarity": 0.61,
            "entry_match": false,
            "exit_match": false,
            "risk_match": true,
            "warnings": ["Major differences detected"]
        }
    }
}
```

---

## Next Steps After Phase 5.3

1. **Fix Phase 5.1 Bugs** (Priority 1)
   - Implement indicator ID mapping
   - Add custom indicator support
   - Standardize regime naming

2. **Re-run Tests** (Priority 2)
   ```bash
   pytest tests/core/tradingbot/test_migration_suite.py -v
   ```
   Target: 46/46 tests pass

3. **Generate Final Report** (Priority 3)
   ```bash
   pytest tests/core/tradingbot/test_migration_suite.py \
     --junit-xml=migration_report.xml \
     --html=migration_report.html
   ```

4. **Deploy to Production** (After 100% pass rate)
   - All strategies validated
   - All equivalence verified
   - Migration complete

---

**Phase 5.3 Status:** ✅ COMPLETE
**Migration Status:** ⏳ PENDING (Awaiting Phase 5.4 bug fixes)
