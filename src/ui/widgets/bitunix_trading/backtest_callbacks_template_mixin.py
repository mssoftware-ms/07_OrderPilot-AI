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
            # Load template file
            filename = self._get_template_filename()
            if not filename:
                return

            template = self._load_template_file(filename)
            if template is None:
                return

            # Parse template data
            meta, params, specs = self._parse_template_data(template)
            if specs is None:
                return

            # Update UI with template data
            self._populate_inspector_table(specs)
            self._update_parameter_space(params)
            self._log_template_metadata(meta, params)

        except Exception as e:
            logger.exception("Failed to load template")
            self._log(f"❌ Template-Laden fehlgeschlagen: {e}")

    def _get_template_filename(self) -> str | None:
        """Show file dialog and return selected template filename.

        Returns:
            Filename or None if cancelled.
        """
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Template laden",
            str(Path("config/backtest_templates")),
            "JSON Files (*.json);;All Files (*)"
        )
        return filename if filename else None

    def _load_template_file(self, filename: str) -> dict | None:
        """Load and validate template file.

        Args:
            filename: Path to template file.

        Returns:
            Template dictionary or None if invalid.
        """
        with open(filename, 'r', encoding='utf-8') as f:
            template = json.load(f)

        # Validate template format
        is_v1_format = 'parameters' in template
        is_v2_format = 'version' in template and ('entry_score' in template or 'strategy_profile' in template)

        if not is_v1_format and not is_v2_format:
            QMessageBox.warning(
                self, "Ungültiges Template",
                "Die ausgewählte Datei ist kein gültiges Backtest-Template.\n\n"
                "Erwartet: V1-Format mit 'parameters' oder V2-Format mit 'entry_score'/'strategy_profile'."
            )
            return None

        return template

    def _parse_template_data(self, template: dict) -> tuple[dict, dict, list | None]:
        """Parse template data into meta, params, and specs.

        Args:
            template: Template dictionary.

        Returns:
            Tuple of (meta, params, specs) or (meta, params, None) if error.
        """
        meta = template.get('meta', {})

        # Check format and convert if needed
        is_v2_format = 'version' in template and ('entry_score' in template or 'strategy_profile' in template)

        if is_v2_format:
            params = self._convert_v2_to_parameters(template)
            full_specs = []  # V2 has no full_specs
            self._log(f"📦 V2-Format erkannt (version: {template.get('version', 'unknown')})")
        else:
            params = template.get('parameters', {})
            full_specs = template.get('full_specs', [])

        # Get specs (from full_specs or reconstruct from params)
        if full_specs:
            specs = full_specs
        else:
            specs = self._reconstruct_specs_from_params(params)

        return meta, params, specs

    def _reconstruct_specs_from_params(self, params: dict) -> list[dict]:
        """Reconstruct specs list from parameters dictionary.

        Args:
            params: Parameters dictionary.

        Returns:
            List of spec dictionaries.
        """
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
        return specs

    def _populate_inspector_table(self, specs: list[dict]) -> None:
        """Populate config inspector table with specs.

        Args:
            specs: List of parameter specifications.
        """
        self.config_inspector_table.setRowCount(len(specs))

        for row, spec in enumerate(specs):
            self._set_table_row(row, spec)

    def _set_table_row(self, row: int, spec: dict) -> None:
        """Set all columns for a single table row.

        Args:
            row: Row index.
            spec: Parameter specification dictionary.
        """
        # Kategorie
        self.config_inspector_table.setItem(
            row, 0, QTableWidgetItem(f"{spec['category']}/{spec.get('subcategory', '')}")
        )

        # Parameter
        self.config_inspector_table.setItem(
            row, 1, QTableWidgetItem(spec.get('display_name', spec.get('parameter', '')))
        )

        # Wert (orange highlighted for templates)
        value = spec.get('current_value')
        value_str = f"{value:.2f}" if spec.get('type') == 'float' and value is not None else str(value)
        value_item = QTableWidgetItem(value_str)
        value_item.setForeground(QColor("#FF9800"))
        self.config_inspector_table.setItem(row, 2, value_item)

        # UI-Tab
        self.config_inspector_table.setItem(
            row, 3, QTableWidgetItem(spec.get('ui_tab', ''))
        )

        # Beschreibung (with tooltip)
        description = spec.get('description', '')
        desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
        desc_item.setToolTip(description)
        self.config_inspector_table.setItem(row, 4, desc_item)

        # Typ
        self.config_inspector_table.setItem(
            row, 5, QTableWidgetItem(spec.get('type', ''))
        )

        # Min/Max
        minmax_str = self._format_minmax(spec.get('min'), spec.get('max'))
        self.config_inspector_table.setItem(row, 6, QTableWidgetItem(minmax_str))

        # Variationen
        var_str = self._format_variations(spec.get('variations', []))
        self.config_inspector_table.setItem(row, 7, QTableWidgetItem(var_str))

    def _format_minmax(self, min_val, max_val) -> str:
        """Format min/max values for display.

        Args:
            min_val: Minimum value.
            max_val: Maximum value.

        Returns:
            Formatted string.
        """
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}"
        return "—"

    def _format_variations(self, variations: list) -> str:
        """Format variations list for display.

        Args:
            variations: List of variation values.

        Returns:
            Formatted string.
        """
        if not variations:
            return "—"

        var_str = ", ".join([str(v)[:6] for v in variations[:4]])
        if len(variations) > 4:
            var_str += "..."
        return var_str

    def _update_parameter_space(self, params: dict) -> None:
        """Update parameter space text field with template parameters.

        Args:
            params: Parameters dictionary.
        """
        param_space = {}
        for param_key, param_data in params.items():
            value = param_data.get('value')
            variations = param_data.get('variations', [])
            if variations:
                param_space[param_key] = variations
            elif value is not None:
                param_space[param_key] = [value]

        self.param_space_text.setText(json.dumps(param_space, indent=2))

    def _log_template_metadata(self, meta: dict, params: dict) -> None:
        """Log template metadata after successful load.

        Args:
            meta: Template metadata dictionary.
            params: Parameters dictionary.
        """
        template_name = meta.get('name', 'Unbekannt')
        template_desc = meta.get('description', '')
        created_at = meta.get('created_at', '')

        self._log(f"✅ Template '{template_name}' geladen")
        self._log(f"   📅 Erstellt: {created_at[:10] if created_at else 'Unbekannt'}")
        self._log(f"   📊 {len(params)} Parameter")

        if template_desc:
            self._log(f"   📝 {template_desc[:50]}...")

    def _on_derive_variant_clicked(self) -> None:
        """
        Erstellt eine Variante basierend auf der aktuellen Basistabelle.

        Öffnet einen Dialog zum Anpassen einzelner Parameter-Werte,
        wobei die Basis-Werte als Ausgangspunkt dienen.
        """
        self._log("📝 Variante ableiten...")

        # Validate base data
        if not self._validate_base_data():
            return

        try:
            # Create and show dialog
            dialog, variant_name_input, param_table = self._create_derive_variant_dialog()

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Extract variant parameters from dialog
            variant_name, variant_params = self._extract_variant_parameters(
                variant_name_input, param_table
            )

            if not variant_params:
                QMessageBox.warning(
                    self, "Keine Änderungen",
                    "Bitte wähle mindestens einen Parameter zum Ändern aus."
                )
                return

            # Update parameter space with new variant
            self._update_parameter_space_with_variant(variant_params)

            # Log success
            self._log_variant_creation(variant_name, variant_params)

        except Exception as e:
            logger.exception("Failed to derive variant")
            self._log(f"❌ Varianten-Erstellung fehlgeschlagen: {e}")

    def _validate_base_data(self) -> bool:
        """Validate that base data is available in table."""
        if self.config_inspector_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Keine Basisdaten",
                "Bitte zuerst Engine Configs laden oder ein Template öffnen."
            )
            return False
        return True

    def _create_derive_variant_dialog(self) -> tuple:
        """Create dialog for variant derivation with parameter table.

        Returns:
            Tuple of (dialog, variant_name_input, param_table)
        """
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
        base_params = self._extract_base_parameters()

        param_table.setRowCount(len(base_params))

        # Populate table with parameters
        self._populate_variant_parameter_table(param_table, base_params)

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

        return dialog, variant_name_input, param_table

    def _extract_base_parameters(self) -> list[dict]:
        """Extract parameters from base configuration table.

        Returns:
            List of parameter dictionaries with name, value, and type.
        """
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
        return base_params

    def _populate_variant_parameter_table(
        self, param_table: QTableWidget, base_params: list[dict]
    ) -> None:
        """Populate variant parameter table with base parameters.

        Args:
            param_table: Table widget to populate.
            base_params: List of base parameter dictionaries.
        """
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

    def _select_all_variant_checkboxes(
        self, param_table: QTableWidget, select: bool
    ) -> None:
        """Select or deselect all checkboxes in variant parameter table.

        Args:
            param_table: Table widget containing checkboxes.
            select: True to select all, False to deselect all.
        """
        for row in range(param_table.rowCount()):
            checkbox_widget = param_table.cellWidget(row, 3)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(select)

    def _extract_variant_parameters(
        self, variant_name_input: QLineEdit, param_table: QTableWidget
    ) -> tuple[str, dict]:
        """Extract variant parameters from dialog.

        Args:
            variant_name_input: Input field for variant name.
            param_table: Table containing parameter changes.

        Returns:
            Tuple of (variant_name, variant_params dictionary)
        """
        from datetime import datetime

        # Get variant name
        variant_name = variant_name_input.text() or f"Variante_{datetime.now().strftime('%H%M%S')}"
        variant_params = {}

        # Extract checked parameters
        for row in range(param_table.rowCount()):
            checkbox_widget = param_table.cellWidget(row, 3)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    param_name = param_table.item(row, 0).text()
                    new_value = param_table.item(row, 2).text()

                    # Convert value to appropriate type
                    variant_params[param_name] = self._convert_parameter_value(new_value)

        return variant_name, variant_params

    def _convert_parameter_value(self, value_str: str) -> int | float | bool | str:
        """Convert parameter value string to appropriate type.

        Args:
            value_str: String value to convert.

        Returns:
            Converted value (int, float, bool, or str).
        """
        try:
            if '.' in value_str:
                return float(value_str)
            elif value_str.isdigit():
                return int(value_str)
            elif value_str.lower() in ('true', 'false'):
                return value_str.lower() == 'true'
            else:
                return value_str
        except ValueError:
            return value_str

    def _update_parameter_space_with_variant(self, variant_params: dict) -> None:
        """Update parameter space JSON with new variant parameters.

        Args:
            variant_params: Dictionary of parameter changes.
        """
        # Load current parameter space
        try:
            current_space_text = self.param_space_text.toPlainText()
            if current_space_text.strip():
                current_space = json.loads(current_space_text)
            else:
                current_space = {}
        except json.JSONDecodeError:
            current_space = {}

        # Merge variant parameters into space
        for param_name, param_value in variant_params.items():
            if param_name not in current_space:
                current_space[param_name] = []
            if param_value not in current_space[param_name]:
                current_space[param_name].append(param_value)

        # Update text field
        self.param_space_text.setText(json.dumps(current_space, indent=2))

    def _log_variant_creation(self, variant_name: str, variant_params: dict) -> None:
        """Log successful variant creation.

        Args:
            variant_name: Name of the created variant.
            variant_params: Dictionary of changed parameters.
        """
        self._log(
            f"✅ Variante '{variant_name}' erstellt mit "
            f"{len(variant_params)} geänderten Parametern"
        )

        # Log first 5 parameters
        for param, value in list(variant_params.items())[:5]:
            self._log(f"   {param}: {value}")

        # Indicate if there are more
        if len(variant_params) > 5:
            self._log(f"   ... und {len(variant_params) - 5} weitere")

