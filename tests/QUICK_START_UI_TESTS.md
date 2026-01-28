# Quick Start: CEL Editor UI Tests

**Issues:** #1 (UI-Duplikate), #5 (Variablenwerte)
**Test Suite:** `tests/ui/test_cel_editor_ui_fixes.py`

---

## 1-Minute Quick Start

### Linux/macOS/WSL

```bash
# Run all tests
./tests/run_ui_tests.sh --all --verbose

# Run specific issue tests
./tests/run_ui_tests.sh --issue1
./tests/run_ui_tests.sh --issue5

# Run with coverage
./tests/run_ui_tests.sh --all --coverage --html
```

### Windows PowerShell

```powershell
# Run all tests
.\tests\run_ui_tests.ps1 -All -Verbose

# Run specific issue tests
.\tests\run_ui_tests.ps1 -Issue1
.\tests\run_ui_tests.ps1 -Issue5

# Run with coverage
.\tests\run_ui_tests.ps1 -All -Coverage -Html
```

---

## Direct pytest Commands

```bash
# Run all tests
pytest tests/ui/test_cel_editor_ui_fixes.py -v

# Run Issue #1 only
pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure -v
pytest tests/ui/test_cel_editor_ui_fixes.py::TestTabFunctionality -v

# Run Issue #5 only
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableValues -v
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableRefresh -v

# Run single test
pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count -v

# Run with keyword filter
pytest tests/ui/test_cel_editor_ui_fixes.py -k "variable" -v
pytest tests/ui/test_cel_editor_ui_fixes.py -k "tab" -v
```

---

## What Gets Tested

### Issue #1: UI-Duplikate (13 tests)

**UI Structure (7 tests):**
- ✅ Exactly 5 central tabs exist
- ✅ Tab titles are correct
- ✅ No duplicate tabs
- ✅ Functions Dock exists with 2 tabs
- ✅ Right Dock has correct structure
- ✅ Left Dock has correct structure

**Tab Functionality (6 tests):**
- ✅ All tabs switch correctly
- ✅ All tabs are accessible
- ✅ All widgets initialized

### Issue #5: Variablenwerte (10 tests)

**Variable Values (7 tests):**
- ✅ Dialog initializes correctly
- ✅ Chart variables have actual values (not None)
- ✅ Bot config variables have values
- ✅ Indicator variables have values
- ✅ Regime variables have values
- ✅ Table displays values correctly
- ✅ Variable types are correct

**Variable Refresh (3 tests):**
- ✅ Refresh updates values
- ✅ "Defined" filter works
- ✅ "Undefined" filter works

---

## Test Results Interpretation

### ✅ SUCCESS (All Passed)

```
tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count PASSED
tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tab_titles PASSED
...
================================== 35 passed in 12.34s ==================================
```

**Action:** No action needed. All fixes are working correctly.

---

### ❌ FAILURE Examples

#### Failure #1: Tab Count Mismatch

```
FAILED tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count
AssertionError: Expected 5 tabs, found 6
```

**Root Cause:** Extra tab added or duplicate tab exists.

**Debug:**
```python
# Add to test file temporarily
def test_debug_tabs(cel_editor_window):
    for i in range(cel_editor_window.central_tabs.count()):
        print(f"Tab {i}: {cel_editor_window.central_tabs.tabText(i)}")
```

**Fix:**
- Remove duplicate tab in `main_window.py`
- Ensure only 5 central tabs: Pattern, Code, Chart, Split, JSON

---

#### Failure #2: None Values in Variables

```
FAILED tests/ui/test_cel_editor_ui_fixes.py::TestVariableValues::test_chart_variables_not_none
AssertionError: Variable 'chart.close' has None value
```

**Root Cause:** ChartWindow data not properly mapped to variables.

**Debug:**
```python
# Add to test file temporarily
def test_debug_chart_vars(qapp, mock_chart_window, mock_bot_config):
    dialog = VariableReferenceDialog(
        chart_window=mock_chart_window,
        bot_config=mock_bot_config
    )

    for var_name, var_info in dialog.variables.items():
        if var_name.startswith('chart.'):
            print(f"{var_name}: {var_info.get('value')}")
```

**Fix:**
- Check `CELContextBuilder.get_available_variables()`
- Verify `chart_window` has data
- Ensure proper attribute access in context builder

---

#### Failure #3: Performance Threshold Exceeded

```
FAILED tests/ui/test_cel_editor_ui_fixes.py::TestPerformance::test_cel_editor_startup_time
AssertionError: CEL Editor took too long to start: 6.23s
```

**Root Cause:** Slow initialization or heavy imports.

**Fix:**
- Profile startup with `pytest --profile`
- Lazy load heavy modules
- Optimize `__init__` methods
- Cache expensive operations

---

## Expected Test Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Total Tests** | 35+ | 35 |
| **Pass Rate** | 100% | TBD |
| **Coverage (UI)** | >90% | TBD |
| **Coverage (Variables)** | >95% | TBD |
| **Startup Time** | <5s | TBD |
| **Variable Load** | <2s | TBD |
| **Tab Switch** | <500ms | TBD |

---

## Manual Verification Checklist

After automated tests pass, manually verify:

### Issue #1: UI-Duplikate

```
[ ] Open CEL Editor
[ ] Count tabs in central widget (should be 5)
[ ] Click Pattern Builder tab
[ ] Click Code Editor tab
[ ] Click Chart View tab
[ ] Click Split View tab
[ ] Click JSON Editor tab
[ ] Open Functions Dock (should have 2 tabs)
[ ] Verify no duplicate UI elements
```

### Issue #5: Variablenwerte

```
[ ] Open CEL Editor
[ ] Menu: Edit > Variables Reference
[ ] Check chart.symbol shows "BTCUSD" (not None)
[ ] Check chart.close shows actual price (not None)
[ ] Check cfg.max_leverage shows 10 (not None)
[ ] Filter: Defined (should show only non-None values)
[ ] Filter: Undefined (should show only None values)
[ ] Copy a variable to clipboard
[ ] Refresh values
```

---

## Troubleshooting

### Problem: "pytest not found"

```bash
# Install pytest
pip install pytest pytest-qt

# Verify installation
pytest --version
```

### Problem: "PyQt6 not found"

```bash
# Install PyQt6
pip install PyQt6

# Verify installation
python -c "import PyQt6; print('OK')"
```

### Problem: "QApplication" errors in tests

```bash
# Install pytest-qt
pip install pytest-qt

# Run with display (Linux)
export DISPLAY=:0
pytest tests/ui/test_cel_editor_ui_fixes.py -v
```

### Problem: Tests timeout or hang

```bash
# Run with timeout
pytest tests/ui/test_cel_editor_ui_fixes.py --timeout=30 -v

# Kill hanging processes
pkill -9 python
```

### Problem: Import errors

```bash
# Add project to PYTHONPATH
export PYTHONPATH="/mnt/d/03_GIT/02_Python/07_OrderPilot-AI:$PYTHONPATH"

# Or run from project root
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
pytest tests/ui/test_cel_editor_ui_fixes.py -v
```

---

## Next Steps

1. **Run tests:**
   ```bash
   ./tests/run_ui_tests.sh --all --verbose
   ```

2. **Review results:**
   - Check console output
   - Review HTML report (if `--html` used)
   - Check coverage report (if `--coverage` used)

3. **Fix failures:**
   - Use debug tests to identify root cause
   - Fix code in `main_window.py` or `variable_reference_dialog.py`
   - Re-run tests to verify fix

4. **Manual testing:**
   - Follow manual checklist above
   - Test with real data (not just mocks)
   - Test on different OS/environments

5. **Document:**
   - Update issue tracker with test results
   - Add notes to `TEST_REPORT_ISSUES_1_AND_5.md`
   - Create PR with test results

---

## Quick Reference Commands

```bash
# Issue #1 tests only
pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure -v
pytest tests/ui/test_cel_editor_ui_fixes.py::TestTabFunctionality -v

# Issue #5 tests only
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableValues -v
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableRefresh -v

# Integration + Edge Cases
pytest tests/ui/test_cel_editor_ui_fixes.py::TestIntegration -v
pytest tests/ui/test_cel_editor_ui_fixes.py::TestEdgeCases -v

# Performance tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestPerformance -v

# With coverage HTML report
pytest tests/ui/test_cel_editor_ui_fixes.py --cov=src/ui --cov-report=html

# Verbose with stack traces
pytest tests/ui/test_cel_editor_ui_fixes.py -vv --tb=long

# Stop on first failure
pytest tests/ui/test_cel_editor_ui_fixes.py -x

# Run in parallel (faster)
pip install pytest-xdist
pytest tests/ui/test_cel_editor_ui_fixes.py -n auto
```

---

## Files Created

| File | Description |
|------|-------------|
| `tests/ui/test_cel_editor_ui_fixes.py` | Complete test suite (35+ tests) |
| `tests/TEST_REPORT_ISSUES_1_AND_5.md` | Detailed test report and documentation |
| `tests/run_ui_tests.sh` | Bash execution script (Linux/macOS/WSL) |
| `tests/run_ui_tests.ps1` | PowerShell execution script (Windows) |
| `tests/QUICK_START_UI_TESTS.md` | This quick start guide |

---

## Support

**Questions?**
- Check `TEST_REPORT_ISSUES_1_AND_5.md` for detailed documentation
- Review test code comments for test logic
- Create GitHub issue for bugs or questions

**Found a bug in tests?**
- Add debug test to isolate issue
- Fix test or report to maintainer
- Update documentation with findings
