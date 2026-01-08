"""
Level Zones Mixin for Chart Widgets.

Rendert LevelEngine-Levels als Zonen im Chart.

Phase 2.4 der Bot-Integration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from PyQt6.QtWidgets import QPushButton, QMenu
from PyQt6.QtGui import QAction

if TYPE_CHECKING:
    import pandas as pd
    from src.core.trading_bot.level_engine import Level, LevelsResult

logger = logging.getLogger(__name__)


# =============================================================================
# LEVEL ZONE COLORS
# =============================================================================

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


# =============================================================================
# LEVEL ZONES MIXIN
# =============================================================================


class LevelZonesMixin:
    """
    Mixin für Level-Zonen-Rendering in Chart-Widgets.

    Fügt folgende Funktionalität hinzu:
    - Konvertiert LevelEngine-Levels zu Chart-Zonen
    - Toggle für Level-Anzeige
    - Farblegende
    - Auto-Update bei Datenänderung

    Usage:
        class MyChartWidget(LevelZonesMixin, QWidget):
            def __init__(self):
                super().__init__()
                self._setup_level_zones()
    """

    _level_zones_visible: bool = True
    _level_zones_ids: List[str] = []
    _levels_result: Optional["LevelsResult"] = None

    def _setup_level_zones(self) -> None:
        """
        Setup level zones functionality.

        Should be called after toolbar and zones system are initialized.
        """
        self._level_zones_ids = []
        self._level_zones_visible = True
        self._levels_result = None
        logger.debug("Level zones mixin initialized")

    def _add_levels_toggle_to_toolbar(self, toolbar) -> None:
        """
        Add levels toggle button to toolbar.

        Args:
            toolbar: QToolBar to add button to
        """
        from PyQt6.QtWidgets import QLabel

        toolbar.addWidget(QLabel("Levels:"))

        self._levels_toggle_button = QPushButton("📊 Levels")
        self._levels_toggle_button.setCheckable(True)
        self._levels_toggle_button.setChecked(True)
        self._levels_toggle_button.setToolTip("Support/Resistance Levels anzeigen/verbergen")
        self._levels_toggle_button.clicked.connect(self._on_levels_toggle)
        self._levels_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #4CAF50;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: #000;
            }
        """)

        # Add dropdown menu for level options
        levels_menu = QMenu(self._levels_toggle_button)
        self._build_levels_menu(levels_menu)
        self._levels_toggle_button.setMenu(levels_menu)

        toolbar.addWidget(self._levels_toggle_button)

    def _build_levels_menu(self, menu: QMenu) -> None:
        """Build the levels dropdown menu."""
        # Refresh action
        refresh_action = QAction("🔄 Levels aktualisieren", self)
        refresh_action.triggered.connect(self._refresh_level_zones)
        menu.addAction(refresh_action)

        menu.addSeparator()

        # Level type toggles
        self._level_type_actions = {}
        level_types = [
            ("support", "🟢 Support Levels", True),
            ("resistance", "🔴 Resistance Levels", True),
            ("pivot", "🟣 Pivot Points", True),
            ("swing_high", "🟠 Swing Highs", False),
            ("swing_low", "🔵 Swing Lows", False),
            ("daily_high", "📈 Daily Highs", False),
            ("daily_low", "📉 Daily Lows", False),
        ]

        for level_type, label, default in level_types:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(default)
            action.triggered.connect(lambda checked, lt=level_type: self._on_level_type_toggle(lt, checked))
            menu.addAction(action)
            self._level_type_actions[level_type] = action

        menu.addSeparator()

        # Key levels only
        key_only_action = QAction("⭐ Nur Key Levels", self)
        key_only_action.setCheckable(True)
        key_only_action.triggered.connect(self._on_key_levels_only)
        menu.addAction(key_only_action)
        self._key_only_action = key_only_action

        menu.addSeparator()

        # Clear levels
        clear_action = QAction("🗑️ Levels entfernen", self)
        clear_action.triggered.connect(self._clear_level_zones)
        menu.addAction(clear_action)

    def _on_levels_toggle(self, checked: bool) -> None:
        """Handle levels toggle button click."""
        self._level_zones_visible = checked

        if checked:
            self._show_level_zones()
        else:
            self._hide_level_zones()

        logger.debug(f"Level zones visibility: {checked}")

    def _on_level_type_toggle(self, level_type: str, checked: bool) -> None:
        """Handle level type toggle."""
        self._refresh_level_zones()

    def _on_key_levels_only(self, checked: bool) -> None:
        """Handle key levels only toggle."""
        self._refresh_level_zones()

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
            self._levels_result = engine.detect_levels(df, symbol, timeframe, current_price)

            if self._level_zones_visible:
                self._render_level_zones()

            logger.debug(f"Detected and rendered {len(self._levels_result.levels)} levels")

        except Exception as e:
            logger.error(f"Failed to detect/render levels: {e}", exc_info=True)

    def set_levels_result(self, result: "LevelsResult") -> None:
        """
        Set levels result directly.

        Args:
            result: LevelsResult from LevelEngine
        """
        self._levels_result = result
        if self._level_zones_visible:
            self._render_level_zones()

    def _render_level_zones(self) -> None:
        """Render level zones in the chart."""
        if self._levels_result is None:
            return

        # Clear existing level zones
        self._clear_level_zones()

        # Get filter settings
        key_only = getattr(self, "_key_only_action", None)
        key_only = key_only.isChecked() if key_only else False

        # Determine which level types to show
        visible_types = set()
        if hasattr(self, "_level_type_actions"):
            for level_type, action in self._level_type_actions.items():
                if action.isChecked():
                    visible_types.add(level_type)
        else:
            visible_types = {"support", "resistance", "pivot"}

        # Get chart time range
        start_time, end_time = self._get_chart_time_range()

        # Render each level
        for level in self._levels_result.levels:
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
            zone_id = self._level_to_zone(level, start_time, end_time)
            if zone_id:
                self._level_zones_ids.append(zone_id)

    def _level_to_zone(
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
            if hasattr(self, "_zones") and hasattr(self._zones, "add"):
                self._zones.add(zone)
                self._render_zone_on_chart(zone)
                # Register for click detection (Phase 5.7)
                self._register_zone_for_click(zone_id, level.price_high, level.price_low, label)
                return zone_id
            elif hasattr(self, "add_zone"):
                self.add_zone(
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
                self._register_zone_for_click(zone_id, level.price_high, level.price_low, label)
                return zone_id

            return None

        except Exception as e:
            logger.error(f"Failed to convert level to zone: {e}")
            return None

    def _render_zone_on_chart(self, zone) -> None:
        """Render zone on JavaScript chart."""
        try:
            # Use existing zone rendering if available
            if hasattr(self, "_run_js") and hasattr(self, "web_view"):
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
                self._run_js(js)
        except Exception as e:
            logger.error(f"Failed to render zone on chart: {e}")

    def _get_chart_time_range(self) -> tuple[int, int]:
        """
        Get current chart time range.

        Returns:
            Tuple of (start_time, end_time) as Unix timestamps
        """
        now = int(datetime.now(timezone.utc).timestamp())

        # Try to get from DataFrame
        if hasattr(self, "_current_df") and self._current_df is not None:
            df = self._current_df
            if hasattr(df, "index") and len(df) > 0:
                try:
                    start = int(df.index[0].timestamp()) if hasattr(df.index[0], "timestamp") else now - 86400
                    end = int(df.index[-1].timestamp()) if hasattr(df.index[-1], "timestamp") else now
                    return (start, end)
                except Exception:
                    pass

        # Default: last 24 hours
        return (now - 86400, now)

    def _show_level_zones(self) -> None:
        """Show all level zones."""
        self._render_level_zones()

    def _hide_level_zones(self) -> None:
        """Hide all level zones (without removing)."""
        # Use JavaScript to hide zones
        for zone_id in self._level_zones_ids:
            try:
                if hasattr(self, "_run_js"):
                    self._run_js(f'if (typeof hideZone === "function") hideZone("{zone_id}");')
            except Exception:
                pass

    def _clear_level_zones(self) -> None:
        """Remove all level zones from chart."""
        for zone_id in self._level_zones_ids:
            try:
                # Unregister from click detection (Phase 5.7)
                self._unregister_zone_from_click(zone_id)

                # Remove from zones manager
                if hasattr(self, "_zones") and hasattr(self._zones, "remove"):
                    self._zones.remove(zone_id)

                # Remove from chart
                if hasattr(self, "_run_js"):
                    self._run_js(f'if (typeof removeZone === "function") removeZone("{zone_id}");')
            except Exception as e:
                logger.debug(f"Failed to remove zone {zone_id}: {e}")

        self._level_zones_ids = []
        logger.debug("Cleared all level zones")

    def _refresh_level_zones(self) -> None:
        """Refresh level zones (re-detect and render)."""
        if hasattr(self, "_current_df") and self._current_df is not None:
            symbol = getattr(self, "current_symbol", "UNKNOWN")
            timeframe = getattr(self, "current_timeframe", "5m")
            current_price = None
            if hasattr(self, "_current_df") and len(self._current_df) > 0:
                current_price = float(self._current_df["close"].iloc[-1])

            self.detect_and_render_levels(self._current_df, symbol, timeframe, current_price)
        elif self._levels_result:
            self._render_level_zones()

    def get_levels_for_chatbot(self) -> str:
        """
        Get levels in tag format for chatbot.

        Returns:
            String with level tags like "[#Support Zone; 91038-91120]"
        """
        if self._levels_result is None:
            return ""
        return self._levels_result.to_tag_format()

    def get_nearest_support(self, price: Optional[float] = None) -> Optional["Level"]:
        """Get nearest support level."""
        if self._levels_result is None:
            return None
        return self._levels_result.get_nearest_support(price)

    def get_nearest_resistance(self, price: Optional[float] = None) -> Optional["Level"]:
        """Get nearest resistance level."""
        if self._levels_result is None:
            return None
        return self._levels_result.get_nearest_resistance(price)

    # =========================================================================
    # Phase 5.7: Level Click Interactions
    # =========================================================================

    def _register_zone_for_click(self, zone_id: str, top: float, bottom: float, label: str) -> None:
        """Register a zone for click detection in JavaScript.

        Args:
            zone_id: Zone identifier
            top: Zone top price
            bottom: Zone bottom price
            label: Zone label
        """
        if hasattr(self, "_run_js"):
            js = f"""
                if (window.chartAPI && window.chartAPI.registerZoneForClick) {{
                    window.chartAPI.registerZoneForClick("{zone_id}", {top}, {bottom}, "{label}");
                }}
            """
            self._run_js(js)

    def _unregister_zone_from_click(self, zone_id: str) -> None:
        """Unregister a zone from click detection.

        Args:
            zone_id: Zone identifier
        """
        if hasattr(self, "_run_js"):
            js = f"""
                if (window.chartAPI && window.chartAPI.unregisterZoneFromClick) {{
                    window.chartAPI.unregisterZoneFromClick("{zone_id}");
                }}
            """
            self._run_js(js)

    def _setup_zone_click_handler(self) -> None:
        """Setup zone click handler by connecting to bridge signal."""
        if hasattr(self, "bridge") and self.bridge is not None:
            if hasattr(self.bridge, "zone_clicked"):
                self.bridge.zone_clicked.connect(self._on_zone_clicked)
                logger.debug("Zone click handler connected")

    def _on_zone_clicked(self, zone_id: str, price: float, top: float, bottom: float, label: str) -> None:
        """Handle zone click event - show context menu.

        Args:
            zone_id: Clicked zone ID
            price: Price at click
            top: Zone top price
            bottom: Zone bottom price
            label: Zone label
        """
        from PyQt6.QtCore import QPoint
        from PyQt6.QtWidgets import QMenu, QApplication
        from PyQt6.QtGui import QCursor

        logger.info(f"Zone clicked: {zone_id} @ {price:.2f}")

        # Store clicked zone info for action handlers
        self._clicked_zone = {
            "id": zone_id,
            "price": price,
            "top": top,
            "bottom": bottom,
            "label": label,
        }

        # Get Level object if available
        level = self._get_level_by_zone_id(zone_id)

        # Create context menu
        menu = QMenu(self if hasattr(self, "setParent") else None)

        # Level info header
        mid_price = (top + bottom) / 2
        menu.addAction(f"📊 {label}").setEnabled(False)
        menu.addAction(f"   Preis: {bottom:.2f} - {top:.2f}").setEnabled(False)
        menu.addAction(f"   Mitte: {mid_price:.2f}").setEnabled(False)

        if level:
            menu.addAction(f"   Stärke: {level.strength.value.upper()}").setEnabled(False)
            if level.touches:
                menu.addAction(f"   Touches: {level.touches}").setEnabled(False)

        menu.addSeparator()

        # Copy actions
        copy_menu = menu.addMenu("📋 Kopieren")
        copy_mid = copy_menu.addAction("Mitte kopieren")
        copy_mid.triggered.connect(lambda: self._copy_level_price(mid_price))
        copy_top = copy_menu.addAction("Oberkante kopieren")
        copy_top.triggered.connect(lambda: self._copy_level_price(top))
        copy_bottom = copy_menu.addAction("Unterkante kopieren")
        copy_bottom.triggered.connect(lambda: self._copy_level_price(bottom))
        copy_range = copy_menu.addAction("Range kopieren")
        copy_range.triggered.connect(lambda: self._copy_level_range(bottom, top))

        menu.addSeparator()

        # Set as TP/SL actions
        set_menu = menu.addMenu("🎯 Als Ziel setzen")
        set_tp = set_menu.addAction("Als Take Profit setzen")
        set_tp.triggered.connect(lambda: self._suggest_set_level_as("TP", mid_price))
        set_sl = set_menu.addAction("Als Stop Loss setzen")
        set_sl.triggered.connect(lambda: self._suggest_set_level_as("SL", mid_price))
        set_entry = set_menu.addAction("Als Entry setzen")
        set_entry.triggered.connect(lambda: self._suggest_set_level_as("Entry", mid_price))

        menu.addSeparator()

        # Remove zone
        remove_action = menu.addAction("🗑️ Level entfernen")
        remove_action.triggered.connect(lambda: self._remove_single_level_zone(zone_id))

        # Show menu at cursor position
        menu.exec(QCursor.pos())

    def _get_level_by_zone_id(self, zone_id: str) -> Optional["Level"]:
        """Get Level object by zone ID.

        Args:
            zone_id: Zone ID in format "level_{level_id}"

        Returns:
            Level object or None
        """
        if self._levels_result is None:
            return None

        # Extract level ID from zone ID
        if zone_id.startswith("level_"):
            level_id = zone_id[6:]  # Remove "level_" prefix
            for level in self._levels_result.levels:
                if level.id == level_id:
                    return level

        return None

    def _copy_level_price(self, price: float) -> None:
        """Copy level price to clipboard.

        Args:
            price: Price to copy
        """
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(f"{price:.2f}")
        logger.info(f"Copied price to clipboard: {price:.2f}")

        # Show brief status if possible
        if hasattr(self, "status_label"):
            self.status_label.setText(f"Kopiert: {price:.2f}")

    def _copy_level_range(self, bottom: float, top: float) -> None:
        """Copy level range to clipboard.

        Args:
            bottom: Lower price
            top: Upper price
        """
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(f"{bottom:.2f} - {top:.2f}")
        logger.info(f"Copied range to clipboard: {bottom:.2f} - {top:.2f}")

    def _suggest_set_level_as(self, target_type: str, price: float) -> None:
        """Suggest setting level as TP/SL/Entry.

        This emits a signal that the parent window can handle.

        Args:
            target_type: "TP", "SL", or "Entry"
            price: Target price
        """
        logger.info(f"Suggest set {target_type} at {price:.2f}")

        # Emit signal if available (Phase 5.7)
        if hasattr(self, "level_target_suggested"):
            self.level_target_suggested.emit(target_type, price)
        else:
            # Fallback: try to find bot control and set directly
            from PyQt6.QtWidgets import QMessageBox

            msg = QMessageBox(self if hasattr(self, "setParent") else None)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(f"{target_type} Vorschlag")
            msg.setText(f"Level als {target_type} vorgeschlagen:")
            msg.setInformativeText(f"Preis: {price:.2f}\n\nDiesen Wert in die Bot-Konfiguration übertragen?")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

            if msg.exec() == QMessageBox.StandardButton.Ok:
                self._copy_level_price(price)
                logger.info(f"{target_type} price copied to clipboard for manual entry")

    def _remove_single_level_zone(self, zone_id: str) -> None:
        """Remove a single level zone.

        Args:
            zone_id: Zone ID to remove
        """
        try:
            # Unregister from click detection
            self._unregister_zone_from_click(zone_id)

            # Remove from zones manager
            if hasattr(self, "_zones") and hasattr(self._zones, "remove"):
                self._zones.remove(zone_id)

            # Remove from chart
            if hasattr(self, "_run_js"):
                self._run_js(f'if (typeof removeZone === "function") removeZone("{zone_id}");')

            # Remove from our list
            if zone_id in self._level_zones_ids:
                self._level_zones_ids.remove(zone_id)

            logger.info(f"Removed level zone: {zone_id}")

        except Exception as e:
            logger.error(f"Failed to remove zone {zone_id}: {e}")
