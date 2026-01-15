"""AI Analysis Prompt Editor - Prompt editor dialog.

Refactored from 822 LOC monolith using composition pattern.

Module 5/5 of ai_analysis_window.py split.

Contains:
- PromptEditorDialog: Dialog for editing analysis prompts
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QDialogButtonBox
)


class PromptEditorDialog(QDialog):
    """Small dialog to edit analysis prompts."""

    def __init__(self, parent, system_prompt: str, tasks_prompt: str, default_system: str, default_tasks: str):
        super().__init__(parent)
        self.setWindowTitle("Edit Analysis Prompts")
        self.resize(700, 600)
        self.default_system = default_system
        self.default_tasks = default_tasks

        # Issue #25: Fenster in der Mitte des Bildschirms positionieren
        self._center_on_screen()

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>System Prompt</b> (Role & global constraints)"))
        self.txt_system = QTextEdit()
        self.txt_system.setPlainText(system_prompt)
        self.txt_system.setMinimumHeight(180)
        layout.addWidget(self.txt_system)

        layout.addWidget(QLabel("<b>Task/Analysis Instructions</b> (added before market data + schema)"))
        self.txt_tasks = QTextEdit()
        self.txt_tasks.setPlainText(tasks_prompt)
        self.txt_tasks.setMinimumHeight(220)
        layout.addWidget(self.txt_tasks)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_reset = QPushButton("Reset to Defaults")
        btn_reset.clicked.connect(self._reset_defaults)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

        footer_layout = QHBoxLayout()
        footer_layout.addWidget(btn_reset)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_box)
        layout.addLayout(footer_layout)

    def _reset_defaults(self):
        self.txt_system.setPlainText(self.default_system)
        self.txt_tasks.setPlainText(self.default_tasks)

    def _center_on_screen(self) -> None:
        """Issue #25: Zentriert das Fenster auf dem Bildschirm."""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2 + screen_geometry.x()
            y = (screen_geometry.height() - self.height()) // 2 + screen_geometry.y()
            self.move(x, y)

    def get_values(self):
        return self.txt_system.toPlainText(), self.txt_tasks.toPlainText()
