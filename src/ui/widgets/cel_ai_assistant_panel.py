"""AI Assistant panel for CEL Editor (Phase 3.3)."""

from __future__ import annotations

import asyncio
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QComboBox,
    QTabWidget,
    QMessageBox,
)

from .cel_ai_helper import CelAIHelper


class _CelAIWorker(QThread):
    """Background worker for AI calls."""

    result_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, mode: str, helper: CelAIHelper, **kwargs):
        super().__init__()
        self.mode = mode
        self.helper = helper
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            if self.mode == "generate":
                result = loop.run_until_complete(
                    self.helper.generate_cel_code(
                        self.kwargs.get("workflow_type", "entry"),
                        self.kwargs.get("pattern_name", ""),
                        self.kwargs.get("strategy_description", ""),
                        self.kwargs.get("context")
                    )
                )
            elif self.mode == "explain":
                result = loop.run_until_complete(
                    self.helper.explain_cel_code(
                        self.kwargs.get("cel_code", ""),
                        self.kwargs.get("context")
                    )
                )
            else:
                result = None
            loop.close()

            if result:
                self.result_ready.emit(result)
            else:
                self.error.emit("No response from AI provider.")
        except Exception as exc:
            self.error.emit(str(exc))


class CelAIAssistantPanel(QWidget):
    """Dockable AI assistant for CEL workflows."""

    code_ready = pyqtSignal(str, str)  # workflow_type, code
    status_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.helper = CelAIHelper()
        self._worker: Optional[_CelAIWorker] = None
        self._setup_ui()
        self._refresh_provider_status()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        header = QLabel("AI Assistant")
        header.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        self.provider_label = QLabel("Provider: n/a")
        self.provider_label.setStyleSheet("color: #848E9C; font-size: 11px;")
        layout.addWidget(self.provider_label)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Generate tab
        gen_tab = QWidget()
        gen_layout = QVBoxLayout(gen_tab)

        self.workflow_combo = QComboBox()
        self.workflow_combo.addItems(["entry", "exit", "before_exit", "update_stop"])
        gen_layout.addWidget(QLabel("Workflow"))
        gen_layout.addWidget(self.workflow_combo)

        self.pattern_name = QLineEdit()
        gen_layout.addWidget(QLabel("Pattern Name"))
        gen_layout.addWidget(self.pattern_name)

        self.strategy_desc = QTextEdit()
        self.strategy_desc.setMinimumHeight(80)
        gen_layout.addWidget(QLabel("Strategy Description"))
        gen_layout.addWidget(self.strategy_desc)

        self.gen_context = QTextEdit()
        self.gen_context.setMinimumHeight(60)
        gen_layout.addWidget(QLabel("Additional Context"))
        gen_layout.addWidget(self.gen_context)

        gen_btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("Generate CEL")
        self.insert_btn = QPushButton("Insert into Editor")
        self.insert_btn.setEnabled(False)
        gen_btn_row.addWidget(self.generate_btn)
        gen_btn_row.addWidget(self.insert_btn)
        gen_layout.addLayout(gen_btn_row)

        self.generated_output = QTextEdit()
        self.generated_output.setReadOnly(True)
        self.generated_output.setMinimumHeight(120)
        gen_layout.addWidget(QLabel("Generated CEL"))
        gen_layout.addWidget(self.generated_output)

        self.tabs.addTab(gen_tab, "Generate")

        # Explain tab
        explain_tab = QWidget()
        explain_layout = QVBoxLayout(explain_tab)

        self.explain_input = QTextEdit()
        self.explain_input.setMinimumHeight(120)
        explain_layout.addWidget(QLabel("CEL to Explain"))
        explain_layout.addWidget(self.explain_input)

        self.explain_context = QTextEdit()
        self.explain_context.setMinimumHeight(60)
        explain_layout.addWidget(QLabel("Additional Context"))
        explain_layout.addWidget(self.explain_context)

        self.explain_btn = QPushButton("Explain CEL")
        explain_layout.addWidget(self.explain_btn)

        self.explain_output = QTextEdit()
        self.explain_output.setReadOnly(True)
        self.explain_output.setMinimumHeight(120)
        explain_layout.addWidget(QLabel("Explanation"))
        explain_layout.addWidget(self.explain_output)

        self.tabs.addTab(explain_tab, "Explain")

        # Connect actions
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        self.insert_btn.clicked.connect(self._on_insert_clicked)
        self.explain_btn.clicked.connect(self._on_explain_clicked)

    def _refresh_provider_status(self) -> None:
        config = self.helper.get_current_provider_config()
        if not config.get("enabled"):
            self.provider_label.setText("Provider: disabled")
        else:
            provider = config.get("display_name") or config.get("provider")
            self.provider_label.setText(f"Provider: {provider}")

    def set_workflow(self, workflow_type: str) -> None:
        idx = self.workflow_combo.findText(workflow_type)
        if idx >= 0:
            self.workflow_combo.setCurrentIndex(idx)

    def set_pattern_context(self, pattern_name: str, description: str) -> None:
        if pattern_name:
            self.pattern_name.setText(pattern_name)
        if description:
            self.strategy_desc.setPlainText(description)

    def set_explain_code(self, code: str) -> None:
        if code:
            self.explain_input.setPlainText(code)
            self.tabs.setCurrentIndex(1)

    def _ensure_ai_ready(self) -> bool:
        config = self.helper.get_current_provider_config()
        if not config.get("enabled"):
            QMessageBox.warning(self, "AI Disabled", "AI features are disabled in settings.")
            return False
        if not config.get("api_key"):
            QMessageBox.warning(self, "API Key Missing", "No API key found for the active provider.")
            return False
        return True

    def _on_generate_clicked(self) -> None:
        self._refresh_provider_status()
        if not self._ensure_ai_ready():
            return
        self._set_busy(True, "Generating...")
        self._worker = _CelAIWorker(
            "generate",
            self.helper,
            workflow_type=self.workflow_combo.currentText(),
            pattern_name=self.pattern_name.text().strip(),
            strategy_description=self.strategy_desc.toPlainText().strip(),
            context=self.gen_context.toPlainText().strip() or None,
        )
        self._worker.result_ready.connect(self._on_generation_result)
        self._worker.error.connect(self._on_generation_error)
        self._worker.start()

    def _on_insert_clicked(self) -> None:
        code = self.generated_output.toPlainText().strip()
        if not code:
            return
        workflow = self.workflow_combo.currentText()
        self.code_ready.emit(workflow, code)

    def _on_explain_clicked(self) -> None:
        self._refresh_provider_status()
        if not self._ensure_ai_ready():
            return
        code = self.explain_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "Explain", "Please paste a CEL expression to explain.")
            return
        self._set_busy(True, "Explaining...")
        self._worker = _CelAIWorker(
            "explain",
            self.helper,
            cel_code=code,
            context=self.explain_context.toPlainText().strip() or None,
        )
        self._worker.result_ready.connect(self._on_explain_result)
        self._worker.error.connect(self._on_explain_error)
        self._worker.start()

    def _on_generation_result(self, result: str) -> None:
        self.generated_output.setPlainText(result)
        self.insert_btn.setEnabled(True)
        self._set_busy(False, "AI: Ready")

    def _on_generation_error(self, message: str) -> None:
        self._set_busy(False, "AI: Error")
        QMessageBox.warning(self, "AI Generation Failed", message)

    def _on_explain_result(self, result: str) -> None:
        self.explain_output.setPlainText(result)
        self._set_busy(False, "AI: Ready")

    def _on_explain_error(self, message: str) -> None:
        self._set_busy(False, "AI: Error")
        QMessageBox.warning(self, "AI Explain Failed", message)

    def _set_busy(self, busy: bool, status: str) -> None:
        self.generate_btn.setEnabled(not busy)
        self.explain_btn.setEnabled(not busy)
        self.status_changed.emit(status)
