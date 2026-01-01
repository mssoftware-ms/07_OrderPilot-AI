from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from .chat_service import ChartChatService
    from .models import ChartAnalysisResult, QuickAnswerResult

logger = logging.getLogger(__name__)


class ChartChatUIMixin:
    """ChartChatUIMixin extracted from ChartChatWidget."""
    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(350)

        # Main container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with symbol info
        self._header = QLabel()
        self._header.setStyleSheet(
            "font-weight: bold; font-size: 14px; padding: 4px;"
        )
        self._update_header()
        layout.addWidget(self._header)

        # Chat display area (using QListWidget for proper bubble rendering)
        self._chat_display = QListWidget()
        self._chat_display.setFrameShape(QFrame.Shape.NoFrame)
        self._chat_display.setStyleSheet("""
            QListWidget {
                background-color: rgb(10, 10, 10);
                border: 1px solid #333;
                border-radius: 4px;
            }
            QListWidget::item {
                background: transparent;
                border: none;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        self._chat_display.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._chat_display.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self._chat_display.setWordWrap(True)
        layout.addWidget(self._chat_display, 1)  # Stretch factor 1

        # ===== Integrated Control Panel (all UI elements in one rounded frame) =====
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 8px;
            }
        """)
        control_panel_layout = QVBoxLayout(control_panel)
        control_panel_layout.setContentsMargins(10, 10, 10, 10)
        control_panel_layout.setSpacing(8)

        # Quick actions bar
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setSpacing(4)

        for action in self.service.get_quick_actions():
            btn = QPushButton(action["label"])
            btn.setToolTip(action.get("tooltip", ""))
            btn.setMaximumHeight(28)
            btn.setProperty("action_type", action["action"])
            btn.setProperty("question", action.get("question", ""))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: white;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
            """)
            btn.clicked.connect(self._on_quick_action)
            quick_actions_layout.addWidget(btn)

        control_panel_layout.addLayout(quick_actions_layout)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)

        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("Frage zum Chart eingeben...")
        self._input_field.returnPressed.connect(self._on_send)
        self._input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        input_layout.addWidget(self._input_field, 1)

        self._send_button = QPushButton("Senden")
        self._send_button.clicked.connect(self._on_send)
        self._send_button.setMaximumWidth(80)
        self._send_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        input_layout.addWidget(self._send_button)

        control_panel_layout.addLayout(input_layout)

        # Progress indicator
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setMaximumHeight(3)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.hide()
        control_panel_layout.addWidget(self._progress_bar)

        # Bottom toolbar with analysis controls
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        # Full analysis button (same style as other buttons)
        self._analyze_button = QPushButton("📊 Vollständige Analyse")
        self._analyze_button.clicked.connect(self._on_full_analysis)
        self._analyze_button.setStyleSheet(
            "QPushButton { background-color: #3a3a3a; color: white; "
            "padding: 6px 12px; border-radius: 4px; font-weight: bold; "
            "border: 1px solid #444; }"
            "QPushButton:hover { background-color: #4a4a4a; }"
            "QPushButton:disabled { background-color: #6c757d; }"
        )
        toolbar_layout.addWidget(self._analyze_button)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #444;")
        toolbar_layout.addWidget(separator)

        # Bars controls
        bars_label = QLabel("Bars:")
        bars_label.setStyleSheet("color: #ccc; font-size: 11px;")
        toolbar_layout.addWidget(bars_label)

        from PyQt6.QtWidgets import QCheckBox
        self._bars_spinbox = QSpinBox()
        self._bars_spinbox.setMinimum(20)
        self._bars_spinbox.setMaximum(500)
        self._bars_spinbox.setValue(100)
        self._bars_spinbox.setSingleStep(10)
        self._bars_spinbox.setMaximumWidth(70)
        self._bars_spinbox.setToolTip("Anzahl der Kerzen für die Analyse")
        self._bars_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #3a3a3a;
                border: 1px solid #555;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #4a4a4a;
            }
        """)
        toolbar_layout.addWidget(self._bars_spinbox)

        self._all_bars_checkbox = QCheckBox("Alle angezeigten")
        self._all_bars_checkbox.setToolTip("Alle im Chart sichtbaren Kerzen verwenden")
        self._all_bars_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ccc;
                font-size: 11px;
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #444;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border-color: #0d6efd;
            }
            QCheckBox::indicator:hover {
                border-color: #666;
            }
        """)
        toolbar_layout.addWidget(self._all_bars_checkbox)

        toolbar_layout.addStretch()

        # Clear history button
        clear_btn = QPushButton("🗑️")
        clear_btn.setToolTip("Chat-Verlauf löschen")
        clear_btn.setMaximumWidth(32)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_history)
        toolbar_layout.addWidget(clear_btn)

        # Export button
        export_btn = QPushButton("📄")
        export_btn.setToolTip("Als Markdown exportieren")
        export_btn.setMaximumWidth(32)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        export_btn.clicked.connect(self._on_export)
        toolbar_layout.addWidget(export_btn)

        control_panel_layout.addLayout(toolbar_layout)

        # Add the integrated control panel to main layout
        layout.addWidget(control_panel)

        self.setWidget(container)
    def _create_message_widget(self, role: str, content: str, time_str: str) -> QWidget:
        """Create a custom widget for a chat message bubble.

        Args:
            role: 'user' or 'assistant'
            content: Message content
            time_str: Formatted time string

        Returns:
            QWidget with the message bubble
        """
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Determine styling based on role
        if role == "user":
            sender = "Du"
            bg_color = "rgb(64,64,64)"  # Medium gray (different from AI)
            text_color = "#FFFFFF"  # White
            alignment = Qt.AlignmentFlag.AlignLeft
        else:
            sender = "AI"
            bg_color = "rgb(48,48,48)"  # Dark gray
            text_color = "#FFFFFF"  # White
            alignment = Qt.AlignmentFlag.AlignRight

        # Header (sender + time + copy button)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)
        header_layout.setSpacing(6)
        if role == "user":
            header_layout.addStretch(0)

        header_label = QLabel(f"<b>{sender}</b> · {time_str}")
        header_label.setStyleSheet("color: #999; font-size: 11px;")
        header_layout.addWidget(header_label)

        # Copy to clipboard button
        copy_btn = QPushButton("📋")
        copy_btn.setMaximumSize(20, 20)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
        """)
        copy_btn.setToolTip("In Zwischenablage kopieren")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(content))
        header_layout.addWidget(copy_btn)

        if role == "assistant":
            header_layout.addStretch(0)

        layout.addLayout(header_layout)

        # Message bubble
        bubble_container = QHBoxLayout()
        bubble_container.setContentsMargins(0, 0, 0, 0)

        if role == "user":
            bubble_container.addStretch(0)

        bubble = QLabel(content)
        bubble.setWordWrap(True)
        bubble.setTextFormat(Qt.TextFormat.PlainText)
        bubble.setMaximumWidth(int(container.width() * 0.7) if container.width() > 0 else 400)
        bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 13px;
                line-height: 1.5;
            }}
        """)
        bubble_container.addWidget(bubble)

        if role == "assistant":
            bubble_container.addStretch(0)

        layout.addLayout(bubble_container)

        return container
    def _update_header(self) -> None:
        """Update the header with current symbol/timeframe."""
        symbol = self.service.current_symbol or "Kein Chart"
        timeframe = self.service.current_timeframe or ""
        self._header.setText(f"💬 {symbol} {timeframe}")
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard.

        Args:
            text: Text to copy
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        logger.debug("Copied message to clipboard")
