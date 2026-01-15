"""
Trading Bot Settings Tab - Vollständige Bot-Konfiguration.

Integration aller Engine-Settings in einen Tab mit Sub-Tabs:
- Entry Score (Gewichte, Quality, Gates)
- Trigger/Exit (SL/TP, Trailing)
- Leverage (Tiers, Regime, Safety)
- LLM Validation (Thresholds, Modifiers)
- Levels (Detection, Filtering)

Phase 5 UI Integration.
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QScrollArea,
    QMessageBox,
)

logger = logging.getLogger(__name__)


class TradingBotSettingsTab(QWidget):
    """
    Kompletter Settings-Tab für den Trading Bot.

    Enthält Sub-Tabs für alle Engine-Konfigurationen.

    Signals:
        settings_changed: Emitted when any settings change
        all_saved: Emitted when all settings are saved

    Usage:
        tab = TradingBotSettingsTab()
        settings_dialog.tabs.addTab(tab, "Trading Bot")
    """

    settings_changed = pyqtSignal()
    all_saved = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI with sub-tabs."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # Header
        header = QLabel("<h3>Trading Bot Konfiguration</h3>")
        main_layout.addWidget(header)

        desc = QLabel(
            "Konfiguriere alle Aspekte des automatischen Trading Bots.\n"
            "Änderungen werden erst nach Klick auf 'Übernehmen' aktiv."
        )
        desc.setStyleSheet("color: #888;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Sub-tabs
        self._tabs = QTabWidget()

        # Import widgets lazily to avoid circular imports
        try:
            from src.ui.widgets.settings import (
                EntryScoreSettingsWidget,
                TriggerExitSettingsWidget,
                LeverageSettingsWidget,
                LLMValidationSettingsWidget,
                LevelSettingsWidget,
            )

            # Entry Score Tab
            self._entry_score_widget = EntryScoreSettingsWidget()
            self._entry_score_widget.settings_changed.connect(self._on_settings_changed)
            scroll1 = self._create_scroll_area(self._entry_score_widget)
            self._tabs.addTab(scroll1, "Entry Score")

            # Trigger/Exit Tab
            self._trigger_exit_widget = TriggerExitSettingsWidget()
            self._trigger_exit_widget.settings_changed.connect(self._on_settings_changed)
            scroll2 = self._create_scroll_area(self._trigger_exit_widget)
            self._tabs.addTab(scroll2, "Trigger/Exit")

            # Leverage Tab
            self._leverage_widget = LeverageSettingsWidget()
            self._leverage_widget.settings_changed.connect(self._on_settings_changed)
            scroll3 = self._create_scroll_area(self._leverage_widget)
            self._tabs.addTab(scroll3, "Leverage")

            # LLM Validation Tab
            self._llm_widget = LLMValidationSettingsWidget()
            self._llm_widget.settings_changed.connect(self._on_settings_changed)
            scroll4 = self._create_scroll_area(self._llm_widget)
            self._tabs.addTab(scroll4, "LLM Validation")

            # Levels Tab
            self._levels_widget = LevelSettingsWidget()
            self._levels_widget.settings_changed.connect(self._on_settings_changed)
            scroll5 = self._create_scroll_area(self._levels_widget)
            self._tabs.addTab(scroll5, "Levels")

            self._widgets_loaded = True

        except ImportError as e:
            logger.warning(f"Could not load settings widgets: {e}")
            placeholder = QLabel(
                "Settings Widgets konnten nicht geladen werden.\n"
                f"Fehler: {e}"
            )
            placeholder.setStyleSheet("color: #f44336;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._tabs.addTab(placeholder, "Error")
            self._widgets_loaded = False

        main_layout.addWidget(self._tabs, 1)

        # Global action buttons
        button_layout = QHBoxLayout()

        self._reset_all_btn = QPushButton("Alle zurücksetzen")
        self._reset_all_btn.clicked.connect(self._reset_all)
        button_layout.addWidget(self._reset_all_btn)

        button_layout.addStretch()

        self._apply_all_btn = QPushButton("Alle übernehmen")
        self._apply_all_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._apply_all_btn.clicked.connect(self._apply_all)
        button_layout.addWidget(self._apply_all_btn)

        self._save_all_btn = QPushButton("Alle speichern")
        self._save_all_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._save_all_btn.clicked.connect(self._save_all)
        button_layout.addWidget(self._save_all_btn)

        main_layout.addLayout(button_layout)

    def _create_scroll_area(self, widget: QWidget) -> QScrollArea:
        """Create a scroll area for a widget."""
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll

    def _on_settings_changed(self, settings: dict = None) -> None:
        """Handle settings change from any sub-widget."""
        self.settings_changed.emit()

    def _apply_all(self) -> None:
        """Apply all settings."""
        if not self._widgets_loaded:
            return

        try:
            self._entry_score_widget._apply_settings()
            self._trigger_exit_widget._apply_settings()
            self._leverage_widget._apply_settings()
            self._llm_widget._apply_settings()
            self._levels_widget._apply_settings()

            logger.info("All bot settings applied")
        except Exception as e:
            logger.error(f"Failed to apply all settings: {e}")
            QMessageBox.critical(
                self, "Fehler",
                f"Einstellungen konnten nicht übernommen werden:\n{e}"
            )

    def _save_all(self) -> None:
        """Save all settings."""
        if not self._widgets_loaded:
            return

        try:
            self._entry_score_widget._save_settings()
            self._trigger_exit_widget._save_settings()
            self._leverage_widget._save_settings()
            self._llm_widget._save_settings()
            self._levels_widget._save_settings()

            self.all_saved.emit()
            logger.info("All bot settings saved")

            QMessageBox.information(
                self, "Erfolg",
                "Alle Trading Bot Einstellungen wurden gespeichert."
            )
        except Exception as e:
            logger.error(f"Failed to save all settings: {e}")
            QMessageBox.critical(
                self, "Fehler",
                f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    def _reset_all(self) -> None:
        """Reset all settings to defaults."""
        if not self._widgets_loaded:
            return

        reply = QMessageBox.question(
            self,
            "Bestätigung",
            "Alle Einstellungen auf Standardwerte zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._entry_score_widget._reset_to_defaults()
            self._trigger_exit_widget._reset_to_defaults()
            self._leverage_widget._reset_to_defaults()
            self._llm_widget._reset_to_defaults()
            self._levels_widget._reset_to_defaults()

            logger.info("All bot settings reset to defaults")

    def get_all_settings(self) -> dict:
        """Get all settings as a combined dict."""
        if not self._widgets_loaded:
            return {}

        return {
            "entry_score": self._entry_score_widget.get_settings(),
            "trigger_exit": self._trigger_exit_widget.get_settings(),
            "leverage": self._leverage_widget.get_settings(),
            "llm_validation": self._llm_widget.get_settings(),
            "levels": self._levels_widget.get_settings(),
        }
