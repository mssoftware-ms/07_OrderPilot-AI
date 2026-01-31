"""Entry Analyzer Events Mixin - Event Handling and Live Analysis.

Provides event handlers, signal connections, and live analysis lifecycle
for the Entry Analyzer functionality.

Part of the modular entry_analyzer split (Task 3.3.4):
- entry_analyzer_ui_mixin.py: UI components
- entry_analyzer_events_mixin.py (this file): Event handlers
- entry_analyzer_logic_mixin.py: Business logic

Agent: CODER-021
Task: 3.3.4 - entry_analyzer_mixin refactoring
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QAction

from .live_analysis_bridge import LiveAnalysisBridge

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult

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
        json_config_path: str | None = None,
        parent: Any = None,
    ) -> None:
        """Initialize the analysis worker.

        Args:
            visible_range: Dict with 'from' and 'to' timestamps.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            candles: Pre-loaded candle data from chart.
            use_optimizer: If True, run FastOptimizer (Phase 2).
            json_config_path: Path to JSON config file for regime parameters.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._visible_range = visible_range
        self._symbol = symbol
        self._timeframe = timeframe
        self._candles = candles
        self._use_optimizer = use_optimizer
        self._json_config_path = json_config_path

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
                from_idx=from_idx
                if from_idx is not None
                else self._visible_range.get("from_idx"),
                to_idx=to_idx if to_idx is not None else self._visible_range.get("to_idx"),
            )

            # Run analysis with pre-loaded candles
            # Issue #28: Use JSON config path for regime parameters
            analyzer = VisibleChartAnalyzer(
                use_optimizer=self._use_optimizer,
                json_config_path=self._json_config_path,
            )
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


class EntryAnalyzerEventsMixin:
    """Mixin for Entry Analyzer event handling.

    Provides:
    - Event handlers for regime filter actions
    - Live analysis lifecycle management
    - Signal/slot connections for chart events

    Requires the chart widget to have:
    - get_visible_range(callback) method
    - _symbol attribute
    - _timeframe attribute
    """

    # Class attributes
    _analysis_worker = None
    _live_bridge: LiveAnalysisBridge | None = None
    _live_mode_enabled: bool = False
    _auto_draw_entries: bool = True
    _current_json_config_path: str | None = None
    _regime_filter_menu = None
    _current_regime_data: list[dict] = []
    _entry_analyzer_popup = None

    # ==================== Regime Filter Event Handlers ====================

    def _on_regime_filter_action_triggered(self, checked: bool) -> None:
        """Handle menu action trigger."""
        sender = self.sender()
        if not isinstance(sender, QAction):
            return

        data = sender.data()

        if data == "__header__":
            # Toggle all
            for action in self._regime_filter_menu.actions():
                if action.isCheckable() and action.data() != "__header__":
                    action.setChecked(checked)

        else:
            # Individual item toggled
            all_actions = [
                a
                for a in self._regime_filter_menu.actions()
                if a.isCheckable() and a.data() != "__header__"
            ]
            all_checked = all(a.isChecked() for a in all_actions)

            # Find header action
            for action in self._regime_filter_menu.actions():
                if action.data() == "__header__":
                    action.blockSignals(True)
                    action.setChecked(all_checked)
                    action.blockSignals(False)
                    break

        # Collect selected items
        selected = self.get_selected_items()
        self._on_regime_filter_changed(selected)

    def _on_regime_filter_changed(self, selected_regimes: list[str]) -> None:
        """Handle regime filter selection change.

        Re-draws regime lines based on current filter selection.

        Args:
            selected_regimes: List of selected regime IDs
        """
        logger.info(f"Regime filter changed: {selected_regimes}")
        print(f"[FILTER] _on_regime_filter_changed: {selected_regimes}", flush=True)

        # If no cached regime data, try to reconstruct from existing chart lines
        if not self._current_regime_data:
            self._reconstruct_regime_data_from_chart()

        if not self._current_regime_data:
            logger.warning("No regime data available to filter - clearing all lines")
            print(
                f"[FILTER] WARNING: No regime data to filter! Clearing lines.", flush=True
            )

        print(
            f"[FILTER] Have {len(self._current_regime_data)} regime entries to filter",
            flush=True,
        )
        # Apply filter and redraw
        self._apply_regime_filter(selected_regimes)

    # ==================== Live Analysis Lifecycle ====================

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
        # Issue #28: Pass JSON config path for regime parameters
        self._live_bridge.start_live_analysis(
            reanalyze_interval_sec,
            use_optimizer,
            json_config_path=self._current_json_config_path,
        )
        self._live_mode_enabled = True

        # Trigger initial analysis
        self._request_live_analysis()

        logger.info(
            "Live entry analysis started (json=%s)", self._current_json_config_path
        )

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
                symbol = getattr(self, "_symbol", None) or getattr(
                    self, "symbol", "UNKNOWN"
                )
                timeframe = getattr(self, "_timeframe", None) or getattr(
                    self, "timeframe", "1m"
                )
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
                symbol = getattr(self, "_symbol", None) or getattr(
                    self, "symbol", "UNKNOWN"
                )
                timeframe = getattr(self, "_timeframe", None) or getattr(
                    self, "timeframe", "1m"
                )
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

    def _start_visible_range_analysis(self, json_config_path: str = "") -> None:
        """Start analysis of the visible chart range using Live Bridge.

        Issue #28: Now accepts json_config_path from the popup signal.

        Args:
            json_config_path: Path to JSON config file from popup (empty for defaults).
        """
        if not hasattr(self, "get_visible_range"):
            logger.error("Chart widget has no get_visible_range method")
            if self._entry_analyzer_popup:
                self._entry_analyzer_popup.set_analyzing(False)
            return

        # Store the JSON config path for this analysis
        self._current_json_config_path = json_config_path if json_config_path else None
        logger.info("Using JSON config for analysis: %s", self._current_json_config_path)

        # Enable live mode and request analysis
        self.start_live_entry_analysis(auto_draw=True)

        # Manually set analyzing state (will be cleared in _on_live_result)
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.set_analyzing(True)

    # ==================== Chart Event Handlers ====================

    def _on_entry_analyzer_closed(self, result: int) -> None:
        """Handle Entry Analyzer dialog close event (Issue #32).

        Args:
            result: Dialog result code (Accepted/Rejected).
        """
        logger.info("Entry Analyzer dialog closed")

        # Issue #32: Reset button state when dialog closes
        if hasattr(self, "entry_analyzer_button"):
            self.entry_analyzer_button.setChecked(False)

    def _on_entry_analyzer_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change to update live analysis.

        Args:
            symbol: New symbol.
        """
        if self._live_mode_enabled:
            logger.info("Symbol changed to %s, refreshing live analysis", symbol)
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

    # Placeholder event handlers (can be implemented later if needed)
    def _on_live_new_entry(self, entry: Any) -> None:
        """Handle new entry from live bridge."""
        pass

    def _on_live_regime_change(self, regime: Any) -> None:
        """Handle regime change from live bridge."""
        pass

    def _on_live_error(self, error: str) -> None:
        """Handle error from live bridge."""
        logger.error(f"Live analysis error: {error}")

    # ==================== Forward Declarations (implemented in other mixins) ====================

    def get_selected_items(self) -> list[str]:
        """Get selected items (implemented in UI mixin)."""
        raise NotImplementedError("Must be provided by EntryAnalyzerUIMixin")

    def _apply_regime_filter(self, selected_regimes: list[str] | None = None) -> None:
        """Apply regime filter (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _reconstruct_regime_data_from_chart(self) -> None:
        """Reconstruct regime data (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _draw_entry_markers(self, entries: list) -> None:
        """Draw entry markers (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _clear_entry_markers(self) -> None:
        """Clear entry markers (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )
