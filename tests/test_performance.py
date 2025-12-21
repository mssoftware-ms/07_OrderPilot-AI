"""Tests for Performance Monitoring."""

import asyncio
import time

import pytest

from src.common.performance import (
    PerformanceMonitor,
    PerformanceTimer,
    log_performance,
    monitor_performance,
    performance_monitor,
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.monitor = PerformanceMonitor()

    def test_record_latency(self):
        """Test recording latency metrics."""
        self.monitor.record_latency("test_operation", 100.5)
        self.monitor.record_latency("test_operation", 150.2)
        self.monitor.record_latency("test_operation", 125.8)

        stats = self.monitor.get_stats("test_operation")
        assert stats["count"] == 3
        assert stats["min"] == 100.5
        assert stats["max"] == 150.2
        assert abs(stats["avg"] - 125.5) < 1  # Allow small floating point error

    def test_increment_counter(self):
        """Test incrementing counters."""
        self.monitor.increment_counter("orders_placed")
        self.monitor.increment_counter("orders_placed")
        self.monitor.increment_counter("orders_filled")

        assert self.monitor.counters["orders_placed"] == 2
        assert self.monitor.counters["orders_filled"] == 1

    def test_context_manager(self):
        """Test measuring with context manager."""
        with self.monitor.measure("test_operation"):
            time.sleep(0.01)  # Sleep 10ms

        stats = self.monitor.get_stats("test_operation")
        assert stats["count"] == 1
        assert stats["min"] >= 10  # At least 10ms

    def test_get_all_stats(self):
        """Test getting all statistics."""
        self.monitor.record_latency("op1", 100)
        self.monitor.record_latency("op2", 200)

        all_stats = self.monitor.get_all_stats()
        assert "op1" in all_stats
        assert "op2" in all_stats
        assert all_stats["op1"]["avg"] == 100
        assert all_stats["op2"]["avg"] == 200

    def test_reset(self):
        """Test resetting metrics."""
        self.monitor.record_latency("test_op", 100)
        self.monitor.increment_counter("test_counter")

        self.monitor.reset()

        assert len(self.monitor.metrics) == 0
        assert len(self.monitor.counters) == 0

    def test_percentiles(self):
        """Test percentile calculations."""
        # Add 100 measurements
        for i in range(100):
            self.monitor.record_latency("test_op", float(i))

        stats = self.monitor.get_stats("test_op")
        assert stats["p50"] == 50.0  # Median
        assert stats["p95"] == 95.0
        assert stats["p99"] == 99.0

    def test_report_generation(self):
        """Test performance report generation."""
        self.monitor.record_latency("operation1", 100)
        self.monitor.record_latency("operation1", 200)
        self.monitor.increment_counter("orders_placed")

        report = self.monitor.report()

        assert "PERFORMANCE REPORT" in report
        assert "operation1" in report
        assert "Count:" in report
        assert "Avg:" in report
        assert "orders_placed" in report


class TestPerformanceDecorators:
    """Test performance monitoring decorators."""

    def setup_method(self):
        """Setup test fixtures."""
        performance_monitor.reset()

    def test_monitor_performance_sync(self):
        """Test monitoring synchronous functions."""
        @monitor_performance("sync_func")
        def slow_function():
            time.sleep(0.01)
            return "result"

        result = slow_function()
        assert result == "result"

        stats = performance_monitor.get_stats("sync_func")
        assert stats["count"] == 1
        assert stats["min"] >= 10

    @pytest.mark.asyncio
    async def test_monitor_performance_async(self):
        """Test monitoring asynchronous functions."""
        @monitor_performance("async_func")
        async def slow_async_function():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await slow_async_function()
        assert result == "async_result"

        stats = performance_monitor.get_stats("async_func")
        assert stats["count"] == 1
        assert stats["min"] >= 10

    def test_log_performance_sync(self):
        """Test log_performance decorator for sync functions."""
        @log_performance("logged_func", threshold_ms=1)
        def fast_function():
            return "fast"

        result = fast_function()
        assert result == "fast"

        stats = performance_monitor.get_stats("logged_func")
        assert stats["count"] == 1

    @pytest.mark.asyncio
    async def test_log_performance_async(self):
        """Test log_performance decorator for async functions."""
        @log_performance("logged_async", threshold_ms=1)
        async def fast_async_function():
            return "fast_async"

        result = await fast_async_function()
        assert result == "fast_async"

        stats = performance_monitor.get_stats("logged_async")
        assert stats["count"] == 1


class TestPerformanceTimer:
    """Test PerformanceTimer functionality."""

    def test_manual_timer(self):
        """Test manual timer usage."""
        timer = PerformanceTimer("manual_test", auto_log=False)
        timer.start()
        time.sleep(0.01)
        elapsed = timer.stop()

        assert elapsed >= 10
        assert timer.elapsed_ms == elapsed

    def test_timer_context_manager(self):
        """Test timer as context manager."""
        with PerformanceTimer("context_test", auto_log=False) as timer:
            time.sleep(0.01)

        assert timer.elapsed_ms is not None
        assert timer.elapsed_ms >= 10

    def test_timer_not_started_error(self):
        """Test timer error when not started."""
        timer = PerformanceTimer("error_test")

        with pytest.raises(RuntimeError, match="Timer not started"):
            timer.stop()

    def test_timer_records_to_global_monitor(self):
        """Test timer records to global monitor."""
        performance_monitor.reset()

        with PerformanceTimer("global_test", auto_log=False):
            time.sleep(0.01)

        stats = performance_monitor.get_stats("global_test")
        assert stats["count"] == 1
        assert stats["min"] >= 10
