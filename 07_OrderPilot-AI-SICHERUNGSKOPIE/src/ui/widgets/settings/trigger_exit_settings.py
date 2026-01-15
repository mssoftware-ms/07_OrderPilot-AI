"""Trigger & Exit Settings Widget."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QComboBox,
    QGroupBox,
    QCheckBox,
)

from src.core.trading_bot import (
    load_trigger_exit_config,
    save_trigger_exit_config,
)


class TriggerExitSettingsWidget(QWidget):
    """Settings widget for Trigger & Exit Engine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # SL/TP Mode
        sltp_group = QGroupBox("Stop Loss & Take Profit")
        sltp_layout = QFormLayout(sltp_group)

        self.sl_mode = QComboBox()
        self.sl_mode.addItems(["atr", "fixed_pct", "swing"])
        sltp_layout.addRow("SL Mode:", self.sl_mode)

        self.sl_atr_mult = QDoubleSpinBox()
        self.sl_atr_mult.setRange(0.1, 10)
        self.sl_atr_mult.setSingleStep(0.1)
        self.sl_atr_mult.setValue(2.0)
        sltp_layout.addRow("SL ATR Multiplier:", self.sl_atr_mult)

        self.tp_atr_mult = QDoubleSpinBox()
        self.tp_atr_mult.setRange(0.1, 10)
        self.tp_atr_mult.setSingleStep(0.1)
        self.tp_atr_mult.setValue(3.0)
        sltp_layout.addRow("TP ATR Multiplier:", self.tp_atr_mult)

        layout.addWidget(sltp_group)

        # Trailing Stop
        trailing_group = QGroupBox("Trailing Stop")
        trailing_layout = QFormLayout(trailing_group)

        self.trailing_enabled = QCheckBox("Enable Trailing Stop")
        self.trailing_enabled.setChecked(True)
        trailing_layout.addRow(self.trailing_enabled)

        self.trailing_activation = QDoubleSpinBox()
        self.trailing_activation.setRange(0, 100)
        self.trailing_activation.setSingleStep(0.5)
        self.trailing_activation.setValue(1.5)
        self.trailing_activation.setSuffix(" x ATR")
        trailing_layout.addRow("Activation Distance:", self.trailing_activation)

        self.trailing_distance = QDoubleSpinBox()
        self.trailing_distance.setRange(0.1, 10)
        self.trailing_distance.setSingleStep(0.1)
        self.trailing_distance.setValue(1.0)
        self.trailing_distance.setSuffix(" x ATR")
        trailing_layout.addRow("Trailing Distance:", self.trailing_distance)

        layout.addWidget(trailing_group)
        layout.addStretch()

    def load_settings(self) -> None:
        """Load settings from config file."""
        config = load_trigger_exit_config()

        # SL/TP (using actual attribute names from TriggerExitConfig)
        self.sl_mode.setCurrentText(config.sl_type.replace("_based", "").upper() if hasattr(config, 'sl_type') else "ATR")
        self.sl_atr_mult.setValue(config.sl_atr_multiplier)
        self.tp_atr_mult.setValue(config.tp_atr_multiplier)

        # Trailing
        self.trailing_enabled.setChecked(config.trailing_enabled)
        self.trailing_activation.setValue(config.trailing_activation_profit_pct)
        self.trailing_distance.setValue(config.trailing_atr_multiplier)

    def apply_settings(self) -> None:
        """Apply settings."""
        config = load_trigger_exit_config()

        # Map UI mode to config type
        mode_map = {"ATR": "atr_based", "FIXED_PCT": "percent_based", "SWING": "atr_based"}
        config.sl_type = mode_map.get(self.sl_mode.currentText(), "atr_based")
        config.sl_atr_multiplier = self.sl_atr_mult.value()
        config.tp_atr_multiplier = self.tp_atr_mult.value()

        config.trailing_enabled = self.trailing_enabled.isChecked()
        config.trailing_activation_profit_pct = self.trailing_activation.value()
        config.trailing_atr_multiplier = self.trailing_distance.value()

        save_trigger_exit_config(config)

    def save_settings(self) -> None:
        """Save settings to config file."""
        self.apply_settings()
