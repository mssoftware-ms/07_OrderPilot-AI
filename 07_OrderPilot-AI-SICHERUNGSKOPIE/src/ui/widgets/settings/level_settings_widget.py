"""
Level Settings Widget - Konfiguration für LevelEngine.

Erlaubt die Anpassung von:
- Swing Detection Parametern
- Zone Width Einstellungen
- Level Filtering
- Pivot Point Einstellungen

Phase 2.7 der Bot-Integration.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QPushButton,
    QFrame,
    QMessageBox,
)

logger = logging.getLogger(__name__)

# Default config file path
DEFAULT_CONFIG_PATH = Path("config/level_engine_config.json")


class LevelSettingsWidget(QWidget):
    """
    Widget für LevelEngine-Einstellungen.

    Ermöglicht die Konfiguration aller LevelEngine-Parameter.

    Signals:
        settings_changed: Emitted when settings are changed
        settings_saved: Emitted when settings are saved

    Usage:
        widget = LevelSettingsWidget()
        widget.settings_changed.connect(on_settings_changed)
        layout.addWidget(widget)
    """

    settings_changed = pyqtSignal(dict)
    settings_saved = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("<h3>Level Engine Einstellungen</h3>")
        main_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Konfiguriere die Erkennung von Support/Resistance Levels.\n"
            "Änderungen werden bei der nächsten Level-Analyse wirksam."
        )
        desc.setStyleSheet("color: #888;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Swing Detection Group
        swing_group = self._create_swing_group()
        main_layout.addWidget(swing_group)

        # Zone Width Group
        zone_group = self._create_zone_group()
        main_layout.addWidget(zone_group)

        # Filtering Group
        filter_group = self._create_filter_group()
        main_layout.addWidget(filter_group)

        # Pivot Points Group
        pivot_group = self._create_pivot_group()
        main_layout.addWidget(pivot_group)

        # Historical Levels Group
        historical_group = self._create_historical_group()
        main_layout.addWidget(historical_group)

        # Spacer
        main_layout.addStretch()

        # Action Buttons
        button_layout = QHBoxLayout()

        self._reset_btn = QPushButton("🔄 Zurücksetzen")
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self._reset_btn)

        button_layout.addStretch()

        self._apply_btn = QPushButton("✓ Übernehmen")
        self._apply_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(self._apply_btn)

        self._save_btn = QPushButton("💾 Speichern")
        self._save_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self._save_btn)

        main_layout.addLayout(button_layout)

    def _create_swing_group(self) -> QGroupBox:
        """Create swing detection settings group."""
        group = QGroupBox("Swing Detection")
        layout = QFormLayout(group)

        # Swing Lookback
        self._swing_lookback = QSpinBox()
        self._swing_lookback.setRange(3, 50)
        self._swing_lookback.setValue(10)
        self._swing_lookback.setToolTip(
            "Anzahl der Bars links/rechts für Swing High/Low Erkennung.\n"
            "Höhere Werte = weniger, aber signifikantere Swings."
        )
        layout.addRow("Swing Lookback:", self._swing_lookback)

        # Min Swing Touches
        self._min_swing_touches = QSpinBox()
        self._min_swing_touches.setRange(1, 10)
        self._min_swing_touches.setValue(2)
        self._min_swing_touches.setToolTip(
            "Minimum Berührungen für ein valides Level."
        )
        layout.addRow("Min. Touches:", self._min_swing_touches)

        return group

    def _create_zone_group(self) -> QGroupBox:
        """Create zone width settings group."""
        group = QGroupBox("Zone Breite")
        layout = QFormLayout(group)

        # ATR Multiplier
        self._zone_atr_mult = QDoubleSpinBox()
        self._zone_atr_mult.setRange(0.1, 2.0)
        self._zone_atr_mult.setValue(0.3)
        self._zone_atr_mult.setSingleStep(0.1)
        self._zone_atr_mult.setDecimals(1)
        self._zone_atr_mult.setToolTip(
            "Zone-Breite als Vielfaches von ATR.\n"
            "0.3 = 30% des ATR."
        )
        layout.addRow("ATR Multiplikator:", self._zone_atr_mult)

        # Min Zone Width %
        self._min_zone_pct = QDoubleSpinBox()
        self._min_zone_pct.setRange(0.01, 1.0)
        self._min_zone_pct.setValue(0.1)
        self._min_zone_pct.setSingleStep(0.05)
        self._min_zone_pct.setDecimals(2)
        self._min_zone_pct.setSuffix(" %")
        self._min_zone_pct.setToolTip("Minimale Zone-Breite in Prozent des Preises.")
        layout.addRow("Min. Breite:", self._min_zone_pct)

        # Max Zone Width %
        self._max_zone_pct = QDoubleSpinBox()
        self._max_zone_pct.setRange(0.5, 5.0)
        self._max_zone_pct.setValue(2.0)
        self._max_zone_pct.setSingleStep(0.5)
        self._max_zone_pct.setDecimals(1)
        self._max_zone_pct.setSuffix(" %")
        self._max_zone_pct.setToolTip("Maximale Zone-Breite in Prozent des Preises.")
        layout.addRow("Max. Breite:", self._max_zone_pct)

        return group

    def _create_filter_group(self) -> QGroupBox:
        """Create filtering settings group."""
        group = QGroupBox("Filterung & Priorisierung")
        layout = QFormLayout(group)

        # Max Levels
        self._max_levels = QSpinBox()
        self._max_levels.setRange(5, 50)
        self._max_levels.setValue(20)
        self._max_levels.setToolTip("Maximum Anzahl Levels pro Analyse.")
        layout.addRow("Max. Levels:", self._max_levels)

        # Proximity Merge %
        self._proximity_merge = QDoubleSpinBox()
        self._proximity_merge.setRange(0.1, 2.0)
        self._proximity_merge.setValue(0.3)
        self._proximity_merge.setSingleStep(0.1)
        self._proximity_merge.setDecimals(1)
        self._proximity_merge.setSuffix(" %")
        self._proximity_merge.setToolTip(
            "Levels innerhalb dieses Prozentsatzes werden zusammengeführt."
        )
        layout.addRow("Merge Abstand:", self._proximity_merge)

        # Strength Thresholds
        layout.addRow(QLabel("<b>Stärke-Schwellenwerte</b>"))

        self._strong_threshold = QSpinBox()
        self._strong_threshold.setRange(2, 10)
        self._strong_threshold.setValue(3)
        self._strong_threshold.setToolTip("Touches für STRONG Level.")
        layout.addRow("STRONG ab Touches:", self._strong_threshold)

        self._key_threshold = QSpinBox()
        self._key_threshold.setRange(3, 20)
        self._key_threshold.setValue(5)
        self._key_threshold.setToolTip("Touches für KEY Level.")
        layout.addRow("KEY ab Touches:", self._key_threshold)

        return group

    def _create_pivot_group(self) -> QGroupBox:
        """Create pivot point settings group."""
        group = QGroupBox("Pivot Points")
        layout = QFormLayout(group)

        # Include Pivots
        self._include_pivots = QCheckBox("Pivot Points berechnen")
        self._include_pivots.setChecked(True)
        self._include_pivots.setToolTip("PP, R1, R2, S1, S2 berechnen.")
        layout.addRow(self._include_pivots)

        # Pivot Type
        self._pivot_type = QComboBox()
        self._pivot_type.addItems(["Standard", "Fibonacci", "Woodie", "Camarilla"])
        self._pivot_type.setToolTip("Art der Pivot-Berechnung.")
        layout.addRow("Pivot Typ:", self._pivot_type)

        return group

    def _create_historical_group(self) -> QGroupBox:
        """Create historical levels settings group."""
        group = QGroupBox("Historische Levels")
        layout = QFormLayout(group)

        # Daily H/L
        self._include_daily = QCheckBox("Daily Highs/Lows")
        self._include_daily.setChecked(True)
        self._include_daily.setToolTip("Tages-Hochs und -Tiefs einbeziehen.")
        layout.addRow(self._include_daily)

        self._daily_lookback = QSpinBox()
        self._daily_lookback.setRange(1, 30)
        self._daily_lookback.setValue(5)
        self._daily_lookback.setSuffix(" Tage")
        layout.addRow("Daily Lookback:", self._daily_lookback)

        # Weekly H/L
        self._include_weekly = QCheckBox("Weekly Highs/Lows")
        self._include_weekly.setChecked(True)
        self._include_weekly.setToolTip("Wochen-Hochs und -Tiefs einbeziehen.")
        layout.addRow(self._include_weekly)

        self._weekly_lookback = QSpinBox()
        self._weekly_lookback.setRange(1, 12)
        self._weekly_lookback.setValue(4)
        self._weekly_lookback.setSuffix(" Wochen")
        layout.addRow("Weekly Lookback:", self._weekly_lookback)

        return group

    def _connect_signals(self) -> None:
        """Connect change signals."""
        # All value changes emit settings_changed
        for spinbox in [
            self._swing_lookback,
            self._min_swing_touches,
            self._max_levels,
            self._strong_threshold,
            self._key_threshold,
            self._daily_lookback,
            self._weekly_lookback,
        ]:
            spinbox.valueChanged.connect(self._on_value_changed)

        for dspinbox in [
            self._zone_atr_mult,
            self._min_zone_pct,
            self._max_zone_pct,
            self._proximity_merge,
        ]:
            dspinbox.valueChanged.connect(self._on_value_changed)

        for checkbox in [
            self._include_pivots,
            self._include_daily,
            self._include_weekly,
        ]:
            checkbox.stateChanged.connect(self._on_value_changed)

        self._pivot_type.currentIndexChanged.connect(self._on_value_changed)

    def _on_value_changed(self, *args) -> None:
        """Handle any value change."""
        # Mark as changed
        self._apply_btn.setStyleSheet(
            "background-color: #FF9800; color: white; font-weight: bold; padding: 8px 16px;"
        )

    def get_config(self) -> dict:
        """
        Get current configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "swing_lookback": self._swing_lookback.value(),
            "min_swing_touches": self._min_swing_touches.value(),
            "zone_width_atr_mult": self._zone_atr_mult.value(),
            "min_zone_width_pct": self._min_zone_pct.value(),
            "max_zone_width_pct": self._max_zone_pct.value(),
            "max_levels": self._max_levels.value(),
            "proximity_merge_pct": self._proximity_merge.value(),
            "strong_touch_threshold": self._strong_threshold.value(),
            "key_touch_threshold": self._key_threshold.value(),
            "include_pivots": self._include_pivots.isChecked(),
            "pivot_type": self._pivot_type.currentText().lower(),
            "include_daily_hl": self._include_daily.isChecked(),
            "include_weekly_hl": self._include_weekly.isChecked(),
            "daily_lookback": self._daily_lookback.value(),
            "weekly_lookback": self._weekly_lookback.value(),
        }

    def set_config(self, config: dict) -> None:
        """
        Set configuration from dictionary.

        Args:
            config: Configuration dictionary
        """
        if "swing_lookback" in config:
            self._swing_lookback.setValue(config["swing_lookback"])
        if "min_swing_touches" in config:
            self._min_swing_touches.setValue(config["min_swing_touches"])
        if "zone_width_atr_mult" in config:
            self._zone_atr_mult.setValue(config["zone_width_atr_mult"])
        if "min_zone_width_pct" in config:
            self._min_zone_pct.setValue(config["min_zone_width_pct"])
        if "max_zone_width_pct" in config:
            self._max_zone_pct.setValue(config["max_zone_width_pct"])
        if "max_levels" in config:
            self._max_levels.setValue(config["max_levels"])
        if "proximity_merge_pct" in config:
            self._proximity_merge.setValue(config["proximity_merge_pct"])
        if "strong_touch_threshold" in config:
            self._strong_threshold.setValue(config["strong_touch_threshold"])
        if "key_touch_threshold" in config:
            self._key_threshold.setValue(config["key_touch_threshold"])
        if "include_pivots" in config:
            self._include_pivots.setChecked(config["include_pivots"])
        if "pivot_type" in config:
            idx = self._pivot_type.findText(config["pivot_type"].title())
            if idx >= 0:
                self._pivot_type.setCurrentIndex(idx)
        if "include_daily_hl" in config:
            self._include_daily.setChecked(config["include_daily_hl"])
        if "include_weekly_hl" in config:
            self._include_weekly.setChecked(config["include_weekly_hl"])
        if "daily_lookback" in config:
            self._daily_lookback.setValue(config["daily_lookback"])
        if "weekly_lookback" in config:
            self._weekly_lookback.setValue(config["weekly_lookback"])

    def _load_settings(self) -> None:
        """Load settings from config file."""
        try:
            if DEFAULT_CONFIG_PATH.exists():
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    config = json.load(f)
                    self.set_config(config)
                logger.debug("Level settings loaded from config")
        except Exception as e:
            logger.warning(f"Failed to load level settings: {e}")

    def _save_settings(self) -> None:
        """Save settings to config file."""
        try:
            config = self.get_config()

            # Ensure directory exists
            DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

            with open(DEFAULT_CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)

            logger.info("Level settings saved to config")
            self.settings_saved.emit()

            # Reset button style
            self._apply_btn.setStyleSheet(
                "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
            )

            QMessageBox.information(
                self,
                "Gespeichert",
                "Level-Einstellungen wurden gespeichert.",
            )

        except Exception as e:
            logger.error(f"Failed to save level settings: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Einstellungen konnten nicht gespeichert werden:\n{e}",
            )

    def _apply_settings(self) -> None:
        """Apply settings to LevelEngine."""
        try:
            config = self.get_config()

            # Update global LevelEngine
            from src.core.trading_bot.level_engine import (
                get_level_engine,
                LevelEngineConfig,
                reset_level_engine,
            )

            # Create new config
            new_config = LevelEngineConfig(
                swing_lookback=config["swing_lookback"],
                min_swing_touches=config["min_swing_touches"],
                zone_width_atr_mult=config["zone_width_atr_mult"],
                min_zone_width_pct=config["min_zone_width_pct"],
                max_zone_width_pct=config["max_zone_width_pct"],
                max_levels=config["max_levels"],
                proximity_merge_pct=config["proximity_merge_pct"],
                strong_touch_threshold=config["strong_touch_threshold"],
                key_touch_threshold=config["key_touch_threshold"],
                include_pivots=config["include_pivots"],
                pivot_type=config["pivot_type"],
                include_daily_hl=config["include_daily_hl"],
                include_weekly_hl=config["include_weekly_hl"],
                daily_lookback=config["daily_lookback"],
                weekly_lookback=config["weekly_lookback"],
            )

            # Reset and reinitialize with new config
            reset_level_engine()
            get_level_engine(new_config)

            logger.info("Level settings applied")
            self.settings_changed.emit(config)

            # Reset button style
            self._apply_btn.setStyleSheet(
                "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
            )

        except Exception as e:
            logger.error(f"Failed to apply level settings: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Einstellungen konnten nicht angewendet werden:\n{e}",
            )

    def _reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        from src.core.trading_bot.level_engine import LevelEngineConfig

        defaults = LevelEngineConfig()

        self._swing_lookback.setValue(defaults.swing_lookback)
        self._min_swing_touches.setValue(defaults.min_swing_touches)
        self._zone_atr_mult.setValue(defaults.zone_width_atr_mult)
        self._min_zone_pct.setValue(defaults.min_zone_width_pct)
        self._max_zone_pct.setValue(defaults.max_zone_width_pct)
        self._max_levels.setValue(defaults.max_levels)
        self._proximity_merge.setValue(defaults.proximity_merge_pct)
        self._strong_threshold.setValue(defaults.strong_touch_threshold)
        self._key_threshold.setValue(defaults.key_touch_threshold)
        self._include_pivots.setChecked(defaults.include_pivots)
        self._pivot_type.setCurrentIndex(0)
        self._include_daily.setChecked(defaults.include_daily_hl)
        self._include_weekly.setChecked(defaults.include_weekly_hl)
        self._daily_lookback.setValue(defaults.daily_lookback)
        self._weekly_lookback.setValue(defaults.weekly_lookback)

        logger.debug("Level settings reset to defaults")


def create_level_settings_tab() -> QWidget:
    """
    Factory function to create a Level Settings Tab.

    Use this in SettingsDialog to add a "Levels" tab.

    Returns:
        LevelSettingsWidget instance
    """
    return LevelSettingsWidget()
