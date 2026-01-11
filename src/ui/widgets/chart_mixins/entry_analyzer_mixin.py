"""Entry Analyzer Mixin for Chart Widget.

Provides integration of the Entry Analyzer popup
with the embedded TradingView chart.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult, EntryEvent

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """Background worker for running analysis without blocking UI."""

    finished = pyqtSignal(object)  # AnalysisResult
    error = pyqtSignal(str)

    def __init__(
        self,
        visible_range: dict,
        symbol: str,
        timeframe: str,
        parent: Any = None,
    ) -> None:
        """Initialize the analysis worker.

        Args:
            visible_range: Dict with 'from' and 'to' timestamps.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._visible_range = visible_range
        self._symbol = symbol
        self._timeframe = timeframe

    def run(self) -> None:
        """Execute the analysis in background thread."""
        try:
            from src.analysis.visible_chart.analyzer import VisibleChartAnalyzer
            from src.analysis.visible_chart.types import VisibleRange

            # Convert range
            from_ts = int(self._visible_range.get("from", 0))
            to_ts = int(self._visible_range.get("to", 0))

            if from_ts == 0 or to_ts == 0:
                self.error.emit("Invalid visible range")
                return

            visible_range = VisibleRange(
                from_ts=from_ts,
                to_ts=to_ts,
                from_idx=self._visible_range.get("from_idx"),
                to_idx=self._visible_range.get("to_idx"),
            )

            # Run analysis
            analyzer = VisibleChartAnalyzer()
            result = analyzer.analyze(
                visible_range=visible_range,
                symbol=self._symbol,
                timeframe=self._timeframe,
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
    """

    _entry_analyzer_popup = None
    _analysis_worker = None

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

        self._entry_analyzer_popup.show()
        self._entry_analyzer_popup.raise_()
        self._entry_analyzer_popup.activateWindow()

    def _start_visible_range_analysis(self) -> None:
        """Start analysis of the visible chart range."""
        if not hasattr(self, "get_visible_range"):
            logger.error("Chart widget has no get_visible_range method")
            QMessageBox.warning(
                self,
                "Error",
                "Visible range API not available",
            )
            if self._entry_analyzer_popup:
                self._entry_analyzer_popup.set_analyzing(False)
            return

        # Get visible range asynchronously
        self.get_visible_range(self._on_visible_range_received)

    def _on_visible_range_received(self, range_data: dict | None) -> None:
        """Handle received visible range data.

        Args:
            range_data: Dict with 'from' and 'to' keys, or None on error.
        """
        if range_data is None:
            logger.error("Failed to get visible range")
            QMessageBox.warning(
                self,
                "Error",
                "Could not determine visible chart range",
            )
            if self._entry_analyzer_popup:
                self._entry_analyzer_popup.set_analyzing(False)
            return

        logger.info("Visible range received: %s", range_data)

        # Get symbol and timeframe
        symbol = getattr(self, "_symbol", None) or getattr(self, "symbol", "UNKNOWN")
        timeframe = getattr(self, "_timeframe", None) or getattr(
            self, "timeframe", "1m"
        )

        # Start background analysis
        self._analysis_worker = AnalysisWorker(
            visible_range=range_data,
            symbol=symbol,
            timeframe=timeframe,
            parent=self,
        )
        self._analysis_worker.finished.connect(self._on_analysis_finished)
        self._analysis_worker.error.connect(self._on_analysis_error)
        self._analysis_worker.start()

    def _on_analysis_finished(self, result: AnalysisResult) -> None:
        """Handle completed analysis.

        Args:
            result: The analysis result.
        """
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.set_analyzing(False)
            self._entry_analyzer_popup.set_result(result)

        logger.info(
            "Analysis completed: %d entries found, regime=%s",
            len(result.entries),
            result.regime.value,
        )

    def _on_analysis_error(self, error_msg: str) -> None:
        """Handle analysis error.

        Args:
            error_msg: Error message.
        """
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.set_analyzing(False)

        logger.error("Analysis error: %s", error_msg)
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Analysis failed: {error_msg}",
        )

    def _draw_entry_markers(self, entries: list[EntryEvent]) -> None:
        """Draw entry markers on the chart.

        Args:
            entries: List of entry events to draw.
        """
        if not hasattr(self, "add_bot_marker"):
            logger.warning("Chart widget has no add_bot_marker method")
            return

        from src.ui.widgets.chart_mixins.bot_overlay_types import MarkerType

        for entry in entries:
            marker_type = (
                MarkerType.ENTRY_CONFIRMED
                if entry.confidence > 0.7
                else MarkerType.ENTRY_CANDIDATE
            )

            self.add_bot_marker(
                timestamp=entry.timestamp,
                price=entry.price,
                marker_type=marker_type,
                side=entry.side.value,
                text=f"{entry.side.value.upper()} ({entry.confidence:.0%})",
                score=entry.confidence,
            )

        logger.info("Drew %d entry markers on chart", len(entries))

    def _clear_entry_markers(self) -> None:
        """Clear all entry markers from the chart."""
        if hasattr(self, "clear_bot_markers"):
            self.clear_bot_markers()
            logger.info("Cleared entry markers")
        elif hasattr(self, "_clear_all_markers"):
            self._clear_all_markers()
            logger.info("Cleared all markers")
