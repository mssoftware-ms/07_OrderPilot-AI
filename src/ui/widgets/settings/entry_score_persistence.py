"""
Entry Score Persistence - Settings Serialization and File Operations.

Refactored from entry_score_settings_widget.py.

Contains:
- get_settings: Serialize current settings to dict
- set_settings: Deserialize dict to widget values
- load_settings: Load from config file
- apply_settings: Apply to EntryScoreEngine
- save_settings: Save to config file
- reset_to_defaults: Reset to default values
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from .entry_score_settings_widget import EntryScoreSettingsWidget

logger = logging.getLogger(__name__)

# Default config file path
DEFAULT_CONFIG_PATH = Path("config/entry_score_config.json")


class EntryScorePersistence:
    """Helper for settings persistence operations."""

    def __init__(self, parent: EntryScoreSettingsWidget):
        self.parent = parent

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return {
            "weights": {
                "trend_alignment": self.parent._weight_trend.value(),
                "rsi": self.parent._weight_rsi.value(),
                "macd": self.parent._weight_macd.value(),
                "adx": self.parent._weight_adx.value(),
                "volatility": self.parent._weight_volatility.value(),
                "volume": self.parent._weight_volume.value(),
            },
            "thresholds": {
                "excellent": self.parent._threshold_excellent.value(),
                "good": self.parent._threshold_good.value(),
                "moderate": self.parent._threshold_moderate.value(),
                "weak": self.parent._threshold_weak.value(),
            },
            "gates": {
                "block_in_chop": self.parent._block_in_chop.isChecked(),
                "block_against_strong_trend": self.parent._block_against_trend.isChecked(),
                "allow_counter_trend_sfp": self.parent._allow_sfp_counter.isChecked(),
                "trend_boost": self.parent._boost_modifier.value(),
                "chop_penalty": self.parent._chop_penalty.value(),
                "volatile_penalty": self.parent._volatile_penalty.value(),
            },
            "min_score_for_entry": self.parent._min_score_entry.value(),
        }

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict."""
        if "weights" in settings:
            w = settings["weights"]
            self.parent._weight_trend.setValue(w.get("trend_alignment", 0.25))
            self.parent._weight_rsi.setValue(w.get("rsi", 0.15))
            self.parent._weight_macd.setValue(w.get("macd", 0.20))
            self.parent._weight_adx.setValue(w.get("adx", 0.15))
            self.parent._weight_volatility.setValue(w.get("volatility", 0.10))
            self.parent._weight_volume.setValue(w.get("volume", 0.15))

        if "thresholds" in settings:
            t = settings["thresholds"]
            self.parent._threshold_excellent.setValue(t.get("excellent", 0.80))
            self.parent._threshold_good.setValue(t.get("good", 0.65))
            self.parent._threshold_moderate.setValue(t.get("moderate", 0.50))
            self.parent._threshold_weak.setValue(t.get("weak", 0.35))

        if "gates" in settings:
            g = settings["gates"]
            self.parent._block_in_chop.setChecked(g.get("block_in_chop", True))
            self.parent._block_against_trend.setChecked(g.get("block_against_strong_trend", True))
            self.parent._allow_sfp_counter.setChecked(g.get("allow_counter_trend_sfp", True))
            self.parent._boost_modifier.setValue(g.get("trend_boost", 0.10))
            self.parent._chop_penalty.setValue(g.get("chop_penalty", 0.15))
            self.parent._volatile_penalty.setValue(g.get("volatile_penalty", 0.10))

        self.parent._min_score_entry.setValue(settings.get("min_score_for_entry", 0.50))

        self.parent._validation.on_weight_changed()

    def load_settings(self) -> None:
        """Load settings from config file."""
        try:
            if DEFAULT_CONFIG_PATH.exists():
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    settings = json.load(f)
                self.set_settings(settings)
                logger.info("Entry score settings loaded from config")
            else:
                self.parent._validation.on_weight_changed()  # Initialize display
        except Exception as e:
            logger.warning(f"Failed to load entry score settings: {e}")
            self.parent._validation.on_weight_changed()

    def apply_settings(self) -> None:
        """Apply settings to engine."""
        settings = self.get_settings()

        # Validate weights sum
        total = sum(settings["weights"].values())
        if abs(total - 1.0) > 0.01:
            QMessageBox.warning(
                self.parent,
                "Ungültige Gewichte",
                f"Die Gewichte müssen sich zu 1.0 summieren.\n"
                f"Aktuelle Summe: {total:.2f}",
            )
            return

        try:
            from src.core.trading_bot import get_entry_score_engine, EntryScoreConfig

            engine = get_entry_score_engine()
            config = EntryScoreConfig(
                trend_weight=settings["weights"]["trend_alignment"],
                rsi_weight=settings["weights"]["rsi"],
                macd_weight=settings["weights"]["macd"],
                adx_weight=settings["weights"]["adx"],
                volatility_weight=settings["weights"]["volatility"],
                volume_weight=settings["weights"]["volume"],
                excellent_threshold=settings["thresholds"]["excellent"],
                good_threshold=settings["thresholds"]["good"],
                moderate_threshold=settings["thresholds"]["moderate"],
                weak_threshold=settings["thresholds"]["weak"],
                block_in_chop=settings["gates"]["block_in_chop"],
                block_against_strong_trend=settings["gates"]["block_against_strong_trend"],
                allow_counter_trend_sfp=settings["gates"]["allow_counter_trend_sfp"],
                trend_boost=settings["gates"]["trend_boost"],
                chop_penalty=settings["gates"]["chop_penalty"],
                volatile_penalty=settings["gates"]["volatile_penalty"],
                min_score_for_entry=settings["min_score_for_entry"],
            )
            engine.update_config(config)
            logger.info("Entry score settings applied")

            QMessageBox.information(
                self.parent, "Erfolg", "Einstellungen wurden übernommen."
            )
        except Exception as e:
            logger.error(f"Failed to apply entry score settings: {e}")
            QMessageBox.critical(
                self.parent, "Fehler", f"Einstellungen konnten nicht übernommen werden:\n{e}"
            )

    def save_settings(self) -> None:
        """Save settings to config file."""
        settings = self.get_settings()

        # Validate weights sum
        total = sum(settings["weights"].values())
        if abs(total - 1.0) > 0.01:
            QMessageBox.warning(
                self.parent,
                "Ungültige Gewichte",
                f"Die Gewichte müssen sich zu 1.0 summieren.\n"
                f"Aktuelle Summe: {total:.2f}",
            )
            return

        try:
            DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(DEFAULT_CONFIG_PATH, "w") as f:
                json.dump(settings, f, indent=2)

            self.apply_settings()
            self.parent.settings_saved.emit()
            logger.info(f"Entry score settings saved to {DEFAULT_CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to save entry score settings: {e}")
            QMessageBox.critical(
                self.parent, "Fehler", f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    def reset_to_defaults(self) -> None:
        """Reset to default settings (Micro-Account optimiert)."""
        self.set_settings({
            "weights": {
                "trend_alignment": 0.25,
                "rsi": 0.15,
                "macd": 0.20,
                "adx": 0.15,
                "volatility": 0.10,
                "volume": 0.15,
            },
            "thresholds": {
                "excellent": 0.80,
                "good": 0.65,
                "moderate": 0.50,
                "weak": 0.35,
            },
            "gates": {
                "block_in_chop": False,  # Micro-Account: auch in Chop traden
                "block_against_strong_trend": True,
                "allow_counter_trend_sfp": True,
                "trend_boost": 0.10,
                "chop_penalty": 0.10,  # Micro-Account: weniger Strafe
                "volatile_penalty": 0.10,
            },
            "min_score_for_entry": 0.45,  # Micro-Account: niedrigere Schwelle
        })
        self.parent._validation.emit_settings_changed()
        logger.info("Entry score settings reset to defaults")
