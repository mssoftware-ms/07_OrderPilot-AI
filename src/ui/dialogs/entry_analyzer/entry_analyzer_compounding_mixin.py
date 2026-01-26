"""Entry Analyzer - Compounding/P&L Calculator Tab (Mixin)."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.ui.widgets.compounding_component.ui import CompoundingPanel


class CompoundingMixin:
    """Mixin for Compounding/P&L calculator tab in Entry Analyzer."""

    _compounding_panel: CompoundingPanel

    def _setup_compounding_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)

        self._compounding_panel = CompoundingPanel(tab)
        layout.addWidget(self._compounding_panel, stretch=1)
