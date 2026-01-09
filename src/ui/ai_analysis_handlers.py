"""AI Analysis Handlers - Event handlers and analysis logic.

Refactored from 822 LOC monolith using composition pattern.

Module 3/5 of ai_analysis_window.py split.

Contains:
- start_analysis(): Main analysis trigger
- on_analysis_finished(): Handle analysis completion
- on_analysis_error(): Handle analysis error
- copy_to_clipboard(): Copy result to clipboard
- open_analyse_log(): Open log file
- open_prompt_editor(): Open prompt editor
- apply_prompt_overrides(): Apply prompt overrides
- show_error(): Show error dialog
"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox, QApplication

from src.core.ai_analysis.prompt import PromptComposer

if TYPE_CHECKING:
    pass

analysis_logger = logging.getLogger('ai_analysis')


class AIAnalysisHandlers:
    """Helper für AIAnalysisWindow Handlers (Analysis, Errors, UI Actions)."""

    def __init__(self, parent):
        """
        Args:
            parent: AIAnalysisWindow Instanz
        """
        self.parent = parent

    def show_error(self, title: str, message: str):
        """Show error message box popup."""
        QMessageBox.critical(self.parent, title, message, QMessageBox.StandardButton.Ok)

    def start_analysis(self):
        """
        Triggers the analysis engine in a separate thread.
        Worker will fetch fresh data from history_manager.
        """
        from src.ui.ai_analysis_worker import AnalysisWorker

        # 1. Get chart context
        if not hasattr(self.parent.parent(), 'chart_widget'):
             analysis_logger.error("Start analysis failed: chart widget not accessible", extra={
                 'tab': 'overview',
                 'action': 'start_analysis',
                 'step': 'context_error'
             })
             self.parent.lbl_status.setText("Error: Could not access chart widget.")
             return

        chart_widget = self.parent.parent().chart_widget

        # Get required context from chart
        try:
            history_manager = getattr(chart_widget, 'history_manager', None)
            symbol = getattr(chart_widget, 'symbol', self.parent.symbol)
            timeframe = getattr(chart_widget, 'current_timeframe', '1T')
            asset_class = getattr(chart_widget, 'current_asset_class', None)
            data_source = getattr(chart_widget, 'current_data_source', None)

            if not history_manager:
                analysis_logger.error("History manager not available", extra={
                    'tab': 'overview',
                    'action': 'start_analysis',
                    'step': 'validation_error'
                })
                self.parent.lbl_status.setText("Error: History manager not available.")
                return

            if not asset_class or not data_source:
                analysis_logger.error("Asset class or data source not configured", extra={
                    'tab': 'overview',
                    'action': 'start_analysis',
                    'asset_class': asset_class,
                    'data_source': data_source,
                    'step': 'validation_error'
                })
                self.parent.lbl_status.setText("Error: Asset class or data source not configured.")
                return

        except Exception as e:
             analysis_logger.error("Failed to access chart context", extra={
                 'tab': 'overview',
                 'action': 'start_analysis',
                 'error': str(e),
                 'error_type': type(e).__name__,
                 'step': 'context_error'
             }, exc_info=True)
             self.parent.lbl_status.setText(f"Error: Could not access chart context: {str(e)}")
             return

        # 2. Validate Engine
        if not self.parent.engine:
            analysis_logger.error("Analysis engine not initialized", extra={
                'tab': 'overview',
                'action': 'start_analysis',
                'step': 'engine_error'
            })
            self.parent.lbl_status.setText("Error: OpenAI API key missing or not configured")
            return

        # Inject context into DeepAnalysisWidget
        if hasattr(self.parent, 'deep_analysis_tab'):
            self.parent.deep_analysis_tab.context.set_market_context(
                history_manager, symbol, asset_class, data_source
            )

        # 3. UI State Update
        self.parent.btn_analyze.setEnabled(False)
        self.parent.progress_bar.setVisible(True)
        self.parent.lbl_status.setText(f"Fetching fresh data and analyzing {symbol}...")
        self.parent.txt_output.clear()

        # 4. Start Worker (will fetch fresh data async)
        selected_model = self.parent.combo_model.currentText()
        selected_provider = self.parent.combo_provider.currentText()

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

        self.parent.worker = AnalysisWorker(
            self.parent.engine, symbol, timeframe,
            history_manager, asset_class, data_source,
            model=selected_model
        )
        self.parent.worker.finished.connect(self.on_analysis_finished)
        self.parent.worker.error.connect(self.on_analysis_error)
        self.parent.worker.start()

    def on_analysis_finished(self, result):
        """Handle analysis completion."""
        self.parent.btn_analyze.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        self.parent.lbl_status.setText("Analysis complete.")

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
                self.parent.deep_analysis_tab.update_from_initial_analysis(result_dict)

                json_str = result.model_dump_json(indent=2)
                self.parent.txt_output.setText(json_str)

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
                self.parent.txt_output.setText(str(result))
                print(f"Error transferring data to DeepAnalysis: {e}")
        else:
            analysis_logger.warning("Analysis returned None", extra={
                'tab': 'overview',
                'action': 'results_received',
                'step': 'ui_warning'
            })
            self.parent.txt_output.setText("Analysis failed (returned None). Check logs.")

    def on_analysis_error(self, error_msg):
        """Handle analysis error."""
        self.parent.btn_analyze.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        self.parent.lbl_status.setText("Error occurred.")
        self.parent.txt_output.setText(f"Error: {error_msg}")

        analysis_logger.error("Analysis error reported to UI", extra={
            'tab': 'overview',
            'action': 'error_received',
            'error_message': error_msg,
            'step': 'ui_error'
        })

        # Show popup ONLY for data source/provider errors
        if "Ungültiger Datenquellen-Typ" in error_msg or "Datenquelle" in error_msg:
            self.show_error("Provider/Chart Fehler", error_msg)

    def copy_to_clipboard(self):
        """Copy analysis result to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.parent.txt_output.toPlainText())
        self.parent.lbl_status.setText("Copied to clipboard!")

    def open_analyse_log(self):
        """Open Analyse.log file in default text editor."""
        log_file = Path("logs/Analyse.log")

        if not log_file.exists():
            QMessageBox.warning(
                self.parent,
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
            self.parent.lbl_status.setText("Logdatei geöffnet.")
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Fehler beim Öffnen",
                f"Konnte Logdatei nicht öffnen: {e}"
            )

    def open_prompt_editor(self):
        """Popup dialog allowing the user to edit system and task prompts."""
        from src.ui.ai_analysis_prompt_editor import PromptEditorDialog

        if not self.parent.engine:
            self.show_error("AI Prompt", "AI service is not initialized (missing API key).")
            return

        current_system = self.parent.settings.value("ai_analysis_system_prompt_override", "")
        current_tasks = self.parent.settings.value("ai_analysis_tasks_prompt_override", "")

        dialog = PromptEditorDialog(
            parent=self.parent,
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

            self.parent.settings.setValue("ai_analysis_system_prompt_override", sys_value)
            self.parent.settings.setValue("ai_analysis_tasks_prompt_override", tasks_value)

            self.parent.engine.apply_prompt_overrides(sys_value, tasks_value)
            self.parent.lbl_status.setText("Prompt updated.")

    def apply_prompt_overrides(self):
        """Read prompt overrides from settings and push into the engine."""
        if not self.parent.engine:
            return

        sys_override = self.parent.settings.value("ai_analysis_system_prompt_override", "")
        tasks_override = self.parent.settings.value("ai_analysis_tasks_prompt_override", "")
        self.parent.engine.apply_prompt_overrides(sys_override, tasks_override)
