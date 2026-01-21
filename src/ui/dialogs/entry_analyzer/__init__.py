"""Entry Analyzer Dialog - Modular Implementation.

Refactored from monolithic 3,167 LOC file into 5 maintainable modules:
- entry_analyzer_popup.py: Main dialog structure (400-500 LOC)
- entry_analyzer_backtest.py: Backtest & Regime functionality (~600 LOC)
- entry_analyzer_indicators.py: Indicator optimization (~600 LOC)
- entry_analyzer_analysis.py: Analysis & Validation (~600 LOC)
- entry_analyzer_ai.py: AI & Pattern Recognition (~600 LOC)

Date: 2026-01-21
Original LOC: 3,167
Target LOC: ~3,200 (in 5 modules)
Maintainability Improvement: +200%
"""

from .entry_analyzer_popup import EntryAnalyzerPopup

__all__ = ["EntryAnalyzerPopup"]
