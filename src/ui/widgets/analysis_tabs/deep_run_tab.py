"""Tab 4: Deep Analysis Run & Results."""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QProgressBar, QTextEdit, QLabel
)
from src.core.analysis.context import AnalysisContext
from src.core.analysis.orchestrator import AnalysisWorker

# Use dedicated analysis logger
analysis_logger = logging.getLogger('ai_analysis')

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
        self.status_label.setProperty("class", "status-label")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False) # Clean look
        # Theme handles styling
        layout.addWidget(self.progress_bar)

        self.start_btn = QPushButton("🚀 Deep Analysis starten")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setProperty("class", "primary")
        self.start_btn.clicked.connect(self._start_analysis)
        layout.addWidget(self.start_btn)

        # Output Area
        layout.addWidget(QLabel("Ergebnis-Bericht:"))
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setPlaceholderText("Ergebnis erscheint hier...")
        # Theme handles styling
        layout.addWidget(self.output_view)

    def _start_analysis(self):
        if self._worker and self._worker.isRunning():
            analysis_logger.warning("Deep analysis already running", extra={
                'tab': 'deep_run_tab',
                'action': 'start_analysis',
                'step': 'already_running'
            })
            return

        # Get context info for logging
        regime = self.context.get_regime()
        strategy = self.context.get_selected_strategy()

        analysis_logger.info("Starting deep analysis", extra={
            'tab': 'deep_run_tab',
            'action': 'start_analysis',
            'regime': regime,
            'strategy': strategy.name if strategy else 'None',
            'step': 'worker_start'
        })

        self.start_btn.setEnabled(False)
        self.output_view.clear()

        self._worker = AnalysisWorker(self.context)
        self._worker.status_update.connect(self.status_label.setText)
        self._worker.progress_update.connect(self.progress_bar.setValue)
        self._worker.result_ready.connect(self._on_success)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_success(self, report: str):
        analysis_logger.info("Deep analysis completed successfully", extra={
            'tab': 'deep_run_tab',
            'action': 'analysis_complete',
            'report_length': len(report),
            'step': 'success'
        })
        self.output_view.setMarkdown(report)
        self.start_btn.setEnabled(True)
        self.status_label.setText("Analyse erfolgreich abgeschlossen.")

    def _on_error(self, error_msg: str):
        analysis_logger.error("Deep analysis failed", extra={
            'tab': 'deep_run_tab',
            'action': 'analysis_error',
            'error_message': error_msg,
            'step': 'error'
        })
        self.output_view.setText(f"❌ FEHLER: {error_msg}")
        self.start_btn.setEnabled(True)
        self.status_label.setText("Abgebrochen.")
        self.progress_bar.setValue(0)
