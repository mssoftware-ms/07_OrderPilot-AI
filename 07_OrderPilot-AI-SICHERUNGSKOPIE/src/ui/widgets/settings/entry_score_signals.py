"""
Entry Score Signals - Signal Connection Logic.

Refactored from entry_score_settings_widget.py.

Contains:
- connect_signals: Connects all widget change signals
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entry_score_settings_widget import EntryScoreSettingsWidget


class EntryScoreSignals:
    """Helper for connecting widget signals."""

    def __init__(self, parent: EntryScoreSettingsWidget):
        self.parent = parent

    def connect_signals(self) -> None:
        """Connect change signals."""
        # Weight spinboxes
        weight_spinboxes = [
            self.parent._weight_trend,
            self.parent._weight_rsi,
            self.parent._weight_macd,
            self.parent._weight_adx,
            self.parent._weight_volatility,
            self.parent._weight_volume,
        ]

        for spinbox in weight_spinboxes:
            spinbox.valueChanged.connect(self.parent._validation.on_weight_changed)
            spinbox.valueChanged.connect(self.parent._validation.emit_settings_changed)

        # Other spinboxes
        other_spinboxes = [
            self.parent._threshold_excellent,
            self.parent._threshold_good,
            self.parent._threshold_moderate,
            self.parent._threshold_weak,
            self.parent._boost_modifier,
            self.parent._chop_penalty,
            self.parent._volatile_penalty,
            self.parent._min_score_entry,
        ]

        for spinbox in other_spinboxes:
            spinbox.valueChanged.connect(self.parent._validation.emit_settings_changed)

        # Checkboxes
        checkboxes = [
            self.parent._block_in_chop,
            self.parent._block_against_trend,
            self.parent._allow_sfp_counter,
        ]

        for checkbox in checkboxes:
            checkbox.stateChanged.connect(self.parent._validation.emit_settings_changed)
