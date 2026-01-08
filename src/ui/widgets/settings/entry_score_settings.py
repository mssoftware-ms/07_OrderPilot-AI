"""Entry Score Settings Widget."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QGroupBox,
    QLabel,
)

from src.core.trading_bot import (
    load_entry_score_config,
    save_entry_score_config,
)


class EntryScoreSettingsWidget(QWidget):
    """Settings widget for Entry Score Engine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Component Weights
        weights_group = QGroupBox("Component Weights (sum = 1.0)")
        weights_layout = QFormLayout(weights_group)

        self.trend_weight = QDoubleSpinBox()
        self.trend_weight.setRange(0, 1)
        self.trend_weight.setSingleStep(0.05)
        self.trend_weight.setValue(0.25)
        weights_layout.addRow("Trend:", self.trend_weight)

        self.rsi_weight = QDoubleSpinBox()
        self.rsi_weight.setRange(0, 1)
        self.rsi_weight.setSingleStep(0.05)
        self.rsi_weight.setValue(0.15)
        weights_layout.addRow("RSI:", self.rsi_weight)

        self.macd_weight = QDoubleSpinBox()
        self.macd_weight.setRange(0, 1)
        self.macd_weight.setSingleStep(0.05)
        self.macd_weight.setValue(0.20)
        weights_layout.addRow("MACD:", self.macd_weight)

        self.adx_weight = QDoubleSpinBox()
        self.adx_weight.setRange(0, 1)
        self.adx_weight.setSingleStep(0.05)
        self.adx_weight.setValue(0.15)
        weights_layout.addRow("ADX:", self.adx_weight)

        self.volatility_weight = QDoubleSpinBox()
        self.volatility_weight.setRange(0, 1)
        self.volatility_weight.setSingleStep(0.05)
        self.volatility_weight.setValue(0.15)
        weights_layout.addRow("Volatility:", self.volatility_weight)

        self.volume_weight = QDoubleSpinBox()
        self.volume_weight.setRange(0, 1)
        self.volume_weight.setSingleStep(0.05)
        self.volume_weight.setValue(0.10)
        weights_layout.addRow("Volume:", self.volume_weight)

        layout.addWidget(weights_group)

        # Quality Thresholds
        thresholds_group = QGroupBox("Quality Thresholds")
        thresholds_layout = QFormLayout(thresholds_group)

        self.excellent_threshold = QDoubleSpinBox()
        self.excellent_threshold.setRange(0, 1)
        self.excellent_threshold.setSingleStep(0.05)
        self.excellent_threshold.setValue(0.75)
        thresholds_layout.addRow("Excellent (≥):", self.excellent_threshold)

        self.good_threshold = QDoubleSpinBox()
        self.good_threshold.setRange(0, 1)
        self.good_threshold.setSingleStep(0.05)
        self.good_threshold.setValue(0.60)
        thresholds_layout.addRow("Good (≥):", self.good_threshold)

        self.acceptable_threshold = QDoubleSpinBox()
        self.acceptable_threshold.setRange(0, 1)
        self.acceptable_threshold.setSingleStep(0.05)
        self.acceptable_threshold.setValue(0.40)
        thresholds_layout.addRow("Acceptable (≥):", self.acceptable_threshold)

        layout.addWidget(thresholds_group)
        layout.addStretch()

    def load_settings(self) -> None:
        """Load settings from config file."""
        config = load_entry_score_config()

        # Component Weights (using actual attribute names from EntryScoreConfig)
        self.trend_weight.setValue(config.weight_trend_alignment)
        self.rsi_weight.setValue(config.weight_momentum_rsi)
        self.macd_weight.setValue(config.weight_momentum_macd)
        self.adx_weight.setValue(config.weight_trend_strength)
        self.volatility_weight.setValue(config.weight_volatility)
        self.volume_weight.setValue(config.weight_volume)

        # Quality Thresholds
        self.excellent_threshold.setValue(config.threshold_excellent)
        self.good_threshold.setValue(config.threshold_good)
        self.acceptable_threshold.setValue(config.threshold_moderate)

    def apply_settings(self) -> None:
        """Apply settings (in-memory only, does not save to file)."""
        config = load_entry_score_config()

        # Update weights
        config.weight_trend_alignment = self.trend_weight.value()
        config.weight_momentum_rsi = self.rsi_weight.value()
        config.weight_momentum_macd = self.macd_weight.value()
        config.weight_trend_strength = self.adx_weight.value()
        config.weight_volatility = self.volatility_weight.value()
        config.weight_volume = self.volume_weight.value()

        # Update thresholds
        config.threshold_excellent = self.excellent_threshold.value()
        config.threshold_good = self.good_threshold.value()
        config.threshold_moderate = self.acceptable_threshold.value()

        save_entry_score_config(config)

    def save_settings(self) -> None:
        """Save settings to config file."""
        self.apply_settings()
