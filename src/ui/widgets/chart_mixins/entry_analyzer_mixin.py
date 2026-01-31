"""Entry Analyzer Mixin for Chart Widget - Backward Compatibility Wrapper.

This module provides backward compatibility for imports.
The actual implementation has been split into modular mixins in the
entry_analyzer package.

For new code, prefer importing from the package directly:
    from src.ui.widgets.chart_mixins.entry_analyzer import EntryAnalyzerMixin

This wrapper maintains compatibility with existing code:
    from src.ui.widgets.chart_mixins.entry_analyzer_mixin import EntryAnalyzerMixin

Agent: CODER-021
Task: 3.3.4 - entry_analyzer_mixin refactoring
"""

from __future__ import annotations

# Import from the new modular package
from .entry_analyzer import (
    AnalysisWorker,
    EntryAnalyzerEventsMixin,
    EntryAnalyzerLogicMixin,
    EntryAnalyzerMixin,
    EntryAnalyzerUIMixin,
)

# Re-export for backward compatibility
__all__ = [
    "EntryAnalyzerMixin",
    "EntryAnalyzerUIMixin",
    "EntryAnalyzerEventsMixin",
    "EntryAnalyzerLogicMixin",
    "AnalysisWorker",
]
