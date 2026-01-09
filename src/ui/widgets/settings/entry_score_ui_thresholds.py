"""
Entry Score UI - Quality Thresholds Group.

Refactored from entry_score_settings_widget.py.

Contains:
- _create_thresholds_group: Creates UI for quality thresholds
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QGroupBox,
    QFormLayout,
    QLabel,
    QDoubleSpinBox,
)

if TYPE_CHECKING:
    from .entry_score_settings_widget import EntryScoreSettingsWidget


class EntryScoreUIThresholds:
    """Helper for creating quality thresholds UI group."""

    def __init__(self, parent: EntryScoreSettingsWidget):
        self.parent = parent

    def create_thresholds_group(self) -> QGroupBox:
        """Create quality threshold settings group."""
        group = QGroupBox("Quality Thresholds")
        layout = QFormLayout(group)

        # Info
        info = QLabel("Score-Schwellenwerte für Quality-Klassifizierung:")
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(info)

        # Excellent Threshold
        self.parent._threshold_excellent = QDoubleSpinBox()
        self.parent._threshold_excellent.setRange(0.5, 1.0)
        self.parent._threshold_excellent.setValue(0.80)
        self.parent._threshold_excellent.setSingleStep(0.05)
        self.parent._threshold_excellent.setDecimals(2)
        self.parent._threshold_excellent.setToolTip("Score >= diesem Wert = EXCELLENT Quality")
        layout.addRow("EXCELLENT >=", self.parent._threshold_excellent)

        # Good Threshold
        self.parent._threshold_good = QDoubleSpinBox()
        self.parent._threshold_good.setRange(0.4, 0.9)
        self.parent._threshold_good.setValue(0.65)
        self.parent._threshold_good.setSingleStep(0.05)
        self.parent._threshold_good.setDecimals(2)
        self.parent._threshold_good.setToolTip("Score >= diesem Wert = GOOD Quality")
        layout.addRow("GOOD >=", self.parent._threshold_good)

        # Moderate Threshold
        self.parent._threshold_moderate = QDoubleSpinBox()
        self.parent._threshold_moderate.setRange(0.3, 0.8)
        self.parent._threshold_moderate.setValue(0.50)
        self.parent._threshold_moderate.setSingleStep(0.05)
        self.parent._threshold_moderate.setDecimals(2)
        self.parent._threshold_moderate.setToolTip("Score >= diesem Wert = MODERATE Quality")
        layout.addRow("MODERATE >=", self.parent._threshold_moderate)

        # Weak Threshold
        self.parent._threshold_weak = QDoubleSpinBox()
        self.parent._threshold_weak.setRange(0.1, 0.6)
        self.parent._threshold_weak.setValue(0.35)
        self.parent._threshold_weak.setSingleStep(0.05)
        self.parent._threshold_weak.setDecimals(2)
        self.parent._threshold_weak.setToolTip("Score >= diesem Wert = WEAK Quality")
        layout.addRow("WEAK >=", self.parent._threshold_weak)

        return group
