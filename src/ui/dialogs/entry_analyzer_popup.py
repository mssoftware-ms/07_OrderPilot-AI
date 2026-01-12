"""Entry Analyzer Popup Dialog.

Displays analysis results for the visible chart range,
including optimized indicator sets and entry signals.

Phase 5: Added AI Copilot, Validation, Filters, Reports.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult, EntryEvent

logger = logging.getLogger(__name__)


class CopilotWorker(QThread):
    """Background worker for AI Copilot analysis."""

    finished = pyqtSignal(object)  # CopilotResponse
    error = pyqtSignal(str)

    def __init__(
        self,
        analysis: Any,
        symbol: str,
        timeframe: str,
        validation: Any = None,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._analysis = analysis
        self._symbol = symbol
        self._timeframe = timeframe
        self._validation = validation

    def run(self) -> None:
        try:
            from src.analysis.visible_chart.entry_copilot import get_entry_analysis

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    get_entry_analysis(
                        self._analysis,
                        self._symbol,
                        self._timeframe,
                        self._validation,
                    )
                )
                if result:
                    self.finished.emit(result)
                else:
                    self.error.emit("AI analysis returned no result")
            finally:
                loop.close()
        except Exception as e:
            logger.exception("Copilot analysis failed")
            self.error.emit(str(e))


class ValidationWorker(QThread):
    """Background worker for walk-forward validation."""

    finished = pyqtSignal(object)  # ValidationResult
    error = pyqtSignal(str)

    def __init__(
        self,
        analysis: Any,
        candles: list[dict],
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._analysis = analysis
        self._candles = candles

    def run(self) -> None:
        try:
            from src.analysis.visible_chart.validation import validate_with_walkforward

            result = validate_with_walkforward(
                entries=self._analysis.entries,
                candles=self._candles,
                indicator_set=self._analysis.best_set,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Validation failed")
            self.error.emit(str(e))


class EntryAnalyzerPopup(QDialog):
    """Popup dialog for Entry Analyzer results.

    Displays:
    - Current regime detection
    - Optimized indicator set with parameters
    - List of detected entries (LONG green / SHORT red)
    - AI Copilot recommendations (Phase 5)
    - Walk-forward validation (Phase 4)
    - Report generation (Phase 4.5)
    """

    analyze_requested = pyqtSignal()
    draw_entries_requested = pyqtSignal(list)
    clear_entries_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("🎯 Entry Analyzer - Visible Chart")
        self.setMinimumSize(750, 650)
        self.resize(850, 700)

        self._result: AnalysisResult | None = None
        self._validation_result: Any = None
        self._copilot_response: Any = None
        self._candles: list[dict] = []
        self._symbol: str = "UNKNOWN"
        self._timeframe: str = "1m"
        self._copilot_worker: CopilotWorker | None = None
        self._validation_worker: ValidationWorker | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header with status
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget for different views
        self._tabs = QTabWidget()

        # Tab 1: Analysis (entries + indicators)
        analysis_tab = QWidget()
        self._setup_analysis_tab(analysis_tab)
        self._tabs.addTab(analysis_tab, "📊 Analysis")

        # Tab 2: AI Copilot
        ai_tab = QWidget()
        self._setup_ai_tab(ai_tab)
        self._tabs.addTab(ai_tab, "🤖 AI Copilot")

        # Tab 3: Validation
        validation_tab = QWidget()
        self._setup_validation_tab(validation_tab)
        self._tabs.addTab(validation_tab, "✅ Validation")

        layout.addWidget(self._tabs, stretch=1)

        # Footer with actions
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 10)

        self._regime_label = QLabel("Regime: --")
        self._regime_label.setStyleSheet(
            "font-weight: bold; font-size: 14pt; padding: 5px;"
        )
        layout.addWidget(self._regime_label)

        layout.addStretch()

        self._signal_count_label = QLabel("Signals: 0 LONG / 0 SHORT")
        self._signal_count_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(self._signal_count_label)

        self._signal_rate_label = QLabel("Rate: 0/h")
        self._signal_rate_label.setStyleSheet("font-size: 11pt; color: #888;")
        layout.addWidget(self._signal_rate_label)

        return widget

    def _setup_analysis_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Indicator Set info
        indicator_group = self._create_indicator_group()
        splitter.addWidget(indicator_group)

        # Bottom: Entry table
        entries_group = self._create_entries_group()
        splitter.addWidget(entries_group)

        splitter.setSizes([200, 300])
        layout.addWidget(splitter)

    def _setup_ai_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        # AI Status / Action row
        action_row = QHBoxLayout()
        self._ai_analyze_btn = QPushButton("🤖 Run AI Analysis")
        self._ai_analyze_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #8B5CF6; color: white;"
        )
        self._ai_analyze_btn.clicked.connect(self._on_ai_analyze_clicked)
        action_row.addWidget(self._ai_analyze_btn)

        self._ai_progress = QProgressBar()
        self._ai_progress.setMaximumWidth(150)
        self._ai_progress.setVisible(False)
        action_row.addWidget(self._ai_progress)

        self._ai_status_label = QLabel("Ready")
        self._ai_status_label.setStyleSheet("color: #888;")
        action_row.addWidget(self._ai_status_label)
        action_row.addStretch()
        layout.addLayout(action_row)

        # AI Results
        self._ai_results_text = QTextEdit()
        self._ai_results_text.setReadOnly(True)
        self._ai_results_text.setStyleSheet(
            "font-family: monospace; background-color: #1a1a1a; color: #e0e0e0;"
        )
        self._ai_results_text.setPlaceholderText(
            "AI analysis results will appear here...\n\n"
            "Click 'Run AI Analysis' to get:\n"
            "• Entry quality assessments\n"
            "• Risk/reward analysis\n"
            "• Best entry recommendation\n"
            "• Trade suggestions"
        )
        layout.addWidget(self._ai_results_text)

    def _setup_validation_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        # Validation action row
        action_row = QHBoxLayout()
        self._validate_btn = QPushButton("✅ Run Validation")
        self._validate_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #10B981; color: white;"
        )
        self._validate_btn.clicked.connect(self._on_validate_clicked)
        action_row.addWidget(self._validate_btn)

        self._val_progress = QProgressBar()
        self._val_progress.setMaximumWidth(150)
        self._val_progress.setVisible(False)
        action_row.addWidget(self._val_progress)

        self._val_status_label = QLabel("Ready")
        self._val_status_label.setStyleSheet("color: #888;")
        action_row.addWidget(self._val_status_label)
        action_row.addStretch()
        layout.addLayout(action_row)

        # Validation summary
        self._val_summary = QLabel("No validation results yet")
        self._val_summary.setStyleSheet("font-size: 12pt; padding: 10px;")
        layout.addWidget(self._val_summary)

        # Folds table
        self._folds_table = QTableWidget()
        self._folds_table.setColumnCount(6)
        self._folds_table.setHorizontalHeaderLabels(
            ["Fold", "Train Score", "Test Score", "Ratio", "OOS WR", "Overfit"]
        )
        self._folds_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self._folds_table)

    def _create_indicator_group(self) -> QGroupBox:
        group = QGroupBox("📊 Optimized Indicator Set")
        layout = QVBoxLayout(group)

        self._set_name_label = QLabel("Active Set: --")
        self._set_name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._set_name_label)

        self._params_table = QTableWidget()
        self._params_table.setColumnCount(3)
        self._params_table.setHorizontalHeaderLabels(["Family", "Parameter", "Value"])
        self._params_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._params_table.setMaximumHeight(150)
        layout.addWidget(self._params_table)

        self._score_label = QLabel("Score: --")
        layout.addWidget(self._score_label)

        self._alternatives_label = QLabel("Alternatives: --")
        self._alternatives_label.setStyleSheet("color: #888; font-size: 10pt;")
        self._alternatives_label.setVisible(False)
        layout.addWidget(self._alternatives_label)

        return group

    def _create_entries_group(self) -> QGroupBox:
        group = QGroupBox("🎯 Detected Entries")
        layout = QVBoxLayout(group)

        # Filter toggle
        filter_row = QHBoxLayout()
        self._filter_checkbox = QCheckBox("Apply Trade Filters (no-trade zones)")
        self._filter_checkbox.setChecked(False)
        self._filter_checkbox.setToolTip(
            "Filter out entries during volatility spikes, low volume, etc."
        )
        filter_row.addWidget(self._filter_checkbox)
        self._filter_stats_label = QLabel("")
        self._filter_stats_label.setStyleSheet("color: #888;")
        filter_row.addWidget(self._filter_stats_label)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self._entries_table = QTableWidget()
        self._entries_table.setColumnCount(5)
        self._entries_table.setHorizontalHeaderLabels(
            ["Time", "Side", "Price", "Confidence", "Reasons"]
        )
        self._entries_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._entries_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self._entries_table)

        return group

    def _create_footer(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        # Analyze button
        self._analyze_btn = QPushButton("🔄 Analyze Visible Range")
        self._analyze_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #3b82f6; color: white;"
        )
        self._analyze_btn.clicked.connect(self._on_analyze_clicked)
        layout.addWidget(self._analyze_btn)

        self._progress = QProgressBar()
        self._progress.setMaximumWidth(150)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        layout.addStretch()

        # Report button
        self._report_btn = QPushButton("📄 Generate Report")
        self._report_btn.setEnabled(False)
        self._report_btn.clicked.connect(self._on_report_clicked)
        layout.addWidget(self._report_btn)

        # Draw entries button
        self._draw_btn = QPushButton("📍 Draw on Chart")
        self._draw_btn.setEnabled(False)
        self._draw_btn.clicked.connect(self._on_draw_clicked)
        layout.addWidget(self._draw_btn)

        # Clear button
        self._clear_btn = QPushButton("🗑️ Clear Entries")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self._clear_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return widget

    def set_context(self, symbol: str, timeframe: str, candles: list[dict]) -> None:
        """Set context for AI/Validation."""
        self._symbol = symbol
        self._timeframe = timeframe
        self._candles = candles

    def set_analyzing(self, analyzing: bool) -> None:
        """Set analyzing state and update progress bar.

        Issue #27: Added debug logging for progress bar state changes.
        """
        # Import debug logger
        try:
            from src.analysis.visible_chart.debug_logger import debug_logger
        except ImportError:
            debug_logger = logger

        debug_logger.info("PROGRESS BAR: set_analyzing(%s)", analyzing)

        self._analyze_btn.setEnabled(not analyzing)
        self._progress.setVisible(analyzing)
        if analyzing:
            self._progress.setRange(0, 0)  # Indeterminate mode (busy spinner)
            debug_logger.debug("Progress bar: indeterminate mode (analyzing)")
        else:
            self._progress.setRange(0, 100)  # Determinate mode
            self._progress.setValue(100)  # Complete
            debug_logger.debug("Progress bar: complete (100%%)")

        # Force GUI update
        self._progress.update()
        debug_logger.debug("Progress bar updated, visible=%s", analyzing)

    def set_result(self, result: AnalysisResult) -> None:
        self._result = result

        # Update regime
        regime_colors = {
            "trend_up": "#22c55e",
            "trend_down": "#ef4444",
            "range": "#f59e0b",
            "high_vol": "#a855f7",
            "squeeze": "#3b82f6",
            "no_trade": "#6b7280",
        }
        regime_text = result.regime.value.replace("_", " ").title()
        color = regime_colors.get(result.regime.value, "#888")
        self._regime_label.setText(f"Regime: {regime_text}")
        self._regime_label.setStyleSheet(
            f"font-weight: bold; font-size: 14pt; padding: 5px; color: {color};"
        )

        # Update signal counts
        self._signal_count_label.setText(
            f"Signals: {result.long_count} LONG / {result.short_count} SHORT"
        )
        self._signal_rate_label.setText(f"Rate: {result.signal_rate_per_hour:.1f}/h")

        # Update indicator set
        if result.active_set:
            self._set_name_label.setText(f"Active Set: {result.active_set.name}")
            self._score_label.setText(f"Score: {result.active_set.score:.3f}")
            self._update_params_table(result.active_set.parameters)

            if result.alternative_sets:
                alt_names = [s.name for s in result.alternative_sets[:2]]
                self._alternatives_label.setText(f"Alternatives: {', '.join(alt_names)}")
                self._alternatives_label.setVisible(True)
            else:
                self._alternatives_label.setVisible(False)
        else:
            self._set_name_label.setText("Active Set: Default (no optimization)")
            self._score_label.setText("Score: --")
            self._params_table.setRowCount(0)
            self._alternatives_label.setVisible(False)

        # Update entries table
        self._update_entries_table(result.entries)

        # Enable buttons
        self._draw_btn.setEnabled(len(result.entries) > 0)
        self._report_btn.setEnabled(True)
        self._ai_analyze_btn.setEnabled(True)
        self._validate_btn.setEnabled(len(result.entries) > 0 and len(self._candles) > 0)

        logger.info(
            "Analysis result displayed: %d entries, regime=%s",
            len(result.entries),
            result.regime.value,
        )

    def _update_params_table(self, params: dict) -> None:
        self._params_table.setRowCount(0)
        row = 0

        for family, family_params in params.items():
            if isinstance(family_params, dict):
                for param, value in family_params.items():
                    self._params_table.insertRow(row)
                    self._params_table.setItem(row, 0, QTableWidgetItem(family))
                    self._params_table.setItem(row, 1, QTableWidgetItem(param))
                    self._params_table.setItem(row, 2, QTableWidgetItem(str(value)))
                    row += 1
            else:
                self._params_table.insertRow(row)
                self._params_table.setItem(row, 0, QTableWidgetItem(family))
                self._params_table.setItem(row, 1, QTableWidgetItem("value"))
                self._params_table.setItem(row, 2, QTableWidgetItem(str(family_params)))
                row += 1

    def _update_entries_table(self, entries: list[EntryEvent]) -> None:
        self._entries_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            time_str = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M")
            self._entries_table.setItem(row, 0, QTableWidgetItem(time_str))

            side_item = QTableWidgetItem(entry.side.value.upper())
            self._entries_table.setItem(row, 1, side_item)

            self._entries_table.setItem(row, 2, QTableWidgetItem(f"{entry.price:.2f}"))
            self._entries_table.setItem(row, 3, QTableWidgetItem(f"{entry.confidence:.0%}"))

            reasons_item = QTableWidgetItem(", ".join(entry.reason_tags))
            self._entries_table.setItem(row, 4, reasons_item)

    def _on_analyze_clicked(self) -> None:
        self.set_analyzing(True)
        self.analyze_requested.emit()

    def _on_draw_clicked(self) -> None:
        if self._result and self._result.entries:
            self.draw_entries_requested.emit(self._result.entries)

    def _on_clear_clicked(self) -> None:
        self.clear_entries_requested.emit()

    def _on_ai_analyze_clicked(self) -> None:
        if not self._result:
            QMessageBox.warning(self, "No Data", "Run analysis first")
            return

        self._ai_analyze_btn.setEnabled(False)
        self._ai_progress.setVisible(True)
        self._ai_progress.setRange(0, 0)
        self._ai_status_label.setText("Running AI analysis...")

        self._copilot_worker = CopilotWorker(
            analysis=self._result,
            symbol=self._symbol,
            timeframe=self._timeframe,
            validation=self._validation_result,
            parent=self,
        )
        self._copilot_worker.finished.connect(self._on_ai_finished)
        self._copilot_worker.error.connect(self._on_ai_error)
        self._copilot_worker.start()

    def _on_ai_finished(self, response: Any) -> None:
        self._copilot_response = response
        self._ai_progress.setVisible(False)
        self._ai_analyze_btn.setEnabled(True)
        self._ai_status_label.setText("Complete")

        # Format results
        lines = ["# AI Copilot Analysis\n"]

        lines.append(f"## Recommendation: {response.recommended_action.upper()}\n")
        lines.append(f"{response.reasoning}\n")

        lines.append(f"\n## Market Assessment\n{response.summary.market_assessment}")
        lines.append(f"\n**Bias:** {response.summary.overall_bias}")
        lines.append(f"**Best Entry:** #{response.summary.best_entry_idx + 1}" if response.summary.best_entry_idx >= 0 else "**Best Entry:** None recommended")

        if response.summary.risk_warning:
            lines.append(f"\n⚠️ **Risk Warning:** {response.summary.risk_warning}")

        if response.summary.key_levels:
            levels = ", ".join(f"{lv:.2f}" for lv in response.summary.key_levels)
            lines.append(f"\n**Key Levels:** {levels}")

        lines.append("\n\n## Entry Assessments\n")
        for i, assess in enumerate(response.entry_assessments):
            lines.append(f"### Entry {i + 1}: {assess.quality.value.upper()}")
            lines.append(f"Confidence adjustment: {assess.confidence_adjustment:+.1%}")
            lines.append(f"**Strengths:** {', '.join(assess.strengths)}")
            lines.append(f"**Weaknesses:** {', '.join(assess.weaknesses)}")
            lines.append(f"**Suggestion:** {assess.trade_suggestion}\n")

        self._ai_results_text.setPlainText("\n".join(lines))
        logger.info("AI analysis complete: %s", response.recommended_action)

    def _on_ai_error(self, error_msg: str) -> None:
        self._ai_progress.setVisible(False)
        self._ai_analyze_btn.setEnabled(True)
        self._ai_status_label.setText("Error")
        self._ai_results_text.setPlainText(f"❌ AI Analysis Error:\n\n{error_msg}")
        logger.error("AI analysis error: %s", error_msg)

    def _on_validate_clicked(self) -> None:
        if not self._result or not self._candles:
            QMessageBox.warning(self, "No Data", "Run analysis first and ensure candle data is available")
            return

        self._validate_btn.setEnabled(False)
        self._val_progress.setVisible(True)
        self._val_progress.setRange(0, 0)
        self._val_status_label.setText("Running validation...")

        self._validation_worker = ValidationWorker(
            analysis=self._result,
            candles=self._candles,
            parent=self,
        )
        self._validation_worker.finished.connect(self._on_validation_finished)
        self._validation_worker.error.connect(self._on_validation_error)
        self._validation_worker.start()

    def _on_validation_finished(self, result: Any) -> None:
        self._validation_result = result
        self._val_progress.setVisible(False)
        self._validate_btn.setEnabled(True)

        status = "✅ PASSED" if result.is_valid else "❌ FAILED"
        self._val_status_label.setText(status)

        summary = (
            f"**Status:** {status}\n"
            f"**OOS Score:** {result.avg_test_score:.3f}\n"
            f"**OOS Win Rate:** {result.oos_win_rate:.1%}\n"
            f"**Train/Test Ratio:** {result.avg_train_test_ratio:.2f}\n"
            f"**Total OOS Trades:** {result.total_oos_trades}"
        )
        if result.failure_reasons:
            summary += f"\n**Issues:** {', '.join(result.failure_reasons)}"
        self._val_summary.setText(summary)

        # Update folds table
        self._folds_table.setRowCount(len(result.folds))
        for row, fold in enumerate(result.folds):
            self._folds_table.setItem(row, 0, QTableWidgetItem(str(fold.fold_idx)))
            self._folds_table.setItem(row, 1, QTableWidgetItem(f"{fold.train_score:.3f}"))
            self._folds_table.setItem(row, 2, QTableWidgetItem(f"{fold.test_score:.3f}"))
            self._folds_table.setItem(row, 3, QTableWidgetItem(f"{fold.train_test_ratio:.2f}"))
            self._folds_table.setItem(row, 4, QTableWidgetItem(f"{fold.test_win_rate:.1%}"))
            overfit = "Yes" if fold.is_overfit else "No"
            self._folds_table.setItem(row, 5, QTableWidgetItem(overfit))

        logger.info("Validation complete: %s", "passed" if result.is_valid else "failed")

    def _on_validation_error(self, error_msg: str) -> None:
        self._val_progress.setVisible(False)
        self._validate_btn.setEnabled(True)
        self._val_status_label.setText("Error")
        self._val_summary.setText(f"❌ Validation Error: {error_msg}")
        logger.error("Validation error: %s", error_msg)

    def _on_report_clicked(self) -> None:
        if not self._result:
            QMessageBox.warning(self, "No Data", "Run analysis first")
            return

        # Ask for save location
        default_name = f"entry_analysis_{self._symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path.home() / f"{default_name}.md"),
            "Markdown (*.md);;JSON (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            from src.analysis.visible_chart.report_generator import (
                ReportGenerator,
                create_report_from_analysis,
            )

            # Create report data
            report_data = create_report_from_analysis(
                analysis=self._result,
                symbol=self._symbol,
                timeframe=self._timeframe,
                validation=self._validation_result,
            )

            generator = ReportGenerator()
            path = Path(file_path)

            if path.suffix == ".json":
                import json
                content = generator.generate_json(report_data)
                path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            else:
                content = generator.generate_markdown(report_data)
                path.write_text(content, encoding="utf-8")

            QMessageBox.information(self, "Report Saved", f"Report saved to:\n{path}")
            logger.info("Report saved: %s", path)

        except Exception as e:
            logger.exception("Report generation failed")
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")
