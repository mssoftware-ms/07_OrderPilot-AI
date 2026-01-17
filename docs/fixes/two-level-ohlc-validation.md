# Two-Level OHLC Validation Architecture

**Date:** 2026-01-17
**Purpose:** Clarify the difference between provider and database OHLC validation

---

## Overview

OrderPilot-AI uses a **two-level OHLC validation system** to ensure chart data quality:

1. **Level 1: Provider Validation** (during download) - ALWAYS active
2. **Level 2: Database Validation** (after download) - User-controllable

---

## Level 1: Provider Validation (Primary)

### Location
`src/core/market_data/providers/bitunix_provider.py` (Lines 336-430)

### When It Runs
**ALWAYS** - every time data is fetched from Bitunix API

### What It Does
```python
# Parse kline data from Bitunix
o, h, l, c = parse_ohlc(kline)

# CRITICAL FIX: Validate and correct OHLC consistency
corrected_high = max(o, h, c)
corrected_low = min(o, l, c)

if h != corrected_high or l != corrected_low:
    validation_errors += 1
    logger.debug(f"OHLC validation fix: {symbol} @ {timestamp}")

bar = HistoricalBar(
    high=corrected_high,  # ✅ Always valid
    low=corrected_low,    # ✅ Always valid
    ...
)
```

### Purpose
- **Immediate correction** at the source
- Prevents bad data from ever entering the database
- Handles Bitunix API rounding errors (0.10-12.10 deviations)
- Runs during data ingestion, minimal overhead

### Logs
```
✅ Fixed 8 OHLC inconsistencies in BTCUSDT data
```

### Can It Be Disabled?
**NO** - This is built into the provider and always runs

---

## Level 2: Database Validation (Secondary)

### Location
`src/database/ohlc_validator.py` + `src/ui/workers/historical_download_worker.py`

### When It Runs
**OPTIONAL** - after download completes, if checkbox is enabled

### What It Does
```python
# Scan entire database for inconsistencies
query = session.query(MarketBar).filter(
    (MarketBar.high < MarketBar.open) |
    (MarketBar.high < MarketBar.close) |
    (MarketBar.low > MarketBar.open) |
    (MarketBar.low > MarketBar.close)
)

# Fix any found issues
for bar in invalid_bars:
    bar.high = max(bar.open, bar.high, bar.close)
    bar.low = min(bar.open, bar.low, bar.close)
```

### Purpose
- **Safety net** for edge cases
- Catches issues from:
  - Manual database edits
  - Database corruption
  - Provider bugs that slip through
  - Legacy data from before provider validation existed
- Comprehensive scan of all stored data

### Logs
```
🔍 Validating OHLC data in database...
✅ Database validation: Fixed 22 remaining OHLC inconsistencies
```

### Can It Be Disabled?
**YES** - User checkbox: "Validate OHLC Data in Database"

---

## UI Checkbox: "Validate OHLC Data in Database"

### Location
Settings → Market Data → Bitunix → Historical Data Download

### Label
```
☑️ Validate OHLC Data in Database
```

### Tooltip
```
After download: Scan database for any remaining OHLC inconsistencies and fix them.
Note: Provider already fixes OHLC during download, this is a secondary check.
Uncheck to skip database validation (saves ~5 seconds).
```

### Default State
**ENABLED (checked)** - Recommended for most users

---

## Why Two Levels?

### Level 1 (Provider) - Fast & Proactive
- ✅ Fixes issues at the source
- ✅ Zero database overhead
- ✅ Prevents bad data from ever being stored
- ✅ Fast (happens during data parsing)
- ❌ Can't fix data already in database
- ❌ Can't catch database corruption

### Level 2 (Database) - Comprehensive & Defensive
- ✅ Scans all stored data
- ✅ Catches manual edits, corruption
- ✅ Verifies provider validation worked
- ✅ Can fix legacy data
- ❌ Slower (~5-10 seconds for 525k bars)
- ❌ Runs after data is already stored

### Combined Strategy
**Defense in Depth:**
1. Provider validation prevents 99% of issues
2. Database validation catches the remaining 1%
3. User can disable level 2 for performance

---

## Typical Workflow

### Download with Both Enabled (Default)

```
[ 5%] 📂 Initializing database...
[10%] 🔧 Creating bitunix provider...
[20%] 🚀 Starting download for BTCUSDT...

[During download - Level 1]
✅ Fixed 8 OHLC inconsistencies in BTCUSDT data  (Provider)
✅ Fixed 11 OHLC inconsistencies in BTCUSDT data (Provider)
...

[After download - Level 2]
[92%] 🔍 Validating OHLC data in database...
[95%] ✅ Fixed 22 DB inconsistencies             (Database)
[100%] ✅ Download complete!

Success Dialog:
"Downloaded 525,600 bars for 1 symbol(s)
 ✅ Database check: Fixed 22 inconsistencies"
```

### Download with Database Validation Disabled

```
[ 5%] 📂 Initializing database...
[10%] 🔧 Creating bitunix provider...
[20%] 🚀 Starting download for BTCUSDT...

[During download - Level 1 still runs]
✅ Fixed 8 OHLC inconsistencies in BTCUSDT data  (Provider)
✅ Fixed 11 OHLC inconsistencies in BTCUSDT data (Provider)
...

[After download - Level 2 skipped]
[92%] ⏭️ Database validation skipped (disabled)
[100%] ✅ Download complete!

Success Dialog:
"Downloaded 525,600 bars for 1 symbol(s)
 ⏭️ Database validation was skipped"
```

---

## When to Disable Database Validation?

### Good Reasons to Disable
- **Performance testing:** Save 5-10 seconds
- **Repeated downloads:** Testing provider changes
- **Clean database:** Fresh install, no legacy data
- **Trust provider:** Level 1 handles 99% of cases

### Bad Reasons to Disable
- "My database is perfect" - Corruption can happen
- "It's too slow" - 5 seconds vs. broken charts?
- "Provider fixes it" - True, but belt AND suspenders

### Recommendation
**Keep it ENABLED** unless you have a specific reason to disable it.

---

## Manual Validation Button

**Settings → Bitunix → Data Quality Validation → "Validate & Fix OHLC Data"**

This button ALWAYS runs database validation, regardless of checkbox state.

**Use cases:**
- User disabled checkbox but later wants to validate
- Suspect database corruption
- Manual database edits
- Legacy data cleanup

---

## Performance Impact

### Level 1 (Provider Validation)
- **Time:** Negligible (~0.1ms per bar)
- **Happens:** During API response parsing
- **Cannot be disabled**

### Level 2 (Database Validation)
- **Time:** ~5-10 seconds for 525,600 bars
- **Happens:** After all data is stored
- **Can be disabled via checkbox**

### Total Overhead
- **With both levels:** ~5-10 seconds (acceptable)
- **Level 1 only:** ~0 seconds extra (built into download)

---

## Code Flow Diagram

```
User clicks "Download Full History"
    ↓
┌─────────────────────────────────────────┐
│ LEVEL 1: Provider Validation (ALWAYS)  │
├─────────────────────────────────────────┤
│ Bitunix API → Parse JSON → Validate    │
│ OHLC → Correct → Create HistoricalBar  │
│ → Save to Database                      │
│                                         │
│ Logs: "✅ Fixed 8 OHLC inconsistencies" │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ LEVEL 2: Database Validation (OPTIONAL)│
├─────────────────────────────────────────┤
│ if enable_ohlc_validation:              │
│   Scan database → Find invalid bars →  │
│   Fix → Save                            │
│                                         │
│ Logs: "✅ Fixed 22 DB inconsistencies"  │
│                                         │
│ else:                                   │
│   Skip validation                       │
│   Logs: "⏭️ Database validation skipped"│
└─────────────────────────────────────────┘
    ↓
Download Complete
```

---

## Summary

| Feature | Provider Validation | Database Validation |
|---------|--------------------|--------------------|
| **When** | During download | After download |
| **Speed** | Fast (0.1ms/bar) | Slower (5-10 sec total) |
| **Scope** | Incoming data only | All stored data |
| **Can disable?** | ❌ No | ✅ Yes (checkbox) |
| **Prevents bad data** | ✅ Yes | ❌ No (fixes only) |
| **Catches corruption** | ❌ No | ✅ Yes |
| **Default** | Always ON | ON (recommended) |

**Best Practice:** Keep both levels enabled for maximum data quality.

---

**Status:** ✅ Documented - 2026-01-17
