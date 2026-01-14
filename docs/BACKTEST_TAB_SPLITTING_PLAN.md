# BACKTEST_TAB.PY SPLITTING PLAN
## Detailed Refactoring Strategy - 3,175 LOC → 8 Modules

---

## 📊 CURRENT STATE ANALYSIS

**File:** `src/ui/widgets/bitunix_trading/backtest_tab.py`
- **Total LOC:** 4,176 (3,175 productive)
- **Classes:** 2 (`BatchTestWorker`, `BacktestTab`)
- **Methods:** 55 total (2 in Worker, 53 in BacktestTab)
- **Violation:** 5.3x over 600 LOC limit

### 🔥 CRITICAL COMPLEXITY ISSUES

**Monster Methods (>100 LOC):**
1. `_get_signal_callback` - **394 LOC** (CC=55) - CRITICAL
2. `get_parameter_specification` - **298 LOC**
3. `_create_compact_button_row` - **189 LOC**
4. `_on_derive_variant_clicked` - **188 LOC**
5. `_create_batch_tab` - **185 LOC**
6. `_on_load_template_clicked` - **155 LOC**
7. `_create_results_tab` - **125 LOC**
8. `_on_save_template_clicked` - **123 LOC**
9. `generate_ai_test_variants` - **113 LOC**
10. `_convert_v2_to_parameters` - **111 LOC**

---

## 🎯 SPLITTING STRATEGY

### MODULE ORGANIZATION (8 Modules)

```
src/ui/widgets/bitunix_trading/
├── backtest_tab.py (250 LOC)
│   └── Main widget, tab coordination, signals
│
├── backtest_tab_worker.py (150 LOC)
│   └── BatchTestWorker class (background processing)
│
├── backtest_tab_ui_setup.py (400 LOC)
│   └── Setup tab UI (_create_setup_tab + helpers)
│
├── backtest_tab_ui_execution.py (350 LOC)
│   └── Execution tab UI (_create_execution_tab + fees/slippage)
│
├── backtest_tab_ui_results.py (450 LOC)
│   └── Results tab UI (_create_results_tab + all _update_*_table methods)
│
├── backtest_tab_ui_batch.py (500 LOC)
│   └── Batch/WF tab UI (_create_batch_tab + batch callbacks)
│
├── backtest_tab_config.py (550 LOC)
│   └── Config management (engine configs, templates, settings load/save)
│
└── backtest_tab_signal.py (450 LOC)
    └── Signal callback + export utilities (refactor _get_signal_callback!)
```

---

## 📋 DETAILED MODULE BREAKDOWN

### 1. `backtest_tab.py` (Main Widget - 250 LOC)

**Responsibility:** Main widget class, tab coordination, signal definitions

**Contents:**
- Class definition & signals
- `__init__` (simplified, delegates to sub-modules)
- `_setup_ui` (creates QTabWidget, delegates tab creation)
- `set_history_manager`
- `_connect_signals` (connects sub-module signals)
- Signal emissions

**Imports from sub-modules:**
```python
from .backtest_tab_worker import BatchTestWorker
from .backtest_tab_ui_setup import BacktestSetupTabUI
from .backtest_tab_ui_execution import BacktestExecutionTabUI
from .backtest_tab_ui_results import BacktestResultsTabUI
from .backtest_tab_ui_batch import BacktestBatchTabUI
from .backtest_tab_config import BacktestConfigManager
from .backtest_tab_signal import BacktestSignalCallback
```

**Key Changes:**
- Delegate tab creation to sub-modules
- Use composition instead of giant monolithic class
- Keep only coordination logic

---

### 2. `backtest_tab_worker.py` (Worker Thread - 150 LOC)

**Responsibility:** Background thread for batch processing

**Contents:**
- `BatchTestWorker` class (complete)
  - `__init__`
  - `run`
- Worker signals (progress, log, finished, error)

**No changes needed** - This is already well-isolated

---

### 3. `backtest_tab_ui_setup.py` (Setup Tab - 400 LOC)

**Responsibility:** Setup tab UI (data source, symbol, timeframe, strategy)

**Contents:**
- `BacktestSetupTabUI` class
- `_create_setup_tab` (renamed to `create_tab`)
- Symbol selection widgets
- Date range widgets
- Strategy selection
- Data source configuration

**Methods:**
- `create_tab() -> QWidget`
- `get_symbol() -> str`
- `get_start_date() -> datetime`
- `get_end_date() -> datetime`
- `get_strategy_name() -> str`

---

### 4. `backtest_tab_ui_execution.py` (Execution Tab - 350 LOC)

**Responsibility:** Execution settings tab (fees, slippage, leverage)

**Contents:**
- `BacktestExecutionTabUI` class
- `_create_execution_tab` (renamed to `create_tab`)
- Fee settings widgets
- Slippage settings
- Leverage configuration
- Capital settings

**Methods:**
- `create_tab() -> QWidget`
- `get_execution_config() -> Dict`
- `set_execution_config(config: Dict)`

---

### 5. `backtest_tab_ui_results.py` (Results Tab - 450 LOC)

**Responsibility:** Results display (equity curve, metrics, trades)

**Contents:**
- `BacktestResultsTabUI` class
- `_create_results_tab` (renamed to `create_tab`)
- `_create_kpi_card`
- All update methods:
  - `_update_metrics_table`
  - `_update_trades_table`
  - `_update_breakdown_table`
- Equity chart plotting
- Results export triggers

**Methods:**
- `create_tab() -> QWidget`
- `display_results(result: BacktestResult)`
- `clear_results()`
- `export_csv(path: Path)`
- `export_equity_csv(path: Path)`

---

### 6. `backtest_tab_ui_batch.py` (Batch/WF Tab - 500 LOC)

**Responsibility:** Batch testing and walk-forward analysis UI

**Contents:**
- `BacktestBatchTabUI` class
- `_create_batch_tab` (renamed to `create_tab`)
- Batch configuration widgets
- Walk-forward configuration
- Batch results table
- All batch callbacks:
  - `_on_batch_btn_clicked`
  - `_on_batch_worker_finished`
  - `_on_batch_worker_error`
  - `_finalize_batch_ui`
  - `_export_batch_results`
  - `_on_wf_btn_clicked`
- Results tables:
  - `_update_batch_results_table`
  - `_update_wf_results_table`

**Methods:**
- `create_tab() -> QWidget`
- `start_batch_test(config: Dict)`
- `start_walk_forward(config: Dict)`
- `display_batch_results(results: List)`

---

### 7. `backtest_tab_config.py` (Config Management - 550 LOC)

**Responsibility:** Configuration management (engine configs, templates, settings)

**Contents:**
- `BacktestConfigManager` class
- Engine config collection:
  - `collect_engine_configs`
  - `_get_default_engine_configs`
  - `get_parameter_space_from_configs`
  - `get_parameter_specification`
- Settings persistence:
  - `_load_settings`
  - `_save_settings`
- Template management:
  - `_on_save_template_clicked`
  - `_on_load_template_clicked`
  - `_convert_v2_to_parameters`
  - `_get_nested_value`
- Variant generation:
  - `_on_derive_variant_clicked`
  - `_on_auto_generate_clicked`
  - `_apply_variants_to_param_space`
  - `_export_variants_json`
- Indicator sets:
  - `get_available_indicator_sets`
  - `generate_ai_test_variants`
  - `_on_indicator_set_changed`

**Methods:**
- `collect_all_engine_configs() -> Dict`
- `build_backtest_config() -> Dict`
- `load_settings(path: Path)`
- `save_settings(path: Path)`
- `save_template(name: str, config: Dict)`
- `load_template(name: str) -> Dict`
- `generate_variants(config: Dict) -> List[Dict]`

---

### 8. `backtest_tab_signal.py` (Signal Callback - 450 LOC)

**Responsibility:** Signal generation callback + export utilities

**Contents:**
- `BacktestSignalCallback` class
- `_get_signal_callback` → **REFACTORED** (394 LOC → 200 LOC)
  - Extract to smaller methods:
    - `_validate_signal_data`
    - `_build_market_context`
    - `_calculate_entry_score`
    - `_apply_gates`
    - `_generate_long_signals`
    - `_generate_short_signals`
- Export utilities:
  - `_export_csv`
  - `_export_equity_csv`
  - `_export_json`
- Helper methods:
  - `_on_progress_updated`
  - `_on_log_message`
  - `_log`

**Methods:**
- `create_signal_callback() -> Callable`
- `export_results(format: str, path: Path)`

**CRITICAL REFACTORING:**
The 394-line `_get_signal_callback` needs to be split into:
1. **Signal validation** (50 LOC)
2. **Market context building** (80 LOC)
3. **Entry score calculation** (100 LOC)
4. **Gate evaluation** (50 LOC)
5. **Signal generation** (80 LOC)
6. **Result packaging** (40 LOC)

---

## 🔄 MIGRATION STRATEGY

### PHASE 1: Create Sub-Modules (Copy, don't move)

1. Create all 8 new files
2. Copy relevant code to each module
3. Add proper imports and class definitions
4. **DO NOT delete from original yet**

### PHASE 2: Update Main backtest_tab.py

1. Import sub-modules
2. Replace method calls with sub-module delegation
3. Test that UI still works
4. **Still keep original methods commented out**

### PHASE 3: Clean Up

1. Remove duplicated code from original
2. Update all imports throughout codebase
3. Run full test suite
4. Manual UI testing

### PHASE 4: Verification

1. Check that ALL 55 methods are preserved
2. Verify all UI elements functional
3. Test batch processing
4. Test template management
5. Test results export

---

## ⚠️ CRITICAL CONSIDERATIONS

### Backwards Compatibility

**Old imports:**
```python
from src.ui.widgets.bitunix_trading.backtest_tab import BacktestTab
```

**Must still work!** The main `backtest_tab.py` re-exports everything.

### Circular Import Prevention

**Dependency Order:**
1. `backtest_tab_worker.py` (no deps)
2. `backtest_tab_signal.py` (minimal deps)
3. `backtest_tab_config.py` (depends on signal)
4. `backtest_tab_ui_*.py` (depends on config, signal)
5. `backtest_tab.py` (depends on all)

### Testing After Split

**Critical Tests:**
- [ ] Backtest tab loads without errors
- [ ] Setup tab UI functional
- [ ] Execution tab UI functional
- [ ] Results display works
- [ ] Batch processing runs
- [ ] Walk-forward runs
- [ ] Template save/load works
- [ ] Export functions work
- [ ] All 55 methods accessible

---

## 📊 EXPECTED OUTCOME

| Module | LOC | Responsibility | Risk |
|--------|-----|----------------|------|
| backtest_tab.py | 250 | Main coordination | LOW |
| backtest_tab_worker.py | 150 | Background processing | LOW |
| backtest_tab_ui_setup.py | 400 | Setup UI | LOW |
| backtest_tab_ui_execution.py | 350 | Execution UI | LOW |
| backtest_tab_ui_results.py | 450 | Results UI | MEDIUM |
| backtest_tab_ui_batch.py | 500 | Batch/WF UI | MEDIUM |
| backtest_tab_config.py | 550 | Config management | HIGH |
| backtest_tab_signal.py | 450 | Signal callback | HIGH |
| **TOTAL** | **3,100** | (vs 3,175 original) | |

**Savings:** 75 LOC (removed redundancy)
**Max module size:** 550 LOC (within 600 LOC limit) ✅
**All functions preserved:** 55/55 ✅

---

## 🚀 NEXT STEPS

1. **Review this plan** - Confirm splitting strategy
2. **Create backtest_tab_worker.py** - Easiest first (already isolated)
3. **Create backtest_tab_signal.py** - Second (refactor 394-line monster)
4. **Create UI modules** - Third (straightforward extraction)
5. **Create config module** - Fourth (complex but self-contained)
6. **Update main backtest_tab.py** - Fifth (coordination)
7. **Test thoroughly** - Sixth (all UI + batch tests)
8. **Commit** - Seventh (with verification report)

---

**Estimated effort:** 6-8 hours (with testing)
**Risk level:** HIGH (complex UI with many interconnections)
**Mitigation:** Incremental approach, test after each module
