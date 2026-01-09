"""Level Zones Toolbar - Toolbar and menu building for level zones.

Refactored from 722 LOC monolith using composition pattern.

Module 2/5 of level_zones_mixin.py split.

Contains:
- add_levels_toggle_to_toolbar(): Add levels toggle button to toolbar
- build_levels_menu(): Build dropdown menu with level type toggles
- on_levels_toggle(): Handle main visibility toggle
- on_level_type_toggle(): Handle level type filter toggle
- on_key_levels_only(): Handle key levels only filter
"""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import QPushButton, QMenu, QLabel
from PyQt6.QtGui import QAction

logger = logging.getLogger(__name__)


class LevelZonesToolbar:
    """Helper für Level Zones Toolbar und Menu."""

    def __init__(self, parent):
        """
        Args:
            parent: LevelZonesMixin Instanz
        """
        self.parent = parent

    def add_levels_toggle_to_toolbar(self, toolbar) -> None:
        """
        Add levels toggle button to toolbar.

        Args:
            toolbar: QToolBar to add button to
        """
        toolbar.addWidget(QLabel("Levels:"))

        self.parent._levels_toggle_button = QPushButton("📊 Levels")
        self.parent._levels_toggle_button.setCheckable(True)
        self.parent._levels_toggle_button.setChecked(True)
        self.parent._levels_toggle_button.setToolTip("Support/Resistance Levels anzeigen/verbergen")
        self.parent._levels_toggle_button.clicked.connect(self.on_levels_toggle)
        self.parent._levels_toggle_button.setStyleSheet("""
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
        levels_menu = QMenu(self.parent._levels_toggle_button)
        self.build_levels_menu(levels_menu)
        self.parent._levels_toggle_button.setMenu(levels_menu)

        toolbar.addWidget(self.parent._levels_toggle_button)

    def build_levels_menu(self, menu: QMenu) -> None:
        """Build the levels dropdown menu."""
        # Refresh action
        refresh_action = QAction("🔄 Levels aktualisieren", self.parent)
        refresh_action.triggered.connect(self.parent._rendering.refresh_level_zones)
        menu.addAction(refresh_action)

        menu.addSeparator()

        # Level type toggles
        self.parent._level_type_actions = {}
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
            action = QAction(label, self.parent)
            action.setCheckable(True)
            action.setChecked(default)
            action.triggered.connect(lambda checked, lt=level_type: self.on_level_type_toggle(lt, checked))
            menu.addAction(action)
            self.parent._level_type_actions[level_type] = action

        menu.addSeparator()

        # Key levels only
        key_only_action = QAction("⭐ Nur Key Levels", self.parent)
        key_only_action.setCheckable(True)
        key_only_action.triggered.connect(self.on_key_levels_only)
        menu.addAction(key_only_action)
        self.parent._key_only_action = key_only_action

        menu.addSeparator()

        # Clear levels
        clear_action = QAction("🗑️ Levels entfernen", self.parent)
        clear_action.triggered.connect(self.parent._rendering.clear_level_zones)
        menu.addAction(clear_action)

    def on_levels_toggle(self, checked: bool) -> None:
        """Handle levels toggle button click."""
        self.parent._level_zones_visible = checked

        if checked:
            self.parent._rendering.show_level_zones()
        else:
            self.parent._rendering.hide_level_zones()

        logger.debug(f"Level zones visibility: {checked}")

    def on_level_type_toggle(self, level_type: str, checked: bool) -> None:
        """Handle level type toggle."""
        self.parent._rendering.refresh_level_zones()

    def on_key_levels_only(self, checked: bool) -> None:
        """Handle key levels only toggle."""
        self.parent._rendering.refresh_level_zones()
