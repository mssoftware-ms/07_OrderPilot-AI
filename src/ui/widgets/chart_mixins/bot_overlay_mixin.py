"""Bot Overlay Mixin for Chart Widget.

Provides methods to display tradingbot signals, stop-loss lines,
and debug information on the chart.

REFACTORED: Data types extracted to bot_overlay_types.py
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable

from .bot_overlay_types import (
    BotMarker,
    BotOverlayState,
    MarkerType,
    RegimeLine,
    StopLine,
    build_hud_content,
)
from .data_loading_mixin import get_local_timezone_offset_seconds

# Re-export for backward compatibility
__all__ = [
    "MarkerType",
    "BotMarker",
    "StopLine",
    "BotOverlayState",
    "BotOverlayMixin",
]

if TYPE_CHECKING:
    from src.core.tradingbot.models import PositionState, Signal

logger = logging.getLogger(__name__)


class BotOverlayMixin:
    """Mixin providing bot overlay functionality for chart widgets.

    Requires the chart widget to have:
    - _execute_js(script: str) method
    - page_loaded and chart_initialized flags
    """

    def _init_bot_overlay(self) -> None:
        """Initialize bot overlay state."""
        self._bot_overlay_state = BotOverlayState()
        self._bot_overlay_callbacks: dict[str, Callable] = {}
        logger.info("Bot overlay initialized")

    # ==================== TIMESTAMP UTILITIES ====================

    def _get_timeframe_seconds(self) -> int:
        """Get current chart timeframe in seconds.

        Converts current_timeframe string ('1m', '5m', '1h', etc.) to seconds.
        Falls back to 60 seconds (1 minute) if not set or unrecognized.

        Returns:
            Timeframe duration in seconds

        Examples:
            '1m' -> 60
            '5m' -> 300
            '1h' -> 3600
            '4h' -> 14400
        """
        # Try explicit _current_timeframe_seconds first
        if hasattr(self, '_current_timeframe_seconds') and self._current_timeframe_seconds:
            return self._current_timeframe_seconds

        # Get current timeframe string from parent chart
        timeframe_str = getattr(self.parent, 'current_timeframe', '1m')

        # Mapping of timeframe strings to seconds
        timeframe_mapping = {
            '1S': 1,      # 1 second
            '1m': 60,     # 1 minute
            '5m': 300,    # 5 minutes
            '15m': 900,   # 15 minutes
            '30m': 1800,  # 30 minutes
            '1h': 3600,   # 1 hour
            '1H': 3600,   # 1 hour (alternative)
            '2h': 7200,   # 2 hours
            '4h': 14400,  # 4 hours
            '4H': 14400,  # 4 hours (alternative)
            '1d': 86400,  # 1 day
            '1D': 86400,  # 1 day (alternative)
            '1w': 604800, # 1 week
            '1W': 604800, # 1 week (alternative)
        }

        return timeframe_mapping.get(timeframe_str, 60)

    def _snap_to_candle_boundary(self, timestamp: int, timeframe_seconds: int = 60) -> int:
        """Snap timestamp to the previous candle boundary.

        This ensures markers align exactly with candle timestamps,
        preventing jumps when new candles appear.

        Args:
            timestamp: Unix timestamp in seconds
            timeframe_seconds: Candle duration in seconds (default: 60 for 1 minute)

        Returns:
            Timestamp snapped to the previous candle boundary

        Example:
            timestamp = 1704067245 (10:30:45)
            timeframe_seconds = 60 (1 minute)
            returns 1704067200 (10:30:00)
        """
        # Validate timeframe_seconds to prevent division by zero
        if timeframe_seconds <= 0:
            logger.warning(f"Invalid timeframe {timeframe_seconds}s, defaulting to 60s")
            timeframe_seconds = 60

        return (timestamp // timeframe_seconds) * timeframe_seconds

    # ==================== MARKERS ====================

    def add_bot_marker(
        self,
        timestamp: datetime | int,
        price: float,
        marker_type: MarkerType,
        side: str,
        text: str = "",
        score: float = 0.0
    ) -> None:
        """Add a bot marker to the chart.

        Issue #13: Prevents duplicate markers at the same timestamp/price/type.

        Args:
            timestamp: Bar timestamp (datetime or Unix timestamp)
            price: Price level for marker
            marker_type: Type of marker
            side: "long" or "short"
            text: Optional text to display
            score: Optional score value
        """
        # Convert timestamp to Unix seconds (NO timezone offset)
        # Chart candles use raw Unix timestamps from DataFrame index.timestamp()
        # which already returns correct UTC values - NO offset adjustment needed!
        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            ts = int(timestamp.timestamp())
        else:
            ts = timestamp

        # Get current timeframe in seconds from chart
        # This ensures markers snap to the correct candle boundary for all timeframes
        timeframe_seconds = self._get_timeframe_seconds()

        # Snap to candle boundary to ensure marker stays fixed
        # This prevents markers from jumping when new candles appear
        ts = self._snap_to_candle_boundary(ts, timeframe_seconds)

        # Issue #13: Check for duplicate markers (same timestamp, type, and side)
        # This prevents markers from being drawn multiple times on chart refresh
        for existing in self._bot_overlay_state.markers:
            if (existing.timestamp == ts and
                existing.marker_type == marker_type and
                existing.side == side):
                # Allow price tolerance of 0.01% for floating point comparison
                price_tolerance = price * 0.0001 if price > 0 else 0.01
                if abs(existing.price - price) < price_tolerance:
                    logger.debug(
                        f"Skipping duplicate marker: {marker_type.value} at {ts} "
                        f"(already exists at price {existing.price:.4f})"
                    )
                    return

        marker = BotMarker(
            timestamp=ts,
            price=price,
            marker_type=marker_type,
            side=side,
            text=text,
            score=score
        )
        self._bot_overlay_state.markers.append(marker)
        self._update_chart_markers()
        logger.debug(f"Added bot marker: {marker_type.value} at {ts}")

    def add_entry_candidate(
        self,
        timestamp: datetime | int,
        price: float,
        side: str,
        score: float
    ) -> None:
        """Add entry candidate marker.

        Args:
            timestamp: Bar timestamp
            price: Entry price
            side: "long" or "short"
            score: Entry score (0-100)
        """
        # Show score and price in marker text
        text = f"C:{score:.0f} @{price:.2f}"
        self.add_bot_marker(
            timestamp, price, MarkerType.ENTRY_CANDIDATE,
            side, text, score
        )

    def add_entry_confirmed(
        self,
        timestamp: datetime | int,
        price: float,
        side: str,
        score: float
    ) -> None:
        """Add confirmed entry marker.

        Args:
            timestamp: Bar timestamp
            price: Entry price
            side: "long" or "short"
            score: Entry score
        """
        # Show score and price in marker text
        text = f"E:{score:.0f} @{price:.2f}"
        self.add_bot_marker(
            timestamp, price, MarkerType.ENTRY_CONFIRMED,
            side, text, score
        )

    def add_exit_marker(
        self,
        timestamp: datetime | int,
        price: float,
        side: str,
        reason: str
    ) -> None:
        """Add exit signal marker.

        Args:
            timestamp: Bar timestamp
            price: Exit price
            side: Original position side
            reason: Exit reason code
        """
        text = reason[:10]  # Truncate reason
        self.add_bot_marker(
            timestamp, price, MarkerType.EXIT_SIGNAL,
            side, text
        )

    def add_stop_triggered_marker(
        self,
        timestamp: datetime | int,
        price: float,
        side: str
    ) -> None:
        """Add stop-triggered marker.

        Args:
            timestamp: Bar timestamp
            price: Stop price
            side: Position side
        """
        self.add_bot_marker(
            timestamp, price, MarkerType.STOP_TRIGGERED,
            side, "STOP"
        )

    def add_macd_marker(
        self,
        timestamp: datetime | int,
        price: float,
        is_bearish: bool
    ) -> None:
        """Add MACD cross marker (info only, no exit triggered).

        Args:
            timestamp: Bar timestamp
            price: Current price
            is_bearish: True for bearish cross, False for bullish
        """
        marker_type = MarkerType.MACD_BEARISH if is_bearish else MarkerType.MACD_BULLISH
        text = "MACD↓" if is_bearish else "MACD↑"
        # Use "macd" as side since it's not position-related
        side = "macd"
        self.add_bot_marker(
            timestamp, price, marker_type,
            side, text
        )
        logger.info(f"Added MACD marker: {'bearish' if is_bearish else 'bullish'} @ {price:.2f}")

    def clear_bot_markers(self) -> None:
        """Clear all bot markers from chart."""
        self._bot_overlay_state.markers.clear()
        self._execute_js("window.chartAPI?.clearMarkers();")
        logger.debug("Cleared all bot markers")

    def _update_chart_markers(self) -> None:
        """Update chart with current markers."""
        if not self._bot_overlay_state.markers:
            logger.debug("No markers to update")
            return

        # Sort markers by time
        sorted_markers = sorted(
            self._bot_overlay_state.markers,
            key=lambda m: m.timestamp
        )

        # Convert to chart format
        chart_markers = [m.to_chart_marker() for m in sorted_markers]
        markers_json = json.dumps(chart_markers)

        logger.info(f"Updating chart with {len(chart_markers)} markers: {chart_markers}")

        try:
            self._execute_js(f"window.chartAPI?.addTradeMarkers({markers_json});")
            logger.info(f"Sent {len(chart_markers)} markers to chart")
        except Exception as e:
            logger.error(f"Failed to send markers to chart: {e}", exc_info=True)

    # ==================== STOP LINES ====================

    def add_stop_line(
        self,
        line_id: str,
        price: float,
        line_type: str = "trailing",
        color: str | None = None,
        label: str = ""
    ) -> None:
        """Add or update a stop-loss line on the chart.

        Args:
            line_id: Unique identifier for the line
            price: Stop price level
            line_type: "initial", "trailing", or "target"
            color: Line color (auto-selected if None)
            label: Optional label text
        """
        if color is None:
            if line_type == "initial":
                color = "#ef5350"  # Red for initial stop
            elif line_type == "trailing":
                color = "#ff9800"  # Orange for trailing
            else:
                color = "#4caf50"  # Green for target

        # Line style - all solid for better visibility
        line_style = "solid"

        # Remove existing line if updating
        if line_id in self._bot_overlay_state.stop_lines:
            self._remove_chart_line(line_id)

        # Create label with price
        display_label = label or f"SL @ {price:.2f}"

        stop_line = StopLine(
            line_id=line_id,
            price=price,
            color=color,
            line_type=line_type,
            label=display_label
        )
        self._bot_overlay_state.stop_lines[line_id] = stop_line

        # Add to chart with label, style and custom ID for later updates
        self._execute_js(
            f"window.chartAPI?.addHorizontalLine({price}, '{color}', '{display_label}', '{line_style}', '{line_id}');"
        )
        logger.info(f"Added stop line: {line_id} at {price} ({display_label})")

    def update_stop_line(self, line_id: str, new_price: float, label: str | None = None) -> bool:
        """Update an existing stop line.

        Args:
            line_id: Line identifier
            new_price: New price level
            label: Optional custom label (if None, uses default format)

        Returns:
            True if updated, False if line not found
        """
        if line_id not in self._bot_overlay_state.stop_lines:
            logger.warning(f"Stop line not found: {line_id}")
            return False

        stop_line = self._bot_overlay_state.stop_lines[line_id]

        # Update price and label
        stop_line.price = new_price
        if label is not None:
            stop_line.label = label
        else:
            stop_line.label = f"SL @ {new_price:.2f}"

        # Line style - all solid for better visibility
        line_style = "solid"

        # Add with custom ID - JavaScript will remove existing line with same ID
        self._execute_js(
            f"window.chartAPI?.addHorizontalLine({new_price}, '{stop_line.color}', '{stop_line.label}', '{line_style}', '{line_id}');"
        )
        logger.info(f"Updated stop line: {line_id} to {new_price}")
        return True

    def remove_stop_line(self, line_id: str) -> bool:
        """Remove a stop line from the chart.

        Args:
            line_id: Line identifier

        Returns:
            True if removed, False if not found
        """
        if line_id not in self._bot_overlay_state.stop_lines:
            return False

        self._remove_chart_line(line_id)
        del self._bot_overlay_state.stop_lines[line_id]
        logger.debug(f"Removed stop line: {line_id}")
        return True

    def clear_stop_lines(self) -> None:
        """Clear all stop lines from chart."""
        for line_id in list(self._bot_overlay_state.stop_lines.keys()):
            self._remove_chart_line(line_id)
        self._bot_overlay_state.stop_lines.clear()
        logger.debug("Cleared all stop lines")

    def _remove_chart_line(self, line_id: str) -> None:
        """Remove a line from the chart by ID."""
        # Note: The chart API stores line IDs internally
        self._execute_js(f"window.chartAPI?.removeDrawingById('{line_id}');")

    # ==================== REGIME LINES ====================

    def add_regime_line(
        self,
        line_id: str,
        timestamp: datetime | int,
        regime_name: str,
        color: str | None = None,
        label: str = ""
    ) -> None:
        """Add a vertical regime boundary line on the chart.

        Args:
            line_id: Unique identifier for the line
            timestamp: Regime change timestamp
            regime_name: Regime name (e.g., "TREND_UP", "RANGE")
            color: Line color (auto-selected if None)
            label: Optional label text
        """
        print(f"[BOT_OVERLAY] add_regime_line called: id={line_id}, ts={timestamp}, regime={regime_name}, label={label}", flush=True)

        # Convert timestamp to Unix timestamp and apply local timezone offset
        # Issue #56: Must match chart candle times which use UTC + local_offset
        local_offset = get_local_timezone_offset_seconds()

        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                from datetime import timezone
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            ts = int(timestamp.timestamp()) + local_offset
        else:
            ts = timestamp + local_offset

        print(f"[BOT_OVERLAY] Converted timestamp to: {ts} (with offset: {local_offset})", flush=True)

        # Auto-select color based on regime name ONLY if not provided
        if color is None:
            if "BULL" in regime_name.upper() or "TREND_UP" in regime_name.upper():
                color = "#26a69a"  # Green for trend up
            elif "BEAR" in regime_name.upper() or "TREND_DOWN" in regime_name.upper():
                color = "#ef5350"  # Red for trend down
            elif "OVERBOUGHT" in regime_name.upper():
                color = "#ffa726"  # Orange for overbought
            elif "OVERSOLD" in regime_name.upper():
                color = "#42a5f5"  # Blue for oversold
            elif "RANGE" in regime_name.upper() or "SIDEWAYS" in regime_name.upper():
                color = "#9e9e9e"  # Grey for range
            else:
                color = "#bdbdbd"  # Light grey for unknown
            logger.debug(f"Auto-selected color {color} for regime {regime_name}")

        # Remove existing line if updating
        if line_id in self._bot_overlay_state.regime_lines:
            self._remove_chart_regime_line(line_id)

        # Create label
        display_label = label or regime_name

        regime_line = RegimeLine(
            line_id=line_id,
            timestamp=ts,
            color=color,
            regime_name=regime_name,
            label=display_label
        )
        self._bot_overlay_state.regime_lines[line_id] = regime_line

        # Add vertical line to chart
        # Note: Assuming chartAPI has addVerticalLine similar to addHorizontalLine
        js_code = f"window.chartAPI?.addVerticalLine({ts}, '{color}', '{display_label}', 'solid', '{line_id}');"
        print(f"[BOT_OVERLAY] Executing JS: {js_code}", flush=True)
        self._execute_js(js_code)
        print(f"[BOT_OVERLAY] ✅ JS executed for regime line {line_id}", flush=True)
        logger.info(f"Added regime line: {line_id} at {ts} with color {color} ({display_label})")

    def clear_regime_lines(self) -> None:
        """Clear all regime lines from chart."""
        # Use the prefix-based removal to catch all lines, even those not in state
        # (e.g. lines restored by chart persistence but not in python state)
        self._execute_js("window.chartAPI?.removeDrawingsByPrefix('regime_');")

        # Also clear local state
        self._bot_overlay_state.regime_lines.clear()
        logger.debug("Cleared all regime lines")

    def _remove_chart_regime_line(self, line_id: str) -> None:
        """Remove a regime line from the chart by ID."""
        self._execute_js(f"window.chartAPI?.removeDrawingById('{line_id}');")

    # ==================== DEBUG HUD ====================

    def set_debug_hud_visible(self, visible: bool) -> None:
        """Set debug HUD visibility.

        Args:
            visible: Whether to show debug HUD
        """
        self._bot_overlay_state.debug_hud_visible = visible
        if visible:
            self._update_debug_hud()
        else:
            self._execute_js(
                "document.getElementById('bot-debug-hud')?.remove();"
            )

    def update_debug_info(
        self,
        regime: str = "",
        strategy: str = "",
        ki_mode: str = "",
        trailing_mode: str = "",
        confidence: float = 0.0,
        state: str = "",
        extra: dict[str, Any] | None = None
    ) -> None:
        """Update debug HUD information.

        Args:
            regime: Current regime (e.g., "TREND_UP")
            strategy: Active strategy name
            ki_mode: KI mode (NO_KI, LOW_KI, FULL_KI)
            trailing_mode: Trailing stop mode
            confidence: Decision confidence (0-1)
            state: Bot state (FLAT, SIGNAL, etc.)
            extra: Additional key-value pairs
        """
        self._bot_overlay_state.last_regime = regime
        self._bot_overlay_state.last_strategy = strategy
        self._bot_overlay_state.last_ki_mode = ki_mode

        if self._bot_overlay_state.debug_hud_visible:
            self._update_debug_hud(
                regime=regime,
                strategy=strategy,
                ki_mode=ki_mode,
                trailing_mode=trailing_mode,
                confidence=confidence,
                state=state,
                extra=extra
            )

    def _update_debug_hud(
        self,
        regime: str = "",
        strategy: str = "",
        ki_mode: str = "",
        trailing_mode: str = "",
        confidence: float = 0.0,
        state: str = "",
        extra: dict[str, Any] | None = None
    ) -> None:
        """Update the debug HUD on chart."""
        content = build_hud_content(state, regime, strategy, trailing_mode, ki_mode, confidence, extra)
        # Create/update HUD element via JavaScript
        hud_js = f"""
        (function() {{
            let hud = document.getElementById('bot-debug-hud');
            if (!hud) {{
                hud = document.createElement('div');
                hud.id = 'bot-debug-hud';
                hud.style.cssText = `
                    position: absolute;
                    top: 35px;
                    right: 10px;
                    background: rgba(0,0,0,0.75);
                    color: #fff;
                    font-family: monospace;
                    font-size: 11px;
                    padding: 5px 10px;
                    border-radius: 4px;
                    z-index: 1000;
                    pointer-events: none;
                `;
                document.getElementById('chart-container').appendChild(hud);
            }}
            hud.innerHTML = `{content}`;
        }})();
        """
        self._execute_js(hud_js)

    # ==================== POSITION DISPLAY ====================

    def display_position(self, position: PositionState) -> None:
        """Display position information on chart.

        Args:
            position: Current position state
        """
        # Clear existing position markers
        self.remove_stop_line("pos_entry")
        self.remove_stop_line("initial_stop")
        self.remove_stop_line("trailing_stop")

        # If position is None, just return after clearing
        if position is None:
            return

        side = position.side.value if hasattr(position.side, 'value') else str(position.side)

        # Entry line (blue, solid)
        self.add_stop_line(
            "pos_entry",
            position.entry_price,
            line_type="initial",
            color="#2196f3",  # Blue
            label=f"Entry @ {position.entry_price:.4f}"
        )

        # Initial stop loss line (red, solid)
        if position.trailing and position.trailing.initial_stop_price:
            initial_stop = position.trailing.initial_stop_price
            self.add_stop_line(
                "initial_stop",
                initial_stop,
                line_type="initial",
                color="#ef5350",  # Red for initial stop loss
                label=f"Initial SL @ {initial_stop:.4f}"
            )

            # Trailing stop (orange, solid) - only if different from initial
            current_stop = position.trailing.current_stop_price
            if abs(current_stop - initial_stop) > 0.0001:
                self.add_stop_line(
                    "trailing_stop",
                    current_stop,
                    line_type="trailing",
                    color="#ff9800",  # Orange for trailing stop
                    label=f"Trailing SL @ {current_stop:.4f}"
                )

    def clear_position_display(self) -> None:
        """Clear position display elements."""
        self.remove_stop_line("pos_entry")
        self.remove_stop_line("initial_stop")
        self.remove_stop_line("trailing_stop")

    # ==================== SIGNAL DISPLAY ====================

    def display_signal(self, signal: Signal) -> None:
        """Display a signal on the chart.

        Args:
            signal: Signal to display
        """
        from src.core.tradingbot.models import SignalType

        try:
            ts = signal.timestamp
            if isinstance(ts, datetime):
                ts_int = int(ts.timestamp())
            else:
                ts_int = int(ts)

            side = signal.side.value if hasattr(signal.side, 'value') else str(signal.side)
            signal_type = signal.signal_type if hasattr(signal, 'signal_type') else SignalType.CONFIRMED

            logger.info(
                f"Displaying signal: {signal_type.value if hasattr(signal_type, 'value') else signal_type} "
                f"{side} @ {signal.entry_price:.4f} (ts={ts_int})"
            )

            if signal_type == SignalType.CANDIDATE:
                self.add_entry_candidate(ts_int, signal.entry_price, side, signal.score)
            else:
                self.add_entry_confirmed(ts_int, signal.entry_price, side, signal.score)

            # Add stop-loss line for signal
            if signal.stop_loss_price:
                self.add_stop_line(
                    f"signal_{signal.id}",
                    signal.stop_loss_price,
                    line_type="initial",
                    label=f"Signal SL @ {signal.stop_loss_price:.4f}"
                )
                logger.debug(f"Added stop-loss line at {signal.stop_loss_price:.4f}")

        except Exception as e:
            logger.error(f"Error displaying signal: {e}", exc_info=True)
            raise

    def clear_signal_display(self, signal_id: str | None = None) -> None:
        """Clear signal display.

        Args:
            signal_id: Specific signal to clear, or None for all
        """
        if signal_id:
            self.remove_stop_line(f"signal_{signal_id}")
        else:
            # Clear all signal lines
            to_remove = [
                lid for lid in self._bot_overlay_state.stop_lines
                if lid.startswith("signal_")
            ]
            for lid in to_remove:
                self.remove_stop_line(lid)

    # ==================== CLEANUP ====================

    def clear_bot_overlay(self) -> None:
        """Clear all bot overlay elements."""
        self.clear_bot_markers()
        self.clear_stop_lines()
        self.set_debug_hud_visible(False)
        logger.info("Cleared all bot overlay elements")

    def restore_state_from_dict(self, state_dict: dict) -> None:
        """Restore bot overlay state from chart state dictionary.

        This allows restoring regime lines and other overlays that were
        persisted in the chart's state but lost from Python memory.

        Args:
            state_dict: Complete chart state dictionary from QSettings
        """
        if not state_dict or 'drawings' not in state_dict:
            return

        drawings = state_dict.get('drawings', [])
        restored_count = 0

        for drawing in drawings:
            drawing_id = drawing.get('id', '')
            drawing_type = drawing.get('type', '')

            # Restore Regime Lines
            if drawing_type == 'vline' and drawing_id.startswith('regime_'):
                timestamp = drawing.get('timestamp', 0)
                color = drawing.get('color')
                label = drawing.get('label', '')

                # Try to extract pure regime name from label "NAME (SCORE)"
                # e.g. "STRONG TREND BULL (95.0)" -> "STRONG_TREND_BULL"
                regime_name = label.split(' (')[0].replace(' ', '_')

                # Fallback if label is empty or different format
                if not regime_name:
                    regime_name = "UNKNOWN"

                regime_line = RegimeLine(
                    line_id=drawing_id,
                    timestamp=timestamp,
                    color=color,
                    regime_name=regime_name,
                    label=label
                )
                self._bot_overlay_state.regime_lines[drawing_id] = regime_line
                restored_count += 1
                logger.debug(f"Restored regime line: {regime_name} (ID: {drawing_id})")

        if restored_count > 0:
            logger.info(f"Restored {restored_count} regime lines from saved chart state")
            # If we have an EntryAnalyzerMixin, update its data too
            if hasattr(self, '_reconstruct_regime_data_from_chart'):
                # This will use the populated _bot_overlay_state to fill _current_regime_data
                self._reconstruct_regime_data_from_chart()

