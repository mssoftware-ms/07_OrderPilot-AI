"""LLM Validation Settings Widget."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QGroupBox,
    QCheckBox,
)

from src.core.trading_bot import (
    load_llm_validation_config,
    save_llm_validation_config,
)


class LLMValidationSettingsWidget(QWidget):
    """Settings widget for LLM Validation Service."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Quick Analysis Thresholds
        quick_group = QGroupBox("Quick Analysis Thresholds")
        quick_layout = QFormLayout(quick_group)

        self.quick_approve = QSpinBox()
        self.quick_approve.setRange(0, 100)
        self.quick_approve.setValue(75)
        self.quick_approve.setToolTip("Score >= this: Approve immediately")
        quick_layout.addRow("Approve (≥):", self.quick_approve)

        self.quick_deep = QSpinBox()
        self.quick_deep.setRange(0, 100)
        self.quick_deep.setValue(50)
        self.quick_deep.setToolTip("Score between deep and approve: Deep analysis")
        quick_layout.addRow("Deep Analysis (≥):", self.quick_deep)

        self.quick_veto = QSpinBox()
        self.quick_veto.setRange(0, 100)
        self.quick_veto.setValue(50)
        self.quick_veto.setToolTip("Score < this: Veto")
        quick_layout.addRow("Veto (<):", self.quick_veto)

        layout.addWidget(quick_group)

        # Score Modifiers
        modifiers_group = QGroupBox("Score Modifiers")
        modifiers_layout = QFormLayout(modifiers_group)

        self.boost_modifier = QDoubleSpinBox()
        self.boost_modifier.setRange(-1.0, 1.0)
        self.boost_modifier.setSingleStep(0.05)
        self.boost_modifier.setValue(0.15)
        self.boost_modifier.setToolTip("+15% on boost recommendation")
        modifiers_layout.addRow("Boost Modifier:", self.boost_modifier)

        self.caution_modifier = QDoubleSpinBox()
        self.caution_modifier.setRange(-1.0, 1.0)
        self.caution_modifier.setSingleStep(0.05)
        self.caution_modifier.setValue(-0.10)
        self.caution_modifier.setToolTip("-10% on caution recommendation")
        modifiers_layout.addRow("Caution Modifier:", self.caution_modifier)

        self.veto_modifier = QDoubleSpinBox()
        self.veto_modifier.setRange(-1.0, 0.0)
        self.veto_modifier.setSingleStep(0.1)
        self.veto_modifier.setValue(-1.0)
        self.veto_modifier.setToolTip("-100% blocks entry")
        modifiers_layout.addRow("Veto Modifier:", self.veto_modifier)

        layout.addWidget(modifiers_group)

        # Enable/Disable
        self.enabled = QCheckBox("Enable LLM Validation")
        self.enabled.setChecked(True)
        layout.addWidget(self.enabled)

        self.fallback = QCheckBox("Fallback to Technical on Error")
        self.fallback.setChecked(True)
        layout.addWidget(self.fallback)

        layout.addStretch()

    def load_settings(self) -> None:
        """Load settings from config file."""
        config = load_llm_validation_config()

        # Quick thresholds (using actual attribute names from LLMValidationConfig)
        self.quick_approve.setValue(config.quick_approve_threshold)
        self.quick_deep.setValue(config.quick_deep_threshold)
        self.quick_veto.setValue(config.quick_veto_threshold)

        # Score modifiers
        self.boost_modifier.setValue(config.boost_score_modifier)
        self.caution_modifier.setValue(config.caution_score_modifier)
        self.veto_modifier.setValue(config.veto_score_modifier)

        # Enabled
        self.enabled.setChecked(config.enabled)
        self.fallback.setChecked(config.fallback_to_technical)

    def apply_settings(self) -> None:
        """Apply settings."""
        config = load_llm_validation_config()

        config.quick_approve_threshold = self.quick_approve.value()
        config.quick_deep_threshold = self.quick_deep.value()
        config.quick_veto_threshold = self.quick_veto.value()

        config.boost_score_modifier = self.boost_modifier.value()
        config.caution_score_modifier = self.caution_modifier.value()
        config.veto_score_modifier = self.veto_modifier.value()

        config.enabled = self.enabled.isChecked()
        config.fallback_to_technical = self.fallback.isChecked()

        save_llm_validation_config(config)

    def save_settings(self) -> None:
        """Save settings to config file."""
        self.apply_settings()
