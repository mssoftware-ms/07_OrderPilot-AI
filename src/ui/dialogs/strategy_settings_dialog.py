"""
Strategy Settings Dialog - JSON-basiertes Strategy Management.

Popup-Dialog für:
- Laden/Löschen/Bearbeiten von JSON-Strategien
- Live Regime-Anzeige
- Strategy-Tabelle mit Status
- Indikatorenset-Auswahl basierend auf Regime

Öffnet sich via Button "Settings Bot" im Trading Bot Tab.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QCheckBox,
)

logger = logging.getLogger(__name__)

# JSON-Verzeichnis gemäß Projektvorgabe
JSON_DIR = Path("03_JSON/Trading_Bot")


class StrategySettingsDialog(QDialog):
    """
    Strategy Settings Popup-Dialog.

    Features:
    - Strategy-Tabelle (Name, Typ, Status, Aktiv/Inaktiv)
    - Live Regime-Anzeige
    - Indikatorenset für aktuelles Regime
    - Buttons: Laden, Löschen, Neu erstellen, Bearbeiten
    - Auto-Refresh alle 5 Sekunden

    Signals:
        strategy_loaded: Emitted when strategy is loaded
        strategy_deleted: Emitted when strategy is deleted
    """

    strategy_loaded = pyqtSignal(str)  # strategy_id
    strategy_deleted = pyqtSignal(str)  # strategy_id

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.setWindowTitle("Strategy Settings - JSON Management")
        self.resize(1000, 700)

        # State
        self.strategies = {}  # strategy_id -> config
        self.current_regime = "Unknown"
        self.active_strategy_set = None

        self._setup_ui()
        self._load_strategies()
        self._start_auto_refresh()

    def _setup_ui(self) -> None:
        """Setup the complete UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Header
        header = QLabel("<h2>🎯 Strategy Management</h2>")
        main_layout.addWidget(header)

        desc = QLabel(
            "Verwalte JSON-basierte Trading-Strategien.\n"
            f"JSON-Verzeichnis: {JSON_DIR}"
        )
        desc.setStyleSheet("color: #888;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # === Live Regime Section ===
        regime_group = QGroupBox("📊 Live Markt-Regime")
        regime_layout = QVBoxLayout(regime_group)

        regime_info_layout = QHBoxLayout()

        # Current Regime Label
        regime_info_layout.addWidget(QLabel("<b>Aktuelles Regime:</b>"))
        self._regime_label = QLabel(self.current_regime)
        self._regime_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ff6b35; padding: 4px 12px;"
        )
        regime_info_layout.addWidget(self._regime_label)

        regime_info_layout.addStretch()

        # Active Strategy Set
        regime_info_layout.addWidget(QLabel("<b>Aktives Strategy Set:</b>"))
        self._active_set_label = QLabel("Keines")
        self._active_set_label.setStyleSheet("font-size: 14px; color: #4CAF50;")
        regime_info_layout.addWidget(self._active_set_label)

        regime_layout.addLayout(regime_info_layout)

        # Indicator Set for current Regime
        ind_layout = QHBoxLayout()
        ind_layout.addWidget(QLabel("<b>Indikatorenset:</b>"))
        self._indicator_list_label = QLabel("Noch keine Daten")
        self._indicator_list_label.setStyleSheet("color: #666;")
        self._indicator_list_label.setWordWrap(True)
        ind_layout.addWidget(self._indicator_list_label, 1)
        regime_layout.addLayout(ind_layout)

        main_layout.addWidget(regime_group)

        # === Strategy Table ===
        table_group = QGroupBox("📋 Verfügbare Strategien")
        table_layout = QVBoxLayout(table_group)

        self._strategy_table = QTableWidget()
        self._strategy_table.setColumnCount(6)
        self._strategy_table.setHorizontalHeaderLabels([
            "Name", "Typ", "Indikatoren", "Entry Conditions", "Exit Conditions", "Aktiv"
        ])

        # Column widths
        header = self._strategy_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self._strategy_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._strategy_table.setAlternatingRowColors(True)
        self._strategy_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #2a2a2a; }"
        )

        table_layout.addWidget(self._strategy_table)
        main_layout.addWidget(table_group, 1)

        # === Action Buttons ===
        button_layout = QHBoxLayout()

        self._load_btn = QPushButton("📁 Laden")
        self._load_btn.setToolTip("JSON-Strategie aus Datei laden")
        self._load_btn.clicked.connect(self._load_strategy_from_file)
        button_layout.addWidget(self._load_btn)

        self._delete_btn = QPushButton("🗑️ Löschen")
        self._delete_btn.setToolTip("Ausgewählte Strategie löschen")
        self._delete_btn.clicked.connect(self._delete_selected_strategy)
        button_layout.addWidget(self._delete_btn)

        self._new_btn = QPushButton("➕ Neu erstellen")
        self._new_btn.setToolTip("Neue JSON-Strategie erstellen")
        self._new_btn.clicked.connect(self._create_new_strategy)
        button_layout.addWidget(self._new_btn)

        self._edit_btn = QPushButton("✏️ Bearbeiten")
        self._edit_btn.setToolTip("Ausgewählte Strategie bearbeiten")
        self._edit_btn.clicked.connect(self._edit_selected_strategy)
        button_layout.addWidget(self._edit_btn)

        button_layout.addStretch()

        self._refresh_btn = QPushButton("🔄 Aktualisieren")
        self._refresh_btn.clicked.connect(self._load_strategies)
        button_layout.addWidget(self._refresh_btn)

        self._close_btn = QPushButton("❌ Schließen")
        self._close_btn.clicked.connect(self.close)
        button_layout.addWidget(self._close_btn)

        main_layout.addLayout(button_layout)

    def _load_strategies(self) -> None:
        """Load all strategies from JSON directory."""
        self.strategies.clear()
        self._strategy_table.setRowCount(0)

        # Ensure directory exists
        JSON_DIR.mkdir(parents=True, exist_ok=True)

        # Load all JSON files
        json_files = list(JSON_DIR.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON strategy files in {JSON_DIR}")

        for json_file in sorted(json_files):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                strategy_id = json_file.stem
                self.strategies[strategy_id] = config

                self._add_strategy_to_table(strategy_id, config)

            except Exception as e:
                logger.error(f"Failed to load {json_file.name}: {e}")

        logger.info(f"Loaded {len(self.strategies)} strategies")

        # Update indicator set
        self._update_indicator_set()

    def _add_strategy_to_table(self, strategy_id: str, config: dict) -> None:
        """Add strategy to table."""
        row = self._strategy_table.rowCount()
        self._strategy_table.insertRow(row)

        # Extract strategy info (first strategy in config)
        strategy = config.get("strategies", [{}])[0]
        name = strategy.get("name", strategy_id)

        # Try to determine type from strategy ID or config
        strategy_type = "Unknown"
        if "trend_following" in strategy_id:
            strategy_type = "Trend Following"
        elif "mean_reversion" in strategy_id:
            strategy_type = "Mean Reversion"
        elif "breakout" in strategy_id:
            strategy_type = "Breakout"
        elif "momentum" in strategy_id:
            strategy_type = "Momentum"
        elif "scalping" in strategy_id:
            strategy_type = "Scalping"
        elif "sideways" in strategy_id:
            strategy_type = "Sideways"

        # Count indicators
        indicators = config.get("indicators", [])
        indicator_count = len(indicators)

        # Count conditions
        entry_all = strategy.get("entry", {}).get("all", [])
        entry_any = strategy.get("entry", {}).get("any", [])
        entry_count = len(entry_all) + len(entry_any)

        exit_all = strategy.get("exit", {}).get("all", [])
        exit_any = strategy.get("exit", {}).get("any", [])
        exit_count = len(exit_all) + len(exit_any)

        # Add cells
        self._strategy_table.setItem(row, 0, QTableWidgetItem(name))
        self._strategy_table.setItem(row, 1, QTableWidgetItem(strategy_type))
        self._strategy_table.setItem(row, 2, QTableWidgetItem(str(indicator_count)))
        self._strategy_table.setItem(row, 3, QTableWidgetItem(str(entry_count)))
        self._strategy_table.setItem(row, 4, QTableWidgetItem(str(exit_count)))

        # Active checkbox
        active_checkbox = QCheckBox()
        active_checkbox.setChecked(False)  # TODO: Load from bot state
        self._strategy_table.setCellWidget(row, 5, active_checkbox)

    def _load_strategy_from_file(self) -> None:
        """Load strategy from external JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "JSON-Strategie laden",
            str(JSON_DIR),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            # Copy file to JSON directory
            source = Path(file_path)
            target = JSON_DIR / source.name

            if target.exists():
                reply = QMessageBox.question(
                    self,
                    "Überschreiben?",
                    f"Datei '{source.name}' existiert bereits. Überschreiben?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.No:
                    return

            # Copy file
            import shutil
            shutil.copy(source, target)

            logger.info(f"Loaded strategy from {source} to {target}")

            # Reload strategies
            self._load_strategies()

            QMessageBox.information(
                self,
                "Erfolg",
                f"Strategie '{source.name}' erfolgreich geladen!"
            )

            self.strategy_loaded.emit(source.stem)

        except Exception as e:
            logger.error(f"Failed to load strategy from file: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Strategie konnte nicht geladen werden:\n{e}"
            )

    def _delete_selected_strategy(self) -> None:
        """Delete selected strategy."""
        selected_rows = self._strategy_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Keine Auswahl",
                "Bitte wähle eine Strategie zum Löschen aus."
            )
            return

        row = selected_rows[0].row()
        name = self._strategy_table.item(row, 0).text()

        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Strategie '{name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Find strategy_id from table
                strategy_id = None
                for sid, config in self.strategies.items():
                    strategy = config.get("strategies", [{}])[0]
                    if strategy.get("name") == name:
                        strategy_id = sid
                        break

                if strategy_id:
                    # Delete JSON file
                    json_file = JSON_DIR / f"{strategy_id}.json"
                    if json_file.exists():
                        json_file.unlink()

                    logger.info(f"Deleted strategy: {strategy_id}")

                    # Reload
                    self._load_strategies()

                    QMessageBox.information(
                        self,
                        "Erfolg",
                        f"Strategie '{name}' wurde gelöscht."
                    )

                    self.strategy_deleted.emit(strategy_id)

            except Exception as e:
                logger.error(f"Failed to delete strategy: {e}")
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Strategie konnte nicht gelöscht werden:\n{e}"
                )

    def _create_new_strategy(self) -> None:
        """Create new strategy from template."""
        QMessageBox.information(
            self,
            "Feature in Entwicklung",
            "Strategie-Editor wird in der nächsten Version verfügbar sein.\n\n"
            "Vorerst bitte JSON-Dateien manuell erstellen und laden."
        )

    def _edit_selected_strategy(self) -> None:
        """Edit selected strategy."""
        selected_rows = self._strategy_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Keine Auswahl",
                "Bitte wähle eine Strategie zum Bearbeiten aus."
            )
            return

        QMessageBox.information(
            self,
            "Feature in Entwicklung",
            "Strategie-Editor wird in der nächsten Version verfügbar sein.\n\n"
            "Vorerst bitte JSON-Dateien extern bearbeiten."
        )

    def _update_indicator_set(self) -> None:
        """Update indicator set for current regime."""
        if not self.strategies:
            self._indicator_list_label.setText("Keine Strategien geladen")
            return

        # Collect all unique indicators from all strategies
        all_indicators = set()
        for config in self.strategies.values():
            for indicator in config.get("indicators", []):
                all_indicators.add(indicator.get("id", "unknown"))

        # Display
        if all_indicators:
            indicator_text = ", ".join(sorted(all_indicators))
            self._indicator_list_label.setText(indicator_text)
        else:
            self._indicator_list_label.setText("Keine Indikatoren gefunden")

    def _start_auto_refresh(self) -> None:
        """Start auto-refresh timer for live regime update."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._update_regime)
        self._refresh_timer.start(5000)  # Update every 5 seconds

    def _update_regime(self) -> None:
        """Update live regime display (TODO: Connect to actual RegimeDetector)."""
        # TODO: Get actual regime from RegimeDetector
        # For now, placeholder
        pass

    def set_current_regime(self, regime: str) -> None:
        """Set current regime (called from Bot)."""
        self.current_regime = regime
        self._regime_label.setText(regime)
        self._update_indicator_set()

    def set_active_strategy_set(self, strategy_set_id: str) -> None:
        """Set active strategy set (called from Bot)."""
        self.active_strategy_set = strategy_set_id
        self._active_set_label.setText(strategy_set_id)
