"""Chart Chat Widget - PyQt6 UI for the chatbot.

Provides a dockable widget with chat interface, quick actions,
and markdown-rendered responses.
"""

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


class AnalysisWorker(QThread):
    """Background worker for AI analysis calls."""

    finished = pyqtSignal(object)  # ChartAnalysisResult or QuickAnswerResult
    error = pyqtSignal(str)

    def __init__(
        self,
        service: "ChartChatService",
        action: str,
        question: str | None = None,
    ):
        super().__init__()
        self.service = service
        self.action = action
        self.question = question

    def run(self) -> None:
        """Execute the AI call in background."""
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.action == "full_analysis":
                result = loop.run_until_complete(self.service.analyze_chart())
            elif self.action == "ask" and self.question:
                result = loop.run_until_complete(
                    self.service.ask_question(self.question)
                )
            else:
                self.error.emit("Unbekannte Aktion")
                return

            loop.close()
            self.finished.emit(result)

        except Exception as e:
            logger.exception("Analysis worker error")
            self.error.emit(str(e))


class ChartChatWidget(QDockWidget):
    """Dockable chat widget for chart analysis.

    Provides:
    - Chat display with Markdown rendering
    - Input field for questions
    - Quick action buttons
    - Full analysis button
    """

    analysis_requested = pyqtSignal()  # Emitted when user requests analysis

    def __init__(
        self,
        service: "ChartChatService",
        parent: QWidget | None = None,
    ):
        """Initialize the chat widget.

        Args:
            service: ChartChatService instance
            parent: Parent widget
        """
        super().__init__("Chart Analysis", parent)

        self.service = service
        self._worker: AnalysisWorker | None = None

        self._setup_ui()
        self._connect_signals()
        self._load_existing_history()

        # Connect bars controls
        self._bars_spinbox.valueChanged.connect(self._on_bars_changed)
        self._all_bars_checkbox.stateChanged.connect(self._on_all_bars_toggled)

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

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        pass  # Reserved for future use

    def _update_header(self) -> None:
        """Update the header with current symbol/timeframe."""
        symbol = self.service.current_symbol or "Kein Chart"
        timeframe = self.service.current_timeframe or ""
        self._header.setText(f"💬 {symbol} {timeframe}")

    def _load_existing_history(self) -> None:
        """Load and display existing chat history."""
        for msg in self.service.conversation_history:
            self._append_message(
                msg.role.value if hasattr(msg.role, 'value') else msg.role,
                msg.content,
                msg.timestamp,
            )

    def _append_message(
        self,
        role: str,
        content: str,
        timestamp: datetime | None = None,
    ) -> None:
        """Append a message to the chat display with bubble styling.

        Args:
            role: 'user' or 'assistant'
            content: Message content
            timestamp: Optional timestamp
        """
        ts = timestamp or datetime.now()
        time_str = ts.strftime("%H:%M:%S")

        # Clean up excessive newlines in content
        import re
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Create custom widget for this message
        message_widget = self._create_message_widget(role, content, time_str)

        # Add to list
        item = QListWidgetItem(self._chat_display)
        item.setSizeHint(message_widget.sizeHint())
        self._chat_display.addItem(item)
        self._chat_display.setItemWidget(item, message_widget)

        # Scroll to bottom
        self._chat_display.scrollToBottom()

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

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard.

        Args:
            text: Text to copy
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        logger.debug("Copied message to clipboard")

    def _on_quick_action(self) -> None:
        """Handle quick action button click."""
        button = self.sender()
        if not button:
            return

        action_type = button.property("action_type")
        question = button.property("question")

        if action_type == "full_analysis":
            self._on_full_analysis()
        elif action_type == "ask" and question:
            self._input_field.setText(question)
            self._on_send()

    def _on_send(self) -> None:
        """Handle send button click."""
        question = self._input_field.text().strip()
        if not question:
            return

        self._input_field.clear()
        self._append_message("user", question)
        self._start_analysis("ask", question)

    def _on_full_analysis(self) -> None:
        """Handle full analysis button click."""
        self._append_message(
            "user",
            f"[Vollständige Chartanalyse angefordert]"
        )
        self._start_analysis("full_analysis")
        self.analysis_requested.emit()

    def _start_analysis(
        self, action: str, question: str | None = None
    ) -> None:
        """Start background analysis.

        Args:
            action: 'full_analysis' or 'ask'
            question: Optional question for 'ask' action
        """
        if self._worker and self._worker.isRunning():
            logger.warning("Analysis already in progress")
            return

        self._set_loading(True)

        self._worker = AnalysisWorker(self.service, action, question)
        self._worker.finished.connect(self._on_analysis_complete)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_complete(self, result: Any) -> None:
        """Handle completed analysis.

        Args:
            result: ChartAnalysisResult or QuickAnswerResult
        """
        self._set_loading(False)

        # Format response based on type
        if hasattr(result, "to_markdown"):
            # ChartAnalysisResult
            content = result.to_markdown()
        elif hasattr(result, "answer"):
            # QuickAnswerResult
            content = result.answer
            if result.follow_up_suggestions:
                content += "\n\n**Weitere Fragen:**\n"
                for suggestion in result.follow_up_suggestions:
                    content += f"- {suggestion}\n"
        else:
            content = str(result)

        self._append_message("assistant", content)

    def _on_analysis_error(self, error: str) -> None:
        """Handle analysis error.

        Args:
            error: Error message
        """
        self._set_loading(False)
        self._append_message(
            "assistant",
            f"⚠️ **Fehler:** {error}"
        )

    def _set_loading(self, loading: bool) -> None:
        """Set loading state.

        Args:
            loading: True if loading
        """
        self._progress_bar.setVisible(loading)
        self._send_button.setEnabled(not loading)
        self._analyze_button.setEnabled(not loading)
        self._input_field.setEnabled(not loading)

    def _on_clear_history(self) -> None:
        """Handle clear history button click."""
        self.service.clear_history()
        self._chat_display.clear()

        # Add welcome message back
        self._append_message(
            "assistant",
            "Chat-Verlauf wurde gelöscht. Wie kann ich dir helfen?"
        )

    def _on_bars_changed(self, value: int) -> None:
        """Handle bars spinbox value change.

        Args:
            value: New bars value
        """
        if not self._all_bars_checkbox.isChecked():
            self.service.set_lookback_bars(value)
            logger.info(f"Chart analysis lookback set to {value} bars")

    def _on_all_bars_toggled(self, state: int) -> None:
        """Handle 'all bars' checkbox toggle.

        Args:
            state: Checkbox state (Qt.CheckState)
        """
        is_checked = state == Qt.CheckState.Checked.value

        # Enable/disable spinbox
        self._bars_spinbox.setEnabled(not is_checked)

        if is_checked:
            # Use all available bars from chart
            df = getattr(self.service.chart_widget, "data", None)
            if df is not None and not df.empty:
                all_bars = len(df)
                self.service.set_lookback_bars(all_bars)
                logger.info(f"Using all available bars: {all_bars}")
            else:
                logger.warning("No chart data available for 'all bars'")
        else:
            # Use spinbox value
            self.service.set_lookback_bars(self._bars_spinbox.value())

    def _on_export(self) -> None:
        """Handle export button click."""
        from PyQt6.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Chat exportieren",
            f"chat_{self.service.current_symbol}_{self.service.current_timeframe}.md",
            "Markdown (*.md)",
        )

        if filename:
            self._export_to_markdown(filename)

    def _export_to_markdown(self, filename: str) -> None:
        """Export chat history to Markdown file.

        Args:
            filename: Output file path
        """
        lines = [
            f"# Chart Analysis Chat",
            f"**Symbol:** {self.service.current_symbol}",
            f"**Timeframe:** {self.service.current_timeframe}",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
        ]

        for msg in self.service.conversation_history:
            ts = msg.timestamp.strftime("%Y-%m-%d %H:%M")
            role = "Du" if msg.role.value == "user" else "AI"
            lines.append(f"### [{ts}] {role}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            logger.info("Chat exported to %s", filename)
        except Exception as e:
            logger.error("Export failed: %s", e)

    def on_chart_changed(self) -> None:
        """Handle chart symbol/timeframe change.

        Call this when the chart switches to a different symbol.
        """
        self.service.on_chart_changed()
        self._update_header()

        # Reload history for new chart
        self._chat_display.clear()
        self._load_existing_history()

        if not self.service.conversation_history:
            self._append_message(
                "assistant",
                f"Willkommen zur Chart-Analyse für "
                f"{self.service.current_symbol} {self.service.current_timeframe}.\n\n"
                f"Klicke auf **Vollständige Analyse** oder stelle eine Frage."
            )

    def closeEvent(self, event) -> None:
        """Handle widget close."""
        self.service.shutdown()
        super().closeEvent(event)
