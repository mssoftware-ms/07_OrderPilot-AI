"""Trigger/Exit Settings Management - Settings Getter/Setter/Signals.

Refactored from trigger_exit_settings_widget.py.

Contains:
- get_settings: Build dict from widgets
- set_settings: Apply dict to widgets
- _connect_signals: Wire up value change signals
- _emit_settings_changed: Signal emission
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .trigger_exit_settings_widget import TriggerExitSettingsWidget


class TriggerExitSettingsManagement:
    """Helper for settings management."""

    def __init__(self, parent: TriggerExitSettingsWidget):
        self.parent = parent

    def connect_signals(self) -> None:
        """Connect change signals."""
        # All widgets emit settings_changed on value change
        spinboxes = [
            self.parent._breakout_volume_mult, self.parent._breakout_close_threshold,
            self.parent._pullback_max_distance, self.parent._pullback_rejection_wick,
            self.parent._sfp_wick_body_ratio, self.parent._sfp_penetration,
            self.parent._sl_atr_mult, self.parent._sl_percent, self.parent._sl_structure_buffer,
            self.parent._tp_rr_ratio, self.parent._tp_atr_mult,
            self.parent._trailing_distance, self.parent._trailing_step,
            self.parent._max_hold_hours,
            self.parent._partial_tp1_r, self.parent._partial_tp1_size,
        ]

        for spinbox in spinboxes:
            spinbox.valueChanged.connect(self.emit_settings_changed)

        checkboxes = [
            self.parent._breakout_enabled, self.parent._pullback_enabled, self.parent._sfp_enabled,
            self.parent._tp_use_level,
            self.parent._trailing_enabled, self.parent._trailing_move_to_be,
            self.parent._time_stop_enabled,
            self.parent._partial_tp_enabled, self.parent._move_sl_after_tp1,
        ]

        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self.emit_settings_changed)

        self.parent._sl_type.currentIndexChanged.connect(self.emit_settings_changed)

    def emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.parent.settings_changed.emit(self.get_settings())

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return {
            "triggers": {
                "breakout": {
                    "enabled": self.parent._breakout_enabled.isChecked(),
                    "volume_multiplier": self.parent._breakout_volume_mult.value(),
                    "close_threshold_atr": self.parent._breakout_close_threshold.value(),
                },
                "pullback": {
                    "enabled": self.parent._pullback_enabled.isChecked(),
                    "max_distance_atr": self.parent._pullback_max_distance.value(),
                    "rejection_wick_atr": self.parent._pullback_rejection_wick.value(),
                },
                "sfp": {
                    "enabled": self.parent._sfp_enabled.isChecked(),
                    "wick_body_ratio": self.parent._sfp_wick_body_ratio.value(),
                    "min_penetration_atr": self.parent._sfp_penetration.value(),
                },
            },
            "stop_loss": {
                "type": ["atr", "percent", "structure"][self.parent._sl_type.currentIndex()],
                "atr_multiplier": self.parent._sl_atr_mult.value(),
                "percent": self.parent._sl_percent.value(),
                "structure_buffer_atr": self.parent._sl_structure_buffer.value(),
            },
            "take_profit": {
                "rr_ratio": self.parent._tp_rr_ratio.value(),
                "atr_multiplier": self.parent._tp_atr_mult.value(),
                "use_level": self.parent._tp_use_level.isChecked(),
            },
            "trailing": {
                "enabled": self.parent._trailing_enabled.isChecked(),
                "distance_atr": self.parent._trailing_distance.value(),
                "step_atr": self.parent._trailing_step.value(),
                "move_to_be": self.parent._trailing_move_to_be.isChecked(),
            },
            "time_stop": {
                "enabled": self.parent._time_stop_enabled.isChecked(),
                "max_hold_hours": self.parent._max_hold_hours.value(),
            },
            "partial_tp": {
                "enabled": self.parent._partial_tp_enabled.isChecked(),
                "tp1_r": self.parent._partial_tp1_r.value(),
                "tp1_size_percent": self.parent._partial_tp1_size.value(),
                "move_sl_after_tp1": self.parent._move_sl_after_tp1.isChecked(),
            },
        }

    def set_settings(self, settings: dict) -> None:
        """Set settings from dict."""
        if "triggers" in settings:
            t = settings["triggers"]
            if "breakout" in t:
                self.parent._breakout_enabled.setChecked(t["breakout"].get("enabled", True))
                self.parent._breakout_volume_mult.setValue(t["breakout"].get("volume_multiplier", 1.5))
                self.parent._breakout_close_threshold.setValue(t["breakout"].get("close_threshold_atr", 0.5))
            if "pullback" in t:
                self.parent._pullback_enabled.setChecked(t["pullback"].get("enabled", True))
                self.parent._pullback_max_distance.setValue(t["pullback"].get("max_distance_atr", 1.0))
                self.parent._pullback_rejection_wick.setValue(t["pullback"].get("rejection_wick_atr", 0.3))
            if "sfp" in t:
                self.parent._sfp_enabled.setChecked(t["sfp"].get("enabled", True))
                self.parent._sfp_wick_body_ratio.setValue(t["sfp"].get("wick_body_ratio", 2.0))
                self.parent._sfp_penetration.setValue(t["sfp"].get("min_penetration_atr", 0.2))

        if "stop_loss" in settings:
            sl = settings["stop_loss"]
            sl_types = {"atr": 0, "percent": 1, "structure": 2}
            self.parent._sl_type.setCurrentIndex(sl_types.get(sl.get("type", "atr"), 0))
            self.parent._sl_atr_mult.setValue(sl.get("atr_multiplier", 1.5))
            self.parent._sl_percent.setValue(sl.get("percent", 2.0))
            self.parent._sl_structure_buffer.setValue(sl.get("structure_buffer_atr", 0.2))

        if "take_profit" in settings:
            tp = settings["take_profit"]
            self.parent._tp_rr_ratio.setValue(tp.get("rr_ratio", 2.0))
            self.parent._tp_atr_mult.setValue(tp.get("atr_multiplier", 3.0))
            self.parent._tp_use_level.setChecked(tp.get("use_level", True))

        if "trailing" in settings:
            tr = settings["trailing"]
            self.parent._trailing_enabled.setChecked(tr.get("enabled", True))
            # Note: activation_r field removed per Issue #24
            self.parent._trailing_distance.setValue(tr.get("distance_atr", 0.5))
            self.parent._trailing_step.setValue(tr.get("step_atr", 0.2))
            self.parent._trailing_move_to_be.setChecked(tr.get("move_to_be", True))

        if "time_stop" in settings:
            ts = settings["time_stop"]
            self.parent._time_stop_enabled.setChecked(ts.get("enabled", False))
            self.parent._max_hold_hours.setValue(ts.get("max_hold_hours", 24))

        if "partial_tp" in settings:
            pt = settings["partial_tp"]
            self.parent._partial_tp_enabled.setChecked(pt.get("enabled", True))
            self.parent._partial_tp1_r.setValue(pt.get("tp1_r", 1.0))
            self.parent._partial_tp1_size.setValue(pt.get("tp1_size_percent", 50))
            self.parent._move_sl_after_tp1.setChecked(pt.get("move_sl_after_tp1", True))
