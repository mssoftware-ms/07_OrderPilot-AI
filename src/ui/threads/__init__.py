"""UI threads for background processing.

REFACTORED (Phase 3.2.3):
- indicator_optimization_thread.py split into 3 modules:
  - indicator_optimization_core.py (main QThread)
  - indicator_optimization_phases.py (regime detection, params, indicator calc)
  - indicator_optimization_results.py (scoring, metrics)
- Backward compatible imports maintained
"""

# Import from core file (refactored, composition pattern)
from .indicator_optimization_core import IndicatorOptimizationThread

__all__ = ['IndicatorOptimizationThread']
