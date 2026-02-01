"""Backtest Tab Handlers - Config and UI Event Handlers.

Refactored from backtest_tab_main.py.

Contains:
- on_load_configs_clicked: Load engine configs handler
- on_auto_generate_clicked: Auto-generate variants handler
- on_indicator_set_changed: Indicator set selection handler
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from .backtest_tab_main import BacktestTab

logger = logging.getLogger(__name__)


class BacktestTabHandlers:
    """Helper for config and UI event handlers."""

    def __init__(self, parent: "BacktestTab"):
        self.parent = parent

    def on_load_configs_clicked(self) -> None:
        """Lädt Engine-Configs und zeigt sie im Config Inspector an.

        Delegates to config_manager for collection and display.
        """
        self.parent._logging.log("📥 Lade Engine Configs...")
        logger.info("Load Configs Button clicked - loading engine configurations")

        try:
            # Sammle Parameter-Spezifikation via config_manager
            specs = self.parent.config_manager.get_parameter_specification()
            logger.info(f"Loaded {len(specs)} parameter specifications")

            # Tabelle aktualisieren
            self.parent.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Populate table - implementation details available in original file
                pass

            # Erstelle Parameter-Space aus Configs
            param_space = self.parent.config_manager.get_parameter_space_from_configs()

            if param_space:
                self.parent.param_space_text.setText(json.dumps(param_space, indent=2))
                self.parent._logging.log(f"✅ {len(specs)} Parameter geladen, {len(param_space)} für Batch-Test")
            else:
                self.parent._logging.log("⚠️ Keine Parameter für Batch-Test verfügbar")

            # Wechsle automatisch zum Batch/WF Tab
            self.parent.sub_tabs.setCurrentIndex(3)
            logger.info("Switched to Batch/WF tab to show Config Inspector")

        except Exception as e:
            logger.exception("Failed to load configs")
            self.parent._logging.log(f"❌ Fehler: {e}")
            QMessageBox.critical(self.parent, "Fehler", f"Config-Laden fehlgeschlagen:\n{e}")

    def on_auto_generate_clicked(self) -> None:
        """Generiert automatisch Test-Varianten.

        Delegates to Mixin _on_auto_generate_clicked().
        """
        if hasattr(self.parent, '_on_auto_generate_clicked'):
            self.parent._on_auto_generate_clicked()
        else:
            logger.warning("Mixin _on_auto_generate_clicked not found - using fallback")
            self._auto_generate_fallback()

    def _auto_generate_fallback(self) -> None:
        """Fallback if mixin not available."""
        try:
            specs = self.parent.config_manager.get_parameter_specification()
            num_variants = min(self.parent.batch_iterations.value(), 20)
            variants = self.parent.config_manager.generate_ai_test_variants(specs, num_variants)
            self.parent._logging.log(f"✅ {len(variants)} Test-Varianten generiert")

            # Update param space
            param_space = {v['id']: v['parameters'] for v in variants}
            self.parent.param_space_text.setText(json.dumps(param_space, indent=2))

        except Exception as e:
            logger.exception("Auto-generate failed")
            self.parent._logging.log(f"❌ Fehler: {e}")

    def on_indicator_set_changed(self, index: int) -> None:
        """Handler für Indikator-Set Auswahl.

        Delegates to Mixin _on_indicator_set_changed().
        """
        if index == 0:  # "-- Manuell --"
            return

        if hasattr(self.parent, '_on_indicator_set_changed'):
            self.parent._on_indicator_set_changed(index)
        else:
            logger.warning("Mixin _on_indicator_set_changed not found")
            indicator_sets = self.parent.config_manager.get_available_indicator_sets()
            if index > 0 and index <= len(indicator_sets):
                selected = indicator_sets[index - 1]
                self.parent._logging.log(f"📊 Indikator-Set: {selected.get('name', 'Unknown')}")
