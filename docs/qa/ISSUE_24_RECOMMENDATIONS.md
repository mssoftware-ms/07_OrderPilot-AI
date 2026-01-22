# Issue #24 - Implementation Recommendations Checklist

**Status:** ✅ Fix Approved - Follow-up Work Needed
**Priority Levels:** 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW

---

## 📋 Quick Action Summary

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 🔴 HIGH | Add unit tests | 2 hours | Prevent regressions |
| 🔴 HIGH | Add inline docs | 30 mins | Developer guidance |
| 🔴 HIGH | Add validation | 1 hour | Robustness |
| 🟡 MEDIUM | Centralize logic | 4 hours | DRY principle |
| 🟡 MEDIUM | Update ARCHITECTURE.md | 1 hour | Team alignment |
| 🟢 LOW | Add caching | 2 hours | Performance |
| 🟢 LOW | Add metrics | 1 hour | Observability |

**Total Effort:** ~12 hours to complete all recommendations

---

## 🔴 HIGH PRIORITY (Implement This Sprint)

### Recommendation #1: Add Unit Tests
**Effort:** 2 hours | **Impact:** Prevent regressions | **Risk if skipped:** HIGH

#### Implementation Checklist

- [ ] **Create test file:** `tests/ui/widgets/test_compact_chart_widget_resample.py`

- [ ] **Test Case 1: Unnamed DatetimeIndex**
  ```python
  def test_resample_with_unnamed_index(self):
      """Test resample handles unnamed DatetimeIndex correctly."""
      # Given: DataFrame with unnamed DatetimeIndex
      df = pd.DataFrame({
          'open': [100, 101, 102],
          'high': [102, 103, 104],
          'low': [99, 100, 101],
          'close': [101, 102, 103],
          'volume': [1000, 1100, 1200]
      }, index=pd.date_range('2024-01-01', periods=3, freq='1min'))

      assert df.index.name is None  # Verify unnamed

      # When: Resample to 5m
      widget = CompactChartWidget()
      result = widget._resample_data(df, "5m")

      # Then: Should have 'time' column (unix timestamp)
      assert 'time' in result.columns
      assert len(result) > 0
      assert result['time'].dtype == 'int64'
  ```

- [ ] **Test Case 2: Named DatetimeIndex (timestamp)**
  ```python
  def test_resample_with_timestamp_index(self):
      """Test resample with index named 'timestamp' (Alpaca format)."""
      df = pd.DataFrame({
          'open': [100], 'high': [102], 'low': [99],
          'close': [101], 'volume': [1000]
      }, index=pd.DatetimeIndex(
          [pd.Timestamp('2024-01-01')],
          name='timestamp'  # Alpaca uses 'timestamp'
      ))

      widget = CompactChartWidget()
      result = widget._resample_data(df, "1h")

      assert 'time' in result.columns
      assert result['time'].iloc[0] > 0  # Valid unix timestamp
  ```

- [ ] **Test Case 3: Named DatetimeIndex (datetime)**
  ```python
  def test_resample_with_datetime_index(self):
      """Test resample with index named 'datetime' (Bitunix format)."""
      df = pd.DataFrame({
          'open': [100], 'high': [102], 'low': [99],
          'close': [101], 'volume': [1000]
      }, index=pd.DatetimeIndex(
          [pd.Timestamp('2024-01-01')],
          name='datetime'  # Bitunix uses 'datetime'
      ))

      widget = CompactChartWidget()
      result = widget._resample_data(df, "1h")

      assert 'time' in result.columns
  ```

- [ ] **Test Case 4: Input with 'time' column (not index)**
  ```python
  def test_resample_with_time_column(self):
      """Test resample when input has 'time' column instead of datetime index."""
      df = pd.DataFrame({
          'time': [1704067200, 1704067260, 1704067320],  # Unix timestamps
          'open': [100, 101, 102],
          'high': [102, 103, 104],
          'low': [99, 100, 101],
          'close': [101, 102, 103],
          'volume': [1000, 1100, 1200]
      })

      widget = CompactChartWidget()
      result = widget._resample_data(df, "5m")

      assert 'time' in result.columns
      assert len(result) > 0
  ```

- [ ] **Test Case 5: Empty DataFrame**
  ```python
  def test_resample_empty_dataframe(self):
      """Test resample handles empty DataFrame gracefully."""
      df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

      widget = CompactChartWidget()
      result = widget._resample_data(df, "1h")

      assert result.empty or 'time' in result.columns
  ```

- [ ] **Test Case 6: OHLC Correctness**
  ```python
  def test_resample_ohlc_correctness(self):
      """Verify OHLC aggregation logic is mathematically correct."""
      # Given: 3 minutes of data with known OHLC
      df = pd.DataFrame({
          'open': [100, 105, 103],
          'high': [102, 108, 107],
          'low': [99, 104, 102],
          'close': [101, 107, 106],
          'volume': [1000, 1100, 1200]
      }, index=pd.date_range('2024-01-01 10:00', periods=3, freq='1min'))

      # When: Resample to 5m (all 3 bars in one period)
      widget = CompactChartWidget()
      result = widget._resample_data(df, "5m")

      # Then: Verify aggregation
      assert result['open'].iloc[0] == 100    # First open
      assert result['high'].iloc[0] == 108    # Max of all highs
      assert result['low'].iloc[0] == 99      # Min of all lows
      assert result['close'].iloc[0] == 106   # Last close
      assert result['volume'].iloc[0] == 3300 # Sum of volumes
  ```

- [ ] **Test Case 7: All Timeframes**
  ```python
  def test_resample_all_timeframes(self):
      """Test all supported timeframes (1m, 5m, 15m, 1h, 4h, 1d)."""
      df = pd.DataFrame({
          'open': [100] * 1440,
          'high': [102] * 1440,
          'low': [99] * 1440,
          'close': [101] * 1440,
          'volume': [1000] * 1440
      }, index=pd.date_range('2024-01-01', periods=1440, freq='1min'))

      widget = CompactChartWidget()

      for tf in ["1m", "5m", "15m", "1h", "4h", "1d"]:
          result = widget._resample_data(df, tf)
          assert 'time' in result.columns, f"Failed for {tf}"
          assert len(result) > 0, f"Empty result for {tf}"
  ```

- [ ] **Run tests:** `pytest tests/ui/widgets/test_compact_chart_widget_resample.py -v`

---

### Recommendation #2: Add Inline Documentation
**Effort:** 30 mins | **Impact:** Developer guidance | **Risk if skipped:** MEDIUM

#### Implementation Checklist

- [ ] **Update function docstring** in `compact_chart_widget.py`:
  ```python
  def _resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
      """Resample OHLCV data to selected timeframe.

      This function handles datetime conversion robustly by using dynamic column
      detection after reset_index(). Pandas does not guarantee the datetime column
      will be named "index" - it uses the original index name (e.g., "timestamp"
      for Alpaca data, "datetime" for Bitunix data, or "index" if unnamed).

      Args:
          df: OHLCV DataFrame with either:
              - DatetimeIndex (preferred)
              - 'time' column with unix timestamps or datetime strings
          timeframe: Target timeframe string
              Supported: '1m', '5m', '15m', '1h', '4h', '1d'

      Returns:
          Resampled DataFrame with columns: time, open, high, low, close, volume
          where 'time' is unix timestamp (seconds since epoch, int64)

      Note:
          The resample logic uses pandas' standard OHLC aggregation:
          - open: first price in period
          - high: maximum price in period
          - low: minimum price in period
          - close: last price in period
          - volume: sum of volumes in period

      Issue Reference:
          See Issue #24 for details on why dynamic column detection is used
          after reset_index() instead of hardcoded "index" column access.
      """
  ```

- [ ] **Add inline comment at critical line** (Line 357):
  ```python
  resampled = resampled.reset_index()
  # Get datetime column dynamically - pandas uses original index name
  # (e.g., "timestamp" for Alpaca, "datetime" for Bitunix, "index" if unnamed)
  # See Issue #24 for why we don't hardcode "index"
  datetime_col = resampled.columns[0]
  resampled["time"] = (resampled[datetime_col].astype("int64") // 10**9).astype(int)
  ```

- [ ] **Add example usage in docstring**:
  ```python
  """
  Examples:
      >>> # Example 1: DataFrame with DatetimeIndex
      >>> df = pd.DataFrame({
      ...     'open': [100, 101], 'high': [102, 103],
      ...     'low': [99, 100], 'close': [101, 102], 'volume': [1000, 1100]
      ... }, index=pd.date_range('2024-01-01', periods=2, freq='1min'))
      >>> result = widget._resample_data(df, "5m")

      >>> # Example 2: DataFrame with 'time' column (unix timestamps)
      >>> df = pd.DataFrame({
      ...     'time': [1704067200, 1704067260],
      ...     'open': [100, 101], 'high': [102, 103],
      ...     'low': [99, 100], 'close': [101, 102], 'volume': [1000, 1100]
      ... })
      >>> result = widget._resample_data(df, "5m")
  """
  ```

---

### Recommendation #3: Add Validation
**Effort:** 1 hour | **Impact:** Robustness | **Risk if skipped:** MEDIUM

#### Implementation Checklist

- [ ] **Add validation after reset_index()** (Insert after line 355):
  ```python
  resampled = resampled.reset_index()

  # Validation: Ensure reset_index() produced at least one column
  if resampled.empty or len(resampled.columns) == 0:
      logger.warning(f"Resample to {timeframe} produced empty result")
      return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

  # Get datetime column (guaranteed to be first column after reset_index)
  datetime_col = resampled.columns[0]

  # Validation: Ensure it's actually a datetime column
  if not pd.api.types.is_datetime64_any_dtype(resampled[datetime_col]):
      logger.error(
          f"Expected datetime column after reset_index, got {resampled[datetime_col].dtype}. "
          f"Column name: {datetime_col}"
      )
      return df  # Return original data as fallback

  # Convert to unix timestamp
  resampled["time"] = (resampled[datetime_col].astype("int64") // 10**9).astype(int)
  ```

- [ ] **Add import for logger** (if not already present):
  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```

- [ ] **Test validation with edge cases:**
  - [ ] Empty DataFrame
  - [ ] Non-datetime first column (should never happen, but defensive)
  - [ ] Very large DataFrame (performance test)

---

## 🟡 MEDIUM PRIORITY (Next Sprint)

### Recommendation #4: Centralize Resample Logic
**Effort:** 4 hours | **Impact:** DRY principle | **Risk if skipped:** LOW

#### Implementation Checklist

- [ ] **Create new module:** `src/core/market_data/resample_service.py`

- [ ] **Implement centralized service:**
  ```python
  """Centralized OHLCV resampling service.

  This module provides a single, well-tested implementation of OHLC resampling
  to eliminate code duplication across the codebase (11+ files with resample logic).
  """

  from typing import Literal
  import pandas as pd
  import logging

  logger = logging.getLogger(__name__)

  TimeframeStr = Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

  class OHLCVResampler:
      """Centralized OHLCV resampling service following pandas best practices."""

      # Map user-friendly timeframes to pandas offset strings
      TIMEFRAME_MAP = {
          "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
          "1h": "1h", "4h": "4h", "1d": "1d"
      }

      @classmethod
      def resample_ohlcv(
          cls,
          df: pd.DataFrame,
          target_tf: TimeframeStr,
          return_with_time_column: bool = False,
          validate: bool = True
      ) -> pd.DataFrame:
          """Resample OHLCV data with robust datetime handling.

          Args:
              df: DataFrame with OHLCV columns and DatetimeIndex
              target_tf: Target timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
              return_with_time_column: If True, adds 'time' column with unix timestamps
              validate: If True, validates result (recommended)

          Returns:
              Resampled DataFrame with DatetimeIndex (or 'time' column if requested)
          """
          # ... (Implementation with all edge case handling from Issue #24 fix)
  ```

- [ ] **Migrate existing resample implementations** (11 files):
  - [ ] `src/ui/widgets/compact_chart_widget.py` ← **Start here**
  - [ ] `src/ui/widgets/chart_shared/data_conversion.py`
  - [ ] `src/core/market_data/providers/database_provider.py`
  - [ ] `src/backtesting/data_loader.py`
  - [ ] `src/core/market_data/providers/bitunix_provider.py`
  - [ ] `src/core/market_data/resampler.py` ← **Refactor to use service**
  - [ ] `src/core/backtesting/mtf_resampler.py`
  - [ ] `src/core/pattern_db/timeframe_converter.py`
  - [ ] `src/core/tradingbot/timeframe_data_manager.py`
  - [ ] `src/ui/widgets/chart_mixins/data_loading_series.py`
  - [ ] `src/core/simulator/simulation_engine.py`

- [ ] **Add unit tests for service:** `tests/core/market_data/test_resample_service.py`

- [ ] **Update imports across codebase:**
  ```python
  from src.core.market_data.resample_service import OHLCVResampler

  # Old code:
  # resampled = df.resample("1h").agg({...})

  # New code:
  resampled = OHLCVResampler.resample_ohlcv(df, "1h")
  ```

---

### Recommendation #5: Update ARCHITECTURE.md
**Effort:** 1 hour | **Impact:** Team alignment | **Risk if skipped:** LOW

#### Implementation Checklist

- [ ] **Add section to ARCHITECTURE.md:**
  ```markdown
  ## Data Conventions: DateTime Handling

  ### Standard Pattern

  **Internal Storage:**
  - ALWAYS use DatetimeIndex (not 'time' column) during processing
  - ALWAYS use UTC timezone (`pd.to_datetime(..., utc=True)`)
  - Only convert to unix timestamp at UI/chart boundary

  **Resample Operations:**
  - Use centralized `OHLCVResampler` service
  - NEVER hardcode datetime column name after `reset_index()`
  - Use dynamic access: `datetime_col = df.columns[0]`

  ### Examples

  #### ✅ GOOD: Keep DateTime in Index
  ```python
  # Set DatetimeIndex with UTC
  df.index = pd.to_datetime(df["time"], unit="s", utc=True)
  df = df[["open", "high", "low", "close", "volume"]]

  # Resample with index
  resampled = df.resample("1h").agg({
      "open": "first",
      "high": "max",
      "low": "min",
      "close": "last",
      "volume": "sum"
  })

  # Keep datetime in index until chart layer
  # Only convert to unix timestamp for chart library
  chart_data = resampled.reset_index()
  datetime_col = chart_data.columns[0]  # Dynamic!
  chart_data["time"] = (chart_data[datetime_col].astype("int64") // 10**9).astype(int)
  ```

  #### ❌ BAD: Hardcoded Column Names
  ```python
  # DON'T DO THIS
  df = df.reset_index()
  df["time"] = df["index"]  # WRONG: "index" may not exist!
  ```

  ### Data Source Differences

  Different data sources use different datetime column names:

  | Source | DateTime Column Name | Index Name After reset_index() |
  |--------|---------------------|-------------------------------|
  | Alpaca | Internal: DatetimeIndex | `timestamp` |
  | Bitunix | Internal: DatetimeIndex | `datetime` |
  | CSV Import | Varies | Varies |
  | Manual Data | Often unnamed | `index` |

  **Solution:** Always use dynamic column access after `reset_index()`.

  ### Related Issues
  - Issue #24: Compact chart resample index/column confusion
  ```

- [ ] **Add to "Best Practices" section:**
  ```markdown
  ## Pandas Best Practices

  1. **Use DatetimeIndex for time series data**
     - Benefits: Automatic time-based indexing, resampling, date range selection
     - Pattern: `df.index = pd.to_datetime(df["time"], utc=True)`

  2. **Dynamic column access after reset_index()**
     - Problem: `reset_index()` uses original index name, not always "index"
     - Solution: `datetime_col = df.columns[0]`
     - See: Issue #24

  3. **OHLC Aggregation**
     - Open: `first` (first price in period)
     - High: `max` (maximum price in period)
     - Low: `min` (minimum price in period)
     - Close: `last` (last price in period)
     - Volume: `sum` (total volume in period)
  ```

---

## 🟢 LOW PRIORITY (Future Optimization)

### Recommendation #6: Add Caching
**Effort:** 2 hours | **Impact:** Performance | **Risk if skipped:** NONE

#### Implementation Checklist

- [ ] **Add LRU cache to compact_chart_widget.py:**
  ```python
  from functools import lru_cache

  class CompactChartWidget(QWidget):
      def __init__(self, ...):
          # ...
          self._resample_cache: dict[str, tuple[int, pd.DataFrame]] = {}
          self._cache_max_size = 10  # Keep last 10 resampled results

      def _resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
          # Generate cache key
          cache_key = f"{id(df)}_{timeframe}_{len(df)}"

          # Check cache
          if cache_key in self._resample_cache:
              timestamp, cached_result = self._resample_cache[cache_key]
              # Cache hit!
              logger.debug(f"Resample cache hit for {timeframe}")
              return cached_result

          # ... existing resample logic ...

          # Store in cache
          self._resample_cache[cache_key] = (pd.Timestamp.now(), resampled)

          # Evict old entries
          if len(self._resample_cache) > self._cache_max_size:
              oldest_key = min(self._resample_cache.keys(),
                              key=lambda k: self._resample_cache[k][0])
              del self._resample_cache[oldest_key]

          return resampled
  ```

- [ ] **Add cache invalidation:**
  ```python
  def update_chart_data(self, df: pd.DataFrame) -> None:
      # Clear cache when new data arrives
      if df is not self._last_raw_data:
          self._resample_cache.clear()

      self._last_raw_data = df
      # ... existing logic ...
  ```

- [ ] **Measure performance improvement:**
  - [ ] Benchmark resample time without cache
  - [ ] Benchmark resample time with cache
  - [ ] Document improvement in metrics

---

### Recommendation #7: Add Metrics
**Effort:** 1 hour | **Impact:** Observability | **Risk if skipped:** NONE

#### Implementation Checklist

- [ ] **Add performance logging:**
  ```python
  import time

  def _resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
      start = time.perf_counter()

      # ... existing resample logic ...

      elapsed = time.perf_counter() - start

      # Log slow operations
      if elapsed > 0.1:  # 100ms threshold
          logger.warning(
              f"Slow resample: {len(df)} rows → {timeframe} "
              f"took {elapsed*1000:.1f}ms"
          )
      elif elapsed > 0.01:  # 10ms info threshold
          logger.info(
              f"Resample: {len(df)} rows → {timeframe} "
              f"in {elapsed*1000:.1f}ms"
          )

      return resampled
  ```

- [ ] **Add metrics collection (optional):**
  ```python
  class ResampleMetrics:
      """Track resample operation metrics."""

      def __init__(self):
          self.total_calls = 0
          self.total_time = 0.0
          self.slow_calls = 0
          self.by_timeframe: dict[str, list[float]] = {}

      def record(self, timeframe: str, elapsed: float, row_count: int):
          self.total_calls += 1
          self.total_time += elapsed
          if elapsed > 0.1:
              self.slow_calls += 1

          if timeframe not in self.by_timeframe:
              self.by_timeframe[timeframe] = []
          self.by_timeframe[timeframe].append(elapsed)

      def summary(self) -> str:
          avg_time = self.total_time / self.total_calls if self.total_calls else 0
          return (
              f"Resample Metrics:\n"
              f"  Total calls: {self.total_calls}\n"
              f"  Avg time: {avg_time*1000:.1f}ms\n"
              f"  Slow calls (>100ms): {self.slow_calls}\n"
          )
  ```

---

## 📊 Progress Tracking

### Implementation Progress

| Priority | Recommendation | Status | Assignee | Deadline |
|----------|---------------|--------|----------|----------|
| 🔴 HIGH | #1: Unit Tests | ⬜ Not Started | TBD | Sprint 1 |
| 🔴 HIGH | #2: Documentation | ⬜ Not Started | TBD | Sprint 1 |
| 🔴 HIGH | #3: Validation | ⬜ Not Started | TBD | Sprint 1 |
| 🟡 MEDIUM | #4: Centralize | ⬜ Not Started | TBD | Sprint 2 |
| 🟡 MEDIUM | #5: ARCHITECTURE.md | ⬜ Not Started | TBD | Sprint 2 |
| 🟢 LOW | #6: Caching | ⬜ Not Started | TBD | Future |
| 🟢 LOW | #7: Metrics | ⬜ Not Started | TBD | Future |

### Effort Summary

- **Sprint 1 (HIGH):** 3.5 hours
- **Sprint 2 (MEDIUM):** 5 hours
- **Future (LOW):** 3 hours
- **Total:** ~12 hours

---

## 🎯 Definition of Done

### For Each Recommendation

#### Unit Tests (#1)
- [ ] All 7 test cases implemented
- [ ] Tests pass with 100% success rate
- [ ] Code coverage > 90% for `_resample_data()`
- [ ] Tests run in CI/CD pipeline

#### Documentation (#2)
- [ ] Docstring updated with Args, Returns, Note, Examples
- [ ] Inline comments added at critical lines
- [ ] Issue #24 referenced in comments
- [ ] Code review approved

#### Validation (#3)
- [ ] Edge case validation added
- [ ] Logger statements added
- [ ] Fallback behavior tested
- [ ] No new exceptions raised in production

#### Centralization (#4)
- [ ] `OHLCVResampler` service created
- [ ] All 11 files migrated to use service
- [ ] Unit tests for service (100% coverage)
- [ ] Performance regression test passed
- [ ] Documentation updated

#### ARCHITECTURE.md (#5)
- [ ] DateTime conventions section added
- [ ] Examples provided (good vs bad)
- [ ] Data source differences documented
- [ ] Best practices section updated
- [ ] Peer reviewed

#### Caching (#6)
- [ ] LRU cache implementation added
- [ ] Cache invalidation logic tested
- [ ] Performance improvement measured (>30% faster)
- [ ] Memory usage within limits

#### Metrics (#7)
- [ ] Performance logging added
- [ ] Metrics collection implemented (optional)
- [ ] Dashboard/monitoring configured (optional)
- [ ] Slow operation alerts configured

---

## 🚦 Acceptance Criteria

### Minimum (Required for Issue #24 Closure)
- ✅ Fix implemented (DONE)
- ✅ Code review approved (DONE)
- ✅ Architecture analysis complete (DONE)
- ⬜ HIGH priority recommendations implemented (#1-3)
- ⬜ No regressions detected in testing

### Ideal (Full Quality Standard)
- ⬜ All HIGH + MEDIUM recommendations implemented
- ⬜ Code coverage > 90%
- ⬜ Documentation complete
- ⬜ Performance benchmarks passed
- ⬜ Team training on datetime conventions

---

## 📅 Implementation Timeline

### Sprint 1 (Week 1)
**Focus:** HIGH priority items

**Day 1:**
- [ ] Create unit test file
- [ ] Implement test cases 1-3 (unnamed, timestamp, datetime index)
- [ ] Run tests, ensure passing

**Day 2:**
- [ ] Implement test cases 4-7 (time column, empty df, OHLC correctness, all timeframes)
- [ ] Update docstring with full documentation
- [ ] Add inline comments

**Day 3:**
- [ ] Add validation logic (empty check, datetime type check)
- [ ] Test validation with edge cases
- [ ] Code review and fixes

**Day 4:**
- [ ] Final testing and QA
- [ ] Merge to main branch
- [ ] Deploy to staging

### Sprint 2 (Week 2)
**Focus:** MEDIUM priority items

**Day 1-2:**
- [ ] Create `OHLCVResampler` service
- [ ] Implement centralized logic with full edge case handling
- [ ] Write unit tests for service

**Day 3:**
- [ ] Migrate compact_chart_widget.py to use service
- [ ] Migrate 3-4 other high-priority files
- [ ] Regression testing

**Day 4:**
- [ ] Update ARCHITECTURE.md
- [ ] Migrate remaining files
- [ ] Final testing

### Future (Low Priority)
- [ ] Add caching (when performance issues arise)
- [ ] Add metrics (when observability is needed)

---

## 🔗 Related Documentation

- [Architecture Analysis](./ISSUE_24_ARCHITECTURE_ANALYSIS.md) - Full technical analysis
- [Visual Comparison](./ISSUE_24_VISUAL_COMPARISON.md) - Before/after code comparison
- [Summary](./ISSUE_24_SUMMARY.md) - Quick overview
- [Index](./ISSUE_24_INDEX.md) - Navigation hub

---

**Document Version:** 1.0
**Last Updated:** 2026-01-22
**Next Review:** After implementing HIGH priority recommendations
