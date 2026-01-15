"""Level Zones Rendering - Level detection, zone conversion, and rendering.

Refactored from 722 LOC monolith using composition pattern.

Module 3/5 of level_zones_mixin.py split.

Contains:
- detect_and_render_levels(): Detect levels from DataFrame and render
- set_levels_result(): Set levels result directly
- render_level_zones(): Render all levels as zones
- level_to_zone(): Convert Level to Zone
- render_zone_on_chart(): Render zone via JavaScript
- Helper methods: get_chart_time_range, show/hide/clear/refresh zones
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from src.ui.widgets.chart_mixins.level_zones_colors import LEVEL_ZONE_COLORS

if TYPE_CHECKING:
    import pandas as pd
    from src.core.trading_bot.level_engine import Level, LevelsResult

logger = logging.getLogger(__name__)


class LevelZonesRendering:
    """Helper für Level Zones Rendering (Detection, Conversion, Rendering)."""

    def __init__(self, parent):
        """
        Args:
            parent: LevelZonesMixin Instanz
        """
        self.parent = parent

    def detect_and_render_levels(
        self,
        df: "pd.DataFrame",
        symbol: str = "UNKNOWN",
        timeframe: str = "5m",
        current_price: Optional[float] = None,
    ) -> None:
        """
        Detect levels from DataFrame and render as zones.

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe
            current_price: Current price for classification
        """
        try:
            from src.core.trading_bot.level_engine import get_level_engine

            engine = get_level_engine()
            self.parent._levels_result = engine.detect_levels(df, symbol, timeframe, current_price)

            if self.parent._level_zones_visible:
                self.render_level_zones()

            logger.debug(f"Detected and rendered {len(self.parent._levels_result.levels)} levels")

        except Exception as e:
            logger.error(f"Failed to detect/render levels: {e}", exc_info=True)

    def set_levels_result(self, result: "LevelsResult") -> None:
        """
        Set levels result directly.

        Args:
            result: LevelsResult from LevelEngine
        """
        self.parent._levels_result = result
        if self.parent._level_zones_visible:
            self.render_level_zones()

    def render_level_zones(self) -> None:
        """Render level zones in the chart."""
        if self.parent._levels_result is None:
            return

        # Clear existing level zones
        self.clear_level_zones()

        # Get filter settings
        key_only = getattr(self.parent, "_key_only_action", None)
        key_only = key_only.isChecked() if key_only else False

        # Determine which level types to show
        visible_types = set()
        if hasattr(self.parent, "_level_type_actions"):
            for level_type, action in self.parent._level_type_actions.items():
                if action.isChecked():
                    visible_types.add(level_type)
        else:
            visible_types = {"support", "resistance", "pivot"}

        # Get chart time range
        start_time, end_time = self.get_chart_time_range()

        # Render each level
        for level in self.parent._levels_result.levels:
            # Filter by key levels
            if key_only and level.strength.value != "key":
                continue

            # Filter by level type
            level_type_str = level.level_type.value
            if level_type_str not in visible_types:
                # Check if it's a derived type
                if level_type_str in ("swing_high", "swing_low") and "swing_high" not in visible_types:
                    continue
                if level_type_str in ("daily_high", "daily_low") and "daily_high" not in visible_types:
                    continue

            # Convert to zone and render
            zone_id = self.level_to_zone(level, start_time, end_time)
            if zone_id:
                self.parent._level_zones_ids.append(zone_id)

    def level_to_zone(
        self,
        level: "Level",
        start_time: int,
        end_time: int,
    ) -> Optional[str]:
        """
        Convert a Level to a chart Zone and render it.

        Args:
            level: Level from LevelEngine
            start_time: Zone start time (Unix timestamp)
            end_time: Zone end time (Unix timestamp)

        Returns:
            Zone ID if created, None otherwise
        """
        try:
            from src.chart_marking.models import Zone, ZoneType as ChartZoneType

            # Map level type to zone type
            zone_type_map = {
                "support": ChartZoneType.SUPPORT,
                "resistance": ChartZoneType.RESISTANCE,
                "swing_low": ChartZoneType.SUPPORT,
                "swing_high": ChartZoneType.RESISTANCE,
                "pivot": ChartZoneType.SUPPORT,  # Will be colored differently
                "daily_low": ChartZoneType.SUPPORT,
                "daily_high": ChartZoneType.RESISTANCE,
                "weekly_low": ChartZoneType.SUPPORT,
                "weekly_high": ChartZoneType.RESISTANCE,
            }

            level_type_str = level.level_type.value
            chart_zone_type = zone_type_map.get(level_type_str, ChartZoneType.SUPPORT)

            # Get colors
            color_key = level_type_str
            if level.strength.value == "key":
                color_key = "key"

            fill_template, border_color, opacity = LEVEL_ZONE_COLORS.get(
                color_key,
                LEVEL_ZONE_COLORS["support"]
            )

            # Increase opacity for stronger levels
            if level.strength.value == "strong":
                opacity = min(opacity * 1.3, 0.5)
            elif level.strength.value == "key":
                opacity = min(opacity * 1.5, 0.6)

            fill_color = fill_template.format(opacity=opacity)

            # Create zone ID
            zone_id = f"level_{level.id}"

            # Create label
            label_parts = []
            if level.label:
                label_parts.append(level.label)
            else:
                label_parts.append(level_type_str.replace("_", " ").title())

            if level.strength.value in ("strong", "key"):
                label_parts.append(f"({level.strength.value.upper()})")

            label = " ".join(label_parts)

            # Create and add zone
            zone = Zone(
                id=zone_id,
                zone_type=chart_zone_type,
                start_time=start_time,
                end_time=end_time,
                top_price=level.price_high,
                bottom_price=level.price_low,
                color=fill_color,
                opacity=opacity,
                label=label,
                is_active=True,
                is_locked=True,  # Automatically generated, so locked
            )

            # Add to chart using existing zones system
            if hasattr(self.parent, "_zones") and hasattr(self.parent._zones, "add"):
                self.parent._zones.add(zone)
                self.render_zone_on_chart(zone)
                # Register for click detection (Phase 5.7)
                self.parent._interactions.register_zone_for_click(zone_id, level.price_high, level.price_low, label)
                return zone_id
            elif hasattr(self.parent, "add_zone"):
                self.parent.add_zone(
                    start_time=start_time,
                    end_time=end_time,
                    top_price=level.price_high,
                    bottom_price=level.price_low,
                    zone_type=chart_zone_type.value,
                    label=label,
                    color=fill_color,
                    zone_id=zone_id,
                )
                # Register for click detection (Phase 5.7)
                self.parent._interactions.register_zone_for_click(zone_id, level.price_high, level.price_low, label)
                return zone_id

            return None

        except Exception as e:
            logger.error(f"Failed to convert level to zone: {e}")
            return None

    def render_zone_on_chart(self, zone) -> None:
        """Render zone on JavaScript chart."""
        try:
            # Use existing zone rendering if available
            if hasattr(self.parent, "_run_js") and hasattr(self.parent, "web_view"):
                js = f"""
                    if (typeof addZone === 'function') {{
                        addZone({{
                            id: "{zone.id}",
                            startTime: {zone.start_time if isinstance(zone.start_time, int) else int(zone.start_time.timestamp())},
                            endTime: {zone.end_time if isinstance(zone.end_time, int) else int(zone.end_time.timestamp())},
                            topPrice: {zone.top_price},
                            bottomPrice: {zone.bottom_price},
                            fillColor: "{zone.fill_color}",
                            borderColor: "{zone.border_color}",
                            label: "{zone.label}"
                        }});
                    }}
                """
                self.parent._run_js(js)
        except Exception as e:
            logger.error(f"Failed to render zone on chart: {e}")

    def get_chart_time_range(self) -> tuple[int, int]:
        """
        Get current chart time range.

        Returns:
            Tuple of (start_time, end_time) as Unix timestamps
        """
        now = int(datetime.now(timezone.utc).timestamp())

        # Try to get from DataFrame
        if hasattr(self.parent, "_current_df") and self.parent._current_df is not None:
            df = self.parent._current_df
            if hasattr(df, "index") and len(df) > 0:
                try:
                    start = int(df.index[0].timestamp()) if hasattr(df.index[0], "timestamp") else now - 86400
                    end = int(df.index[-1].timestamp()) if hasattr(df.index[-1], "timestamp") else now
                    return (start, end)
                except Exception:
                    pass

        # Default: last 24 hours
        return (now - 86400, now)

    def show_level_zones(self) -> None:
        """Show all level zones."""
        self.render_level_zones()

    def hide_level_zones(self) -> None:
        """Hide all level zones (without removing)."""
        # Use JavaScript to hide zones
        for zone_id in self.parent._level_zones_ids:
            try:
                if hasattr(self.parent, "_run_js"):
                    self.parent._run_js(f'if (typeof hideZone === "function") hideZone("{zone_id}");')
            except Exception:
                pass

    def clear_level_zones(self) -> None:
        """Remove all level zones from chart."""
        for zone_id in self.parent._level_zones_ids:
            try:
                # Unregister from click detection (Phase 5.7)
                self.parent._interactions.unregister_zone_from_click(zone_id)

                # Remove from zones manager
                if hasattr(self.parent, "_zones") and hasattr(self.parent._zones, "remove"):
                    self.parent._zones.remove(zone_id)

                # Remove from chart
                if hasattr(self.parent, "_run_js"):
                    self.parent._run_js(f'if (typeof removeZone === "function") removeZone("{zone_id}");')
            except Exception as e:
                logger.debug(f"Failed to remove zone {zone_id}: {e}")

        self.parent._level_zones_ids = []
        logger.debug("Cleared all level zones")

    def refresh_level_zones(self) -> None:
        """Refresh level zones (re-detect and render)."""
        if hasattr(self.parent, "_current_df") and self.parent._current_df is not None:
            symbol = getattr(self.parent, "current_symbol", "UNKNOWN")
            timeframe = getattr(self.parent, "current_timeframe", "5m")
            current_price = None
            if hasattr(self.parent, "_current_df") and len(self.parent._current_df) > 0:
                current_price = float(self.parent._current_df["close"].iloc[-1])

            self.detect_and_render_levels(self.parent._current_df, symbol, timeframe, current_price)
        elif self.parent._levels_result:
            self.render_level_zones()
