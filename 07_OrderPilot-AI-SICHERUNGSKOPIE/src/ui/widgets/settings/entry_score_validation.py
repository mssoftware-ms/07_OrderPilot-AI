"""
Entry Score Validation - Weight Validation Logic.

Refactored from entry_score_settings_widget.py.

Contains:
- on_weight_changed: Updates weight sum display and color
- emit_settings_changed: Emits settings_changed signal
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entry_score_settings_widget import EntryScoreSettingsWidget


class EntryScoreValidation:
    """Helper for weight validation logic."""

    def __init__(self, parent: EntryScoreSettingsWidget):
        self.parent = parent

    def on_weight_changed(self) -> None:
        """Update weight sum display."""
        total = (
            self.parent._weight_trend.value()
            + self.parent._weight_rsi.value()
            + self.parent._weight_macd.value()
            + self.parent._weight_adx.value()
            + self.parent._weight_volatility.value()
            + self.parent._weight_volume.value()
        )

        self.parent._weight_sum_label.setText(f"Summe: {total:.2f}")
        self.parent._weight_sum_bar.setValue(int(total * 100))

        # Color indicator
        if abs(total - 1.0) < 0.01:
            self.parent._weight_sum_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #4CAF50; }"
            )
        else:
            self.parent._weight_sum_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #f44336; }"
            )

    def emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.parent.settings_changed.emit(self.parent._persistence.get_settings())
