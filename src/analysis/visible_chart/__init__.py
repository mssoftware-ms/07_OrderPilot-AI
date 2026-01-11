"""Visible Chart Analysis Module.

Analyzes the visible chart range and generates entry signals
for the entire visible window (not just current candle).

Phase 1: MVP with rules-based detection
Phase 2: FastOptimizer with caching and overfitting protection
Phase 3: Live background analysis with scheduler
Phase 4: Walk-forward validation, trade filters, report generation
"""

from __future__ import annotations

from .analyzer import VisibleChartAnalyzer
from .background_runner import BackgroundRunner, RunnerConfig, PerformanceMetrics
from .cache import AnalyzerCache, get_analyzer_cache, reset_analyzer_cache
from .report_generator import (
    ReportConfig,
    ReportData,
    ReportGenerator,
    create_report_from_analysis,
)
from .trade_filters import (
    FilterConfig,
    FilterReason,
    FilterResult,
    FilterStats,
    TradeFilter,
    create_crypto_filter,
    create_default_filter,
)
from .types import (
    AnalysisResult,
    EntryEvent,
    EntrySide,
    IndicatorSet,
    RegimeType,
    VisibleRange,
)
from .validation import (
    FoldResult,
    ValidationConfig,
    ValidationResult,
    WalkForwardValidator,
    validate_with_walkforward,
)

__all__ = [
    # Core
    "VisibleChartAnalyzer",
    # Background Runner
    "BackgroundRunner",
    "RunnerConfig",
    "PerformanceMetrics",
    # Cache
    "AnalyzerCache",
    "get_analyzer_cache",
    "reset_analyzer_cache",
    # Validation (Phase 4.1)
    "FoldResult",
    "ValidationConfig",
    "ValidationResult",
    "WalkForwardValidator",
    "validate_with_walkforward",
    # Trade Filters (Phase 4.4)
    "FilterConfig",
    "FilterReason",
    "FilterResult",
    "FilterStats",
    "TradeFilter",
    "create_crypto_filter",
    "create_default_filter",
    # Report Generator (Phase 4.5)
    "ReportConfig",
    "ReportData",
    "ReportGenerator",
    "create_report_from_analysis",
    # Types
    "AnalysisResult",
    "EntryEvent",
    "EntrySide",
    "IndicatorSet",
    "RegimeType",
    "VisibleRange",
]
