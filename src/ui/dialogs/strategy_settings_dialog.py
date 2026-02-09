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
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.tradingbot.strategy_settings_pipeline import StrategySettingsPipeline
from src.ui.dialogs.score_calculation_worker import ScoreCalculationWorker

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
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
    QCheckBox,
    QProgressDialog,
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
    draw_regime_lines_requested = pyqtSignal(list)  # regime periods for chart

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.setWindowTitle("Strategy Settings - JSON Management")
        self.resize(1000, 700)

        # State
        self.strategies = {}  # strategy_id -> config
        self.strategy_load_errors = {}  # strategy_id -> error message
        self.current_regime = "Unknown"
        self.active_strategy_set = None
        self._pipeline = StrategySettingsPipeline()
        self._score_explain_by_row: dict[int, dict] = {}

        # Worker thread for score calculation
        self._score_worker: ScoreCalculationWorker | None = None
        self._progress_dialog: QProgressDialog | None = None

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

        # === Matched Strategy Section ===
        matched_group = QGroupBox("🎯 Matched Strategy (from Analysis)")
        matched_layout = QVBoxLayout(matched_group)

        self._matched_strategy_label = QLabel("No analysis performed yet")
        self._matched_strategy_label.setStyleSheet("font-size: 14px; color: #888;")
        self._matched_strategy_label.setWordWrap(True)
        matched_layout.addWidget(self._matched_strategy_label)

        main_layout.addWidget(matched_group)

        # === Strategy Table ===
        table_group = QGroupBox("📋 Verfügbare Strategien")
        table_layout = QVBoxLayout(table_group)

        self._strategy_table = QTableWidget()
        self._strategy_table.setColumnCount(7)
        self._strategy_table.setHorizontalHeaderLabels([
            "MatchScore", "Name", "Typ", "Indikatoren", "Entry Conditions", "Exit Conditions", "Aktiv"
        ])

        # Column widths
        header = self._strategy_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Score
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Typ
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Indikatoren
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Entry
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Exit
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Aktiv

        self._strategy_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._strategy_table.setAlternatingRowColors(True)
        self._strategy_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #2a2a2a; }"
        )
        self._strategy_table.itemDoubleClicked.connect(self._show_score_details)

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

        self._regime_detector_btn = QPushButton("📊 Regime Detector")
        self._regime_detector_btn.setStyleSheet("background-color: #ff9800; font-weight: bold;")
        self._regime_detector_btn.setToolTip(
            "Regimedetektor auf dem gesamten Chart ausführen\n"
            "und vertikale Linien an Regimewechsel-Punkten einzeichnen"
        )
        self._regime_detector_btn.clicked.connect(self._on_run_regime_detector)
        button_layout.addWidget(self._regime_detector_btn)

        self._analyze_btn = QPushButton("🔍 Analyze Current Market")
        self._analyze_btn.setStyleSheet("background-color: #2196f3; font-weight: bold;")
        self._analyze_btn.setToolTip("Analyze current market regime and match strategy")
        self._analyze_btn.clicked.connect(self._analyze_current_market)
        button_layout.addWidget(self._analyze_btn)

        self._calc_score_btn = QPushButton("🏆 Calculate Scores")
        self._calc_score_btn.setStyleSheet("background-color: #9C27B0; font-weight: bold;")
        self._calc_score_btn.setToolTip("Calculate match score for all strategies")
        self._calc_score_btn.clicked.connect(self._calculate_all_scores)
        button_layout.addWidget(self._calc_score_btn)

        self._validate_json_btn = QPushButton("✅ Validate JSON")
        self._validate_json_btn.setStyleSheet("background-color: #00BCD4; font-weight: bold;")
        self._validate_json_btn.setToolTip("Validate all JSON files against schemas (no scoring)")
        self._validate_json_btn.clicked.connect(self._validate_all_json)
        button_layout.addWidget(self._validate_json_btn)

        self._select_all_btn = QPushButton("✅ Alle auswählen")
        self._select_all_btn.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
        self._select_all_btn.setToolTip("Alle Strategien in der 'Aktiv' Spalte auswählen")
        self._select_all_btn.clicked.connect(self._select_all_active)
        button_layout.addWidget(self._select_all_btn)

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
        self.strategy_load_errors.clear()
        self._strategy_table.setRowCount(0)

        # Ensure directory exists
        JSON_DIR.mkdir(parents=True, exist_ok=True)

        # Load all JSON files
        json_files = list(JSON_DIR.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON strategy files in {JSON_DIR}")

        for json_file in sorted(json_files):
            strategy_id = json_file.stem
            try:
                pipeline_cfg = self._pipeline.load_validate(json_file)
                config = pipeline_cfg.raw
                self.strategies[strategy_id] = config
                self._add_strategy_to_table(strategy_id, config, error=None)
            except Exception as e:
                logger.error(f"Failed to load {json_file.name}: {e}")
                self.strategy_load_errors[strategy_id] = str(e)
                self._add_strategy_to_table(strategy_id, {}, error=str(e))

        logger.info(f"Loaded {len(self.strategies)} strategies")

        # Update indicator set
        self._update_indicator_set()

    def _add_strategy_to_table(self, strategy_id: str, config: dict, error: str | None = None) -> None:
        """Add strategy to table."""
        row = self._strategy_table.rowCount()
        self._strategy_table.insertRow(row)

        # Extract strategy info (first strategy in config)
        strategy = config.get("strategies", [{}])[0] if config else {}
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
        indicators = config.get("indicators", []) if config else []
        indicator_count = len(indicators) if indicators else 0

        # Count conditions
        entry_all = strategy.get("entry", {}).get("all", []) if strategy else []
        entry_any = strategy.get("entry", {}).get("any", []) if strategy else []
        entry_count = len(entry_all) + len(entry_any)

        exit_all = strategy.get("exit", {}).get("all", []) if strategy else []
        exit_any = strategy.get("exit", {}).get("any", []) if strategy else []
        exit_count = len(exit_all) + len(exit_any)

        # Add cells - Score is first column (col 0), then name, typ, etc.
        # Score column: Display "--" initially, updated by market analysis
        score_item = QTableWidgetItem("--" if not error else "INVALID")
        score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if error:
            score_item.setToolTip(f"Schema invalid: {error}")
            score_item.setBackground(Qt.GlobalColor.darkRed)
            score_item.setForeground(Qt.GlobalColor.white)
        else:
            score_item.setToolTip("Schema valid")
        self._strategy_table.setItem(row, 0, score_item)
        self._strategy_table.setItem(row, 1, QTableWidgetItem(name))
        self._strategy_table.setItem(row, 2, QTableWidgetItem(strategy_type))
        self._strategy_table.setItem(row, 3, QTableWidgetItem(str(indicator_count)))
        self._strategy_table.setItem(row, 4, QTableWidgetItem(str(entry_count)))
        self._strategy_table.setItem(row, 5, QTableWidgetItem(str(exit_count)))

        # Active checkbox (now column 6)
        active_checkbox = QCheckBox()
        active_checkbox.setChecked(False)  # TODO: Load from bot state
        self._strategy_table.setCellWidget(row, 6, active_checkbox)

    def _select_all_active(self) -> None:
        """Select all checkboxes in the 'Aktiv' column."""
        row_count = self._strategy_table.rowCount()
        if row_count == 0:
            return

        for row in range(row_count):
            checkbox = self._strategy_table.cellWidget(row, 6)
            if checkbox and isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)

        logger.info(f"Selected all {row_count} strategies as active")

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
        name_item = self._strategy_table.item(row, 1)
        name = name_item.text() if name_item else ""

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
        """Update live regime display."""
        try:
            # Try to get regime from parent chart window
            parent = self.parent()
            if parent and hasattr(parent, 'get_current_regime'):
                regime = parent.get_current_regime()
                if regime:
                    self.set_current_regime(str(regime))
        except Exception as e:
            logger.debug(f"Could not update regime from parent: {e}")
            # Keep current regime display

    def _get_current_features(self, chart_window) -> Optional[dict]:
        """Get current feature vector from chart window.

        This method tries multiple approaches to retrieve features:
        1. Direct feature_engine on chart_window
        2. feature_engine on chart_widget
        3. Compute from OHLCV DataFrame using FeatureEngine

        Returns:
            FeatureVector or None if unavailable
        """
        try:
            # Helper to get symbol from chart window
            def get_symbol():
                if hasattr(chart_window, 'current_symbol'):
                    return chart_window.current_symbol
                if hasattr(chart_window, 'symbol'):
                    return chart_window.symbol
                if hasattr(chart_window, 'get_symbol'):
                    return chart_window.get_symbol()
                # Try chart_widget
                if hasattr(chart_window, 'chart_widget'):
                    cw = chart_window.chart_widget
                    if hasattr(cw, 'current_symbol'):
                        return cw.current_symbol
                    if hasattr(cw, 'symbol'):
                        return cw.symbol
                return "UNKNOWN"

            # Approach 1: Direct feature_engine on chart_window
            if hasattr(chart_window, 'feature_engine'):
                feature_engine = chart_window.feature_engine
                if hasattr(feature_engine, 'get_current_features'):
                    features = feature_engine.get_current_features()
                    if features:
                        logger.debug("Features from chart_window.feature_engine")
                        return features

            # Approach 2: feature_engine on chart_widget
            if hasattr(chart_window, 'chart_widget'):
                chart_widget = chart_window.chart_widget
                if hasattr(chart_widget, 'feature_engine'):
                    feature_engine = chart_widget.feature_engine
                    if hasattr(feature_engine, 'get_current_features'):
                        features = feature_engine.get_current_features()
                        if features:
                            logger.debug("Features from chart_widget.feature_engine")
                            return features

                # Approach 3: Get OHLCV DataFrame and compute features
                if hasattr(chart_widget, 'data') and chart_widget.data is not None:
                    df = chart_widget.data
                    if len(df) >= 50:  # Minimum bars for feature calculation
                        from src.core.tradingbot.feature_engine import FeatureEngine
                        feature_engine = FeatureEngine()
                        symbol = get_symbol()
                        features = feature_engine.calculate_features(df, symbol)
                        if features:
                            logger.debug("Features computed from OHLCV data")
                            return features

            # Approach 4: Try data attribute directly on chart_window
            if hasattr(chart_window, 'data') and chart_window.data is not None:
                df = chart_window.data
                if len(df) >= 50:
                    from src.core.tradingbot.feature_engine import FeatureEngine
                    feature_engine = FeatureEngine()
                    symbol = get_symbol()
                    features = feature_engine.calculate_features(df, symbol)
                    if features:
                        logger.debug("Features computed from chart_window.data")
                        return features

            logger.warning("Could not retrieve features from chart window")
            return None

        except Exception as e:
            logger.error(f"Failed to get features: {e}", exc_info=True)
            return None

    def _analyze_current_market(self) -> None:
        """Analyze current market and match strategy.

        This method:
        1. Gets current market data from parent chart
        2. Detects current regime using RegimeEngine
        3. Routes regime to matching strategy
        4. Displays matched strategy with conditions
        """
        try:
            # Get parent chart window
            parent = self.parent()
            if not parent:
                QMessageBox.warning(
                    self,
                    "No Chart Data",
                    "Cannot analyze market: No chart window found.\n"
                    "Please open this dialog from a chart window."
                )
                return
            chart_widget = self._get_chart_widget(parent)
            if chart_widget is None:
                QMessageBox.warning(
                    self,
                    "Kein Chart-Widget",
                    "Chart-Widget nicht gefunden.\n"
                    "Bitte stelle sicher, dass ein Chart geladen ist.",
                )
                return

            candles = self._get_chart_candles(chart_widget)
            if not candles or len(candles) < 50:
                QMessageBox.warning(
                    self,
                    "Zu wenige Daten",
                    f"Mindestens 50 Kerzen benötigt (aktuell: {len(candles) if candles else 0}).\n"
                    "Bitte lade mehr Chart-Daten.",
                )
                return

            # Entry evaluation uses feature context when available
            features = self._get_current_features(parent)

            # Get selected strategy from table
            selected_rows = self._strategy_table.selectedIndexes()
            if not selected_rows:
                QMessageBox.information(
                    self,
                    "Market Analysis",
                    "Bitte wähle eine Strategie aus der Tabelle, um den Markt zu analysieren."
                )
                return

            row = selected_rows[0].row()
            name_item = self._strategy_table.item(row, 1)
            if not name_item:
                QMessageBox.warning(
                    self,
                    "Strategy Not Found",
                    "Selected strategy row has no name."
                )
                return
            strategy_name = name_item.text()

            # Find strategy ID
            strategy_id = None
            for sid, config in self.strategies.items():
                strat = config.get("strategies", [{}])[0]
                if strat.get("name", sid) == strategy_name:
                    strategy_id = sid
                    break

            if not strategy_id:
                QMessageBox.warning(
                    self,
                    "Strategy Not Found",
                    f"Could not find strategy config for '{strategy_name}'"
                )
                return

            json_path = JSON_DIR / f"{strategy_id}.json"

            try:
                result = self._pipeline.run(
                    json_path,
                    candles,
                    features=features,
                    chart_window=parent,
                )
            except Exception as route_error:
                logger.error(f"Routing error: {route_error}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Analysis Error",
                    f"Failed to analyze market:\n\n{str(route_error)}"
                )
                return

            regime_id = result.regimes.selected_regime.regime_id if result.regimes.selected_regime else "UNKNOWN"
            self.set_current_regime(regime_id)

            matched_set = result.matched_sets[0] if result.matched_sets else None
            active_regimes = [r.regime_id for r in result.regimes.active_regimes]

            self._display_analysis_results(
                current_regime=regime_id,
                strategy_name=strategy_name,
                active_regimes=active_regimes,
                matched_set=matched_set,
                loaded_config=result.config.strategy_config
            )

        except Exception as e:
            logger.error(f"Market analysis failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Failed to analyze market:\n\n{str(e)}"
            )

    def _display_analysis_results(
        self,
        current_regime: str,
        strategy_name: str,
        active_regimes: list,
        matched_set: any,
        loaded_config: any
    ) -> None:
        """Display market analysis results in a detailed message box.

        Args:
            current_regime: Current regime string (e.g. "TREND_UP - NORMAL")
            strategy_name: Name of selected strategy
            active_regimes: List of active regime IDs
            matched_set: Matched StrategySet or None
            loaded_config: Loaded TradingBotConfig
        """
        # Build message
        message = "<h3>📊 Market Analysis Results</h3>"
        message += f"<p><b>Current Regime:</b> {current_regime}</p>"
        message += f"<p><b>Selected Strategy:</b> {strategy_name}</p>"

        if active_regimes:
            regime_names = [
                r.id if hasattr(r, "id") else str(r)
                for r in active_regimes
            ]
            message += f"<p><b>Active Regimes:</b> {', '.join(regime_names)}</p>"
        else:
            message += "<p><b>Active Regimes:</b> None</p>"

        if matched_set:
            message += "<hr><p><b style='color: #4CAF50;'>✓ Strategy Matched!</b></p>"
            message += f"<p><b>Matched Set:</b> {matched_set.strategy_set.name}</p>"

            # Show strategies in set
            if matched_set.strategy_set.strategies:
                message += "<p><b>Strategies in Set:</b></p><ul>"
                for strat_id in matched_set.strategy_set.strategies:
                    # Find strategy details
                    for strat in loaded_config.strategies:
                        if strat.id == strat_id:
                            message += f"<li>{strat.name or strat_id}</li>"
                            break
                message += "</ul>"

            # Show entry conditions (simplified)
            if loaded_config and loaded_config.strategies:
                strat = loaded_config.strategies[0]
                if hasattr(strat, 'entry_conditions'):
                    message += f"<p><b>Entry Conditions:</b> {type(strat.entry_conditions).__name__}</p>"
                if hasattr(strat, 'exit_conditions'):
                    message += f"<p><b>Exit Conditions:</b> {type(strat.exit_conditions).__name__}</p>"
        else:
            message += "<hr><p><b style='color: #f44336;'>⚠ No Strategy Matched</b></p>"
            message += "<p>The current market regime does not match the routing rules for this strategy.</p>"

        # Update matched strategy label in UI
        if matched_set:
            ui_text = f"✓ Matched: {matched_set.strategy_set.name}\n"
            ui_text += f"Regimes: {', '.join([r.id if hasattr(r, 'id') else str(r) for r in active_regimes])}"
            self._matched_strategy_label.setText(ui_text)
            self._matched_strategy_label.setStyleSheet("font-size: 14px; color: #4CAF50; font-weight: bold;")
        else:
            ui_text = f"⚠ No match for current regime: {current_regime}\n"
            ui_text += f"Active Regimes: {', '.join([r.id if hasattr(r, 'id') else str(r) for r in active_regimes]) if active_regimes else 'None'}"
            self._matched_strategy_label.setText(ui_text)
            self._matched_strategy_label.setStyleSheet("font-size: 14px; color: #ff9800;")

        # Show message
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Market Analysis Results")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def set_current_regime(self, regime: str) -> None:
        """Set current regime (called from Bot)."""
        self.current_regime = regime
        self._regime_label.setText(regime)
        self._update_indicator_set()

    def set_active_strategy_set(self, strategy_set_id: str) -> None:
        """Set active strategy set (called from Bot)."""
        self.active_strategy_set = strategy_set_id
        self._active_set_label.setText(strategy_set_id)

    def _validate_all_json(self) -> None:
        """Validate all JSON files against schemas without scoring.

        Shows detailed validation report with:
        - Valid files count
        - Invalid files with clickable errors
        - Copy-to-clipboard functionality
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QApplication
        from PyQt6.QtGui import QFont
        from src.core.tradingbot.config.validator import ValidationError

        json_files = list(JSON_DIR.glob("*.json"))
        valid_count = 0
        invalid_files = []

        for json_file in sorted(json_files):
            try:
                self._pipeline.load_validate(json_file)
                valid_count += 1
            except ValidationError as e:
                invalid_files.append({
                    "file": json_file.name,
                    "path": str(json_file),
                    "error": str(e),
                    "json_path": e.json_path if hasattr(e, 'json_path') else "",
                    "schema_rule": e.schema_rule if hasattr(e, 'schema_rule') else ""
                })
            except Exception as e:
                invalid_files.append({
                    "file": json_file.name,
                    "path": str(json_file),
                    "error": f"Unexpected error: {e}",
                    "json_path": "",
                    "schema_rule": ""
                })

        # Create validation report dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("JSON Schema Validation Report")
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Summary header
        summary_label = QLabel()
        summary_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        if invalid_files:
            summary_label.setText(
                f"❌ Validation Failed: {len(invalid_files)} errors, {valid_count} valid"
            )
            summary_label.setStyleSheet("color: #f44336; padding: 10px;")
        else:
            summary_label.setText(f"✅ All {valid_count} files are valid!")
            summary_label.setStyleSheet("color: #4CAF50; padding: 10px;")
        layout.addWidget(summary_label)

        # Error details text area
        report_text = QTextEdit()
        report_text.setReadOnly(True)
        report_text.setFont(QFont("Courier New", 10))

        report_lines = ["JSON Schema Validation Report", "=" * 80, ""]
        report_lines.append(f"Total Files: {len(json_files)}")
        report_lines.append(f"Valid: {valid_count}")
        report_lines.append(f"Invalid: {len(invalid_files)}")
        report_lines.append("")

        if invalid_files:
            report_lines.append("ERRORS:")
            report_lines.append("-" * 80)
            for idx, err in enumerate(invalid_files, 1):
                report_lines.append(f"\n{idx}. {err['file']}")
                report_lines.append(f"   Path: {err['path']}")
                if err['json_path']:
                    report_lines.append(f"   JSON Path: {err['json_path']}")
                if err['schema_rule']:
                    report_lines.append(f"   Schema Rule: {err['schema_rule']}")
                report_lines.append(f"   Error: {err['error']}")
                report_lines.append("")
        else:
            report_lines.append("✅ No errors found. All files conform to v2.1 schemas.")

        report_text.setPlainText("\n".join(report_lines))
        layout.addWidget(report_text)

        # Button layout
        btn_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy Report")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(report_text.toPlainText()))
        btn_layout.addWidget(copy_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        dialog.exec()

    def _show_score_details(self, item: QTableWidgetItem) -> None:
        """Show detailed score explainability panel for selected strategy.

        Displays:
        - Score breakdown (regime/entry/quality)
        - Regime match details
        - Entry evaluation reasons
        - Data quality penalties
        - Missing indicators
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout, QApplication
        from PyQt6.QtGui import QFont

        row = item.row()

        # Check if we have explain data for this row
        if row not in self._score_explain_by_row:
            QMessageBox.information(
                self,
                "No Score Data",
                "No score calculation data available for this strategy.\n\n"
                "Please run 'Calculate Scores' first."
            )
            return

        explain = self._score_explain_by_row[row]

        # Get strategy name
        name_item = self._strategy_table.item(row, 1)
        strategy_name = name_item.text() if name_item else "Unknown"

        # Create explainability dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Score Explainability: {strategy_name}")
        dialog.resize(850, 700)

        layout = QVBoxLayout(dialog)

        # Header with total score
        header_label = QLabel()
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        total_score = explain.get("total_score", 0)
        header_label.setText(f"🎯 Total Score: {total_score}/100")

        if total_score >= 80:
            color = "#4CAF50"  # Green
        elif total_score >= 50:
            color = "#FF9800"  # Orange
        else:
            color = "#f44336"  # Red

        header_label.setStyleSheet(f"color: {color}; padding: 10px;")
        layout.addWidget(header_label)

        # Detailed breakdown text area
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setFont(QFont("Courier New", 10))

        lines = ["SCORE BREAKDOWN", "=" * 80, ""]

        # Score components
        regime_score = explain.get("regime_match_score", 0)
        entry_score = explain.get("entry_signal_score", 0)
        quality_score = explain.get("data_quality_score", 0)

        lines.append(f"Regime Match Score:    {regime_score:3d}/60   {'✅' if regime_score > 0 else '❌'}")
        lines.append(f"Entry Signal Score:    {entry_score:3d}/30   {'✅' if entry_score > 0 else '❌'}")
        lines.append(f"Data Quality Score:    {quality_score:3d}/10")
        lines.append(f"{'-' * 40}")
        lines.append(f"Total Score:           {total_score:3d}/100")
        lines.append("")

        # Schema validation
        schema_info = explain.get("explain", {}).get("schema", {})
        lines.append("SCHEMA VALIDATION")
        lines.append("-" * 80)
        lines.append(f"Kind: {schema_info.get('kind', 'unknown')}")
        lines.append(f"Schema Version: {schema_info.get('schema_version', 'unknown')}")
        lines.append(f"Valid: {'✅ Yes' if schema_info.get('valid') else '❌ No'}")
        lines.append("")

        # Regime details
        regime_info = explain.get("explain", {}).get("regime", {})
        lines.append("REGIME DETECTION")
        lines.append("-" * 80)
        lines.append(f"Matched: {'✅ Yes' if regime_info.get('matched') else '❌ No'}")
        lines.append(f"Selected Regime: {regime_info.get('selected_regime', 'None')}")

        active_regimes = regime_info.get("active_regimes", [])
        if active_regimes:
            lines.append(f"Active Regimes: {', '.join(active_regimes)}")
        else:
            lines.append("Active Regimes: None")

        # Regime evaluations
        evaluations = regime_info.get("evaluations", [])
        if evaluations:
            lines.append("\nRegime Evaluations:")
            for eval_item in evaluations:
                regime_id = eval_item.get("regime_id", "unknown")
                passed = eval_item.get("passed", False)
                status = "✅ PASS" if passed else "❌ FAIL"
                lines.append(f"  • {regime_id}: {status}")

                details = eval_item.get("details", [])
                if details:
                    for detail in details[:3]:  # Show first 3 details
                        lines.append(f"      {detail}")

        # Routing info
        routing = regime_info.get("routing", {})
        matched_sets = routing.get("matched_sets", [])
        if matched_sets:
            lines.append(f"\nMatched Strategy Sets: {', '.join(matched_sets)}")

        lines.append("")

        # Entry evaluation
        entry_info = explain.get("explain", {}).get("entry", {})
        lines.append("ENTRY EVALUATION")
        lines.append("-" * 80)
        lines.append(f"Enabled: {'✅ Yes' if entry_info.get('enabled') else '❌ No'}")

        expression = entry_info.get("expression", "")
        if expression:
            lines.append(f"Expression: {expression[:60]}{'...' if len(expression) > 60 else ''}")
        else:
            lines.append("Expression: ❌ MISSING")

        lines.append(f"Result: {'✅ TRUE' if entry_info.get('result') else '❌ FALSE'}")
        lines.append(f"Long Signal: {'✅' if entry_info.get('long') else '❌'}")
        lines.append(f"Short Signal: {'✅' if entry_info.get('short') else '❌'}")

        reasons = entry_info.get("reasons", [])
        if reasons:
            lines.append("\nReasons:")
            for reason in reasons:
                lines.append(f"  • {reason}")

        errors = entry_info.get("errors", [])
        if errors:
            lines.append("\n⚠️ Errors:")
            for error in errors:
                lines.append(f"  • {error}")

        lines.append("")

        # Data quality
        quality_info = explain.get("explain", {}).get("data_quality", {})
        lines.append("DATA QUALITY")
        lines.append("-" * 80)
        lines.append(f"Candle Count: {quality_info.get('candle_count', 0)}")

        missing = quality_info.get("missing_indicators", [])
        if missing:
            lines.append(f"\n❌ Missing Indicators ({len(missing)}):")
            for ind in missing:
                lines.append(f"  • {ind}")

        nan_indicators = quality_info.get("nan_indicators", [])
        if nan_indicators:
            lines.append(f"\n⚠️ NaN Indicators ({len(nan_indicators)}):")
            for ind in nan_indicators:
                lines.append(f"  • {ind}")

        penalties = quality_info.get("penalties", [])
        if penalties:
            lines.append(f"\n📉 Penalties:")
            for penalty in penalties:
                lines.append(f"  • {penalty}")

        if not missing and not nan_indicators and not penalties:
            lines.append("✅ All indicators calculated successfully")

        details_text.setPlainText("\n".join(lines))
        layout.addWidget(details_text)

        # Button layout
        btn_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Copy Details")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(details_text.toPlainText()))
        btn_layout.addWidget(copy_btn)

        export_btn = QPushButton("💾 Export JSON")
        export_btn.clicked.connect(lambda: self._export_score_json(strategy_name, explain))
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        dialog.exec()

    def _export_score_json(self, strategy_name: str, explain: dict) -> None:
        """Export score explanation as JSON file."""
        import json
        from PyQt6.QtWidgets import QFileDialog

        default_filename = f"{strategy_name.replace(' ', '_')}_score_report.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Score Report",
            default_filename,
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(explain, f, indent=2, ensure_ascii=False)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Score report exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export score report:\n{e}"
                )

    def _calculate_all_scores(self) -> None:
        """Calculate scores for all strategies using background worker thread."""
        # Cancel existing worker if running
        if self._score_worker and self._score_worker.isRunning():
            self._score_worker.cancel()
            self._score_worker.wait()

        try:
            # Get parent and chart data
            parent = self.parent()
            if not parent:
                QMessageBox.warning(
                    self,
                    "No Chart",
                    "No chart window found. Please open this dialog from a chart window."
                )
                return

            chart_widget = self._get_chart_widget(parent)
            if not chart_widget:
                QMessageBox.warning(
                    self,
                    "No Chart Widget",
                    "Chart widget not found. Please ensure a chart is loaded."
                )
                return

            candles = self._get_chart_candles(chart_widget)
            if not candles or len(candles) < 50:
                QMessageBox.warning(
                    self,
                    "Insufficient Data",
                    f"At least 50 candles required (current: {len(candles) if candles else 0})."
                )
                return

            # Get features if available
            features = self._get_current_features(parent)

            # Build row -> strategy_id mapping
            row_mapping = {}
            for row in range(self._strategy_table.rowCount()):
                name_item = self._strategy_table.item(row, 1)
                if not name_item:
                    continue

                strategy_name = name_item.text()

                # Find strategy ID
                for sid, cfg in self.strategies.items():
                    strat = cfg.get("strategies", [{}])[0]
                    if strat.get("name", sid) == strategy_name:
                        row_mapping[row] = sid
                        break

            if not row_mapping:
                QMessageBox.information(
                    self,
                    "No Strategies",
                    "No strategies found to calculate scores for."
                )
                return

            # Clear previous scores
            self._score_explain_by_row.clear()

            # Create worker thread
            self._score_worker = ScoreCalculationWorker(
                pipeline=self._pipeline,
                strategies=self.strategies,
                candles=candles,
                features=features,
                chart_window=parent,
                json_dir=JSON_DIR,
                row_mapping=row_mapping
            )

            # Create progress dialog
            self._progress_dialog = QProgressDialog(
                "Calculating scores...",
                "Cancel",
                0,
                len(row_mapping),
                self
            )
            self._progress_dialog.setWindowTitle("Score Calculation")
            self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self._progress_dialog.setMinimumDuration(0)
            self._progress_dialog.setValue(0)

            # Connect signals
            self._score_worker.progress.connect(self._on_score_progress)
            self._score_worker.score_calculated.connect(self._on_score_result)
            self._score_worker.finished_all.connect(self._on_scores_finished)
            self._score_worker.error.connect(self._on_score_error)
            self._progress_dialog.canceled.connect(self._on_score_cancel)

            # Start worker
            self._score_worker.start()

        except Exception as e:
            logger.error(f"Calculate scores failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Calculation Failed",
                f"Failed to start score calculation:\n\n{e}"
            )

    def _on_score_progress(self, current: int, total: int, strategy_name: str) -> None:
        """Handle progress update from worker."""
        if self._progress_dialog:
            self._progress_dialog.setLabelText(f"Calculating: {strategy_name} ({current}/{total})")
            self._progress_dialog.setValue(current)

    def _on_score_result(self, row: int, score_data: dict) -> None:
        """Handle single score result from worker."""
        # Store explainability data
        self._score_explain_by_row[row] = score_data

        # Update table with score
        score_item = self._strategy_table.item(row, 0)
        if score_item:
            score = score_data["total_score"]
            score_item.setText(str(score))

            # Color code based on score
            if score >= 80:
                score_item.setBackground(QColor(76, 175, 80, 100))  # Green
            elif score >= 50:
                score_item.setBackground(QColor(255, 152, 0, 100))  # Orange
            else:
                score_item.setBackground(QColor(244, 67, 54, 100))  # Red

    def _on_scores_finished(self, success_count: int, error_count: int) -> None:
        """Handle completion of all score calculations."""
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        total = success_count + error_count
        message = f"Scores calculated for {success_count}/{total} strategies."

        if error_count > 0:
            message += f"\n\n⚠️ {error_count} strategies failed (check logs)."

        message += "\n\n💡 Double-click any row to see detailed score explanation."

        QMessageBox.information(
            self,
            "Scores Calculated",
            message
        )

    def _on_score_error(self, error_message: str) -> None:
        """Handle fatal error from worker."""
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        QMessageBox.critical(
            self,
            "Calculation Error",
            f"Score calculation encountered a fatal error:\n\n{error_message}"
        )

    def _on_score_cancel(self) -> None:
        """Handle user cancellation of score calculation."""
        if self._score_worker:
            self._score_worker.cancel()
            logger.info("User cancelled score calculation")

    def _on_run_regime_detector(self) -> None:
        """Run regime detector on full chart and draw vertical lines at regime changes."""
        try:
            # 1. Get chart widget via parent
            parent = self.parent()
            if not parent:
                QMessageBox.warning(
                    self,
                    "Kein Chart",
                    "Kein Chart-Fenster gefunden.\n"
                    "Bitte öffne diesen Dialog aus einem Chart-Fenster.",
                )
                return

            chart_widget = self._get_chart_widget(parent)
            if chart_widget is None:
                QMessageBox.warning(
                    self,
                    "Kein Chart-Widget",
                    "Chart-Widget nicht gefunden.\n"
                    "Bitte stelle sicher, dass ein Chart geladen ist.",
                )
                return

            # 2. Get chart data (DataFrame or candle list)
            candles = self._get_chart_candles(chart_widget)
            if not candles or len(candles) < 50:
                QMessageBox.warning(
                    self,
                    "Zu wenige Daten",
                    f"Mindestens 50 Kerzen benötigt (aktuell: {len(candles) if candles else 0}).\n"
                    "Bitte lade mehr Chart-Daten.",
                )
                return

            # 3. Require selected strategy config
            selected_rows = self._strategy_table.selectedIndexes()
            if not selected_rows:
                QMessageBox.warning(
                    self,
                    "Keine Auswahl",
                    "Bitte wähle eine Strategie für den Regime Detector aus.",
                )
                return

            row = selected_rows[0].row()
            name_item = self._strategy_table.item(row, 1)
            if not name_item:
                QMessageBox.warning(
                    self,
                    "Keine Auswahl",
                    "Ausgewählte Zeile enthält keinen Strategienamen.",
                )
                return

            strategy_name = name_item.text()
            strategy_id = None
            for sid, cfg in self.strategies.items():
                strat = cfg.get("strategies", [{}])[0]
                if strat.get("name", sid) == strategy_name:
                    strategy_id = sid
                    break

            if not strategy_id:
                QMessageBox.warning(
                    self,
                    "Strategie nicht gefunden",
                    f"Keine Konfiguration für '{strategy_name}' gefunden.",
                )
                return

            json_path = JSON_DIR / f"{strategy_id}.json"

            # 4. Run unified regime detection
            logger.info(f"Running regime detector on {len(candles)} candles...")
            config = self._pipeline.load_validate(json_path)
            regime_periods = self._pipeline.detect_regime_periods(candles, config)

            if not regime_periods:
                QMessageBox.information(
                    self,
                    "Keine Regimewechsel",
                    "Keine Regimewechsel im Chart erkannt.\n\n"
                    "Mögliche Gründe:\n"
                    "- Zu wenig Daten\n"
                    "- Regime-Config nicht geladen\n"
                    "- Alle Indikator-Werte ungültig",
                )
                return

            # 5. Emit signal for chart drawing
            self.draw_regime_lines_requested.emit(regime_periods)
            logger.info(f"Emitted {len(regime_periods)} regime lines to chart")

            # 6. Show results
            regime_summary = "\n".join(
                f"  • {r['regime']} ab {r['start_date']} {r['start_time']} "
                f"({r['duration_bars']} Bars)"
                for r in regime_periods[:10]
            )
            more = f"\n  ... und {len(regime_periods) - 10} weitere" if len(regime_periods) > 10 else ""

            QMessageBox.information(
                self,
                "Regime Detector - Ergebnis",
                f"✅ {len(regime_periods)} Regimewechsel erkannt!\n\n"
                f"Analysierte Kerzen: {len(candles)}\n\n"
                f"Erkannte Regimes:\n{regime_summary}{more}",
            )

        except Exception as e:
            logger.error(f"Regime detector failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Regime Detector Fehler",
                f"Regime-Erkennung fehlgeschlagen:\n\n{e}",
            )

    def _get_chart_candles(self, chart_widget) -> list[dict]:
        """Extract candle data from chart widget.

        Tries multiple approaches to get OHLCV data.

        Returns:
            List of candle dicts with timestamp, open, high, low, close, volume
        """
        # Approach 1: DataFrame 'data' attribute
        if hasattr(chart_widget, "data") and chart_widget.data is not None:
            df = chart_widget.data
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                # reset_index() preserves the index (often contains timestamps)
                return df.reset_index().to_dict("records")

        # Approach 2: Internal candle cache
        for attr in ("_candle_data", "_candles", "candle_data", "candles"):
            data = getattr(chart_widget, attr, None)
            if data and len(data) > 0:
                if isinstance(data, pd.DataFrame):
                    return data.reset_index().to_dict("records")
                elif isinstance(data, list):
                    return data

        # Approach 3: Bridge / JS data
        if hasattr(chart_widget, "_chart_bridge"):
            bridge = chart_widget._chart_bridge
            if hasattr(bridge, "get_candle_data"):
                data = bridge.get_candle_data()
                if data:
                    return data

        logger.warning("Could not retrieve candle data from chart widget")
        return []

    def _get_chart_widget(self, parent) -> object | None:
        """Resolve chart widget from parent window."""
        chart_widget = getattr(parent, "chart_widget", None)
        if chart_widget is None:
            for attr in ("chart_widget", "chart", "_chart_widget"):
                if hasattr(parent, attr):
                    chart_widget = getattr(parent, attr)
                    break
        return chart_widget

    def _get_selected_strategy_config(self) -> dict | None:
        """Get the v2 JSON config of the currently selected strategy.

        Returns:
            Strategy config dict or None if no strategy is selected.
        """
        selected_rows = self._strategy_table.selectedIndexes()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        name_item = self._strategy_table.item(row, 1)
        if not name_item:
            return None

        strategy_name = name_item.text()

        for sid, config in self.strategies.items():
            strat = config.get("strategies", [{}])[0]
            if strat.get("name", sid) == strategy_name:
                return config

        return None

    def _perform_regime_detection(
        self, candles: list[dict], strategy_config: dict | None = None
    ) -> list[dict]:
        """Perform candle-by-candle regime detection.

        Uses v2 JSON config from the selected strategy for indicator calculation
        and regime threshold evaluation.

        Args:
            candles: List of OHLCV candle dicts
            strategy_config: Optional v2 JSON strategy config with indicators/regimes

        Returns:
            List of regime period dicts with start_timestamp, regime, score, etc.
        """
        try:
            from src.core.indicators.types import IndicatorConfig, IndicatorType
            from src.core.tradingbot.regime_engine_json import RegimeEngineJSON
            _has_engine = True
        except ImportError as e:
            logger.warning(f"RegimeEngineJSON not available, using simple detection: {e}")
            _has_engine = False

        df = pd.DataFrame(candles)

        # Normalize timestamp column name
        if "timestamp" not in df.columns:
            for alt in ("time", "date", "datetime", "Time", "Timestamp", "index"):
                if alt in df.columns:
                    df["timestamp"] = df[alt]
                    break

        # If still no timestamp, try to use numeric index as timestamp
        if "timestamp" not in df.columns:
            if df.index.dtype in ("int64", "float64"):
                df["timestamp"] = df.index
            elif hasattr(df.index, "astype"):
                try:
                    # DatetimeIndex -> Unix timestamp
                    df["timestamp"] = df.index.astype("int64") // 10**9
                except Exception:
                    # Last resort: use sequential integers
                    df["timestamp"] = range(len(df))

        required = ["open", "high", "low", "close", "timestamp"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Fehlende Spalten: {missing}. Vorhandene: {list(df.columns)}")

        # Normalize timestamps to numeric Unix seconds
        sample_ts = df["timestamp"].iloc[0]
        if isinstance(sample_ts, (pd.Timestamp, datetime)):
            # pandas Timestamp or datetime -> Unix seconds
            df["timestamp"] = pd.to_datetime(df["timestamp"]).astype("int64") // 10**9
        elif isinstance(sample_ts, str):
            df["timestamp"] = pd.to_datetime(df["timestamp"]).astype("int64") // 10**9

        # --- Determine indicators and regimes from config ---
        indicators_v2 = []
        regimes_v2 = []

        if strategy_config:
            # Try optimization_results first (has regimes and indicators)
            opt_results = strategy_config.get("optimization_results", [])
            if opt_results:
                applied = [r for r in opt_results if r.get("applied", False)]
                opt = applied[-1] if applied else opt_results[0]
                indicators_v2 = opt.get("indicators", [])
                regimes_v2 = opt.get("regimes", [])

            # Fallback to top-level indicators/regimes
            if not indicators_v2:
                indicators_v2 = strategy_config.get("indicators", [])
            if not regimes_v2:
                regimes_v2 = strategy_config.get("regimes", [])

        # If no config or no regimes, use regime_detect.json
        if not regimes_v2:
            regime_detect_path = JSON_DIR / "regime_detect" / "regime_detect.json"
            if regime_detect_path.exists():
                try:
                    with open(regime_detect_path, "r", encoding="utf-8") as f:
                        rd = json.load(f)
                    indicators_v2 = rd.get("indicators", indicators_v2)
                    regimes_v2 = rd.get("regimes", regimes_v2)
                    logger.info(f"Loaded regime_detect.json: {len(regimes_v2)} regimes")
                except Exception as e:
                    logger.warning(f"Could not load regime_detect.json: {e}")

        if not regimes_v2 or not _has_engine:
            # Absolute fallback: use RegimeConfig-based simple detection
            return self._perform_simple_regime_detection(df)

        # --- Calculate all indicators ---
        engine = RegimeEngineJSON()
        indicator_values = {}

        for ind in indicators_v2:
            name = ind.get("name", ind.get("id", ""))
            ind_type = ind.get("type", "").upper()
            params = {p["name"]: p["value"] for p in ind.get("params", [])}

            try:
                ind_config = IndicatorConfig(
                    indicator_type=IndicatorType(ind_type.lower()),
                    params=params,
                    use_talib=False,
                    cache_results=True,
                )
                result = engine.indicator_engine.calculate(df, ind_config)
                indicator_values[name] = result.values
            except Exception as e:
                logger.debug(f"Indicator {name} ({ind_type}): {e}")
                indicator_values[name] = pd.Series([np.nan] * len(df))

        # ADX/DI components
        adx_period = 14
        for ind in indicators_v2:
            if ind.get("type", "").upper() == "ADX":
                for p in ind.get("params", []):
                    if p["name"] == "period":
                        adx_period = p["value"]
                        break
                break

        try:
            import pandas_ta as ta

            adx_df = ta.adx(df["high"], df["low"], df["close"], length=adx_period)
            if adx_df is not None and not adx_df.empty:
                di_plus_col = f"DMP_{adx_period}"
                di_minus_col = f"DMN_{adx_period}"
                if di_plus_col in adx_df.columns:
                    indicator_values["PLUS_DI"] = adx_df[di_plus_col]
                    indicator_values["MINUS_DI"] = adx_df[di_minus_col]
                    indicator_values["DI_DIFF"] = adx_df[di_plus_col] - adx_df[di_minus_col]
        except Exception as e:
            logger.debug(f"Could not calculate DI+/DI-: {e}")

        # Price change %
        indicator_values["PRICE_CHANGE_PCT"] = df["close"].pct_change() * 100

        # --- Threshold-to-indicator name mapping ---
        threshold_map = {
            "adx": "STRENGTH_ADX",
            "rsi": "MOMENTUM_RSI",
            "ema": "TREND_FILTER",
            "sma": "TREND_SMA",
            "bb": "VOLATILITY_BB",
            "atr": "VOLATILITY_ATR",
        }

        def get_ind_val(name: str, idx: int) -> float:
            if name not in indicator_values:
                return np.nan
            vals = indicator_values[name]
            if isinstance(vals, pd.DataFrame):
                return float(vals.iloc[idx, 0]) if idx < len(vals) else np.nan
            elif isinstance(vals, pd.Series):
                return float(vals.iloc[idx]) if idx < len(vals) else np.nan
            return np.nan

        def evaluate_regime(regime: dict, idx: int) -> bool:
            thresholds = regime.get("thresholds", [])
            regime_id = regime.get("id", "").upper()

            for thresh in thresholds:
                name = thresh["name"]
                value = thresh["value"]

                if name == "di_diff_min":
                    di_diff = get_ind_val("DI_DIFF", idx)
                    if np.isnan(di_diff):
                        return False
                    if "BULL" in regime_id:
                        if di_diff < value:
                            return False
                    elif "BEAR" in regime_id:
                        if di_diff > -value:
                            return False
                    else:
                        if abs(di_diff) < value:
                            return False
                    continue

                if name in ("rsi_strong_bull", "rsi_confirm_bull"):
                    rsi = get_ind_val("MOMENTUM_RSI", idx)
                    if np.isnan(rsi) or rsi < value:
                        return False
                    continue

                if name in ("rsi_strong_bear", "rsi_confirm_bear"):
                    rsi = get_ind_val("MOMENTUM_RSI", idx)
                    if np.isnan(rsi) or rsi > value:
                        return False
                    continue

                if name == "rsi_exhaustion_max":
                    rsi = get_ind_val("MOMENTUM_RSI", idx)
                    if np.isnan(rsi) or rsi > value:
                        return False
                    continue

                if name == "rsi_exhaustion_min":
                    rsi = get_ind_val("MOMENTUM_RSI", idx)
                    if np.isnan(rsi) or rsi < value:
                        return False
                    continue

                if name == "extreme_move_pct":
                    pct = get_ind_val("PRICE_CHANGE_PCT", idx)
                    if np.isnan(pct):
                        return False
                    if "BULL" in regime_id and pct < value:
                        return False
                    elif "BEAR" in regime_id and pct > -value:
                        return False
                    continue

                if name.endswith("_min"):
                    base = name[:-4]
                    ind_name = threshold_map.get(base.lower(), base.upper())
                    v = get_ind_val(ind_name, idx)
                    if np.isnan(v) or v < value:
                        return False
                elif name.endswith("_max"):
                    base = name[:-4]
                    ind_name = threshold_map.get(base.lower(), base.upper())
                    v = get_ind_val(ind_name, idx)
                    if np.isnan(v) or v >= value:
                        return False

            return True

        # --- Iterate candles ---
        min_candles = 50
        regime_periods = []
        current_regime = None

        sorted_regimes = sorted(regimes_v2, key=lambda r: r.get("priority", 0), reverse=True)
        fallback_id = sorted_regimes[-1]["id"] if sorted_regimes else "SIDEWAYS"

        for i in range(min_candles, len(df)):
            active_id = fallback_id
            for regime in sorted_regimes:
                if evaluate_regime(regime, i):
                    active_id = regime["id"]
                    break

            ts = df.iloc[i]["timestamp"]
            dt = datetime.fromtimestamp(ts / 1000 if ts > 1e10 else ts)

            if current_regime is None:
                current_regime = {
                    "regime": active_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }
            elif current_regime["regime"] != active_id:
                # Close previous regime
                current_regime["end_timestamp"] = ts
                current_regime["end_date"] = dt.strftime("%Y-%m-%d")
                current_regime["end_time"] = dt.strftime("%H:%M:%S")
                current_regime["end_bar_index"] = i
                current_regime["duration_bars"] = i - current_regime["start_bar_index"]
                dur_s = ts - current_regime["start_timestamp"]
                if current_regime["start_timestamp"] > 1e10:
                    dur_s /= 1000
                current_regime["duration_time"] = self._fmt_duration(dur_s)
                regime_periods.append(current_regime)

                current_regime = {
                    "regime": active_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }

        # Close final regime
        if current_regime is not None:
            last_ts = df.iloc[-1]["timestamp"]
            last_dt = datetime.fromtimestamp(last_ts / 1000 if last_ts > 1e10 else last_ts)
            current_regime["end_timestamp"] = last_ts
            current_regime["end_date"] = last_dt.strftime("%Y-%m-%d")
            current_regime["end_time"] = last_dt.strftime("%H:%M:%S")
            current_regime["end_bar_index"] = len(df)
            current_regime["duration_bars"] = len(df) - current_regime["start_bar_index"]
            dur_s = last_ts - current_regime["start_timestamp"]
            if current_regime["start_timestamp"] > 1e10:
                dur_s /= 1000
            current_regime["duration_time"] = self._fmt_duration(dur_s)
            regime_periods.append(current_regime)

        logger.info(f"Regime detection: {len(regime_periods)} periods from {len(df)} candles")
        return regime_periods

    def _perform_simple_regime_detection(self, df: pd.DataFrame) -> list[dict]:
        """Fallback regime detection using RegimeConfig thresholds.

        Used when no v2 JSON strategy config is available.
        """
        from src.core.trading_bot.regime_result import RegimeConfig

        config = RegimeConfig.find_and_load()
        regime_periods = []
        current_regime = None
        min_candles = 50

        # Dynamic parameters from JSON
        p_fast = config.parameters.get("fast_ema_period", 20)
        p_slow = config.parameters.get("slow_ema_period", 50)
        p_trend = config.parameters.get("trend_sma_period", 200)

        # Simple detection: EMA fast vs slow, SMA trend + ADX
        ema20 = df["close"].ewm(span=p_fast).mean()
        ema50 = df["close"].ewm(span=p_slow).mean()
        sma200 = df["close"].rolling(window=p_trend).mean()

        try:
            import pandas_ta as ta
            adx_df = ta.adx(df["high"], df["low"], df["close"], length=14)
            adx = adx_df["ADX_14"] if adx_df is not None else pd.Series([np.nan] * len(df))
        except Exception:
            adx = pd.Series([np.nan] * len(df))

        for i in range(min_candles, len(df)):
            # Determine regime
            e20 = ema20.iloc[i]
            e50 = ema50.iloc[i]
            s200 = sma200.iloc[i] if not np.isnan(sma200.iloc[i]) else e50  # Fallback to EMA50 if not enough data
            price = df["close"].iloc[i]

            adx_val = adx.iloc[i] if i < len(adx) else np.nan

            is_bull_crossover = e20 > e50
            is_above_sma200 = price > s200

            # Logic: Require SMA200 alignment for strong trends
            # Prevent "BULL" signals in deep bear markets (Bear Rallies -> SIDEWAYS)

            if not np.isnan(adx_val) and adx_val >= config.adx_strong_threshold:
                if is_bull_crossover and is_above_sma200:
                    active_id = "BULL_TREND"
                elif not is_bull_crossover and not is_above_sma200:
                    active_id = "BEAR_TREND"
                else:
                    # Conflicting signals (e.g. Rally in Bear or Pullback in Bull) -> SIDEWAYS
                    active_id = "SIDEWAYS"
            elif not np.isnan(adx_val) and adx_val < config.adx_chop_threshold:
                active_id = "CHOP_ZONE"
            else:
                # Moderate ADX (15-30)
                if is_bull_crossover and is_above_sma200:
                    active_id = "BULL"
                elif not is_bull_crossover and not is_above_sma200:
                    active_id = "BEAR"
                else:
                    active_id = "SIDEWAYS"

            ts = df.iloc[i]["timestamp"]
            dt = datetime.fromtimestamp(ts / 1000 if ts > 1e10 else ts)

            if current_regime is None:
                current_regime = {
                    "regime": active_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }
            elif current_regime["regime"] != active_id:
                current_regime["end_timestamp"] = ts
                current_regime["end_date"] = dt.strftime("%Y-%m-%d")
                current_regime["end_time"] = dt.strftime("%H:%M:%S")
                current_regime["end_bar_index"] = i
                current_regime["duration_bars"] = i - current_regime["start_bar_index"]
                dur_s = ts - current_regime["start_timestamp"]
                if current_regime["start_timestamp"] > 1e10:
                    dur_s /= 1000
                current_regime["duration_time"] = self._fmt_duration(dur_s)
                regime_periods.append(current_regime)

                current_regime = {
                    "regime": active_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }

        if current_regime is not None:
            last_ts = df.iloc[-1]["timestamp"]
            last_dt = datetime.fromtimestamp(last_ts / 1000 if last_ts > 1e10 else last_ts)
            current_regime["end_timestamp"] = last_ts
            current_regime["end_date"] = last_dt.strftime("%Y-%m-%d")
            current_regime["end_time"] = last_dt.strftime("%H:%M:%S")
            current_regime["end_bar_index"] = len(df)
            current_regime["duration_bars"] = len(df) - current_regime["start_bar_index"]
            dur_s = last_ts - current_regime["start_timestamp"]
            if current_regime["start_timestamp"] > 1e10:
                dur_s /= 1000
            current_regime["duration_time"] = self._fmt_duration(dur_s)
            regime_periods.append(current_regime)

        return regime_periods

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        try:
            seconds = float(seconds)
            if np.isnan(seconds) or seconds < 0:
                return "n/a"
        except (TypeError, ValueError):
            return "n/a"
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"

    def _calculate_all_scores(self) -> None:
        """Calculate score for all strategies based on current market."""
        try:
            parent = self.parent()
            if not parent:
                QMessageBox.warning(
                    self,
                    "No Chart Data",
                    "Cannot calculate scores: No chart window found.\n"
                    "Please open this dialog from a chart window."
                )
                return
            chart_widget = self._get_chart_widget(parent)
            if chart_widget is None:
                QMessageBox.warning(
                    self,
                    "Kein Chart-Widget",
                    "Chart-Widget nicht gefunden.\n"
                    "Bitte stelle sicher, dass ein Chart geladen ist.",
                )
                return

            candles = self._get_chart_candles(chart_widget)
            if not candles or len(candles) < 50:
                QMessageBox.warning(
                    self,
                    "Zu wenige Daten",
                    f"Mindestens 50 Kerzen benötigt (aktuell: {len(candles) if candles else 0}).\n"
                    "Bitte lade mehr Chart-Daten.",
                )
                return

            features = self._get_current_features(parent)

            updates = []
            self._score_explain_by_row.clear()

            logger.info(f"Calculating scores for {self._strategy_table.rowCount()} strategies...")

            for row in range(self._strategy_table.rowCount()):
                name_item = self._strategy_table.item(row, 1)
                if not name_item:
                    continue

                strategy_name = name_item.text()
                strategy_id = None
                for sid, cfg in self.strategies.items():
                    strat = cfg.get("strategies", [{}])[0]
                    if strat.get("name", sid) == strategy_name:
                        strategy_id = sid
                        break

                if not strategy_id:
                    continue

                json_path = JSON_DIR / f"{strategy_id}.json"
                try:
                    result = self._pipeline.run(
                        json_path,
                        candles,
                        features=features,
                        chart_window=parent,
                    )
                    score_value = result.score.total_score
                    self._score_explain_by_row[row] = result.score.explain
                except Exception as exc:
                    logger.error("Error scoring %s: %s", strategy_name, exc)
                    score_value = 0
                    self._score_explain_by_row[row] = {"error": str(exc)}

                updates.append((row, score_value))

            # Update UI
            self._strategy_table.setSortingEnabled(False)
            for row, score in updates:
                score_item = QTableWidgetItem()
                score_item.setData(Qt.ItemDataRole.DisplayRole, score)
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                explain = self._score_explain_by_row.get(row)
                if explain is not None:
                    score_item.setData(Qt.ItemDataRole.UserRole, explain)
                    score_item.setToolTip(json.dumps(explain, indent=2, ensure_ascii=False, default=str))

                if score >= 90:
                    score_item.setBackground(Qt.GlobalColor.darkGreen)
                    score_item.setForeground(Qt.GlobalColor.white)
                elif score >= 60:
                    score_item.setBackground(Qt.GlobalColor.darkYellow)
                    score_item.setForeground(Qt.GlobalColor.black)
                elif score >= 30:
                    score_item.setBackground(Qt.GlobalColor.darkRed)
                    score_item.setForeground(Qt.GlobalColor.white)

                self._strategy_table.setItem(row, 0, score_item)

            self._strategy_table.setSortingEnabled(True)
            logger.info("Score calculation complete.")

        except Exception as e:
            logger.error(f"Calculate all scores failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Calculation Error", f"Failed to calculate scores:\n{e}")
