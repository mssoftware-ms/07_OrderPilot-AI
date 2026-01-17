# Data Quality Tab - Centralized Data Verification & Validation

**Date:** 2026-01-17
**Purpose:** Centralize data quality tools across all providers

---

## Overview

The new "Data Quality" tab consolidates all data verification and validation tools in one place:

1. **Provider Selection** - Choose which provider's data to work with
2. **Database Verification** - Analyze downloaded data quality and coverage
3. **Manual OHLC Validation** - Fix OHLC inconsistencies across all providers

---

## Location

**Settings → Data Quality**

Previously scattered:
- ❌ Manual OHLC validation was in Bitunix tab only
- ❌ No unified verification tool for database analysis

Now centralized:
- ✅ One tab for all data quality operations
- ✅ Works with Bitunix AND Alpaca data
- ✅ Provider-agnostic tools

---

## Features

### 1. Provider Selection

**Field:** Dropdown (Bitunix, Alpaca)

**Purpose:**
- Select which provider's data to work with
- Auto-updates symbol format examples
- Shows database path for verification

**Example:**
```
Provider: [Bitunix ▼]
Database: data/orderpilot.db (provider: bitunix)
```

---

### 2. Database Verification

**Purpose:** Analyze downloaded data quality without opening external tools

**Inputs:**
- **Symbol:** Symbol to verify (auto-prefixed with provider, e.g., `bitunix:BTCUSDT`)
- **Timeframe:** Expected timeframe (1min, 5min, 15min, 1h, 4h, 1d)

**Action Button:** "Verify Data"

**What it checks:**
1. **Total bars** - Count of stored candles
2. **Time range** - First to last timestamp
3. **Coverage** - % of expected vs actual bars
4. **Intervals** - Confirms actual timeframe matches expected
5. **Gaps** - Detects missing data (intervals > 2x expected)
6. **OHLC consistency** - Validates high/low vs open/close

**Result Display:**
```
✅ Verification Complete for bitunix:BTCUSDT

📊 Statistics:
  Total bars: 525,722
  Time span: 365.1 days
  Coverage: 100.00% (1 missing)

⏱️  Intervals:
  Average: 1.00 min (expected: 1 min)
  Correct: 525,720/525,721 (100.00%)

🔍 Data Quality:
  Gaps (>2min): 0
  OHLC errors: 0

✅ Timeframe verified
✅ Excellent coverage
✅ No gaps
✅ OHLC valid
```

---

### 3. Manual OHLC Validation

**Moved from:** Bitunix tab → Data Quality tab
**Purpose:** Fix OHLC inconsistencies in database

**Description:**
"Fix OHLC inconsistencies in database (high < open/close, low > open/close)"

**Action Buttons:**
- **Validate & Fix** - Scans database and corrects errors
- **Cancel** - Stop validation in progress

**Progress:** Shows real-time validation progress

**What it fixes:**
- Cases where `high < max(open, close)`
- Cases where `low > min(open, close)`

**Result:**
```
✅ OHLC Validation Complete

Invalid bars found: 143
Bars fixed: 143
Symbols affected: bitunix:BTCUSDT, bitunix:ETHUSDT
```

---

## Implementation Details

### File Structure

| File | Purpose |
|------|---------|
| `settings_tabs_data_quality.py` | New tab implementation |
| `settings_tabs_mixin.py` | Added `_create_data_quality_tab()` |
| `settings_dialog.py` | Added tab, reduced width (900→600px) |
| `settings_tabs_bitunix.py` | Removed Manual Validation section |

### Worker Classes

**DataQualityVerificationWorker** (new)
- Runs in background thread
- Directly queries SQLite database
- Analyzes intervals, gaps, OHLC consistency
- Emits progress signals

**OHLCValidationWorker** (existing)
- Reused from Bitunix tab
- Now accessible from Data Quality tab
- Works across all providers

---

## Code Changes

### settings_tabs_data_quality.py (NEW - 400 LOC)

**Key Components:**

```python
class DataQualityVerificationWorker(QThread):
    """Background worker for database verification."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def run(self):
        # Query SQLite directly
        # Analyze intervals, gaps, OHLC
        # Build detailed report

class SettingsTabsDataQuality:
    """Helper for Data Quality tab."""

    def create_data_quality_tab(self) -> QWidget:
        # Provider selection
        # Database verification section
        # Manual OHLC validation section
```

### settings_dialog.py (MODIFIED)

**Window Size:**
```python
# Before
self.setMinimumSize(900, 400)  # Wide for 2-column checkboxes

# After
self.setMinimumSize(600, 400)  # Normal width (Data Quality is separate tab)
```

**Tab Order:**
```python
tabs.addTab(self._create_general_tab(), "General")
tabs.addTab(self._create_trading_tab(), "Trading")
tabs.addTab(self._create_broker_tab(), "Brokers")
tabs.addTab(self._create_market_data_tab(), "Market Data")
tabs.addTab(self._create_data_quality_tab(), "Data Quality")  # NEW
tabs.addTab(self._create_ai_tab(), "AI")
tabs.addTab(self._create_notifications_tab(), "Notifications")
```

### settings_tabs_bitunix.py (MODIFIED)

**Removed:**
- Manual Data Validation group (35 lines)
- `_start_ohlc_validation()` method
- `_cancel_ohlc_validation()` method
- `_on_validate_progress()` method
- `_on_validate_finished()` method
- `_on_validate_error()` method

**Result:** ~90 lines removed, cleaner Bitunix tab

---

## Benefits

### User Experience
- ✅ **Centralized** - All data quality tools in one place
- ✅ **Provider-agnostic** - Works with Bitunix AND Alpaca
- ✅ **Compact UI** - Bitunix tab no longer overloaded
- ✅ **Verification without CLI** - No need to run Python scripts

### Technical
- ✅ **Reusable** - Easy to add more providers (Yahoo, Finnhub, etc.)
- ✅ **Maintainable** - Quality tools decoupled from provider tabs
- ✅ **Extensible** - Can add more verification metrics easily
- ✅ **Settings width reduced** - Back to 600px (was 900px)

---

## Usage Examples

### Verify Downloaded Data

1. Settings → Data Quality
2. Provider: **Bitunix**
3. Symbol: `bitunix:BTCUSDT` (or just `BTCUSDT`)
4. Timeframe: **1min**
5. Click **Verify Data**
6. Review detailed report in popup

### Fix OHLC Errors

1. Settings → Data Quality
2. Provider: **Bitunix** (validates all bitunix symbols)
3. Click **Validate & Fix**
4. Wait for scan to complete
5. Review results (bars fixed, symbols affected)

---

## Future Enhancements

### Possible Additions

1. **Export Reports**
   - Save verification results to CSV/JSON
   - Compare multiple verification runs

2. **Batch Verification**
   - Verify multiple symbols at once
   - Schedule automatic verification

3. **Visual Charts**
   - Coverage timeline graph
   - Gap distribution histogram

4. **More Metrics**
   - Volume consistency checks
   - Price spike detection
   - Timestamp timezone validation

5. **Provider Comparison**
   - Compare Bitunix vs Alpaca data
   - Identify discrepancies

---

## Testing Checklist

- [x] Data Quality tab appears in Settings
- [x] Provider dropdown works (Bitunix, Alpaca)
- [x] Symbol auto-prefixes with provider
- [x] Verify Data button runs verification worker
- [x] Verification results displayed in popup
- [x] Manual OHLC validation works (moved from Bitunix)
- [x] Bitunix tab no longer has Manual Validation section
- [x] Settings window width reduced to 600px
- [x] No console errors on tab switch
- [x] Workers run in background (UI responsive)

---

## Migration Notes

**For existing users:**
- Manual OHLC validation moved from "Market Data → Bitunix" to "Data Quality"
- Functionality unchanged, just relocated
- Settings window is now narrower (600px vs 900px)

**For developers:**
- `SettingsTabsDataQuality` is the new helper class
- Follows same pattern as other tab helpers
- Reuses `OHLCValidationWorker` (no duplication)

---

## Changed Files Summary

| File | Lines Changed | Type |
|------|---------------|------|
| `settings_tabs_data_quality.py` | +400 | NEW |
| `settings_tabs_mixin.py` | +15 | Import + method |
| `settings_dialog.py` | +1, -1 | Tab added, width reduced |
| `settings_tabs_bitunix.py` | -90 | Manual validation removed |
| `docs/ui/data-quality-tab.md` | +300 | NEW (this file) |

**Total:** ~+625 lines (new features), -90 lines (cleanup)

---

**Status:** ✅ Implemented and tested - 2026-01-17
