"""Leverage Settings Widget."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QGroupBox,
)

from src.core.trading_bot import (
    load_leverage_config,
    save_leverage_config,
)


class LeverageSettingsWidget(QWidget):
    """Settings widget for Leverage Rules Engine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Base Leverage by Tier
        tier_group = QGroupBox("Base Leverage by Asset Tier")
        tier_layout = QFormLayout(tier_group)

        self.tier_s_leverage = QDoubleSpinBox()
        self.tier_s_leverage.setRange(1, 50)
        self.tier_s_leverage.setValue(10)
        self.tier_s_leverage.setSuffix("x")
        tier_layout.addRow("Tier S (BTC, ETH):", self.tier_s_leverage)

        self.tier_a_leverage = QDoubleSpinBox()
        self.tier_a_leverage.setRange(1, 30)
        self.tier_a_leverage.setValue(7)
        self.tier_a_leverage.setSuffix("x")
        tier_layout.addRow("Tier A (Top 10):", self.tier_a_leverage)

        self.tier_b_leverage = QDoubleSpinBox()
        self.tier_b_leverage.setRange(1, 20)
        self.tier_b_leverage.setValue(5)
        self.tier_b_leverage.setSuffix("x")
        tier_layout.addRow("Tier B (Top 50):", self.tier_b_leverage)

        self.tier_c_leverage = QDoubleSpinBox()
        self.tier_c_leverage.setRange(1, 10)
        self.tier_c_leverage.setValue(3)
        self.tier_c_leverage.setSuffix("x")
        tier_layout.addRow("Tier C (Others):", self.tier_c_leverage)

        layout.addWidget(tier_group)

        # Regime Modifiers
        regime_group = QGroupBox("Regime Modifiers")
        regime_layout = QFormLayout(regime_group)

        self.trend_mod = QDoubleSpinBox()
        self.trend_mod.setRange(0.5, 2.0)
        self.trend_mod.setSingleStep(0.1)
        self.trend_mod.setValue(1.2)
        self.trend_mod.setSuffix("x")
        regime_layout.addRow("Strong Trend:", self.trend_mod)

        self.chop_mod = QDoubleSpinBox()
        self.chop_mod.setRange(0.1, 1.0)
        self.chop_mod.setSingleStep(0.1)
        self.chop_mod.setValue(0.7)
        self.chop_mod.setSuffix("x")
        regime_layout.addRow("Chop/Range:", self.chop_mod)

        self.volatile_mod = QDoubleSpinBox()
        self.volatile_mod.setRange(0.3, 1.0)
        self.volatile_mod.setSingleStep(0.1)
        self.volatile_mod.setValue(0.5)
        self.volatile_mod.setSuffix("x")
        regime_layout.addRow("Volatile:", self.volatile_mod)

        layout.addWidget(regime_group)
        layout.addStretch()

    def load_settings(self) -> None:
        """Load settings from config file."""
        config = load_leverage_config()

        # Tier Leverage (using actual attribute names from LeverageRulesConfig)
        self.tier_s_leverage.setValue(config.max_leverage_tier_1)  # BTC/ETH
        self.tier_a_leverage.setValue(config.max_leverage_tier_2)  # Major alts
        self.tier_b_leverage.setValue(config.max_leverage_tier_3)  # Mid-cap
        self.tier_c_leverage.setValue(config.max_leverage_tier_4)  # Small-cap

        # Regime Modifiers
        self.trend_mod.setValue(config.regime_multiplier_strong_trend)
        self.chop_mod.setValue(config.regime_multiplier_chop)
        self.volatile_mod.setValue(config.regime_multiplier_volatile)

    def apply_settings(self) -> None:
        """Apply settings."""
        config = load_leverage_config()

        config.max_leverage_tier_1 = int(self.tier_s_leverage.value())
        config.max_leverage_tier_2 = int(self.tier_a_leverage.value())
        config.max_leverage_tier_3 = int(self.tier_b_leverage.value())
        config.max_leverage_tier_4 = int(self.tier_c_leverage.value())

        config.regime_multiplier_strong_trend = self.trend_mod.value()
        config.regime_multiplier_chop = self.chop_mod.value()
        config.regime_multiplier_volatile = self.volatile_mod.value()

        save_leverage_config(config)

    def save_settings(self) -> None:
        """Save settings to config file."""
        self.apply_settings()
