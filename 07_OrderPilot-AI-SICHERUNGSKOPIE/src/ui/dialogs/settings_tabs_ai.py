"""Settings Tabs - AI Provider Tabs.

Refactored from 820 LOC monolith using composition pattern.

Module 6/7 of settings_tabs_mixin.py split.

Contains:
- _create_ai_tab(): Main AI settings tab with provider sub-tabs
- _build_general_ai_layout(): General AI settings (enabled, default provider, budget)
- _build_ai_provider_tabs(): Tab widget with OpenAI, Anthropic, Gemini tabs
- _build_openai_tab(): OpenAI settings with GPT-5.x reasoning effort
- _build_anthropic_tab(): Anthropic Claude settings
- _build_gemini_tab(): Google Gemini settings
- _on_openai_model_changed(): Update reasoning effort options based on model
- _on_openai_reasoning_changed(): Enable/disable sampling controls
"""

import re

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ai.model_constants import (
    AI_PROVIDERS,
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    OPENAI_MODELS,
    OPENAI_REASONING_EFFORTS,
)


class SettingsTabsAI:
    """Helper für AI Provider Tabs (OpenAI, Anthropic, Gemini)."""

    def __init__(self, parent):
        """
        Args:
            parent: SettingsDialog Instanz
        """
        self.parent = parent

    def create_ai_tab(self) -> QWidget:
        """Create AI settings tab with provider sub-tabs."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # General AI settings (enabled, default provider, budget)
        layout.addLayout(self._build_general_ai_layout())

        # Provider-specific tabs (OpenAI, Anthropic, Gemini)
        layout.addWidget(self._build_ai_provider_tabs())

        # Task routing info
        routing_info = QLabel(
            "<b>Note:</b> Task routing is configured in config/ai_providers.yaml. "
            "Different tasks can use different models automatically."
        )
        routing_info.setWordWrap(True)
        layout.addWidget(routing_info)

        layout.addStretch()

        return tab

    def _build_general_ai_layout(self) -> QFormLayout:
        """Build general AI settings layout."""
        general_ai_layout = QFormLayout()

        self.parent.ai_enabled = QCheckBox("Enable AI features")
        self.parent.ai_enabled.setChecked(True)
        general_ai_layout.addRow(self.parent.ai_enabled)

        self.parent.ai_default_provider = QComboBox()
        self.parent.ai_default_provider.addItems(AI_PROVIDERS)
        general_ai_layout.addRow("Default Provider:", self.parent.ai_default_provider)

        self.parent.ai_budget = QDoubleSpinBox()
        self.parent.ai_budget.setRange(1, 1000)
        self.parent.ai_budget.setValue(50)
        self.parent.ai_budget.setPrefix("€")
        general_ai_layout.addRow("Monthly Budget:", self.parent.ai_budget)

        return general_ai_layout

    def _build_ai_provider_tabs(self) -> QTabWidget:
        """Build AI provider tabs (OpenAI, Anthropic, Gemini)."""
        provider_tabs = QTabWidget()
        provider_tabs.addTab(self._build_openai_tab(), "OpenAI")
        provider_tabs.addTab(self._build_anthropic_tab(), "Anthropic")
        provider_tabs.addTab(self._build_gemini_tab(), "Gemini")
        return provider_tabs

    def _build_openai_tab(self) -> QWidget:
        """Build OpenAI settings tab with reasoning effort support."""
        openai_tab = QWidget()
        openai_layout = QFormLayout(openai_tab)

        # API Key
        self.parent.openai_api_key = QLineEdit()
        self.parent.openai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.openai_api_key.setPlaceholderText("Enter OpenAI API Key")
        openai_layout.addRow("API Key:", self.parent.openai_api_key)

        # Model Selection
        self.parent.openai_model = QComboBox()
        self.parent.openai_model.addItems(OPENAI_MODELS)
        self.parent.openai_model.currentTextChanged.connect(self._on_openai_model_changed)
        openai_layout.addRow("Default Model:", self.parent.openai_model)

        # Reasoning Effort (only for GPT-5.x)
        self.parent.openai_reasoning_effort = QComboBox()
        openai_layout.addRow("Reasoning Effort:", self.parent.openai_reasoning_effort)

        # Max Completion Tokens
        self.parent.openai_max_tokens = QSpinBox()
        self.parent.openai_max_tokens.setRange(100, 128000)
        self.parent.openai_max_tokens.setValue(3000)
        self.parent.openai_max_tokens.setToolTip(
            "Maximum tokens for completion (includes reasoning tokens for GPT-5.x)"
        )
        openai_layout.addRow("Max Completion Tokens:", self.parent.openai_max_tokens)

        # Temperature (only when reasoning_effort = none)
        self.parent.openai_temperature = QDoubleSpinBox()
        self.parent.openai_temperature.setRange(0.0, 2.0)
        self.parent.openai_temperature.setSingleStep(0.1)
        self.parent.openai_temperature.setValue(0.1)
        self.parent.openai_temperature.setToolTip(
            "Only active when reasoning_effort = none"
        )
        openai_layout.addRow("Temperature:", self.parent.openai_temperature)

        # Top P (only when reasoning_effort = none)
        self.parent.openai_top_p = QDoubleSpinBox()
        self.parent.openai_top_p.setRange(0.0, 1.0)
        self.parent.openai_top_p.setSingleStep(0.1)
        self.parent.openai_top_p.setValue(1.0)
        self.parent.openai_top_p.setToolTip("Only active when reasoning_effort = none")
        openai_layout.addRow("Top P:", self.parent.openai_top_p)

        # Info Label
        openai_info = QLabel(
            "<b>GPT-5.2:</b> Latest reasoning model (none|low|medium|high|xhigh)<br>"
            "<b>GPT-5.1:</b> Reasoning model (none|low|medium|high)<br>"
            "<b>GPT-4.1:</b> 1M token context, excellent for coding (no reasoning)<br>"
            "<b>GPT-4.1 Nano:</b> Fastest and cheapest<br><br>"
            "⚠️ <i>temperature/top_p only work when reasoning_effort = none</i><br>"
            "Set OPENAI_API_KEY environment variable for automatic configuration."
        )
        openai_info.setWordWrap(True)
        openai_layout.addRow(openai_info)

        # Connect reasoning effort change to update sampling controls
        self.parent.openai_reasoning_effort.currentTextChanged.connect(
            self._on_openai_reasoning_changed
        )

        return openai_tab

    def _on_openai_model_changed(self, model_text: str):
        """Update reasoning effort options based on selected model.

        Args:
            model_text: Selected model display text (e.g., "GPT-5.2 (reasoning)")
        """
        # Extract model name (remove description in parentheses)
        model_name = re.sub(r'\s*\(.*?\)\s*', '', model_text).strip()

        # Get reasoning efforts for this model
        efforts = OPENAI_REASONING_EFFORTS.get(model_name, [])

        # Update combo box
        self.parent.openai_reasoning_effort.blockSignals(True)
        self.parent.openai_reasoning_effort.clear()

        if efforts:
            # Reasoning model → populate efforts
            self.parent.openai_reasoning_effort.addItems(efforts)
            self.parent.openai_reasoning_effort.setCurrentText("medium")  # Default
            self.parent.openai_reasoning_effort.setEnabled(True)
        else:
            # Non-reasoning model → disable reasoning, enable sampling
            self.parent.openai_reasoning_effort.addItem("N/A (non-reasoning model)")
            self.parent.openai_reasoning_effort.setEnabled(False)
            self.parent.openai_temperature.setEnabled(True)
            self.parent.openai_top_p.setEnabled(True)

        self.parent.openai_reasoning_effort.blockSignals(False)
        self._on_openai_reasoning_changed(
            self.parent.openai_reasoning_effort.currentText()
        )

    def _on_openai_reasoning_changed(self, reasoning_effort: str):
        """Enable/disable sampling controls based on reasoning effort.

        Args:
            reasoning_effort: Selected reasoning effort (none|low|medium|high|xhigh)
        """
        # Temperature and top_p only work when reasoning_effort = none
        is_none = reasoning_effort == "none"
        self.parent.openai_temperature.setEnabled(is_none)
        self.parent.openai_top_p.setEnabled(is_none)

    def _build_anthropic_tab(self) -> QWidget:
        """Build Anthropic Claude settings tab."""
        anthropic_tab = QWidget()
        anthropic_layout = QFormLayout(anthropic_tab)

        # API Key
        self.parent.anthropic_api_key = QLineEdit()
        self.parent.anthropic_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.anthropic_api_key.setPlaceholderText("Enter Anthropic API Key")
        anthropic_layout.addRow("API Key:", self.parent.anthropic_api_key)

        # Model Selection
        self.parent.anthropic_model = QComboBox()
        self.parent.anthropic_model.addItems(ANTHROPIC_MODELS)
        anthropic_layout.addRow("Default Model:", self.parent.anthropic_model)

        # Info Label
        anthropic_info = QLabel(
            "Anthropic Claude Sonnet 4.5 excels at complex reasoning, code analysis, "
            "and technical tasks. 1M token context window. "
            "Set ANTHROPIC_API_KEY environment variable for automatic configuration."
        )
        anthropic_info.setWordWrap(True)
        anthropic_layout.addRow(anthropic_info)

        return anthropic_tab

    def _build_gemini_tab(self) -> QWidget:
        """Build Google Gemini settings tab."""
        gemini_tab = QWidget()
        gemini_layout = QFormLayout(gemini_tab)

        # API Key
        self.parent.gemini_api_key = QLineEdit()
        self.parent.gemini_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.gemini_api_key.setPlaceholderText("Enter Gemini API Key")
        gemini_layout.addRow("API Key:", self.parent.gemini_api_key)

        # Model Selection
        self.parent.gemini_model = QComboBox()
        self.parent.gemini_model.addItems(GEMINI_MODELS)
        gemini_layout.addRow("Default Model:", self.parent.gemini_model)

        # Info Label
        gemini_info = QLabel(
            "Google Gemini offers excellent performance at competitive pricing. "
            "gemini-2.0-flash-exp is the latest experimental model. "
            "gemini-1.5-pro has the largest context (2M tokens). "
            "Set GEMINI_API_KEY environment variable for automatic configuration."
        )
        gemini_info.setWordWrap(True)
        gemini_layout.addRow(gemini_info)

        return gemini_tab
