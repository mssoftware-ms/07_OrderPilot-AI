"""Toolbar Mixin for EmbeddedTradingViewChart.

Refactored from 861 LOC monolith using composition pattern.

Module 4/4 of toolbar_mixin.py split (Main Orchestrator).
"""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import QToolBar

from .toolbar_mixin_row1 import ToolbarMixinRow1
from .toolbar_mixin_row2 import ToolbarMixinRow2
from .toolbar_mixin_features import ToolbarMixinFeatures

logger = logging.getLogger(__name__)


class ToolbarMixin:
    """Mixin providing toolbar functionality for EmbeddedTradingViewChart."""

    def __init__(self, *args, **kwargs):
        """Initialize mixin (called by parent class).

        Note: This is a mixin, so __init__ is typically called as part of
        multiple inheritance. Helper classes are initialized lazily in
        _ensure_toolbar_helpers() to avoid initialization order issues.
        """
        super().__init__(*args, **kwargs)
        # Lazy initialization for helper builders
        self._toolbar_row1_helper: ToolbarMixinRow1 | None = None
        self._toolbar_row2_helper: ToolbarMixinRow2 | None = None
        self._toolbar_features_helper: ToolbarMixinFeatures | None = None

    def _ensure_toolbar_helpers(self) -> None:
        """Lazy initialization of toolbar helper builders (composition pattern)."""
        if self._toolbar_row1_helper is None:
            self._toolbar_row1_helper = ToolbarMixinRow1(parent=self)
            self._toolbar_row2_helper = ToolbarMixinRow2(parent=self)
            self._toolbar_features_helper = ToolbarMixinFeatures(parent=self)

    def _create_toolbar(self) -> tuple[QToolBar, QToolBar]:
        """Create chart toolbar (two rows).

        Returns:
            Tuple of (toolbar1, toolbar2) for two-row layout
        """
        self._ensure_toolbar_helpers()

        toolbar1 = QToolBar()
        self._build_toolbar_row1(toolbar1)

        toolbar2 = QToolBar()
        self._build_toolbar_row2(toolbar2)

        return (toolbar1, toolbar2)

    def _build_toolbar_row1(self, toolbar: QToolBar) -> None:
        """Build toolbar row 1 (delegated to row1 helper)."""
        self._toolbar_row1_helper.build_toolbar_row1(toolbar)

    def _build_toolbar_row2(self, toolbar: QToolBar) -> None:
        """Build toolbar row 2 (delegated to row2 + features helpers)."""
        # Row 2 main components (live stream, regime, chart marking, AI, bot, market status)
        self._toolbar_row2_helper.build_toolbar_row2(toolbar)
        
        # Add Phase 5.5 features (levels + export context) between AI buttons and bot toggle
        # (inserted via special hook in row2 builder - not called from here)

    # =========================================================================
    # DELEGATION METHODS FOR FEATURES (backward compatibility)
    # =========================================================================

    def _add_levels_button(self, toolbar: QToolBar) -> None:
        """Add levels button (delegated to features helper)."""
        self._toolbar_features_helper.add_levels_button(toolbar)

    def _add_export_context_button(self, toolbar: QToolBar) -> None:
        """Add export context button (delegated to features helper)."""
        self._toolbar_features_helper.add_export_context_button(toolbar)

    # Regime badge delegation
    def update_regime_badge(self, regime: str, adx: float | None = None,
                            gate_reason: str = "", allows_entry: bool = True) -> None:
        """Update regime badge (delegated to row2 helper)."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.update_regime_badge(regime, adx, gate_reason, allows_entry)

    def update_regime_from_result(self, result) -> None:
        """Update regime from result (delegated to row2 helper)."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.update_regime_from_result(result)

    # =========================================================================
    # EVENT HANDLER DELEGATIONS (UI connections to helper methods)
    # =========================================================================

    def _on_load_chart(self) -> None:
        """Handle load chart button click. Delegates to row1 helper."""
        if self._toolbar_row1_helper:
            self._toolbar_row1_helper.on_load_chart()

    def _on_refresh(self) -> None:
        """Handle refresh button click. Delegates to row1 helper."""
        if self._toolbar_row1_helper:
            self._toolbar_row1_helper.on_refresh()

    def _toggle_live_stream(self) -> None:
        """Toggle live streaming. Delegates to row2 helper."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.toggle_live_stream()

    def _clear_all_markers(self) -> None:
        """Clear all chart markers. Delegates to row2 helper."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.clear_all_markers()

    def _clear_zones_with_js(self) -> None:
        """Clear zones via JavaScript. Delegates to row2 helper."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.clear_zones_with_js()

    def _clear_lines_with_js(self) -> None:
        """Clear lines via JavaScript. Delegates to row2 helper."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.clear_lines_with_js()

    def _clear_all_drawings(self) -> None:
        """Clear all drawings. Delegates to row2 helper."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.clear_all_drawings()

    def _clear_all_markings(self) -> None:
        """Clear all markings. Delegates to row2 helper."""
        if self._toolbar_row2_helper:
            self._toolbar_row2_helper.clear_all_markings()
