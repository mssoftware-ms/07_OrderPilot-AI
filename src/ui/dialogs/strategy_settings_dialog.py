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

        self._analyze_btn = QPushButton("🔍 Analyze Current Market")
        self._analyze_btn.setStyleSheet("background-color: #2196f3; font-weight: bold;")
        self._analyze_btn.setToolTip("Analyze current market regime and match strategy")
        self._analyze_btn.clicked.connect(self._analyze_current_market)
        button_layout.addWidget(self._analyze_btn)

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

            # Get current market data using robust feature retrieval
            features = self._get_current_features(parent)
            if not features:
                QMessageBox.warning(
                    self,
                    "No Market Data",
                    "Cannot analyze market: No feature data available.\n"
                    "Please wait for market data to load."
                )
                return

            # Detect current regime
            from src.core.tradingbot.regime_engine import RegimeEngine
            from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

            regime_engine = RegimeEngine()
            current_regime = regime_engine.classify(features)

            # Update regime display
            regime_str = f"{current_regime.regime.name} - {current_regime.volatility.name}"
            self.set_current_regime(regime_str)

            # Get selected strategy from table
            selected_rows = self._strategy_table.selectedIndexes()
            if not selected_rows:
                QMessageBox.information(
                    self,
                    "Market Analysis",
                    f"Current Market Regime: {regime_str}\n\n"
                    f"ADX: {current_regime.adx:.2f}\n"
                    f"ATR%: {current_regime.atr_pct:.2f}%\n"
                    f"Confidence: {current_regime.regime_confidence:.2%}\n\n"
                    "Select a strategy from the table to check if it matches this regime."
                )
                return

            # Get selected strategy config
            row = selected_rows[0].row()
            strategy_name = self._strategy_table.item(row, 0).text()

            # Find strategy ID
            strategy_id = None
            for sid, config in self.strategies.items():
                strat = config.get("strategies", [{}])[0]
                if strat.get("name", sid) == strategy_name:
                    strategy_id = sid
                    break

            if not strategy_id or strategy_id not in self.strategies:
                QMessageBox.warning(
                    self,
                    "Strategy Not Found",
                    f"Could not find strategy config for '{strategy_name}'"
                )
                return

            config = self.strategies[strategy_id]

            # Try to route regime to strategy
            try:
                from src.core.tradingbot.config.loader import ConfigLoader
                from src.core.tradingbot.config.detector import RegimeDetector
                from src.core.tradingbot.config.router import StrategyRouter

                # Load config properly
                loader = ConfigLoader()
                json_path = JSON_DIR / f"{strategy_id}.json"
                loaded_config = loader.load_config(str(json_path))

                # Calculate indicator values
                indicator_calc = IndicatorValueCalculator()
                indicator_values = indicator_calc.calculate_indicator_values(features)

                # Detect active regimes
                detector = RegimeDetector(loaded_config.regimes)
                active_regimes = detector.detect_active_regimes(indicator_values, scope='entry')

                # Route to strategy
                router = StrategyRouter(loaded_config.routing, loaded_config.strategy_sets)
                matched_set = router.route(active_regimes)

                # Display results
                self._display_analysis_results(
                    current_regime=regime_str,
                    strategy_name=strategy_name,
                    active_regimes=active_regimes,
                    matched_set=matched_set,
                    loaded_config=loaded_config
                )

            except Exception as route_error:
                logger.error(f"Routing error: {route_error}", exc_info=True)
                # Still show basic regime info
                QMessageBox.information(
                    self,
                    "Market Analysis",
                    f"Current Market Regime: {regime_str}\n\n"
                    f"ADX: {current_regime.adx:.2f}\n"
                    f"ATR%: {current_regime.atr_pct:.2f}%\n"
                    f"Confidence: {current_regime.regime_confidence:.2%}\n\n"
                    f"Selected Strategy: {strategy_name}\n\n"
                    f"Note: Could not perform regime routing:\n{str(route_error)}"
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
        message = f"<h3>📊 Market Analysis Results</h3>"
        message += f"<p><b>Current Regime:</b> {current_regime}</p>"
        message += f"<p><b>Selected Strategy:</b> {strategy_name}</p>"

        if active_regimes:
            regime_names = [r.id for r in active_regimes]
            message += f"<p><b>Active Regimes:</b> {', '.join(regime_names)}</p>"
        else:
            message += f"<p><b>Active Regimes:</b> None</p>"

        if matched_set:
            message += f"<hr><p><b style='color: #4CAF50;'>✓ Strategy Matched!</b></p>"
            message += f"<p><b>Matched Set:</b> {matched_set.strategy_set.name}</p>"

            # Show strategies in set
            if matched_set.strategy_set.strategies:
                message += f"<p><b>Strategies in Set:</b></p><ul>"
                for strat_id in matched_set.strategy_set.strategies:
                    # Find strategy details
                    for strat in loaded_config.strategies:
                        if strat.id == strat_id:
                            message += f"<li>{strat.name or strat_id}</li>"
                            break
                message += "</ul>"

            # Show entry conditions (simplified)
            if loaded_config.strategies:
                strat = loaded_config.strategies[0]
                if hasattr(strat, 'entry_conditions'):
                    message += f"<p><b>Entry Conditions:</b> {type(strat.entry_conditions).__name__}</p>"
                if hasattr(strat, 'exit_conditions'):
                    message += f"<p><b>Exit Conditions:</b> {type(strat.exit_conditions).__name__}</p>"
        else:
            message += f"<hr><p><b style='color: #f44336;'>⚠ No Strategy Matched</b></p>"
            message += f"<p>The current market regime does not match the routing rules for this strategy.</p>"

        # Update matched strategy label in UI
        if matched_set:
            ui_text = f"✓ Matched: {matched_set.strategy_set.name}\n"
            ui_text += f"Regimes: {', '.join([r.id for r in active_regimes])}"
            self._matched_strategy_label.setText(ui_text)
            self._matched_strategy_label.setStyleSheet("font-size: 14px; color: #4CAF50; font-weight: bold;")
        else:
            ui_text = f"⚠ No match for current regime: {current_regime}\n"
            ui_text += f"Active Regimes: {', '.join([r.id for r in active_regimes]) if active_regimes else 'None'}"
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
