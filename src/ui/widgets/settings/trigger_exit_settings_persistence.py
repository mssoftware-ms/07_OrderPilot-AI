"""Trigger/Exit Settings Persistence - Load/Save/Apply.

Refactored from trigger_exit_settings_widget.py.

Contains:
- load_settings: Load from JSON file
- save_settings: Save to JSON file
- apply_settings: Apply to engine
- reset_to_defaults: Reset to micro-account defaults
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from .trigger_exit_settings_widget import TriggerExitSettingsWidget

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config/trigger_exit_config.json")


class TriggerExitSettingsPersistence:
    """Helper for settings persistence."""

    def __init__(self, parent: TriggerExitSettingsWidget):
        self.parent = parent

    def load_settings(self) -> None:
        """Load settings from config file."""
        try:
            if DEFAULT_CONFIG_PATH.exists():
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    settings = json.load(f)
                self.parent.set_settings(settings)
                logger.info("Trigger/Exit settings loaded from config")
        except Exception as e:
            logger.warning(f"Failed to load trigger/exit settings: {e}")

    def apply_settings(self) -> None:
        """Apply settings to engine."""
        settings = self.parent.get_settings()

        try:
            from src.core.trading_bot import get_trigger_exit_engine

            engine = get_trigger_exit_engine()
            engine.update_config_from_dict(settings)
            logger.info("Trigger/Exit settings applied")

            QMessageBox.information(
                self.parent, "Erfolg", "Einstellungen wurden übernommen."
            )
        except Exception as e:
            logger.error(f"Failed to apply trigger/exit settings: {e}")
            QMessageBox.critical(
                self.parent, "Fehler", f"Einstellungen konnten nicht übernommen werden:\n{e}"
            )

    def save_settings(self) -> None:
        """Save settings to config file."""
        settings = self.parent.get_settings()

        try:
            DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(DEFAULT_CONFIG_PATH, "w") as f:
                json.dump(settings, f, indent=2)

            self.apply_settings()
            self.parent.settings_saved.emit()
            logger.info(f"Trigger/Exit settings saved to {DEFAULT_CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to save trigger/exit settings: {e}")
            QMessageBox.critical(
                self.parent, "Fehler", f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    def reset_to_defaults(self) -> None:
        """Reset to default settings (Micro-Account optimiert)."""
        defaults = {
            "triggers": {
                "breakout": {"enabled": True, "volume_multiplier": 1.5, "close_threshold_atr": 0.5},
                "pullback": {"enabled": True, "max_distance_atr": 1.0, "rejection_wick_atr": 0.3},
                "sfp": {"enabled": True, "wick_body_ratio": 2.0, "min_penetration_atr": 0.2},
            },
            "stop_loss": {"type": "atr", "atr_multiplier": 1.2, "percent": 1.5, "structure_buffer_atr": 0.2},  # Micro: enger SL
            "take_profit": {"rr_ratio": 1.5, "atr_multiplier": 2.5, "use_level": True},  # Micro: realistisches RR
            "trailing": {"enabled": True, "activation_r": 0.5, "distance_atr": 0.3, "step_atr": 0.15, "move_to_be": True},  # Micro: eng
            "time_stop": {"enabled": False, "max_hold_hours": 24},
            "partial_tp": {"enabled": True, "tp1_r": 0.75, "tp1_size_percent": 50, "move_sl_after_tp1": True},  # Micro: früher TP1
        }
        self.parent.set_settings(defaults)
        self.parent._management.emit_settings_changed()
        logger.info("Trigger/Exit settings reset to defaults")
