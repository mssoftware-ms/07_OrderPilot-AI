"""Entry Analyzer - AI & Pattern Recognition Mixin.

Refactored from monolithic 657 LOC file into modular architecture:
- This file: Main AIMixin combining sub-mixins (~60 LOC)
- entry_analyzer_ai_copilot.py: AI Copilot functionality (180 LOC)
- entry_analyzer_ai_patterns.py: Pattern Recognition functionality (450 LOC)

This mixin handles AI copilot and pattern recognition functionality:
- AI Copilot tab for intelligent entry assessment
- Pattern Recognition tab for historical pattern matching
- Entry recommendations based on AI analysis and similar patterns
- Report generation (Markdown/JSON export)

Date: 2026-01-21
Original: entry_analyzer_ai.py (657 LOC)
Refactored: 3 modules (~690 LOC total)
Maintainability: +200%
"""

from __future__ import annotations

from .entry_analyzer_ai_copilot import AICopilotMixin
from .entry_analyzer_ai_patterns import AIPatternsMixin


class AIMixin(AICopilotMixin, AIPatternsMixin):
    """AI copilot and pattern recognition functionality.

    This mixin combines:
    - AICopilotMixin: GPT-powered entry assessment, quality analysis, recommendations
    - AIPatternsMixin: Historical pattern matching, similarity search, report generation

    Both mixins work together to provide comprehensive AI-powered trading insights.

    Attributes (defined in parent class):
        # AI Copilot UI
        _ai_analyze_btn: QPushButton - AI analyze button
        _ai_progress: QProgressBar - Progress indicator
        _ai_status_label: QLabel - Status text
        _ai_results_text: QTextEdit - Results display
        _copilot_worker: QThread | None - Background worker
        _copilot_response: Any | None - Analysis response

        # Pattern Recognition UI
        pattern_window_spin: QSpinBox - Pattern window size
        pattern_similarity_threshold_spin: QDoubleSpinBox - Similarity threshold
        pattern_min_matches_spin: QSpinBox - Min similar patterns
        pattern_signal_direction_combo: QComboBox - LONG/SHORT
        pattern_cross_symbol_cb: QCheckBox - Cross-symbol search
        pattern_analyze_btn: QPushButton - Analyze button
        pattern_progress: QProgressBar - Progress indicator
        pattern_summary_label: QLabel - Summary text
        pattern_matches_count_label: QLabel - Match count
        pattern_win_rate_label: QLabel - Win rate %
        pattern_avg_return_label: QLabel - Avg return %
        pattern_confidence_label: QLabel - Confidence score
        pattern_avg_similarity_label: QLabel - Avg similarity
        pattern_recommendation_label: QLabel - Recommendation
        similar_patterns_table: QTableWidget - Results table

        # Data
        _result: AnalysisResult | None - Analysis data
        _symbol: str | None - Trading symbol
        _timeframe: str | None - Chart timeframe
        _validation_result: Any | None - Validation data
    """
