"""Engine Settings Widgets Package.

Provides QWidget-based settings editors for each trading bot engine.
"""

from .entry_score_settings import EntryScoreSettingsWidget
from .trigger_exit_settings import TriggerExitSettingsWidget
from .leverage_settings import LeverageSettingsWidget
from .llm_validation_settings import LLMValidationSettingsWidget
from .level_settings import LevelSettingsWidget

__all__ = [
    "EntryScoreSettingsWidget",
    "TriggerExitSettingsWidget",
    "LeverageSettingsWidget",
    "LLMValidationSettingsWidget",
    "LevelSettingsWidget",
]
