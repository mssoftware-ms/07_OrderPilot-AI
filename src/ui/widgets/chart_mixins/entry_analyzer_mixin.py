"""Entry Analyzer Mixin for Chart Widget.

Provides integration of the Entry Analyzer popup
with the embedded TradingView chart.

Phase 3: Added BackgroundRunner for live analysis.
Phase 4: Added Regime Filter dropdown for filtering regime lines on chart.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QAction, QColor, QIcon
from PyQt6.QtWidgets import QMessageBox, QToolButton, QMenu, QWidget, QHBoxLayout, QLabel, QPushButton

from .live_analysis_bridge import LiveAnalysisBridge
from src.ui.icons import get_icon

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
                from_idx=from_idx if from_idx is not None else self._visible_range.get("from_idx"),
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

    Phase 4 additions:
    - Regime filter dropdown for filtering displayed regime lines
    - Store current regime data for re-filtering
    """

    _entry_analyzer_popup = None
    _analysis_worker = None
    _live_bridge: LiveAnalysisBridge | None = None
    _live_mode_enabled: bool = False
    _auto_draw_entries: bool = True
    _current_json_config_path: str | None = None  # Issue #28: Current JSON config path

    # Phase 4: Regime Filter
    _regime_filter_button: QToolButton | None = None
    _regime_filter_menu: QMenu | None = None
    _current_regime_data: list[dict] = []  # Store current regime data for re-filtering
    _regime_filter_enabled: bool = True  # Whether filtering is active

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

    # ==================== Regime Filter Methods (Phase 4) ====================

    def create_regime_filter_widget(self) -> QWidget:
        """Create the regime filter widget for toolbar integration.

        Returns a container widget with the filter button.
        Call this from toolbar setup to add the filter.

        Returns:
            QWidget containing filter button
        """
        # Create the button as a QPushButton to match the "Markierungen" button
        self._regime_filter_button = QPushButton("Filter")
        self._regime_filter_button.setToolTip("Markierungen filtern")
        self._regime_filter_button.setIcon(get_icon("filter_alt"))
        
        # Standard toolbar button properties
        if hasattr(self, "ICON_SIZE"):
            self._regime_filter_button.setIconSize(self.ICON_SIZE)
        else:
            from PyQt6.QtCore import QSize
            self._regime_filter_button.setIconSize(QSize(20, 20))
            
        if hasattr(self, "BUTTON_HEIGHT"):
            self._regime_filter_button.setFixedHeight(self.BUTTON_HEIGHT)
        else:
            self._regime_filter_button.setFixedHeight(32)
            
        self._regime_filter_button.setProperty("class", "toolbar-button")

        # Create menu
        self._regime_filter_menu = QMenu(self._regime_filter_button)
        self._regime_filter_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                border: 1px solid #4a4a4d;
                color: #e0e0e0;
            }
            QMenu::item {
                padding: 5px 20px 5px 30px; /* Space for checkbox */
            }
            QMenu::item:selected {
                background-color: #3d3d40;
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                left: 6px;
            }
        """)
        self._regime_filter_button.setMenu(self._regime_filter_menu)

        self._regime_filter_enabled = True

        # Add default regime types (will be updated when regimes are detected)
        self._populate_regime_filter_defaults()

        logger.info("✓ Regime filter button created (QPushButton)")
        return self._regime_filter_button

    def _populate_regime_filter_defaults(self) -> None:
        """Populate the regime filter menu with default regime types."""
        if not self._regime_filter_menu:
            return

        self._regime_filter_menu.clear()

        # Add "All" action
        all_action = QAction("Alle", self._regime_filter_menu)
        all_action.setCheckable(True)
        all_action.setChecked(True)
        all_action.setData("__header__")
        all_action.triggered.connect(self._on_regime_filter_action_triggered)
        self._regime_filter_menu.addAction(all_action)

        self._regime_filter_menu.addSeparator()

        # Default regimes based on 9-level hierarchy
        default_regimes = [
            ("STRONG_TF", "STRONG_TF"),
            ("STRONG_BULL", "STRONG_BULL"),
            ("STRONG_BEAR", "STRONG_BEAR"),
            ("TF", "TF"),
            ("BULL_EXHAUSTION", "BULL_EXHAUSTION"),
            ("BEAR_EXHAUSTION", "BEAR_EXHAUSTION"),
            ("BULL", "BULL"),
            ("BEAR", "BEAR"),
            ("SIDEWAYS", "SIDEWAYS"),
        ]

        # Regime colors for visual indication (optional, QAction doesn't support colored text easily without HTML or icons)
        # We'll just use text for now, or could use icons if available.

        for display_name, regime_id in default_regimes:
            action = QAction(display_name, self._regime_filter_menu)
            action.setCheckable(True)
            action.setChecked(True)
            action.setData(regime_id)
            action.triggered.connect(self._on_regime_filter_action_triggered)
            self._regime_filter_menu.addAction(action)

    def _update_regime_filter_from_data(self, regimes: list[dict]) -> None:
        """Update regime filter menu based on detected regimes.

        Args:
            regimes: List of regime period dicts with 'regime' key
        """
        print(f"[ENTRY_ANALYZER] _update_regime_filter_from_data called with {len(regimes)} items", flush=True)
        
        # Ensure menu exists and is attached
        if not self._regime_filter_menu:
            if self._regime_filter_button:
                self._regime_filter_menu = self._regime_filter_button.menu()
            
            if not self._regime_filter_menu:
                print("[ENTRY_ANALYZER] _regime_filter_menu is None and could not be recovered!", flush=True)
                return

        try:
            # Extract unique regime IDs from data
            detected_regime_ids = set()
            for i, regime_data in enumerate(regimes):
                try:
                    # Handle both dict and object (just in case)
                    if isinstance(regime_data, dict):
                        regime_id = regime_data.get('regime', 'UNKNOWN')
                    else:
                        regime_id = getattr(regime_data, 'regime', 'UNKNOWN')
                        
                    detected_regime_ids.add(regime_id)
                except Exception as e:
                    print(f"[ENTRY_ANALYZER] Error extracting ID from item {i}: {e}", flush=True)
                    continue

            print(f"[ENTRY_ANALYZER] Detected unique IDs: {detected_regime_ids}", flush=True)

            # Get currently selected items to preserve selection
            # If menu was empty or invalid, this might return empty list.
            currently_selected = []
            try:
                currently_selected = self.get_selected_items()
            except Exception:
                pass # Ignore error getting selection from old menu state

            # Clear and repopulate
            self._regime_filter_menu.clear()

            # Add "All" action
            all_action = QAction(f"Alle ({len(detected_regime_ids)})", self._regime_filter_menu)
            all_action.setCheckable(True)
            all_action.setData("__header__")
            all_action.triggered.connect(self._on_regime_filter_action_triggered)
            self._regime_filter_menu.addAction(all_action)

            self._regime_filter_menu.addSeparator()

            # Regime display mapping
            regime_display = {
                "STRONG_TF": "🟣 STRONG_TF",
                "STRONG_BULL": "🟢 STRONG_BULL",
                "STRONG_BEAR": "🔴 STRONG_BEAR",
                "TF": "💜 TF",
                "BULL_EXHAUSTION": "⚠️ BULL_EXHAUST",
                "BEAR_EXHAUSTION": "⚠️ BEAR_EXHAUST",
                "BULL": "🟢 BULL",
                "BEAR": "🔴 BEAR",
                "SIDEWAYS": "🟡 SIDEWAYS",
                "UNKNOWN": "❓ UNKNOWN",
            }

            all_checked_count = 0

            # Add detected regimes
            for regime_id in sorted(detected_regime_ids):
                display_name = regime_display.get(regime_id, f"📊 {regime_id}")
                action = QAction(display_name, self._regime_filter_menu)
                action.setCheckable(True)
                action.setData(regime_id)
                
                # Preserve selection logic:
                # 1. If we had a previous selection (menu was populated), check if this ID was in it.
                # 2. If menu was empty/default (initial load), default to Checked.
                # 3. If new ID appears that wasn't in previous selection, default to Checked? 
                #    Let's default to Checked to show new data.
                
                is_checked = True
                if currently_selected:
                    is_checked = regime_id in currently_selected
                
                action.setChecked(is_checked)
                if is_checked:
                    all_checked_count += 1
                    
                action.triggered.connect(self._on_regime_filter_action_triggered)
                self._regime_filter_menu.addAction(action)

            # Update "All" state
            all_checked = (all_checked_count == len(detected_regime_ids)) and (len(detected_regime_ids) > 0)
            all_action.setChecked(all_checked)

            logger.info(f"Regime filter updated with {len(detected_regime_ids)} detected regimes")
            
        except Exception as e:
            logger.error(f"Critical error updating regime filter: {e}", exc_info=True)
            print(f"[ENTRY_ANALYZER] Critical error in _update_regime_filter_from_data: {e}", flush=True)

    def _on_regime_filter_action_triggered(self, checked: bool) -> None:
        """Handle menu action trigger."""
        sender = self.sender()
        if not isinstance(sender, QAction):
            return

        data = sender.data()
        
        if data == "__header__":
            # Toggle all
            # "All" clicked. `checked` is the new state of "All".
            # Set all other actions to this state.
            for action in self._regime_filter_menu.actions():
                if action.isCheckable() and action.data() != "__header__":
                    action.setChecked(checked)
            
        else:
            # Individual item toggled.
            # Check if all are now checked to update "All"
            all_actions = [a for a in self._regime_filter_menu.actions() if a.isCheckable() and a.data() != "__header__"]
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

    def get_selected_items(self) -> list[str]:
        """Get list of selected regime IDs."""
        if not self._regime_filter_menu:
            return []
        
        selected = []
        for action in self._regime_filter_menu.actions():
            if action.isCheckable() and action.isChecked() and action.data() != "__header__":
                data = action.data()
                if data:
                    selected.append(data)
        return selected

    def select_all_regimes(self) -> None:
        """Select all regimes in the filter."""
        if not self._regime_filter_menu:
            return
            
        for action in self._regime_filter_menu.actions():
            if action.isCheckable():
                action.setChecked(True)
        self._on_regime_filter_changed(self.get_selected_items())

    def deselect_all_regimes(self) -> None:
        """Deselect all regimes in the filter."""
        if not self._regime_filter_menu:
            return
            
        for action in self._regime_filter_menu.actions():
            if action.isCheckable():
                action.setChecked(False)
        self._on_regime_filter_changed([])

    def set_regime_filter_visible(self, regime_ids: list[str]) -> None:
        """Set which regimes are visible via the filter.

        Args:
            regime_ids: List of regime IDs to show
        """
        if not self._regime_filter_menu:
            return

        for action in self._regime_filter_menu.actions():
            if action.isCheckable() and action.data() != "__header__":
                data = action.data()
                should_check = data in regime_ids
                action.setChecked(should_check)
        
        # Update All
        all_actions = [a for a in self._regime_filter_menu.actions() if a.isCheckable() and a.data() != "__header__"]
        all_checked = all(a.isChecked() for a in all_actions)
        for action in self._regime_filter_menu.actions():
            if action.data() == "__header__":
                action.setChecked(all_checked)
                break

        self._apply_regime_filter(regime_ids)

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
            print(f"[FILTER] WARNING: No regime data to filter! Clearing lines.", flush=True)
            # Proceed to _apply_regime_filter anyway, which will clear lines if data is empty

        print(f"[FILTER] Have {len(self._current_regime_data)} regime entries to filter", flush=True)
        # Apply filter and redraw
        self._apply_regime_filter(selected_regimes)

    def _reconstruct_regime_data_from_chart(self) -> None:
        """Reconstruct _current_regime_data from existing regime lines in chart.

        This is needed when regime lines were loaded from saved chart state
        but _current_regime_data is empty.
        """
        if not hasattr(self, '_bot_overlay_state'):
            logger.debug("No _bot_overlay_state available")
            return

        regime_lines = getattr(self._bot_overlay_state, 'regime_lines', {})
        if not regime_lines:
            logger.debug("No regime lines in bot overlay state")
            return

        logger.info(f"Reconstructing regime data from {len(regime_lines)} chart lines")
        print(f"[FILTER] Reconstructing from {len(regime_lines)} existing lines", flush=True)

        reconstructed = []
        for line_id, regime_line in regime_lines.items():
            # RegimeLine has: line_id, timestamp, color, regime_name, label
            regime_entry = {
                'start_timestamp': regime_line.timestamp,
                'regime': regime_line.regime_name,
                'score': 100.0,  # Default score since we don't have original
                'duration_bars': 0,
                'duration_time': '0s',
                'line_id': line_id,
            }
            reconstructed.append(regime_entry)

        # Sort by timestamp
        reconstructed.sort(key=lambda x: x['start_timestamp'])
        self._current_regime_data = reconstructed
        logger.info(f"Reconstructed {len(reconstructed)} regime entries")
        
        # Update the filter dropdown with the actual regimes we found
        self._update_regime_filter_from_data(reconstructed)

    def _apply_regime_filter(self, selected_regimes: list[str] | None = None) -> None:
        """Apply regime filter and redraw regime lines.

        Args:
            selected_regimes: List of regime IDs to show. If None, get from menu.
        """
        print(f"[FILTER] _apply_regime_filter called with: {selected_regimes}", flush=True)

        if selected_regimes is None and self._regime_filter_menu:
            selected_regimes = self.get_selected_items()
            print(f"[FILTER] Got selection from menu: {selected_regimes}", flush=True)

        if not selected_regimes:
            # No selection means show nothing
            print(f"[FILTER] No regimes selected - clearing all lines", flush=True)
            if hasattr(self, "clear_regime_lines"):
                self.clear_regime_lines()
            return

        # Filter regime data
        filtered_regimes = [
            r for r in self._current_regime_data
            if r.get('regime', 'UNKNOWN') in selected_regimes
        ]

        logger.info(f"Applying filter: {len(filtered_regimes)}/{len(self._current_regime_data)} regimes visible")
        print(f"[FILTER] Filtered: {len(filtered_regimes)}/{len(self._current_regime_data)} regimes", flush=True)
        
        # Debug: Show what was filtered out
        if len(self._current_regime_data) > 0 and len(filtered_regimes) == 0:
            all_regimes = set(r.get('regime', 'UNKNOWN') for r in self._current_regime_data)
            print(f"[FILTER] All available regimes: {all_regimes}", flush=True)
            print(f"[FILTER] Selected regimes: {selected_regimes}", flush=True)

        # Redraw filtered regimes (use internal method to avoid storing again)
        self._draw_regime_lines_internal(filtered_regimes)

    # ==================== End Regime Filter Methods ====================

    def show_entry_analyzer(self) -> None:
        """Show the Entry Analyzer popup dialog."""
        from src.ui.dialogs.entry_analyzer import EntryAnalyzerPopup

        if self._entry_analyzer_popup is None:
            self._entry_analyzer_popup = EntryAnalyzerPopup(self)
            self._entry_analyzer_popup.analyze_requested.connect(
                self._start_visible_range_analysis
            )
            self._entry_analyzer_popup.draw_entries_requested.connect(
                self._draw_entry_markers
            )
            # Patterns overlay
            self._entry_analyzer_popup.draw_patterns_requested.connect(
                self._draw_pattern_overlays
            )
            self._entry_analyzer_popup.clear_entries_requested.connect(
                self._clear_entry_markers
            )
            # Issue #21: Connect regime lines signal
            self._entry_analyzer_popup.draw_regime_lines_requested.connect(
                self._draw_regime_lines
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

    def hide_entry_analyzer(self) -> None:
        """Hide the Entry Analyzer popup dialog if it exists."""
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.close()

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

    def _draw_pattern_overlays(self, overlays: list[dict]) -> None:
        """Draw pattern overlays using real lines/boxes on the chart."""
        candles = self._get_candles_for_validation()
        if not candles:
            logger.warning("No candles available for pattern overlay")
            return
        if not hasattr(self, "_execute_js"):
            logger.warning("Chart widget cannot execute JS for overlays")
            return

        # Clear previous pattern drawings
        self._execute_js("window.chartAPI?.removeDrawingsByPrefix('pattern_');")

        # map idx -> timestamp/price
        ts_map: dict[int, tuple[int, float]] = {}
        for idx, c in enumerate(candles):
            ts = c.get("timestamp")
            if hasattr(ts, "timestamp"):
                ts = int(ts.timestamp())
            ts_map[idx] = (int(ts), float(c.get("close", 0.0)))

        def _js_trend_line(t1: int, p1: float, t2: int, p2: float, color: str, line_id: str) -> None:
            """Inject JS to add a trend line with custom ID (removable by prefix)."""
            self._execute_js(
                f"""
                (() => {{
                    try {{
                        const line = new TrendLinePrimitive({{time:{t1}, price:{p1}}}, {{time:{t2}, price:{p2}}}, '{color}', '{line_id}');
                        if (typeof priceSeries !== 'undefined') {{
                            priceSeries.attachPrimitive(line);
                            if (typeof drawings !== 'undefined') drawings.push(line);
                        }} else {{
                            window.chartAPI?.addTrendLine({{time:{t1}, price:{p1}}}, {{time:{t2}, price:{p2}}}, '{color}');
                        }}
                    }} catch(e) {{ console.error('pattern trend line error', e); }}
                }})();"""
            )

        def _js_box(t1: int, p1: float, t2: int, p2: float, box_id: str, color: str) -> None:
            """Inject JS to draw a percent rectangle."""
            self._execute_js(
                f"window.chartAPI?.addPercentRect({{time:{t1}, price:{p1}}}, {{time:{t2}, price:{p2}}}, '{box_id}');"
            )
            # Add subtle border line on top/bottom for clarity
            self._execute_js(
                f"window.chartAPI?.addHorizontalLine({p1}, '{color}', '{box_id}_low', 'dashed', '{box_id}_low');"
            )
            self._execute_js(
                f"window.chartAPI?.addHorizontalLine({p2}, '{color}', '{box_id}_high', 'dashed', '{box_id}_high');"
            )

        for ov_idx, ov in enumerate(overlays):
            name = ov.get("pattern", "PATTERN")
            lines = ov.get("lines", {}) or {}
            boxes = ov.get("boxes", {}) or {}

            color = "#26a69a" if "Bull" in name or "bull" in name else "#ef5350" if "Bear" in name or "bear" in name else "#ffeb3b"

            # Draw lines
            for line_key, line_points in lines.items():
                if len(line_points) < 2:
                    continue
                start_idx, start_price = line_points[0]
                end_idx, end_price = line_points[-1]
                if start_idx not in ts_map or end_idx not in ts_map:
                    continue
                t1, _ = ts_map[start_idx]
                t2, _ = ts_map[end_idx]
                line_id = f"pattern_line_{ov_idx}_{line_key}"
                _js_trend_line(t1, start_price, t2, end_price, color, line_id)

            # Draw boxes (order blocks / FVG)
            for box_key, box in boxes.items():
                start_idx, end_idx, low, high = box
                if start_idx not in ts_map or end_idx not in ts_map:
                    continue
                t1, _ = ts_map[start_idx]
                t2, _ = ts_map[end_idx]
                box_id = f"pattern_box_{ov_idx}_{box_key}"
                _js_box(t1, low, t2, high, box_id, color)

    def _clear_entry_markers(self) -> None:
        """Clear all entry markers from the chart."""
        if hasattr(self, "clear_bot_markers"):
            self.clear_bot_markers()
            logger.info("Cleared entry markers")
        elif hasattr(self, "_clear_all_markers"):
            self._clear_all_markers()
            logger.info("Cleared all markers")

    def _get_price_at_timestamp(self, timestamp: int) -> float | None:
        """Get the close price at a specific timestamp.

        Args:
            timestamp: Unix timestamp in seconds

        Returns:
            Close price or None if not found
        """
        if not hasattr(self, '_candles') or not self._candles:
            return None

        # Find candle closest to timestamp
        closest_candle = None
        min_diff = float('inf')

        for candle in self._candles:
            candle_time = candle.get('time', candle.get('timestamp', 0))
            diff = abs(candle_time - timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_candle = candle

        if closest_candle:
            return closest_candle.get('close', None)
        return None

    def _draw_regime_lines(self, regimes: list[dict]) -> None:
        """Draw regime period lines on the chart (Issue #21 COMPLETE).

        Stores regime data for filtering and draws lines based on current filter.

        Displays vertical lines showing START of each regime period with:
        - Start line: Light color for regime start
        - Each regime type has unique color pair

        Color Table:
        ┌─────────────────────┬─────────────┬─────────────┬─────────────────────┐
        │ Regime Type         │ START Color │ END Color   │ Description         │
        ├─────────────────────┼─────────────┼─────────────┼─────────────────────┤
        │ STRONG_TREND_BULL   │ #A8E6A3     │ #7BC67A     │ Light/Dark Green    │
        │ STRONG_TREND_BEAR   │ #FFB3BA     │ #FF8A94     │ Light/Dark Red      │
        │ OVERBOUGHT          │ #FFD4A3     │ #FFB870     │ Light/Dark Orange   │
        │ OVERSOLD            │ #A3D8FF     │ #70B8FF     │ Light/Dark Blue     │
        │ RANGE               │ #D3D3D3     │ #AAAAAA     │ Light/Dark Gray     │
        │ UNKNOWN             │ #E0E0E0     │ #C0C0C0     │ Very Light Gray     │
        └─────────────────────┴─────────────┴─────────────┴─────────────────────┘

        Args:
            regimes: List of regime PERIODS with start_timestamp, end_timestamp, regime, score, duration
        """
        if not hasattr(self, "add_regime_line"):
            logger.warning("Chart widget has no add_regime_line method")
            return

        # Phase 4: Store regime data for filtering
        self._current_regime_data = regimes.copy() if regimes else []
        print(f"[ENTRY_ANALYZER] _draw_regime_lines called with {len(regimes)} items", flush=True)

        # Update filter dropdown with detected regimes
        try:
            self._update_regime_filter_from_data(regimes)
        except Exception as e:
            logger.error(f"Failed to update regime filter menu: {e}", exc_info=True)
            print(f"[ENTRY_ANALYZER] ERROR updating filter menu: {e}", flush=True)

        # Apply current filter (if filter exists, use its selection; otherwise show all)
        if self._regime_filter_menu:
            selected = self.get_selected_items()
            if selected:
                filtered_regimes = [r for r in regimes if r.get('regime', 'UNKNOWN') in selected]
            else:
                # If menu exists but nothing selected, assume filter not initialized yet → show all
                # This fixes the issue where regimes aren't drawn on first "Analyse visible Range"
                print("[ENTRY_ANALYZER] Filter exists but selection empty -> Drawing ALL (filter not initialized)", flush=True)
                filtered_regimes = regimes  # Show all when filter is empty
        else:
            print("[ENTRY_ANALYZER] No filter menu -> Drawing ALL", flush=True)
            filtered_regimes = regimes  # No filter widget, show all

        # Draw the filtered regimes
        self._draw_regime_lines_internal(filtered_regimes)

    def _draw_regime_lines_internal(self, regimes: list[dict]) -> None:
        """Internal method to draw regime lines without storing data.

        Called by _draw_regime_lines and _apply_regime_filter.

        Args:
            regimes: Filtered list of regime PERIODS to draw
        """
        if not hasattr(self, "add_regime_line"):
            print("[ENTRY_ANALYZER] ❌ ERROR: add_regime_line method NOT FOUND!", flush=True)
            logger.error("Chart widget missing add_regime_line method - cannot draw regime lines")
            return
        else:
            print(f"[ENTRY_ANALYZER] ✅ add_regime_line method exists, drawing {len(regimes)} regimes", flush=True)

        # Color mapping: regime_type -> (start_color, end_color)
        # Issue #5: Each regime has unique, distinguishable color
        # Supports v2 JSON regime IDs (BULL_TREND, BEAR_TREND, CHOP_ZONE...) and legacy names
        regime_colors = {
            # === V2 JSON Regime IDs ===
            "BULL_TREND": ("#22c55e", "#22c55e"),           # Green for bullish trend
            "BEAR_TREND": ("#ef4444", "#ef4444"),           # Red for bearish trend
            "CHOP_ZONE": ("#f59e0b", "#f59e0b"),            # Amber for chop/sideways
            "SIDEWAYS": ("#f59e0b", "#f59e0b"),             # Amber for sideways
            
            # === Generic V2 Pattern Matching ===
            "BULL": ("#22c55e", "#22c55e"),                 # Green for any bullish
            "BEAR": ("#ef4444", "#ef4444"),                 # Red for any bearish
            "CHOP": ("#f59e0b", "#f59e0b"),                 # Amber for chop
            "RANGE": ("#f59e0b", "#f59e0b"),                # Amber for range
            
            # === Extended V2 Regimes ===
            "STRONG_BULL": ("#16a34a", "#16a34a"),          # Dark green for strong bull (RSI confirmed)
            "STRONG_BEAR": ("#dc2626", "#dc2626"),          # Dark red for strong bear (RSI confirmed)
            "STRONG_TF": ("#6d28d9", "#6d28d9"),            # Dark purple for strong trend following
            "TF": ("#8b5cf6", "#8b5cf6"),                   # Purple for trend following
            "TREND_FOLLOWING": ("#8b5cf6", "#8b5cf6"),      # Purple for trend following (alias)
            "STRONG_TREND": ("#6d28d9", "#6d28d9"),         # Dark purple for strong trend
            "WEAK_TREND": ("#a3a3a3", "#a3a3a3"),           # Gray for weak trend
            "NO_TRADE": ("#6b7280", "#6b7280"),             # Dark gray for no trade zone

            # === Exhaustion / Reversal Warning Regimes ===
            "BULL_EXHAUSTION": ("#fbbf24", "#fbbf24"),      # Yellow-amber for bullish exhaustion (reversal warning)
            "BEAR_EXHAUSTION": ("#fb923c", "#fb923c"),      # Orange for bearish exhaustion (reversal warning)
            
            # === Overbought/Oversold ===
            "OVERBOUGHT": ("#f97316", "#f97316"),           # Orange
            "OVERSOLD": ("#3b82f6", "#3b82f6"),             # Blue
            "SIDEWAYS_OVERBOUGHT": ("#f97316", "#f97316"),  # Orange
            "SIDEWAYS_OVERSOLD": ("#3b82f6", "#3b82f6"),    # Blue
            
            # === Legacy Names ===
            "STRONG_TREND_BULL": ("#22c55e", "#22c55e"),
            "STRONG_TREND_BEAR": ("#ef4444", "#ef4444"),
            
            # === Fallback ===
            "UNKNOWN": ("#9ca3af", "#9ca3af"),              # Gray for unknown
        }
        
        def get_regime_color(regime_id: str) -> tuple[str, str]:
            """Get color for regime ID with intelligent pattern matching."""
            # Exact match first
            if regime_id in regime_colors:
                return regime_colors[regime_id]
            
            # Pattern matching for v2 regime IDs
            regime_upper = regime_id.upper()
            
            # Check for TF/TREND_FOLLOWING first (before BULL/BEAR checks)
            if regime_upper == "STRONG_TF":
                return ("#6d28d9", "#6d28d9")  # Dark purple for strong TF
            elif regime_upper == "TF":
                return ("#8b5cf6", "#8b5cf6")  # Purple for TF
            elif "TREND_FOLLOWING" in regime_upper or ("TREND" in regime_upper and "FOLLOWING" in regime_upper):
                return ("#8b5cf6", "#8b5cf6")  # Purple for trend following
            elif "STRONG_TREND" in regime_upper:
                return ("#6d28d9", "#6d28d9")  # Dark purple for strong trend
            # Check for exhaustion/reversal patterns BEFORE general BULL/BEAR
            elif "EXHAUSTION" in regime_upper:
                if "BULL" in regime_upper:
                    return ("#fbbf24", "#fbbf24")  # Yellow-amber for bull exhaustion
                elif "BEAR" in regime_upper:
                    return ("#fb923c", "#fb923c")  # Orange for bear exhaustion
                return ("#fbbf24", "#fbbf24")  # Default yellow for any exhaustion
            elif "BULL" in regime_upper:
                return ("#22c55e", "#22c55e")  # Green
            elif "BEAR" in regime_upper:
                return ("#ef4444", "#ef4444")  # Red
            elif "CHOP" in regime_upper or "SIDEWAYS" in regime_upper or "RANGE" in regime_upper:
                return ("#f59e0b", "#f59e0b")  # Amber
            elif "OVERBOUGHT" in regime_upper:
                return ("#f97316", "#f97316")  # Orange
            elif "OVERSOLD" in regime_upper:
                return ("#3b82f6", "#3b82f6")  # Blue
            elif "NO_TRADE" in regime_upper or "NOTRADE" in regime_upper:
                return ("#6b7280", "#6b7280")  # Dark gray
            
            # Fallback
            return regime_colors["UNKNOWN"]

        # Clear existing regime lines first
        if hasattr(self, "clear_regime_lines"):
            self.clear_regime_lines()

        # Draw new regime lines (START only for each period)
        print(f"[ENTRY_ANALYZER] Drawing {len(regimes)} regime lines...", flush=True)
        for i, regime_data in enumerate(regimes):
            raw_start_ts = regime_data.get('start_timestamp', 0)
            # Normalize to seconds for lightweight-charts (handles ms inputs)
            start_timestamp = int(raw_start_ts)
            if start_timestamp > 1e12:
                start_timestamp //= 1000
            elif start_timestamp > 1e10:
                start_timestamp = int(start_timestamp / 1000)
            regime = regime_data.get('regime', 'UNKNOWN')
            score = regime_data.get('score', 0)
            duration_bars = regime_data.get('duration_bars', 0)
            duration_time = regime_data.get('duration_time', '0s')

            # Get colors for this regime type (with intelligent pattern matching)
            start_color, end_color = get_regime_color(regime)

            logger.debug(f"Regime {i}: {regime} -> color: {start_color}")
            print(f"[ENTRY_ANALYZER] Regime {i}: {regime} at timestamp {start_timestamp} (raw={raw_start_ts}), color: {start_color}", flush=True)

            # Create label (just regime name with score, no "START" prefix)
            regime_label = f"{regime.replace('_', ' ')} ({score:.1f})"

            # Add regime line to chart
            print(f"[ENTRY_ANALYZER] Calling add_regime_line(id=regime_{i}, ts={start_timestamp}, name={regime}, label={regime_label}, color={start_color})", flush=True)
            self.add_regime_line(
                line_id=f"regime_{i}",
                timestamp=start_timestamp,
                regime_name=regime,
                label=regime_label,
                color=start_color
            )
            print(f"[ENTRY_ANALYZER] ✅ add_regime_line called for regime {i}", flush=True)

            # Add arrow markers at regime start (Issue: Regime arrows)
            # Get price at regime start timestamp
            start_price = self._get_price_at_timestamp(start_timestamp)
            if start_price is not None and hasattr(self, 'add_bot_marker'):
                from src.ui.widgets.chart_mixins.bot_overlay_types import MarkerType

                # Determine marker type based on regime
                if "BULL" in regime.upper() or "UP" in regime.upper():
                    marker_type = MarkerType.REGIME_BULL
                    side = "long"
                elif "BEAR" in regime.upper() or "DOWN" in regime.upper():
                    marker_type = MarkerType.REGIME_BEAR
                    side = "short"
                else:
                    # For other regimes (RANGE, OVERBOUGHT, OVERSOLD), skip marker
                    continue

                # Add marker arrow
                self.add_bot_marker(
                    timestamp=start_timestamp,
                    price=start_price,
                    marker_type=marker_type,
                    side=side,
                    text=f"{regime.replace('_', ' ')}",
                    score=score
                )
                logger.debug(f"Added regime marker: {marker_type.value} at {start_price:.2f}")

        logger.info(
            "Drew %d regime periods (%d lines) on chart",
            len(regimes),
            len(regimes)  # 1 line per period (start only)
        )

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
