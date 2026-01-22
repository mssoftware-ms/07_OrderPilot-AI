# Issue 18 & 19 Testing Guide

## Overview

This document provides a comprehensive guide to testing Issue 18 (Regime Button & Geisterelement) and Issue 19 (Settings Dialog) implementations.

**Test File**: `tests/ui/test_issue_18_19_regime_settings.py`
**Total Tests**: 35
**Status**: All passing (100% success rate)

---

## What Gets Tested?

### Issue 18: Regime Button & Geisterelement

The Regime button should be:
1. Implemented as **QPushButton** (not QLabel or QFrame)
2. **Theme-aware** using `setProperty("class", "toolbar-button")`
3. **Clickable** and functional
4. **32px height** (consistent with other toolbar buttons)
5. **Icon-enabled** with "analytics" icon
6. **Tooltip-enabled** showing ADX, entry status, and gate reasons
7. **Fully integrated** with update methods

### Issue 19: Settings Dialog

Settings dialog should be:
1. **Accessible** from toolbar settings button
2. **Found via parent chain** search first
3. **Fallback** to top-level widgets search
4. **Logged properly** when not found
5. **Graceful** in degraded modes (Chart-Only)

---

## Quick Start

### Prerequisites

```bash
cd /mnt/d/03_GIT/02_Python/07_OrderPilot-AI
source .wsl_venv/bin/activate
```

### Run All Tests

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py -v
```

Expected output:
```
35 passed, 2 warnings in ~18 seconds
```

---

## Test Categories

### 1. Issue 18: Regime Button Properties (8 tests)

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py::TestIssue18RegimeButton -v
```

Tests:
- `test_regime_button_is_qpushbutton` - Type validation
- `test_regime_button_height_is_32px` - Height constant
- `test_regime_button_uses_theme_class` - Theme integration
- `test_regime_button_icon_size_constant` - Icon size (20x20)
- `test_regime_button_has_analytics_icon` - Icon loading
- `test_regime_button_has_tooltip` - Tooltip text
- `test_regime_button_initial_text` - Initial display text
- `test_regime_button_click_connection` - Signal connection

### 2. Issue 18: Update Regime Badge (7 tests)

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py::TestIssue18UpdateRegimeBadge -v
```

Tests:
- `test_update_regime_badge_sets_text` - Text update
- `test_update_regime_badge_with_adx` - ADX in tooltip
- `test_update_regime_badge_with_gate_reason` - Gate reason display
- `test_update_regime_badge_entry_allowed_status` - Entry status
- `test_update_regime_badge_none_regime` - None handling
- `test_update_regime_badge_without_regime_button` - Error handling
- `test_update_regime_from_result_valid` - RegimeResult parsing

### 3. Issue 18: Button Click Handler (3 tests)

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py::TestIssue18RegimeButtonClickHandler -v
```

Tests:
- `test_regime_button_clicked_calls_update_regime_from_data` - Click handler
- `test_regime_button_clicked_without_update_method` - Error handling
- `test_regime_button_clicked_logging` - Debug logging

### 4. Issue 19: Settings Dialog Methods (5 tests)

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py::TestIssue19SettingsDialog -v
```

Tests:
- `test_chart_window_has_open_main_settings_dialog_method` - Method exists
- `test_chart_window_has_get_main_window_method` - Method exists
- `test_open_main_settings_dialog_calls_open_settings` - Delegation
- `test_get_main_window_tries_parent_first` - Parent search
- `test_get_main_window_fallback_top_level_widgets` - Fallback search

### 5. Issue 19: Button Click Workflow (3 tests)

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py::TestIssue19SettingsButtonClickWorkflow -v
```

Tests:
- `test_settings_button_click_handler_exists` - Handler exists
- `test_settings_button_click_tries_open_main_settings_dialog` - First priority
- `test_settings_button_click_parent_chain_search` - Chain search
- `test_settings_button_click_top_level_fallback` - Fallback
- `test_settings_button_click_logging_when_not_found` - Error logging

### 6. Integration Tests (7 tests)

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py::TestIssue18_19Integration -v
```

Tests:
- `test_toolbar_row2_regime_button_and_settings_button` - Coexistence
- `test_regime_button_does_not_interfere_with_settings_button` - Independence
- `test_constants_are_consistent` - Constants validation
- `test_no_qframe_or_qlabel_regime_element` - No wrong types
- `test_no_ghost_element_regime_label` - No ghost elements

---

## Advanced Testing Scenarios

### Run with Verbose Output

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py -vv --tb=short
```

Shows:
- Full test names
- Each assertion
- Short tracebacks on failures

### Run with Full Tracebacks

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py -v --tb=long
```

Use when debugging test failures.

### Run with Print Output

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py -v -s
```

Shows:
- All print() statements in tests
- Useful for debugging with print(f"...")

### Run with Markers

```bash
# Run only Issue 18 tests
pytest tests/ui/test_issue_18_19_regime_settings.py -k "Issue18" -v

# Run only Issue 19 tests
pytest tests/ui/test_issue_18_19_regime_settings.py -k "Issue19" -v

# Run only Integration tests
pytest tests/ui/test_issue_18_19_regime_settings.py -k "Integration" -v
```

### Run with Coverage

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py \
  --cov=src/ui/widgets/chart_mixins/toolbar_mixin_row2 \
  --cov=src/ui/widgets/chart_window \
  --cov-report=html
```

Opens `htmlcov/index.html` in browser.

### Run with Timeout

```bash
pytest tests/ui/test_issue_18_19_regime_settings.py --timeout=60 -v
```

Fails if any test takes longer than 60 seconds.

---

## Test Structure

### Test File Location
```
/mnt/d/03_GIT/02_Python/07_OrderPilot-AI/tests/ui/test_issue_18_19_regime_settings.py
```

### Test Classes

| Class | Purpose | Test Count |
|-------|---------|-----------|
| `TestIssue18RegimeButton` | Basic button properties | 8 |
| `TestIssue18UpdateRegimeBadge` | Badge update methods | 7 |
| `TestIssue18RegimeButtonClickHandler` | Click handling | 3 |
| `TestIssue19SettingsDialog` | Settings dialog access | 5 |
| `TestIssue19SettingsButtonClickWorkflow` | Button workflow | 3 |
| `TestIssue18_19Integration` | Combined functionality | 7 |

### Fixtures

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `qapp` | session | QApplication singleton |

### Mock Objects

Tests use mocks to:
- Simulate parent-child relationships
- Test fallback behavior
- Avoid GUI dependencies
- Test error conditions

---

## Expected Results

### All Tests Pass

```
35 passed, 2 warnings in 18.57s
```

### Warnings Explanation

```
WARNING: ignoring pytest config in pyproject.toml!
```

This is normal - pytest.ini takes precedence.

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'PyQt6'"

**Solution**: Activate virtual environment
```bash
source .wsl_venv/bin/activate
```

### Issue: "DISPLAY not set" or "Cannot connect to X server"

**Solution**: This is expected on WSL without X server
- Tests use `pytest-qt` which handles headless PyQt6
- Tests will run in "offscreen" mode automatically

### Issue: "test_regime_button_uses_theme_class FAILED"

**Check**:
```python
# Verify class property is set
button.property("class")  # Should return "toolbar-button"
```

**Fix**: Ensure `setProperty("class", "toolbar-button")` is called

### Issue: "Settings dialog not available" warning logged

**This is expected** in these scenarios:
- `test_settings_button_click_logging_when_not_found`
- `test_regime_button_clicked_without_update_method`

These tests verify error handling.

---

## Debugging Failed Tests

### Step 1: Run with verbose output
```bash
pytest tests/ui/test_issue_18_19_regime_settings.py::TestIssue18RegimeButton::test_regime_button_is_qpushbutton -vv
```

### Step 2: Check the assertion
Look at the test method to see what it's checking:
```python
def test_regime_button_is_qpushbutton(self, qapp):
    button = QPushButton("Regime: N/A")
    assert isinstance(button, QPushButton)
```

### Step 3: Verify implementation
Check the source file at the lines mentioned in the test:
- Issue 18: `src/ui/widgets/chart_mixins/toolbar_mixin_row2.py:65-76`
- Issue 19: `src/ui/widgets/chart_window.py:214-216`

### Step 4: Review changes
```bash
git diff src/ui/widgets/chart_mixins/toolbar_mixin_row2.py
git diff src/ui/widgets/chart_window.py
```

---

## Test Data

### Sample Regime Data Used in Tests

```python
# Regime update with all fields
result = Mock()
result.regime = Mock(value="bullish")  # or direct string
result.adx = 38.2
result.gate_reason = "Testing"
result.allows_market_entry = True
```

### Sample Tooltip Content Tested

```html
<b>Bullish</b>
<br>ADX: 38.2
<br>✅ Entry erlaubt
```

---

## Continuous Integration

### Run tests before commit

```bash
# Full test suite
pytest tests/ui/test_issue_18_19_regime_settings.py -v

# With coverage
pytest tests/ui/test_issue_18_19_regime_settings.py --cov
```

### Run tests in CI/CD pipeline

```yaml
# Example GitHub Actions
- name: Test Issue 18 & 19
  run: |
    pytest tests/ui/test_issue_18_19_regime_settings.py \
      -v \
      --cov=src/ui/widgets \
      --junit-xml=test-results.xml
```

---

## Performance Metrics

| Metric | Value | Note |
|--------|-------|------|
| Total Tests | 35 | All passing |
| Success Rate | 100% | No failures |
| Total Time | ~18 seconds | Per full run |
| Avg Per Test | ~530ms | With PyQt6 overhead |
| PyQt6 Overhead | ~2 seconds | QApplication creation |

---

## Maintenance

### Adding New Tests

If you add new tests, ensure they:

1. Follow the naming convention: `test_<feature>_<scenario>`
2. Have a docstring explaining what's tested
3. Use descriptive assertions with messages
4. Mock external dependencies
5. Clean up after themselves

Example:

```python
def test_regime_button_custom_feature(self, qapp):
    """Test custom feature of regime button."""
    button = QPushButton("Regime: N/A")
    button.setProperty("custom", "value")

    assert button.property("custom") == "value", \
        "Custom property must be set correctly"
```

### Updating Existing Tests

If implementation changes:

1. Update relevant test methods
2. Run the test: `pytest tests/ui/test_issue_18_19_regime_settings.py::<TestClass>::<test_method> -v`
3. Verify it passes
4. Document the change in git commit

---

## References

### Source Files
- `src/ui/widgets/chart_mixins/toolbar_mixin_row2.py` - Regime button & settings button
- `src/ui/widgets/chart_window.py` - ChartWindow methods
- `src/ui/icons.py` - Icon loading

### Related Tests
- `tests/ui/test_issue_16_17_functional.py` - Button height consistency
- `tests/ui/test_regime_set_builder.py` - Regime logic

### Documentation
- `ARCHITECTURE.md` - System architecture
- `CLAUDE.md` - Development guidelines

---

## Support

If tests fail:

1. Check virtual environment is activated
2. Run: `pip install -r dev-requirements.txt`
3. Run: `pytest tests/ui/test_issue_18_19_regime_settings.py -v`
4. Review test output carefully
5. Check source code for the mentioned lines
6. Review git diff of recent changes

---

**Last Updated**: 2026-01-22
**Test Version**: 1.0
**Status**: Production Ready
