"""
Trigger/Exit Settings Widget - Konfiguration für TriggerExitEngine (REFACTORED).

Erlaubt die Anpassung von:
- Entry Trigger Einstellungen (Breakout, Pullback, SFP)
- SL/TP Einstellungen (ATR-basiert, Percent-basiert)
- Trailing Stop Einstellungen
- Time Stop & Partial TP

REFACTORED: Split into focused helper modules using composition pattern.
- trigger_exit_settings_ui_groups.py: All 8 UI group creation methods
- trigger_exit_settings_management.py: get/set_settings + signal connections
- trigger_exit_settings_persistence.py: load/save/apply + reset to defaults

Phase 5.2 der Bot-Integration.
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
)

# Import helpers
from .trigger_exit_settings_ui_groups import TriggerExitSettingsUIGroups
from .trigger_exit_settings_management import TriggerExitSettingsManagement
from .trigger_exit_settings_persistence import TriggerExitSettingsPersistence

logger = logging.getLogger(__name__)


class TriggerExitSettingsWidget(QWidget):
    """
    Widget für TriggerExitEngine-Einstellungen (REFACTORED).

    Ermöglicht die Konfiguration aller Trigger- und Exit-Parameter.

    Signals:
        settings_changed: Emitted when settings are changed
        settings_saved: Emitted when settings are saved
    """

    settings_changed = pyqtSignal(dict)
    settings_saved = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Create helpers (composition pattern)
        self._ui_groups = TriggerExitSettingsUIGroups(self)
        self._management = TriggerExitSettingsManagement(self)
        self._persistence = TriggerExitSettingsPersistence(self)

        self._setup_ui()
        self._load_settings()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Title
        title = QLabel("<h3>Trigger & Exit Einstellungen</h3>")
        main_layout.addWidget(title)

        # Tab Widget for organization
        tabs = QTabWidget()

        # Entry Triggers Tab
        trigger_tab = QWidget()
        trigger_layout = QVBoxLayout(trigger_tab)
        trigger_layout.addWidget(self._ui_groups.create_breakout_group())
        trigger_layout.addWidget(self._ui_groups.create_pullback_group())
        trigger_layout.addWidget(self._ui_groups.create_sfp_group())
        trigger_layout.addStretch()
        tabs.addTab(trigger_tab, "Entry Triggers")

        # SL/TP Tab
        sl_tp_tab = QWidget()
        sl_tp_layout = QVBoxLayout(sl_tp_tab)
        sl_tp_layout.addWidget(self._ui_groups.create_sl_group())
        sl_tp_layout.addWidget(self._ui_groups.create_tp_group())
        sl_tp_layout.addStretch()
        tabs.addTab(sl_tp_tab, "SL / TP")

        # Trailing & Exit Tab
        trailing_tab = QWidget()
        trailing_layout = QVBoxLayout(trailing_tab)
        trailing_layout.addWidget(self._ui_groups.create_trailing_group())
        trailing_layout.addWidget(self._ui_groups.create_time_group())
        trailing_layout.addWidget(self._ui_groups.create_partial_tp_group())
        trailing_layout.addStretch()
        tabs.addTab(trailing_tab, "Trailing & Exit")

        main_layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self._reset_btn = QPushButton("Defaults (Micro-Account)")
        self._reset_btn.setStyleSheet(
            "background-color: #FF9800; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self._reset_btn)

        button_layout.addStretch()

        self._save_btn = QPushButton("Speichern & Anwenden")
        self._save_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self._save_btn)

        main_layout.addLayout(button_layout)

    # === Signal Connection (Delegiert) ===

    def _connect_signals(self) -> None:
        """Connect change signals (delegiert)."""
        return self._management.connect_signals()

    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal (delegiert)."""
        return self._management.emit_settings_changed()

    # === Settings Getter/Setter (Delegiert) ===

    def get_settings(self) -> dict:
        """Get current settings as dict (delegiert)."""
        return self._management.get_settings()

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict (delegiert)."""
        return self._management.set_settings(settings)

    # === Persistence (Delegiert) ===

    def _load_settings(self) -> None:
        """Load settings from config file (delegiert)."""
        return self._persistence.load_settings()

    def _apply_settings(self) -> None:
        """Apply settings to engine (delegiert)."""
        return self._persistence.apply_settings()

    def _save_settings(self) -> None:
        """Save settings to config file (delegiert)."""
        return self._persistence.save_settings()

    def _reset_to_defaults(self) -> None:
        """Reset to default settings (delegiert)."""
        return self._persistence.reset_to_defaults()
