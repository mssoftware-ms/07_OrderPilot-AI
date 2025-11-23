"""Performance Monitoring for OrderPilot-AI.

Provides decorators and utilities for monitoring performance of critical operations.
"""

import functools
import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor performance metrics for trading operations."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: dict[str, list[float]] = defaultdict(list)
        self.counters: dict[str, int] = defaultdict(int)
        self.start_times: dict[str, float] = {}

    def record_latency(self, operation: str, latency_ms: float) -> None:
        """Record latency for an operation.

        Args:
            operation: Operation name
            latency_ms: Latency in milliseconds
        """
        self.metrics[f"{operation}_latency"].append(latency_ms)

        # Log warning if latency exceeds threshold
        if latency_ms > 1000:  # 1 second
            logger.warning(f"High latency detected: {operation} took {latency_ms:.2f}ms")

    def increment_counter(self, counter: str) -> None:
        """Increment a counter.

        Args:
            counter: Counter name
        """
        self.counters[counter] += 1

    def get_stats(self, operation: str) -> dict[str, float]:
        """Get statistics for an operation.

        Args:
            operation: Operation name

        Returns:
            Dictionary with min, max, avg, count
        """
        key = f"{operation}_latency"
        if key not in self.metrics or not self.metrics[key]:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        latencies = self.metrics[key]
        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "count": len(latencies),
            "p50": sorted(latencies)[len(latencies) // 2],
            "p95": sorted(latencies)[int(len(latencies) * 0.95)],
            "p99": sorted(latencies)[int(len(latencies) * 0.99)]
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get all performance statistics.

        Returns:
            Dictionary of operation -> stats
        """
        operations = {key.replace("_latency", "") for key in self.metrics.keys()}
        return {op: self.get_stats(op) for op in operations}

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.start_times.clear()

    @contextmanager
    def measure(self, operation: str):
        """Context manager to measure operation duration.

        Args:
            operation: Operation name

        Example:
            with monitor.measure("order_placement"):
                await broker.place_order(order)
        """
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed = (time.monotonic() - start) * 1000  # Convert to ms
            self.record_latency(operation, elapsed)

    def report(self) -> str:
        """Generate performance report.

        Returns:
            Formatted performance report
        """
        report_lines = ["=" * 60]
        report_lines.append("PERFORMANCE REPORT")
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("=" * 60)

        stats = self.get_all_stats()
        if not stats:
            report_lines.append("No performance data collected.")
        else:
            for operation, data in sorted(stats.items()):
                report_lines.append(f"\n{operation}:")
                report_lines.append(f"  Count:   {data['count']:.0f}")
                report_lines.append(f"  Avg:     {data['avg']:.2f} ms")
                report_lines.append(f"  Min:     {data['min']:.2f} ms")
                report_lines.append(f"  Max:     {data['max']:.2f} ms")
                report_lines.append(f"  P50:     {data['p50']:.2f} ms")
                report_lines.append(f"  P95:     {data['p95']:.2f} ms")
                report_lines.append(f"  P99:     {data['p99']:.2f} ms")

        if self.counters:
            report_lines.append("\nCOUNTERS:")
            for counter, value in sorted(self.counters.items()):
                report_lines.append(f"  {counter}: {value}")

        report_lines.append("=" * 60)
        return "\n".join(report_lines)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation: str | None = None):
    """Decorator to monitor function performance.

    Args:
        operation: Operation name (defaults to function name)

    Example:
        @monitor_performance("order_placement")
        async def place_order(self, order):
            ...
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            with performance_monitor.measure(op_name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            with performance_monitor.measure(op_name):
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_performance(operation: str, threshold_ms: float = 100) -> Callable:
    """Decorator to log slow operations.

    Args:
        operation: Operation name
        threshold_ms: Threshold in milliseconds for logging

    Example:
        @log_performance("database_query", threshold_ms=50)
        def query_orders(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.monotonic()
            result = await func(*args, **kwargs)
            elapsed = (time.monotonic() - start) * 1000

            if elapsed > threshold_ms:
                logger.warning(
                    f"Slow operation: {operation} took {elapsed:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )

            performance_monitor.record_latency(operation, elapsed)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.monotonic()
            result = func(*args, **kwargs)
            elapsed = (time.monotonic() - start) * 1000

            if elapsed > threshold_ms:
                logger.warning(
                    f"Slow operation: {operation} took {elapsed:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )

            performance_monitor.record_latency(operation, elapsed)
            return result

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class PerformanceTimer:
    """Simple timer for manual performance tracking."""

    def __init__(self, name: str, auto_log: bool = True):
        """Initialize timer.

        Args:
            name: Timer name
            auto_log: Automatically log elapsed time
        """
        self.name = name
        self.auto_log = auto_log
        self.start_time: float | None = None
        self.elapsed_ms: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.monotonic()

    def stop(self) -> float:
        """Stop the timer and return elapsed time.

        Returns:
            Elapsed time in milliseconds
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")

        self.elapsed_ms = (time.monotonic() - self.start_time) * 1000

        if self.auto_log:
            logger.debug(f"{self.name}: {self.elapsed_ms:.2f}ms")

        performance_monitor.record_latency(self.name, self.elapsed_ms)
        return self.elapsed_ms

    def __enter__(self):
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Exit context manager."""
        self.stop()
