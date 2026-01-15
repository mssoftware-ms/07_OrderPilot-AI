"""Background Runner for Live Entry Analysis.

Provides non-blocking background analysis with:
- Scheduled full recomputes
- Incremental updates on new candles
- Thread-safe signal emission for UI updates

Phase 3: Hintergrundlauf Live
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from .analyzer import VisibleChartAnalyzer
from .cache import get_analyzer_cache
from .types import AnalysisResult, EntryEvent, RegimeType, VisibleRange

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of background tasks."""

    FULL_ANALYZE = "full_analyze"
    INCREMENTAL_UPDATE = "incremental_update"
    STOP = "stop"


@dataclass
class AnalysisTask:
    """A task to be executed by the background worker.

    Attributes:
        task_type: Type of task to execute.
        visible_range: Visible chart range.
        symbol: Trading symbol.
        timeframe: Chart timeframe.
        new_candles: New candles for incremental update (optional).
        priority: Task priority (lower = higher priority).
        created_at: Task creation timestamp.
    """

    task_type: TaskType
    visible_range: VisibleRange | None = None
    symbol: str = ""
    timeframe: str = "1m"
    new_candles: list[dict] = field(default_factory=list)
    priority: int = 5
    created_at: float = field(default_factory=time.time)

    def __lt__(self, other: AnalysisTask) -> bool:
        """Compare tasks by priority for queue ordering."""
        return self.priority < other.priority


@dataclass
class RunnerConfig:
    """Configuration for the background runner.

    Attributes:
        reanalyze_interval_sec: Interval for full reanalysis (0 = disabled).
        debounce_ms: Debounce time for rapid updates.
        max_queue_size: Maximum pending tasks.
        use_optimizer: Whether to use the optimizer.
        auto_start: Start runner on init.
        performance_log_interval: Log performance every N analyses.
    """

    reanalyze_interval_sec: float = 60.0  # Reanalyze every minute
    debounce_ms: float = 500.0  # Debounce rapid updates
    max_queue_size: int = 10
    use_optimizer: bool = True
    auto_start: bool = False
    performance_log_interval: int = 10


@dataclass
class PerformanceMetrics:
    """Performance metrics for the background runner.

    Attributes:
        total_analyses: Total number of analyses.
        total_time_ms: Total time spent analyzing.
        avg_time_ms: Average analysis time.
        max_time_ms: Maximum analysis time.
        cache_hit_rate: Cache hit rate.
        queue_overflows: Number of queue overflows.
    """

    total_analyses: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    max_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    queue_overflows: int = 0

    def record_analysis(self, time_ms: float) -> None:
        """Record an analysis duration."""
        self.total_analyses += 1
        self.total_time_ms += time_ms
        self.avg_time_ms = self.total_time_ms / self.total_analyses
        self.max_time_ms = max(self.max_time_ms, time_ms)


class BackgroundRunner:
    """Runs entry analysis in a background thread.

    Features:
    - Priority queue for tasks (incremental > full)
    - Debouncing to prevent rapid re-analysis
    - Scheduled full recomputes
    - Thread-safe callbacks for UI updates
    - Performance monitoring

    Usage:
        runner = BackgroundRunner(config)
        runner.on_result = lambda result: update_ui(result)
        runner.start()
        runner.request_analysis(visible_range, symbol, timeframe)
    """

    def __init__(self, config: RunnerConfig | None = None) -> None:
        """Initialize the background runner.

        Args:
            config: Runner configuration.
        """
        self.config = config or RunnerConfig()
        self._analyzer = VisibleChartAnalyzer(
            use_optimizer=self.config.use_optimizer,
            use_cache=True,
        )

        # Task queue (priority queue)
        self._task_queue: queue.PriorityQueue[tuple[int, AnalysisTask]] = (
            queue.PriorityQueue(maxsize=self.config.max_queue_size)
        )

        # Worker thread
        self._worker_thread: threading.Thread | None = None
        self._running = False
        self._stop_event = threading.Event()

        # Scheduler thread
        self._scheduler_thread: threading.Thread | None = None

        # Debounce state
        self._last_request_time: float = 0.0
        self._pending_request: AnalysisTask | None = None
        self._debounce_lock = threading.Lock()

        # Callbacks
        self.on_result: Callable[[AnalysisResult], None] | None = None
        self.on_new_entry: Callable[[EntryEvent], None] | None = None
        self.on_regime_change: Callable[[RegimeType, RegimeType], None] | None = None
        self.on_error: Callable[[str], None] | None = None

        # State tracking
        self._last_result: AnalysisResult | None = None
        self._last_regime: RegimeType | None = None
        self._current_symbol: str | None = None
        self._current_range: VisibleRange | None = None
        self._candle_cache: list[dict] = []

        # Performance
        self._metrics = PerformanceMetrics()

        if self.config.auto_start:
            self.start()

    def start(self) -> None:
        """Start the background worker and scheduler."""
        if self._running:
            logger.warning("Runner already running")
            return

        self._running = True
        self._stop_event.clear()

        # Start worker thread
        self._worker_thread = threading.Thread(
            target=self._worker_loop, name="EntryAnalyzerWorker", daemon=True
        )
        self._worker_thread.start()

        # Start scheduler thread if interval > 0
        if self.config.reanalyze_interval_sec > 0:
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop, name="EntryAnalyzerScheduler", daemon=True
            )
            self._scheduler_thread.start()

        logger.info(
            "BackgroundRunner started (optimizer=%s, interval=%.1fs)",
            self.config.use_optimizer,
            self.config.reanalyze_interval_sec,
        )

    def stop(self) -> None:
        """Stop the background worker and scheduler."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        # Send stop task to unblock queue
        try:
            stop_task = AnalysisTask(task_type=TaskType.STOP, priority=0)
            self._task_queue.put_nowait((0, stop_task))
        except queue.Full:
            pass

        # Wait for threads
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=2.0)

        logger.info("BackgroundRunner stopped")

    def request_analysis(
        self,
        visible_range: VisibleRange,
        symbol: str,
        timeframe: str = "1m",
        force: bool = False,
    ) -> bool:
        """Request a full analysis of the visible range.

        Requests are debounced to prevent rapid re-analysis.

        Args:
            visible_range: The visible chart range.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            force: Skip debouncing.

        Returns:
            True if request was queued, False otherwise.
        """
        if not self._running:
            logger.warning("Runner not running, cannot queue request")
            return False

        task = AnalysisTask(
            task_type=TaskType.FULL_ANALYZE,
            visible_range=visible_range,
            symbol=symbol,
            timeframe=timeframe,
            priority=5,  # Normal priority
        )

        if force:
            return self._queue_task(task)

        return self._debounce_request(task)

    def push_new_candles(
        self,
        candles: list[dict],
        visible_range: VisibleRange,
        symbol: str,
        timeframe: str = "1m",
    ) -> bool:
        """Push new candles for incremental update.

        Args:
            candles: New candle data.
            visible_range: Current visible range.
            symbol: Trading symbol.
            timeframe: Chart timeframe.

        Returns:
            True if request was queued.
        """
        if not self._running:
            return False

        task = AnalysisTask(
            task_type=TaskType.INCREMENTAL_UPDATE,
            visible_range=visible_range,
            symbol=symbol,
            timeframe=timeframe,
            new_candles=candles,
            priority=3,  # Higher priority than full analyze
        )

        return self._queue_task(task)

    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics.

        Returns:
            Current performance metrics.
        """
        # Update cache hit rate
        cache_stats = get_analyzer_cache().get_stats()
        self._metrics.cache_hit_rate = cache_stats.hit_rate
        return self._metrics

    def get_last_result(self) -> AnalysisResult | None:
        """Get the last analysis result.

        Returns:
            Last result or None.
        """
        return self._last_result

    # ─────────────────────────────────────────────────────────────────
    # Internal Methods
    # ─────────────────────────────────────────────────────────────────

    def _queue_task(self, task: AnalysisTask) -> bool:
        """Add a task to the queue.

        Args:
            task: Task to queue.

        Returns:
            True if queued successfully.
        """
        try:
            self._task_queue.put_nowait((task.priority, task))
            return True
        except queue.Full:
            self._metrics.queue_overflows += 1
            logger.warning("Task queue full, dropping request")
            return False

    def _debounce_request(self, task: AnalysisTask) -> bool:
        """Debounce a request to prevent rapid re-analysis.

        Args:
            task: Task to debounce.

        Returns:
            True if request was queued (after debounce).
        """
        with self._debounce_lock:
            now = time.time()
            debounce_sec = self.config.debounce_ms / 1000.0

            if now - self._last_request_time < debounce_sec:
                # Within debounce window - store as pending
                self._pending_request = task
                return False

            # Outside debounce window - queue immediately
            self._last_request_time = now
            self._pending_request = None
            return self._queue_task(task)

    def _worker_loop(self) -> None:
        """Main worker loop - processes tasks from queue."""
        logger.debug("Worker loop started")

        while self._running and not self._stop_event.is_set():
            try:
                # Get next task (blocking with timeout)
                try:
                    _, task = self._task_queue.get(timeout=0.5)
                except queue.Empty:
                    # Check for pending debounced request
                    self._process_pending_request()
                    continue

                if task.task_type == TaskType.STOP:
                    break

                # Process task
                self._process_task(task)

            except Exception as e:
                logger.exception("Worker loop error: %s", e)
                if self.on_error:
                    self.on_error(str(e))

        logger.debug("Worker loop stopped")

    def _process_pending_request(self) -> None:
        """Process any pending debounced request."""
        with self._debounce_lock:
            if self._pending_request is None:
                return

            now = time.time()
            debounce_sec = self.config.debounce_ms / 1000.0

            if now - self._last_request_time >= debounce_sec:
                task = self._pending_request
                self._pending_request = None
                self._last_request_time = now
                self._queue_task(task)

    def _process_task(self, task: AnalysisTask) -> None:
        """Process a single analysis task.

        Args:
            task: Task to process.
        """
        start_time = time.perf_counter()

        try:
            if task.task_type == TaskType.FULL_ANALYZE:
                result = self._run_full_analysis(task)
            elif task.task_type == TaskType.INCREMENTAL_UPDATE:
                result = self._run_incremental_update(task)
            else:
                return

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._metrics.record_analysis(elapsed_ms)

            # Log performance periodically
            if self._metrics.total_analyses % self.config.performance_log_interval == 0:
                logger.info(
                    "Performance: avg=%.1fms, max=%.1fms, cache_hit=%.1f%%, total=%d",
                    self._metrics.avg_time_ms,
                    self._metrics.max_time_ms,
                    self._metrics.cache_hit_rate * 100,
                    self._metrics.total_analyses,
                )

            if result:
                self._handle_result(result, task)

        except Exception as e:
            logger.exception("Task processing error: %s", e)
            if self.on_error:
                self.on_error(str(e))

    def _run_full_analysis(self, task: AnalysisTask) -> AnalysisResult | None:
        """Run a full analysis.

        Args:
            task: Analysis task.

        Returns:
            Analysis result or None on error.
        """
        if not task.visible_range:
            return None

        result = self._analyzer.analyze(
            visible_range=task.visible_range,
            symbol=task.symbol,
            timeframe=task.timeframe,
        )

        return result

    def _run_incremental_update(self, task: AnalysisTask) -> AnalysisResult | None:
        """Run an incremental update with new candles.

        Appends new candles to cache and re-analyzes.
        Checks if cached data is sufficient for visible range.

        Args:
            task: Incremental update task.

        Returns:
            AnalysisResult or None.
        """
        if not task.visible_range:
            return None

        # 1. Update cache with new candles
        if task.new_candles:
            if not self._candle_cache:
                # No cache? Can't incremental. Fallback to full.
                logger.debug("Incremental update requested but no cache. Falling back to full analysis.")
                return self._run_full_analysis(task)

            # Append new candles (avoid duplicates)
            last_ts = self._candle_cache[-1]["timestamp"]
            new_unique = [c for c in task.new_candles if c["timestamp"] > last_ts]
            
            if new_unique:
                self._candle_cache.extend(new_unique)
                # Keep cache size reasonable (e.g. max 5000 candles)
                if len(self._candle_cache) > 5000:
                     self._candle_cache = self._candle_cache[-5000:]

        # 2. Check if cache covers visible range
        # We need enough warmup data before visible range
        if not self._candle_cache:
             return self._run_full_analysis(task)

        cache_start = self._candle_cache[0]["timestamp"]
        cache_end = self._candle_cache[-1]["timestamp"]
        
        # Required start: visible start - warmup buffer (approx 100 bars)
        # 1m bar = 60s. 100 bars = 6000s.
        warmup_seconds = 60 * 100
        required_start = task.visible_range.from_ts - warmup_seconds
        
        if required_start < cache_start:
            # Cache doesn't go back far enough. Need full load.
            logger.debug("Cache miss for incremental update (start). Falling back to full analysis.")
            return self._run_full_analysis(task)
            
        if task.visible_range.to_ts > cache_end + 300: # Allow 5m slack
             # Cache doesn't go forward enough (shouldn't happen with live updates but possible)
             logger.debug("Cache miss for incremental update (end). Falling back to full analysis.")
             return self._run_full_analysis(task)

        # 3. Run analysis with cached candles
        # Filter cache to relevant range to avoid processing too much? 
        # Actually analyze_with_candles handles the whole list usually.
        # But we can slice it to be efficient.
        
        # Find start index in cache
        start_idx = 0
        for i, c in enumerate(self._candle_cache):
            if c["timestamp"] >= required_start:
                start_idx = i
                break
        
        sliced_candles = self._candle_cache[start_idx:]
        
        return self._analyzer.analyze_with_candles(
            visible_range=task.visible_range,
            symbol=task.symbol,
            timeframe=task.timeframe,
            candles=sliced_candles,
        )

    def _handle_result(self, result: AnalysisResult, task: AnalysisTask) -> None:
        """Handle an analysis result.

        Detects changes and emits appropriate callbacks.
        Updates candle cache.

        Args:
            result: AnalysisResult.
            task: Original task.
        """
        # Update cache if result has candles (from full analysis or incremental)
        if result.candles:
            # For full analysis, replace cache
            if task.task_type == TaskType.FULL_ANALYZE:
                 self._candle_cache = list(result.candles)
            # For incremental, we already updated cache in _run_incremental_update,
            # but result might have processed/sliced ones. 
            # Best to keep the main cache accumulating in _run_incremental_update
            # and only replace on FULL_ANALYZE or if cache was empty.
            elif not self._candle_cache:
                 self._candle_cache = list(result.candles)

        # Check for regime change
        if self._last_regime and result.regime != self._last_regime:
            logger.info(
                "Regime changed: %s -> %s",
                self._last_regime.value,
                result.regime.value,
            )
            if self.on_regime_change:
                self.on_regime_change(self._last_regime, result.regime)

        # Detect new entries (entries not in last result)
        if self._last_result and task.task_type == TaskType.INCREMENTAL_UPDATE:
            new_entries = self._find_new_entries(result.entries)
            for entry in new_entries:
                logger.debug("New entry detected: %s @ %d", entry.side.value, entry.timestamp)
                if self.on_new_entry:
                    self.on_new_entry(entry)

        # Update state
        self._last_result = result
        self._last_regime = result.regime
        self._current_symbol = task.symbol
        self._current_range = task.visible_range

        # Emit result callback
        if self.on_result:
            self.on_result(result)

    def _find_new_entries(self, entries: list[EntryEvent]) -> list[EntryEvent]:
        """Find entries that are new compared to last result.

        Args:
            entries: Current entries.

        Returns:
            List of new entries.
        """
        if not self._last_result:
            return entries

        last_timestamps = {e.timestamp for e in self._last_result.entries}
        return [e for e in entries if e.timestamp not in last_timestamps]

    def _scheduler_loop(self) -> None:
        """Scheduler loop - triggers periodic reanalysis."""
        logger.debug("Scheduler loop started (interval=%.1fs)", self.config.reanalyze_interval_sec)

        while self._running and not self._stop_event.is_set():
            # Wait for interval or stop event
            self._stop_event.wait(self.config.reanalyze_interval_sec)

            if not self._running or self._stop_event.is_set():
                break

            # Trigger reanalysis if we have current state
            if self._current_range and self._current_symbol:
                logger.debug("Scheduled reanalysis triggered")
                self.request_analysis(
                    visible_range=self._current_range,
                    symbol=self._current_symbol,
                    timeframe="1m",
                    force=True,
                )

        logger.debug("Scheduler loop stopped")
