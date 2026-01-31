"""Regime Optimization - Combined Mixin Package.

This package provides the regime optimization functionality split into focused mixins
for better maintainability and adherence to Single Responsibility Principle.

Split structure (from 2,057 LOC monolith):
- regime_optimization_init.py (269 LOC): UI setup and initialization
- regime_optimization_events.py (413 LOC): Optimization lifecycle events
- regime_optimization_actions.py (423 LOC): User action handlers
- regime_optimization_updates.py (555 LOC): Data transformations
- regime_optimization_rendering.py (555 LOC): UI rendering and display

Total: 2,215 LOC (includes module docstrings)

Agent: CODER-013
Task: 3.1.3 - Split regime_optimization_mixin
File: __init__.py - Combined package
"""

from .regime_optimization_actions import RegimeOptimizationActionsMixin
from .regime_optimization_events import RegimeOptimizationEventsMixin
from .regime_optimization_init import RegimeOptimizationInitMixin
from .regime_optimization_rendering import RegimeOptimizationRenderingMixin
from .regime_optimization_updates import RegimeOptimizationUpdatesMixin


class RegimeOptimizationMixin(
    RegimeOptimizationInitMixin,
    RegimeOptimizationEventsMixin,
    RegimeOptimizationActionsMixin,
    RegimeOptimizationUpdatesMixin,
    RegimeOptimizationRenderingMixin,
):
    """Combined mixin for Regime Optimization tab in Entry Analyzer.

    This class combines all split mixins to provide 100% backward compatibility
    with the original monolithic RegimeOptimizationMixin.

    Provides:
        - Start/Stop optimization controls (Events)
        - Progress tracking with ETA (Events)
        - Live top-5 results table (Rendering)
        - TPE-based optimization execution (Events)
        - Export and history management (Actions)
        - Apply to config functionality (Actions)
        - Chart drawing for selected results (Rendering)
        - Parameter transformation logic (Updates)

    All 26 original methods are preserved and accessible through this combined class.

    Usage:
        ```python
        from src.ui.dialogs.entry_analyzer.regime_optimization import RegimeOptimizationMixin

        class EntryAnalyzer(QDialog, RegimeOptimizationMixin):
            def __init__(self):
                super().__init__()
                # ... use all regime optimization methods
        ```

    Backward Compatibility:
        The old import path still works:
        ```python
        from src.ui.dialogs.entry_analyzer.entry_analyzer_regime_optimization_mixin import (
            RegimeOptimizationMixin
        )
        ```
    """

    pass


__all__ = [
    "RegimeOptimizationMixin",
    "RegimeOptimizationInitMixin",
    "RegimeOptimizationEventsMixin",
    "RegimeOptimizationActionsMixin",
    "RegimeOptimizationUpdatesMixin",
    "RegimeOptimizationRenderingMixin",
]
