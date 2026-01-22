"""Bot Overlay Types for Chart Widget.

Contains data classes and enums for bot overlay display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MarkerType(str, Enum):
    """Marker types for chart display."""
    ENTRY_CANDIDATE = "entry_candidate"
    ENTRY_CONFIRMED = "entry_confirmed"
    EXIT_SIGNAL = "exit_signal"
    STOP_TRIGGERED = "stop_triggered"
    TRAILING_UPDATE = "trailing_update"
    MACD_BEARISH = "macd_bearish"
    MACD_BULLISH = "macd_bullish"
    REGIME_BULL = "regime_bull"  # Bullish regime start
    REGIME_BEAR = "regime_bear"  # Bearish regime start


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
        elif self.marker_type == MarkerType.REGIME_BULL:
            shape = "arrowUp"
            color = "#4caf50"  # Green for bullish regime
            position = "belowBar"
        elif self.marker_type == MarkerType.REGIME_BEAR:
            shape = "arrowDown"
            color = "#f44336"  # Red for bearish regime
            position = "aboveBar"
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
class RegimeLine:
    """Regime boundary line data."""
    line_id: str
    timestamp: int  # Unix timestamp
    color: str
    regime_name: str
    label: str = ""


@dataclass
class BotOverlayState:
    """State tracking for bot overlay elements."""
    markers: list[BotMarker] = field(default_factory=list)
    stop_lines: dict[str, StopLine] = field(default_factory=dict)
    regime_lines: dict[str, RegimeLine] = field(default_factory=dict)
    debug_hud_visible: bool = False
    last_regime: str = ""
    last_strategy: str = ""
    last_ki_mode: str = ""


# Color mappings for HUD display
STATE_COLORS = {
    "FLAT": "#607d8b", "SIGNAL": "#ffeb3b", "ENTERED": "#26a69a",
    "MANAGE": "#2196f3", "EXITED": "#9c27b0", "PAUSED": "#ff9800", "ERROR": "#f44336"
}


def build_hud_content(
    state: str = "", regime: str = "", strategy: str = "",
    trailing_mode: str = "", ki_mode: str = "", confidence: float = 0.0,
    extra: dict[str, Any] | None = None
) -> str:
    """Build HTML content for debug HUD."""
    lines = []
    if state:
        state_color = STATE_COLORS.get(state, "#ffffff")
        lines.append(f"<span style='color:{state_color}'>{state}</span>")
    if regime:
        regime_color = "#26a69a" if "UP" in regime else ("#ef5350" if "DOWN" in regime else "#9e9e9e")
        lines.append(f"R:<span style='color:{regime_color}'>{regime}</span>")
    if strategy:
        lines.append(f"S:{strategy[:15]}")
    if trailing_mode:
        lines.append(f"T:{trailing_mode}")
    if ki_mode:
        ki_color = "#4caf50" if ki_mode == "NO_KI" else ("#ff9800" if ki_mode == "LOW_KI" else "#f44336")
        lines.append(f"KI:<span style='color:{ki_color}'>{ki_mode}</span>")
    if confidence > 0:
        lines.append(f"C:{int(confidence * 100)}%")
    if extra:
        for key, value in extra.items():
            lines.append(f"{key}:{value}")
    return " | ".join(lines)
