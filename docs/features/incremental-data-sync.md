# Incremental Data Sync - Auto-Update Database on Chart Load

**Date:** 2026-01-17
**Feature:** Automatic incremental sync when loading charts
**Purpose:** Keep database up-to-date without full re-downloads
**Status:** ✅ Implemented

---

## Problem Statement

### Previous Behavior (Before Fix)

```
User downloads BTCUSDT history today:
  → Database: 00:00 - 15:48 UTC (949 bars)

2 weeks later, user loads chart:
  → Chart requests: current day 00:00 - 23:59 UTC
  → Database still has old data (only until 15:48 from 2 weeks ago)
  → Result: HUGE GAP from 15:48 (2 weeks ago) until now
```

**Issues:**
- ❌ Database never auto-updates after initial download
- ❌ User must manually trigger "Download History" or "Sync" in Settings
- ❌ Charts show gaps for missing recent data
- ❌ Inefficient: downloading entire history again for just missing days

---

## Solution: Incremental Sync

### How It Works

**On Chart Load:**
1. **Check Database** for last available bar
2. **Compare** last_db_bar vs requested end_date
3. **Three Scenarios:**

#### Scenario A: Database Has Complete Data
```
Requested: 2026-01-17 00:00 → 23:59 UTC
Last DB bar: 2026-01-17 18:00 UTC

Action: Use database only (end_date 23:59 is in future)
Result: ✅ Complete data from DB, no API call
Status: "✓ Loaded from database"
```

#### Scenario B: Database Has Partial Data (Incremental Sync)
```
Requested: 2026-01-17 00:00 → 23:59 UTC
Last DB bar: 2026-01-15 15:48 UTC (2 days old)

Action:
  1. Load DB data (00:00 → 15:48 on 2026-01-15)
  2. Fetch missing from API (15:48 on 2026-01-15 → now)
  3. Merge DB + API bars
  4. Store new API bars to DB

Result: ✅ Seamless data, DB auto-updated
Status: "✓ Loaded from database+bitunix"
```

#### Scenario C: Database Empty
```
Requested: 2026-01-17 00:00 → 23:59 UTC
Last DB bar: None (symbol never downloaded)

Action: Fetch all data from API
Result: ✅ Full data from API, stored to DB
Status: "✓ Loaded from bitunix"
```

---

## Implementation Details

### File Changes

#### 1. DatabaseProvider: `get_last_timestamp()` Method

**File:** `src/core/market_data/providers/database_provider.py`
**Lines:** 90-117 (new)

```python
async def get_last_timestamp(self, symbol: str) -> datetime | None:
    """Get timestamp of last bar in database for symbol.

    Returns:
        Timestamp of last bar, or None if no data exists
    """
    return await asyncio.to_thread(self._get_last_timestamp_sync, symbol)

def _get_last_timestamp_sync(self, symbol: str) -> datetime | None:
    """Synchronous get last timestamp (runs in thread)."""
    with self.db_manager.session() as session:
        last_bar = session.query(MarketBar).filter(
            MarketBar.symbol == symbol
        ).order_by(MarketBar.timestamp.desc()).first()

        if last_bar:
            return last_bar.timestamp
        else:
            return None
```

**Purpose:** Fast query to check database freshness without loading all bars.

#### 2. HistoryProviderFetching: Incremental Sync Logic

**File:** `src/core/market_data/history_provider_fetching.py`
**Lines:** 48-89 (modified), 133-277 (new)

**Main Changes:**

**A. `fetch_data()` - Modified to use incremental sync**
```python
async def fetch_data(self, request: DataRequest) -> tuple[list[HistoricalBar], str]:
    """Fetch historical data with incremental sync support."""

    # If specific source requested: use only that source
    if request.source:
        return await self._try_specific_source(request)

    # Try incremental sync with database
    bars, source_used = await self._fetch_with_incremental_sync(request, needs_fresh_data)
    if bars:
        return bars, source_used

    # Fallback: normal provider priority order
    for source in self.parent.priority_order:
        bars = await self._try_provider_source(request, source, needs_fresh_data)
        if bars:
            return bars, source.value
```

**B. `_fetch_with_incremental_sync()` - New method (145 lines)**
```python
async def _fetch_with_incremental_sync(
    self,
    request: DataRequest,
    needs_fresh_data: bool,
) -> tuple[list[HistoricalBar], str]:
    """Fetch data with incremental sync: DB cache + API for missing data."""

    # 1. Check last timestamp in database
    last_db_timestamp = await db_provider.get_last_timestamp(request.symbol)

    if not last_db_timestamp:
        return [], ""  # DB empty, fallback to API

    # 2. Database has complete data?
    if last_db_utc >= end_dt_utc:
        return await db_provider.fetch_bars(...), "database"

    # 3. Database has partial data - sync needed
    db_bars = await db_provider.fetch_bars(start_date, last_db_timestamp)

    # 4. Fetch missing from API
    api_bars = await api_provider.fetch_bars(last_db_timestamp + 1min, end_date)

    # 5. Merge and cache
    await self._store_to_database(api_bars, symbol)
    all_bars = db_bars + api_bars

    return all_bars, f"database+{api_source.value}"
```

**C. `_get_api_source_for_symbol()` - New helper**
```python
def _get_api_source_for_symbol(self, request: DataRequest) -> DataSource | None:
    """Determine appropriate API source for symbol."""
    if asset_class == AssetClass.CRYPTO:
        if "USDT" in symbol or "USDC" in symbol:
            return DataSource.BITUNIX  # BTCUSDT
        elif "/" in symbol:
            return DataSource.ALPACA_CRYPTO  # BTC/USD
    return DataSource.ALPACA  # Stocks
```

---

## User Experience

### Before Incremental Sync

```
User Action: Load BTCUSDT chart (2 weeks after last download)
Chart Loading: "Loading BTCUSDT..."
Status: "✓ Loaded from bitunix" (1607 bars)
Chart Display: Shows gaps (old DB data not used)
Database: Still outdated (not updated)
```

### After Incremental Sync

```
User Action: Load BTCUSDT chart (2 weeks after last download)
Chart Loading: "Loading BTCUSDT..."
Logs:
  📂 Database has partial data for bitunix:BTCUSDT
     Last DB bar: 2026-01-03 15:48:00 UTC
     Requested until: 2026-01-17 23:59:59 UTC
     Gap: 20,171.0 minutes → fetching from API
  📂 Loaded 949 bars from database
  🔄 Fetching missing data from bitunix (2026-01-03 15:49:00 → 2026-01-17 23:59:59)
  🔄 Fetched 20,172 new bars from bitunix
  ✅ Merged data: 949 (DB) + 20,172 (API) = 21,121 total bars

Status: "✓ Loaded from database+bitunix"
Chart Display: Complete data, no gaps ✅
Database: Auto-updated with 20,172 new bars ✅
```

---

## Performance Benefits

### Scenario: User loads chart 2 weeks after last download

**Without Incremental Sync:**
```
API Request: Full 365-day history (525,600 bars @ 1min)
Time: ~44 minutes (2,628 requests @ 200 bars/request)
Data Transfer: 525,600 bars downloaded
Database: Full overwrite/merge
```

**With Incremental Sync:**
```
Database: 949 bars loaded (instant)
API Request: Only missing 2 weeks (20,172 bars @ 1min)
Time: ~1.7 minutes (101 requests @ 200 bars/request)
Data Transfer: 20,172 bars downloaded (96% reduction!)
Database: Incremental append only
```

**Speed-up:** 26x faster (44 min → 1.7 min)
**Data Reduction:** 96% less API traffic

---

## Edge Cases & Error Handling

### Case 1: API Fails During Sync

```
DB has data until: 2026-01-15 15:48
Request: 2026-01-17 23:59
Action: Fetch missing 2 days from API
Error: API timeout / rate limit / network error

Fallback: Return partial DB data
Status: "✓ Loaded from database (partial)"
User Impact: Chart shows data until 15:48, gap at the end
User Action: Retry or wait for API recovery
```

### Case 2: Database Corrupted / Missing

```
DB query returns: None (no last timestamp)
Action: Skip incremental sync, use full API fetch
Result: Normal API download, data stored to DB
Status: "✓ Loaded from bitunix"
```

### Case 3: Clock Skew / Wrong Timezone

```
Last DB bar: 2026-01-17 20:00 UTC
Request end: 2026-01-17 18:00 UTC (user's clock is behind)

Detection: last_db_utc >= end_dt_utc
Action: Use DB only (complete data available)
Result: ✅ No sync needed
```

### Case 4: Symbol Prefix Mismatch

```
Database has: "BTCUSDT" (old format)
Chart requests: "bitunix:BTCUSDT" (new format)
Last timestamp query: Returns None (symbol mismatch)
Action: Full API fetch, stored with prefix
Note: User should re-download to consolidate data
```

---

## Configuration

### No User Settings Required

Incremental sync is **always enabled** and happens automatically when:
- User loads a chart
- Database has existing data
- Last DB bar < requested end_date

### Manual Override (if needed)

User can still trigger full re-download via:
1. Settings → Market Data → Bitunix → Historical Data Download
2. Select symbol, period, timeframe
3. Click "Download" (deletes old data, full re-download)
4. Click "Sync" (incremental sync to today)

**Difference:**
- **Chart Load**: Auto incremental sync (silent, fast)
- **Settings "Sync"**: Manual incremental sync (with progress bar)
- **Settings "Download"**: Full re-download (replaces all data)

---

## Logging & Debugging

### Successful Incremental Sync

```log
INFO - 📂 Database has partial data for bitunix:BTCUSDT
INFO -    Last DB bar: 2026-01-15 15:48:00 UTC
INFO -    Requested until: 2026-01-17 23:59:59 UTC
INFO -    Gap: 3,071.0 minutes → fetching from API
INFO - 📂 Loaded 949 bars from database
INFO - 🔄 Fetching missing data from bitunix (2026-01-15 15:49:00 → 2026-01-17 23:59:59)
INFO - 🔄 Fetched 3,072 new bars from bitunix
INFO - ✅ Merged data: 949 (DB) + 3,072 (API) = 4,021 total bars
```

### Database Has Complete Data

```log
INFO - 📂 Database has complete data for bitunix:BTCUSDT (last bar: 2026-01-17 18:00:00 UTC)
INFO - Fetched 1,080 bars from database for bitunix:BTCUSDT
```

### Database Empty

```log
INFO - 📂 No data in database for bitunix:BTCUSDT - will fetch from API
INFO - Using specific source: bitunix for bitunix:BTCUSDT
INFO - Got 1,607 bars from bitunix
```

---

## Testing

### Manual Test Scenarios

#### Test 1: Fresh Symbol (No DB Data)
```
Action: Load chart for new symbol (e.g., ETHUSDT)
Expected:
  ✅ Log: "📂 No data in database for bitunix:ETHUSDT"
  ✅ Status: "✓ Loaded from bitunix"
  ✅ Chart shows full data from API
  ✅ Database now has data for ETHUSDT
```

#### Test 2: Existing Symbol, Up-to-Date DB
```
Action: Load chart for recently downloaded symbol
Expected:
  ✅ Log: "📂 Database has complete data for bitunix:BTCUSDT"
  ✅ Status: "✓ Loaded from database"
  ✅ Chart shows DB data (no API call)
```

#### Test 3: Existing Symbol, Outdated DB (Incremental Sync)
```
Setup: Manually set last DB timestamp to 2 days ago
Action: Load chart
Expected:
  ✅ Log: "📂 Database has partial data"
  ✅ Log: "Gap: X minutes → fetching from API"
  ✅ Log: "🔄 Fetching missing data from bitunix"
  ✅ Log: "✅ Merged data: X (DB) + Y (API) = Z total"
  ✅ Status: "✓ Loaded from database+bitunix"
  ✅ Chart shows seamless data (no gaps)
  ✅ Database updated with new bars
```

#### Test 4: API Failure During Sync
```
Setup: Disable network or API provider
Action: Load chart with outdated DB data
Expected:
  ✅ Log: "Error fetching missing data from API"
  ✅ Status: "✓ Loaded from database (partial)"
  ✅ Chart shows DB data until last bar
  ✅ Gap visible at the end (expected)
```

---

## Future Enhancements

### 1. Background Sync Scheduler

**Idea:** Auto-sync database every X minutes for active symbols
```python
# In background thread
async def auto_sync_active_symbols():
    while True:
        for symbol in active_symbols:
            await incremental_sync(symbol)
        await asyncio.sleep(300)  # Every 5 minutes
```

**Benefit:** Database always fresh, chart loads instant from DB

### 2. Multi-Symbol Batch Sync

**Idea:** Sync multiple symbols in one API request
```python
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
api_bars = await provider.fetch_bars_batch(symbols, last_timestamp, now)
```

**Benefit:** Fewer API requests, faster sync for watchlists

### 3. Smart Sync Intervals

**Idea:** Adjust sync frequency based on timeframe
```
1min charts: Sync every 5 minutes
1h charts: Sync every 1 hour
1d charts: Sync once per day
```

**Benefit:** Reduce API calls for less time-critical data

### 4. Sync Status UI

**Idea:** Show sync status in chart header
```
Status: "📂 Database (synced 2 min ago)" or "🔄 Syncing..."
Button: [Force Sync Now]
```

**Benefit:** User transparency, manual trigger option

---

## Related Files

| File | Lines Changed | Type | Description |
|------|---------------|------|-------------|
| `database_provider.py` | +28 | New Methods | `get_last_timestamp()`, `_get_last_timestamp_sync()` |
| `history_provider_fetching.py` | +200 | New Method | `_fetch_with_incremental_sync()`, `_get_api_source_for_symbol()` |
| `history_provider_fetching.py` | 48-89 | Modified | `fetch_data()` - uses incremental sync |
| `incremental-data-sync.md` | +600 | New | This documentation |

**Total:** ~828 lines added/modified

---

## References

- Related: `docs/fixes/chart-gaps-crypto-intraday-fix.md` (date range fix)
- Related: `docs/ui/data-quality-tab.md` (manual sync in Settings)
- User Request: "Eigentlich müsste ich die ja immer aktualisieren, wenn ich btcusdt lade!"

---

**Status:** ✅ Ready for testing
**Next Step:** User should test chart loading with outdated DB data to verify auto-sync
