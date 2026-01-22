# Functional QA Tests - All 13 Closed Issues

Comprehensive functional test suite for OrderPilot-AI covering all 13 closed issues.

## Quick Start

```bash
# Run all tests
pytest test_all_issues.py -v

# Run specific issue tests
pytest test_all_issues.py::TestIssue7ChartUIElements -v

# Run with coverage
pytest test_all_issues.py -v --cov=src/ui
```

## Test Suite Overview

- **Total Tests:** 43
- **Pass Rate:** 100%
- **Execution Time:** ~17 seconds
- **Framework:** Pytest + PyQt6

## Issues Covered

| # | Title | Tests | Status |
|---|-------|-------|--------|
| 1 | Taskbar Display | 3 | PASS |
| 2 | Global Theme | 3 | PASS |
| 3 | Theme Buttons | 3 | PASS |
| 4 | GroupBox Width | 3 | PASS |
| 5 | Watchlist Columns | 3 | PASS |
| 6 | Statistics Bar | 2 | PASS |
| 7 | Chart UI Elements | 4 | PASS |
| 8 | Drawing Toolbar | 2 | PASS |
| 9 | Splash Screen | 3 | PASS |
| 10 | Tab Move | 2 | PASS |
| 11 | Preset Table | 3 | PASS |
| 12 | Icons & Theme | 3 | PASS |
| 13 | Mouse Wheel | 4 | PASS |

## Documentation

- `functional_test_report.md` - Comprehensive test documentation
- `TEST_EXECUTION_SUMMARY.md` - Quick reference summary

## Test Structure

```
tests/qa/
├── __init__.py
├── README.md (this file)
└── test_all_issues.py (1,400+ lines, 43 tests)

Supporting files:
- src/ui/widgets/chart_shared/wheel_event_filter.py (Issue #13)
- docs/qa/functional_test_report.md
- docs/qa/TEST_EXECUTION_SUMMARY.md
```

## Running Tests

### All Tests
```bash
pytest test_all_issues.py -v
```

### Specific Issue (Example: Issue #7)
```bash
pytest test_all_issues.py::TestIssue7ChartUIElements -v
```

### Verbose Output
```bash
pytest test_all_issues.py -vv
```

### Performance Tests Only
```bash
pytest test_all_issues.py::TestPerformance -v
```

### With Coverage Report
```bash
pytest test_all_issues.py -v --cov=src/ui --cov-report=html
```

## Test Categories

### Unit Tests
- Theme system tests (Issues #2, #3, #6, #8)
- Widget property tests (Issues #3, #4)
- Column/table tests (Issues #5, #11)

### Integration Tests
- Cross-issue consistency checks
- Settings persistence validation
- UI hierarchy verification

### Performance Tests
- Table population efficiency
- Settings load time
- Theme color loading

## Requirements

```
pytest >= 7.0
pytest-qt >= 4.2
PyQt6 >= 6.0
```

## Installing Dependencies

```bash
pip install pytest pytest-qt pytest-cov
```

## Test Failures

If tests fail:

1. Check test logs:
   ```bash
   pytest test_all_issues.py -vv -s
   ```

2. Review issue documentation:
   ```
   docs/qa/functional_test_report.md
   ```

3. Verify dependencies:
   ```bash
   pytest --version
   pip list | grep -i pyqt
   ```

4. Check PyQt6 installation:
   ```python
   python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
   ```

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
- name: Run Functional Tests
  run: pytest tests/qa/test_all_issues.py -v
```

## Test Maintenance

### Adding New Tests

1. Create test class: `TestIssueNN`
2. Add test methods: `test_scenario_name`
3. Use fixtures provided in conftest.py or inline
4. Document requirements in docstring
5. Run: `pytest tests/qa/test_all_issues.py::TestIssueNN -v`

### Updating Tests

1. Modify test method
2. Run affected tests
3. Verify no regressions
4. Update documentation

## Key Test Files

### test_all_issues.py (Main Test File)
- 43 test methods
- 15 test classes
- 1,400+ lines of code
- Full PyQt6 widget testing

### wheel_event_filter.py (Utility)
- WheelEventFilter implementation
- Used by Issue #13 tests
- Blocks mouse wheel events on UI controls

## Test Execution Example

```bash
$ pytest tests/qa/test_all_issues.py -v

collected 43 items

tests/qa/test_all_issues.py::TestIssue1TaskbarDisplay::test_chart_window_parent_none PASSED
tests/qa/test_all_issues.py::TestIssue1TaskbarDisplay::test_chart_window_visible_in_taskbar PASSED
tests/qa/test_all_issues.py::TestIssue1TaskbarDisplay::test_get_main_window_with_parent_none PASSED
... (40 more tests)

======================= 43 passed in 17.26s ==========================
```

## Troubleshooting

### "Display not initialized" error
Solution: Use headless test runner or X11 forwarding
```bash
xvfb-run -a pytest test_all_issues.py -v
```

### "QApplication already exists" error
Solution: Tests handle this automatically via fixtures

### "EventFilter not found" error
Solution: Verify wheel_event_filter.py is in correct location:
```
src/ui/widgets/chart_shared/wheel_event_filter.py
```

## Contact & Support

For issues or questions:
1. Review test source code with comments
2. Check functional_test_report.md for details
3. Run failing test with `-vvv` flag
4. See troubleshooting section above

---

**Last Updated:** 2026-01-22
**Status:** Production Ready
**All 13 Issues:** Tested and Validated
