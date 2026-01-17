# Bad Tick Detector Fixes

**Date:** 2026-01-17
**Issue:** Download failed with 0 bars due to type errors and missing logging

---

## Problem 1: AttributeError - 'HistoricalBar' has no attribute 'symbol'

### Symptom
```
AttributeError: 'HistoricalBar' object has no attribute 'symbol'
File "bitunix_bad_tick_detector.py", line 116
    symbol=bars[0].symbol if bars else symbol
```

### Root Cause
The bad tick detector tried to convert filtered bars back to **Alpaca `Bar` objects** (which have a `symbol` attribute), but Bitunix provider returns **`HistoricalBar` objects** (which do NOT have a `symbol` attribute).

**Type Mismatch:**
- **Input:** `HistoricalBar` (no symbol, uses Decimal for prices)
- **Output attempt:** Alpaca `Bar` (needs symbol, uses float)
- **Correct output:** `HistoricalBar` (match input type)

### Fix

**File:** `src/core/market_data/bitunix_bad_tick_detector.py` (Lines 105-129)

**Before (WRONG):**
```python
# Convert back to Bar objects
from alpaca.data.models.bars import Bar

cleaned_bars.append(
    Bar(
        symbol=bars[0].symbol,  # ❌ HistoricalBar has no 'symbol'!
        timestamp=ts,
        open=float(row["open"]),
        ...
    )
)
```

**After (CORRECT):**
```python
# Convert back to HistoricalBar objects
from src.core.market_data.types import HistoricalBar
from decimal import Decimal

cleaned_bars.append(
    HistoricalBar(
        timestamp=ts,
        open=Decimal(str(row["open"])),  # ✅ Use Decimal like input
        high=Decimal(str(row["high"])),
        low=Decimal(str(row["low"])),
        close=Decimal(str(row["close"])),
        volume=int(row["volume"]),
        vwap=Decimal(str(bars[0].vwap)) if bars and bars[0].vwap else None,
        trades=bars[0].trades if bars and bars[0].trades else None,
        source="bitunix"
    )
)
```

**Key Changes:**
1. ✅ Return `HistoricalBar` instead of Alpaca `Bar`
2. ✅ Use `Decimal` for OHLC values (matches input type)
3. ✅ No `symbol` attribute needed
4. ✅ Preserve `vwap`, `trades`, and `source` fields

---

## Problem 2: FutureWarning - Deprecated fillna method

### Symptom
```
FutureWarning: Series.fillna with 'method' is deprecated
Use obj.ffill() or obj.bfill() instead.
```

### Fix

**File:** `src/core/market_data/bitunix_bad_tick_detector.py` (Multiple locations)

**Before (DEPRECATED):**
```python
df[col] = df[col].fillna(method="ffill")
df[col] = df[col].fillna(method="bfill")
```

**After (MODERN):**
```python
df[col] = df[col].ffill()
df[col] = df[col].bfill()
```

**Locations Changed:**
- `_interpolate_bad_ticks()` (lines 280, 283)
- `_forward_fill_bad_ticks()` (lines 308, 311)

---

## Problem 3: Status Messages nur im UI, nicht in Logs

### Symptom
User wollte alle Status-Schritte auch im CMD/Log-Fenster sehen, nicht nur im UI-Label.

### Fix

**File:** `src/ui/workers/historical_download_worker.py` (Multiple locations)

**Pattern:**
```python
# ❌ BEFORE: Only UI signal
self.progress.emit(5, "📂 Initializing database...")

# ✅ AFTER: Log + UI signal
status_msg = "📂 Initializing database..."
logger.info(status_msg)
self.progress.emit(5, status_msg)
```

**Messages with Logging Added:**
1. `📂 Initializing database...` (5%)
2. `✅ Database ready` (8%)
3. `🔧 Creating {provider} provider...` (10%)
4. `🌐 Using public Bitunix API...` (15%)
5. `📊 Preparing download...` (20%)
6. `🚀 Starting download for {symbol}...` (20%)
7. Batch progress updates (logged every 100th batch to avoid spam)
8. `🔍 Validating OHLC data quality...` (92%)
9. `✅ Fixed X OHLC inconsistencies` (95%)
10. `🎉 Finalizing...` (98%)
11. `✅ Download complete!` (100%)

**Batch Logging Strategy:**
```python
# Log every 100th batch to avoid spam
if batch_num % 100 == 0 or batch_num == 1:
    logger.info(f"[{current_pct:3d}%] {full_msg}")
```

**Example Log Output:**
```
📂 Initializing database...
✅ Database ready
🔧 Creating bitunix provider...
🌐 Using public Bitunix API (no keys required)...
📊 Preparing download for BTCUSDT...
🚀 Starting download for BTCUSDT...
[ 20%] BTCUSDT: Batch 1: 200 Bars geladen, aktuell bei 17.01.2026 14:20
[ 22%] BTCUSDT: Batch 100: 20,000 Bars geladen, aktuell bei 15.01.2026 08:45
[ 33%] BTCUSDT: Batch 500: 100,000 Bars geladen, aktuell bei 28.12.2025 16:30
[ 46%] BTCUSDT: Batch 1000: 200,000 Bars geladen, aktuell bei 10.11.2025 09:15
...
[ 90%] BTCUSDT: Batch 2629: 525,600 Bars geladen, aktuell bei 18.01.2025 00:00
🔍 Validating OHLC data quality...
✅ Fixed 22 OHLC inconsistencies
🎉 Finalizing...
✅ Download complete!
```

---

## Testing

### Test 1: Download with Bad Tick Filter
1. Settings → Bitunix → Historical Data Download
2. Symbol: BTCUSDT
3. Period: 365 days
4. Timeframe: 1min
5. Enable "Bad Tick Filter"
6. Click "Download Full History"

**Expected:**
- ✅ Download completes successfully (no AttributeError)
- ✅ ~525,600 bars saved to database
- ✅ Bad ticks filtered (Hampel method, ~0.5-1% filtered)
- ✅ No FutureWarnings in console
- ✅ All status messages appear in both UI label AND console logs

### Test 2: Verify Bar Type
```python
# Check database contains HistoricalBar-compatible data
from src.database import get_db_manager
from src.database.models import MarketBar

db = get_db_manager()
with db.get_connection() as conn:
    bar = conn.query(MarketBar).first()
    print(f"Open type: {type(bar.open)}")  # Should be Decimal
    print(f"Has symbol: {bar.symbol}")     # Should be "bitunix:BTCUSDT"
```

**Expected:**
- ✅ OHLC values stored as Decimal
- ✅ Symbol includes source prefix ("bitunix:BTCUSDT")
- ✅ Data can be read back without type errors

---

## Summary

| Fix | File | Impact |
|-----|------|--------|
| Return `HistoricalBar` instead of `Bar` | `bitunix_bad_tick_detector.py` | ✅ Critical - Download now works |
| Use `.ffill()`/`.bfill()` | `bitunix_bad_tick_detector.py` | ✅ Clean - No warnings |
| Add logging to status messages | `historical_download_worker.py` | ✅ UX - User sees progress in logs |

**Result:** Download now completes successfully with full visibility in both UI and logs.

---

**Status:** ✅ Implemented and tested - 2026-01-17
