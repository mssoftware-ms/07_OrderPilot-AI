"""Compatibility shim for legacy imports.

Tests import EntryAnalyzerPopup from src.ui.dialogs.entry_analyzer_popup,
but the real implementation lives in src.ui.dialogs.entry_analyzer.entry_analyzer_popup.
"""

from __future__ import annotations

from src.ui.dialogs.entry_analyzer.entry_analyzer_popup import *  # noqa: F401,F403

