"""Entry Analyzer - AI Copilot Mixin.

Extracted from entry_analyzer_ai.py to keep files under 550 LOC.
Handles AI-powered entry assessment using GPT models:
- AI Copilot tab with entry quality analysis
- Entry recommendations based on AI analysis
- Risk/reward assessment and trade suggestions

Date: 2026-01-21
LOC: ~180
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Import icon provider (Issue #12)
from src.ui.icons import get_icon

if TYPE_CHECKING:
    from PyQt6.QtCore import QThread

logger = logging.getLogger(__name__)


class AICopilotMixin:
    """AI Copilot functionality for entry analysis.

    Provides GPT-powered intelligent entry assessment with:
    - Entry quality grading (excellent/good/poor)
    - Risk/reward analysis
    - Market assessment and bias detection
    - Per-entry strengths, weaknesses, and suggestions
    - Best entry recommendation

    Attributes (defined in parent class):
        _ai_analyze_btn: QPushButton - AI analyze button
        _ai_progress: QProgressBar - Progress indicator
        _ai_status_label: QLabel - Status text
        _ai_results_text: QTextEdit - Results display
        _copilot_worker: QThread | None - Background worker
        _copilot_response: Any | None - Analysis response
        _result: AnalysisResult | None - Analysis data
        _symbol: str | None - Trading symbol
        _timeframe: str | None - Chart timeframe
        _validation_result: Any | None - Validation data
    """

    # Type hints for parent class attributes
    _ai_analyze_btn: QPushButton
    _ai_progress: QProgressBar
    _ai_status_label: QLabel
    _ai_results_text: QTextEdit
    _copilot_worker: QThread | None
    _copilot_response: Any | None
    _result: Any | None
    _symbol: str | None
    _timeframe: str | None
    _validation_result: Any | None

    def _setup_ai_tab(self, tab: QWidget) -> None:
        """Setup AI Copilot tab.

        Original: entry_analyzer_popup.py:934-972

        Creates:
        - AI Analyze button (GPT-powered analysis)
        - Progress bar
        - Status label
        - Results text area with markdown-like formatting
        """
        layout = QVBoxLayout(tab)

        # AI Status / Action row (Issue #12: Material Design icon + theme color)
        action_row = QHBoxLayout()
        self._ai_analyze_btn = QPushButton(" Run AI Analysis")
        self._ai_analyze_btn.setIcon(get_icon("smart_toy"))
        self._ai_analyze_btn.setProperty("class", "primary")  # Use theme primary color
        self._ai_analyze_btn.clicked.connect(self._on_ai_analyze_clicked)
        action_row.addWidget(self._ai_analyze_btn)

        self._ai_progress = QProgressBar()
        self._ai_progress.setMaximumWidth(150)
        self._ai_progress.setVisible(False)
        action_row.addWidget(self._ai_progress)

        self._ai_status_label = QLabel("Ready")
        self._ai_status_label.setProperty("class", "status-label")  # Issue #12: Use theme
        action_row.addWidget(self._ai_status_label)
        action_row.addStretch()
        layout.addLayout(action_row)

        # AI Results (Issue #12: Remove hardcoded colors, use theme)
        self._ai_results_text = QTextEdit()
        self._ai_results_text.setReadOnly(True)
        self._ai_results_text.setStyleSheet("font-family: monospace;")  # Theme handles colors
        self._ai_results_text.setPlaceholderText(
            "AI analysis results will appear here...\n\n"
            "Click 'Run AI Analysis' to get:\n"
            "• Entry quality assessments\n"
            "• Risk/reward analysis\n"
            "• Best entry recommendation\n"
            "• Trade suggestions"
        )
        layout.addWidget(self._ai_results_text)

    def _on_ai_analyze_clicked(self) -> None:
        """Handle AI analyze button click.

        Original: entry_analyzer_popup.py:1253-1272

        Starts AI analysis with CopilotWorker:
        - Checks for analysis result
        - Disables AI button and shows progress
        - Creates CopilotWorker thread
        - Connects finished/error signals
        - Starts background analysis
        """
        if not self._result:
            QMessageBox.warning(self, "No Data", "Run analysis first")
            return

        self._ai_analyze_btn.setEnabled(False)
        self._ai_progress.setVisible(True)
        self._ai_progress.setRange(0, 0)
        self._ai_status_label.setText("Running AI analysis...")

        from .entry_analyzer_workers import CopilotWorker

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
        """Handle AI analysis completion.

        Original: entry_analyzer_popup.py:1274-1306

        Displays:
        - Recommended action (BUY/SELL/HOLD)
        - Reasoning and summary
        - Market assessment and bias
        - Best entry recommendation
        - Risk warnings
        - Key levels (support/resistance)
        - Per-entry assessments with quality, strengths, weaknesses, suggestions
        """
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
        lines.append(
            f"**Best Entry:** #{response.summary.best_entry_idx + 1}"
            if response.summary.best_entry_idx >= 0
            else "**Best Entry:** None recommended"
        )

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
        """Handle AI analysis error.

        Original: entry_analyzer_popup.py:1308-1313

        Displays error message, hides progress, re-enables button.
        """
        self._ai_progress.setVisible(False)
        self._ai_analyze_btn.setEnabled(True)
        self._ai_status_label.setText("Error")
        self._ai_results_text.setPlainText(f"❌ AI Analysis Error:\n\n{error_msg}")
        logger.error("AI analysis error: %s", error_msg)
