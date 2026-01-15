"""
Entry Score UI - Component Weights Group.

Refactored from entry_score_settings_widget.py.

Contains:
- _create_weights_group: Creates UI for 6 component weights
- Weight sum indicator (label + progress bar)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QGroupBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QProgressBar,
)

if TYPE_CHECKING:
    from .entry_score_settings_widget import EntryScoreSettingsWidget


class EntryScoreUIWeights:
    """Helper for creating component weights UI group."""

    def __init__(self, parent: EntryScoreSettingsWidget):
        self.parent = parent

    def create_weights_group(self) -> QGroupBox:
        """Create component weights settings group."""
        group = QGroupBox("Komponenten-Gewichte (Summe = 1.0)")
        layout = QFormLayout(group)

        # Weight sum indicator
        self.parent._weight_sum_label = QLabel("Summe: 1.00")
        self.parent._weight_sum_bar = QProgressBar()
        self.parent._weight_sum_bar.setRange(0, 100)
        self.parent._weight_sum_bar.setValue(100)
        self.parent._weight_sum_bar.setTextVisible(False)
        self.parent._weight_sum_bar.setFixedHeight(8)

        sum_layout = QHBoxLayout()
        sum_layout.addWidget(self.parent._weight_sum_label)
        sum_layout.addWidget(self.parent._weight_sum_bar, 1)
        layout.addRow(sum_layout)

        # Trend Alignment Weight
        self.parent._weight_trend = QDoubleSpinBox()
        self.parent._weight_trend.setRange(0.0, 1.0)
        self.parent._weight_trend.setValue(0.25)
        self.parent._weight_trend.setSingleStep(0.05)
        self.parent._weight_trend.setDecimals(2)
        self.parent._weight_trend.setToolTip(
            "Gewicht für Trend-Alignment (EMA-Stack, Preis über/unter EMAs)."
        )
        layout.addRow("Trend Alignment:", self.parent._weight_trend)

        # RSI Weight
        self.parent._weight_rsi = QDoubleSpinBox()
        self.parent._weight_rsi.setRange(0.0, 1.0)
        self.parent._weight_rsi.setValue(0.15)
        self.parent._weight_rsi.setSingleStep(0.05)
        self.parent._weight_rsi.setDecimals(2)
        self.parent._weight_rsi.setToolTip(
            "Gewicht für RSI (Oversold/Overbought + Neutral Zone)."
        )
        layout.addRow("RSI:", self.parent._weight_rsi)

        # MACD Weight
        self.parent._weight_macd = QDoubleSpinBox()
        self.parent._weight_macd.setRange(0.0, 1.0)
        self.parent._weight_macd.setValue(0.20)
        self.parent._weight_macd.setSingleStep(0.05)
        self.parent._weight_macd.setDecimals(2)
        self.parent._weight_macd.setToolTip(
            "Gewicht für MACD (Crossover, Histogram-Richtung)."
        )
        layout.addRow("MACD:", self.parent._weight_macd)

        # ADX Weight
        self.parent._weight_adx = QDoubleSpinBox()
        self.parent._weight_adx.setRange(0.0, 1.0)
        self.parent._weight_adx.setValue(0.15)
        self.parent._weight_adx.setSingleStep(0.05)
        self.parent._weight_adx.setDecimals(2)
        self.parent._weight_adx.setToolTip(
            "Gewicht für ADX (Trend-Stärke, DI+/DI- Alignment)."
        )
        layout.addRow("ADX:", self.parent._weight_adx)

        # Volatility Weight
        self.parent._weight_volatility = QDoubleSpinBox()
        self.parent._weight_volatility.setRange(0.0, 1.0)
        self.parent._weight_volatility.setValue(0.10)
        self.parent._weight_volatility.setSingleStep(0.05)
        self.parent._weight_volatility.setDecimals(2)
        self.parent._weight_volatility.setToolTip(
            "Gewicht für Volatilität (ATR-basiert, nicht zu hoch/niedrig)."
        )
        layout.addRow("Volatility:", self.parent._weight_volatility)

        # Volume Weight
        self.parent._weight_volume = QDoubleSpinBox()
        self.parent._weight_volume.setRange(0.0, 1.0)
        self.parent._weight_volume.setValue(0.15)
        self.parent._weight_volume.setSingleStep(0.05)
        self.parent._weight_volume.setDecimals(2)
        self.parent._weight_volume.setToolTip(
            "Gewicht für Volumen (Ratio zu Average, Volumentrend)."
        )
        layout.addRow("Volume:", self.parent._weight_volume)

        return group
