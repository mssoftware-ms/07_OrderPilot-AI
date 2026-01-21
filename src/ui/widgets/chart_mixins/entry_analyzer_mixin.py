"""Entry Analyzer Mixin for Chart Widget.

Provides integration of the Entry Analyzer popup
with the embedded TradingView chart.

Phase 3: Added BackgroundRunner for live analysis.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from .live_analysis_bridge import LiveAnalysisBridge

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult, EntryEvent, RegimeType

logger = logging.getLogger(__name__)

# Import debug logger
try:
    from src.analysis.visible_chart.debug_logger import debug_logger
except ImportError:
    debug_logger = logger


class AnalysisWorker(QThread):
    """Background worker for running analysis without blocking UI."""

    finished = pyqtSignal(object)  # AnalysisResult
    error = pyqtSignal(str)

    def __init__(
        self,
        visible_range: dict,
        symbol: str,
        timeframe: str,
        candles: list[dict],
        use_optimizer: bool = True,
        parent: Any = None,
    ) -> None:
        """Initialize the analysis worker.

        Args:
            visible_range: Dict with 'from' and 'to' timestamps.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            candles: Pre-loaded candle data from chart.
            use_optimizer: If True, run FastOptimizer (Phase 2).
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._visible_range = visible_range
        self._symbol = symbol
        self._timeframe = timeframe
        self._candles = candles
        self._use_optimizer = use_optimizer

    def run(self) -> None:
        """Execute the analysis in background thread."""
        try:
            from src.analysis.visible_chart.analyzer import VisibleChartAnalyzer
            from src.analysis.visible_chart.types import VisibleRange
            from src.analysis.visible_chart.debug_logger import debug_logger

            # Convert range
            from_raw = self._visible_range.get("from")
            to_raw = self._visible_range.get("to")
            from_ts = int(from_raw) if from_raw is not None else 0
            to_ts = int(to_raw) if to_raw is not None else 0
            from_idx = None
            to_idx = None

            if self._candles:
                from_idx = int(round(from_raw)) if from_raw is not None else None
                to_idx = int(round(to_raw)) if to_raw is not None else None
                if from_idx is not None and to_idx is not None:
                    max_idx = len(self._candles) - 1
                    if 0 <= from_idx <= max_idx and 0 <= to_idx <= max_idx:
                        from_ts = self._candles[from_idx]["timestamp"]
                        to_ts = self._candles[to_idx]["timestamp"]

            debug_logger.info(
                "EntryAnalyzerWorker: range raw=%s -> ts=(%s,%s) idx=(%s,%s)",
                self._visible_range,
                from_ts,
                to_ts,
                from_idx,
                to_idx,
            )

            if from_ts == 0 or to_ts == 0:
                self.error.emit("Invalid visible range")
                return

            if not self._candles:
                self.error.emit("No candle data available")
                return

            visible_range = VisibleRange(
                from_ts=from_ts,
                to_ts=to_ts,
                from_idx=from_idx if from_idx is not None else self._visible_range.get("from_idx"),
                to_idx=to_idx if to_idx is not None else self._visible_range.get("to_idx"),
            )

            # Run analysis with pre-loaded candles
            analyzer = VisibleChartAnalyzer(use_optimizer=self._use_optimizer)
            result = analyzer.analyze_with_candles(
                visible_range=visible_range,
                symbol=self._symbol,
                timeframe=self._timeframe,
                candles=self._candles,
            )

            self.finished.emit(result)

        except Exception as e:
            logger.exception("Analysis failed")
            self.error.emit(str(e))


class EntryAnalyzerMixin:
    """Mixin to add Entry Analyzer functionality to chart widget.

    Requires the chart widget to have:
    - get_visible_range(callback) method
    - add_bot_marker() method (from BotOverlayMixin)
    - clear_bot_markers() method
    - _symbol attribute
    - _timeframe attribute

    Phase 3 additions:
    - Live mode with BackgroundRunner
    - Incremental updates on new candles
    - Auto-reanalysis on schedule
    """

    _entry_analyzer_popup = None
    _analysis_worker = None
    _live_bridge: LiveAnalysisBridge | None = None
    _live_mode_enabled: bool = False
    _auto_draw_entries: bool = True

    def _init_entry_analyzer(self) -> None:
        """Initialize entry analyzer connections.

        Must be called from chart widget __init__.
        """
        # Connect to chart signals if they exist
        if hasattr(self, "symbol_changed"):
            self.symbol_changed.connect(self._on_entry_analyzer_symbol_changed)
        if hasattr(self, "timeframe_changed"):
            self.timeframe_changed.connect(self._on_entry_analyzer_timeframe_changed)
        if hasattr(self, "data_loaded"):
            self.data_loaded.connect(self._on_entry_analyzer_data_loaded)

    def show_entry_analyzer(self) -> None:
        """Show the Entry Analyzer popup dialog."""
        from src.ui.dialogs.entry_analyzer_popup import EntryAnalyzerPopup

        if self._entry_analyzer_popup is None:
            self._entry_analyzer_popup = EntryAnalyzerPopup(self)
            self._entry_analyzer_popup.analyze_requested.connect(
                self._start_visible_range_analysis
            )
            self._entry_analyzer_popup.draw_entries_requested.connect(
                self._draw_entry_markers
            )
            self._entry_analyzer_popup.clear_entries_requested.connect(
                self._clear_entry_markers
            )
            # Issue #32: Connect finished signal to reset button
            self._entry_analyzer_popup.finished.connect(
                self._on_entry_analyzer_closed
            )

        # Set context for AI/Validation
        symbol = getattr(self, "_symbol", None) or getattr(self, "current_symbol", "UNKNOWN")
        timeframe = getattr(self, "_timeframe", None) or getattr(self, "current_timeframe", "1m")
        candles = self._get_candles_for_validation()
        self._entry_analyzer_popup.set_context(symbol, timeframe, candles)

        self._entry_analyzer_popup.show()
        self._entry_analyzer_popup.raise_()
        self._entry_analyzer_popup.activateWindow()

    def _get_candles_for_validation(self) -> list[dict]:
        """Get candle data for validation from chart data.

        Returns:
            List of candle dicts with OHLCV data.
        """
        candles = []
        data = getattr(self, "data", None)

        if data is not None and hasattr(data, "iterrows"):
            try:
                from src.ui.widgets.chart_mixins.data_loading_utils import (
                    get_local_timezone_offset_seconds,
                )

                local_offset = get_local_timezone_offset_seconds()
                has_time_column = "time" in data.columns

                for idx, row in data.iterrows():
                    if has_time_column:
                        timestamp = int(row.get("time", 0))
                    else:
                        timestamp = 0
                        if hasattr(idx, "timestamp"):
                            timestamp = int(idx.timestamp()) + local_offset
                        elif isinstance(idx, (int, float)):
                            timestamp = int(idx)

                    candle = {
                        "timestamp": timestamp,
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": float(row.get("volume", 0)),
                    }
                    candles.append(candle)
                debug_logger.info(
                    "EntryAnalyzer: extracted %d candles (has_time_column=%s, local_offset=%s)",
                    len(candles),
                    has_time_column,
                    local_offset,
                )
            except Exception as e:
                logger.warning("Failed to extract candles: %s", e)
                debug_logger.exception("EntryAnalyzer: candle extraction failed")

        return candles

    # ─────────────────────────────────────────────────────────────────
    # Live Mode API (Phase 3)
    # ─────────────────────────────────────────────────────────────────

    def start_live_entry_analysis(
        self,
        reanalyze_interval_sec: float = 60.0,
        use_optimizer: bool = True,
        auto_draw: bool = True,
    ) -> None:
        """Start continuous live entry analysis.

        Args:
            reanalyze_interval_sec: Interval for scheduled reanalysis.
            use_optimizer: Whether to use the optimizer.
            auto_draw: Automatically draw new entries on chart.
        """
        if self._live_bridge is None:
            self._live_bridge = LiveAnalysisBridge(self)
            self._live_bridge.result_ready.connect(self._on_live_result)
            self._live_bridge.new_entry.connect(self._on_live_new_entry)
            self._live_bridge.regime_changed.connect(self._on_live_regime_change)
            self._live_bridge.error_occurred.connect(self._on_live_error)

        self._auto_draw_entries = auto_draw
        self._live_bridge.start_live_analysis(reanalyze_interval_sec, use_optimizer)
        self._live_mode_enabled = True

        # Trigger initial analysis
        self._request_live_analysis()

        logger.info("Live entry analysis started")

    def stop_live_entry_analysis(self) -> None:
        """Stop continuous live entry analysis."""
        if self._live_bridge:
            self._live_bridge.stop_live_analysis()
        self._live_mode_enabled = False
        logger.info("Live entry analysis stopped")

    def is_live_analysis_running(self) -> bool:
        """Check if live analysis is running.

        Returns:
            True if live mode is active.
        """
        return self._live_mode_enabled and (
            self._live_bridge is not None and self._live_bridge.is_running()
        )

    def on_new_candle_received(self, candle: dict) -> None:
        """Handle new candle data for incremental update.

        Call this from chart's streaming data handler.

        Args:
            candle: New candle dict with OHLCV data.
        """
        if not self._live_mode_enabled or not self._live_bridge:
            return

        if not hasattr(self, "get_visible_range"):
            return

        # Get current visible range and push update
        def on_range(range_data: dict | None) -> None:
            if range_data and self._live_bridge:
                symbol = getattr(self, "_symbol", None) or getattr(self, "symbol", "UNKNOWN")
                timeframe = getattr(self, "_timeframe", None) or getattr(self, "timeframe", "1m")
                self._live_bridge.push_new_candle(candle, range_data, symbol, timeframe)

        self.get_visible_range(on_range)

    def get_live_metrics(self) -> dict:
        """Get live analysis performance metrics.

        Returns:
            Dict with performance statistics.
        """
        if self._live_bridge:
            return self._live_bridge.get_metrics()
        return {}

    def _request_live_analysis(self) -> None:
        """Request live analysis of current visible range."""
        if not self._live_bridge or not hasattr(self, "get_visible_range"):
            return

        def on_range(range_data: dict | None) -> None:
            if range_data and self._live_bridge:
                symbol = getattr(self, "_symbol", None) or getattr(self, "symbol", "UNKNOWN")
                timeframe = getattr(self, "_timeframe", None) or getattr(self, "timeframe", "1m")
                self._live_bridge.request_analysis(range_data, symbol, timeframe)

        self.get_visible_range(on_range)

    def _on_live_result(self, result: Any) -> None:
        """Handle live analysis result.

        Args:
            result: AnalysisResult from background runner.
        """
        # Stop loading animation
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.set_analyzing(False)
            self._entry_analyzer_popup.set_result(result)

        # Auto-draw entries
        if self._auto_draw_entries and result.entries:
            self._clear_entry_markers()
            self._draw_entry_markers(result.entries)

        logger.debug(
            "Live result: %d entries, regime=%s",
            len(result.entries),
            result.regime.value,
        )

    # ... (other methods) ...

    def _start_visible_range_analysis(self) -> None:
        """Start analysis of the visible chart range using Live Bridge."""
        if not hasattr(self, "get_visible_range"):
            logger.error("Chart widget has no get_visible_range method")
            if self._entry_analyzer_popup:
                self._entry_analyzer_popup.set_analyzing(False)
            return

        # Enable live mode and request analysis
        # This unifies the "Analyze" button with the Live/Incremental architecture
        self.start_live_entry_analysis(auto_draw=True)
        
        # Manually set analyzing state (will be cleared in _on_live_result)
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.set_analyzing(True)

    def _draw_entry_markers(self, entries: list[EntryEvent]) -> None:
        """Draw entry markers on the chart.

        LONG entries are displayed in GREEN (below bar, arrow up).
        SHORT entries are displayed in RED (above bar, arrow down).

        Args:
            entries: List of entry events to draw.
        """
        if not hasattr(self, "add_bot_marker"):
            logger.warning("Chart widget has no add_bot_marker method")
            return

        from src.analysis.visible_chart.types import EntrySide
        from src.ui.widgets.chart_mixins.bot_overlay_types import MarkerType

        for entry in entries:
            # Always use ENTRY_CONFIRMED for clear LONG=green, SHORT=red display
            # The to_chart_marker() method handles colors:
            # - LONG: #26a69a (green), arrowUp, belowBar
            # - SHORT: #ef5350 (red), arrowDown, aboveBar
            marker_type = MarkerType.ENTRY_CONFIRMED

            # Build descriptive text with confidence and reason
            reasons_str = ", ".join(entry.reason_tags[:2]) if entry.reason_tags else ""
            text = f"{entry.side.value.upper()} {entry.confidence:.0%}"
            if reasons_str:
                text = f"{text} [{reasons_str}]"

            self.add_bot_marker(
                timestamp=entry.timestamp,
                price=entry.price,
                marker_type=marker_type,
                side=entry.side.value,
                text=text,
                score=entry.confidence,
            )

        logger.info(
            "Drew %d entry markers on chart (LONG=green, SHORT=red)",
            len(entries),
        )

    def _clear_entry_markers(self) -> None:
        """Clear all entry markers from the chart."""
        if hasattr(self, "clear_bot_markers"):
            self.clear_bot_markers()
            logger.info("Cleared entry markers")
        elif hasattr(self, "_clear_all_markers"):
            self._clear_all_markers()
            logger.info("Cleared all markers")

    def _on_entry_analyzer_closed(self, result: int) -> None:
        """Handle Entry Analyzer dialog close event (Issue #32).

        Args:
            result: Dialog result code (Accepted/Rejected).
        """
        logger.info("Entry Analyzer dialog closed")

        # Issue #32: Reset button state when dialog closes
        if hasattr(self, 'entry_analyzer_button'):
            self.entry_analyzer_button.setChecked(False)

    def _on_entry_analyzer_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change to update live analysis.

        Args:
            symbol: New symbol.
        """
        if self._live_mode_enabled:
            logger.info("Symbol changed to %s, refreshing live analysis", symbol)
            # Short delay to allow data to load?
            # Ideally we wait for data_loaded signal, but for now request update.
            self._request_live_analysis()

    def _on_entry_analyzer_timeframe_changed(self, timeframe: str) -> None:
        """Handle timeframe change to update live analysis.

        Args:
            timeframe: New timeframe.
        """
        if self._live_mode_enabled:
            logger.info("Timeframe changed to %s, refreshing live analysis", timeframe)
            self._request_live_analysis()

    def _on_entry_analyzer_data_loaded(self) -> None:
        """Handle data loaded event to update live analysis.
        
        This ensures analysis runs after new symbol/timeframe data 
        is actually available in the chart.
        """
        if self._live_mode_enabled:
            logger.info("Chart data loaded, refreshing live analysis")
            self._request_live_analysis()
