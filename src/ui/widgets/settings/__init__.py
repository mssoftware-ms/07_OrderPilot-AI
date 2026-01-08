"""
Settings Widgets Package - UI-Widgets für alle Engine-Konfigurationen.

Phase 5 der Bot-Integration.

Enthält Settings-Widgets für:
- LevelEngine (Level-Detection Einstellungen)
- EntryScoreEngine (Score-Gewichte, Quality Thresholds, Gates)
- TriggerExitEngine (Entry Triggers, SL/TP, Trailing)
- LeverageRulesEngine (Asset Tiers, Regime Modifier, Safety)
- LLMValidationService (Thresholds, Modifiers, Prompt Settings)
"""

from .level_settings_widget import LevelSettingsWidget
from .entry_score_settings_widget import EntryScoreSettingsWidget
from .trigger_exit_settings_widget import TriggerExitSettingsWidget
from .leverage_settings_widget import LeverageSettingsWidget
from .llm_validation_settings_widget import LLMValidationSettingsWidget

__all__ = [
    "LevelSettingsWidget",
    "EntryScoreSettingsWidget",
    "TriggerExitSettingsWidget",
    "LeverageSettingsWidget",
    "LLMValidationSettingsWidget",
]
