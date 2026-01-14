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

class BacktestCallbacksTemplateMixin:
    """Template management callbacks"""

    def _on_save_template_clicked(self) -> None:
        """
        Speichert die aktuelle Basistabelle als JSON-Template.

        Das Template enthält:
        - Alle Parameter-Spezifikationen
        - Aktuelle Werte aus Engine Settings
        - Metadaten (Timestamp, Name, Beschreibung)
        """
        self._log("💾 Speichere Template...")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()

            if not specs:
                QMessageBox.warning(
                    self, "Keine Daten",
                    "Bitte zuerst Engine Configs laden (Button 'Lade Engine Configs')."
                )
                return

            # Template-Struktur erstellen
            template = {
                'meta': {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'type': 'backtest_config_template',
                    'description': '',
                    'name': '',
                },
                'parameters': {},
                'full_specs': specs,  # Komplette Spezifikation für Wiederherstellung
            }

            # Extrahiere Parameter-Werte
            for spec in specs:
                param_key = spec['parameter']
                template['parameters'][param_key] = {
                    'value': spec['current_value'],
                    'type': spec['type'],
                    'category': spec['category'],
                    'subcategory': spec['subcategory'],
                    'description': spec.get('description', ''),
                    'min': spec['min'],
                    'max': spec['max'],
                    'variations': spec.get('variations', []),
                }

            # Dialog für Template-Name und Beschreibung
            dialog = QDialog(self)
            dialog.setWindowTitle("💾 Template speichern")
            dialog.setMinimumWidth(400)

            dlg_layout = QVBoxLayout(dialog)

            # Name Input
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Name:"))
            name_input = QLineEdit()
            name_input.setPlaceholderText("z.B. 'Aggressive Trend Strategy'")
            name_layout.addWidget(name_input)
            dlg_layout.addLayout(name_layout)

            # Description Input
            desc_layout = QVBoxLayout()
            desc_layout.addWidget(QLabel("Beschreibung:"))
            desc_input = QTextEdit()
            desc_input.setMaximumHeight(80)
            desc_input.setPlaceholderText("Optionale Beschreibung des Templates...")
            desc_layout.addWidget(desc_input)
            dlg_layout.addLayout(desc_layout)

            # Info
            info_label = QLabel(f"📊 {len(specs)} Parameter werden gespeichert.")
            info_label.setStyleSheet("color: #888; font-size: 11px;")
            dlg_layout.addWidget(info_label)

            # Buttons
            btn_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
            )
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            dlg_layout.addWidget(btn_box)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Template-Metadaten aktualisieren
            template['meta']['name'] = name_input.text() or f"Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            template['meta']['description'] = desc_input.toPlainText()

            # Speichern mit FileDialog
            default_filename = f"backtest_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Template speichern",
                str(Path("config/backtest_templates") / default_filename),
                "JSON Files (*.json);;All Files (*)"
            )

            if not filename:
                return

            # Verzeichnis erstellen falls nötig
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            # Speichern
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)

            self._log(f"✅ Template gespeichert: {filename}")
            QMessageBox.information(
                self, "Template gespeichert",
                f"Template '{template['meta']['name']}' wurde gespeichert.\n\nDatei: {filename}"
            )

        except Exception as e:
            logger.exception("Failed to save template")
            self._log(f"❌ Template-Speicherung fehlgeschlagen: {e}")

    def _on_load_template_clicked(self) -> None:
        """
        Lädt ein gespeichertes JSON-Template.

        Stellt alle Parameter-Werte aus dem Template wieder her und
        aktualisiert die Basistabelle.
        """
        self._log("📂 Lade Template...")

        try:
            # FileDialog zum Öffnen
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Template laden",
                str(Path("config/backtest_templates")),
                "JSON Files (*.json);;All Files (*)"
            )

            if not filename:
                return

            # Template laden
            with open(filename, 'r', encoding='utf-8') as f:
                template = json.load(f)

            # Validiere Template-Struktur - Unterstütze V1 (parameters) UND V2 (entry_score, etc.) Format
            is_v1_format = 'parameters' in template
            is_v2_format = 'version' in template and ('entry_score' in template or 'strategy_profile' in template)

            if not is_v1_format and not is_v2_format:
                QMessageBox.warning(
                    self, "Ungültiges Template",
                    "Die ausgewählte Datei ist kein gültiges Backtest-Template.\n\n"
                    "Erwartet: V1-Format mit 'parameters' oder V2-Format mit 'entry_score'/'strategy_profile'."
                )
                return

            meta = template.get('meta', {})

            # V2-Format: Konvertiere zu V1-kompatiblem Format für die UI
            if is_v2_format:
                params = self._convert_v2_to_parameters(template)
                full_specs = []  # V2 hat keine full_specs
                self._log(f"📦 V2-Format erkannt (version: {template.get('version', 'unknown')})")
            else:
                params = template.get('parameters', {})
                full_specs = template.get('full_specs', [])

            # Falls full_specs vorhanden, diese für Tabelle verwenden
            if full_specs:
                specs = full_specs
            else:
                # Rekonstruiere specs aus parameters
                specs = []
                for param_key, param_data in params.items():
                    specs.append({
                        'parameter': param_key,
                        'display_name': param_key.replace('_', ' ').title(),
                        'current_value': param_data.get('value'),
                        'type': param_data.get('type', 'float'),
                        'category': param_data.get('category', 'Unknown'),
                        'subcategory': param_data.get('subcategory', ''),
                        'ui_tab': param_data.get('category', 'Unknown'),
                        'description': param_data.get('description', ''),
                        'min': param_data.get('min'),
                        'max': param_data.get('max'),
                        'variations': param_data.get('variations', []),
                    })

            # Tabelle aktualisieren
            self.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Kategorie
                self.config_inspector_table.setItem(
                    row, 0, QTableWidgetItem(f"{spec['category']}/{spec.get('subcategory', '')}")
                )

                # Parameter
                self.config_inspector_table.setItem(
                    row, 1, QTableWidgetItem(spec.get('display_name', spec.get('parameter', '')))
                )

                # Wert
                value = spec.get('current_value')
                if spec.get('type') == 'float' and value is not None:
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                value_item = QTableWidgetItem(value_str)
                value_item.setForeground(QColor("#FF9800"))  # Orange für Template-Werte
                self.config_inspector_table.setItem(row, 2, value_item)

                # UI-Tab
                self.config_inspector_table.setItem(
                    row, 3, QTableWidgetItem(spec.get('ui_tab', ''))
                )

                # Beschreibung
                description = spec.get('description', '')
                desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
                desc_item.setToolTip(description)
                self.config_inspector_table.setItem(row, 4, desc_item)

                # Typ
                self.config_inspector_table.setItem(
                    row, 5, QTableWidgetItem(spec.get('type', ''))
                )

                # Min/Max
                min_val = spec.get('min')
                max_val = spec.get('max')
                if min_val is not None and max_val is not None:
                    minmax_str = f"{min_val}-{max_val}"
                else:
                    minmax_str = "—"
                self.config_inspector_table.setItem(row, 6, QTableWidgetItem(minmax_str))

                # Variationen
                variations = spec.get('variations', [])
                if variations:
                    var_str = ", ".join([str(v)[:6] for v in variations[:4]])
                    if len(variations) > 4:
                        var_str += "..."
                else:
                    var_str = "—"
                self.config_inspector_table.setItem(row, 7, QTableWidgetItem(var_str))

            # Parameter Space aus Template-Parametern erstellen
            param_space = {}
            for param_key, param_data in params.items():
                value = param_data.get('value')
                variations = param_data.get('variations', [])
                if variations:
                    param_space[param_key] = variations
                elif value is not None:
                    param_space[param_key] = [value]

            self.param_space_text.setText(json.dumps(param_space, indent=2))

            template_name = meta.get('name', 'Unbekannt')
            template_desc = meta.get('description', '')
            created_at = meta.get('created_at', '')

            self._log(f"✅ Template '{template_name}' geladen")
            self._log(f"   📅 Erstellt: {created_at[:10] if created_at else 'Unbekannt'}")
            self._log(f"   📊 {len(params)} Parameter")

            if template_desc:
                self._log(f"   📝 {template_desc[:50]}...")

        except Exception as e:
            logger.exception("Failed to load template")
            self._log(f"❌ Template-Laden fehlgeschlagen: {e}")

    def _on_derive_variant_clicked(self) -> None:
        """
        Erstellt eine Variante basierend auf der aktuellen Basistabelle.

        Öffnet einen Dialog zum Anpassen einzelner Parameter-Werte,
        wobei die Basis-Werte als Ausgangspunkt dienen.
        """
        self._log("📝 Variante ableiten...")

        # Prüfe ob Daten in Tabelle vorhanden
        if self.config_inspector_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Keine Basisdaten",
                "Bitte zuerst Engine Configs laden oder ein Template öffnen."
            )
            return

        try:
            # Dialog für Varianten-Erstellung
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Variante aus Basis ableiten")
            dialog.setMinimumSize(600, 500)

            dlg_layout = QVBoxLayout(dialog)

            # Info
            info = QLabel(
                "Wähle Parameter aus der Basistabelle und passe deren Werte an.\n"
                "Nicht geänderte Werte werden von der Basis übernommen."
            )
            info.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
            dlg_layout.addWidget(info)

            # Varianten-Name
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Varianten-Name:"))
            variant_name_input = QLineEdit()
            variant_name_input.setPlaceholderText("z.B. 'Aggressive V1'")
            name_layout.addWidget(variant_name_input)
            dlg_layout.addLayout(name_layout)

            # Parameter-Editor Tabelle (editierbar!)
            param_table = QTableWidget()
            param_table.setColumnCount(4)
            param_table.setHorizontalHeaderLabels(["Parameter", "Basis-Wert", "Neuer Wert", "Ändern?"])
            param_table.horizontalHeader().setStretchLastSection(True)

            # Extrahiere Parameter aus Basistabelle
            base_params = []
            for row in range(self.config_inspector_table.rowCount()):
                param_item = self.config_inspector_table.item(row, 1)
                value_item = self.config_inspector_table.item(row, 2)
                type_item = self.config_inspector_table.item(row, 5)

                if param_item and value_item:
                    base_params.append({
                        'name': param_item.text(),
                        'value': value_item.text(),
                        'type': type_item.text() if type_item else 'float',
                    })

            param_table.setRowCount(len(base_params))

            for row, param in enumerate(base_params):
                # Parameter-Name (read-only)
                name_item = QTableWidgetItem(param['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                param_table.setItem(row, 0, name_item)

                # Basis-Wert (read-only)
                base_item = QTableWidgetItem(param['value'])
                base_item.setFlags(base_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                base_item.setForeground(QColor("#888"))
                param_table.setItem(row, 1, base_item)

                # Neuer Wert (editierbar)
                new_item = QTableWidgetItem(param['value'])
                new_item.setForeground(QColor("#4CAF50"))
                param_table.setItem(row, 2, new_item)

                # Checkbox "Ändern?"
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox = QCheckBox()
                checkbox_layout.addWidget(checkbox)
                param_table.setCellWidget(row, 3, checkbox_widget)

            dlg_layout.addWidget(param_table)

            # Quick-Actions
            quick_layout = QHBoxLayout()

            # "Alle auswählen" Button
            select_all_btn = QPushButton("Alle auswählen")
            select_all_btn.clicked.connect(
                lambda: self._select_all_variant_checkboxes(param_table, True)
            )
            quick_layout.addWidget(select_all_btn)

            # "Keine auswählen" Button
            select_none_btn = QPushButton("Keine auswählen")
            select_none_btn.clicked.connect(
                lambda: self._select_all_variant_checkboxes(param_table, False)
            )
            quick_layout.addWidget(select_none_btn)

            quick_layout.addStretch()
            dlg_layout.addLayout(quick_layout)

            # Buttons
            btn_box = QDialogButtonBox()

            create_btn = QPushButton("✅ Variante erstellen")
            create_btn.clicked.connect(dialog.accept)
            btn_box.addButton(create_btn, QDialogButtonBox.ButtonRole.AcceptRole)

            cancel_btn = QPushButton("Abbrechen")
            cancel_btn.clicked.connect(dialog.reject)
            btn_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

            dlg_layout.addWidget(btn_box)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Variante aus Dialog-Daten erstellen
            variant_name = variant_name_input.text() or f"Variante_{datetime.now().strftime('%H%M%S')}"
            variant_params = {}

            for row in range(param_table.rowCount()):
                checkbox_widget = param_table.cellWidget(row, 3)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        param_name = param_table.item(row, 0).text()
                        new_value = param_table.item(row, 2).text()

                        # Versuche Wert zu konvertieren
                        try:
                            if '.' in new_value:
                                variant_params[param_name] = float(new_value)
                            elif new_value.isdigit():
                                variant_params[param_name] = int(new_value)
                            elif new_value.lower() in ('true', 'false'):
                                variant_params[param_name] = new_value.lower() == 'true'
                            else:
                                variant_params[param_name] = new_value
                        except ValueError:
                            variant_params[param_name] = new_value

            if not variant_params:
                QMessageBox.warning(
                    self, "Keine Änderungen",
                    "Bitte wähle mindestens einen Parameter zum Ändern aus."
                )
                return

            # Variante zu Parameter-Space hinzufügen
            try:
                current_space_text = self.param_space_text.toPlainText()
                if current_space_text.strip():
                    current_space = json.loads(current_space_text)
                else:
                    current_space = {}
            except json.JSONDecodeError:
                current_space = {}

            # Merge Varianten-Parameter in Space
            for param_name, param_value in variant_params.items():
                if param_name not in current_space:
                    current_space[param_name] = []
                if param_value not in current_space[param_name]:
                    current_space[param_name].append(param_value)

            self.param_space_text.setText(json.dumps(current_space, indent=2))

            self._log(f"✅ Variante '{variant_name}' erstellt mit {len(variant_params)} geänderten Parametern")
            for param, value in list(variant_params.items())[:5]:
                self._log(f"   {param}: {value}")
            if len(variant_params) > 5:
                self._log(f"   ... und {len(variant_params) - 5} weitere")

        except Exception as e:
            logger.exception("Failed to derive variant")
            self._log(f"❌ Varianten-Erstellung fehlgeschlagen: {e}")

