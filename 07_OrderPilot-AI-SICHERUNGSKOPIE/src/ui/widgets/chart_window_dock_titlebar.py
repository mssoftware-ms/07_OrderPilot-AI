"""Chart Window - Custom Dock Title Bar Widget.

Refactored from 706 LOC monolith using composition pattern.

Module 1/6 of chart_window.py split.

Contains:
- DockTitleBar: Custom title bar for dock widget with minimize/maximize/reset/close/help buttons
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QSizePolicy


class DockTitleBar(QWidget):
    """Custom title bar for dock widget with minimize/maximize buttons."""

    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    reset_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    help_clicked = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_maximized = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Title label
        self.title_label = QLabel(title)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.title_label)

        # Help button (blue circle with ?)
        self.help_btn = QToolButton()
        self.help_btn.setObjectName("helpButton")
        self.help_btn.setText("?")
        self.help_btn.setToolTip("Hilfe zu Trailing Stop & Exit-Strategien (F1)")
        self.help_btn.setFixedSize(24, 24)
        self.help_btn.clicked.connect(self.help_clicked.emit)
        layout.addWidget(self.help_btn)

        # Reset button
        self.reset_btn = QToolButton()
        self.reset_btn.setText("⊞")
        self.reset_btn.setToolTip("Layout zurücksetzen (Strg+R)")
        self.reset_btn.setFixedSize(24, 24)
        self.reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self.reset_btn)

        # Minimize button
        self.minimize_btn = QToolButton()
        self.minimize_btn.setText("−")
        self.minimize_btn.setToolTip("Minimieren")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.minimize_btn)

        # Maximize/Restore button
        self.maximize_btn = QToolButton()
        self.maximize_btn.setText("□")
        self.maximize_btn.setToolTip("Maximieren")
        self.maximize_btn.setFixedSize(24, 24)
        self.maximize_btn.clicked.connect(self._on_maximize_clicked)
        layout.addWidget(self.maximize_btn)

        # Close button
        self.close_btn = QToolButton()
        self.close_btn.setText("×")
        self.close_btn.setToolTip("Schließen")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)

        self.setStyleSheet("""
            DockTitleBar {
                background: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: bold;
                padding-left: 4px;
            }
            QToolButton {
                background: transparent;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: #3d3d3d;
                border-radius: 2px;
            }
            QToolButton:pressed {
                background: #4d4d4d;
            }
            QToolButton#helpButton {
                background: #2196f3;
                border-radius: 12px;
                color: white;
            }
            QToolButton#helpButton:hover {
                background: #1976d2;
            }
        """)

    def _on_maximize_clicked(self):
        self._is_maximized = not self._is_maximized
        if self._is_maximized:
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("Wiederherstellen")
        else:
            self.maximize_btn.setText("□")
            self.maximize_btn.setToolTip("Maximieren")
        self.maximize_clicked.emit()

    def set_maximized(self, maximized: bool):
        """Update button state without emitting signal."""
        self._is_maximized = maximized
        if maximized:
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("Wiederherstellen")
        else:
            self.maximize_btn.setText("□")
            self.maximize_btn.setToolTip("Maximieren")
