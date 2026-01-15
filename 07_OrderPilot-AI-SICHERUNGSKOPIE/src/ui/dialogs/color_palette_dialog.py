"""Color Palette Dialog for editing color assignment rules.

Allows users to customize which colors are automatically assigned
to evaluation entries based on keyword matching.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QColorDialog
)
from PyQt6.QtGui import QColor


class ColorPaletteDialog(QDialog):
    """Dialog for editing color assignment rules."""

    def __init__(self, parent, color_manager):
        """Initialize color palette dialog.

        Args:
            parent: Parent widget
            color_manager: ColorManager instance to edit
        """
        super().__init__(parent)
        self.color_manager = color_manager

        self.setWindowTitle("Farben zuordnen")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Create row for each color rule
        self.buttons = {}
        for key, color in self.color_manager.rules.items():
            row_layout = self._create_rule_row(key, color)
            layout.addLayout(row_layout)

        # Buttons
        button_layout = QHBoxLayout()

        # Reset button
        reset_btn = QPushButton("Zurücksetzen")
        reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        # Apply button
        apply_btn = QPushButton("Übernehmen")
        apply_btn.clicked.connect(self._on_save)
        button_layout.addWidget(apply_btn)

        # Cancel button
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.resize(400, 500)

    def _create_rule_row(self, key: str, color: str) -> QHBoxLayout:
        """Create row for one color rule.

        Args:
            key: Rule keyword (e.g., "support", "resistance")
            color: Current color for this rule

        Returns:
            QHBoxLayout with label and color button
        """
        layout = QHBoxLayout()

        label = QLabel(key.title())
        label.setMinimumWidth(150)

        btn = QPushButton("   ")
        btn.setFixedWidth(50)
        btn.setStyleSheet(f"background-color:{color};")
        btn.clicked.connect(lambda: self._on_pick_color(key, btn))

        self.buttons[key] = btn

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(btn)

        return layout

    def _on_pick_color(self, key: str, button: QPushButton):
        """Pick color for a rule.

        Args:
            key: Rule keyword
            button: Button to update with new color
        """
        current = self.color_manager.rules[key]
        chosen = QColorDialog.getColor(QColor(current), self, f"Farbe für {key}")

        if chosen.isValid():
            self.color_manager.rules[key] = chosen.name()
            button.setStyleSheet(f"background-color:{chosen.name()};")

    def _on_reset(self):
        """Reset all colors to defaults."""
        self.color_manager.reset_to_defaults()

        # Update button colors
        for key, button in self.buttons.items():
            color = self.color_manager.rules.get(key, "#0d6efd")
            button.setStyleSheet(f"background-color:{color};")

    def _on_save(self):
        """Save rules and close."""
        self.color_manager.save_rules()
        self.accept()
