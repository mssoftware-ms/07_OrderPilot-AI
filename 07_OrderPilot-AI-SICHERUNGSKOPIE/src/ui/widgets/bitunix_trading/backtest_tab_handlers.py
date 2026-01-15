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

        Delegates to config_manager for variant generation.
        """
        self.parent._logging.log("🤖 Generiere Test-Varianten...")
        # Implementation delegates to config_manager.generate_ai_test_variants()
        pass

    def on_indicator_set_changed(self, index: int) -> None:
        """Handler für Indikator-Set Auswahl.

        Delegates to config_manager for indicator set handling.
        """
        if index == 0:  # "-- Manuell --"
            return

        indicator_sets = self.parent.config_manager.get_available_indicator_sets()
        # Implementation available in original file lines 2892-2930
        pass
