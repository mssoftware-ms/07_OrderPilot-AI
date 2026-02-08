"""Entry Analyzer Logic Mixin - Business Logic and Drawing.

Provides business logic, data processing, and chart drawing functionality
for the Entry Analyzer.

Part of the modular entry_analyzer split (Task 3.3.4):
- entry_analyzer_ui_mixin.py: UI components
- entry_analyzer_events_mixin.py: Event handlers
- entry_analyzer_logic_mixin.py (this file): Business logic

Agent: CODER-021
Task: 3.3.4 - entry_analyzer_mixin refactoring
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import EntryEvent, RegimeType

logger = logging.getLogger(__name__)

# Import debug logger
try:
    from src.analysis.visible_chart.debug_logger import debug_logger
except ImportError:
    debug_logger = logger


class EntryAnalyzerLogicMixin:
    """Mixin for Entry Analyzer business logic and drawing.

    Provides:
    - Entry markers drawing
    - Regime lines drawing
    - Pattern overlays
    - Data processing and filtering
    - Chart reconstruction logic

    Requires the chart widget to have:
    - add_bot_marker() method (from BotOverlayMixin)
    - clear_bot_markers() method
    - add_regime_line() method
    - clear_regime_lines() method
    - _execute_js() method (for pattern overlays)
    - data attribute (pandas DataFrame)
    """

    # Class attributes
    _current_regime_data: list[dict] = []
    _regime_filter_menu = None

    # ==================== Data Extraction ====================

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

    def _get_price_at_timestamp(self, timestamp: int) -> float | None:
        """Get the close price at a specific timestamp.

        Args:
            timestamp: Unix timestamp in seconds

        Returns:
            Close price or None if not found
        """
        if not hasattr(self, "_candles") or not self._candles:
            return None

        # Find candle closest to timestamp
        closest_candle = None
        min_diff = float("inf")

        for candle in self._candles:
            candle_time = candle.get("time", candle.get("timestamp", 0))
            diff = abs(candle_time - timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_candle = candle

        if closest_candle:
            return closest_candle.get("close", None)
        return None

    # ==================== Entry Markers Drawing ====================

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

    # ==================== Pattern Overlays ====================

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

        def _js_trend_line(
            t1: int, p1: float, t2: int, p2: float, color: str, line_id: str
        ) -> None:
            """Inject JS to add a trend line with custom ID."""
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

        def _js_box(
            t1: int, p1: float, t2: int, p2: float, box_id: str, color: str
        ) -> None:
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

            color = (
                "#26a69a"
                if "Bull" in name or "bull" in name
                else "#ef5350" if "Bear" in name or "bear" in name else "#ffeb3b"
            )

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

    # ==================== Regime Lines Drawing ====================

    def _draw_regime_lines(self, regimes: list[dict]) -> None:
        """Draw regime period lines on the chart (Issue #21 COMPLETE).

        Stores regime data for filtering and draws lines based on current filter.

        Args:
            regimes: List of regime PERIODS with start_timestamp, regime, score, duration
        """
        if not hasattr(self, "add_regime_line"):
            logger.warning("Chart widget has no add_regime_line method")
            return

        # Store regime data for filtering
        self._current_regime_data = regimes.copy() if regimes else []
        print(
            f"[ENTRY_ANALYZER] _draw_regime_lines called with {len(regimes)} items",
            flush=True,
        )

        # Update filter dropdown with detected regimes
        try:
            self._update_regime_filter_from_data(regimes)
        except Exception as e:
            logger.error(f"Failed to update regime filter menu: {e}", exc_info=True)
            print(f"[ENTRY_ANALYZER] ERROR updating filter menu: {e}", flush=True)

        # Apply current filter (if filter UI is available)
        filtered_regimes = regimes  # Default: draw all
        try:
            if self._regime_filter_menu:
                selected = self.get_selected_items()
                if selected:
                    filtered_regimes = [
                        r for r in regimes if r.get("regime", "UNKNOWN") in selected
                    ]
                else:
                    # If menu exists but nothing selected, show all (filter not initialized)
                    print(
                        "[ENTRY_ANALYZER] Filter exists but selection empty -> Drawing ALL",
                        flush=True,
                    )
            else:
                print("[ENTRY_ANALYZER] No filter menu -> Drawing ALL", flush=True)
        except (NotImplementedError, AttributeError) as e:
            # Filter UI not available (e.g. called from StrategySettingsDialog)
            print(f"[ENTRY_ANALYZER] Filter not available ({e}) -> Drawing ALL", flush=True)
            filtered_regimes = regimes

        # Draw the filtered regimes
        self._draw_regime_lines_internal(filtered_regimes)

    def _draw_regime_lines_internal(self, regimes: list[dict]) -> None:
        """Internal method to draw regime lines without storing data.

        Called by _draw_regime_lines and _apply_regime_filter.

        Args:
            regimes: Filtered list of regime PERIODS to draw
        """
        if not hasattr(self, "add_regime_line"):
            print(
                "[ENTRY_ANALYZER] ❌ ERROR: add_regime_line method NOT FOUND!",
                flush=True,
            )
            logger.error(
                "Chart widget missing add_regime_line method - cannot draw regime lines"
            )
            return
        else:
            print(
                f"[ENTRY_ANALYZER] ✅ add_regime_line method exists, drawing {len(regimes)} regimes",
                flush=True,
            )

        # Color mapping for regime types
        regime_colors = {
            # === V2 JSON Regime IDs ===
            "BULL_TREND": ("#22c55e", "#22c55e"),
            "BEAR_TREND": ("#ef4444", "#ef4444"),
            "CHOP_ZONE": ("#f59e0b", "#f59e0b"),
            "SIDEWAYS": ("#f59e0b", "#f59e0b"),
            # === Generic ===
            "BULL": ("#22c55e", "#22c55e"),
            "BEAR": ("#ef4444", "#ef4444"),
            "CHOP": ("#f59e0b", "#f59e0b"),
            "RANGE": ("#f59e0b", "#f59e0b"),
            # === Extended ===
            "STRONG_BULL": ("#16a34a", "#16a34a"),
            "STRONG_BEAR": ("#dc2626", "#dc2626"),
            "STRONG_TF": ("#6d28d9", "#6d28d9"),
            "TF": ("#8b5cf6", "#8b5cf6"),
            "TREND_FOLLOWING": ("#8b5cf6", "#8b5cf6"),
            "STRONG_TREND": ("#6d28d9", "#6d28d9"),
            "WEAK_TREND": ("#a3a3a3", "#a3a3a3"),
            "NO_TRADE": ("#6b7280", "#6b7280"),
            # === Exhaustion ===
            "BULL_EXHAUSTION": ("#fbbf24", "#fbbf24"),
            "BEAR_EXHAUSTION": ("#fb923c", "#fb923c"),
            # === Overbought/Oversold ===
            "OVERBOUGHT": ("#f97316", "#f97316"),
            "OVERSOLD": ("#3b82f6", "#3b82f6"),
            "SIDEWAYS_OVERBOUGHT": ("#f97316", "#f97316"),
            "SIDEWAYS_OVERSOLD": ("#3b82f6", "#3b82f6"),
            # === Legacy ===
            "STRONG_TREND_BULL": ("#22c55e", "#22c55e"),
            "STRONG_TREND_BEAR": ("#ef4444", "#ef4444"),
            # === Fallback ===
            "UNKNOWN": ("#9ca3af", "#9ca3af"),
        }

        def get_regime_color(regime_id: str) -> tuple[str, str]:
            """Get color for regime ID with intelligent pattern matching."""
            if regime_id in regime_colors:
                return regime_colors[regime_id]

            regime_upper = regime_id.upper()

            # Pattern matching
            if regime_upper == "STRONG_TF":
                return ("#6d28d9", "#6d28d9")
            elif regime_upper == "TF":
                return ("#8b5cf6", "#8b5cf6")
            elif "TREND_FOLLOWING" in regime_upper:
                return ("#8b5cf6", "#8b5cf6")
            elif "STRONG_TREND" in regime_upper:
                return ("#6d28d9", "#6d28d9")
            elif "EXHAUSTION" in regime_upper:
                if "BULL" in regime_upper:
                    return ("#fbbf24", "#fbbf24")
                elif "BEAR" in regime_upper:
                    return ("#fb923c", "#fb923c")
                return ("#fbbf24", "#fbbf24")
            elif "BULL" in regime_upper:
                return ("#22c55e", "#22c55e")
            elif "BEAR" in regime_upper:
                return ("#ef4444", "#ef4444")
            elif "CHOP" in regime_upper or "SIDEWAYS" in regime_upper or "RANGE" in regime_upper:
                return ("#f59e0b", "#f59e0b")
            elif "OVERBOUGHT" in regime_upper:
                return ("#f97316", "#f97316")
            elif "OVERSOLD" in regime_upper:
                return ("#3b82f6", "#3b82f6")
            elif "NO_TRADE" in regime_upper:
                return ("#6b7280", "#6b7280")

            return regime_colors["UNKNOWN"]

        # Clear existing regime lines
        if hasattr(self, "clear_regime_lines"):
            self.clear_regime_lines()

        # Draw new regime lines
        print(f"[ENTRY_ANALYZER] Drawing {len(regimes)} regime lines...", flush=True)
        for i, regime_data in enumerate(regimes):
            raw_start_ts = regime_data.get("start_timestamp", 0)
            # Normalize to seconds
            start_timestamp = int(raw_start_ts)
            if start_timestamp > 1e12:
                start_timestamp //= 1000
            elif start_timestamp > 1e10:
                start_timestamp = int(start_timestamp / 1000)

            regime = regime_data.get("regime", "UNKNOWN")
            score = regime_data.get("score", 0)

            # Get colors
            start_color, end_color = get_regime_color(regime)

            logger.debug(f"Regime {i}: {regime} -> color: {start_color}")
            print(
                f"[ENTRY_ANALYZER] Regime {i}: {regime} at {start_timestamp}, color: {start_color}",
                flush=True,
            )

            # Create label
            regime_label = f"{regime.replace('_', ' ')} ({score:.1f})"

            # Add regime line
            print(
                f"[ENTRY_ANALYZER] Calling add_regime_line(regime_{i}, {start_timestamp}, {regime})",
                flush=True,
            )
            self.add_regime_line(
                line_id=f"regime_{i}",
                timestamp=start_timestamp,
                regime_name=regime,
                label=regime_label,
                color=start_color,
            )

            # Add arrow markers at regime start
            start_price = self._get_price_at_timestamp(start_timestamp)
            if start_price is not None and hasattr(self, "add_bot_marker"):
                from src.ui.widgets.chart_mixins.bot_overlay_types import MarkerType

                # Determine marker type
                if "BULL" in regime.upper() or "UP" in regime.upper():
                    marker_type = MarkerType.REGIME_BULL
                    side = "long"
                elif "BEAR" in regime.upper() or "DOWN" in regime.upper():
                    marker_type = MarkerType.REGIME_BEAR
                    side = "short"
                else:
                    continue

                # Add marker
                self.add_bot_marker(
                    timestamp=start_timestamp,
                    price=start_price,
                    marker_type=marker_type,
                    side=side,
                    text=f"{regime.replace('_', ' ')}",
                    score=score,
                )
                logger.debug(f"Added regime marker: {marker_type.value} at {start_price:.2f}")

        logger.info(
            "Drew %d regime periods on chart",
            len(regimes),
        )

    # ==================== Regime Filter Logic ====================

    def _reconstruct_regime_data_from_chart(self) -> None:
        """Reconstruct _current_regime_data from existing regime lines in chart.

        This is needed when regime lines were loaded from saved chart state
        but _current_regime_data is empty.
        """
        if not hasattr(self, "_bot_overlay_state"):
            logger.debug("No _bot_overlay_state available")
            return

        regime_lines = getattr(self._bot_overlay_state, "regime_lines", {})
        if not regime_lines:
            logger.debug("No regime lines in bot overlay state")
            return

        logger.info(f"Reconstructing regime data from {len(regime_lines)} chart lines")
        print(
            f"[FILTER] Reconstructing from {len(regime_lines)} existing lines", flush=True
        )

        reconstructed = []
        for line_id, regime_line in regime_lines.items():
            regime_entry = {
                "start_timestamp": regime_line.timestamp,
                "regime": regime_line.regime_name,
                "score": 100.0,
                "duration_bars": 0,
                "duration_time": "0s",
                "line_id": line_id,
            }
            reconstructed.append(regime_entry)

        # Sort by timestamp
        reconstructed.sort(key=lambda x: x["start_timestamp"])
        self._current_regime_data = reconstructed
        logger.info(f"Reconstructed {len(reconstructed)} regime entries")

        # Update the filter dropdown
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
            print(f"[FILTER] No regimes selected - clearing all lines", flush=True)
            if hasattr(self, "clear_regime_lines"):
                self.clear_regime_lines()
            return

        # Filter regime data
        filtered_regimes = [
            r
            for r in self._current_regime_data
            if r.get("regime", "UNKNOWN") in selected_regimes
        ]

        logger.info(
            f"Applying filter: {len(filtered_regimes)}/{len(self._current_regime_data)} regimes visible"
        )
        print(
            f"[FILTER] Filtered: {len(filtered_regimes)}/{len(self._current_regime_data)} regimes",
            flush=True,
        )

        # Debug: Show what was filtered out
        if len(self._current_regime_data) > 0 and len(filtered_regimes) == 0:
            all_regimes = set(
                r.get("regime", "UNKNOWN") for r in self._current_regime_data
            )
            print(f"[FILTER] All available regimes: {all_regimes}", flush=True)
            print(f"[FILTER] Selected regimes: {selected_regimes}", flush=True)

        # Redraw filtered regimes
        self._draw_regime_lines_internal(filtered_regimes)

    # ==================== Forward Declarations (implemented in other mixins) ====================

    def get_selected_items(self) -> list[str]:
        """Get selected items (implemented in UI mixin)."""
        raise NotImplementedError("Must be provided by EntryAnalyzerUIMixin")

    def _update_regime_filter_from_data(self, regimes: list[dict]) -> None:
        """Update filter from data (implemented in UI mixin)."""
        raise NotImplementedError("Must be provided by EntryAnalyzerUIMixin")
