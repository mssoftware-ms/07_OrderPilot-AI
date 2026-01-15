from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTabWidget, QLineEdit,
    QHeaderView,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)

class BacktestCallbacksConfigMixin:
    """Configuration management callbacks"""

    def _on_auto_generate_clicked(self) -> None:
        """
        Generiert automatisch Test-Varianten.

        Erstellt sinnvolle Kombinationen aus:
        - Vordefinierten Indikator-Sets
        - Algorithmisch variierten Parametern
        """
        self._log("🤖 Generiere Test-Varianten...")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()

            # Generiere Varianten
            num_variants = self.batch_iterations.value()
            num_variants = min(num_variants, 20)  # Max 20 für Auto-Generate

            variants = self.generate_ai_test_variants(specs, num_variants)

            # Zeige Dialog mit generierten Varianten
            dialog = QDialog(self)
            dialog.setWindowTitle("🤖 Generierte Test-Varianten")
            dialog.setMinimumSize(700, 500)

            dlg_layout = QVBoxLayout(dialog)

            # Info Label
            info = QLabel(f"✅ {len(variants)} Test-Varianten generiert:")
            info.setStyleSheet("font-weight: bold; color: #4CAF50;")
            dlg_layout.addWidget(info)

            # Varianten-Tabelle
            var_table = QTableWidget()
            var_table.setColumnCount(4)
            var_table.setHorizontalHeaderLabels(["ID", "Name", "Quelle", "Parameter"])
            var_table.horizontalHeader().setStretchLastSection(True)
            var_table.setRowCount(len(variants))

            for row, variant in enumerate(variants):
                var_table.setItem(row, 0, QTableWidgetItem(variant['id']))
                var_table.setItem(row, 1, QTableWidgetItem(variant['name']))
                var_table.setItem(row, 2, QTableWidgetItem(variant['source']))

                params_str = ", ".join([f"{k}={v}" for k, v in list(variant['parameters'].items())[:3]])
                if len(variant['parameters']) > 3:
                    params_str += "..."
                var_table.setItem(row, 3, QTableWidgetItem(params_str))

            dlg_layout.addWidget(var_table)

            # Buttons
            btn_box = QDialogButtonBox()

            use_btn = QPushButton("✅ Als Parameter Space verwenden")
            use_btn.clicked.connect(lambda: self._apply_variants_to_param_space(variants, dialog))
            btn_box.addButton(use_btn, QDialogButtonBox.ButtonRole.AcceptRole)

            export_btn = QPushButton("📄 Als JSON exportieren")
            export_btn.clicked.connect(lambda: self._export_variants_json(variants))
            btn_box.addButton(export_btn, QDialogButtonBox.ButtonRole.ActionRole)

            cancel_btn = QPushButton("Abbrechen")
            cancel_btn.clicked.connect(dialog.reject)
            btn_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

            dlg_layout.addWidget(btn_box)

            dialog.exec()

        except Exception as e:
            logger.exception("Failed to generate variants")
            self._log(f"❌ Fehler: {e}")

    def _on_load_configs_clicked(self) -> None:
        """
        Lädt Engine-Configs und zeigt sie im Config Inspector an.

        Sammelt alle konfigurierbaren Parameter aus den Engine Settings Tabs
        und zeigt sie in der Tabelle an.
        """
        self._log("📥 Lade Engine Configs...")
        logger.info("Load Configs Button clicked - loading engine configurations")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()
            logger.info(f"Loaded {len(specs)} parameter specifications")

            # Tabelle aktualisieren
            self.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Kategorie
                self.config_inspector_table.setItem(
                    row, 0, QTableWidgetItem(f"{spec['category']}/{spec['subcategory']}")
                )

                # Parameter
                self.config_inspector_table.setItem(
                    row, 1, QTableWidgetItem(spec['display_name'])
                )

                # Wert
                value_str = str(spec['current_value'])
                if spec['type'] == 'float':
                    value_str = f"{spec['current_value']:.2f}"
                value_item = QTableWidgetItem(value_str)
                value_item.setForeground(QColor("#4CAF50"))
                self.config_inspector_table.setItem(row, 2, value_item)

                # UI-Tab
                self.config_inspector_table.setItem(
                    row, 3, QTableWidgetItem(spec['ui_tab'])
                )

                # Beschreibung (neue Spalte)
                description = spec.get('description', '')
                desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
                desc_item.setToolTip(description)  # Volle Beschreibung als Tooltip
                self.config_inspector_table.setItem(row, 4, desc_item)

                # Typ
                self.config_inspector_table.setItem(
                    row, 5, QTableWidgetItem(spec['type'])
                )

                # Min/Max
                if spec['min'] is not None and spec['max'] is not None:
                    minmax_str = f"{spec['min']}-{spec['max']}"
                else:
                    minmax_str = "—"
                self.config_inspector_table.setItem(
                    row, 6, QTableWidgetItem(minmax_str)
                )

                # Variationen
                variations = spec.get('variations', [])
                if variations:
                    var_str = ", ".join([str(v)[:6] for v in variations[:4]])
                    if len(variations) > 4:
                        var_str += "..."
                else:
                    var_str = "—"
                self.config_inspector_table.setItem(
                    row, 7, QTableWidgetItem(var_str)
                )

            # Erstelle Parameter-Space aus Configs
            param_space = self.get_parameter_space_from_configs()

            if param_space:
                self.param_space_text.setText(json.dumps(param_space, indent=2))
                self._log(f"✅ {len(specs)} Parameter geladen, {len(param_space)} für Batch-Test")
            else:
                self._log("⚠️ Keine Parameter für Batch-Test verfügbar")

            # Wechsle automatisch zum Batch/WF Tab um die Config-Tabelle zu zeigen
            # Tab 3 ist "🔄 Batch/WF"
            self.sub_tabs.setCurrentIndex(3)
            logger.info("Switched to Batch/WF tab to show Config Inspector")

        except Exception as e:
            logger.exception("Failed to load configs")
            self._log(f"❌ Fehler: {e}")

    def _on_indicator_set_changed(self, index: int) -> None:
        """
        Handler für Indikator-Set Auswahl.

        Lädt ein vordefiniertes Indikator-Set und zeigt dessen Parameter an.
        """
        if index == 0:  # "-- Manuell --"
            return

        indicator_sets = self.get_available_indicator_sets()

        # Index anpassen (0 = Manuell, 1+ = Sets)
        set_index = index - 1

        if 0 <= set_index < len(indicator_sets):
            ind_set = indicator_sets[set_index]

            # Erstelle Parameter-Space aus Set
            param_space = {}

            # Weights
            for weight_name, weight_val in ind_set.get('weights', {}).items():
                param_space[f'weight_{weight_name}'] = [weight_val]

            # Andere Settings
            if 'min_score_for_entry' in ind_set:
                param_space['min_score_for_entry'] = [ind_set['min_score_for_entry']]
            if 'gates' in ind_set:
                for gate_name, gate_val in ind_set['gates'].items():
                    param_space[f'gate_{gate_name}'] = [gate_val]
            if 'leverage' in ind_set:
                for lev_name, lev_val in ind_set['leverage'].items():
                    param_space[lev_name] = [lev_val]
            if 'level_settings' in ind_set:
                for lvl_name, lvl_val in ind_set['level_settings'].items():
                    param_space[lvl_name] = [lvl_val]

            self.param_space_text.setText(json.dumps(param_space, indent=2))
            self._log(f"📊 Indikator-Set '{ind_set['name']}' geladen: {ind_set['description']}")

    # =========================================================================
    # TEMPLATE MANAGEMENT HANDLERS

