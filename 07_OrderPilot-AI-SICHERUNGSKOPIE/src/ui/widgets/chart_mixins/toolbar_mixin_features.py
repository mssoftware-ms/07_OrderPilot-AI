"""Toolbar Mixin Features - Levels and Export Context (Phase 5.5).

Module 3/4 of toolbar_mixin.py split.

Contains Phase 5.5 feature buttons:
- Levels button (detect, toggle types, clear)
- Export Context button (inspector, copy JSON/prompt, export file, refresh)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLabel, QMenu, QPushButton, QToolBar

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolbarMixinFeatures:
    """Phase 5.5 feature buttons (Levels + Export Context)."""

    def __init__(self, parent):
        self.parent = parent

    def add_levels_button(self, toolbar: QToolBar) -> None:
        """Add levels toggle button to toolbar (Phase 5.5)."""
        self.parent.levels_button = QPushButton("📊 Levels")
        self.parent.levels_button.setCheckable(True)
        self.parent.levels_button.setChecked(False)
        self.parent.levels_button.setToolTip(
            "Support/Resistance Levels im Chart anzeigen/verbergen"
        )
        self.parent.levels_button.setStyleSheet(
            """
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
        """
        )

        # Add dropdown menu for level options
        levels_menu = QMenu(self.parent)
        self._build_levels_menu(levels_menu)
        self.parent.levels_button.setMenu(levels_menu)

        toolbar.addWidget(self.parent.levels_button)
        logger.debug("Levels button added to toolbar")

    def _build_levels_menu(self, menu: QMenu) -> None:
        """Build the levels dropdown menu."""
        # Refresh/Detect action
        detect_action = QAction("🔍 Levels erkennen", self.parent)
        detect_action.triggered.connect(self.on_detect_levels)
        menu.addAction(detect_action)

        menu.addSeparator()

        # Level type toggles
        self.parent._level_type_actions = {}
        level_types = [
            ("support", "🟢 Support Levels", True),
            ("resistance", "🔴 Resistance Levels", True),
            ("pivot", "🟣 Pivot Points", False),
            ("swing", "🟠 Swing Highs/Lows", False),
            ("daily", "📈 Daily H/L", False),
        ]

        for level_type, label, default in level_types:
            action = QAction(label, self.parent)
            action.setCheckable(True)
            action.setChecked(default)
            action.triggered.connect(
                lambda checked, lt=level_type: self.on_level_type_toggle(lt, checked)
            )
            menu.addAction(action)
            self.parent._level_type_actions[level_type] = action

        menu.addSeparator()

        # Key levels only
        key_only_action = QAction("⭐ Nur Key Levels", self.parent)
        key_only_action.setCheckable(True)
        menu.addAction(key_only_action)
        self.parent._key_only_action = key_only_action

        menu.addSeparator()

        # Clear levels
        clear_action = QAction("🗑️ Levels entfernen", self.parent)
        clear_action.triggered.connect(self.on_clear_levels)
        menu.addAction(clear_action)

    def on_detect_levels(self) -> None:
        """Trigger level detection."""
        logger.debug("Level detection requested via toolbar")
        # Signal wird in chart_window.py verbunden
        if hasattr(self.parent, "levels_detect_requested"):
            self.parent.levels_detect_requested.emit()

    def on_level_type_toggle(self, level_type: str, checked: bool) -> None:
        """Handle level type toggle."""
        logger.debug(f"Level type {level_type} toggled: {checked}")
        if hasattr(self.parent, "level_type_toggled"):
            self.parent.level_type_toggled.emit(level_type, checked)

    def on_clear_levels(self) -> None:
        """Clear all level zones from chart."""
        logger.debug("Clear levels requested")
        if hasattr(self.parent, "clear_zones"):
            self.parent.clear_zones()

    def add_export_context_button(self, toolbar: QToolBar) -> None:
        """Add export context button to toolbar (Phase 5.5)."""
        self.parent.export_context_button = QPushButton("📤 Context")
        self.parent.export_context_button.setToolTip(
            "MarketContext exportieren (JSON/Clipboard)"
        )
        self.parent.export_context_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2a2a2a;
                color: #00BCD4;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """
        )

        # Add dropdown menu for export options
        export_menu = QMenu(self.parent)
        self._build_export_context_menu(export_menu)
        self.parent.export_context_button.setMenu(export_menu)

        toolbar.addWidget(self.parent.export_context_button)
        logger.debug("Export context button added to toolbar")

    def _build_export_context_menu(self, menu: QMenu) -> None:
        """Build the export context dropdown menu."""
        # View Inspector
        inspect_action = QAction("🔍 Context Inspector öffnen", self.parent)
        inspect_action.triggered.connect(self.on_open_context_inspector)
        menu.addAction(inspect_action)

        menu.addSeparator()

        # Copy to clipboard
        copy_json_action = QAction("📋 Als JSON kopieren", self.parent)
        copy_json_action.triggered.connect(self.on_copy_context_json)
        menu.addAction(copy_json_action)

        copy_prompt_action = QAction("📝 Als AI Prompt kopieren", self.parent)
        copy_prompt_action.triggered.connect(self.on_copy_context_prompt)
        menu.addAction(copy_prompt_action)

        menu.addSeparator()

        # Export to file
        export_file_action = QAction("💾 Als JSON exportieren...", self.parent)
        export_file_action.triggered.connect(self.on_export_context_file)
        menu.addAction(export_file_action)

        menu.addSeparator()

        # Refresh context
        refresh_action = QAction("🔄 Context aktualisieren", self.parent)
        refresh_action.triggered.connect(self.on_refresh_context)
        menu.addAction(refresh_action)

    def on_open_context_inspector(self) -> None:
        """Open the MarketContext Inspector dialog."""
        logger.debug("Context inspector requested")
        # Wird in chart_window.py implementiert
        if hasattr(self.parent, "context_inspector_requested"):
            self.parent.context_inspector_requested.emit()

    def on_copy_context_json(self) -> None:
        """Copy MarketContext as JSON to clipboard."""
        logger.debug("Copy context JSON requested")
        if hasattr(self.parent, "context_copy_json_requested"):
            self.parent.context_copy_json_requested.emit()

    def on_copy_context_prompt(self) -> None:
        """Copy MarketContext as AI prompt to clipboard."""
        logger.debug("Copy context prompt requested")
        if hasattr(self.parent, "context_copy_prompt_requested"):
            self.parent.context_copy_prompt_requested.emit()

    def on_export_context_file(self) -> None:
        """Export MarketContext to JSON file."""
        logger.debug("Export context file requested")
        if hasattr(self.parent, "context_export_file_requested"):
            self.parent.context_export_file_requested.emit()

    def on_refresh_context(self) -> None:
        """Refresh MarketContext."""
        logger.debug("Refresh context requested")
        if hasattr(self.parent, "context_refresh_requested"):
            self.parent.context_refresh_requested.emit()
