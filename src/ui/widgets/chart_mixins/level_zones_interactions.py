"""Level Zones Interactions - Click detection and context menu.

Refactored from 722 LOC monolith using composition pattern.

Module 4/5 of level_zones_mixin.py split.

Contains (Phase 5.7: Level Click Interactions):
- register_zone_for_click(): Register zone for click detection
- unregister_zone_from_click(): Unregister zone
- setup_zone_click_handler(): Connect bridge signal
- on_zone_clicked(): Handle zone click → show context menu
- get_level_by_zone_id(): Get Level object by zone ID
- copy_level_price(): Copy price to clipboard
- copy_level_range(): Copy range to clipboard
- suggest_set_level_as(): Suggest TP/SL/Entry
- remove_single_level_zone(): Remove single zone
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.trading_bot.level_engine import Level

logger = logging.getLogger(__name__)


class LevelZonesInteractions:
    """Helper für Level Zones Interactions (Click Detection, Context Menu)."""

    def __init__(self, parent):
        """
        Args:
            parent: LevelZonesMixin Instanz
        """
        self.parent = parent

    # =========================================================================
    # Phase 5.7: Level Click Interactions
    # =========================================================================

    def register_zone_for_click(self, zone_id: str, top: float, bottom: float, label: str) -> None:
        """Register a zone for click detection in JavaScript.

        Args:
            zone_id: Zone identifier
            top: Zone top price
            bottom: Zone bottom price
            label: Zone label
        """
        if hasattr(self.parent, "_run_js"):
            js = f"""
                if (window.chartAPI && window.chartAPI.registerZoneForClick) {{
                    window.chartAPI.registerZoneForClick("{zone_id}", {top}, {bottom}, "{label}");
                }}
            """
            self.parent._run_js(js)

    def unregister_zone_from_click(self, zone_id: str) -> None:
        """Unregister a zone from click detection.

        Args:
            zone_id: Zone identifier
        """
        if hasattr(self.parent, "_run_js"):
            js = f"""
                if (window.chartAPI && window.chartAPI.unregisterZoneFromClick) {{
                    window.chartAPI.unregisterZoneFromClick("{zone_id}");
                }}
            """
            self.parent._run_js(js)

    def setup_zone_click_handler(self) -> None:
        """Setup zone click handler by connecting to bridge signal."""
        if hasattr(self.parent, "bridge") and self.parent.bridge is not None:
            if hasattr(self.parent.bridge, "zone_clicked"):
                self.parent.bridge.zone_clicked.connect(self.on_zone_clicked)
                logger.debug("Zone click handler connected")

    def on_zone_clicked(self, zone_id: str, price: float, top: float, bottom: float, label: str) -> None:
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
        self.parent._clicked_zone = {
            "id": zone_id,
            "price": price,
            "top": top,
            "bottom": bottom,
            "label": label,
        }

        # Get Level object if available
        level = self.get_level_by_zone_id(zone_id)

        # Create context menu
        menu = QMenu(self.parent if hasattr(self.parent, "setParent") else None)

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
        copy_mid.triggered.connect(lambda: self.copy_level_price(mid_price))
        copy_top = copy_menu.addAction("Oberkante kopieren")
        copy_top.triggered.connect(lambda: self.copy_level_price(top))
        copy_bottom = copy_menu.addAction("Unterkante kopieren")
        copy_bottom.triggered.connect(lambda: self.copy_level_price(bottom))
        copy_range = copy_menu.addAction("Range kopieren")
        copy_range.triggered.connect(lambda: self.copy_level_range(bottom, top))

        menu.addSeparator()

        # Set as TP/SL actions
        set_menu = menu.addMenu("🎯 Als Ziel setzen")
        set_tp = set_menu.addAction("Als Take Profit setzen")
        set_tp.triggered.connect(lambda: self.suggest_set_level_as("TP", mid_price))
        set_sl = set_menu.addAction("Als Stop Loss setzen")
        set_sl.triggered.connect(lambda: self.suggest_set_level_as("SL", mid_price))
        set_entry = set_menu.addAction("Als Entry setzen")
        set_entry.triggered.connect(lambda: self.suggest_set_level_as("Entry", mid_price))

        menu.addSeparator()

        # Remove zone
        remove_action = menu.addAction("🗑️ Level entfernen")
        remove_action.triggered.connect(lambda: self.remove_single_level_zone(zone_id))

        # Show menu at cursor position
        menu.exec(QCursor.pos())

    def get_level_by_zone_id(self, zone_id: str) -> Optional["Level"]:
        """Get Level object by zone ID.

        Args:
            zone_id: Zone ID in format "level_{level_id}"

        Returns:
            Level object or None
        """
        if self.parent._levels_result is None:
            return None

        # Extract level ID from zone ID
        if zone_id.startswith("level_"):
            level_id = zone_id[6:]  # Remove "level_" prefix
            for level in self.parent._levels_result.levels:
                if level.id == level_id:
                    return level

        return None

    def copy_level_price(self, price: float) -> None:
        """Copy level price to clipboard.

        Args:
            price: Price to copy
        """
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(f"{price:.2f}")
        logger.info(f"Copied price to clipboard: {price:.2f}")

        # Show brief status if possible
        if hasattr(self.parent, "status_label"):
            self.parent.status_label.setText(f"Kopiert: {price:.2f}")

    def copy_level_range(self, bottom: float, top: float) -> None:
        """Copy level range to clipboard.

        Args:
            bottom: Lower price
            top: Upper price
        """
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(f"{bottom:.2f} - {top:.2f}")
        logger.info(f"Copied range to clipboard: {bottom:.2f} - {top:.2f}")

    def suggest_set_level_as(self, target_type: str, price: float) -> None:
        """Suggest setting level as TP/SL/Entry.

        This emits a signal that the parent window can handle.

        Args:
            target_type: "TP", "SL", or "Entry"
            price: Target price
        """
        logger.info(f"Suggest set {target_type} at {price:.2f}")

        # Emit signal if available (Phase 5.7)
        if hasattr(self.parent, "level_target_suggested"):
            self.parent.level_target_suggested.emit(target_type, price)
        else:
            # Fallback: try to find bot control and set directly
            from PyQt6.QtWidgets import QMessageBox

            msg = QMessageBox(self.parent if hasattr(self.parent, "setParent") else None)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(f"{target_type} Vorschlag")
            msg.setText(f"Level als {target_type} vorgeschlagen:")
            msg.setInformativeText(f"Preis: {price:.2f}\n\nDiesen Wert in die Bot-Konfiguration übertragen?")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

            if msg.exec() == QMessageBox.StandardButton.Ok:
                self.copy_level_price(price)
                logger.info(f"{target_type} price copied to clipboard for manual entry")

    def remove_single_level_zone(self, zone_id: str) -> None:
        """Remove a single level zone.

        Args:
            zone_id: Zone ID to remove
        """
        try:
            # Unregister from click detection
            self.unregister_zone_from_click(zone_id)

            # Remove from zones manager
            if hasattr(self.parent, "_zones") and hasattr(self.parent._zones, "remove"):
                self.parent._zones.remove(zone_id)

            # Remove from chart
            if hasattr(self.parent, "_run_js"):
                self.parent._run_js(f'if (typeof removeZone === "function") removeZone("{zone_id}");')

            # Remove from our list
            if zone_id in self.parent._level_zones_ids:
                self.parent._level_zones_ids.remove(zone_id)

            logger.info(f"Removed level zone: {zone_id}")

        except Exception as e:
            logger.error(f"Failed to remove zone {zone_id}: {e}")
