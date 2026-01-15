"""Chart Analysis Chatbot for OrderPilot-AI.

This module provides an AI-powered chatbot that analyzes the currently
open chart and provides trading recommendations. Features:

- Trend analysis and detection
- Support/Resistance level identification
- Entry/Exit recommendations
- Risk assessment (stop-loss, take-profit)
- Conversational Q&A about the chart
- Chat history persistence per chart window (symbol + timeframe)

Usage:
    The ChartChatMixin is added to ChartWindow and provides a dock widget
    on the right side of the chart. Users can:
    - Click "Analyze Chart" for full analysis
    - Ask questions about the chart
    - Export chat history as Markdown
"""

from .analyzer import ChartAnalyzer
from .chat_service import ChartChatService
from .context_builder import ChartContext, ChartContextBuilder
from .history_store import HistoryStore
from .mixin import ChartChatMixin
from .models import (
    ChatMessage,
    ChartAnalysisResult,
    EntryExitRecommendation,
    MessageRole,
    PatternInfo,
    QuickAnswerResult,
    RiskAssessment,
    SignalStrength,
    SupportResistanceLevel,
    TrendDirection,
)

__all__ = [
    # Services
    "ChartChatService",
    "ChartAnalyzer",
    "ChartContextBuilder",
    "ChartContext",
    "HistoryStore",
    # UI
    "ChartChatMixin",
    # Models
    "ChatMessage",
    "MessageRole",
    "TrendDirection",
    "SignalStrength",
    "SupportResistanceLevel",
    "EntryExitRecommendation",
    "RiskAssessment",
    "PatternInfo",
    "QuickAnswerResult",
    "ChartAnalysisResult",
]

__version__ = "1.0.0"
