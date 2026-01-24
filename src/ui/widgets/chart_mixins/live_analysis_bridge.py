"""Live Analysis Bridge for Chart Widget.

Bridges the BackgroundRunner (threading) with PyQt signals
for safe UI updates in live entry analysis mode.

Phase 3: Hintergrundlauf Live
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QObject, pyqtSignal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LiveAnalysisBridge(QObject):
    """Bridge between BackgroundRunner (threading) and Qt signals.

    Converts thread-based callbacks to Qt signals for safe UI updates.

    Signals:
        result_ready: Emitted when analysis completes (AnalysisResult).
        new_entry: Emitted when new entry is detected (EntryEvent).
        regime_changed: Emitted when regime changes (old, new RegimeType).
        error_occurred: Emitted on error (error message).
    """

    result_ready = pyqtSignal(object)  # AnalysisResult
    new_entry = pyqtSignal(object)  # EntryEvent
    regime_changed = pyqtSignal(object, object)  # old, new RegimeType
    error_occurred = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the bridge.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._runner = None

    def start_live_analysis(
        self,
        reanalyze_interval_sec: float = 60.0,
        use_optimizer: bool = True,
        json_config_path: str | None = None,
    ) -> None:
        """Start the background runner for live analysis.

        Args:
            reanalyze_interval_sec: Interval for scheduled reanalysis.
            use_optimizer: Whether to use the optimizer.
            json_config_path: Path to JSON config file for regime parameters.
        """
        from src.analysis.visible_chart.background_runner import (
            BackgroundRunner,
            RunnerConfig,
        )

        if self._runner:
            self._runner.stop()

        # Issue #28: Pass JSON config path to runner
        config = RunnerConfig(
            reanalyze_interval_sec=reanalyze_interval_sec,
            use_optimizer=use_optimizer,
            debounce_ms=500.0,
            json_config_path=json_config_path,
        )

        self._runner = BackgroundRunner(config)
        self._runner.on_result = self._on_result
        self._runner.on_new_entry = self._on_new_entry
        self._runner.on_regime_change = self._on_regime_change
        self._runner.on_error = self._on_error
        self._runner.start()

        logger.info(
            "Live analysis started (interval=%.1fs, json=%s)",
            reanalyze_interval_sec,
            json_config_path,
        )

    def stop_live_analysis(self) -> None:
        """Stop the background runner."""
        if self._runner:
            self._runner.stop()
            self._runner = None
            logger.info("Live analysis stopped")

    def request_analysis(
        self,
        visible_range_dict: dict,
        symbol: str,
        timeframe: str = "1m",
    ) -> bool:
        """Request analysis of visible range.

        Args:
            visible_range_dict: Dict with 'from' and 'to' timestamps.
            symbol: Trading symbol.
            timeframe: Chart timeframe.

        Returns:
            True if request was queued.
        """
        if not self._runner:
            return False

        from src.analysis.visible_chart.types import VisibleRange

        from_ts = int(visible_range_dict.get("from", 0))
        to_ts = int(visible_range_dict.get("to", 0))

        if from_ts == 0 or to_ts == 0:
            return False

        visible_range = VisibleRange(
            from_ts=from_ts,
            to_ts=to_ts,
            from_idx=visible_range_dict.get("from_idx"),
            to_idx=visible_range_dict.get("to_idx"),
        )

        return self._runner.request_analysis(visible_range, symbol, timeframe)

    def push_new_candle(
        self,
        candle: dict,
        visible_range_dict: dict,
        symbol: str,
        timeframe: str = "1m",
    ) -> bool:
        """Push a new candle for incremental update.

        Args:
            candle: New candle data.
            visible_range_dict: Current visible range.
            symbol: Trading symbol.
            timeframe: Chart timeframe.

        Returns:
            True if request was queued.
        """
        if not self._runner:
            return False

        from src.analysis.visible_chart.types import VisibleRange

        from_ts = int(visible_range_dict.get("from", 0))
        to_ts = int(visible_range_dict.get("to", 0))

        if from_ts == 0 or to_ts == 0:
            return False

        visible_range = VisibleRange(
            from_ts=from_ts,
            to_ts=to_ts,
        )

        return self._runner.push_new_candles([candle], visible_range, symbol, timeframe)

    def is_running(self) -> bool:
        """Check if live analysis is running.

        Returns:
            True if the background runner is active.
        """
        return self._runner is not None and self._runner._running

    def get_metrics(self) -> dict:
        """Get performance metrics.

        Returns:
            Dict with performance stats including:
            - total_analyses: Number of analyses run
            - avg_time_ms: Average analysis time
            - max_time_ms: Maximum analysis time
            - cache_hit_rate: Cache hit rate (0-1)
            - queue_overflows: Number of dropped requests
        """
        if not self._runner:
            return {}

        metrics = self._runner.get_metrics()
        return {
            "total_analyses": metrics.total_analyses,
            "avg_time_ms": metrics.avg_time_ms,
            "max_time_ms": metrics.max_time_ms,
            "cache_hit_rate": metrics.cache_hit_rate,
            "queue_overflows": metrics.queue_overflows,
        }

    def _on_result(self, result: Any) -> None:
        """Handle result from background runner.

        Args:
            result: AnalysisResult from the runner.
        """
        self.result_ready.emit(result)

    def _on_new_entry(self, entry: Any) -> None:
        """Handle new entry from background runner.

        Args:
            entry: New EntryEvent detected.
        """
        self.new_entry.emit(entry)

    def _on_regime_change(self, old: Any, new: Any) -> None:
        """Handle regime change from background runner.

        Args:
            old: Previous RegimeType.
            new: New RegimeType.
        """
        self.regime_changed.emit(old, new)

    def _on_error(self, error_msg: str) -> None:
        """Handle error from background runner.

        Args:
            error_msg: Error message.
        """
        self.error_occurred.emit(error_msg)
