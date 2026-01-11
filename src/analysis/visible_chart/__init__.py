"""Visible Chart Analysis Module.

Analyzes the visible chart range and generates entry signals
for the entire visible window (not just current candle).

Phase 1: MVP with rules-based detection
Phase 2: FastOptimizer with caching and overfitting protection
"""

from __future__ import annotations

from .analyzer import VisibleChartAnalyzer
from .cache import AnalyzerCache, get_analyzer_cache, reset_analyzer_cache
from .types import (
    AnalysisResult,
    EntryEvent,
    EntrySide,
    IndicatorSet,
    RegimeType,
    VisibleRange,
)

__all__ = [
    "VisibleChartAnalyzer",
    "AnalyzerCache",
    "get_analyzer_cache",
    "reset_analyzer_cache",
    "AnalysisResult",
    "EntryEvent",
    "EntrySide",
    "IndicatorSet",
    "RegimeType",
    "VisibleRange",
]
