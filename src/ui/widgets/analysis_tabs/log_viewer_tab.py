"""Tab 5: Log Viewer for Deep Analysis.

Displays the Analyse.log file with auto-refresh and management features.
"""

import logging
import os
import sys
import platform
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from src.core.analysis.context import AnalysisContext

# Use dedicated analysis logger
analysis_logger = logging.getLogger('ai_analysis')


class LogViewerTab(QWidget):
    """UI for viewing and managing the AI Analysis log file."""

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context
        self.log_file_path = Path("./logs/Analyse.log")
        self._timer = None
        self._setup_ui()
        self._start_auto_refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Status bar with file info
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Log-Datei: logs/Analyse.log")
        self.status_label.setProperty("class", "status-label")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_btn.setToolTip("Log-Datei neu laden")
        self.refresh_btn.clicked.connect(self._refresh_log)
        self.refresh_btn.setProperty("class", "primary")
        btn_layout.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("🗑️ Log löschen")
        self.clear_btn.setToolTip("Log-Datei leeren")
        self.clear_btn.clicked.connect(self._clear_log)
        self.clear_btn.setProperty("class", "danger")
        btn_layout.addWidget(self.clear_btn)

        self.open_btn = QPushButton("📂 In Editor öffnen")
        self.open_btn.setToolTip("Log-Datei im Standardeditor öffnen")
        self.open_btn.clicked.connect(self._open_in_editor)
        self.open_btn.setProperty("class", "success")
        btn_layout.addWidget(self.open_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Log display area
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Log-Einträge erscheinen hier...")
        self.log_view.setFont(QFont("Consolas", 10))
        # Theme handles styling
        layout.addWidget(self.log_view)

    def _start_auto_refresh(self):
        """Start auto-refresh timer (updates every 1000ms)."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_log)
        self._timer.start(1000)  # 1 second
        # Load initial content
        self._refresh_log()

    def _refresh_log(self):
        """Reload log file content and update display."""
        try:
            if not self.log_file_path.exists():
                self.log_view.setText("Log-Datei noch nicht vorhanden. Wird beim ersten Analyselauf erstellt.")
                self.status_label.setText("Log-Datei: Nicht vorhanden")
                return

            # Issue #41: Only read last 100KB of log file to prevent memory issues
            file_size = self.log_file_path.stat().st_size
            max_read_bytes = 100 * 1024  # 100KB limit

            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                if file_size > max_read_bytes:
                    f.seek(file_size - max_read_bytes)
                    f.readline()  # Skip partial line
                    content = "... (ältere Einträge ausgeblendet, Datei > 100KB) ...\n\n" + f.read()
                else:
                    content = f.read()

            # Update display
            self.log_view.setText(content)

            # Auto-scroll to bottom
            scrollbar = self.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # Update status with file size and last modification
            file_size = self.log_file_path.stat().st_size
            file_mtime = datetime.fromtimestamp(self.log_file_path.stat().st_mtime)
            size_kb = file_size / 1024

            self.status_label.setText(
                f"Log-Datei: logs/Analyse.log | Größe: {size_kb:.1f} KB | "
                f"Zuletzt geändert: {file_mtime.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except Exception as e:
            analysis_logger.error("Error refreshing log viewer", extra={
                'tab': 'log_viewer_tab',
                'action': 'refresh_log',
                'error': str(e),
                'step': 'error'
            })
            self.log_view.setText(f"Fehler beim Laden der Log-Datei: {e}")
            self.status_label.setText("Log-Datei: Fehler beim Laden")

    def _clear_log(self):
        """Clear the log file after confirmation."""
        # German confirmation dialog
        reply = QMessageBox.question(
            self,
            "Log löschen",
            "Sind Sie sicher, dass Sie das Log löschen möchten?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.log_file_path.exists():
                    # Clear file content
                    with open(self.log_file_path, 'w', encoding='utf-8') as f:
                        f.write("")

                    analysis_logger.info("Log file cleared by user", extra={
                        'tab': 'log_viewer_tab',
                        'action': 'clear_log',
                        'step': 'user_action'
                    })

                    self._refresh_log()
                    QMessageBox.information(self, "Log gelöscht", "Die Log-Datei wurde erfolgreich geleert.")
                else:
                    QMessageBox.warning(self, "Fehler", "Log-Datei existiert nicht.")

            except Exception as e:
                analysis_logger.error("Error clearing log file", extra={
                    'tab': 'log_viewer_tab',
                    'action': 'clear_log',
                    'error': str(e),
                    'step': 'error'
                })
                QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen der Log-Datei: {e}")

    def _open_in_editor(self):
        """Open log file in default system editor (cross-platform)."""
        try:
            if not self.log_file_path.exists():
                QMessageBox.warning(self, "Fehler", "Log-Datei existiert noch nicht.")
                return

            abs_path = str(self.log_file_path.absolute())
            system = platform.system()

            # Cross-platform file opening
            if system == "Windows":
                os.startfile(abs_path)
            elif system == "Darwin":  # macOS
                os.system(f'open "{abs_path}"')
            else:  # Linux and others
                os.system(f'xdg-open "{abs_path}"')

            analysis_logger.info("Log file opened in editor", extra={
                'tab': 'log_viewer_tab',
                'action': 'open_in_editor',
                'platform': system,
                'step': 'user_action'
            })

        except Exception as e:
            analysis_logger.error("Error opening log file in editor", extra={
                'tab': 'log_viewer_tab',
                'action': 'open_in_editor',
                'error': str(e),
                'step': 'error'
            })
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen der Datei: {e}")

    def closeEvent(self, event):
        """Stop timer when tab is closed."""
        if self._timer:
            self._timer.stop()
        super().closeEvent(event)
