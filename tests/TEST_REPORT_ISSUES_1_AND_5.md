# Test Report: CEL Editor UI Fixes (Issues #1 and #5)

**Created:** 2026-01-28
**Test Suite:** `tests/ui/test_cel_editor_ui_fixes.py`
**Issues Covered:** #1 (UI-Duplikate), #5 (Variablenwerte)

---

## Executive Summary

Comprehensive pytest test suite created to validate fixes for:
- **Issue #1:** UI-Duplikate (duplicate UI elements, missing tabs)
- **Issue #5:** Variablenwerte (None values in Variable Reference Dialog)

**Total Test Cases:** 35+
**Coverage Areas:** UI Structure, Tab Functionality, Variable Values, Integration, Edge Cases, Performance

---

## Test Structure

### 1. UI Structure Tests (Issue #1)
**Class:** `TestUIStructure`
**Tests:** 7 test cases

| Test ID | Test Name | Description | Critical |
|---------|-----------|-------------|----------|
| #1.1 | `test_central_tabs_count` | Verify exactly 5 central tabs | ✅ Yes |
| #1.2 | `test_central_tab_titles` | Verify tab titles correct | ✅ Yes |
| #1.3 | `test_no_duplicate_tabs` | No duplicate tabs exist | ✅ Yes |
| #1.4 | `test_functions_dock_exists` | Functions Dock exists | ✅ Yes |
| #1.5 | `test_functions_dock_tabs` | Functions Dock has 2 tabs | ✅ Yes |
| #1.6 | `test_right_dock_structure` | Right Dock has 2 tabs | ⚠️ Medium |
| #1.7 | `test_left_dock_structure` | Left Dock has 2 tabs | ⚠️ Medium |

**Expected Central Tabs:**
1. Pattern Builder
2. Code Editor
3. Chart View
4. Split View
5. JSON Editor

**Expected Functions Dock Tabs:**
1. Command Reference
2. Function Palette

---

### 2. Tab Functionality Tests (Issue #1)
**Class:** `TestTabFunctionality`
**Tests:** 6 test cases

| Test ID | Test Name | Description | Critical |
|---------|-----------|-------------|----------|
| #1.8 | `test_switch_to_pattern_view` | Pattern tab switches correctly | ✅ Yes |
| #1.9 | `test_switch_to_code_view` | Code Editor tab switches | ✅ Yes |
| #1.10 | `test_switch_to_chart_view` | Chart View tab switches | ✅ Yes |
| #1.11 | `test_switch_to_split_view` | Split View tab switches | ✅ Yes |
| #1.12 | `test_all_tabs_accessible` | All tabs clickable | ✅ Yes |
| #1.13 | `test_tab_widgets_not_none` | All widgets initialized | ✅ Yes |

**Tested Interactions:**
- Tab switching via `_switch_view_mode()`
- Action button state synchronization
- Widget initialization verification

---

### 3. Variable Values Tests (Issue #5)
**Class:** `TestVariableValues`
**Tests:** 7 test cases

| Test ID | Test Name | Description | Critical |
|---------|-----------|-------------|----------|
| #5.1 | `test_variable_reference_dialog_initialization` | Dialog initializes | ✅ Yes |
| #5.2 | `test_chart_variables_not_none` | Chart vars have values | ✅ Yes |
| #5.3 | `test_bot_variables_not_none` | Bot config vars have values | ✅ Yes |
| #5.4 | `test_indicator_variables_not_none` | Indicator vars have values | ✅ Yes |
| #5.5 | `test_regime_variables_not_none` | Regime vars have values | ✅ Yes |
| #5.6 | `test_variable_table_display` | Table displays values correctly | ✅ Yes |
| #5.7 | `test_variable_types_correct` | Variable types are correct | ⚠️ Medium |

**Tested Variable Categories:**
- **Chart Variables:** symbol, timeframe, OHLCV
- **Bot Variables:** min_volume_pctl, max_leverage, etc.
- **Indicator Variables:** rsi14, ema21, macd, atr, bb
- **Regime Variables:** current_regime, regime_strength, trend_direction

**Critical Checks:**
- ✅ No `None` values where data is available
- ✅ No string `"None"` in display
- ✅ Correct type mapping (int, float, str, bool, list, dict)

---

### 4. Variable Refresh Tests (Issue #5)
**Class:** `TestVariableRefresh`
**Tests:** 3 test cases

| Test ID | Test Name | Description | Critical |
|---------|-----------|-------------|----------|
| #5.8 | `test_refresh_updates_values` | Refresh reloads variables | ⚠️ Medium |
| #5.9 | `test_filter_defined_variables` | "Defined" filter works | ⚠️ Medium |
| #5.10 | `test_filter_undefined_variables` | "Undefined" filter works | ⚠️ Medium |

**Tested Functionality:**
- Dynamic value updates
- Filter by "Defined" (non-None values)
- Filter by "Undefined" (None values)
- Search functionality

---

### 5. Integration Tests
**Class:** `TestIntegration`
**Tests:** 4 test cases

| Test ID | Test Name | Description | Critical |
|---------|-----------|-------------|----------|
| INT #1 | `test_open_variable_reference_from_menu` | Menu action works | ✅ Yes |
| INT #2 | `test_variable_button_in_toolbar` | Variables button exists | ⚠️ Medium |
| INT #3 | `test_all_ui_elements_visible` | UI elements visible | ✅ Yes |
| INT #4 | `test_no_duplicate_widgets` | No duplicate QTabWidgets | ✅ Yes |

**Integration Points:**
- CEL Editor ↔ Variable Reference Dialog
- Menu actions ↔ Toolbar buttons
- Dock widgets ↔ Central tabs

---

### 6. Edge Case Tests
**Class:** `TestEdgeCases`
**Tests:** 3 test cases

| Test ID | Test Name | Description | Critical |
|---------|-----------|-------------|----------|
| EDGE #1 | `test_variable_dialog_no_data_sources` | Handle missing data sources | ⚠️ Medium |
| EDGE #2 | `test_cel_editor_window_close_cleanup` | Cleanup on close | ⚠️ Medium |
| EDGE #3 | `test_invalid_variable_type_handling` | Handle invalid types | ⚠️ Medium |

**Tested Scenarios:**
- No ChartWindow provided
- No BotConfig provided
- Invalid project_vars_path
- Window close during operations

---

### 7. Performance Tests
**Class:** `TestPerformance`
**Tests:** 3 test cases

| Test ID | Test Name | Description | Threshold |
|---------|-----------|-------------|-----------|
| PERF #1 | `test_cel_editor_startup_time` | CEL Editor startup | < 5.0s |
| PERF #2 | `test_variable_dialog_load_time` | Variable Dialog load | < 2.0s |
| PERF #3 | `test_tab_switch_performance` | Tab switching | < 0.5s avg |

**Performance Benchmarks:**
- CEL Editor startup: **< 5 seconds**
- Variable Reference load: **< 2 seconds**
- Tab switching: **< 500ms average**

---

## Test Execution

### Prerequisites

```bash
# Install dependencies
pip install pytest pytest-qt PyQt6

# Ensure project structure
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
```

### Run All Tests

```bash
# Run complete test suite
pytest tests/ui/test_cel_editor_ui_fixes.py -v

# Run with detailed output
pytest tests/ui/test_cel_editor_ui_fixes.py -v --tb=short

# Run with coverage
pytest tests/ui/test_cel_editor_ui_fixes.py --cov=src/ui --cov-report=html
```

### Run Specific Test Classes

```bash
# Issue #1: UI Structure Tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure -v

# Issue #1: Tab Functionality Tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestTabFunctionality -v

# Issue #5: Variable Values Tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableValues -v

# Issue #5: Variable Refresh Tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableRefresh -v

# Integration Tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestIntegration -v

# Edge Case Tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestEdgeCases -v

# Performance Tests
pytest tests/ui/test_cel_editor_ui_fixes.py::TestPerformance -v
```

### Run Specific Tests

```bash
# Run single test
pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure::test_central_tabs_count -v

# Run multiple tests with keyword filter
pytest tests/ui/test_cel_editor_ui_fixes.py -k "variable" -v
pytest tests/ui/test_cel_editor_ui_fixes.py -k "tab" -v
```

---

## Test Fixtures

### Mock Data Fixtures

```python
@pytest.fixture
def mock_chart_window():
    """Mock ChartWindow with BTCUSD 1h data."""
    # Returns Mock with:
    # - symbol: "BTCUSD"
    # - timeframe: "1h"
    # - OHLCV: open=50000, high=51000, low=49500, close=50500, volume=1000

@pytest.fixture
def mock_bot_config():
    """Mock BotConfig with test parameters."""
    # Returns Mock with:
    # - min_volume_pctl: 50
    # - max_leverage: 10
    # - min_atrp_pct: 0.5
    # - max_atrp_pct: 5.0

@pytest.fixture
def mock_indicators():
    """Mock indicator values."""
    # Returns dict with:
    # - rsi14: {value: 65.5}
    # - ema21: {value: 50200.0}
    # - macd_12_26_9: {value: 150.0, signal: 100.0, histogram: 50.0}
    # - atr14: {value: 500.0}
    # - bb_20_2: {upper: 51500, middle: 50000, lower: 48500, width: 3000}

@pytest.fixture
def mock_regime():
    """Mock regime detection values."""
    # Returns dict with:
    # - current_regime: "R3"
    # - regime_strength: 0.85
    # - trend_direction: "bullish"
```

---

## Expected Test Results

### Issue #1: UI-Duplikate Tests

**Expected Outcome:**
- ✅ All 13 tests PASS
- ✅ No duplicate tabs found
- ✅ All tabs accessible and functional
- ✅ All dock widgets properly initialized

**Critical Failures:**
- ❌ If duplicate tabs exist
- ❌ If tab count != 5 (central tabs)
- ❌ If Functions Dock missing
- ❌ If tab switching doesn't update `current_view_mode`

---

### Issue #5: Variablenwerte Tests

**Expected Outcome:**
- ✅ All 10 tests PASS
- ✅ No `None` values for available data
- ✅ All variable types correct
- ✅ Filters work correctly

**Critical Failures:**
- ❌ If chart variables show "None" when data available
- ❌ If bot config variables are None
- ❌ If indicator values missing
- ❌ If table displays "None" string
- ❌ If "Defined" filter shows None values

---

## Debugging Failed Tests

### Common Issues

#### Issue #1: Tab Count Mismatch

```python
# SYMPTOM: test_central_tabs_count fails
# CAUSE: Extra or missing tabs
# DEBUG:
def test_debug_tab_count(cel_editor_window):
    print(f"\nTotal tabs: {cel_editor_window.central_tabs.count()}")
    for i in range(cel_editor_window.central_tabs.count()):
        print(f"  Tab {i}: {cel_editor_window.central_tabs.tabText(i)}")
```

#### Issue #5: None Values in Variables

```python
# SYMPTOM: test_chart_variables_not_none fails
# CAUSE: Missing data source or incorrect mapping
# DEBUG:
def test_debug_variable_values(qapp, mock_chart_window, mock_bot_config):
    dialog = VariableReferenceDialog(
        chart_window=mock_chart_window,
        bot_config=mock_bot_config
    )

    for var_name, var_info in dialog.variables.items():
        if var_name.startswith('chart.'):
            value = var_info.get('value')
            print(f"{var_name}: {value} (type: {type(value)})")
```

#### Performance Issues

```bash
# Run with profiling
pytest tests/ui/test_cel_editor_ui_fixes.py::TestPerformance -v --profile

# Check slow tests
pytest tests/ui/test_cel_editor_ui_fixes.py --durations=10
```

---

## Test Coverage Goals

### Target Coverage

- **UI Structure:** 100% (all widgets and tabs tested)
- **Variable System:** 95% (all variable categories tested)
- **Integration Points:** 90% (major interactions tested)
- **Edge Cases:** 80% (common failures handled)
- **Performance:** 100% (all critical paths benchmarked)

### Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ui/test_cel_editor_ui_fixes.py --cov=src/ui --cov-report=html

# View report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

---

## Known Limitations

1. **Mock Data Limitations:**
   - ChartWindow mock doesn't include full dataframe
   - Indicator values are static (no live updates)
   - Regime detection simplified

2. **Qt GUI Testing:**
   - Some tests require X11/display server
   - Timing-dependent tests may be flaky
   - Widget visibility tests depend on window manager

3. **Performance Tests:**
   - Thresholds may vary by system
   - Cold start vs warm start differences
   - CI/CD environments may be slower

---

## Continuous Integration

### GitHub Actions Integration

```yaml
# .github/workflows/test_cel_editor_ui.yml
name: CEL Editor UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-qt PyQt6
          pip install -r requirements.txt

      - name: Run Issue #1 Tests
        run: |
          pytest tests/ui/test_cel_editor_ui_fixes.py::TestUIStructure -v
          pytest tests/ui/test_cel_editor_ui_fixes.py::TestTabFunctionality -v

      - name: Run Issue #5 Tests
        run: |
          pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableValues -v
          pytest tests/ui/test_cel_editor_ui_fixes.py::TestVariableRefresh -v

      - name: Run Integration Tests
        run: |
          pytest tests/ui/test_cel_editor_ui_fixes.py::TestIntegration -v
```

---

## Manual Testing Checklist

### Issue #1: UI-Duplikate

- [ ] Open CEL Editor
- [ ] Count central tabs (should be 5)
- [ ] Click each tab (Pattern, Code, Chart, Split, JSON)
- [ ] Verify Functions Dock has 2 tabs (Commands, Functions)
- [ ] Verify Right Dock has 2 tabs (Properties, AI Assistant)
- [ ] Verify Left Dock has 2 tabs (Library, RulePack)
- [ ] Check for duplicate tabs (visual inspection)
- [ ] Test tab switching with keyboard shortcuts

### Issue #5: Variablenwerte

- [ ] Open Variable Reference Dialog (Menu: Edit > Variables Reference)
- [ ] Check chart variables have values (not "None")
- [ ] Check bot config variables have values
- [ ] Add indicators and verify values appear
- [ ] Add regime and verify values appear
- [ ] Test "Defined" filter (should show only non-None)
- [ ] Test "Undefined" filter (should show only None)
- [ ] Test search functionality
- [ ] Test copy to clipboard
- [ ] Test refresh button

---

## Recommendations

### For Developers

1. **Run tests before committing:**
   ```bash
   pytest tests/ui/test_cel_editor_ui_fixes.py -v
   ```

2. **Add tests for new UI features:**
   - Always test tab count after adding tabs
   - Test variable values for new data sources
   - Test performance for heavy operations

3. **Use fixtures for consistent mocks:**
   - Reuse `mock_chart_window` for chart tests
   - Reuse `mock_bot_config` for config tests
   - Create new fixtures for new components

### For QA

1. **Automated testing:**
   - Run full test suite daily
   - Run critical tests on every PR
   - Track test failures in issue tracker

2. **Manual testing:**
   - Follow manual checklist weekly
   - Test on different OS (Windows, Linux, macOS)
   - Test with real data (not just mocks)

3. **Regression testing:**
   - Re-run Issue #1 tests after UI changes
   - Re-run Issue #5 tests after variable system changes
   - Re-run integration tests after major refactoring

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-01-28 | Initial test suite creation | OrderPilot-AI Dev Team |

---

## Contact

**Issues/Questions:**
- GitHub Issues: [OrderPilot-AI Issues](https://github.com/your-org/orderpilot-ai/issues)
- Email: dev@orderpilot-ai.com

**Test Maintainer:**
- Claude Code / OrderPilot-AI Development Team
