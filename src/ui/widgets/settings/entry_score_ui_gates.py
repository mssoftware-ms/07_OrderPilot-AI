"""
Entry Score UI - Regime Gates Group.

Refactored from entry_score_settings_widget.py.

Contains:
- _create_gates_group: Creates UI for regime gates settings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QGroupBox,
    QFormLayout,
    QLabel,
    QCheckBox,
    QDoubleSpinBox,
)

if TYPE_CHECKING:
    from .entry_score_settings_widget import EntryScoreSettingsWidget


class EntryScoreUIGates:
    """Helper for creating regime gates UI group."""

    def __init__(self, parent: EntryScoreSettingsWidget):
        self.parent = parent

    def create_gates_group(self) -> QGroupBox:
        """Create regime gate settings group."""
        group = QGroupBox("Regime Gates")
        layout = QFormLayout(group)

        # Info
        info = QLabel("Gates können Entries blockieren oder Score modifizieren:")
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(info)

        # Block in CHOP
        self.parent._block_in_chop = QCheckBox("Block bei CHOP/RANGE Regime")
        self.parent._block_in_chop.setChecked(False)  # Micro-Account: auch in Chop traden
        self.parent._block_in_chop.setToolTip(
            "Blockiert Market-Entries wenn Markt in Seitwärtsbewegung ist."
        )
        layout.addRow(self.parent._block_in_chop)

        # Block against trend
        self.parent._block_against_trend = QCheckBox("Block gegen Strong Trend")
        self.parent._block_against_trend.setChecked(True)
        self.parent._block_against_trend.setToolTip(
            "Blockiert Long-Entries bei STRONG_TREND_BEAR und umgekehrt."
        )
        layout.addRow(self.parent._block_against_trend)

        # Allow SFP counter-trend
        self.parent._allow_sfp_counter = QCheckBox("SFP Counter-Trend erlauben")
        self.parent._allow_sfp_counter.setChecked(True)
        self.parent._allow_sfp_counter.setToolTip(
            "Erlaubt Swing Failure Pattern auch gegen den Trend."
        )
        layout.addRow(self.parent._allow_sfp_counter)

        # Boost modifier
        self.parent._boost_modifier = QDoubleSpinBox()
        self.parent._boost_modifier.setRange(0.0, 0.5)
        self.parent._boost_modifier.setValue(0.10)
        self.parent._boost_modifier.setSingleStep(0.05)
        self.parent._boost_modifier.setDecimals(2)
        self.parent._boost_modifier.setPrefix("+")
        self.parent._boost_modifier.setToolTip(
            "Score-Bonus bei aligned Strong Trend."
        )
        layout.addRow("Boost bei aligned Trend:", self.parent._boost_modifier)

        # Chop penalty
        self.parent._chop_penalty = QDoubleSpinBox()
        self.parent._chop_penalty.setRange(0.0, 0.5)
        self.parent._chop_penalty.setValue(0.10)  # Micro-Account: weniger Strafe
        self.parent._chop_penalty.setSingleStep(0.05)
        self.parent._chop_penalty.setDecimals(2)
        self.parent._chop_penalty.setPrefix("-")
        self.parent._chop_penalty.setToolTip(
            "Score-Reduktion bei CHOP Regime (wenn nicht blockiert)."
        )
        layout.addRow("Penalty bei CHOP:", self.parent._chop_penalty)

        # Volatile penalty
        self.parent._volatile_penalty = QDoubleSpinBox()
        self.parent._volatile_penalty.setRange(0.0, 0.5)
        self.parent._volatile_penalty.setValue(0.10)
        self.parent._volatile_penalty.setSingleStep(0.05)
        self.parent._volatile_penalty.setDecimals(2)
        self.parent._volatile_penalty.setPrefix("-")
        self.parent._volatile_penalty.setToolTip(
            "Score-Reduktion bei VOLATILITY_EXPLOSIVE Regime."
        )
        layout.addRow("Penalty bei Volatile:", self.parent._volatile_penalty)

        return group
