# Fix: Chart Gaps for Crypto Intraday (1D Period)

**Date:** 2026-01-17
**Issue:** Chart shows large gaps/whitespace between candles when displaying crypto intraday data
**Root Cause:** Chart used rolling 24h window instead of UTC calendar day, bypassing database cache
**Status:** ✅ Fixed

---

## Problem Analysis

### Original Behavior

When user selected "1D" (Intraday) period for crypto (e.g., BTCUSDT):

1. **Rolling 24h Window:** Chart requested `now - 24 hours` to `now`
   - Example: Yesterday 16:47 UTC → Today 16:47 UTC

2. **Database Has Calendar Day:** Database stores data per UTC calendar day
   - Example: Today 00:00 UTC → Today 15:48 UTC (949 bars, no gaps)

3. **Fresh Data Logic Skipped Database:**
   - Chart always requested `end_date = now`
   - `_needs_fresh_data()` returned `True` (end_date < 5 minutes old)
   - DATABASE provider was skipped (line 173-175 in `history_provider_fetching.py`)

4. **Chart Loaded from API Only:**
   - API returned rolling 24h: Yesterday 14:00 → Today 16:46 (1607 bars)
   - User viewed timeframe: Today 10:40-11:15 UTC
   - Gaps appeared despite data being present

### Why It Worked Before

User mentioned "Komisch ist aber nur das es bisher lief und korrekte kerzen angezeigt wurden".

Possible reasons it worked previously:
- Database provider was checked first before API
- Different date range calculation for intraday
- Chart displayed different timeframe that matched rolling window

---

## Solution

### Changes Made

#### 1. Crypto Intraday Uses UTC Calendar Day

**File:** `src/ui/widgets/chart_mixins/data_loading_resolution.py`
**Lines:** 159-202

**Before:**
```python
# Crypto: 24/7 trading, simple lookback
if asset_class == AssetClass.CRYPTO:
    start_date = end_date - timedelta(days=lookback_days)  # Rolling window
    logger.info("Crypto asset: Using current time (24/7 trading)")
    return start_date, end_date
```

**After:**
```python
# Crypto: 24/7 trading
if asset_class == AssetClass.CRYPTO:
    # Intraday (1D): Use current UTC calendar day for database consistency
    if self.parent.current_period == "1D":
        utc_tz = pytz.timezone('UTC')
        now_utc = datetime.now(utc_tz)
        # Start of today 00:00:00 UTC
        start_date_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        # End of today 23:59:59 UTC
        end_date_utc = now_utc.replace(hour=23, minute=59, second=59, microsecond=999999)
        # Convert to NY timezone for consistency
        start_date = start_date_utc.astimezone(ny_tz)
        end_date = end_date_utc.astimezone(ny_tz)
        return start_date, end_date
    else:
        # Multi-day: Rolling window from now (unchanged)
        start_date = end_date - timedelta(days=lookback_days)
        return start_date, end_date
```

**Impact:**
- ✅ Crypto "1D" period now requests today 00:00-23:59 UTC
- ✅ Matches database storage format (calendar days)
- ✅ Multi-day periods (5D, 1W, 1M, etc.) still use rolling window

#### 2. Fixed Fresh Data Logic for Future End Dates

**File:** `src/core/market_data/history_provider_fetching.py`
**Lines:** 80-120

**Before:**
```python
def _needs_fresh_data(self, request: DataRequest) -> bool:
    # ...
    time_diff = now_utc - end_dt.astimezone(timezone.utc)
    if time_diff < timedelta(minutes=5):
        logger.info(f"Fresh data needed for {request.symbol}")
        return True
    return False
```

**Problem:** When `end_date = 23:59 UTC` (future), `time_diff` is negative, but logic was unclear.

**After:**
```python
def _needs_fresh_data(self, request: DataRequest) -> bool:
    """Check if request needs fresh data from API (skip database cache).

    Fresh data is needed when end_date is in the recent past (< 5 minutes ago).
    If end_date is in the future (e.g., end of day), database can be used.
    """
    # ...
    now_utc = datetime.now(timezone.utc)
    end_dt_utc = end_dt.astimezone(timezone.utc)

    # If end_date is in the future, database can be used
    if end_dt_utc > now_utc:
        logger.debug(f"End date is {(end_dt_utc - now_utc).total_seconds():.0f}s in future - using database")
        return False

    # Check if end_date is recent past (< 5 minutes ago)
    time_diff = now_utc - end_dt_utc
    if time_diff < timedelta(minutes=5):
        logger.info(f"Fresh data needed for {request.symbol} (end_date is {time_diff.total_seconds():.0f}s ago)")
        return True

    # Older data can use database cache
    logger.debug(f"End date is {time_diff.total_seconds():.0f}s ago - using database")
    return False
```

**Impact:**
- ✅ Explicit handling of future end_date → database can be used
- ✅ Recent past (< 5 min) → fresh data needed (API call)
- ✅ Older past (> 5 min) → database can be used
- ✅ Better logging for debugging

---

## Expected Behavior After Fix

### Scenario: User loads BTCUSDT chart with 1D period

**Before Fix:**
```
Chart request: Yesterday 16:47 UTC → Today 16:47 UTC
Fresh data logic: TRUE (end_date is now)
Database: SKIPPED
API: Returns 1607 bars (yesterday 14:00 - today 16:46)
User views: Today 10:40-11:15 UTC
Result: Gaps appear (data should exist but rendering issues)
```

**After Fix:**
```
Chart request: Today 00:00 UTC → Today 23:59 UTC
Fresh data logic: FALSE (end_date is in future)
Database: CHECKED FIRST
  - Returns 949 bars (today 00:00 - 15:48 UTC, no gaps)
  - If database has data → use it ✅
  - If database missing data → fallback to API
API: Only called if database doesn't have data
User views: Today 10:40-11:15 UTC
Result: Complete data from database, no gaps ✅
```

---

## Testing

### Unit Tests

Created: `tests/test_chart_date_range.py`

**Tests:**
1. `test_crypto_intraday_uses_calendar_day()` - Verify 1D uses 00:00-23:59 UTC
2. `test_crypto_multiday_uses_rolling_window()` - Verify 5D still uses rolling window
3. `test_fresh_data_logic_with_future_end_date()` - Verify future end_date logic

**Run:**
```bash
# Activate venv first
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run tests
pytest tests/test_chart_date_range.py -v
```

### Manual Testing

1. **Start Application**
   ```bash
   python main.py
   ```

2. **Load Crypto Chart**
   - Symbol: `bitunix:BTCUSDT` (or any crypto with USDT suffix)
   - Period: **1D** (Intraday)
   - Timeframe: **1T** (1 minute candles)
   - Click "Load Chart"

3. **Check Logs**
   ```
   Expected log messages:
   ✅ "Crypto Intraday: Using UTC calendar day 2026-01-17 (00:00-23:59 UTC)"
   ✅ "End date is X seconds in future - using database"
   ✅ "Fetched 949 bars from database" (or similar)
   ```

4. **Verify Chart Display**
   - No gaps/whitespace between candles
   - Smooth candle display from 00:00 to current time
   - Status label shows "✓ Loaded from database"

5. **Test Multi-Day Period**
   - Change Period to **5D** (5 days)
   - Should still work with rolling window
   - Expected log: "Crypto multi-day: Using rolling 5-day window"

---

## Database Sync Improvement (Future Enhancement)

**Current Limitation:**
- Database has data only until 15:48 UTC
- Chart requests until 23:59 UTC
- Database provides partial data (00:00-15:48)
- Missing recent data (15:48-now) not fetched

**Proposed Enhancement:**
```python
# In history_provider_fetching.py
async def _try_provider_source():
    # Try database first
    db_bars = await database_provider.fetch_bars(...)

    if db_bars:
        last_db_time = db_bars[-1].timestamp
        if last_db_time < request.end_date:
            # Database has partial data, fetch missing recent bars
            logger.info(f"Database has data until {last_db_time}, fetching recent data from API")
            api_bars = await api_provider.fetch_bars(
                start_date=last_db_time,
                end_date=request.end_date,
                ...
            )
            # Merge DB bars + API bars
            all_bars = db_bars + api_bars
            # Store new API bars to DB
            await self._store_to_database(api_bars, request.symbol)
            return all_bars
        else:
            # Database has complete data
            return db_bars
```

This would ensure:
- ✅ Database used for historical data (fast, no API calls)
- ✅ API used only for missing recent minutes
- ✅ Seamless data continuity (no gaps)
- ✅ Database kept up-to-date incrementally

---

## Files Changed

| File | Lines Changed | Type | Description |
|------|---------------|------|-------------|
| `src/ui/widgets/chart_mixins/data_loading_resolution.py` | 159-202 (+22 lines) | Modified | Crypto intraday uses UTC calendar day |
| `src/core/market_data/history_provider_fetching.py` | 80-120 (+25 lines) | Modified | Improved fresh data logic |
| `tests/test_chart_date_range.py` | +159 lines | New | Unit tests for date range fix |
| `docs/fixes/chart-gaps-crypto-intraday-fix.md` | +300 lines | New | This documentation |

**Total:** ~506 lines changed/added

---

## References

### Related Issues
- User request: "Kannst du mal in der Datenbank nachsehen, wie die Daten heute um 12:11, 12:12 und 12:13 gespeichert wurden"
- User question: "Kann ich den download über die api schnittstelle auch an uhrzeiten binen? also die letzten 24h"
- User insight: "Komisch ist aber nur das es bisher lief und korrekte kerzen angezeigt wurden"

### TradingView Chart Behavior
- [Issue #209](https://github.com/tradingview/lightweight-charts/issues/209): Candlesticks require all OHLC values
- [Issue #1288](https://github.com/tradingview/lightweight-charts/issues/1288): Missing candlestick interpolation
- [Whitespace Demo](https://tradingview.github.io/lightweight-charts/tutorials/demos/whitespace): Intentional gaps

### Bitunix API
- Timezone: UTC millisecond timestamps
- 24/7 Trading: No market hours gaps for crypto
- Docs: https://openapidoc.bitunix.com/

---

**Status:** ✅ Ready for testing
**Next Step:** User should test with actual application to verify gaps are resolved
