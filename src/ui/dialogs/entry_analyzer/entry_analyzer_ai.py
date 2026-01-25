"""Entry Analyzer - AI Copilot Mixin.

This mixin handles AI Copilot functionality for intelligent entry assessment:
- AI Copilot tab for GPT-powered entry analysis
- Entry recommendations based on AI analysis
- Quality scoring and confidence assessment
- Report generation (Markdown/JSON export)

Date: 2026-01-25
Previous: Combined AI + Pattern Recognition (657 LOC)
Current: AI Copilot only (after Pattern Recognition removal)
"""

from __future__ import annotations

from .entry_analyzer_ai_copilot import AICopilotMixin


class AIMixin(AICopilotMixin):
    """AI Copilot functionality for Entry Analyzer.

    This mixin provides GPT-powered entry assessment with:
    - Intelligent analysis of entry signals
    - Quality scoring and confidence levels
    - Trading recommendations with risk assessment
    - Report generation and export

    Attributes (defined in parent class):
        # AI Copilot UI
        _ai_analyze_btn: QPushButton - AI analyze button
        _ai_progress: QProgressBar - Progress indicator
        _ai_status_label: QLabel - Status text
        _ai_results_text: QTextEdit - Results display
        _copilot_worker: QThread | None - Background worker
        _copilot_response: Any | None - Analysis response

        # Data
        _result: AnalysisResult | None - Analysis data
        _symbol: str | None - Trading symbol
        _timeframe: str | None - Chart timeframe
        _validation_result: Any | None - Validation data
    """

    pass
