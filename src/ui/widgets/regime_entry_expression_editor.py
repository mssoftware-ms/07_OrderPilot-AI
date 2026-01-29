"""Regime Entry Expression Editor - UI für CEL Entry Expression Erstellung.

GUI zum Erstellen von CEL Entry Expressions für Regime JSON Dateien.
Verwendet Parser, Generator und Writer für vollständigen Workflow.

Author: Claude Code
Date: 2026-01-29
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QFileDialog, QMessageBox, QTextEdit, QComboBox,
    QCheckBox, QScrollArea, QSplitter, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.ui.widgets.regime_json_parser import (
    RegimeJsonParser, RegimeJsonData, RegimeInfo
)
from src.ui.widgets.entry_expression_generator import (
    EntryExpressionGenerator, StrategyTemplate
)
from src.ui.widgets.regime_json_writer import RegimeJsonWriter

logger = logging.getLogger(__name__)


class RegimeEntryExpressionEditor(QWidget):
    """Editor für Regime JSON Entry Expressions.

    Workflow:
    1. Lade Regime JSON (File Picker)
    2. Wähle Regimes für Long/Short (Checkboxen)
    3. Wähle Template oder Custom
    4. Generiere Expression (Preview)
    5. Validiere Expression
    6. Speichere in JSON
    """

    expression_generated = pyqtSignal(str)  # Wenn Expression generiert
    json_saved = pyqtSignal(str)  # Wenn JSON gespeichert

    def __init__(self, parent=None):
        super().__init__(parent)
        self._regime_data: Optional[RegimeJsonData] = None
        self._long_checkboxes: dict[str, QCheckBox] = {}
        self._short_checkboxes: dict[str, QCheckBox] = {}
        self._current_expression: str = ""

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI mit allen Komponenten."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === Header ===
        header = self._create_header()
        layout.addWidget(header)

        # === Splitter: Regime Selection + Preview ===
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Regime Selection
        selection_panel = self._create_selection_panel()
        splitter.addWidget(selection_panel)

        # Right: Expression Preview
        preview_panel = self._create_preview_panel()
        splitter.addWidget(preview_panel)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter, 1)

        # === Footer: Actions ===
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Erstellt Header mit JSON Loader."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("📊 Regime Entry Expression Editor")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4A9EFF;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Erstelle CEL Entry Expressions für Regime JSON Dateien. "
            "Wähle Regimes für Long/Short Entry."
        )
        subtitle.setStyleSheet("color: #888; font-size: 11px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # JSON File Loader
        loader_layout = QHBoxLayout()

        self.json_path_label = QLabel("Keine JSON geladen")
        self.json_path_label.setStyleSheet("color: #666; font-size: 11px;")
        loader_layout.addWidget(self.json_path_label, 1)

        self.load_json_btn = QPushButton("📂 Regime JSON laden")
        self.load_json_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.load_json_btn.clicked.connect(self._on_load_json_clicked)
        loader_layout.addWidget(self.load_json_btn)

        layout.addLayout(loader_layout)

        return widget

    def _create_selection_panel(self) -> QWidget:
        """Erstellt Regime Selection Panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # === Template Selection ===
        template_group = QGroupBox("📋 Strategy Template")
        template_layout = QVBoxLayout(template_group)

        self.template_combo = QComboBox()
        self.template_combo.addItem("Conservative (Nur STRONG_TF)", StrategyTemplate.CONSERVATIVE)
        self.template_combo.addItem("Moderate (Strong Bull/Bear)", StrategyTemplate.MODERATE)
        self.template_combo.addItem("Aggressive (Alle Trends)", StrategyTemplate.AGGRESSIVE)
        self.template_combo.addItem("Mean Reversion (Exhaustion)", StrategyTemplate.MEAN_REVERSION)
        self.template_combo.addItem("Custom (Manuelle Auswahl)", StrategyTemplate.CUSTOM)
        self.template_combo.setCurrentIndex(1)  # Moderate
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        template_layout.addWidget(self.template_combo)

        self.template_desc_label = QLabel()
        self.template_desc_label.setStyleSheet("color: #888; font-size: 10px;")
        self.template_desc_label.setWordWrap(True)
        template_layout.addWidget(self.template_desc_label)

        self.apply_template_btn = QPushButton("✨ Template anwenden")
        self.apply_template_btn.clicked.connect(self._on_apply_template_clicked)
        template_layout.addWidget(self.apply_template_btn)

        layout.addWidget(template_group)

        # === Direction Selection ===
        direction_group = QGroupBox("🎯 Entry Direction")
        direction_layout = QVBoxLayout(direction_group)

        self.direction_button_group = QButtonGroup()
        self.direction_long_short = QRadioButton("Long + Short")
        self.direction_long_only = QRadioButton("Long only")
        self.direction_short_only = QRadioButton("Short only")
        self.direction_long_short.setChecked(True)

        self.direction_button_group.addButton(self.direction_long_short, 0)
        self.direction_button_group.addButton(self.direction_long_only, 1)
        self.direction_button_group.addButton(self.direction_short_only, 2)

        direction_layout.addWidget(self.direction_long_short)
        direction_layout.addWidget(self.direction_long_only)
        direction_layout.addWidget(self.direction_short_only)

        layout.addWidget(direction_group)

        # === Regime Selection (Scroll Area) ===
        regime_group = QGroupBox("🔹 Regime Selection")
        regime_layout = QVBoxLayout(regime_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)

        self.regime_selection_widget = QWidget()
        self.regime_selection_layout = QVBoxLayout(self.regime_selection_widget)
        self.regime_selection_layout.setContentsMargins(5, 5, 5, 5)

        self.no_regimes_label = QLabel("Keine Regime JSON geladen")
        self.no_regimes_label.setStyleSheet("color: #666; font-style: italic;")
        self.regime_selection_layout.addWidget(self.no_regimes_label)

        scroll.setWidget(self.regime_selection_widget)
        regime_layout.addWidget(scroll)

        layout.addWidget(regime_group, 1)

        return widget

    def _create_preview_panel(self) -> QWidget:
        """Erstellt Expression Preview Panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # === Preview Group ===
        preview_group = QGroupBox("📝 Generated Expression Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.expression_preview = QTextEdit()
        self.expression_preview.setReadOnly(False)  # Editierbar!
        self.expression_preview.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        self.expression_preview.setPlaceholderText(
            "Expression wird hier angezeigt...\n\n"
            "1. Lade eine Regime JSON\n"
            "2. Wähle Template oder Regimes\n"
            "3. Klicke 'Generate'\n\n"
            "Du kannst die Expression auch direkt hier bearbeiten!"
        )
        preview_layout.addWidget(self.expression_preview, 1)
        
        # Button: Update from Edit
        self.update_from_edit_btn = QPushButton("✏️ Übernehme Änderungen aus Editor")
        self.update_from_edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.update_from_edit_btn.setToolTip("Übernimmt die bearbeitete Expression aus dem Editor")
        self.update_from_edit_btn.clicked.connect(self._on_update_from_edit_clicked)
        self.update_from_edit_btn.setEnabled(False)
        preview_layout.addWidget(self.update_from_edit_btn)
        
        # Connect textChanged to enable update button
        self.expression_preview.textChanged.connect(self._on_expression_text_changed)

        # Info Label
        self.preview_info_label = QLabel()
        self.preview_info_label.setStyleSheet("color: #888; font-size: 10px;")
        self.preview_info_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_info_label)

        layout.addWidget(preview_group, 1)

        # === Current Expression (if exists) ===
        current_group = QGroupBox("💾 Existing Expression in JSON")
        current_layout = QVBoxLayout(current_group)

        self.current_expression_label = QLabel("Keine entry_expression in JSON vorhanden")
        self.current_expression_label.setStyleSheet(
            "color: #888; font-size: 11px; font-family: 'Consolas', monospace;"
        )
        self.current_expression_label.setWordWrap(True)
        current_layout.addWidget(self.current_expression_label)

        layout.addWidget(current_group)

        return widget

    def _create_footer(self) -> QWidget:
        """Erstellt Footer mit Action Buttons."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        # Generate Button
        self.generate_btn = QPushButton("⚡ Generate Expression")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_btn)

        # Validate Button
        self.validate_btn = QPushButton("✓ Validate")
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self._on_validate_clicked)
        layout.addWidget(self.validate_btn)

        layout.addStretch()

        # Save Button
        self.save_btn = QPushButton("💾 Save to JSON")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.save_btn)

        # Save As Button
        self.save_as_btn = QPushButton("💾 Save As...")
        self.save_as_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.save_as_btn.setEnabled(False)
        self.save_as_btn.clicked.connect(self._on_save_as_clicked)
        layout.addWidget(self.save_as_btn)

        return widget

    # === Event Handlers ===

    def _on_load_json_clicked(self):
        """Handler: JSON Laden."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Regime JSON auswählen",
            "03_JSON/Entry_Analyzer/Regime/",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        self._load_json(file_path)

    def _load_json(self, file_path: str):
        """Lädt Regime JSON und aktualisiert UI."""
        try:
            # Parse JSON
            self._regime_data = RegimeJsonParser.parse(file_path)

            # Update UI
            self.json_path_label.setText(f"📂 {Path(file_path).name}")
            self.json_path_label.setStyleSheet("color: #4CAF50; font-size: 11px;")

            # Update current expression label
            if self._regime_data.has_entry_expression:
                expr = self._regime_data.current_expression[:100]
                self.current_expression_label.setText(
                    f"✅ Vorhanden: {expr}..."
                )
                self.current_expression_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
            else:
                self.current_expression_label.setText(
                    "❌ Keine entry_expression vorhanden (muss hinzugefügt werden)"
                )
                self.current_expression_label.setStyleSheet("color: #FF9800; font-size: 11px;")

            # Populate regime checkboxes
            self._populate_regime_checkboxes()

            # Wenn entry_expression vorhanden: Im Preview anzeigen und Checkboxen setzen
            if self._regime_data.has_entry_expression and self._regime_data.current_expression:
                self._load_existing_expression()

            # Enable buttons
            self.generate_btn.setEnabled(True)

            logger.info(f"Loaded {len(self._regime_data.regimes)} regimes from {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler beim Laden",
                f"Regime JSON konnte nicht geladen werden:\n\n{e}"
            )
            logger.exception(f"Failed to load JSON: {file_path}")

    def _populate_regime_checkboxes(self):
        """Erstellt Checkboxen für alle Regimes."""
        # Clear old checkboxes
        while self.regime_selection_layout.count():
            item = self.regime_selection_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._long_checkboxes.clear()
        self._short_checkboxes.clear()

        if not self._regime_data:
            return

        # Long Regimes
        long_label = QLabel("🟢 Long Entry Regimes:")
        long_label.setStyleSheet("font-weight: bold; color: #4CAF50; margin-top: 10px;")
        self.regime_selection_layout.addWidget(long_label)

        for regime in self._regime_data.regimes:
            checkbox = QCheckBox(regime.display_name)
            checkbox.setStyleSheet("color: #ddd;")
            self._long_checkboxes[regime.id] = checkbox
            self.regime_selection_layout.addWidget(checkbox)

        # Short Regimes
        short_label = QLabel("🔴 Short Entry Regimes:")
        short_label.setStyleSheet("font-weight: bold; color: #f44336; margin-top: 15px;")
        self.regime_selection_layout.addWidget(short_label)

        for regime in self._regime_data.regimes:
            checkbox = QCheckBox(regime.display_name)
            checkbox.setStyleSheet("color: #ddd;")
            self._short_checkboxes[regime.id] = checkbox
            self.regime_selection_layout.addWidget(checkbox)

        self.regime_selection_layout.addStretch()

    def _on_template_changed(self, index: int):
        """Handler: Template geändert."""
        template = self.template_combo.itemData(index)
        desc = EntryExpressionGenerator.get_template_description(template)
        self.template_desc_label.setText(desc)

    def _on_apply_template_clicked(self):
        """Handler: Template anwenden."""
        if not self._regime_data:
            QMessageBox.warning(self, "Keine JSON geladen", "Bitte zuerst eine Regime JSON laden.")
            return

        template_index = self.template_combo.currentIndex()
        template = self.template_combo.itemData(template_index)

        # Generiere Regime-Auswahl vom Template
        gen = EntryExpressionGenerator()
        long_regimes, short_regimes = gen.generate_from_template(
            template,
            self._regime_data.regime_ids
        )

        # Update checkboxes
        for regime_id, checkbox in self._long_checkboxes.items():
            checkbox.setChecked(regime_id in long_regimes)

        for regime_id, checkbox in self._short_checkboxes.items():
            checkbox.setChecked(regime_id in short_regimes)

        logger.info(f"Template applied: {template.value} → Long: {long_regimes}, Short: {short_regimes}")

    def _on_generate_clicked(self):
        """Handler: Expression generieren."""
        if not self._regime_data:
            return

        # Sammle ausgewählte Regimes
        long_regimes = [
            regime_id for regime_id, cb in self._long_checkboxes.items()
            if cb.isChecked()
        ]
        short_regimes = [
            regime_id for regime_id, cb in self._short_checkboxes.items()
            if cb.isChecked()
        ]

        # Prüfe Direction
        direction_id = self.direction_button_group.checkedId()
        if direction_id == 1:  # Long only
            short_regimes = []
        elif direction_id == 2:  # Short only
            long_regimes = []

        # Validierung
        if not long_regimes and not short_regimes:
            QMessageBox.warning(
                self,
                "Keine Regimes ausgewählt",
                "Bitte wähle mindestens ein Regime für Long oder Short Entry."
            )
            return

        # Generiere Expression
        gen = EntryExpressionGenerator()
        self._current_expression = gen.generate(
            long_regimes=long_regimes,
            short_regimes=short_regimes,
            add_trigger=True,
            add_side_check=True,
            pretty=True
        )

        # Update Preview
        self.expression_preview.setPlainText(self._current_expression)

        # Update Info
        self.preview_info_label.setText(
            f"✅ Expression generiert | "
            f"Long Regimes: {len(long_regimes)} | "
            f"Short Regimes: {len(short_regimes)}"
        )
        self.preview_info_label.setStyleSheet("color: #4CAF50; font-size: 10px;")

        # Enable buttons
        self.validate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.save_as_btn.setEnabled(True)

        # Emit signal
        self.expression_generated.emit(self._current_expression)

        logger.info(f"Expression generated: {self._current_expression[:80]}...")

    def _on_validate_clicked(self):
        """Handler: Expression validieren."""
        if not self._current_expression:
            QMessageBox.warning(self, "Keine Expression", "Bitte zuerst eine Expression generieren.")
            return

        try:
            # Validiere mit CELEngine (Import nur wenn nötig)
            from src.core.tradingbot.cel_engine import CELEngine

            cel = CELEngine()

            # Test-Context
            test_context = {
                "side": "long",
                "rsi": 55,
                "adx": 30,
                "chart_window": None,
                "last_closed_candle": {"regime": "STRONG_BULL"}
            }

            result = cel.evaluate(self._current_expression, test_context)

            QMessageBox.information(
                self,
                "✅ Validation Success",
                f"Expression ist valide!\n\n"
                f"Test-Evaluation mit STRONG_BULL + Long:\n"
                f"Result: {result}\n\n"
                f"Expression kann gespeichert werden."
            )

            logger.info(f"Expression validated successfully: {result}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Validation Failed",
                f"Expression ist NICHT valide:\n\n{e}\n\n"
                f"Bitte korrigiere die Expression."
            )
            logger.exception("Expression validation failed")

    def _on_save_clicked(self):
        """Handler: In JSON speichern (überschreiben)."""
        if not self._regime_data or not self._current_expression:
            return

        reply = QMessageBox.question(
            self,
            "In JSON speichern?",
            f"entry_expression wird in JSON gespeichert:\n\n"
            f"📂 {Path(self._regime_data.file_path).name}\n\n"
            f"Backup wird automatisch erstellt.\n\n"
            f"Fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        writer = RegimeJsonWriter()
        success, message = writer.write_entry_expression(
            self._regime_data.file_path,
            self._current_expression,
            create_backup=True,
            add_comments=True
        )

        if success:
            QMessageBox.information(self, "✅ Gespeichert", message)
            self.json_saved.emit(self._regime_data.file_path)

            # Reload JSON um Updated state zu zeigen
            self._load_json(self._regime_data.file_path)
        else:
            QMessageBox.critical(self, "❌ Fehler", message)

    def _on_save_as_clicked(self):
        """Handler: Als neue Datei speichern."""
        if not self._regime_data or not self._current_expression:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Speichern als...",
            str(Path(self._regime_data.file_path).parent),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        writer = RegimeJsonWriter()
        success, message, new_path = writer.save_as_new(
            self._regime_data.file_path,
            self._current_expression,
            Path(file_path).name
        )

        if success:
            QMessageBox.information(self, "✅ Gespeichert", message)
            self.json_saved.emit(str(new_path))

            # Reload new JSON
            self._load_json(str(new_path))
        else:
            QMessageBox.critical(self, "❌ Fehler", message)

    def _on_expression_text_changed(self):
        """Handler: Expression Text wurde im Editor geändert."""
        # Enable Update Button wenn Text vorhanden
        text = self.expression_preview.toPlainText().strip()
        if text:
            self.update_from_edit_btn.setEnabled(True)

    def _on_update_from_edit_clicked(self):
        """Handler: Übernimmt bearbeitete Expression aus dem Editor."""
        # Hole Text aus Editor
        edited_expression = self.expression_preview.toPlainText().strip()
        
        if not edited_expression:
            QMessageBox.warning(
                self,
                "Keine Expression",
                "Der Editor ist leer. Bitte gib eine Expression ein."
            )
            return
        
        # Update current expression
        self._current_expression = edited_expression
        
        # Update Info
        self.preview_info_label.setText(
            f"✏️ Expression aus Editor übernommen | Länge: {len(edited_expression)} Zeichen"
        )
        self.preview_info_label.setStyleSheet("color: #9C27B0; font-size: 10px;")
        
        # Enable Validate/Save Buttons
        self.validate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.save_as_btn.setEnabled(True)
        
        logger.info(f"Expression from edit accepted: {edited_expression[:80]}...")
        
        QMessageBox.information(
            self,
            "✅ Übernommen",
            f"Expression wurde übernommen!\n\n"
            f"Länge: {len(edited_expression)} Zeichen\n\n"
            f"Du kannst jetzt validieren oder speichern."
        )

    # === Loading Existing Expression ===

    def _load_existing_expression(self):
        """Lädt existierende entry_expression aus JSON und zeigt sie im Preview an.
        
        Versucht auch die Expression zu parsen und die Checkboxen entsprechend zu setzen.
        """
        if not self._regime_data or not self._regime_data.current_expression:
            return
        
        expression = self._regime_data.current_expression
        
        # Zeige Expression im Preview
        self._current_expression = expression
        self.expression_preview.setPlainText(expression)
        
        # Update Info Label
        self.preview_info_label.setText(
            f"📂 Expression aus JSON geladen | Länge: {len(expression)} Zeichen"
        )
        self.preview_info_label.setStyleSheet("color: #2196F3; font-size: 10px;")
        
        # Enable Buttons
        self.validate_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.save_as_btn.setEnabled(True)
        self.update_from_edit_btn.setEnabled(True)  # User kann die Expression bearbeiten
        
        # Versuche Expression zu parsen und Checkboxen zu setzen
        self._parse_expression_and_set_checkboxes(expression)
        
        logger.info(f"Loaded existing expression from JSON ({len(expression)} chars)")
    
    def _parse_expression_and_set_checkboxes(self, expression: str):
        """Versucht die Expression zu parsen und Checkboxen zu setzen.
        
        Sucht nach Regime-Namen in der Expression und aktiviert die entsprechenden Checkboxen.
        """
        if not self._regime_data:
            return
        
        # Einfaches Parsing: Suche nach last_closed_regime() == 'REGIME_NAME'
        import re
        
        # Pattern: last_closed_regime() == 'REGIME_NAME'
        pattern = r"last_closed_regime\(\)\s*==\s*['\"]([A-Z_]+)['\"]"
        matches = re.findall(pattern, expression)
        
        if not matches:
            logger.info("Konnte keine Regime-Namen in Expression finden (kein last_closed_regime())")
            return
        
        logger.info(f"Gefundene Regime-Namen in Expression: {matches}")
        
        # Versuche zu erkennen ob Long oder Short basierend auf Kontext
        # Pattern: side == 'long' && ... last_closed_regime() == 'REGIME'
        long_section_pattern = r"side\s*==\s*['\"]long['\"]\s*&&\s*\([^)]*last_closed_regime\(\)\s*==\s*['\"]([A-Z_]+)['\"]"
        short_section_pattern = r"side\s*==\s*['\"]short['\"]\s*&&\s*\([^)]*last_closed_regime\(\)\s*==\s*['\"]([A-Z_]+)['\"]"
        
        long_regimes = re.findall(long_section_pattern, expression)
        short_regimes = re.findall(short_section_pattern, expression)
        
        # Wenn keine Side-spezifischen Patterns gefunden, versuche heuristisch
        if not long_regimes and not short_regimes:
            # Heuristik: Bull/TF → Long, Bear → Short
            for regime_name in matches:
                if 'BULL' in regime_name or 'TF' in regime_name:
                    long_regimes.append(regime_name)
                elif 'BEAR' in regime_name:
                    short_regimes.append(regime_name)
                else:
                    # Unbekannt - zu Long hinzufügen
                    long_regimes.append(regime_name)
        
        # Setze Checkboxen
        for regime_id in long_regimes:
            if regime_id in self._long_checkboxes:
                self._long_checkboxes[regime_id].setChecked(True)
                logger.info(f"Set Long checkbox: {regime_id}")
        
        for regime_id in short_regimes:
            if regime_id in self._short_checkboxes:
                self._short_checkboxes[regime_id].setChecked(True)
                logger.info(f"Set Short checkbox: {regime_id}")
        
        # Update Info
        if long_regimes or short_regimes:
            self.preview_info_label.setText(
                f"📂 Expression geladen & geparst | "
                f"Long: {len(long_regimes)} | Short: {len(short_regimes)}"
            )
            self.preview_info_label.setStyleSheet("color: #4CAF50; font-size: 10px;")

    # === Public API ===

    def load_json_path(self, json_path: str):
        """Lädt JSON programmatisch (für externe Aufrufe)."""
        self._load_json(json_path)

    def get_current_expression(self) -> str:
        """Gibt aktuelle generierte Expression zurück."""
        return self._current_expression
