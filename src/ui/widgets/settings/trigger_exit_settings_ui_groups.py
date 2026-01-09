"""Trigger/Exit Settings UI Groups - UI Component Creation.

Refactored from trigger_exit_settings_widget.py.

Contains all 8 _create_*_group methods:
- Breakout, Pullback, SFP triggers
- SL, TP, Trailing, Time, Partial TP
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
)

if TYPE_CHECKING:
    from .trigger_exit_settings_widget import TriggerExitSettingsWidget


class TriggerExitSettingsUIGroups:
    """Helper for UI group creation."""

    def __init__(self, parent: TriggerExitSettingsWidget):
        self.parent = parent

    def create_breakout_group(self) -> QGroupBox:
        """Create breakout trigger settings."""
        group = QGroupBox("Breakout Trigger")
        layout = QFormLayout(group)

        self.parent._breakout_enabled = QCheckBox("Aktiviert")
        self.parent._breakout_enabled.setChecked(True)
        layout.addRow(self.parent._breakout_enabled)

        self.parent._breakout_volume_mult = QDoubleSpinBox()
        self.parent._breakout_volume_mult.setRange(1.0, 5.0)
        self.parent._breakout_volume_mult.setValue(1.5)
        self.parent._breakout_volume_mult.setSingleStep(0.1)
        self.parent._breakout_volume_mult.setDecimals(1)
        self.parent._breakout_volume_mult.setSuffix("x")
        self.parent._breakout_volume_mult.setToolTip("Volume muss X mal höher als Average sein.")
        layout.addRow("Volume Multiplikator:", self.parent._breakout_volume_mult)

        self.parent._breakout_close_threshold = QDoubleSpinBox()
        self.parent._breakout_close_threshold.setRange(0.1, 2.0)
        self.parent._breakout_close_threshold.setValue(0.5)
        self.parent._breakout_close_threshold.setSingleStep(0.1)
        self.parent._breakout_close_threshold.setDecimals(1)
        self.parent._breakout_close_threshold.setSuffix("% ATR")
        self.parent._breakout_close_threshold.setToolTip("Close muss X% ATR über Level sein.")
        layout.addRow("Close Threshold:", self.parent._breakout_close_threshold)

        return group

    def create_pullback_group(self) -> QGroupBox:
        """Create pullback trigger settings."""
        group = QGroupBox("Pullback Trigger")
        layout = QFormLayout(group)

        self.parent._pullback_enabled = QCheckBox("Aktiviert")
        self.parent._pullback_enabled.setChecked(True)
        layout.addRow(self.parent._pullback_enabled)

        self.parent._pullback_max_distance = QDoubleSpinBox()
        self.parent._pullback_max_distance.setRange(0.5, 3.0)
        self.parent._pullback_max_distance.setValue(1.0)
        self.parent._pullback_max_distance.setSingleStep(0.1)
        self.parent._pullback_max_distance.setDecimals(1)
        self.parent._pullback_max_distance.setSuffix("x ATR")
        self.parent._pullback_max_distance.setToolTip("Max Distanz zum Level für Pullback.")
        layout.addRow("Max Distanz:", self.parent._pullback_max_distance)

        self.parent._pullback_rejection_wick = QDoubleSpinBox()
        self.parent._pullback_rejection_wick.setRange(0.1, 1.0)
        self.parent._pullback_rejection_wick.setValue(0.3)
        self.parent._pullback_rejection_wick.setSingleStep(0.05)
        self.parent._pullback_rejection_wick.setDecimals(2)
        self.parent._pullback_rejection_wick.setSuffix("x ATR")
        self.parent._pullback_rejection_wick.setToolTip("Min Wick-Größe für Rejection.")
        layout.addRow("Rejection Wick:", self.parent._pullback_rejection_wick)

        return group

    def create_sfp_group(self) -> QGroupBox:
        """Create SFP trigger settings."""
        group = QGroupBox("Swing Failure Pattern (SFP)")
        layout = QFormLayout(group)

        self.parent._sfp_enabled = QCheckBox("Aktiviert")
        self.parent._sfp_enabled.setChecked(True)
        layout.addRow(self.parent._sfp_enabled)

        self.parent._sfp_wick_body_ratio = QDoubleSpinBox()
        self.parent._sfp_wick_body_ratio.setRange(0.5, 5.0)
        self.parent._sfp_wick_body_ratio.setValue(2.0)
        self.parent._sfp_wick_body_ratio.setSingleStep(0.5)
        self.parent._sfp_wick_body_ratio.setDecimals(1)
        self.parent._sfp_wick_body_ratio.setSuffix("x")
        self.parent._sfp_wick_body_ratio.setToolTip("Min Verhältnis Wick zu Body.")
        layout.addRow("Wick/Body Ratio:", self.parent._sfp_wick_body_ratio)

        self.parent._sfp_penetration = QDoubleSpinBox()
        self.parent._sfp_penetration.setRange(0.0, 1.0)
        self.parent._sfp_penetration.setValue(0.2)
        self.parent._sfp_penetration.setSingleStep(0.05)
        self.parent._sfp_penetration.setDecimals(2)
        self.parent._sfp_penetration.setSuffix("% ATR")
        self.parent._sfp_penetration.setToolTip("Min Penetration durch Level.")
        layout.addRow("Min Penetration:", self.parent._sfp_penetration)

        return group

    def create_sl_group(self) -> QGroupBox:
        """Create stop loss settings."""
        group = QGroupBox("Stop Loss")
        layout = QFormLayout(group)

        # SL Type
        self.parent._sl_type = QComboBox()
        self.parent._sl_type.addItems(["ATR-basiert", "Percent-basiert", "Struktur-basiert"])
        self.parent._sl_type.setToolTip("Art der SL-Berechnung.")
        layout.addRow("SL Typ:", self.parent._sl_type)

        # ATR SL
        self.parent._sl_atr_mult = QDoubleSpinBox()
        self.parent._sl_atr_mult.setRange(0.5, 5.0)
        self.parent._sl_atr_mult.setValue(1.2)  # Micro-Account: enger SL
        self.parent._sl_atr_mult.setSingleStep(0.1)
        self.parent._sl_atr_mult.setDecimals(1)
        self.parent._sl_atr_mult.setSuffix("x ATR")
        self.parent._sl_atr_mult.setToolTip("SL Distanz als Vielfaches von ATR.")
        layout.addRow("ATR Multiplikator:", self.parent._sl_atr_mult)

        # Percent SL
        self.parent._sl_percent = QDoubleSpinBox()
        self.parent._sl_percent.setRange(0.1, 10.0)
        self.parent._sl_percent.setValue(1.5)  # Micro-Account: enger SL
        self.parent._sl_percent.setSingleStep(0.5)
        self.parent._sl_percent.setDecimals(1)
        self.parent._sl_percent.setSuffix("%")
        self.parent._sl_percent.setToolTip("SL Distanz als Prozentsatz.")
        layout.addRow("Percent SL:", self.parent._sl_percent)

        # Structure buffer
        self.parent._sl_structure_buffer = QDoubleSpinBox()
        self.parent._sl_structure_buffer.setRange(0.0, 1.0)
        self.parent._sl_structure_buffer.setValue(0.2)
        self.parent._sl_structure_buffer.setSingleStep(0.05)
        self.parent._sl_structure_buffer.setDecimals(2)
        self.parent._sl_structure_buffer.setSuffix("x ATR")
        self.parent._sl_structure_buffer.setToolTip("Buffer unter/über Struktur-Level.")
        layout.addRow("Struktur Buffer:", self.parent._sl_structure_buffer)

        return group

    def create_tp_group(self) -> QGroupBox:
        """Create take profit settings."""
        group = QGroupBox("Take Profit")
        layout = QFormLayout(group)

        # Risk/Reward Target
        self.parent._tp_rr_ratio = QDoubleSpinBox()
        self.parent._tp_rr_ratio.setRange(1.0, 10.0)
        self.parent._tp_rr_ratio.setValue(1.5)  # Micro-Account: realistisches RR
        self.parent._tp_rr_ratio.setSingleStep(0.5)
        self.parent._tp_rr_ratio.setDecimals(1)
        self.parent._tp_rr_ratio.setPrefix("1:")
        self.parent._tp_rr_ratio.setToolTip("Risk/Reward Ratio für TP.")
        layout.addRow("R:R Ratio:", self.parent._tp_rr_ratio)

        # ATR TP
        self.parent._tp_atr_mult = QDoubleSpinBox()
        self.parent._tp_atr_mult.setRange(1.0, 10.0)
        self.parent._tp_atr_mult.setValue(3.0)
        self.parent._tp_atr_mult.setSingleStep(0.5)
        self.parent._tp_atr_mult.setDecimals(1)
        self.parent._tp_atr_mult.setSuffix("x ATR")
        self.parent._tp_atr_mult.setToolTip("TP Distanz als Vielfaches von ATR.")
        layout.addRow("ATR Multiplikator:", self.parent._tp_atr_mult)

        # Use level as TP
        self.parent._tp_use_level = QCheckBox("Level als TP verwenden")
        self.parent._tp_use_level.setChecked(True)
        self.parent._tp_use_level.setToolTip("Nächstes Resistance/Support Level als TP.")
        layout.addRow(self.parent._tp_use_level)

        return group

    def create_trailing_group(self) -> QGroupBox:
        """Create trailing stop settings."""
        group = QGroupBox("Trailing Stop")
        layout = QFormLayout(group)

        self.parent._trailing_enabled = QCheckBox("Aktiviert")
        self.parent._trailing_enabled.setChecked(True)
        layout.addRow(self.parent._trailing_enabled)

        # Activation threshold
        self.parent._trailing_activation = QDoubleSpinBox()
        self.parent._trailing_activation.setRange(0.5, 5.0)
        self.parent._trailing_activation.setValue(0.5)  # Micro-Account: früher aktivieren
        self.parent._trailing_activation.setSingleStep(0.1)
        self.parent._trailing_activation.setDecimals(1)
        self.parent._trailing_activation.setSuffix("x R")
        self.parent._trailing_activation.setToolTip("Profit-Distanz für Trailing-Aktivierung (in R).")
        layout.addRow("Aktivierung bei:", self.parent._trailing_activation)

        # Trailing distance
        self.parent._trailing_distance = QDoubleSpinBox()
        self.parent._trailing_distance.setRange(0.3, 2.0)
        self.parent._trailing_distance.setValue(0.3)  # Micro-Account: enger Trailing
        self.parent._trailing_distance.setSingleStep(0.1)
        self.parent._trailing_distance.setDecimals(1)
        self.parent._trailing_distance.setSuffix("x ATR")
        self.parent._trailing_distance.setToolTip("Trailing-Distanz zum Preis.")
        layout.addRow("Trailing Distanz:", self.parent._trailing_distance)

        # Step size
        self.parent._trailing_step = QDoubleSpinBox()
        self.parent._trailing_step.setRange(0.1, 1.0)
        self.parent._trailing_step.setValue(0.2)
        self.parent._trailing_step.setSingleStep(0.05)
        self.parent._trailing_step.setDecimals(2)
        self.parent._trailing_step.setSuffix("x ATR")
        self.parent._trailing_step.setToolTip("Minimale Schrittweite für Trailing-Update.")
        layout.addRow("Step Size:", self.parent._trailing_step)

        # Move to BE
        self.parent._trailing_move_to_be = QCheckBox("Move to Break-Even bei 1R")
        self.parent._trailing_move_to_be.setChecked(True)
        layout.addRow(self.parent._trailing_move_to_be)

        return group

    def create_time_group(self) -> QGroupBox:
        """Create time stop settings."""
        group = QGroupBox("Time Stop")
        layout = QFormLayout(group)

        self.parent._time_stop_enabled = QCheckBox("Aktiviert")
        self.parent._time_stop_enabled.setChecked(False)
        layout.addRow(self.parent._time_stop_enabled)

        self.parent._max_hold_hours = QSpinBox()
        self.parent._max_hold_hours.setRange(1, 168)  # Up to 1 week
        self.parent._max_hold_hours.setValue(24)
        self.parent._max_hold_hours.setSuffix(" Stunden")
        self.parent._max_hold_hours.setToolTip("Maximale Haltezeit.")
        layout.addRow("Max. Haltezeit:", self.parent._max_hold_hours)

        return group

    def create_partial_tp_group(self) -> QGroupBox:
        """Create partial take profit settings."""
        group = QGroupBox("Partial Take Profit")
        layout = QFormLayout(group)

        self.parent._partial_tp_enabled = QCheckBox("Aktiviert")
        self.parent._partial_tp_enabled.setChecked(True)
        layout.addRow(self.parent._partial_tp_enabled)

        self.parent._partial_tp1_r = QDoubleSpinBox()
        self.parent._partial_tp1_r.setRange(0.5, 3.0)
        self.parent._partial_tp1_r.setValue(1.0)
        self.parent._partial_tp1_r.setSingleStep(0.25)
        self.parent._partial_tp1_r.setDecimals(2)
        self.parent._partial_tp1_r.setPrefix("TP1 bei ")
        self.parent._partial_tp1_r.setSuffix("R")
        self.parent._partial_tp1_r.setToolTip("Erster Teilverkauf bei X R.")
        layout.addRow(self.parent._partial_tp1_r)

        self.parent._partial_tp1_size = QSpinBox()
        self.parent._partial_tp1_size.setRange(10, 90)
        self.parent._partial_tp1_size.setValue(50)
        self.parent._partial_tp1_size.setSuffix("%")
        self.parent._partial_tp1_size.setToolTip("Anteil der Position beim TP1.")
        layout.addRow("TP1 Größe:", self.parent._partial_tp1_size)

        self.parent._move_sl_after_tp1 = QCheckBox("SL → Break-Even nach TP1")
        self.parent._move_sl_after_tp1.setChecked(True)
        layout.addRow(self.parent._move_sl_after_tp1)

        return group
