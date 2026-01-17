# Progressive Chart Loading - Quick Display + Background History Download

**Date:** 2026-01-17
**Feature:** Progressive loading for instant chart display
**Purpose:** Show chart within 1-2 seconds, download full history in background
**Status:** 🔄 Planned

---

## Problem Statement

### Current Behavior (With Incremental Sync)

```
User loads NEW symbol (ETHUSDT, no DB data):
  → System fetches 365 days from API (~525,600 bars @ 1min)
  → Download time: ~44 minutes (2,628 API requests)
  → User waits... ⏳⏳⏳
  → Chart finally appears after 44 minutes ❌
```

**Issue:** Poor UX for first-time symbol load. User expects instant feedback.

---

## Solution: Progressive Loading

### Two-Phase Loading Strategy

#### Phase 1: Quick Load (Instant Display)
```
User clicks "Load Chart":
  ✅ Fetch only last 24 hours (1,440 bars @ 1min)
  ✅ Time: 1-2 seconds (7-8 API requests)
  ✅ Chart displays immediately
  ✅ Status: "✓ Loaded (24h view)"
  ✅ Period dropdown: Only "1D", "2D" enabled (rest grayed out)
```

#### Phase 2: Background History Download (Silent)
```
While user views chart:
  🔄 Background worker starts
  🔄 Downloads remaining 364 days (524,160 bars)
  🔄 Time: ~43 minutes (running in background)
  🔄 Status: "🔄 Downloading history... 15% (54/365 days)"

  User can:
    ✅ Analyze visible 24h data
    ✅ Switch symbols (pauses download)
    ✅ Close app (download resumes on restart)
    ❌ Select 5D/1W/1M/etc (disabled during download)

When download completes:
  ✅ Status: "✅ History complete! Reload chart for full data"
  ✅ Period dropdown: All options enabled
  ✅ Auto-refresh chart (or manual click)
  ✅ Full 365-day data available
```

---

## Implementation Plan

### File Changes

#### 1. New Background Worker

**File:** `src/ui/workers/background_history_worker.py` (NEW)

```python
class BackgroundHistoryWorker(QThread):
    """Background worker to download full history without blocking UI."""

    progress = pyqtSignal(int, str)  # (percentage, message)
    finished = pyqtSignal(bool, str, dict)
    error = pyqtSignal(str)

    def __init__(self, symbol, timeframe, days, provider_type):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.days = days
        self.provider_type = provider_type
        self._cancelled = False

    def run(self):
        """Download full history in background."""
        # Skip first 24h (already loaded in quick phase)
        start_date = datetime.now(timezone.utc) - timedelta(days=self.days)
        quick_load_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        # Download from start_date to quick_load_cutoff (avoiding duplicate 24h)
        # Use same logic as HistoricalDownloadWorker but resume-capable
        # Emit progress every X bars

    def cancel(self):
        """Cancel background download."""
        self._cancelled = True
```

#### 2. Modify `load_symbol()` for Progressive Loading

**File:** `src/ui/widgets/chart_mixins/data_loading_symbol.py`
**Method:** `load_symbol()` (lines 36-154)

**Changes:**

```python
async def load_symbol(self, symbol: str, data_provider: Optional[str] = None):
    """Load symbol with progressive loading: quick 24h + background full history."""

    # ... (existing setup) ...

    # NEW: Check if full history exists in database
    needs_full_download = await self._check_needs_full_download(symbol, lookback_days)

    if needs_full_download:
        logger.info(f"📥 Progressive loading for {symbol}: Quick 24h + background full history")

        # Phase 1: Quick load last 24h
        quick_bars = await self._quick_load_24h(symbol, provider_source, timeframe, asset_class)

        if quick_bars:
            # Display chart immediately
            df = self.parent._resolution.bars_to_dataframe(quick_bars)
            self.parent.load_data(df)

            # Lock period dropdown to intraday only
            self._lock_period_dropdown()

            # Status: Quick load complete
            self.set_loaded_status("database+API (24h view)")
            self.parent.market_status_label.setText("✓ Loaded (24h) 🔄 Downloading full history...")

            # Phase 2: Start background download
            self._start_background_history_download(symbol, provider_source, timeframe, lookback_days)

            return

    # Normal flow: Full data available or incremental sync
    # ... (existing code) ...
```

**New Helper Methods:**

```python
async def _check_needs_full_download(self, symbol: str, lookback_days: int) -> bool:
    """Check if full history download is needed.

    Returns True if:
    - Database empty for symbol
    - Database has < 50% of requested days
    """
    db_provider = self.parent.history_manager.providers.get(DataSource.DATABASE)
    if not db_provider:
        return False

    last_timestamp = await db_provider.get_last_timestamp(symbol)
    if not last_timestamp:
        return True  # DB empty

    # Check coverage
    now = datetime.now(timezone.utc)
    db_days_coverage = (now - last_timestamp).days

    if db_days_coverage > lookback_days * 0.5:
        logger.info(f"Database has {db_days_coverage} days old data, need {lookback_days} days")
        return True

    return False

async def _quick_load_24h(self, symbol, provider_source, timeframe, asset_class):
    """Quick load last 24 hours for instant chart display."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=24)

    request = DataRequest(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe=timeframe,
        asset_class=asset_class,
        source=provider_source
    )

    bars, source = await self.parent.history_manager.fetch_data(request)
    logger.info(f"📥 Quick loaded {len(bars)} bars (24h) from {source}")
    return bars

def _lock_period_dropdown(self):
    """Lock period dropdown to intraday only during background download."""
    if not hasattr(self.parent, 'period_combo'):
        return

    # Disable all items except 1D, 2D
    for i in range(self.parent.period_combo.count()):
        item_text = self.parent.period_combo.itemText(i)
        if item_text not in ["1D", "2D"]:
            # Disable item (requires model access)
            model = self.parent.period_combo.model()
            item = model.item(i)
            if item:
                item.setEnabled(False)

def _unlock_period_dropdown(self):
    """Unlock all period options after background download completes."""
    if not hasattr(self.parent, 'period_combo'):
        return

    # Enable all items
    for i in range(self.parent.period_combo.count()):
        model = self.parent.period_combo.model()
        item = model.item(i)
        if item:
            item.setEnabled(True)

def _start_background_history_download(self, symbol, provider_source, timeframe, lookback_days):
    """Start background worker to download full history."""
    from src.ui.workers.background_history_worker import BackgroundHistoryWorker

    self._bg_worker = BackgroundHistoryWorker(
        symbol=symbol,
        timeframe=timeframe,
        days=lookback_days,
        provider_type=provider_source.value
    )

    # Connect signals
    self._bg_worker.progress.connect(self._on_bg_download_progress)
    self._bg_worker.finished.connect(self._on_bg_download_finished)
    self._bg_worker.error.connect(self._on_bg_download_error)

    # Start worker
    self._bg_worker.start()
    logger.info(f"🔄 Background download started for {symbol} ({lookback_days} days)")

def _on_bg_download_progress(self, percentage: int, message: str):
    """Handle background download progress updates."""
    # Update status label
    self.parent.market_status_label.setText(
        f"🔄 Downloading history... {percentage}% - {message}"
    )

def _on_bg_download_finished(self, success: bool, message: str, results: dict):
    """Handle background download completion."""
    # Unlock period dropdown
    self._unlock_period_dropdown()

    if success:
        # Update status
        self.parent.market_status_label.setText(
            "✅ History complete! Reloading chart..."
        )

        # Auto-refresh chart with full data
        logger.info(f"✅ Background download complete, reloading chart with full data")
        asyncio.ensure_future(self.load_symbol(self.parent.current_symbol, self.parent.current_data_provider))
    else:
        # Show error
        self.parent.market_status_label.setText(
            f"⚠ Background download failed: {message}"
        )

def _on_bg_download_error(self, error_message: str):
    """Handle background download error."""
    logger.error(f"Background download error: {error_message}")
    self._unlock_period_dropdown()
    self.parent.market_status_label.setText(
        f"⚠ Download error: {error_message[:30]}"
    )
```

---

## User Experience Flow

### Scenario: User loads ETHUSDT for first time (no DB data)

**Step 1: User Action**
```
User: Selects "ETHUSDT" from dropdown
User: Clicks "Load Chart"
```

**Step 2: Quick Load (1-2 seconds)**
```
System: "Loading ETHUSDT..."
System: Fetches last 24 hours from Bitunix API (1,440 bars)
System: Displays chart immediately ✅
Status: "✓ Loaded (24h) 🔄 Downloading full history..."
Period Dropdown: [1D ✓] [2D ✓] [5D ✗] [1W ✗] [1M ✗] ...
```

**Step 3: Background Download (43 minutes)**
```
User: Analyzes visible 24h data
User: Can pan/zoom within 24h window
User: Can switch to other symbols (pauses download)

Status Updates (every 30 seconds):
  "🔄 Downloading history... 5% (18/365 days)"
  "🔄 Downloading history... 15% (54/365 days)"
  "🔄 Downloading history... 50% (182/365 days)"
  "🔄 Downloading history... 85% (310/365 days)"
```

**Step 4: Download Complete**
```
Status: "✅ History complete! Reloading chart..."
Period Dropdown: All options enabled ✅
Chart: Auto-refreshes with full 365-day data
User: Can now select any period (5D, 1W, 1M, etc.)
```

---

## Configuration Options

### Settings → Market Data → Progressive Loading

```
[✓] Enable progressive loading (quick 24h + background full history)
    Full history days: [___365___] days
    Background download: [🔄 Start] [⏸️ Pause] [🗑️ Cancel]

    Current status:
    - Symbol: ETHUSDT
    - Progress: 45% (164/365 days)
    - Speed: ~1,200 bars/min
    - ETA: 22 minutes
```

### Auto-Start Background Download

```python
# In settings
auto_start_background_download = True  # Default: True
background_download_days = 365  # Default: 365
quick_load_hours = 24  # Default: 24
```

---

## Edge Cases & Error Handling

### Case 1: User Switches Symbol During Background Download

```
Background download running: ETHUSDT (25% complete)
User: Loads BTCUSDT

Action:
  1. Pause ETHUSDT download
  2. Load BTCUSDT (quick 24h or full from DB)
  3. Resume ETHUSDT download in background (lower priority)

Benefit: User not blocked, downloads continue
```

### Case 2: Network Error During Background Download

```
Background download: 150/365 days complete
Error: API timeout / rate limit

Action:
  1. Retry with exponential backoff
  2. Resume from last successful timestamp
  3. If persistent error: Show "⚠ Download paused - retry manually"

Benefit: Download resumes where it left off
```

### Case 3: User Selects Disabled Period (5D) During Download

```
Period Dropdown: 5D is grayed out (disabled)
User: Clicks on 5D

Action:
  1. Show tooltip: "Downloading full history... 45% complete"
  2. Optionally: Dialog "Download in progress. Switch to 5D after completion or cancel download?"

Benefit: User understands why option is disabled
```

### Case 4: App Closes During Background Download

```
Background download: 200/365 days complete
User: Closes app

On Next App Start:
  1. Check database: ETHUSDT has 200 days of data
  2. Detect incomplete download (< 365 days)
  3. Ask: "Resume background download for ETHUSDT?"
     [Yes] [No, use current data]

Benefit: Download persists across sessions
```

---

## Performance Comparison

### Without Progressive Loading
```
User loads ETHUSDT (no DB data):
  Waiting time: 44 minutes (full 365-day download)
  User experience: ⏳ Staring at loading screen
  Can use chart: After 44 minutes
```

### With Progressive Loading
```
User loads ETHUSDT (no DB data):
  Waiting time: 1-2 seconds (24h quick load)
  User experience: ✅ Chart appears instantly
  Can use chart: Immediately (24h data)
  Full data: Available after 43 minutes (background)

  User productivity: +98% (43 min wasted vs 1 sec wait)
```

---

## Technical Challenges

### Challenge 1: Duplicate Data Prevention

**Problem:** Quick load fetches 24h, background download fetches 365 days (includes same 24h)

**Solution:**
```python
# Background worker skips already-loaded 24h
start_date = now - timedelta(days=365)
quick_cutoff = now - timedelta(hours=24)

# Download only: start_date → quick_cutoff (avoiding duplicate 24h)
await provider.fetch_bars(start_date, quick_cutoff, ...)
```

### Challenge 2: Database Merge During Background Download

**Problem:** User might trigger incremental sync while background download runs

**Solution:**
```python
# Lock database writes during background download
with db_lock:
    await db.bulk_insert(bars)

# Or: Use queue for background inserts
background_insert_queue.put(bars)
```

### Challenge 3: Memory Usage

**Problem:** Holding 525,600 bars in memory during background download

**Solution:**
```python
# Chunk-based insertion (insert every 10,000 bars)
for chunk in chunks(bars, chunk_size=10000):
    await db.bulk_insert(chunk)
    del chunk  # Free memory
```

---

## Future Enhancements

### 1. Smart Background Prioritization

**Idea:** Download most recent days first (descending order)
```
Quick load: Last 24h (now - 24h)
Background phase 1: Last 7 days (now - 7d → now - 24h)
Background phase 2: Last 30 days (now - 30d → now - 7d)
Background phase 3: Last 365 days (now - 365d → now - 30d)
```

**Benefit:** User can access 7D/1M earlier without waiting for full 365d

### 2. Adaptive Quick Load Window

**Idea:** Adjust quick load window based on requested period
```
Period 1D: Quick load 24h
Period 5D: Quick load 5 days
Period 1M: Quick load 30 days
```

**Benefit:** Faster availability of requested period data

### 3. Background Download Scheduler

**Idea:** Download full history during off-peak hours
```
Settings: "Download full history overnight (00:00-06:00)"
User loads symbol at 14:00: Quick 24h only
At 00:00: Background download starts automatically
At 06:00: Full data available
```

**Benefit:** Doesn't interfere with daytime trading

---

## Related Files

| File | Type | Description |
|------|------|-------------|
| `src/ui/workers/background_history_worker.py` | New (300 LOC) | Background download worker |
| `src/ui/widgets/chart_mixins/data_loading_symbol.py` | Modified (+200 LOC) | Progressive loading logic |
| `docs/features/progressive-chart-loading.md` | New | This documentation |

**Total:** ~500 lines new code

---

## Status

- ✅ Design complete
- 🔄 Implementation planned
- ⏳ Awaiting approval

**Next Steps:**
1. Implement `BackgroundHistoryWorker` class
2. Modify `load_symbol()` for two-phase loading
3. Add period dropdown lock/unlock logic
4. Test with ETHUSDT (no DB data)
5. Test download pause/resume
6. Test app restart with incomplete download

---

**User Requirement:** "Chart sofort anzeigen (24h), Historie im Hintergrund laden, nur Intraday wählbar bis Download fertig, dann Daten neu initialisieren"

✅ All requirements addressed in this design.
