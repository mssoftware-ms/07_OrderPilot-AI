"""Bot UI Engine Settings Mixin.

Provides the Engine Settings tab for the Trading Bot panel in the chart window.
Contains tabs for all engine configurations:
- Entry Score Engine
- Trigger & Exit Engine
- Leverage Rules Engine
- LLM Validation Service
- Level Detection Engine
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class BotUIEngineSettingsMixin:
    """Mixin providing Engine Settings tab for the Trading Bot panel."""

    def _create_engine_settings_tab(self) -> QWidget:
        """Create the Engine Settings tab with sub-tabs for each engine."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header with Apply/Reset buttons
        header = QHBoxLayout()
        header.addStretch()

        apply_btn = QPushButton("Apply All")
        apply_btn.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; padding: 6px 16px;"
        )
        apply_btn.clicked.connect(self._apply_all_engine_settings)
        header.addWidget(apply_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet("padding: 6px 16px;")
        reset_btn.clicked.connect(self._reset_engine_settings)
        header.addWidget(reset_btn)

        layout.addLayout(header)

        # Tab widget for engine settings
        self.engine_settings_tabs = QTabWidget()

        # Create tabs for each engine
        self._create_entry_score_tab()
        self._create_trigger_exit_tab()
        self._create_leverage_tab()
        self._create_llm_validation_tab()
        self._create_level_detection_tab()

        layout.addWidget(self.engine_settings_tabs)
        return widget

    def _create_entry_score_tab(self) -> None:
        """Create Entry Score Engine settings tab."""
        try:
            from src.ui.widgets.settings import EntryScoreSettingsWidget
            self.entry_score_settings = EntryScoreSettingsWidget()
            self.engine_settings_tabs.addTab(self.entry_score_settings, "Entry Score")
        except ImportError as e:
            logger.warning(f"Could not load EntryScoreSettingsWidget: {e}")
            self._add_placeholder_tab("Entry Score")

    def _create_trigger_exit_tab(self) -> None:
        """Create Trigger & Exit Engine settings tab."""
        try:
            from src.ui.widgets.settings import TriggerExitSettingsWidget
            self.trigger_exit_settings = TriggerExitSettingsWidget()
            self.engine_settings_tabs.addTab(self.trigger_exit_settings, "Trigger/Exit")
        except ImportError as e:
            logger.warning(f"Could not load TriggerExitSettingsWidget: {e}")
            self._add_placeholder_tab("Trigger/Exit")

    def _create_leverage_tab(self) -> None:
        """Create Leverage Rules Engine settings tab."""
        try:
            from src.ui.widgets.settings import LeverageSettingsWidget
            self.leverage_settings = LeverageSettingsWidget()
            self.engine_settings_tabs.addTab(self.leverage_settings, "Leverage")
        except ImportError as e:
            logger.warning(f"Could not load LeverageSettingsWidget: {e}")
            self._add_placeholder_tab("Leverage")

    def _create_llm_validation_tab(self) -> None:
        """Create LLM Validation Service settings tab."""
        try:
            from src.ui.widgets.settings import LLMValidationSettingsWidget
            self.llm_validation_settings = LLMValidationSettingsWidget()
            self.engine_settings_tabs.addTab(self.llm_validation_settings, "LLM Validation")
        except ImportError as e:
            logger.warning(f"Could not load LLMValidationSettingsWidget: {e}")
            self._add_placeholder_tab("LLM Validation")

    def _create_level_detection_tab(self) -> None:
        """Create Level Detection Engine settings tab."""
        try:
            from src.ui.widgets.settings import LevelSettingsWidget
            self.level_settings = LevelSettingsWidget()
            self.engine_settings_tabs.addTab(self.level_settings, "Levels")
        except ImportError as e:
            logger.warning(f"Could not load LevelSettingsWidget: {e}")
            self._add_placeholder_tab("Levels")

    def _add_placeholder_tab(self, name: str) -> None:
        """Add a placeholder tab when settings widget is not available."""
        from PyQt6.QtWidgets import QLabel
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        label = QLabel(f"{name} settings not available.\nModule not found.")
        label.setStyleSheet("color: #ff9800; font-size: 14px;")
        layout.addWidget(label)
        layout.addStretch()
        self.engine_settings_tabs.addTab(placeholder, name)

    def _apply_all_engine_settings(self) -> None:
        """Apply all engine settings."""
        logger.info("Applying all engine settings...")

        settings_widgets = [
            ('entry_score_settings', 'Entry Score'),
            ('trigger_exit_settings', 'Trigger/Exit'),
            ('leverage_settings', 'Leverage'),
            ('llm_validation_settings', 'LLM Validation'),
            ('level_settings', 'Level Detection'),
        ]

        for attr_name, display_name in settings_widgets:
            widget = getattr(self, attr_name, None)
            if widget and hasattr(widget, 'apply_settings'):
                try:
                    widget.apply_settings()
                    logger.info(f"Applied {display_name} settings")
                except Exception as e:
                    logger.error(f"Failed to apply {display_name} settings: {e}")

        # Add KI log entry if available
        if hasattr(self, '_add_ki_log_entry'):
            self._add_ki_log_entry("CONFIG", "Engine settings applied")

    def _reset_engine_settings(self) -> None:
        """Reset all engine settings to defaults."""
        logger.info("Resetting engine settings to defaults...")

        settings_widgets = [
            ('entry_score_settings', 'Entry Score'),
            ('trigger_exit_settings', 'Trigger/Exit'),
            ('leverage_settings', 'Leverage'),
            ('llm_validation_settings', 'LLM Validation'),
            ('level_settings', 'Level Detection'),
        ]

        for attr_name, display_name in settings_widgets:
            widget = getattr(self, attr_name, None)
            if widget and hasattr(widget, 'load_settings'):
                try:
                    widget.load_settings()
                    logger.info(f"Reset {display_name} settings")
                except Exception as e:
                    logger.error(f"Failed to reset {display_name} settings: {e}")
