"""Bot Overlay Mixin for Chart Widget.

Provides methods to display tradingbot signals, stop-loss lines,
and debug information on the chart.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from .data_loading_mixin import get_local_timezone_offset_seconds

if TYPE_CHECKING:
    from src.core.tradingbot.models import PositionState, Signal

logger = logging.getLogger(__name__)


class MarkerType(str, Enum):
    """Marker types for chart display."""
    ENTRY_CANDIDATE = "entry_candidate"
    ENTRY_CONFIRMED = "entry_confirmed"
    EXIT_SIGNAL = "exit_signal"
    STOP_TRIGGERED = "stop_triggered"
    TRAILING_UPDATE = "trailing_update"
    MACD_BEARISH = "macd_bearish"
    MACD_BULLISH = "macd_bullish"


@dataclass
class BotMarker:
    """Marker data for chart display."""
    timestamp: int  # Unix timestamp
    price: float
    marker_type: MarkerType
    side: str  # "long" or "short"
    text: str = ""
    score: float = 0.0

    def to_chart_marker(self) -> dict[str, Any]:
        """Convert to Lightweight Charts marker format."""
        # Marker shapes: arrowUp, arrowDown, circle, square
        # Colors based on type and side
        if self.marker_type == MarkerType.ENTRY_CANDIDATE:
            shape = "circle"
            color = "#ffeb3b" if self.side == "long" else "#ff9800"  # Yellow/orange
            position = "belowBar" if self.side == "long" else "aboveBar"
        elif self.marker_type == MarkerType.ENTRY_CONFIRMED:
            shape = "arrowUp" if self.side == "long" else "arrowDown"
            color = "#26a69a" if self.side == "long" else "#ef5350"  # Green/red
            position = "belowBar" if self.side == "long" else "aboveBar"
        elif self.marker_type == MarkerType.EXIT_SIGNAL:
            shape = "square"
            color = "#9c27b0"  # Purple
            position = "aboveBar" if self.side == "long" else "belowBar"
        elif self.marker_type == MarkerType.STOP_TRIGGERED:
            shape = "circle"
            color = "#f44336"  # Red
            position = "aboveBar" if self.side == "long" else "belowBar"
        elif self.marker_type == MarkerType.MACD_BEARISH:
            shape = "arrowDown"
            color = "#e91e63"  # Pink/Magenta for bearish MACD
            position = "aboveBar"
        elif self.marker_type == MarkerType.MACD_BULLISH:
            shape = "arrowUp"
            color = "#00bcd4"  # Cyan for bullish MACD
            position = "belowBar"
        else:
            shape = "circle"
            color = "#607d8b"  # Grey
            position = "belowBar"

        return {
            "time": self.timestamp,
            "position": position,
            "color": color,
            "shape": shape,
            "text": self.text or f"{self.marker_type.value}",
            "size": 2
        }


@dataclass
class StopLine:
    """Stop-loss line data."""
    line_id: str
    price: float
    color: str
    line_type: str  # "initial", "trailing", "target"
    is_active: bool = True
    label: str = ""


@dataclass
class BotOverlayState:
    """State tracking for bot overlay elements."""
    markers: list[BotMarker] = field(default_factory=list)
    stop_lines: dict[str, StopLine] = field(default_factory=dict)
    debug_hud_visible: bool = False
    last_regime: str = ""
    last_strategy: str = ""
    last_ki_mode: str = ""


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

        Args:
            timestamp: Bar timestamp (datetime or Unix timestamp)
            price: Price level for marker
            marker_type: Type of marker
            side: "long" or "short"
            text: Optional text to display
            score: Optional score value
        """
        # Convert to Unix timestamp and add local timezone offset
        # to match chart data which is also shifted to local time
        local_offset = get_local_timezone_offset_seconds()
        if isinstance(timestamp, datetime):
            ts = int(timestamp.timestamp()) + local_offset
        else:
            ts = timestamp + local_offset

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

        # Add to chart with label and style
        self._execute_js(
            f"window.chartAPI?.addHorizontalLine({price}, '{color}', '{display_label}', '{line_style}');"
        )
        logger.info(f"Added stop line: {line_id} at {price} ({display_label})")

    def update_stop_line(self, line_id: str, new_price: float) -> bool:
        """Update an existing stop line.

        Args:
            line_id: Line identifier
            new_price: New price level

        Returns:
            True if updated, False if line not found
        """
        if line_id not in self._bot_overlay_state.stop_lines:
            logger.warning(f"Stop line not found: {line_id}")
            return False

        stop_line = self._bot_overlay_state.stop_lines[line_id]

        # Remove old line
        self._remove_chart_line(line_id)

        # Update price and label
        stop_line.price = new_price
        stop_line.label = f"SL @ {new_price:.2f}"

        # Line style - all solid for better visibility
        line_style = "solid"

        self._execute_js(
            f"window.chartAPI?.addHorizontalLine({new_price}, '{stop_line.color}', '{stop_line.label}', '{line_style}');"
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
        # Build HUD content
        lines = []
        if state:
            state_color = {
                "FLAT": "#607d8b",
                "SIGNAL": "#ffeb3b",
                "ENTERED": "#26a69a",
                "MANAGE": "#2196f3",
                "EXITED": "#9c27b0",
                "PAUSED": "#ff9800",
                "ERROR": "#f44336"
            }.get(state, "#ffffff")
            lines.append(f"<span style='color:{state_color}'>{state}</span>")

        if regime:
            regime_color = "#26a69a" if "UP" in regime else (
                "#ef5350" if "DOWN" in regime else "#9e9e9e"
            )
            lines.append(f"R:<span style='color:{regime_color}'>{regime}</span>")

        if strategy:
            lines.append(f"S:{strategy[:15]}")

        if trailing_mode:
            lines.append(f"T:{trailing_mode}")

        if ki_mode:
            ki_color = "#4caf50" if ki_mode == "NO_KI" else (
                "#ff9800" if ki_mode == "LOW_KI" else "#f44336"
            )
            lines.append(f"KI:<span style='color:{ki_color}'>{ki_mode}</span>")

        if confidence > 0:
            conf_pct = int(confidence * 100)
            lines.append(f"C:{conf_pct}%")

        if extra:
            for key, value in extra.items():
                lines.append(f"{key}:{value}")

        content = " | ".join(lines)

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
