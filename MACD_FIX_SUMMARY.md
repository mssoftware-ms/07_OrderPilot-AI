# MACD Fix Summary

## Problem
The MACD indicator panel was displaying empty/no data in the chart windows.

## Root Causes

### 1. JavaScript API Issue (Primary)
**JavaScript errors:**
```
TypeError: paneApi.addHistogramSeries is not a function
TypeError: paneApi.addLineSeries is not a function
```

In Lightweight Charts v5, the pane API changed. The old v4 methods `paneApi.addHistogramSeries()` and `paneApi.addLineSeries()` no longer exist. Instead, you must use `chart.addSeries()` with the pane index.

### 2. Column Detection Logic (Secondary)
The column detection logic in `src/ui/widgets/embedded_tradingview_chart.py` was incorrectly identifying MACD columns from pandas_ta.

**pandas_ta returns MACD with these column names:**
- `MACD_12_26_9` - The MACD line (EMA12 - EMA26)
- `MACDh_12_26_9` - The Histogram (MACD - Signal)
- `MACDs_12_26_9` - The Signal line (EMA9 of MACD)

**The bug:** The code was checking for generic 'macd' in the column name BEFORE checking for 'macdh' or 'macds'. This caused:
- `MACDh_12_26_9` to be incorrectly matched as the MACD line (because it contains 'macd' and doesn't contain 'hist')
- The actual MACD line `MACD_12_26_9` to be skipped
- Wrong data being sent to the wrong series

## Solutions

### Solution 1: Fixed Lightweight Charts v5 API Usage

**Lines 190-214 (`createPanel` function):**

Changed from v4 API:
```javascript
// OLD - DOESN'T WORK IN V5
series = paneApi.addHistogramSeries({ ... });
series = paneApi.addLineSeries({ ... });
```

To v5 API:
```javascript
// NEW - CORRECT FOR V5
const paneIndex = paneApi.paneIndex();
series = chart.addSeries(HistogramSeries, { ... }, paneIndex);
series = chart.addSeries(LineSeries, { ... }, paneIndex);
```

**Lines 221-236 (`addPanelSeries` function):**

Same fix applied - use `chart.addSeries()` with pane index instead of pane API methods.

### Solution 2: Fixed Column Detection Logic

Reordered the column detection logic to check for specific patterns first:

**Before (WRONG ORDER):**
```python
if 'macd' in col_lower and 'signal' not in col_lower and 'hist' not in col_lower:
    macd_col = col  # This incorrectly matches MACDh_12_26_9
elif 'signal' in col_lower or 'macds' in col_lower:
    signal_col = col
elif 'hist' in col_lower or 'macdh' in col_lower:
    hist_col = col
```

**After (CORRECT ORDER):**
```python
# Check histogram first (MACDh_12_26_9 or histogram)
if 'macdh' in col_lower or 'hist' in col_lower:
    hist_col = col
# Check signal (MACDs_12_26_9 or signal)
elif 'macds' in col_lower or 'signal' in col_lower:
    signal_col = col
# Check MACD line (MACD_12_26_9)
elif 'macd' in col_lower:
    macd_col = col
```

## Files Modified
1. **`src/ui/widgets/embedded_tradingview_chart.py`**
   - **Lines 190-214**: Fixed `createPanel` to use v5 API (`chart.addSeries()` with pane index)
   - **Lines 221-236**: Fixed `addPanelSeries` to use v5 API
   - **Lines 755-767**: Fixed column detection logic
   - Added debug logging to verify correct column mapping

## Testing
A test script was created to verify the fix: `test_macd_fix.py`

**Test Results:**
```
[OK] MACD line column detected: MACD_12_26_9
[OK] Histogram column detected: MACDh_12_26_9
[OK] Signal column detected: MACDs_12_26_9

Column Mapping:
   MACD Line  : MACD_12_26_9
   Signal Line: MACDs_12_26_9
   Histogram  : MACDh_12_26_9

Data Statistics:
   MACD Line:      75 non-null values (expected - needs 26 bar warm-up)
   Signal Line:    67 non-null values (expected - needs 35 bar warm-up)
   Histogram:      67 non-null values (expected - needs 35 bar warm-up)

[SUCCESS] MACD TEST PASSED
```

## How to Verify the Fix

1. Start OrderPilot-AI
2. Double-click any symbol in the watchlist (e.g., QQQ)
3. In the popup chart window, enable the MACD indicator
4. You should now see:
   - **Blue line**: MACD line (EMA12 - EMA26)
   - **Orange line**: Signal line (EMA9 of MACD)
   - **Green/Red bars**: Histogram (MACD - Signal)
   - **Gray horizontal line**: Zero reference line

## Expected Behavior

The MACD indicator should now display all three components:
- MACD line shows the difference between fast and slow EMAs
- Signal line smooths the MACD line
- Histogram shows the divergence between MACD and Signal
- Green bars when histogram is positive (MACD > Signal)
- Red bars when histogram is negative (MACD < Signal)

## Additional Debug Logging

Added logging messages to help diagnose any future issues:
- Column detection mapping
- Number of values in each series
- Number of non-null values
- Number of data points prepared for chart

Check the logs at `logs/orderpilot.log` for these messages when MACD is enabled.
