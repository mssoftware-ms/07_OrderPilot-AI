"""Tab 4: Deep Analysis Run & Results."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QProgressBar, QTextEdit, QLabel
)
from src.core.analysis.context import AnalysisContext
from src.core.analysis.orchestrator import AnalysisWorker

class DeepRunTab(QWidget):
    """UI for executing the analysis and viewing results."""

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        self.status_label = QLabel("Bereit zum Start.")
        self.status_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False) # Clean look
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #222;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.start_btn = QPushButton("🚀 Deep Analysis starten")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200EA;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #7C4DFF; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.start_btn.clicked.connect(self._start_analysis)
        layout.addWidget(self.start_btn)

        # Output Area
        layout.addWidget(QLabel("Ergebnis-Bericht:"))
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setPlaceholderText("Ergebnis erscheint hier...")
        self.output_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ddd;
                border: 1px solid #333;
                font-family: Consolas, monospace;
            }
        """)
        layout.addWidget(self.output_view)

    def _start_analysis(self):
        if self._worker and self._worker.isRunning():
            return

        self.start_btn.setEnabled(False)
        self.output_view.clear()
        
        self._worker = AnalysisWorker(self.context)
        self._worker.status_update.connect(self.status_label.setText)
        self._worker.progress_update.connect(self.progress_bar.setValue)
        self._worker.result_ready.connect(self._on_success)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_success(self, report: str):
        self.output_view.setMarkdown(report)
        self.start_btn.setEnabled(True)
        self.status_label.setText("Analyse erfolgreich abgeschlossen.")

    def _on_error(self, error_msg: str):
        self.output_view.setText(f"❌ FEHLER: {error_msg}")
        self.start_btn.setEnabled(True)
        self.status_label.setText("Abgebrochen.")
        self.progress_bar.setValue(0)
