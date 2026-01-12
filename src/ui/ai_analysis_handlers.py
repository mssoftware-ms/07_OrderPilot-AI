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

from PyQt6.QtWidgets import QMessageBox, QApplication, QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

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
        # Storage for the last AI payload (for "Show Payload" feature)
        self._last_payload_data: dict | None = None

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
        # Issue #20: Get parent chart window for strategy simulator access
        chart_window = self.parent.parent()

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

            # Issue #20: Extract strategy configurations from Strategy Simulator tab
            strategy_configs = self._extract_strategy_configs(chart_window)

            # Store pre-analysis data for "Show Payload" feature
            self._last_payload_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "asset_class": str(asset_class) if asset_class else None,
                "data_source": str(data_source) if data_source else None,
                "strategy_configs": strategy_configs,
                "timestamp": None,  # Will be set by engine
                "regime": None,  # Will be set by engine
                "technicals": None,  # Will be set by engine
                "structure": None,  # Will be set by engine
                "last_candles_summary": None,  # Will be set by engine
            }

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

        # Issue #20: Pass strategy configs to worker
        self.parent.worker = AnalysisWorker(
            self.parent.engine, symbol, timeframe,
            history_manager, asset_class, data_source,
            model=selected_model,
            strategy_configs=strategy_configs
        )
        self.parent.worker.finished.connect(self.on_analysis_finished)
        self.parent.worker.error.connect(self.on_analysis_error)
        self.parent.worker.start()

    def on_analysis_finished(self, result):
        """Handle analysis completion."""
        self.parent.btn_analyze.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        self.parent.lbl_status.setText("Analysis complete.")

        # Enable "Show Payload" button after successful analysis
        if hasattr(self.parent, 'btn_show_payload'):
            self.parent.btn_show_payload.setEnabled(True)

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

                # Push result into Daily Strategy tab (if available)
                chart_window = self.parent.parent()
                if chart_window and hasattr(chart_window, "_update_daily_analysis_view"):
                    chart_window._update_daily_analysis_view(result_dict)

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

    def show_payload_popup(self):
        """
        Show a popup dialog with all data that was sent to the AI.

        Displays the full AIAnalysisInput payload in a formatted JSON view.
        """
        if not self.parent.engine:
            QMessageBox.warning(
                self.parent,
                "Keine Daten",
                "AI Engine nicht initialisiert."
            )
            return

        # Get the last analysis input from the engine
        last_input = getattr(self.parent.engine, '_last_analysis_input', None)

        if not last_input:
            QMessageBox.information(
                self.parent,
                "Keine Daten",
                "Es wurden noch keine Daten an die KI gesendet.\n\n"
                "Führen Sie zuerst 'Start Analysis' aus."
            )
            return

        # Create popup dialog
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("📋 AI Analysis Payload - Gesendete Daten")
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 700)

        layout = QVBoxLayout(dialog)

        # Header
        header_label = QLabel(
            "<h3>Alle Daten, die an die KI gesendet wurden:</h3>"
            "<p style='color: gray;'>Diese Daten werden im JSON-Format an das LLM übermittelt.</p>"
        )
        layout.addWidget(header_label)

        # JSON content
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(
            "font-family: 'Consolas', 'Monaco', monospace; "
            "font-size: 11px; "
            "background-color: #1e1e1e; "
            "color: #d4d4d4; "
            "padding: 10px;"
        )

        try:
            # Serialize the AIAnalysisInput to pretty JSON
            json_content = last_input.model_dump_json(indent=2)
            text_edit.setPlainText(json_content)
        except Exception as e:
            text_edit.setPlainText(f"Fehler beim Serialisieren: {e}\n\nRohdaten:\n{str(last_input)}")

        layout.addWidget(text_edit)

        # Summary info
        summary_parts = []
        summary_parts.append(f"<b>Symbol:</b> {last_input.symbol}")
        summary_parts.append(f"<b>Timeframe:</b> {last_input.timeframe}")
        summary_parts.append(f"<b>Regime:</b> {last_input.regime.value if last_input.regime else 'N/A'}")
        summary_parts.append(f"<b>Timestamp:</b> {last_input.timestamp}")

        if last_input.strategy_configs:
            summary_parts.append(f"<b>Strategien:</b> {len(last_input.strategy_configs)}")

        if last_input.last_candles_summary:
            summary_parts.append(f"<b>Kerzen:</b> {len(last_input.last_candles_summary)}")

        summary_label = QLabel(" | ".join(summary_parts))
        summary_label.setStyleSheet("color: #888; font-size: 10px; padding: 5px;")
        layout.addWidget(summary_label)

        # Buttons
        button_layout = QHBoxLayout()

        btn_copy = QPushButton("📋 In Zwischenablage kopieren")
        btn_copy.clicked.connect(lambda: self._copy_payload_to_clipboard(text_edit.toPlainText()))
        button_layout.addWidget(btn_copy)

        button_layout.addStretch()

        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(dialog.accept)
        button_layout.addWidget(btn_close)

        layout.addLayout(button_layout)

        dialog.exec()

    def _copy_payload_to_clipboard(self, text: str):
        """Copy payload text to clipboard and show confirmation."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.parent.lbl_status.setText("Payload in Zwischenablage kopiert!")

    def _extract_strategy_configs(self, chart_window) -> list[dict] | None:
        """
        Issue #20: Extract strategy configurations from Strategy Simulator tab.

        Extracts all available strategies with their current parameter values
        from the Strategy Simulator UI.

        Args:
            chart_window: The parent chart window that contains Strategy Simulator mixin

        Returns:
            List of strategy config dicts or None if not available
        """
        try:
            from src.core.simulator import (
                StrategyName,
                get_strategy_parameters,
                STRATEGY_PARAMETER_REGISTRY,
            )

            strategy_configs = []

            # Check if chart window has strategy simulator components
            if not hasattr(chart_window, 'simulator_strategy_combo'):
                analysis_logger.info("Strategy simulator not available in chart window", extra={
                    'tab': 'overview',
                    'action': 'extract_strategies',
                    'step': 'skipped'
                })
                return None

            # Get the currently selected strategy and its parameters from UI
            current_strategy_name = None
            current_params = {}

            if hasattr(chart_window, '_get_simulator_strategy_name'):
                current_strategy_name = chart_window._get_simulator_strategy_name()

            if hasattr(chart_window, '_get_simulator_parameters'):
                current_params = chart_window._get_simulator_parameters()

            # Extract ALL strategies from registry with their definitions
            for strategy_enum, param_config in STRATEGY_PARAMETER_REGISTRY.items():
                strategy_data = {
                    "strategy_name": param_config.display_name,
                    "strategy_id": strategy_enum.value,
                    "description": param_config.description,
                    "parameters": {},
                    "is_selected": False,
                }

                # Build parameters with defaults and descriptions
                for param_def in param_config.parameters:
                    param_info = {
                        "value": param_def.default,
                        "display_name": param_def.display_name,
                        "type": param_def.param_type,
                        "description": param_def.description,
                    }
                    if param_def.min_value is not None:
                        param_info["min"] = param_def.min_value
                    if param_def.max_value is not None:
                        param_info["max"] = param_def.max_value

                    strategy_data["parameters"][param_def.name] = param_info

                # If this is the currently selected strategy, use the UI values
                if current_strategy_name and (
                    current_strategy_name == param_config.display_name or
                    current_strategy_name == strategy_enum.value or
                    current_strategy_name.lower().replace('_', ' ') == param_config.display_name.lower()
                ):
                    strategy_data["is_selected"] = True
                    # Override defaults with current UI values
                    for param_name, param_value in current_params.items():
                        if param_name in strategy_data["parameters"]:
                            strategy_data["parameters"][param_name]["value"] = param_value

                strategy_configs.append(strategy_data)

            # Sort: selected strategy first, then alphabetically
            strategy_configs.sort(key=lambda x: (not x["is_selected"], x["strategy_name"]))

            analysis_logger.info("Extracted strategy configurations", extra={
                'tab': 'overview',
                'action': 'extract_strategies',
                'strategies_count': len(strategy_configs),
                'selected_strategy': current_strategy_name,
                'step': 'success'
            })

            return strategy_configs

        except Exception as e:
            analysis_logger.warning(f"Failed to extract strategy configs: {e}", extra={
                'tab': 'overview',
                'action': 'extract_strategies',
                'error': str(e),
                'error_type': type(e).__name__,
                'step': 'error'
            })
            return None
