"""Level Zones Colors - Color definitions for level zones.

Refactored from 722 LOC monolith using composition pattern.

Module 1/5 of level_zones_mixin.py split.

Contains:
- LEVEL_ZONE_COLORS: Mapping of level types to (fill_color, border_color, opacity)
"""

# LEVEL ZONE COLORS
LEVEL_ZONE_COLORS = {
    # Level Type -> (fill_color, border_color, opacity)
    "support": ("rgba(46, 125, 50, {opacity})", "#4CAF50", 0.25),
    "resistance": ("rgba(198, 40, 40, {opacity})", "#F44336", 0.25),
    "swing_high": ("rgba(255, 152, 0, {opacity})", "#FF9800", 0.2),
    "swing_low": ("rgba(33, 150, 243, {opacity})", "#2196F3", 0.2),
    "pivot": ("rgba(156, 39, 176, {opacity})", "#9C27B0", 0.15),
    "daily_high": ("rgba(255, 87, 34, {opacity})", "#FF5722", 0.2),
    "daily_low": ("rgba(0, 150, 136, {opacity})", "#009688", 0.2),
    "weekly_high": ("rgba(233, 30, 99, {opacity})", "#E91E63", 0.25),
    "weekly_low": ("rgba(0, 188, 212, {opacity})", "#00BCD4", 0.25),
    "vwap": ("rgba(103, 58, 183, {opacity})", "#673AB7", 0.15),
    "poc": ("rgba(255, 235, 59, {opacity})", "#FFEB3B", 0.2),
    "key": ("rgba(255, 193, 7, {opacity})", "#FFC107", 0.35),  # Key levels
}
