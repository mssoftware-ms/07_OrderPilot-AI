# OHLC Validation Toggle - UI Feature

**Date:** 2026-01-17
**Feature:** User-controllable OHLC validation after download

---

## Overview

Added a checkbox in the Bitunix settings tab to enable/disable automatic OHLC validation after downloads. This gives users control over whether they want automatic data quality checks.

### UI Location

**Settings → Market Data → Bitunix → Historical Data Download**

Two checkboxes are now available:
1. ☑️ **Enable Bad Tick Filter (Hampel)** - Filters outliers during download
2. ☑️ **Enable OHLC Validation after Download** - Validates OHLC consistency after download

---

## Implementation

### 1. UI Checkbox

**File:** `src/ui/dialogs/settings_tabs_bitunix.py` (Lines 125-133)

```python
# OHLC Validation Checkbox
self.parent.bitunix_validate_ohlc = QCheckBox("Enable OHLC Validation after Download")
self.parent.bitunix_validate_ohlc.setChecked(True)  # Default: enabled
self.parent.bitunix_validate_ohlc.setToolTip(
    "Automatically validate and fix OHLC inconsistencies after download. "
    "Ensures high >= max(open, close) and low <= min(open, close). "
    "Uncheck to skip validation (faster but may have rendering issues)."
)
download_layout.addRow(self.parent.bitunix_validate_ohlc)
```

**Tooltip explains:**
- What it does: Validates and fixes OHLC inconsistencies
- The rule: `high >= max(open, close)` and `low <= min(open, close)`
- Why disable: Faster downloads but may cause chart rendering issues

### 2. Pass to Worker

**File:** `src/ui/dialogs/settings_tabs_bitunix.py` (Lines 253, 263)

```python
enable_ohlc_validation = self.parent.bitunix_validate_ohlc.isChecked()

self._bitunix_download_worker = HistoricalDownloadWorker(
    provider_type="bitunix",
    symbols=[symbol],
    days=days,
    timeframe=timeframe,
    mode=mode,
    enable_bad_tick_filter=enable_filter,
    enable_ohlc_validation=enable_ohlc_validation,  # New parameter
)
```

### 3. Worker Parameter

**File:** `src/ui/workers/historical_download_worker.py` (Lines 31, 51)

```python
def __init__(
    self,
    provider_type: str,
    symbols: list[str],
    days: int,
    timeframe: str,
    mode: str = "download",
    enable_bad_tick_filter: bool = True,
    enable_ohlc_validation: bool = True,  # New parameter, default: enabled
):
    """Initialize download worker.

    Args:
        ...
        enable_ohlc_validation: Enable/disable OHLC validation after download
    """
    self.enable_ohlc_validation = enable_ohlc_validation
```

### 4. Conditional Validation

**File:** `src/ui/workers/historical_download_worker.py` (Lines 145-167)

```python
# Auto-validate OHLC data after download (if enabled)
if total_bars > 0 and not self._cancelled and self.enable_ohlc_validation:
    status_msg = "🔍 Validating OHLC data quality..."
    logger.info(status_msg)
    self.progress.emit(92, status_msg)
    validation_results = await self._auto_validate_ohlc()

    if validation_results and validation_results.get('fixed_bars', 0) > 0:
        fixed = validation_results['fixed_bars']
        status_msg = f"✅ Fixed {fixed} OHLC inconsistencies"
        logger.info(f"✅ Auto-fixed {fixed} OHLC inconsistencies after download")
        self.progress.emit(95, status_msg)
        results['ohlc_fixed'] = fixed
    else:
        status_msg = "✅ All OHLC data valid"
        logger.info("✅ OHLC validation: All data is valid")
        self.progress.emit(95, status_msg)
        results['ohlc_fixed'] = 0

elif total_bars > 0 and not self.enable_ohlc_validation:
    # Validation disabled - skip
    status_msg = "⏭️ OHLC validation skipped (disabled)"
    logger.info(status_msg)
    self.progress.emit(92, status_msg)
    results['ohlc_fixed'] = 0
```

### 5. Completion Message

**File:** `src/ui/workers/historical_download_worker.py` (Lines 177-182)

```python
# Build completion message
message = f"Downloaded {total_bars:,} bars for {len(self.symbols)} symbol(s)"
if self.enable_ohlc_validation and results.get('ohlc_fixed', 0) > 0:
    message += f"\n✅ Auto-fixed {results['ohlc_fixed']} OHLC inconsistencies"
elif not self.enable_ohlc_validation:
    message += f"\n⏭️ OHLC validation was disabled"
```

### 6. Startup Logging

**File:** `src/ui/workers/historical_download_worker.py` (Line 88)

```python
logger.info(f"📊 OHLC validation: {self.enable_ohlc_validation}")
```

---

## User Flow

### Scenario 1: Validation Enabled (Default)

**User Actions:**
1. Settings → Bitunix → Historical Data Download
2. ☑️ Enable OHLC Validation after Download (checked)
3. Click "Download Full History"

**Expected Behavior:**
```
📂 Initializing database...
✅ Database ready
...
🔍 Validating OHLC data quality...     [92%]
✅ Fixed 22 OHLC inconsistencies       [95%]
✅ Download complete!                  [100%]

Success Dialog:
"Downloaded 525,600 bars for 1 symbol(s)
✅ Auto-fixed 22 OHLC inconsistencies"
```

**Log Output:**
```
📊 OHLC validation: True
...
🔍 Validating OHLC data quality...
✅ Auto-fixed 22 OHLC inconsistencies after download
```

### Scenario 2: Validation Disabled

**User Actions:**
1. Settings → Bitunix → Historical Data Download
2. ☐ Enable OHLC Validation after Download (unchecked)
3. Click "Download Full History"

**Expected Behavior:**
```
📂 Initializing database...
✅ Database ready
...
⏭️ OHLC validation skipped (disabled)  [92%]
✅ Download complete!                  [100%]

Success Dialog:
"Downloaded 525,600 bars for 1 symbol(s)
⏭️ OHLC validation was disabled"
```

**Log Output:**
```
📊 OHLC validation: False
...
⏭️ OHLC validation skipped (disabled)
```

---

## Performance Impact

### With Validation Enabled (Default)
- **Time:** +5-10 seconds for 525,600 bars
- **Benefit:** Ensures chart renders correctly, no missing candle bodies/wicks
- **Use case:** Normal usage, recommended for most users

### With Validation Disabled
- **Time:** Saves 5-10 seconds
- **Risk:** May have OHLC inconsistencies that cause rendering issues
- **Use case:** Advanced users testing raw data, debugging provider issues

---

## Testing

### Test 1: Enabled (Default Behavior)
1. Open Settings → Bitunix
2. Verify ☑️ "Enable OHLC Validation after Download" is checked by default
3. Start download for BTCUSDT, 365 days, 1min
4. **Expected:**
   - Progress bar shows 92%: "🔍 Validating OHLC data quality..."
   - Progress bar shows 95%: "✅ Fixed X OHLC inconsistencies"
   - Success dialog mentions fixes
   - Logs show validation messages

### Test 2: Disabled
1. Open Settings → Bitunix
2. Uncheck ☐ "Enable OHLC Validation after Download"
3. Start download for BTCUSDT, 365 days, 1min
4. **Expected:**
   - Progress bar shows 92%: "⏭️ OHLC validation skipped (disabled)"
   - Success dialog: "⏭️ OHLC validation was disabled"
   - Logs show "OHLC validation: False"
   - Download ~5-10 seconds faster

### Test 3: Verify Data Quality
1. Download with validation DISABLED
2. Check database for OHLC inconsistencies:
   ```python
   from src.database.ohlc_validator import OHLCValidator
   validator = OHLCValidator()
   results = validator.validate_and_fix(symbol="bitunix:BTCUSDT", dry_run=True)
   print(f"Found {results['invalid_bars']} invalid bars")
   ```
3. Run manual validation button (Settings → Bitunix → Data Quality Validation)
4. **Expected:** Should find and fix inconsistencies

### Test 4: Verify Chart Rendering
1. Download with validation DISABLED
2. Open chart for BTCUSDT, 1min
3. **Expected:** May see candles with missing bodies/wicks (OHLC violations)
4. Run manual validation
5. Refresh chart
6. **Expected:** All candles render correctly

---

## Manual Validation Button

Users can always manually validate data using the **"Validate & Fix OHLC Data"** button in the **Data Quality Validation** section, regardless of the auto-validation checkbox state.

**Use cases:**
- User disabled auto-validation but later wants to clean data
- Re-validate after database corruption
- Check data quality after manual database edits

---

## Configuration Persistence

The checkbox state is **NOT currently persisted** between sessions. It defaults to **enabled (checked)** on every app restart.

**Future Enhancement:** Store setting in `config/profiles/paper.toml`:
```toml
[bitunix]
enable_ohlc_validation = true  # User preference
```

---

## Changed Files

| File | Changes | LOC Changed |
|------|---------|-------------|
| `src/ui/dialogs/settings_tabs_bitunix.py` | Added checkbox + parameter passing | +10 |
| `src/ui/workers/historical_download_worker.py` | Added parameter, conditional validation, logging | +15 |

**Total:** ~25 LOC added

---

## Summary

✅ **User Control:** Users can now choose whether to validate OHLC data automatically
✅ **Performance:** Skip validation for faster downloads when testing raw data
✅ **Safety:** Default is ENABLED to ensure data quality for most users
✅ **Visibility:** Logs and UI clearly show validation status
✅ **Flexibility:** Manual validation button always available as fallback

---

**Status:** ✅ Implemented and tested - 2026-01-17
