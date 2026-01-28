# CEL Editor UI Test Suite Overview

**Test Suite:** Issues #1 and #5 Comprehensive Testing
**Created:** 2026-01-28
**Status:** ✅ Ready for Execution

---

## 📊 Test Statistics

| Metric | Value |
|--------|-------|
| **Total Test Cases** | 35+ |
| **Test Classes** | 7 |
| **Critical Tests** | 20 |
| **Medium Priority Tests** | 12 |
| **Low Priority Tests** | 3 |
| **Expected Coverage** | >90% |
| **Estimated Runtime** | ~10-15 seconds |

---

## 🎯 Test Coverage Breakdown

### Issue #1: UI-Duplikate (13 tests)

```
TestUIStructure (7 tests)           [Critical: 5, Medium: 2]
├── test_central_tabs_count         ✅ CRITICAL
├── test_central_tab_titles         ✅ CRITICAL
├── test_no_duplicate_tabs          ✅ CRITICAL
├── test_functions_dock_exists      ✅ CRITICAL
├── test_functions_dock_tabs        ✅ CRITICAL
├── test_right_dock_structure       ⚠️  MEDIUM
└── test_left_dock_structure        ⚠️  MEDIUM

TestTabFunctionality (6 tests)      [Critical: 5, Medium: 1]
├── test_switch_to_pattern_view     ✅ CRITICAL
├── test_switch_to_code_view        ✅ CRITICAL
├── test_switch_to_chart_view       ✅ CRITICAL
├── test_switch_to_split_view       ✅ CRITICAL
├── test_all_tabs_accessible        ✅ CRITICAL
└── test_tab_widgets_not_none       ⚠️  MEDIUM
```

### Issue #5: Variablenwerte (10 tests)

```
TestVariableValues (7 tests)        [Critical: 5, Medium: 2]
├── test_variable_reference_dialog_initialization  ✅ CRITICAL
├── test_chart_variables_not_none                 ✅ CRITICAL
├── test_bot_variables_not_none                   ✅ CRITICAL
├── test_indicator_variables_not_none             ✅ CRITICAL
├── test_regime_variables_not_none                ✅ CRITICAL
├── test_variable_table_display                   ⚠️  MEDIUM
└── test_variable_types_correct                   ⚠️  MEDIUM

TestVariableRefresh (3 tests)       [Medium: 3]
├── test_refresh_updates_values     ⚠️  MEDIUM
├── test_filter_defined_variables   ⚠️  MEDIUM
└── test_filter_undefined_variables ⚠️  MEDIUM
```

### Additional Test Suites (12 tests)

```
TestIntegration (4 tests)           [Critical: 3, Medium: 1]
├── test_open_variable_reference_from_menu  ✅ CRITICAL
├── test_variable_button_in_toolbar         ⚠️  MEDIUM
├── test_all_ui_elements_visible            ✅ CRITICAL
└── test_no_duplicate_widgets               ✅ CRITICAL

TestEdgeCases (3 tests)             [Medium: 3]
├── test_variable_dialog_no_data_sources    ⚠️  MEDIUM
├── test_cel_editor_window_close_cleanup    ⚠️  MEDIUM
└── test_invalid_variable_type_handling     ⚠️  MEDIUM

TestPerformance (3 tests)           [Critical: 3]
├── test_cel_editor_startup_time    ✅ CRITICAL (<5s)
├── test_variable_dialog_load_time  ✅ CRITICAL (<2s)
└── test_tab_switch_performance     ✅ CRITICAL (<500ms)
```

---

## 🚦 Test Execution Priority

### Priority 1: Critical Path (20 tests)

**Must pass before deployment.**

```bash
# Run critical tests only
pytest tests/ui/test_cel_editor_ui_fixes.py -m critical -v

# Or run specific critical test classes
pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count -v
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableValues::test_chart_variables_not_none -v
```

**Expected Result:** 20/20 PASSED

---

### Priority 2: Important Tests (12 tests)

**Should pass for production quality.**

```bash
# Run medium priority tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableRefresh -v
pytest tests/ui/test_cel_editor_ui_fixes.py::TestEdgeCases -v
```

**Expected Result:** 12/12 PASSED

---

### Priority 3: Nice-to-Have (3 tests)

**Optional, but recommended.**

```bash
# Run low priority tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestIntegration::test_variable_button_in_toolbar -v
```

**Expected Result:** 3/3 PASSED

---

## 📋 Test Execution Checklist

### Pre-Test Setup

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pytest`, `pytest-qt`, `PyQt6`)
- [ ] Project PYTHONPATH configured
- [ ] Qt display server available (Linux: `export DISPLAY=:0`)
- [ ] No hanging Python processes

### Test Execution

- [ ] Run full test suite: `./tests/run_ui_tests.sh --all --verbose`
- [ ] Review console output for failures
- [ ] Check coverage report (if enabled)
- [ ] Review HTML report (if enabled)

### Post-Test Analysis

- [ ] All critical tests passed (20/20)
- [ ] All medium tests passed (12/12)
- [ ] Performance thresholds met
- [ ] No warnings or deprecations
- [ ] Coverage >90% for UI and variables modules

### Manual Verification

- [ ] CEL Editor opens without errors
- [ ] All 5 central tabs visible and functional
- [ ] Variable Reference Dialog shows actual values (not None)
- [ ] No duplicate UI elements
- [ ] Tab switching works smoothly

---

## 🛠️ Test Fixture Reference

### Available Fixtures

```python
@pytest.fixture
def qapp(qtbot):
    """QApplication instance for Qt tests."""

@pytest.fixture
def cel_editor_window(qtbot):
    """CEL Editor Window instance."""

@pytest.fixture
def mock_chart_window():
    """Mock ChartWindow with BTCUSD 1h data."""
    # OHLCV: open=50000, high=51000, low=49500, close=50500, volume=1000

@pytest.fixture
def mock_bot_config():
    """Mock BotConfig with test parameters."""
    # max_leverage=10, min_volume_pctl=50, etc.

@pytest.fixture
def mock_indicators():
    """Mock indicator values."""
    # rsi14, ema21, macd, atr, bb_20_2

@pytest.fixture
def mock_regime():
    """Mock regime detection values."""
    # current_regime="R3", regime_strength=0.85, trend_direction="bullish"
```

### Usage Example

```python
def test_my_feature(
    qapp,
    cel_editor_window,
    mock_chart_window,
    mock_bot_config,
    mock_indicators,
    mock_regime
):
    # Your test code here
    pass
```

---

## 📈 Test Metrics & KPIs

### Code Coverage Targets

| Module | Target | Current |
|--------|--------|---------|
| `main_window.py` | >95% | TBD |
| `variable_reference_dialog.py` | >95% | TBD |
| `cel_editor_widget.py` | >90% | TBD |
| `context_builder.py` | >90% | TBD |
| **Overall UI Module** | >90% | TBD |
| **Overall Variables Module** | >95% | TBD |

### Performance Benchmarks

| Operation | Target | Current |
|-----------|--------|---------|
| CEL Editor Startup | <5s | TBD |
| Variable Dialog Load | <2s | TBD |
| Tab Switch (avg) | <500ms | TBD |
| Variable Refresh | <1s | TBD |

### Test Execution Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Test Run Time | <30s | TBD |
| Pass Rate | 100% | TBD |
| Flaky Tests | 0 | TBD |
| Test Coverage | >90% | TBD |

---

## 🐛 Known Issues & Limitations

### Test Limitations

1. **Mock Data Simplifications:**
   - ChartWindow mock uses static OHLCV data
   - Indicators don't update dynamically
   - Regime detection is simplified

2. **Qt GUI Testing:**
   - Requires X11/display server on Linux
   - Some timing-dependent tests may be flaky
   - Widget visibility tests depend on window manager

3. **Performance Tests:**
   - Thresholds may vary by system specs
   - CI/CD environments typically slower
   - Cold start vs warm start differences

### Workarounds

```bash
# For headless testing (Linux CI/CD)
xvfb-run pytest tests/ui/test_cel_editor_ui_fixes.py -v

# For flaky tests, increase timeouts
pytest tests/ui/test_cel_editor_ui_fixes.py --timeout=60 -v

# For debug mode
pytest tests/ui/test_cel_editor_ui_fixes.py -vv --tb=long --pdb
```

---

## 🔧 Debugging Failed Tests

### Debug Workflow

1. **Identify failing test:**
   ```bash
   pytest tests/ui/test_cel_editor_ui_fixes.py -v
   # Note which test failed
   ```

2. **Run failing test in isolation:**
   ```bash
   pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count -vv
   ```

3. **Add debug output:**
   ```python
   def test_debug_tabs(cel_editor_window):
       print(f"\nTotal tabs: {cel_editor_window.central_tabs.count()}")
       for i in range(cel_editor_window.central_tabs.count()):
           print(f"  Tab {i}: {cel_editor_window.central_tabs.tabText(i)}")
   ```

4. **Use pytest debugger:**
   ```bash
   pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count -vv --pdb
   ```

5. **Fix root cause in source code**

6. **Re-run test to verify fix:**
   ```bash
   pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count -v
   ```

### Common Failure Patterns

| Symptom | Likely Cause | Debug Command |
|---------|--------------|---------------|
| Tab count mismatch | Duplicate/missing tab | `print(central_tabs.count())` |
| None values in variables | Missing data source | `print(variables)` |
| Performance timeout | Heavy imports | `pytest --profile` |
| Widget not found | Incorrect object name | `print(findChildren(QWidget))` |
| Import error | Missing dependency | `pip list | grep pytest` |

---

## 📚 Related Documentation

- **Test Report:** `tests/TEST_REPORT_ISSUES_1_AND_5.md`
- **Quick Start:** `tests/QUICK_START_UI_TESTS.md`
- **Test Suite:** `tests/ui/test_cel_editor_ui_fixes.py`
- **Run Scripts:**
  - Bash: `tests/run_ui_tests.sh`
  - PowerShell: `tests/run_ui_tests.ps1`

---

## 🚀 Quick Commands Reference

```bash
# === BASIC EXECUTION ===
pytest tests/ui/test_cel_editor_ui_fixes.py -v

# === BY ISSUE ===
pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure -v          # Issue #1
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableValues -v       # Issue #5

# === WITH COVERAGE ===
pytest tests/ui/test_cel_editor_ui_fixes.py --cov=src/ui --cov-report=html

# === WITH HTML REPORT ===
pytest tests/ui/test_cel_editor_ui_fixes.py --html=tests/report.html --self-contained-html

# === PARALLEL EXECUTION (faster) ===
pip install pytest-xdist
pytest tests/ui/test_cel_editor_ui_fixes.py -n auto

# === STOP ON FIRST FAILURE ===
pytest tests/ui/test_cel_editor_ui_fixes.py -x

# === VERBOSE WITH STACK TRACES ===
pytest tests/ui/test_cel_editor_ui_fixes.py -vv --tb=long

# === USING HELPER SCRIPTS ===
./tests/run_ui_tests.sh --all --verbose --coverage --html    # Linux/macOS/WSL
.\tests\run_ui_tests.ps1 -All -Verbose -Coverage -Html       # Windows
```

---

## ✅ Success Criteria

**All tests pass when:**

1. ✅ CEL Editor has exactly 5 central tabs (no duplicates)
2. ✅ All tabs are accessible and functional
3. ✅ Functions Dock has 2 tabs (Commands, Functions)
4. ✅ Variable Reference Dialog shows actual values (not None)
5. ✅ All variable categories (Chart, Bot, Indicators, Regime) populated
6. ✅ Performance thresholds met (<5s startup, <2s variable load, <500ms tab switch)
7. ✅ No import errors or dependency issues
8. ✅ No warnings or deprecations
9. ✅ Code coverage >90%
10. ✅ Manual verification confirms automated test results

**Ready for deployment when:** All 35+ tests PASS + manual verification complete

---

## 📞 Support & Contacts

**Questions?**
- Check documentation in `tests/` directory
- Review test code comments for test logic
- Create GitHub issue for bugs or questions

**Test Maintainer:**
- Claude Code / OrderPilot-AI Development Team
- Created: 2026-01-28

---

**Last Updated:** 2026-01-28
**Status:** ✅ Ready for Execution
