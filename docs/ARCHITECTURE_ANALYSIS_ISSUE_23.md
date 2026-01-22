# Architecture Analysis: Issue #23 Fix (MACD Field Name Mapping)

**Date**: 2026-01-22
**Analyzed By**: Code Analyzer Agent
**Issue**: #23 - Regime detection failing due to MACD field name mismatch
**Architecture Rating**: **7.5/10**

---

## Executive Summary

Issue #23 revealed a **field name mapping vulnerability** in the regime detection system where JSON config field names (`"MACD_12_26_9"`) did not match the internal indicator engine output (`"macd"`, `"signal"`, `"histogram"`). This created a **silent failure mode** where regime conditions evaluated to `NaN`, causing all regimes to be classified as "UNKNOWN".

**Critical Finding**: The system has **implicit field name normalization** in `RegimeEngineJSON._calculate_indicators()` (lines 214-232), but this was **not applied during incremental detection** in `entry_analyzer_backtest_config.py`. This architectural gap creates **two code paths with different behaviors**.

---

## System Architecture Overview

### Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. JSON Config (entry_analyzer_regime.json)                │
│    - indicators: [{id, type, params}]                      │
│    - regimes: [{id, conditions}]                           │
│    - Field names in conditions: "MACD_12_26_9"             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. IndicatorEngine (src/core/indicators/engine.py)         │
│    - Dispatches to TrendIndicators.calculate_macd()        │
│    - Returns IndicatorResult with DataFrame values         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. pandas_ta.macd() [ACTUAL COLUMN NAMES]                  │
│    DataFrame columns:                                       │
│    - 'MACD_12_26_9'   (main line)                          │
│    - 'MACDh_12_26_9'  (histogram)                          │
│    - 'MACDs_12_26_9'  (signal)                             │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌─────────────────┐  ┌─────────────────────────────────────┐
│ PATH A:         │  │ PATH B:                             │
│ RegimeEngineJSON│  │ entry_analyzer_backtest_config.py   │
│ ._calculate_    │  │ ._indicator_values_at()             │
│  indicators()   │  │                                     │
│                 │  │ ❌ BUG: Used raw pandas_ta output    │
│ ✅ Normalizes   │  │    without normalization            │
│    field names: │  │    {"MACD_12_26_9": val}            │
│    {"macd": val}│  │                                     │
│    Lines 214-232│  │    Lines 477-494 (backtest_config)  │
└────────┬────────┘  └────────┬────────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. RegimeDetector.detect_active_regimes()                  │
│    - Evaluates conditions against indicator_values         │
│    - Condition references field "MACD_12_26_9"             │
│    - Looks up: indicator_values["macd_12_26_9"]            │
│                                 ["MACD_12_26_9"]            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. ConditionEvaluator.evaluate()                           │
│    - Gets value from indicator_values dict                 │
│    - PATH A: ✅ Finds "macd" (normalized)                   │
│    - PATH B: ❌ Looks for "MACD_12_26_9" but dict has      │
│              "MACD_12_26_9" → Success ONLY if exact match  │
└─────────────────────────────────────────────────────────────┘
```

---

## Field Name Mapping Analysis

### MACD Field Names (Issue #23 Root Cause)

| Source | Main Line | Signal | Histogram |
|--------|-----------|--------|-----------|
| **pandas_ta Output** | `MACD_12_26_9` | `MACDs_12_26_9` | `MACDh_12_26_9` |
| **TA-Lib Output** | `macd` | `signal` | `histogram` |
| **JSON Config (User-facing)** | `MACD_12_26_9` ✅ | `MACDs_12_26_9` | `MACDh_12_26_9` |
| **Internal Normalized (PATH A)** | `macd` ✅ | `signal` | `histogram` |
| **PATH B (Bug)** | `MACD_12_26_9` ❌ | `MACDs_12_26_9` ❌ | `MACDh_12_26_9` ❌ |

**Problem**: JSON config uses `"MACD_12_26_9"` (pandas_ta format), but PATH A normalizes to `"macd"` (TA-Lib format), creating a mismatch.

**Fix Applied**: Changed JSON config from `"field": "MACD_12_26_9"` → `"field": "value"` (generic alias that maps to main line).

---

### Other Indicators Field Name Mapping

#### 1. ADX (Average Directional Index)

| Source | Output Type | Field Names | Risk Level |
|--------|-------------|-------------|------------|
| **pandas_ta** | `Series` | `ADX_14` (single value) | ⚠️ MEDIUM |
| **TA-Lib** | `Series` | (no column name, just Series) | ✅ LOW |
| **JSON Config** | - | `"field": "value"` | ✅ SAFE |
| **Internal** | - | Wrapped as `{"value": float}` | ✅ SAFE |

**Status**: ✅ **NO RISK** - ADX is a Series, always wrapped as `{"value": X}`. Config correctly uses `"field": "value"`.

**Evidence from code**:
```python
# src/core/indicators/trend.py:169
values = ta.adx(..., length=period)['ADX_14']  # Extracts Series directly
# RegimeEngineJSON:202
indicator_values[ind_def.id] = {"value": latest_value}  # Always wraps as "value"
```

#### 2. RSI (Relative Strength Index)

| Source | Output Type | Field Names | Risk Level |
|--------|-------------|-------------|------------|
| **pandas_ta** | `Series` | (no column name) | ✅ LOW |
| **TA-Lib** | `Series` | (no column name) | ✅ LOW |
| **JSON Config** | - | `"field": "value"` | ✅ SAFE |
| **Internal** | - | Wrapped as `{"value": float}` | ✅ SAFE |

**Status**: ✅ **NO RISK** - RSI is always a Series, wrapped as `{"value": X}`.

**Evidence from JSON config**:
```json
{
  "id": "rsi14",
  "type": "RSI",
  "params": {"period": 14}
}
// Used as: {"indicator_id": "rsi14", "field": "value"}
```

#### 3. ATR (Average True Range)

| Source | Output Type | Field Names | Risk Level |
|--------|-------------|-------------|------------|
| **pandas_ta** | `Series` | (no column name) | ✅ LOW |
| **TA-Lib** | `Series` | (no column name) | ✅ LOW |
| **JSON Config** | - | `"field": "value"` | ✅ SAFE |
| **Internal** | - | Wrapped as `{"value": float}` | ✅ SAFE |

**Status**: ✅ **NO RISK** - ATR is always a Series, wrapped as `{"value": X}`.

#### 4. Bollinger Bands (BB)

| Source | Main Band | Upper | Lower | Bandwidth | Risk Level |
|--------|-----------|-------|-------|-----------|------------|
| **pandas_ta** | `BBM_20_2.0` | `BBU_20_2.0` | `BBL_20_2.0` | `BBB_20_2.0` | ⚠️ **HIGH** |
| **TA-Lib** | `middle` | `upper` | `lower` | (calculated) | ✅ LOW |
| **JSON Config** | - | `"upper"` | `"lower"` | `"width"` | ⚠️ **RISK** |
| **Internal Normalized** | `middle` | `upper` | `lower` | `bandwidth` / `width` | ✅ SAFE |

**Status**: ⚠️ **MEDIUM RISK** - BB has multiple fields with library-specific names, BUT normalization is applied.

**Evidence from code**:
```python
# src/core/indicators/volatility.py:80-86 (TA-Lib)
return pd.DataFrame({
    'upper': upper,
    'middle': middle,
    'lower': lower,
    'bandwidth': upper - lower,
    'percent': (data['close'] - lower) / (upper - lower)
})

# src/core/indicators/volatility.py:104-118 (pandas_ta)
result = ta.bbands(...)  # Returns BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
return pd.DataFrame({
    'lower': result[f'BBL_{period}_{std_dev}'],
    'middle': result[f'BBM_{period}_{std_dev}'],
    'upper': result[f'BBU_{period}_{std_dev}'],
    'bandwidth': result[f'BBB_{period}_{std_dev}'],
    'percent': result[f'BBP_{period}_{std_dev}']
})
```

**Additional Safety**: Lines 211-213 in `RegimeEngineJSON` add `width` alias for `bandwidth`:
```python
if 'bandwidth' in indicator_values[ind_def.id]:
    # Alias: bandwidth → width (for BB indicators)
    indicator_values[ind_def.id]['width'] = indicator_values[ind_def.id]['bandwidth']
```

**Current JSON Config Status**:
```json
// No BB usage in entry_analyzer_regime.json currently
// If added, should use: "field": "upper" | "lower" | "middle" | "width"
```

---

## Architecture Issues Identified

### 1. **Two Code Paths with Different Normalization** (CRITICAL)

**Location**:
- **PATH A**: `RegimeEngineJSON._calculate_indicators()` (lines 168-248)
- **PATH B**: `entry_analyzer_backtest_config.py._indicator_values_at()` (lines 477-494)

**Problem**: PATH B (incremental regime detection in backtest) **does not apply field name normalization**, while PATH A does. This creates **inconsistent behavior**:
- Direct call to `RegimeEngineJSON.classify_from_config()` → Works ✅
- Incremental detection in Entry Analyzer → Failed ❌ (before fix)

**Root Cause**: Copy-paste code duplication. The incremental detection logic manually constructs `indicator_values` dict without using the normalization logic from `RegimeEngineJSON`.

**Evidence**:
```python
# PATH B (entry_analyzer_backtest_config.py:477-494)
def _indicator_values_at(index: int) -> dict[str, dict[str, float]]:
    values: dict[str, dict[str, float]] = {}
    for ind_id, result in indicator_results.items():
        if isinstance(result, pd.Series):
            val = result.iloc[index] if index < len(result) else float("nan")
            values[ind_id] = {"value": _safe_value(val)}
        elif isinstance(result, pd.DataFrame):
            values[ind_id] = {}
            for col in result.columns:  # ❌ Uses raw pandas_ta column names!
                val = result[col].iloc[index] if index < len(result) else float("nan")
                values[ind_id][col] = _safe_value(val)  # col = "MACD_12_26_9"
            # ⚠️ No normalization applied!
```

Compare to PATH A (RegimeEngineJSON:204-232):
```python
elif isinstance(result.values, pd.DataFrame):
    indicator_values[ind_def.id] = {}
    for col in result.values.columns:
        latest_value = result.values[col].iloc[-1] if len(result.values) > 0 else None
        indicator_values[ind_def.id][col] = latest_value

    # ✅ Normalization applied for BB
    if 'bandwidth' in indicator_values[ind_def.id]:
        indicator_values[ind_def.id]['width'] = indicator_values[ind_def.id]['bandwidth']

    # ✅ Normalization applied for MACD
    if ind_config.indicator_type == IndicatorType.MACD:
        cols = list(indicator_values[ind_def.id].keys())
        macd_col = next((c for c in cols if "macd" in c.lower() and ...), None)
        signal_col = next((c for c in cols if "signal" in c.lower()), None)
        hist_col = next((c for c in cols if "hist" in c.lower()), None)
        # Creates normalized aliases: "macd", "signal", "histogram", "value"
```

**Fix Required**: Extract normalization logic into a separate method and reuse in both paths.

---

### 2. **No Field Name Validation at Config Load Time** (HIGH PRIORITY)

**Problem**: JSON configs can reference **any field name** without validation. Errors only occur at runtime during condition evaluation.

**Example Failure Mode**:
```json
{
  "left": {"indicator_id": "macd_12_26_9", "field": "invalid_field_name"},
  "op": "gt",
  "right": {"value": 0}
}
```
This will fail silently with `ConditionEvaluationError: Field 'invalid_field_name' not found in indicator 'macd_12_26_9'`.

**Solution**: Add validation at config load time:
1. `ConfigLoader` should validate that all referenced fields exist in indicator schema
2. Create a registry of valid field names per indicator type
3. Fail fast with clear error message during `load_config()`, not during backtest

**Suggested Registry**:
```python
INDICATOR_FIELDS = {
    IndicatorType.MACD: ["value", "macd", "signal", "histogram",
                         "MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9"],
    IndicatorType.BB: ["upper", "middle", "lower", "width", "bandwidth", "percent"],
    IndicatorType.ADX: ["value"],
    IndicatorType.RSI: ["value"],
    IndicatorType.ATR: ["value"],
}
```

---

### 3. **Implicit Field Name Aliases** (MEDIUM PRIORITY)

**Problem**: The system has **undocumented field name aliases**:
- `"value"` → main indicator output (works for MACD, RSI, ADX, ATR)
- `"width"` ↔ `"bandwidth"` (for BB)
- `"macd"` ↔ `"MACD_12_26_9"` (implicit normalization)

**Risk**: Users may unknowingly rely on aliases that only work in one code path (PATH A) but not PATH B.

**Solution**: Document all aliases explicitly in:
1. JSON schema documentation
2. Indicator calculation method docstrings
3. User-facing field name reference guide

---

### 4. **No Unit Tests for Field Name Mapping** (HIGH PRIORITY)

**Problem**: Issue #23 existed because there were no tests validating:
1. Field names in JSON configs match indicator engine output
2. Normalization logic works correctly for all indicators
3. Both PATH A and PATH B produce identical results

**Gaps Identified**:
```
❌ test_macd_field_name_normalization() - Missing
❌ test_incremental_vs_batch_regime_detection() - Missing
❌ test_bb_field_name_aliases() - Missing
❌ test_invalid_field_name_rejection() - Missing
```

**Fix Required**: Create integration tests in `tests/qa/test_regime_detection_field_names.py`

---

### 5. **Silent Failure Mode with NaN** (MEDIUM PRIORITY)

**Problem**: When a field name doesn't exist, the evaluator returns `NaN` instead of raising an error:

```python
# ConditionEvaluator (assumption based on behavior)
value = indicator_values[indicator_id].get(field_name, float("nan"))
# No error raised! Condition evaluates to False silently
```

This caused all regimes to be classified as "UNKNOWN" without any error message.

**Better Design**:
```python
if field_name not in indicator_values[indicator_id]:
    raise ConditionEvaluationError(
        f"Field '{field_name}' not found in indicator '{indicator_id}'. "
        f"Available fields: {list(indicator_values[indicator_id].keys())}"
    )
```

---

## Risk Assessment by Indicator

| Indicator | Risk Level | Reason | Mitigation Status |
|-----------|-----------|--------|-------------------|
| **MACD** | 🔴 **CRITICAL** | Multi-field, library-specific names, PATH B failed | ✅ **FIXED** (Issue #23) |
| **BB (Bollinger Bands)** | 🟡 **MEDIUM** | Multi-field, has normalization in PATH A only | ⚠️ **PARTIAL** (not tested in PATH B) |
| **ADX** | 🟢 **LOW** | Single value, always wrapped as `{"value": X}` | ✅ **SAFE** |
| **RSI** | 🟢 **LOW** | Single value, always wrapped as `{"value": X}` | ✅ **SAFE** |
| **ATR** | 🟢 **LOW** | Single value, always wrapped as `{"value": X}` | ✅ **SAFE** |
| **Custom (Momentum Score)** | 🟡 **MEDIUM** | Calculated indicator, no normalization needed | ✅ **SAFE** (always `{"value": X}`) |

---

## Error Handling Evaluation

### Current Error Handling

**Location**: `RegimeDetector.detect_active_regimes()` (lines 156-178)

```python
try:
    is_active = evaluator.evaluate_group(regime_def.conditions)
    if is_active:
        active_regimes.append(ActiveRegime(definition=regime_def))
except Exception as e:
    error_count += 1
    last_error = e
    logger.error(
        f"Error evaluating regime '{regime_def.id}': {e}. "
        f"Treating as inactive."
    )
```

**Issue**: Catches **all exceptions** broadly. This masks:
1. Field name mismatches (ConditionEvaluationError)
2. Missing indicators
3. Type errors
4. Math errors (division by zero, etc.)

**All exceptions are treated as "regime inactive"**, which is incorrect. A field name mismatch should **fail fast**, not silently continue.

**Better Design**:
```python
try:
    is_active = evaluator.evaluate_group(regime_def.conditions)
except ConditionEvaluationError as e:
    # This is a configuration error, not a runtime issue
    raise ConfigLoadError(
        f"Regime '{regime_def.id}' configuration error: {e}. "
        f"Check indicator field names in JSON config."
    ) from e
except Exception as e:
    # Unexpected runtime error
    error_count += 1
    logger.error(f"Runtime error evaluating regime '{regime_def.id}': {e}")
```

---

## Architectural Improvements Recommended

### Priority 1: Critical (Must Fix)

1. **Extract Field Name Normalization Logic**
   - Create `IndicatorFieldMapper` class with method `normalize_indicator_values()`
   - Use in both RegimeEngineJSON and entry_analyzer_backtest_config
   - **Estimated Effort**: 2-3 hours
   - **Files to Change**:
     - Create `src/core/indicators/field_mapper.py`
     - Refactor `regime_engine_json.py` (lines 204-232)
     - Refactor `entry_analyzer_backtest_config.py` (lines 477-494)

2. **Add Field Name Validation at Config Load**
   - Create field name registry (`INDICATOR_FIELDS` dict)
   - Validate field references in `ConfigLoader.load_config()`
   - **Estimated Effort**: 3-4 hours
   - **Files to Change**:
     - `src/core/tradingbot/config/loader.py`
     - `src/core/indicators/types.py` (add registry)

3. **Add Integration Tests**
   - Test field name mapping for all indicators
   - Test PATH A vs PATH B consistency
   - Test invalid field name rejection
   - **Estimated Effort**: 4-5 hours
   - **Files to Create**: `tests/qa/test_regime_field_names.py`

### Priority 2: High (Should Fix)

4. **Improve Error Messages**
   - Replace NaN fallback with explicit errors
   - Add "Available fields: [...]" to error messages
   - Distinguish config errors from runtime errors
   - **Estimated Effort**: 2 hours
   - **Files to Change**: `src/core/tradingbot/config/evaluator.py`

5. **Document Field Name Aliases**
   - Create user-facing field name reference guide
   - Add docstrings to indicator calculators
   - Update JSON schema documentation
   - **Estimated Effort**: 2-3 hours
   - **Files to Create**: `docs/INDICATOR_FIELD_NAMES.md`

### Priority 3: Medium (Nice to Have)

6. **Add Field Name Auto-Completion**
   - JSON schema with field name enums per indicator
   - IDE auto-completion support for field names
   - **Estimated Effort**: 1-2 hours

7. **Create Field Name Migration Tool**
   - Script to update old configs to new field names
   - **Estimated Effort**: 1 hour

---

## Design Pattern Analysis

### Current Pattern: **Mixed Normalization Strategy**

**Pros**:
- Allows flexibility (users can use either TA-Lib or pandas_ta names)
- Backward compatible with existing configs

**Cons**:
- Inconsistent behavior between code paths (PATH A vs PATH B)
- Implicit aliases create confusion
- No validation → late runtime errors

### Recommended Pattern: **Explicit Canonical Names**

**Proposal**:
1. Define **canonical field names** for each indicator (TA-Lib style: `"macd"`, `"signal"`, `"histogram"`)
2. Always normalize library-specific names to canonical names
3. Document canonical names in schema
4. Reject non-canonical names at config load time

**Benefits**:
- Single source of truth
- Consistent behavior across all code paths
- Early validation
- Clear documentation

**Migration Path**:
1. Add normalization to PATH B (entry_analyzer_backtest_config)
2. Deprecate library-specific names in JSON configs (warn but accept for 1 version)
3. Enforce canonical names in next major version

---

## Overall Architecture Rating: **7.5/10**

### Strengths ✅
1. **Clean Separation of Concerns**: IndicatorEngine, RegimeDetector, ConfigLoader are well-separated
2. **Flexible Library Support**: Supports both TA-Lib and pandas_ta with fallback to manual calculation
3. **JSON-Based Configuration**: Allows runtime regime definition changes without code changes
4. **Logging and Debugging**: Good logging throughout the system
5. **TYPE SAFETY**: Strong use of Pydantic models and type hints

### Weaknesses ❌
1. **Code Duplication**: Two paths for indicator value extraction (PATH A vs PATH B)
2. **Implicit Normalization**: Field name normalization only in one path
3. **No Config Validation**: Field names not validated until runtime
4. **Broad Exception Handling**: Masks configuration errors
5. **Missing Tests**: No integration tests for field name mapping
6. **Inconsistent Naming**: Mix of library-specific and canonical field names
7. **Silent Failures**: NaN fallback instead of explicit errors

### Risk Level: **MEDIUM** (after Issue #23 fix)
- MACD issue is fixed for Entry Analyzer use case
- BB could have similar issues in PATH B (untested)
- No validation prevents future field name bugs

---

## Conclusion

The Issue #23 fix correctly addressed the immediate MACD field name problem by changing the JSON config to use `"field": "value"` instead of `"field": "MACD_12_26_9"`. However, the **root architectural issue remains**: the system has two different code paths for constructing `indicator_values` dicts, and only one applies field name normalization.

**Immediate Action Items**:
1. ✅ Issue #23 Fixed (MACD field name in JSON config)
2. ⚠️ Document field name aliases (HIGH PRIORITY)
3. ⚠️ Extract normalization logic into shared module (CRITICAL)
4. ⚠️ Add validation at config load time (HIGH PRIORITY)
5. ⚠️ Add integration tests (HIGH PRIORITY)

**Long-Term Action**:
- Migrate to canonical field names with schema validation
- Deprecate library-specific names in configs
- Unify PATH A and PATH B into single normalization logic

---

## Test Coverage Gaps

### Missing Test Scenarios
```python
# tests/qa/test_regime_field_names.py (TO BE CREATED)

def test_macd_field_name_normalization():
    """Verify MACD field names work in both PATH A and PATH B"""
    pass

def test_bb_field_name_aliases():
    """Verify BB 'width' and 'bandwidth' are interchangeable"""
    pass

def test_invalid_field_name_raises_error():
    """Verify invalid field names fail at config load time"""
    pass

def test_incremental_vs_batch_consistency():
    """Verify PATH A and PATH B produce identical results"""
    pass

def test_all_indicators_have_value_field():
    """Verify all single-value indicators support 'value' field"""
    pass

def test_pandas_ta_vs_talib_normalization():
    """Verify both libraries produce normalized output"""
    pass
```

### Current Test Coverage Estimate
- **Unit Tests**: ~60% (individual indicator calculations tested)
- **Integration Tests**: ~30% (regime detection tested, but not field names)
- **Field Name Tests**: **0%** ❌

---

## Appendix: Field Name Reference

### Quick Reference Table

| Indicator | Type | Canonical Fields | pandas_ta Names | TA-Lib Names |
|-----------|------|------------------|-----------------|--------------|
| MACD | Multi | `value`, `signal`, `histogram` | `MACD_12_26_9`, `MACDs_12_26_9`, `MACDh_12_26_9` | `macd`, `signal`, `histogram` |
| BB | Multi | `upper`, `middle`, `lower`, `width`, `percent` | `BBU_20_2.0`, `BBM_20_2.0`, `BBL_20_2.0`, `BBB_20_2.0`, `BBP_20_2.0` | `upper`, `middle`, `lower` |
| ADX | Single | `value` | `ADX_14` | (Series, no name) |
| RSI | Single | `value` | (Series, no name) | (Series, no name) |
| ATR | Single | `value` | (Series, no name) | (Series, no name) |

### Safe Field Names (Always Work)
- **Single-value indicators**: Always use `"field": "value"`
- **MACD**: Use `"value"` (main line), `"signal"`, `"histogram"`
- **BB**: Use `"upper"`, `"lower"`, `"middle"`, `"width"`

---

**END OF REPORT**
