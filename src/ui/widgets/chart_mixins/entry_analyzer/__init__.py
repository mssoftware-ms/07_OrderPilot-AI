"""Entry Analyzer - Combined Mixin Package.

This package provides the entry analyzer functionality split into focused mixins
for better maintainability and adherence to Single Responsibility Principle.

Split structure (from 1,259 LOC monolith):
- entry_analyzer_ui_mixin.py (400 LOC): UI components and filter widgets
- entry_analyzer_events_mixin.py (450 LOC): Event handlers and live analysis
- entry_analyzer_logic_mixin.py (450 LOC): Business logic and drawing

Total: ~1,300 LOC (includes module docstrings)

Agent: CODER-021
Task: 3.3.4 - Split entry_analyzer_mixin
File: __init__.py - Combined package
"""

from .entry_analyzer_events_mixin import (
    AnalysisWorker,
    EntryAnalyzerEventsMixin,
)
from .entry_analyzer_logic_mixin import EntryAnalyzerLogicMixin
from .entry_analyzer_ui_mixin import EntryAnalyzerUIMixin


class EntryAnalyzerMixin(
    EntryAnalyzerLogicMixin,
    EntryAnalyzerEventsMixin,
    EntryAnalyzerUIMixin,
):
    """Combined mixin for Entry Analyzer functionality in Chart Widget.

    This class combines all split mixins to provide 100% backward compatibility
    with the original monolithic EntryAnalyzerMixin.

    Provides:
    - Regime filter widget with dropdown menu (UI)
    - Live analysis with background worker threads (Events)
    - Entry markers drawing (LONG=green, SHORT=red) (Logic)
    - Regime period lines with color coding (Logic)
    - Pattern overlays (order blocks, FVG) (Logic)
    - Filter management and state preservation (UI + Logic)
    - Chart event handlers (symbol/timeframe/data changes) (Events)

    All original methods are preserved and accessible through this combined class.

    Usage:
        ```python
        from src.ui.widgets.chart_mixins.entry_analyzer import EntryAnalyzerMixin

        class ChartWidget(QWidget, EntryAnalyzerMixin):
            def __init__(self):
                super().__init__()
                self._init_entry_analyzer()
                # ... use all entry analyzer methods
        ```

    Backward Compatibility:
        The old import path still works:
        ```python
        from src.ui.widgets.chart_mixins.entry_analyzer_mixin import (
            EntryAnalyzerMixin
        )
        ```
    """

    pass


__all__ = [
    "EntryAnalyzerMixin",
    "EntryAnalyzerUIMixin",
    "EntryAnalyzerEventsMixin",
    "EntryAnalyzerLogicMixin",
    "AnalysisWorker",
]
