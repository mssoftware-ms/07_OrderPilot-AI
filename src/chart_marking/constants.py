"""Constants for Chart Marking System.

Defines colors, styles, and default values for all marking types.
"""

from __future__ import annotations


class Colors:
    """Color constants for chart markings."""

    # Entry markers
    LONG_ENTRY = "#00B050"  # Green
    SHORT_ENTRY = "#FF0000"  # Red

    # Structure breaks
    BOS_BULLISH = "#0000FF"  # Blue
    BOS_BEARISH = "#0000FF"  # Blue
    CHOCH_BULLISH = "#FFA500"  # Orange
    CHOCH_BEARISH = "#FFA500"  # Orange
    MSB = "#9C27B0"  # Purple

    # Zones
    SUPPORT_FILL = "rgba(39, 245, 80, 0.3)"
    SUPPORT_BORDER = "#27f550"
    RESISTANCE_FILL = "rgba(245, 39, 39, 0.3)"
    RESISTANCE_BORDER = "#f52727"
    DEMAND_FILL = "rgba(33, 150, 243, 0.3)"
    DEMAND_BORDER = "#2196f3"
    SUPPLY_FILL = "rgba(255, 152, 0, 0.3)"
    SUPPLY_BORDER = "#ff9800"

    # Stop-loss lines
    STOP_LOSS = "#ef5350"  # Red
    TRAILING_STOP = "#ff9800"  # Orange
    TAKE_PROFIT = "#4caf50"  # Green
    ENTRY_LINE = "#2196f3"  # Blue

    # General
    TEXT_LIGHT = "#e0e0e0"
    TEXT_DARK = "#212121"
    BACKGROUND = "#1a1a1a"


class LineStyles:
    """Line style constants."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"

    # JavaScript line style values for Lightweight Charts
    JS_SOLID = 0
    JS_DASHED = 1
    JS_DOTTED = 2


class MarkerSizes:
    """Marker size constants."""

    SMALL = 1
    MEDIUM = 2
    LARGE = 3

    # Default sizes per marker type
    ENTRY_MARKER = 2
    STRUCTURE_BREAK = 2
    EXIT_MARKER = 2


class ZoneDefaults:
    """Default values for zones."""

    OPACITY = 0.3
    BORDER_WIDTH = 1
    MIN_HEIGHT_PERCENT = 0.1  # Minimum 0.1% of price range


class LayoutDefaults:
    """Default values for multi-chart layouts."""

    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    GRID_COLS = 2
    GRID_ROWS = 2


# JavaScript shape mappings for Lightweight Charts
SHAPE_MAP = {
    "arrowUp": "arrowUp",
    "arrowDown": "arrowDown",
    "circle": "circle",
    "square": "square",
    "triangleUp": "triangleUp",
    "triangleDown": "triangleDown",
}

# JavaScript position mappings
POSITION_MAP = {
    "aboveBar": "aboveBar",
    "belowBar": "belowBar",
    "inBar": "inBar",
}
