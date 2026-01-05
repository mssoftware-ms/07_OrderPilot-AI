import json
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QProgressBar, QApplication, QMessageBox,
    QDialogButtonBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QClipboard

from src.core.ai_analysis.engine import AIAnalysisEngine
from src.core.ai_analysis.prompt import PromptComposer
from src.config.loader import config_manager
from src.ai.model_constants import (
    AI_PROVIDERS,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
)
from src.ui.widgets.deep_analysis_window import DeepAnalysisWidget

class AnalysisWorker(QThread):
    """
    Worker thread to run the AI analysis without freezing the UI.
    Fetches fresh data from history_manager before analysis.
    """
    finished = pyqtSignal(object) # Returns AIAnalysisOutput or None
    error = pyqtSignal(str)

    def __init__(self, engine: AIAnalysisEngine, symbol: str, timeframe: str,
                 history_manager, asset_class, data_source, model: Optional[str] = None):
        super().__init__()
        self.engine = engine
        self.symbol = symbol
        self.timeframe = timeframe
        self.history_manager = history_manager
        self.asset_class = asset_class
        self.data_source = data_source
        self.model = model

    def run(self):
        import asyncio
        from datetime import datetime, timedelta, timezone
        from src.core.market_data.history_provider import DataRequest, Timeframe as TF, DataSource

        try:
            # We need a new loop for this thread if using async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Fetch FRESH data from history_manager (async)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)  # 1 week lookback

            # Map timeframe string to Timeframe enum
            timeframe_map = {
                "1T": TF.MINUTE_1,
                "5T": TF.MINUTE_5,
                "15T": TF.MINUTE_15,
                "1H": TF.HOUR_1,
                "1D": TF.DAY_1
            }
            tf_enum = timeframe_map.get(self.timeframe, TF.MINUTE_1)

            # Convert data_source to enum if it's a string
            # NO FALLBACK - use exact data source from active chart or fail
            if isinstance(self.data_source, str):
                source_str = self.data_source.upper().replace(" ", "_")
                source_map = {
                    "ALPACA": DataSource.ALPACA,
                    "ALPACA_CRYPTO": DataSource.ALPACA_CRYPTO,
                    "BITUNIX": DataSource.BITUNIX,
                    "YAHOO": DataSource.YAHOO,
                    "YAHOO_FINANCE": DataSource.YAHOO,
                    "ALPHA_VANTAGE": DataSource.ALPHA_VANTAGE,
                    "FINNHUB": DataSource.FINNHUB,
                    "IBKR": DataSource.IBKR,
                    "DATABASE": DataSource.DATABASE
                }
                source_enum = source_map.get(source_str, None)

                if source_enum is None:
                    self.error.emit(f"Ungültiger Datenquellen-Typ: '{self.data_source}'. Bitte Chart-Datenquelle überprüfen.")
                    loop.close()
                    return
            else:
                source_enum = self.data_source

            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"AI Analysis: Requesting data for {self.symbol}")
            logger.info(f"  Timeframe: {self.timeframe} -> {tf_enum}")
            logger.info(f"  Asset Class: {self.asset_class}")
            logger.info(f"  Data Source: {self.data_source} -> {source_enum}")

            request = DataRequest(
                symbol=self.symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=tf_enum,
                asset_class=self.asset_class,
                source=source_enum
            )

            bars, source_used = loop.run_until_complete(
                self.history_manager.fetch_data(request)
            )

            logger.info(f"AI Analysis: Received {len(bars) if bars else 0} bars from {source_used}")

            if not bars:
                self.error.emit(f"Failed to fetch data from {source_used}")
                loop.close()
                return

            # Convert bars to DataFrame
            import pandas as pd
            data = []
            for bar in bars:
                data.append({
                    'time': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': float(bar.volume)
                })

            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)

            if df.empty:
                self.error.emit("Converted DataFrame is empty")
                loop.close()
                return

            # Run analysis with fresh data
            result = loop.run_until_complete(
                self.engine.run_analysis(self.symbol, self.timeframe, df, model=self.model)
            )
            self.finished.emit(result)
            loop.close()
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")


class AIAnalysisWindow(QDialog):
    """
    Popup window for AI Market Analysis.
    Triggered from Chart Window.
    """
    def __init__(self, parent=None, symbol: str = ""):
        super().__init__(parent)
        self.symbol = symbol
        self.setWindowTitle(f"AI Analysis - {symbol}")
        self.resize(800, 800)
        self.settings = QSettings("OrderPilot", "TradingApp")

        self.engine: Optional[AIAnalysisEngine] = None
        try:
            api_key = config_manager.get_credential("openai_api_key")
            self.engine = AIAnalysisEngine(api_key=api_key)
        except Exception:
            self.engine = None

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Tab 1: Overview (Original UI) ---
        self.overview_tab = QWidget()
        self._init_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")

        # --- Tab 2: Deep Analysis (New) ---
        self.deep_analysis_tab = DeepAnalysisWidget()
        self.tabs.addTab(self.deep_analysis_tab, "Deep Analysis")

    def _init_overview_tab(self):
        layout = QVBoxLayout(self.overview_tab)

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
        action_layout = QHBoxLayout()

        self.btn_analyze = QPushButton("Start Analysis")
        self.btn_analyze.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; padding: 8px;")
        action_layout.addWidget(self.btn_analyze)

        self.btn_edit_prompt = QPushButton("Edit Prompt")
        self.btn_edit_prompt.clicked.connect(self._open_prompt_editor)
        action_layout.addWidget(self.btn_edit_prompt)

        action_layout.addStretch()
        layout.addLayout(action_layout)

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

        # Prompt overrides
        self._apply_prompt_overrides()

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

    def _apply_prompt_overrides(self):
        """Read prompt overrides from settings and push into the engine."""
        if not self.engine:
            return

        sys_override = self.settings.value("ai_analysis_system_prompt_override", "")
        tasks_override = self.settings.value("ai_analysis_tasks_prompt_override", "")
        self.engine.apply_prompt_overrides(sys_override, tasks_override)

    def _show_error(self, title: str, message: str):
        """Show error message box popup."""
        QMessageBox.critical(self, title, message, QMessageBox.StandardButton.Ok)

    def start_analysis(self):
        """
        Triggers the analysis engine in a separate thread.
        Worker will fetch fresh data from history_manager.
        """
        # 1. Get chart context
        if not hasattr(self.parent(), 'chart_widget'):
             self.lbl_status.setText("Error: Could not access chart widget.")
             return

        chart_widget = self.parent().chart_widget

        # Get required context from chart
        try:
            history_manager = getattr(chart_widget, 'history_manager', None)
            symbol = getattr(chart_widget, 'symbol', self.symbol)
            timeframe = getattr(chart_widget, 'current_timeframe', '1T')
            asset_class = getattr(chart_widget, 'current_asset_class', None)
            data_source = getattr(chart_widget, 'current_data_source', None)

            if not history_manager:
                self.lbl_status.setText("Error: History manager not available.")
                return

            if not asset_class or not data_source:
                self.lbl_status.setText("Error: Asset class or data source not configured.")
                return

        except Exception as e:
             self.lbl_status.setText(f"Error: Could not access chart context: {str(e)}")
             return

        # 2. Validate Engine
        if not self.engine:
            self.lbl_status.setText("Error: OpenAI API key missing or not configured")
            return

        # Inject context into DeepAnalysisWidget
        if hasattr(self, 'deep_analysis_tab'):
            self.deep_analysis_tab.context.set_market_context(
                history_manager, symbol, asset_class, data_source
            )

        # 3. UI State Update
        self.btn_analyze.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText(f"Fetching fresh data and analyzing {symbol}...")
        self.txt_output.clear()

        # 4. Start Worker (will fetch fresh data async)
        selected_model = self.combo_model.currentText()

        self.worker = AnalysisWorker(
            self.engine, symbol, timeframe,
            history_manager, asset_class, data_source,
            model=selected_model
        )
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
                # Convert to dict for DeepAnalysisWidget
                result_dict = result.model_dump()
                self.deep_analysis_tab.update_from_initial_analysis(result_dict)
                
                json_str = result.model_dump_json(indent=2)
                self.txt_output.setText(json_str)
            except Exception as e:
                self.txt_output.setText(str(result))
                print(f"Error transferring data to DeepAnalysis: {e}")
        else:
            self.txt_output.setText("Analysis failed (returned None). Check logs.")

    def _on_analysis_error(self, error_msg):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Error occurred.")
        self.txt_output.setText(f"Error: {error_msg}")

        # Show popup ONLY for data source/provider errors
        if "Ungültiger Datenquellen-Typ" in error_msg or "Datenquelle" in error_msg:
            self._show_error("Provider/Chart Fehler", error_msg)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.txt_output.toPlainText())
        self.lbl_status.setText("Copied to clipboard!")

    def _open_prompt_editor(self):
        """Popup dialog allowing the user to edit system and task prompts."""
        if not self.engine:
            self._show_error("AI Prompt", "AI service is not initialized (missing API key).")
            return

        current_system = self.settings.value("ai_analysis_system_prompt_override", "")
        current_tasks = self.settings.value("ai_analysis_tasks_prompt_override", "")

        dialog = PromptEditorDialog(
            parent=self,
            system_prompt=current_system or PromptComposer.DEFAULT_SYSTEM_PROMPT,
            tasks_prompt=current_tasks or PromptComposer.DEFAULT_TASKS_PROMPT,
            default_system=PromptComposer.DEFAULT_SYSTEM_PROMPT,
            default_tasks=PromptComposer.DEFAULT_TASKS_PROMPT,
        )

        if dialog.exec():
            sys_prompt, tasks_prompt = dialog.get_values()

            # Store empty string when equal to defaults to keep QSettings minimal
            sys_value = "" if sys_prompt.strip() == PromptComposer.DEFAULT_SYSTEM_PROMPT.strip() else sys_prompt
            tasks_value = "" if tasks_prompt.strip() == PromptComposer.DEFAULT_TASKS_PROMPT.strip() else tasks_prompt

            self.settings.setValue("ai_analysis_system_prompt_override", sys_value)
            self.settings.setValue("ai_analysis_tasks_prompt_override", tasks_value)

            self.engine.apply_prompt_overrides(sys_value, tasks_value)
            self.lbl_status.setText("Prompt updated.")


class PromptEditorDialog(QDialog):
    """Small dialog to edit analysis prompts."""

    def __init__(self, parent, system_prompt: str, tasks_prompt: str, default_system: str, default_tasks: str):
        super().__init__(parent)
        self.setWindowTitle("Edit Analysis Prompts")
        self.resize(700, 600)
        self.default_system = default_system
        self.default_tasks = default_tasks

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

    def get_values(self):
        return self.txt_system.toPlainText(), self.txt_tasks.toPlainText()
