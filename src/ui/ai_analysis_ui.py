"""AI Analysis UI - UI setup methods.

Refactored from 822 LOC monolith using composition pattern.

Module 2/5 of ai_analysis_window.py split.

Contains:
- init_ui(): Main UI initialization
- init_overview_tab(): Overview tab setup
- setup_regime_info_panel(): Regime info panel
- load_settings(): Load settings from QSettings
- on_provider_changed(): Provider change handler
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QProgressBar, QFrame, QTabWidget, QWidget
)

from src.ai.model_constants import AI_PROVIDERS, OPENAI_MODELS, ANTHROPIC_MODELS, GEMINI_MODELS
from src.core.ai_analysis.prompt import PromptComposer

if TYPE_CHECKING:
    pass

analysis_logger = logging.getLogger('ai_analysis')


class AIAnalysisUI:
    """Helper für AIAnalysisWindow UI (Setup, Widgets, Tabs)."""

    def __init__(self, parent):
        """
        Args:
            parent: AIAnalysisWindow Instanz
        """
        self.parent = parent

    def init_ui(self):
        """Initialize main UI with tabs."""
        from PyQt6.QtWidgets import QVBoxLayout, QTabWidget
        from src.ui.widgets.deep_analysis_window import DeepAnalysisWidget

        main_layout = QVBoxLayout(self.parent)

        self.parent.tabs = QTabWidget()
        main_layout.addWidget(self.parent.tabs)

        # --- Tab 1: Overview (Original UI) ---
        self.parent.overview_tab = QWidget()
        self.init_overview_tab()
        self.parent.tabs.addTab(self.parent.overview_tab, "Overview")

        # --- Tab 2: Deep Analysis (New) ---
        self.parent.deep_analysis_tab = DeepAnalysisWidget()
        self.parent.tabs.addTab(self.parent.deep_analysis_tab, "Deep Analysis")

    def init_overview_tab(self):
        """Initialize overview tab UI."""
        layout = QVBoxLayout(self.parent.overview_tab)

        # --- Header ---
        header_layout = QHBoxLayout()
        self.parent.lbl_header = QLabel(f"<h2>Analysis: {self.parent.symbol}</h2>")
        header_layout.addWidget(self.parent.lbl_header)
        layout.addLayout(header_layout)

        # --- Regime Info Panel (Phase 2.2) ---
        self.setup_regime_info_panel(layout)

        # --- Controls ---
        controls_layout = QHBoxLayout()

        # Provider
        self.parent.combo_provider = QComboBox()
        self.parent.combo_provider.addItems(AI_PROVIDERS)
        self.parent.combo_provider.currentTextChanged.connect(self.on_provider_changed)
        controls_layout.addWidget(QLabel("Provider:"))
        controls_layout.addWidget(self.parent.combo_provider)

        # Model
        self.parent.combo_model = QComboBox()
        # Items populated in load_settings / on_provider_changed
        controls_layout.addWidget(QLabel("Model:"))
        controls_layout.addWidget(self.parent.combo_model)

        layout.addLayout(controls_layout)

        # --- Action ---
        action_layout = QHBoxLayout()

        self.parent.btn_analyze = QPushButton("Start Analysis")
        self.parent.btn_analyze.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; padding: 8px;")
        action_layout.addWidget(self.parent.btn_analyze)

        self.parent.btn_edit_prompt = QPushButton("Edit Prompt")
        self.parent.btn_edit_prompt.clicked.connect(self.parent._handlers.open_prompt_editor)
        action_layout.addWidget(self.parent.btn_edit_prompt)

        # Button to show full AI payload data
        self.parent.btn_show_payload = QPushButton("📋 Payload anzeigen")
        self.parent.btn_show_payload.setToolTip(
            "Zeigt alle Daten an, die bei der letzten Analyse an die KI gesendet wurden.\n"
            "Führen Sie zuerst 'Start Analysis' aus."
        )
        self.parent.btn_show_payload.setStyleSheet("padding: 8px;")
        self.parent.btn_show_payload.clicked.connect(self.parent._handlers.show_payload_popup)
        self.parent.btn_show_payload.setEnabled(False)  # Disabled until analysis is run
        action_layout.addWidget(self.parent.btn_show_payload)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # --- Progress ---
        self.parent.progress_bar = QProgressBar()
        self.parent.progress_bar.setVisible(False)
        self.parent.progress_bar.setRange(0, 0)  # Infinite loading
        layout.addWidget(self.parent.progress_bar)

        self.parent.lbl_status = QLabel("Ready")
        layout.addWidget(self.parent.lbl_status)

        # --- Output ---
        layout.addWidget(QLabel("Analysis Result:"))
        self.parent.txt_output = QTextEdit()
        self.parent.txt_output.setReadOnly(True)
        self.parent.txt_output.setPlaceholderText("Result will appear here...")
        layout.addWidget(self.parent.txt_output)

        # --- Footer Actions ---
        footer_layout = QHBoxLayout()

        self.parent.btn_copy = QPushButton("Copy JSON")
        self.parent.btn_copy.clicked.connect(self.parent._handlers.copy_to_clipboard)
        footer_layout.addWidget(self.parent.btn_copy)

        self.parent.btn_open_log = QPushButton("Logdatei öffnen")
        self.parent.btn_open_log.clicked.connect(self.parent._handlers.open_analyse_log)
        footer_layout.addWidget(self.parent.btn_open_log)

        self.parent.btn_close = QPushButton("Close")
        self.parent.btn_close.clicked.connect(self.parent.close)
        footer_layout.addWidget(self.parent.btn_close)

        layout.addLayout(footer_layout)

        # --- Connections ---
        self.parent.btn_analyze.clicked.connect(self.parent._handlers.start_analysis)

    def setup_regime_info_panel(self, layout: QVBoxLayout) -> None:
        """Setup the regime info panel (Phase 2.2)."""
        try:
            from src.ui.widgets.regime_badge_widget import RegimeInfoPanel

            self.parent._regime_panel = RegimeInfoPanel()
            layout.addWidget(self.parent._regime_panel)

            # Add separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("color: #444;")
            layout.addWidget(separator)

            analysis_logger.debug("Regime info panel added to overview tab")
        except ImportError as e:
            analysis_logger.warning(f"Could not add regime info panel: {e}")
            self.parent._regime_panel = None

    def load_settings(self):
        """Load settings from QSettings."""
        # Provider
        default_provider = self.parent.settings.value("ai_default_provider", "OpenAI")
        idx = self.parent.combo_provider.findText(default_provider)
        if idx >= 0:
            self.parent.combo_provider.setCurrentIndex(idx)

        # Trigger model population
        self.on_provider_changed(self.parent.combo_provider.currentText())

        # Prompt overrides
        self.parent._handlers.apply_prompt_overrides()

    def on_provider_changed(self, provider: str):
        """Populate model combo based on selected provider."""
        self.parent.combo_model.blockSignals(True)
        self.parent.combo_model.clear()

        models = []
        default_model = ""

        if provider == "OpenAI":
            models = OPENAI_MODELS
            default_model = self.parent.settings.value("openai_model", "")
        elif provider == "Anthropic":
            models = ANTHROPIC_MODELS
            default_model = self.parent.settings.value("anthropic_model", "")
        elif provider == "Gemini":
            models = GEMINI_MODELS
            default_model = self.parent.settings.value("gemini_model", "")

        self.parent.combo_model.addItems(models)

        # Select default if available
        if default_model:
            idx = self.parent.combo_model.findText(default_model)
            if idx >= 0:
                self.parent.combo_model.setCurrentIndex(idx)

        self.parent.combo_model.blockSignals(False)
