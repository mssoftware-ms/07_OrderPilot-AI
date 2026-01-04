import json
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QClipboard

from src.core.ai_analysis.engine import AIAnalysisEngine
from src.config.loader import config_manager
from src.ai.model_constants import (
    AI_PROVIDERS,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
)

class AnalysisWorker(QThread):
    """
    Worker thread to run the AI analysis without freezing the UI.
    """
    finished = pyqtSignal(object) # Returns AIAnalysisOutput or None
    error = pyqtSignal(str)

    def __init__(self, engine: AIAnalysisEngine, symbol: str, timeframe: str, df, model: Optional[str] = None):
        super().__init__()
        self.engine = engine
        self.symbol = symbol
        self.timeframe = timeframe
        self.df = df
        self.model = model

    def run(self):
        import asyncio
        try:
            # We need a new loop for this thread if using async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.engine.run_analysis(self.symbol, self.timeframe, self.df, model=self.model)
            )
            self.finished.emit(result)
            loop.close()
        except Exception as e:
            self.error.emit(str(e))


class AIAnalysisWindow(QDialog):
    """
    Popup window for AI Market Analysis.
    Triggered from Chart Window.
    """
    def __init__(self, parent=None, symbol: str = ""):
        super().__init__(parent)
        self.symbol = symbol
        self.setWindowTitle(f"AI Analysis - {symbol}")
        self.resize(500, 700)
        self.settings = QSettings("OrderPilot", "TradingApp")
        
        # Initialize Engine with API Key from ConfigManager
        api_key = config_manager.get_credential("openai_api_key")
        self.engine = AIAnalysisEngine(api_key=api_key)

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- Header ---
        header_layout = QHBoxLayout()
        self.lbl_header = QLabel(f"<h2>Analysis: {self.symbol}</h2>")
        header_layout.addWidget(self.lbl_header)
        layout.addLayout(header_layout)

        # --- Controls ---
        controls_layout = QHBoxLayout()
        
        # Provider
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(AI_PROVIDERS)
        self.combo_provider.currentTextChanged.connect(self._on_provider_changed)
        controls_layout.addWidget(QLabel("Provider:"))
        controls_layout.addWidget(self.combo_provider)

        # Model
        self.combo_model = QComboBox()
        # Items populated in _load_settings / _on_provider_changed
        controls_layout.addWidget(QLabel("Model:"))
        controls_layout.addWidget(self.combo_model)

        layout.addLayout(controls_layout)

        # --- Action ---
        self.btn_analyze = QPushButton("Start Analysis")
        self.btn_analyze.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(self.btn_analyze)

        # --- Progress ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0) # Infinite loading
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready")
        layout.addWidget(self.lbl_status)

        # --- Output ---
        layout.addWidget(QLabel("Analysis Result:"))
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setPlaceholderText("Result will appear here...")
        layout.addWidget(self.txt_output)

        # --- Footer Actions ---
        footer_layout = QHBoxLayout()
        
        self.btn_copy = QPushButton("Copy JSON")
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        footer_layout.addWidget(self.btn_copy)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        footer_layout.addWidget(self.btn_close)

        layout.addLayout(footer_layout)

        # --- Connections ---
        self.btn_analyze.clicked.connect(self.start_analysis)

    def _load_settings(self):
        """Load settings from QSettings."""
        # Provider
        default_provider = self.settings.value("ai_default_provider", "OpenAI")
        idx = self.combo_provider.findText(default_provider)
        if idx >= 0:
            self.combo_provider.setCurrentIndex(idx)
        
        # Trigger model population
        self._on_provider_changed(self.combo_provider.currentText())

    def _on_provider_changed(self, provider: str):
        """Populate model combo based on selected provider."""
        self.combo_model.blockSignals(True)
        self.combo_model.clear()
        
        models = []
        default_model = ""
        
        if provider == "OpenAI":
            models = OPENAI_MODELS
            default_model = self.settings.value("openai_model", "")
        elif provider == "Anthropic":
            models = ANTHROPIC_MODELS
            default_model = self.settings.value("anthropic_model", "")
        elif provider == "Gemini":
            models = GEMINI_MODELS
            default_model = self.settings.value("gemini_model", "")
            
        self.combo_model.addItems(models)
        
        # Select default if available
        if default_model:
            idx = self.combo_model.findText(default_model)
            if idx >= 0:
                self.combo_model.setCurrentIndex(idx)
                
        self.combo_model.blockSignals(False)

    def showEvent(self, event):
        """Refresh settings when window is shown."""
        super().showEvent(event)
        self._load_settings()

    def start_analysis(self):
        """
        Triggers the analysis engine in a separate thread.
        """
        # 1. Get Data (from parent Chart Window)
        if not hasattr(self.parent(), 'chart_widget') or not hasattr(self.parent().chart_widget, 'data'):
             self.lbl_status.setText("Error: Could not access chart data.")
             return
        
        # Accessing data from main thread is safe here
        try:
            # Try to get data from history manager attached to chart
            df = self.parent().chart_widget.data
            if df is None or df.empty:
                self.lbl_status.setText("Error: No data available in chart.")
                return
        except AttributeError:
             self.lbl_status.setText("Error: Chart data not accessible.")
             return

        # 2. UI State Update
        self.btn_analyze.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Analyzing market structure...")
        self.txt_output.clear()

        # 3. Start Worker
        # TODO: Get actual timeframe string
        timeframe = "1h" 
        selected_model = self.combo_model.currentText()
        
        self.worker = AnalysisWorker(self.engine, self.symbol, timeframe, df, model=selected_model)
        self.worker.finished.connect(self._on_analysis_finished)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.start()

    def _on_analysis_finished(self, result):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Analysis complete.")
        
        if result:
            # Pretty print the Pydantic model
            try:
                json_str = result.model_dump_json(indent=2)
                self.txt_output.setText(json_str)
            except:
                self.txt_output.setText(str(result))
        else:
            self.txt_output.setText("Analysis failed (returned None). Check logs.")

    def _on_analysis_error(self, error_msg):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Error occurred.")
        self.txt_output.setText(f"Error: {error_msg}")

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.txt_output.toPlainText())
        self.lbl_status.setText("Copied to clipboard!")
