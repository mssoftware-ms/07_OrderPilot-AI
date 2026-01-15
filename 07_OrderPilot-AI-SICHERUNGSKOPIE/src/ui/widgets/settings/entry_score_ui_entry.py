"""
Entry Score UI - Entry Requirements Group.

Refactored from entry_score_settings_widget.py.

Contains:
- _create_entry_group: Creates UI for entry requirements (min score)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox,
)

if TYPE_CHECKING:
    from .entry_score_settings_widget import EntryScoreSettingsWidget


class EntryScoreUIEntry:
    """Helper for creating entry requirements UI group."""

    def __init__(self, parent: EntryScoreSettingsWidget):
        self.parent = parent

    def create_entry_group(self) -> QGroupBox:
        """Create entry requirements group."""
        group = QGroupBox("Entry Requirements")
        layout = QFormLayout(group)

        # Min score for entry
        self.parent._min_score_entry = QDoubleSpinBox()
        self.parent._min_score_entry.setRange(0.1, 0.9)
        self.parent._min_score_entry.setValue(0.45)  # Micro-Account: niedrigere Schwelle
        self.parent._min_score_entry.setSingleStep(0.05)
        self.parent._min_score_entry.setDecimals(2)
        self.parent._min_score_entry.setToolTip(
            "Minimum Entry Score für einen Trade.\n"
            "Unter diesem Wert: NO_SIGNAL."
        )
        layout.addRow("Min. Score für Entry:", self.parent._min_score_entry)

        return group
