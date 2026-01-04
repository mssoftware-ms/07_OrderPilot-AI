from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)
from PyQt6.QtCore import QSettings

from .prompts import (
    CHART_ANALYSIS_SYSTEM_PROMPT,
    CONVERSATIONAL_SYSTEM_PROMPT,
    COMPACT_ANALYSIS_SYSTEM_PROMPT,
    CHART_ANALYSIS_USER_TEMPLATE,
    CONVERSATIONAL_USER_TEMPLATE,
    COMPACT_ANALYSIS_USER_TEMPLATE,
    get_chart_analysis_system_prompt,
    get_conversational_system_prompt,
    get_compact_system_prompt,
    get_chart_analysis_user_template,
    get_conversational_user_template,
    get_compact_user_template,
)


class PromptsEditorDialog(QDialog):
    """Popup dialog to edit all chatbot prompts (system + user templates)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chatbot Prompts bearbeiten")
        self.resize(900, 720)
        self.settings = QSettings("OrderPilot", "TradingApp")

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_system_tab(), "System Prompts")
        self.tabs.addTab(self._build_user_tab(), "User Templates")
        layout.addWidget(self.tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        reset_btn = QPushButton("Auf Defaults zurücksetzen")
        reset_btn.clicked.connect(self._reset_defaults)

        footer = QHBoxLayout()
        footer.addWidget(reset_btn)
        footer.addStretch()
        footer.addWidget(buttons)
        layout.addLayout(footer)

    def _build_system_tab(self):
        tab = QDialog()
        lyt = QVBoxLayout(tab)

        self.txt_sys_analysis = self._make_editor("Chart Analysis System", get_chart_analysis_system_prompt())
        self.txt_sys_convo = self._make_editor("Conversational System", get_conversational_system_prompt())
        self.txt_sys_compact = self._make_editor("Compact System", get_compact_system_prompt())

        for widget in (self.txt_sys_analysis, self.txt_sys_convo, self.txt_sys_compact):
            lyt.addWidget(widget["label"])
            lyt.addWidget(widget["edit"])

        return tab

    def _build_user_tab(self):
        tab = QDialog()
        lyt = QVBoxLayout(tab)

        self.txt_user_analysis = self._make_editor("Chart Analysis User Template", get_chart_analysis_user_template())
        self.txt_user_convo = self._make_editor("Conversational User Template", get_conversational_user_template())
        self.txt_user_compact = self._make_editor("Compact User Template", get_compact_user_template())

        for widget in (self.txt_user_analysis, self.txt_user_convo, self.txt_user_compact):
            lyt.addWidget(widget["label"])
            lyt.addWidget(widget["edit"])

        return tab

    def _make_editor(self, title: str, text: str):
        lbl = QLabel(f"<b>{title}</b>")
        edit = QTextEdit()
        edit.setPlainText(text)
        edit.setMinimumHeight(160)
        return {"label": lbl, "edit": edit}

    def _reset_defaults(self):
        # Reset all editors to the code defaults
        self.txt_sys_analysis["edit"].setPlainText(CHART_ANALYSIS_SYSTEM_PROMPT)
        self.txt_sys_convo["edit"].setPlainText(CONVERSATIONAL_SYSTEM_PROMPT)
        self.txt_sys_compact["edit"].setPlainText(COMPACT_ANALYSIS_SYSTEM_PROMPT)
        self.txt_user_analysis["edit"].setPlainText(CHART_ANALYSIS_USER_TEMPLATE)
        self.txt_user_convo["edit"].setPlainText(CONVERSATIONAL_USER_TEMPLATE)
        self.txt_user_compact["edit"].setPlainText(COMPACT_ANALYSIS_USER_TEMPLATE)

    def _save(self):
        # Write overrides (empty string if equals default to keep settings clean)
        self._set_override("chat_prompts/chart_analysis_system", self.txt_sys_analysis["edit"].toPlainText(), CHART_ANALYSIS_SYSTEM_PROMPT)
        self._set_override("chat_prompts/conversational_system", self.txt_sys_convo["edit"].toPlainText(), CONVERSATIONAL_SYSTEM_PROMPT)
        self._set_override("chat_prompts/compact_system", self.txt_sys_compact["edit"].toPlainText(), COMPACT_ANALYSIS_SYSTEM_PROMPT)
        self._set_override("chat_prompts/chart_analysis_user", self.txt_user_analysis["edit"].toPlainText(), CHART_ANALYSIS_USER_TEMPLATE)
        self._set_override("chat_prompts/conversational_user", self.txt_user_convo["edit"].toPlainText(), CONVERSATIONAL_USER_TEMPLATE)
        self._set_override("chat_prompts/compact_user", self.txt_user_compact["edit"].toPlainText(), COMPACT_ANALYSIS_USER_TEMPLATE)
        self.accept()

    def _set_override(self, key: str, value: str, default: str):
        cleaned = (value or "").strip()
        if cleaned == default.strip():
            self.settings.setValue(key, "")
        else:
            self.settings.setValue(key, cleaned)
