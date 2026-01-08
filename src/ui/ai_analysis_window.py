import json
from typing import Optional
from pathlib import Path

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QProgressBar, QApplication, QMessageBox,
    QDialogButtonBox, QTabWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings

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

# Use dedicated analysis logger
analysis_logger = logging.getLogger('ai_analysis')

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

            # Analysis logging
            import logging
            analysis_logger = logging.getLogger('ai_analysis')
            analysis_logger.info("Worker requesting data", extra={
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'timeframe_enum': str(tf_enum),
                'asset_class': self.asset_class,
                'data_source': str(self.data_source),
                'data_source_enum': str(source_enum),
                'step': 'data_request'
            })

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

            # Determine data type
            data_type = "HISTORICAL" if bars else "NONE"

            analysis_logger.info("Data fetched", extra={
                'symbol': self.symbol,
                'bars_count': len(bars) if bars else 0,
                'data_source_used': str(source_used),
                'data_type': data_type,
                'step': 'data_fetch'
            })

            if not bars:
                analysis_logger.error("No data received", extra={
                    'symbol': self.symbol,
                    'data_source': str(source_used),
                    'step': 'data_fetch_error'
                })
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

            # Tag DataFrame with data source type for logging
            df._data_source_type = data_type

            if df.empty:
                analysis_logger.error("DataFrame conversion resulted in empty DataFrame", extra={
                    'symbol': self.symbol,
                    'step': 'dataframe_conversion_error'
                })
                self.error.emit("Converted DataFrame is empty")
                loop.close()
                return

            analysis_logger.info("DataFrame prepared for analysis", extra={
                'symbol': self.symbol,
                'df_shape': df.shape,
                'data_type': data_type,
                'step': 'dataframe_ready'
            })

            # Run analysis with fresh data
            result = loop.run_until_complete(
                self.engine.run_analysis(self.symbol, self.timeframe, df, model=self.model)
            )
            self.finished.emit(result)
            loop.close()
        except Exception as e:
            import traceback
            analysis_logger.error("Worker exception", extra={
                'symbol': self.symbol,
                'error': str(e),
                'error_type': type(e).__name__,
                'step': 'worker_error'
            }, exc_info=True)
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

        # Clear Analyse.log for fresh analysis session
        try:
            analyse_log_path = Path("logs/Analyse.log")
            if analyse_log_path.exists():
                analyse_log_path.write_text("")  # Clear the file
                analysis_logger.info("Analyse.log cleared for new analysis session")
        except Exception as e:
            # Don't fail if log clearing fails
            print(f"Warning: Could not clear Analyse.log: {e}")

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

        # --- Regime Info Panel (Phase 2.2) ---
        self._setup_regime_info_panel(layout)

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

        self.btn_open_log = QPushButton("Logdatei öffnen")
        self.btn_open_log.clicked.connect(self._open_analyse_log)
        footer_layout.addWidget(self.btn_open_log)

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
        # Phase 5.8: Update AI Chat Tab with MarketContext
        self._update_chat_context()

    def _apply_prompt_overrides(self):
        """Read prompt overrides from settings and push into the engine."""
        if not self.engine:
            return

        sys_override = self.settings.value("ai_analysis_system_prompt_override", "")
        tasks_override = self.settings.value("ai_analysis_tasks_prompt_override", "")
        self.engine.apply_prompt_overrides(sys_override, tasks_override)

    def _update_chat_context(self) -> None:
        """Update AI Chat Tab with MarketContext (Phase 5.8)."""
        try:
            if not hasattr(self.parent(), 'chart_widget'):
                return

            chart_widget = self.parent().chart_widget

            # Get chart data
            df = getattr(chart_widget, 'data', None)
            symbol = getattr(chart_widget, 'symbol', getattr(chart_widget, 'current_symbol', self.symbol))
            timeframe = getattr(chart_widget, 'current_timeframe', '1H')

            if df is None or df.empty:
                analysis_logger.debug("No chart data available for chat context")
                return

            # Build MarketContext
            from src.core.trading_bot.market_context_builder import MarketContextBuilder

            builder = MarketContextBuilder()
            context = builder.build(
                symbol=symbol,
                timeframe=timeframe,
                df=df,
            )

            # Update chat tab
            if hasattr(self, 'deep_analysis_tab') and hasattr(self.deep_analysis_tab, 'set_market_context'):
                self.deep_analysis_tab.set_market_context(context)
                analysis_logger.info(f"Chat context updated: {symbol} {timeframe}")

            # Connect draw signal to chart (Phase 5.9)
            self._connect_chat_draw_signal()

        except Exception as e:
            analysis_logger.warning(f"Failed to update chat context: {e}")

    def _connect_chat_draw_signal(self) -> None:
        """Connect AI Chat draw signal to chart widget (Phase 5.9)."""
        try:
            if not hasattr(self, 'deep_analysis_tab'):
                return

            draw_signal = self.deep_analysis_tab.get_draw_zone_signal()
            if draw_signal is None:
                return

            # Disconnect existing connection if any
            try:
                draw_signal.disconnect(self._on_chat_draw_zone)
            except TypeError:
                pass  # Not connected yet

            # Connect to chart draw handler
            draw_signal.connect(self._on_chat_draw_zone)
            analysis_logger.debug("Chat draw signal connected")

        except Exception as e:
            analysis_logger.warning(f"Failed to connect chat draw signal: {e}")

    def _on_chat_draw_zone(self, zone_type: str, top: float, bottom: float, label: str) -> None:
        """Handle draw zone request from AI Chat (Phase 5.9).

        Args:
            zone_type: "support" or "resistance"
            top: Zone top price
            bottom: Zone bottom price
            label: Zone label
        """
        try:
            if not hasattr(self.parent(), 'chart_widget'):
                return

            chart_widget = self.parent().chart_widget

            # Use the chart's add_zone method if available
            if hasattr(chart_widget, 'add_zone'):
                import time
                start_time = int(time.time()) - 86400 * 7  # Last 7 days
                end_time = int(time.time()) + 86400  # Tomorrow

                # Map zone type to color
                color_map = {
                    "support": "rgba(46, 125, 50, 0.25)",
                    "resistance": "rgba(198, 40, 40, 0.25)",
                }
                color = color_map.get(zone_type.lower(), "rgba(100, 100, 100, 0.25)")

                zone_id = f"ai_chat_{zone_type}_{int(time.time())}"

                chart_widget.add_zone(
                    start_time=start_time,
                    end_time=end_time,
                    top_price=top,
                    bottom_price=bottom,
                    zone_type=zone_type,
                    label=f"AI: {label}",
                    color=color,
                    zone_id=zone_id,
                )
                analysis_logger.info(f"Chat zone drawn: {zone_type} {bottom:.2f}-{top:.2f}")

        except Exception as e:
            analysis_logger.error(f"Failed to draw chat zone: {e}")

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
             analysis_logger.error("Start analysis failed: chart widget not accessible", extra={
                 'tab': 'overview',
                 'action': 'start_analysis',
                 'step': 'context_error'
             })
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
                analysis_logger.error("History manager not available", extra={
                    'tab': 'overview',
                    'action': 'start_analysis',
                    'step': 'validation_error'
                })
                self.lbl_status.setText("Error: History manager not available.")
                return

            if not asset_class or not data_source:
                analysis_logger.error("Asset class or data source not configured", extra={
                    'tab': 'overview',
                    'action': 'start_analysis',
                    'asset_class': asset_class,
                    'data_source': data_source,
                    'step': 'validation_error'
                })
                self.lbl_status.setText("Error: Asset class or data source not configured.")
                return

        except Exception as e:
             analysis_logger.error("Failed to access chart context", extra={
                 'tab': 'overview',
                 'action': 'start_analysis',
                 'error': str(e),
                 'error_type': type(e).__name__,
                 'step': 'context_error'
             }, exc_info=True)
             self.lbl_status.setText(f"Error: Could not access chart context: {str(e)}")
             return

        # 2. Validate Engine
        if not self.engine:
            analysis_logger.error("Analysis engine not initialized", extra={
                'tab': 'overview',
                'action': 'start_analysis',
                'step': 'engine_error'
            })
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
        selected_provider = self.combo_provider.currentText()

        analysis_logger.info("Starting analysis from UI", extra={
            'tab': 'overview',
            'action': 'start_analysis',
            'symbol': symbol,
            'timeframe': timeframe,
            'asset_class': asset_class,
            'data_source': str(data_source),
            'model': selected_model,
            'provider': selected_provider,
            'step': 'worker_start'
        })

        self.worker = AnalysisWorker(
            self.engine, symbol, timeframe,
            history_manager, asset_class, data_source,
            model=selected_model
        )
        self.worker.finished.connect(self._on_analysis_finished)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.start()

    def _setup_regime_info_panel(self, layout: QVBoxLayout) -> None:
        """Setup the regime info panel (Phase 2.2)."""
        try:
            from src.ui.widgets.regime_badge_widget import RegimeInfoPanel

            self._regime_panel = RegimeInfoPanel()
            layout.addWidget(self._regime_panel)

            # Add separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("color: #444;")
            layout.addWidget(separator)

            analysis_logger.debug("Regime info panel added to overview tab")
        except ImportError as e:
            analysis_logger.warning(f"Could not add regime info panel: {e}")
            self._regime_panel = None

    def update_regime_info(self, result) -> None:
        """
        Update the regime info panel with detection results.

        Args:
            result: RegimeResult from RegimeDetectorService
        """
        if hasattr(self, "_regime_panel") and self._regime_panel:
            self._regime_panel.set_regime_result(result)

    def _detect_and_update_regime(self, df) -> None:
        """
        Detect regime from DataFrame and update panel.

        Args:
            df: DataFrame with OHLCV data
        """
        if df is None or df.empty:
            return

        try:
            from src.core.trading_bot.regime_detector import get_regime_detector

            detector = get_regime_detector()
            result = detector.detect(df)
            self.update_regime_info(result)
        except Exception as e:
            analysis_logger.warning(f"Failed to detect regime: {e}")

    def _on_analysis_finished(self, result):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Analysis complete.")

        if result:
            analysis_logger.info("Analysis results received in UI", extra={
                'tab': 'overview',
                'action': 'results_received',
                'result_type': type(result).__name__,
                'step': 'ui_update'
            })
            # Pretty print the Pydantic model
            try:
                # Convert to dict for DeepAnalysisWidget
                result_dict = result.model_dump()
                self.deep_analysis_tab.update_from_initial_analysis(result_dict)

                json_str = result.model_dump_json(indent=2)
                self.txt_output.setText(json_str)

                analysis_logger.info("Analysis results displayed", extra={
                    'tab': 'overview',
                    'action': 'results_displayed',
                    'result_length': len(json_str),
                    'step': 'ui_update'
                })
            except Exception as e:
                analysis_logger.error("Error processing results", extra={
                    'tab': 'overview',
                    'action': 'results_processing',
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'step': 'ui_error'
                }, exc_info=True)
                self.txt_output.setText(str(result))
                print(f"Error transferring data to DeepAnalysis: {e}")
        else:
            analysis_logger.warning("Analysis returned None", extra={
                'tab': 'overview',
                'action': 'results_received',
                'step': 'ui_warning'
            })
            self.txt_output.setText("Analysis failed (returned None). Check logs.")

    def _on_analysis_error(self, error_msg):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Error occurred.")
        self.txt_output.setText(f"Error: {error_msg}")

        analysis_logger.error("Analysis error reported to UI", extra={
            'tab': 'overview',
            'action': 'error_received',
            'error_message': error_msg,
            'step': 'ui_error'
        })

        # Show popup ONLY for data source/provider errors
        if "Ungültiger Datenquellen-Typ" in error_msg or "Datenquelle" in error_msg:
            self._show_error("Provider/Chart Fehler", error_msg)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.txt_output.toPlainText())
        self.lbl_status.setText("Copied to clipboard!")

    def _open_analyse_log(self):
        """Open Analyse.log file in default text editor."""
        import os
        import platform

        log_file = Path("logs/Analyse.log")

        if not log_file.exists():
            QMessageBox.warning(
                self,
                "Logdatei nicht gefunden",
                "Die Analyse.log Datei existiert noch nicht. Führen Sie erst eine Analyse durch."
            )
            return

        try:
            # Open file with default application
            if platform.system() == 'Windows':
                os.startfile(str(log_file))
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{log_file}"')
            else:  # Linux
                os.system(f'xdg-open "{log_file}"')
            self.lbl_status.setText("Logdatei geöffnet.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler beim Öffnen",
                f"Konnte Logdatei nicht öffnen: {e}"
            )

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
