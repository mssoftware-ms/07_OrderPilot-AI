"""
Backtest Template Manager - Template Save/Load/Derive Operations

Handles template management for backtest configurations:
- Save current config as JSON template
- Load template from file
- Derive variants from base config
- Export/import functionality

Module 4/5 of backtest_tab.py split (Lines 2936-3402)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget as QWidgetType

logger = logging.getLogger(__name__)


class BacktestTemplateManager:
    """Verwaltet Template-Operationen für Backtest-Konfigurationen.

    Verantwortlich für:
    - Speichern der aktuellen Config als JSON-Template
    - Laden von gespeicherten Templates
    - Ableiten von Varianten aus Basis-Config
    - Export/Import von Konfigurationen
    """

    def __init__(self, parent_widget: "QWidgetType"):
        """Initialisiert BacktestTemplateManager.

        Args:
            parent_widget: Das BacktestTab Widget
        """
        self.parent = parent_widget

    def on_save_template_clicked(self) -> None:
        """Speichert die aktuelle Basistabelle als JSON-Template.

        Template-Struktur:
        - meta: Metadaten (created_at, version, type, name, description)
        - parameters: Dict mit allen Parameter-Werten
        - full_specs: Vollständige Parameter-Spezifikation

        Workflow:
        1. Sammle Parameter-Spezifikation via config_manager
        2. Dialog für Template-Name und Beschreibung
        3. Speichere als JSON mit FileDialog
        """
        self.parent._log("💾 Speichere Template...")

        try:
            # Sammle Parameter-Spezifikation vom ConfigManager
            if not hasattr(self.parent, 'config_manager'):
                QMessageBox.warning(
                    self.parent, "Kein Config Manager",
                    "Config Manager nicht initialisiert."
                )
                return

            specs = self.parent.config_manager.get_parameter_specification()

            if not specs:
                QMessageBox.warning(
                    self.parent, "Keine Daten",
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
            dialog = QDialog(self.parent)
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
                self.parent,
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

            self.parent._log(f"✅ Template gespeichert: {filename}")
            QMessageBox.information(
                self.parent, "Template gespeichert",
                f"Template '{template['meta']['name']}' wurde gespeichert.\n\nDatei: {filename}"
            )

        except Exception as e:
            logger.exception("Failed to save template")
            self.parent._log(f"❌ Template-Speicherung fehlgeschlagen: {e}")
            QMessageBox.critical(self.parent, "Fehler", f"Template-Speicherung fehlgeschlagen:\n{e}")

    def on_load_template_clicked(self) -> None:
        """Lädt ein gespeichertes JSON-Template.

        Workflow:
        1. FileDialog zum Auswählen der Template-Datei
        2. Validiere Template-Struktur (meta, parameters, full_specs)
        3. Aktualisiere config_inspector_table mit Template-Werten
        4. Aktualisiere param_space_text mit Template-Parametern
        5. Zeige Template-Info (Name, Beschreibung, Erstelldatum)
        """
        self.parent._log("📂 Lade Template...")

        try:
            # Default path für JSON Strategien (Issue #13)
            default_path = Path("D:/03_Git/02_Python/07_OrderPilot-AI/03_JSON/Trading_Bot")
            # Fallback auf config/backtest_templates wenn Pfad nicht existiert
            if not default_path.exists():
                default_path = Path("config/backtest_templates")

            # FileDialog zum Öffnen
            filename, _ = QFileDialog.getOpenFileName(
                self.parent,
                "Template laden",
                str(default_path),
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
                    self.parent, "Ungültiges Template",
                    "Die ausgewählte Datei ist kein gültiges Backtest-Template.\n\n"
                    "Erwartet: V1-Format mit 'parameters' oder V2-Format mit 'entry_score'/'strategy_profile'."
                )
                return

            meta = template.get('meta', {})

            # V2-Format: Konvertiere zu V1-kompatiblem Format für die UI
            if is_v2_format:
                params = self._convert_v2_to_parameters(template)
                full_specs = []  # V2 hat keine full_specs
                self.parent._log(f"📦 V2-Format erkannt (version: {template.get('version', 'unknown')})")
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
            self.parent.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Kategorie
                self.parent.config_inspector_table.setItem(
                    row, 0, QTableWidgetItem(f"{spec['category']}/{spec.get('subcategory', '')}")
                )

                # Parameter
                self.parent.config_inspector_table.setItem(
                    row, 1, QTableWidgetItem(spec.get('display_name', spec.get('parameter', '')))
                )

                # Wert (Orange für Template-Werte)
                value = spec.get('current_value')
                if spec.get('type') == 'float' and value is not None:
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                value_item = QTableWidgetItem(value_str)
                value_item.setForeground(QColor("#FF9800"))  # Orange für Template-Werte
                self.parent.config_inspector_table.setItem(row, 2, value_item)

                # UI-Tab
                self.parent.config_inspector_table.setItem(
                    row, 3, QTableWidgetItem(spec.get('ui_tab', ''))
                )

                # Beschreibung
                description = spec.get('description', '')
                desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
                desc_item.setToolTip(description)
                self.parent.config_inspector_table.setItem(row, 4, desc_item)

                # Typ
                self.parent.config_inspector_table.setItem(
                    row, 5, QTableWidgetItem(spec.get('type', ''))
                )

                # Min/Max
                min_val = spec.get('min')
                max_val = spec.get('max')
                if min_val is not None and max_val is not None:
                    minmax_str = f"{min_val}-{max_val}"
                else:
                    minmax_str = "—"
                self.parent.config_inspector_table.setItem(row, 6, QTableWidgetItem(minmax_str))

                # Variationen
                variations = spec.get('variations', [])
                if variations:
                    var_str = ", ".join([str(v)[:6] for v in variations[:4]])
                    if len(variations) > 4:
                        var_str += "..."
                else:
                    var_str = "—"
                self.parent.config_inspector_table.setItem(row, 7, QTableWidgetItem(var_str))

            # Parameter Space aus Template-Parametern erstellen
            param_space = {}
            for param_key, param_data in params.items():
                value = param_data.get('value')
                variations = param_data.get('variations', [])
                if variations:
                    param_space[param_key] = variations
                elif value is not None:
                    param_space[param_key] = [value]

            self.parent.param_space_text.setText(json.dumps(param_space, indent=2))

            # Template-Info loggen
            template_name = meta.get('name', 'Unbekannt')
            template_desc = meta.get('description', '')
            created_at = meta.get('created_at', '')

            self.parent._log(f"✅ Template '{template_name}' geladen")
            self.parent._log(f"   📅 Erstellt: {created_at[:10] if created_at else 'Unbekannt'}")
            self.parent._log(f"   📊 {len(params)} Parameter")

            if template_desc:
                self.parent._log(f"   📝 {template_desc[:50]}...")

        except Exception as e:
            logger.exception("Failed to load template")
            self.parent._log(f"❌ Template-Laden fehlgeschlagen: {e}")
            QMessageBox.critical(self.parent, "Fehler", f"Template-Laden fehlgeschlagen:\n{e}")

    def on_derive_variant_clicked(self) -> None:
        """Erstellt eine Variante basierend auf der aktuellen Basistabelle.

        Workflow:
        1. Prüfe ob Daten in config_inspector_table vorhanden
        2. Dialog mit Parameter-Editor (4 Spalten: Parameter, Basis-Wert, Neuer Wert, Ändern?)
        3. User wählt Parameter aus und editiert Werte
        4. Quick-Actions: "Alle auswählen" / "Keine auswählen"
        5. Variante zu param_space_text hinzufügen

        Dialog-Features:
        - Parameter-Name (read-only)
        - Basis-Wert (read-only, grau)
        - Neuer Wert (editierbar, grün)
        - Checkbox "Ändern?" (für Auswahl)
        """
        self.parent._log("📝 Variante ableiten...")

        # Prüfe ob Daten in Tabelle vorhanden
        if self.parent.config_inspector_table.rowCount() == 0:
            QMessageBox.warning(
                self.parent, "Keine Basisdaten",
                "Bitte zuerst Engine Configs laden oder ein Template öffnen."
            )
            return

        try:
            # Dialog für Varianten-Erstellung
            dialog = QDialog(self.parent)
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
            for row in range(self.parent.config_inspector_table.rowCount()):
                param_item = self.parent.config_inspector_table.item(row, 1)
                value_item = self.parent.config_inspector_table.item(row, 2)
                type_item = self.parent.config_inspector_table.item(row, 5)

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

                # Basis-Wert (read-only, grau)
                base_item = QTableWidgetItem(param['value'])
                base_item.setFlags(base_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                base_item.setForeground(QColor("#888"))
                param_table.setItem(row, 1, base_item)

                # Neuer Wert (editierbar, grün)
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
                    self.parent, "Keine Änderungen",
                    "Bitte wähle mindestens einen Parameter zum Ändern aus."
                )
                return

            # Variante zu Parameter-Space hinzufügen
            try:
                current_space_text = self.parent.param_space_text.toPlainText()
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

            self.parent.param_space_text.setText(json.dumps(current_space, indent=2))

            # Log Variante
            self.parent._log(f"✅ Variante '{variant_name}' erstellt mit {len(variant_params)} geänderten Parametern")
            for param, value in list(variant_params.items())[:5]:
                self.parent._log(f"   {param}: {value}")
            if len(variant_params) > 5:
                self.parent._log(f"   ... und {len(variant_params) - 5} weitere")

        except Exception as e:
            logger.exception("Failed to derive variant")
            self.parent._log(f"❌ Varianten-Erstellung fehlgeschlagen: {e}")
            QMessageBox.critical(self.parent, "Fehler", f"Varianten-Erstellung fehlgeschlagen:\n{e}")

    def _select_all_variant_checkboxes(self, table: QTableWidget, checked: bool) -> None:
        """Hilfsfunktion zum Auswählen/Abwählen aller Checkboxen.

        Args:
            table: Die Parameter-Tabelle mit Checkboxen
            checked: True = alle auswählen, False = keine auswählen
        """
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 3)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)

    def _convert_v2_to_parameters(self, template: dict[str, Any]) -> dict[str, Any]:
        """Konvertiert V2-Format Template zu V1-kompatiblem parameters-Dict.

        V2-Format hat verschachtelte Struktur wie:
        - entry_score.weights, entry_score.thresholds, entry_score.gates
        - exit_management.stop_loss, exit_management.take_profit
        - risk_leverage.risk_per_trade_pct, risk_leverage.base_leverage

        Args:
            template: Das V2-Format Template

        Returns:
            Dict im V1-parameters-Format für die UI-Anzeige
        """
        params: dict[str, Any] = {}

        # Mapping von V2-Pfaden zu V1-Parameter-Namen und Kategorien
        v2_mappings = [
            # Entry Score - Weights
            ('entry_score.weights.use_preset', 'weight_preset', 'Entry Score', 'Weights', 'Preset für Gewichtungen'),
            # Entry Score - Thresholds
            ('entry_score.thresholds.min_score_for_entry', 'min_score_for_entry', 'Entry Score', 'Thresholds', 'Minimum Entry Score'),
            # Entry Score - Gates
            ('entry_score.gates.block_in_chop', 'block_in_chop', 'Entry Score', 'Gates', 'Im Chop-Regime blocken'),
            ('entry_score.gates.block_against_strong_trend', 'block_against_strong_trend', 'Entry Score', 'Gates', 'Gegen starken Trend blocken'),
            ('entry_score.gates.allow_counter_trend_sfp', 'allow_counter_trend_sfp', 'Entry Score', 'Gates', 'Counter-Trend SFP erlauben'),
            # Entry Score - Indicator Params
            ('entry_score.indicator_params.ema_short', 'ema_short', 'Entry Score', 'Indicators', 'EMA Short Periode'),
            ('entry_score.indicator_params.ema_medium', 'ema_medium', 'Entry Score', 'Indicators', 'EMA Medium Periode'),
            ('entry_score.indicator_params.ema_long', 'ema_long', 'Entry Score', 'Indicators', 'EMA Long Periode'),
            ('entry_score.indicator_params.rsi_period', 'rsi_period', 'Entry Score', 'Indicators', 'RSI Periode'),
            ('entry_score.indicator_params.adx_strong_trend', 'adx_strong_trend', 'Entry Score', 'Indicators', 'ADX Schwelle für starken Trend'),
            # Entry Triggers
            ('entry_triggers.breakout.enabled', 'breakout_enabled', 'Entry Triggers', 'Breakout', 'Breakout-Trigger aktiv'),
            ('entry_triggers.breakout.volume_multiplier', 'breakout_volume_multiplier', 'Entry Triggers', 'Breakout', 'Volumen-Multiplikator'),
            ('entry_triggers.pullback.enabled', 'pullback_enabled', 'Entry Triggers', 'Pullback', 'Pullback-Trigger aktiv'),
            ('entry_triggers.pullback.max_distance_atr', 'pullback_max_distance_atr', 'Entry Triggers', 'Pullback', 'Max Distanz in ATR'),
            ('entry_triggers.sfp.enabled', 'sfp_enabled', 'Entry Triggers', 'SFP', 'SFP-Trigger aktiv'),
            # Exit Management - Stop Loss
            ('exit_management.stop_loss.type', 'sl_type', 'Exit Management', 'Stop Loss', 'Stop-Loss Typ'),
            ('exit_management.stop_loss.atr_multiplier', 'sl_atr_multiplier', 'Exit Management', 'Stop Loss', 'ATR-Multiplikator für SL'),
            # Exit Management - Take Profit
            ('exit_management.take_profit.type', 'tp_type', 'Exit Management', 'Take Profit', 'Take-Profit Typ'),
            ('exit_management.take_profit.atr_multiplier', 'tp_atr_multiplier', 'Exit Management', 'Take Profit', 'ATR-Multiplikator für TP'),
            ('exit_management.take_profit.use_level', 'tp_use_level', 'Exit Management', 'Take Profit', 'Level für TP verwenden'),
            # Exit Management - Trailing Stop
            ('exit_management.trailing_stop.enabled', 'trailing_enabled', 'Exit Management', 'Trailing', 'Trailing Stop aktiv'),
            ('exit_management.trailing_stop.move_to_breakeven', 'trailing_move_to_breakeven', 'Exit Management', 'Trailing', 'Move to Breakeven'),
            ('exit_management.trailing_stop.activation_atr', 'trailing_activation_atr', 'Exit Management', 'Trailing', 'Aktivierung in ATR'),
            ('exit_management.trailing_stop.distance_atr', 'trailing_distance_atr', 'Exit Management', 'Trailing', 'Trailing-Distanz in ATR'),
            # Risk & Leverage
            ('risk_leverage.risk_per_trade_pct', 'risk_per_trade_pct', 'Risk/Leverage', 'Risk', 'Risiko pro Trade in %'),
            ('risk_leverage.base_leverage', 'base_leverage', 'Risk/Leverage', 'Leverage', 'Basis-Hebel'),
            ('risk_leverage.max_leverage', 'max_leverage', 'Risk/Leverage', 'Leverage', 'Maximaler Hebel'),
            ('risk_leverage.min_liquidation_distance_pct', 'min_liquidation_distance_pct', 'Risk/Leverage', 'Risk', 'Min. Liquidations-Distanz %'),
            ('risk_leverage.max_daily_loss_pct', 'max_daily_loss_pct', 'Risk/Leverage', 'Risk', 'Max. täglicher Verlust %'),
            ('risk_leverage.max_trades_per_day', 'max_trades_per_day', 'Risk/Leverage', 'Limits', 'Max. Trades pro Tag'),
            ('risk_leverage.max_concurrent_positions', 'max_concurrent_positions', 'Risk/Leverage', 'Limits', 'Max. gleichzeitige Positionen'),
            # Execution Simulation
            ('execution_simulation.initial_capital', 'initial_capital', 'Simulation', 'Capital', 'Startkapital'),
            ('execution_simulation.fee_maker_pct', 'fee_maker_pct', 'Simulation', 'Fees', 'Maker-Fee %'),
            ('execution_simulation.fee_taker_pct', 'fee_taker_pct', 'Simulation', 'Fees', 'Taker-Fee %'),
            ('execution_simulation.slippage_bps', 'slippage_bps', 'Simulation', 'Slippage', 'Slippage in BPS'),
            # Strategy Profile
            ('strategy_profile.type', 'strategy_type', 'Strategy', 'Profile', 'Strategie-Typ'),
            ('strategy_profile.preset', 'strategy_preset', 'Strategy', 'Profile', 'Strategie-Preset'),
            ('strategy_profile.direction_bias', 'direction_bias', 'Strategy', 'Profile', 'Richtungs-Bias'),
            # Walk Forward
            ('walk_forward.enabled', 'wf_enabled', 'Walk Forward', 'Settings', 'Walk-Forward aktiv'),
            ('walk_forward.train_window_days', 'wf_train_window_days', 'Walk Forward', 'Settings', 'Training-Fenster (Tage)'),
            ('walk_forward.test_window_days', 'wf_test_window_days', 'Walk Forward', 'Settings', 'Test-Fenster (Tage)'),
        ]

        for v2_path, param_name, category, subcategory, description in v2_mappings:
            value = self._get_nested_value(template, v2_path)
            if value is not None:
                # Extrahiere optimize und range falls vorhanden (V2-Format für optimierbare Parameter)
                if isinstance(value, dict) and 'value' in value:
                    actual_value = value.get('value')
                    variations = value.get('range', [])
                    optimize = value.get('optimize', False)
                else:
                    actual_value = value
                    variations = []
                    optimize = False

                # Bestimme Typ
                if isinstance(actual_value, bool):
                    param_type = 'bool'
                elif isinstance(actual_value, int):
                    param_type = 'int'
                elif isinstance(actual_value, float):
                    param_type = 'float'
                elif isinstance(actual_value, str):
                    param_type = 'str'
                else:
                    param_type = 'unknown'

                params[param_name] = {
                    'value': actual_value,
                    'type': param_type,
                    'category': category,
                    'subcategory': subcategory,
                    'description': description,
                    'min': None,
                    'max': None,
                    'variations': variations if variations else [actual_value] if actual_value is not None else [],
                    'optimize': optimize,
                }

        return params

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """Holt einen verschachtelten Wert aus einem Dict via Punkt-Notation.

        Args:
            data: Das Source-Dictionary
            path: Punkt-separierter Pfad (z.B. 'entry_score.weights.use_preset')

        Returns:
            Der Wert am Pfad oder None wenn nicht gefunden
        """
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
