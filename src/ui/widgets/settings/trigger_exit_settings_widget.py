"""
Trigger/Exit Settings Widget - Konfiguration für TriggerExitEngine.

Erlaubt die Anpassung von:
- Entry Trigger Einstellungen (Breakout, Pullback, SFP)
- SL/TP Einstellungen (ATR-basiert, Percent-basiert)
- Trailing Stop Einstellungen
- Time Stop & Partial TP

Phase 5.2 der Bot-Integration.
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
    QTabWidget,
    QMessageBox,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config/trigger_exit_config.json")


class TriggerExitSettingsWidget(QWidget):
    """
    Widget für TriggerExitEngine-Einstellungen.

    Ermöglicht die Konfiguration aller Trigger- und Exit-Parameter.

    Signals:
        settings_changed: Emitted when settings are changed
        settings_saved: Emitted when settings are saved
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
        main_layout.setSpacing(12)

        # Title
        title = QLabel("<h3>Trigger & Exit Einstellungen</h3>")
        main_layout.addWidget(title)

        # Tab Widget for organization
        tabs = QTabWidget()

        # Entry Triggers Tab
        trigger_tab = QWidget()
        trigger_layout = QVBoxLayout(trigger_tab)
        trigger_layout.addWidget(self._create_breakout_group())
        trigger_layout.addWidget(self._create_pullback_group())
        trigger_layout.addWidget(self._create_sfp_group())
        trigger_layout.addStretch()
        tabs.addTab(trigger_tab, "Entry Triggers")

        # SL/TP Tab
        sltp_tab = QWidget()
        sltp_layout = QVBoxLayout(sltp_tab)
        sltp_layout.addWidget(self._create_sl_group())
        sltp_layout.addWidget(self._create_tp_group())
        sltp_layout.addStretch()
        tabs.addTab(sltp_tab, "SL/TP")

        # Trailing & Time Tab
        trailing_tab = QWidget()
        trailing_layout = QVBoxLayout(trailing_tab)
        trailing_layout.addWidget(self._create_trailing_group())
        trailing_layout.addWidget(self._create_time_group())
        trailing_layout.addWidget(self._create_partial_tp_group())
        trailing_layout.addStretch()
        tabs.addTab(trailing_tab, "Trailing & Time")

        main_layout.addWidget(tabs)

        # Action Buttons
        button_layout = QHBoxLayout()

        self._reset_btn = QPushButton("Zurücksetzen")
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self._reset_btn)

        button_layout.addStretch()

        self._apply_btn = QPushButton("Übernehmen")
        self._apply_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(self._apply_btn)

        self._save_btn = QPushButton("Speichern")
        self._save_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self._save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self._save_btn)

        main_layout.addLayout(button_layout)

    def _create_breakout_group(self) -> QGroupBox:
        """Create breakout trigger settings."""
        group = QGroupBox("Breakout Trigger")
        layout = QFormLayout(group)

        self._breakout_enabled = QCheckBox("Aktiviert")
        self._breakout_enabled.setChecked(True)
        layout.addRow(self._breakout_enabled)

        self._breakout_volume_mult = QDoubleSpinBox()
        self._breakout_volume_mult.setRange(1.0, 5.0)
        self._breakout_volume_mult.setValue(1.5)
        self._breakout_volume_mult.setSingleStep(0.1)
        self._breakout_volume_mult.setDecimals(1)
        self._breakout_volume_mult.setSuffix("x")
        self._breakout_volume_mult.setToolTip("Volume muss X mal höher als Average sein.")
        layout.addRow("Volume Multiplikator:", self._breakout_volume_mult)

        self._breakout_close_threshold = QDoubleSpinBox()
        self._breakout_close_threshold.setRange(0.1, 2.0)
        self._breakout_close_threshold.setValue(0.5)
        self._breakout_close_threshold.setSingleStep(0.1)
        self._breakout_close_threshold.setDecimals(1)
        self._breakout_close_threshold.setSuffix("% ATR")
        self._breakout_close_threshold.setToolTip("Close muss X% ATR über Level sein.")
        layout.addRow("Close Threshold:", self._breakout_close_threshold)

        return group

    def _create_pullback_group(self) -> QGroupBox:
        """Create pullback trigger settings."""
        group = QGroupBox("Pullback Trigger")
        layout = QFormLayout(group)

        self._pullback_enabled = QCheckBox("Aktiviert")
        self._pullback_enabled.setChecked(True)
        layout.addRow(self._pullback_enabled)

        self._pullback_max_distance = QDoubleSpinBox()
        self._pullback_max_distance.setRange(0.5, 3.0)
        self._pullback_max_distance.setValue(1.0)
        self._pullback_max_distance.setSingleStep(0.1)
        self._pullback_max_distance.setDecimals(1)
        self._pullback_max_distance.setSuffix("x ATR")
        self._pullback_max_distance.setToolTip("Max Distanz zum Level für Pullback.")
        layout.addRow("Max Distanz:", self._pullback_max_distance)

        self._pullback_rejection_wick = QDoubleSpinBox()
        self._pullback_rejection_wick.setRange(0.1, 1.0)
        self._pullback_rejection_wick.setValue(0.3)
        self._pullback_rejection_wick.setSingleStep(0.05)
        self._pullback_rejection_wick.setDecimals(2)
        self._pullback_rejection_wick.setSuffix("x ATR")
        self._pullback_rejection_wick.setToolTip("Min Wick-Größe für Rejection.")
        layout.addRow("Rejection Wick:", self._pullback_rejection_wick)

        return group

    def _create_sfp_group(self) -> QGroupBox:
        """Create SFP trigger settings."""
        group = QGroupBox("Swing Failure Pattern (SFP)")
        layout = QFormLayout(group)

        self._sfp_enabled = QCheckBox("Aktiviert")
        self._sfp_enabled.setChecked(True)
        layout.addRow(self._sfp_enabled)

        self._sfp_wick_body_ratio = QDoubleSpinBox()
        self._sfp_wick_body_ratio.setRange(0.5, 5.0)
        self._sfp_wick_body_ratio.setValue(2.0)
        self._sfp_wick_body_ratio.setSingleStep(0.5)
        self._sfp_wick_body_ratio.setDecimals(1)
        self._sfp_wick_body_ratio.setSuffix("x")
        self._sfp_wick_body_ratio.setToolTip("Min Verhältnis Wick zu Body.")
        layout.addRow("Wick/Body Ratio:", self._sfp_wick_body_ratio)

        self._sfp_penetration = QDoubleSpinBox()
        self._sfp_penetration.setRange(0.0, 1.0)
        self._sfp_penetration.setValue(0.2)
        self._sfp_penetration.setSingleStep(0.05)
        self._sfp_penetration.setDecimals(2)
        self._sfp_penetration.setSuffix("% ATR")
        self._sfp_penetration.setToolTip("Min Penetration durch Level.")
        layout.addRow("Min Penetration:", self._sfp_penetration)

        return group

    def _create_sl_group(self) -> QGroupBox:
        """Create stop loss settings."""
        group = QGroupBox("Stop Loss")
        layout = QFormLayout(group)

        # SL Type
        self._sl_type = QComboBox()
        self._sl_type.addItems(["ATR-basiert", "Percent-basiert", "Struktur-basiert"])
        self._sl_type.setToolTip("Art der SL-Berechnung.")
        layout.addRow("SL Typ:", self._sl_type)

        # ATR SL
        self._sl_atr_mult = QDoubleSpinBox()
        self._sl_atr_mult.setRange(0.5, 5.0)
        self._sl_atr_mult.setValue(1.5)
        self._sl_atr_mult.setSingleStep(0.1)
        self._sl_atr_mult.setDecimals(1)
        self._sl_atr_mult.setSuffix("x ATR")
        self._sl_atr_mult.setToolTip("SL Distanz als Vielfaches von ATR.")
        layout.addRow("ATR Multiplikator:", self._sl_atr_mult)

        # Percent SL
        self._sl_percent = QDoubleSpinBox()
        self._sl_percent.setRange(0.1, 10.0)
        self._sl_percent.setValue(2.0)
        self._sl_percent.setSingleStep(0.5)
        self._sl_percent.setDecimals(1)
        self._sl_percent.setSuffix("%")
        self._sl_percent.setToolTip("SL Distanz als Prozentsatz.")
        layout.addRow("Percent SL:", self._sl_percent)

        # Structure buffer
        self._sl_structure_buffer = QDoubleSpinBox()
        self._sl_structure_buffer.setRange(0.0, 1.0)
        self._sl_structure_buffer.setValue(0.2)
        self._sl_structure_buffer.setSingleStep(0.05)
        self._sl_structure_buffer.setDecimals(2)
        self._sl_structure_buffer.setSuffix("x ATR")
        self._sl_structure_buffer.setToolTip("Buffer unter/über Struktur-Level.")
        layout.addRow("Struktur Buffer:", self._sl_structure_buffer)

        return group

    def _create_tp_group(self) -> QGroupBox:
        """Create take profit settings."""
        group = QGroupBox("Take Profit")
        layout = QFormLayout(group)

        # Risk/Reward Target
        self._tp_rr_ratio = QDoubleSpinBox()
        self._tp_rr_ratio.setRange(1.0, 10.0)
        self._tp_rr_ratio.setValue(2.0)
        self._tp_rr_ratio.setSingleStep(0.5)
        self._tp_rr_ratio.setDecimals(1)
        self._tp_rr_ratio.setPrefix("1:")
        self._tp_rr_ratio.setToolTip("Risk/Reward Ratio für TP.")
        layout.addRow("R:R Ratio:", self._tp_rr_ratio)

        # ATR TP
        self._tp_atr_mult = QDoubleSpinBox()
        self._tp_atr_mult.setRange(1.0, 10.0)
        self._tp_atr_mult.setValue(3.0)
        self._tp_atr_mult.setSingleStep(0.5)
        self._tp_atr_mult.setDecimals(1)
        self._tp_atr_mult.setSuffix("x ATR")
        self._tp_atr_mult.setToolTip("TP Distanz als Vielfaches von ATR.")
        layout.addRow("ATR Multiplikator:", self._tp_atr_mult)

        # Use level as TP
        self._tp_use_level = QCheckBox("Level als TP verwenden")
        self._tp_use_level.setChecked(True)
        self._tp_use_level.setToolTip("Nächstes Resistance/Support Level als TP.")
        layout.addRow(self._tp_use_level)

        return group

    def _create_trailing_group(self) -> QGroupBox:
        """Create trailing stop settings."""
        group = QGroupBox("Trailing Stop")
        layout = QFormLayout(group)

        self._trailing_enabled = QCheckBox("Aktiviert")
        self._trailing_enabled.setChecked(True)
        layout.addRow(self._trailing_enabled)

        # Activation threshold
        self._trailing_activation = QDoubleSpinBox()
        self._trailing_activation.setRange(0.5, 5.0)
        self._trailing_activation.setValue(1.0)
        self._trailing_activation.setSingleStep(0.1)
        self._trailing_activation.setDecimals(1)
        self._trailing_activation.setSuffix("x R")
        self._trailing_activation.setToolTip("Profit-Distanz für Trailing-Aktivierung (in R).")
        layout.addRow("Aktivierung bei:", self._trailing_activation)

        # Trailing distance
        self._trailing_distance = QDoubleSpinBox()
        self._trailing_distance.setRange(0.3, 2.0)
        self._trailing_distance.setValue(0.5)
        self._trailing_distance.setSingleStep(0.1)
        self._trailing_distance.setDecimals(1)
        self._trailing_distance.setSuffix("x ATR")
        self._trailing_distance.setToolTip("Trailing-Distanz zum Preis.")
        layout.addRow("Trailing Distanz:", self._trailing_distance)

        # Step size
        self._trailing_step = QDoubleSpinBox()
        self._trailing_step.setRange(0.1, 1.0)
        self._trailing_step.setValue(0.2)
        self._trailing_step.setSingleStep(0.05)
        self._trailing_step.setDecimals(2)
        self._trailing_step.setSuffix("x ATR")
        self._trailing_step.setToolTip("Minimale Schrittweite für Trailing-Update.")
        layout.addRow("Step Size:", self._trailing_step)

        # Move to BE
        self._trailing_move_to_be = QCheckBox("Move to Break-Even bei 1R")
        self._trailing_move_to_be.setChecked(True)
        layout.addRow(self._trailing_move_to_be)

        return group

    def _create_time_group(self) -> QGroupBox:
        """Create time stop settings."""
        group = QGroupBox("Time Stop")
        layout = QFormLayout(group)

        self._time_stop_enabled = QCheckBox("Aktiviert")
        self._time_stop_enabled.setChecked(False)
        layout.addRow(self._time_stop_enabled)

        self._max_hold_hours = QSpinBox()
        self._max_hold_hours.setRange(1, 168)  # Up to 1 week
        self._max_hold_hours.setValue(24)
        self._max_hold_hours.setSuffix(" Stunden")
        self._max_hold_hours.setToolTip("Maximale Haltezeit.")
        layout.addRow("Max. Haltezeit:", self._max_hold_hours)

        return group

    def _create_partial_tp_group(self) -> QGroupBox:
        """Create partial take profit settings."""
        group = QGroupBox("Partial Take Profit")
        layout = QFormLayout(group)

        self._partial_tp_enabled = QCheckBox("Aktiviert")
        self._partial_tp_enabled.setChecked(True)
        layout.addRow(self._partial_tp_enabled)

        self._partial_tp1_r = QDoubleSpinBox()
        self._partial_tp1_r.setRange(0.5, 3.0)
        self._partial_tp1_r.setValue(1.0)
        self._partial_tp1_r.setSingleStep(0.25)
        self._partial_tp1_r.setDecimals(2)
        self._partial_tp1_r.setPrefix("TP1 bei ")
        self._partial_tp1_r.setSuffix("R")
        self._partial_tp1_r.setToolTip("Erster Teilverkauf bei X R.")
        layout.addRow(self._partial_tp1_r)

        self._partial_tp1_size = QSpinBox()
        self._partial_tp1_size.setRange(10, 90)
        self._partial_tp1_size.setValue(50)
        self._partial_tp1_size.setSuffix("%")
        self._partial_tp1_size.setToolTip("Anteil der Position beim TP1.")
        layout.addRow("TP1 Größe:", self._partial_tp1_size)

        self._move_sl_after_tp1 = QCheckBox("SL → Break-Even nach TP1")
        self._move_sl_after_tp1.setChecked(True)
        layout.addRow(self._move_sl_after_tp1)

        return group

    def _connect_signals(self) -> None:
        """Connect change signals."""
        # All widgets emit settings_changed on value change
        spinboxes = [
            self._breakout_volume_mult, self._breakout_close_threshold,
            self._pullback_max_distance, self._pullback_rejection_wick,
            self._sfp_wick_body_ratio, self._sfp_penetration,
            self._sl_atr_mult, self._sl_percent, self._sl_structure_buffer,
            self._tp_rr_ratio, self._tp_atr_mult,
            self._trailing_activation, self._trailing_distance, self._trailing_step,
            self._max_hold_hours,
            self._partial_tp1_r, self._partial_tp1_size,
        ]

        for spinbox in spinboxes:
            spinbox.valueChanged.connect(self._emit_settings_changed)

        checkboxes = [
            self._breakout_enabled, self._pullback_enabled, self._sfp_enabled,
            self._tp_use_level,
            self._trailing_enabled, self._trailing_move_to_be,
            self._time_stop_enabled,
            self._partial_tp_enabled, self._move_sl_after_tp1,
        ]

        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self._emit_settings_changed)

        self._sl_type.currentIndexChanged.connect(self._emit_settings_changed)

    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.settings_changed.emit(self.get_settings())

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return {
            "triggers": {
                "breakout": {
                    "enabled": self._breakout_enabled.isChecked(),
                    "volume_multiplier": self._breakout_volume_mult.value(),
                    "close_threshold_atr": self._breakout_close_threshold.value(),
                },
                "pullback": {
                    "enabled": self._pullback_enabled.isChecked(),
                    "max_distance_atr": self._pullback_max_distance.value(),
                    "rejection_wick_atr": self._pullback_rejection_wick.value(),
                },
                "sfp": {
                    "enabled": self._sfp_enabled.isChecked(),
                    "wick_body_ratio": self._sfp_wick_body_ratio.value(),
                    "min_penetration_atr": self._sfp_penetration.value(),
                },
            },
            "stop_loss": {
                "type": ["atr", "percent", "structure"][self._sl_type.currentIndex()],
                "atr_multiplier": self._sl_atr_mult.value(),
                "percent": self._sl_percent.value(),
                "structure_buffer_atr": self._sl_structure_buffer.value(),
            },
            "take_profit": {
                "rr_ratio": self._tp_rr_ratio.value(),
                "atr_multiplier": self._tp_atr_mult.value(),
                "use_level": self._tp_use_level.isChecked(),
            },
            "trailing": {
                "enabled": self._trailing_enabled.isChecked(),
                "activation_r": self._trailing_activation.value(),
                "distance_atr": self._trailing_distance.value(),
                "step_atr": self._trailing_step.value(),
                "move_to_be": self._trailing_move_to_be.isChecked(),
            },
            "time_stop": {
                "enabled": self._time_stop_enabled.isChecked(),
                "max_hold_hours": self._max_hold_hours.value(),
            },
            "partial_tp": {
                "enabled": self._partial_tp_enabled.isChecked(),
                "tp1_r": self._partial_tp1_r.value(),
                "tp1_size_percent": self._partial_tp1_size.value(),
                "move_sl_after_tp1": self._move_sl_after_tp1.isChecked(),
            },
        }

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict."""
        if "triggers" in settings:
            t = settings["triggers"]
            if "breakout" in t:
                self._breakout_enabled.setChecked(t["breakout"].get("enabled", True))
                self._breakout_volume_mult.setValue(t["breakout"].get("volume_multiplier", 1.5))
                self._breakout_close_threshold.setValue(t["breakout"].get("close_threshold_atr", 0.5))
            if "pullback" in t:
                self._pullback_enabled.setChecked(t["pullback"].get("enabled", True))
                self._pullback_max_distance.setValue(t["pullback"].get("max_distance_atr", 1.0))
                self._pullback_rejection_wick.setValue(t["pullback"].get("rejection_wick_atr", 0.3))
            if "sfp" in t:
                self._sfp_enabled.setChecked(t["sfp"].get("enabled", True))
                self._sfp_wick_body_ratio.setValue(t["sfp"].get("wick_body_ratio", 2.0))
                self._sfp_penetration.setValue(t["sfp"].get("min_penetration_atr", 0.2))

        if "stop_loss" in settings:
            sl = settings["stop_loss"]
            sl_types = {"atr": 0, "percent": 1, "structure": 2}
            self._sl_type.setCurrentIndex(sl_types.get(sl.get("type", "atr"), 0))
            self._sl_atr_mult.setValue(sl.get("atr_multiplier", 1.5))
            self._sl_percent.setValue(sl.get("percent", 2.0))
            self._sl_structure_buffer.setValue(sl.get("structure_buffer_atr", 0.2))

        if "take_profit" in settings:
            tp = settings["take_profit"]
            self._tp_rr_ratio.setValue(tp.get("rr_ratio", 2.0))
            self._tp_atr_mult.setValue(tp.get("atr_multiplier", 3.0))
            self._tp_use_level.setChecked(tp.get("use_level", True))

        if "trailing" in settings:
            tr = settings["trailing"]
            self._trailing_enabled.setChecked(tr.get("enabled", True))
            self._trailing_activation.setValue(tr.get("activation_r", 1.0))
            self._trailing_distance.setValue(tr.get("distance_atr", 0.5))
            self._trailing_step.setValue(tr.get("step_atr", 0.2))
            self._trailing_move_to_be.setChecked(tr.get("move_to_be", True))

        if "time_stop" in settings:
            ts = settings["time_stop"]
            self._time_stop_enabled.setChecked(ts.get("enabled", False))
            self._max_hold_hours.setValue(ts.get("max_hold_hours", 24))

        if "partial_tp" in settings:
            pt = settings["partial_tp"]
            self._partial_tp_enabled.setChecked(pt.get("enabled", True))
            self._partial_tp1_r.setValue(pt.get("tp1_r", 1.0))
            self._partial_tp1_size.setValue(pt.get("tp1_size_percent", 50))
            self._move_sl_after_tp1.setChecked(pt.get("move_sl_after_tp1", True))

    def _load_settings(self) -> None:
        """Load settings from config file."""
        try:
            if DEFAULT_CONFIG_PATH.exists():
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    settings = json.load(f)
                self.set_settings(settings)
                logger.info("Trigger/Exit settings loaded from config")
        except Exception as e:
            logger.warning(f"Failed to load trigger/exit settings: {e}")

    def _apply_settings(self) -> None:
        """Apply settings to engine."""
        settings = self.get_settings()

        try:
            from src.core.trading_bot import get_trigger_exit_engine

            engine = get_trigger_exit_engine()
            engine.update_config_from_dict(settings)
            logger.info("Trigger/Exit settings applied")

            QMessageBox.information(
                self, "Erfolg", "Einstellungen wurden übernommen."
            )
        except Exception as e:
            logger.error(f"Failed to apply trigger/exit settings: {e}")
            QMessageBox.critical(
                self, "Fehler", f"Einstellungen konnten nicht übernommen werden:\n{e}"
            )

    def _save_settings(self) -> None:
        """Save settings to config file."""
        settings = self.get_settings()

        try:
            DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(DEFAULT_CONFIG_PATH, "w") as f:
                json.dump(settings, f, indent=2)

            self._apply_settings()
            self.settings_saved.emit()
            logger.info(f"Trigger/Exit settings saved to {DEFAULT_CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to save trigger/exit settings: {e}")
            QMessageBox.critical(
                self, "Fehler", f"Einstellungen konnten nicht gespeichert werden:\n{e}"
            )

    def _reset_to_defaults(self) -> None:
        """Reset to default settings."""
        defaults = {
            "triggers": {
                "breakout": {"enabled": True, "volume_multiplier": 1.5, "close_threshold_atr": 0.5},
                "pullback": {"enabled": True, "max_distance_atr": 1.0, "rejection_wick_atr": 0.3},
                "sfp": {"enabled": True, "wick_body_ratio": 2.0, "min_penetration_atr": 0.2},
            },
            "stop_loss": {"type": "atr", "atr_multiplier": 1.5, "percent": 2.0, "structure_buffer_atr": 0.2},
            "take_profit": {"rr_ratio": 2.0, "atr_multiplier": 3.0, "use_level": True},
            "trailing": {"enabled": True, "activation_r": 1.0, "distance_atr": 0.5, "step_atr": 0.2, "move_to_be": True},
            "time_stop": {"enabled": False, "max_hold_hours": 24},
            "partial_tp": {"enabled": True, "tp1_r": 1.0, "tp1_size_percent": 50, "move_sl_after_tp1": True},
        }
        self.set_settings(defaults)
        self._emit_settings_changed()
        logger.info("Trigger/Exit settings reset to defaults")
