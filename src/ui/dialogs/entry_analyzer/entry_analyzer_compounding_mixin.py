"""Entry Analyzer - Compounding/P&L Calculator Tab (Mixin)."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.ui.widgets.compounding_component.ui import CompoundingPanel


class CompoundingMixin:
    """Mixin for Compounding/P&L calculator tab in Entry Analyzer."""

    _compounding_panel: CompoundingPanel

    def _setup_compounding_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        header = QLabel("Compounding & P&L Calculator")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)

        description = QLabel(
            "Berechnet Zinseszins mit Gebuehren, Hebel, Steuern und Reinvestition. "
            "Alle Werte werden live aktualisiert und lassen sich als CSV exportieren."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(description)

        self._compounding_panel = CompoundingPanel(tab)
        layout.addWidget(self._compounding_panel, stretch=1)
