"""Entry Analyzer - Backtest Configuration Mixin.

Extracted from entry_analyzer_backtest.py to keep files under 550 LOC.
Handles backtest setup, strategy loading, and execution:
- Backtest Configuration tab UI
- Strategy file selection
- Backtest execution with BacktestWorker
- Candle data conversion to DataFrame
- Regime set backtesting

Date: 2026-01-21
LOC: ~290
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Import icon provider (Issue #12)
from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestConfigMixin:
    """Backtest configuration and execution functionality.

    Provides setup UI, strategy loading, and backtest execution with:
    - Strategy file selection
    - Date range and capital inputs
    - Regime set selection
    - BacktestWorker thread management
    - Chart data conversion to DataFrame

    Attributes (defined in parent class):
        _bt_strategy_path_label: QLabel - Strategy file path display
        _bt_start_date: QDateEdit - Backtest start date
        _bt_end_date: QDateEdit - Backtest end date
        _bt_initial_capital: QDoubleSpinBox - Initial capital input
        _bt_regime_set_combo: QComboBox - Regime set selector
        _bt_run_btn: QPushButton - Run backtest button
        _bt_progress: QProgressBar - Progress indicator
        _bt_status_label: QLabel - Status text
        _backtest_worker: QThread | None - Background worker
        _candles: list[dict] - Chart candle data
        _symbol: str - Trading symbol
    """

    # Type hints for parent class attributes (Issue #21: Updated for Regime tab)
    _regime_start_day: QLabel  # Start day from chart
    _regime_end_day: QLabel  # End day from chart
    _regime_period_days: QLabel  # Period in days
    _regime_num_bars: QLabel  # Number of bars
    _detected_regimes_table: QWidget  # Detected regimes table (QTableWidget) - renamed to avoid mixin collision
    _regime_config_path_label: QLabel  # Regime config path display
    _regime_config_table: QWidget  # Regime config table (QTableWidget)
    _regime_config_load_btn: QPushButton  # Regime config load button
    _regime_config_path: Path | None  # Current config path
    _regime_config: object | None  # Loaded TradingBotConfig
    _candles: list[dict]  # Chart candle data
    _symbol: str  # Trading symbol
    _timeframe: str  # Chart timeframe

    def _setup_backtest_config_tab(self, tab: QWidget) -> None:
        """Setup Regime Analysis tab.

        Issue #21: Completely refactored from "Backtest Setup" to "Regime"
        - Removed: Load Strategy, Run Backtest, Regime Set Dropdown
        - Added: Chart data fields (Start/End Day, Period, Bars)
        - Added: Analyze Visible Range button
        - Added: Regime detection table with timestamps
        """
        layout = QVBoxLayout(tab)

        # Chart Data Information (Issue #21: New section)
        chart_info_group = QGroupBox("Chart Data Information")
        chart_info_layout = QFormLayout()

        # Start Day (read-only, filled from chart)
        self._regime_start_day = QLabel("Not loaded")
        self._regime_start_day.setStyleSheet("color: #888;")
        chart_info_layout.addRow("Start Day:", self._regime_start_day)

        # End Day (read-only, filled from chart)
        self._regime_end_day = QLabel("Not loaded")
        self._regime_end_day.setStyleSheet("color: #888;")
        chart_info_layout.addRow("End Day:", self._regime_end_day)

        # Period in Days (read-only, calculated)
        self._regime_period_days = QLabel("0 days")
        self._regime_period_days.setStyleSheet("color: #888;")
        chart_info_layout.addRow("Period (Days):", self._regime_period_days)

        # Number of Bars (read-only, from chart)
        self._regime_num_bars = QLabel("0 bars")
        self._regime_num_bars.setStyleSheet("color: #888;")
        chart_info_layout.addRow("Number of Bars:", self._regime_num_bars)

        chart_info_group.setLayout(chart_info_layout)
        layout.addWidget(chart_info_group)

        # Analyze Visible Range button (Issue #21: Replaces "Analyze Current Regime")
        analyze_range_btn = QPushButton(" Analyze Visible Range")
        analyze_range_btn.setIcon(get_icon("timeline"))  # Timeline icon for range analysis
        analyze_range_btn.setProperty("class", "success")  # Use theme success color
        analyze_range_btn.clicked.connect(self._on_analyze_visible_range_clicked)
        layout.addWidget(analyze_range_btn)

        # Regime Detection Results Table (Issue #21: COMPLETE - Shows START and END of each regime)
        results_group = QGroupBox("Detected Regimes (Periods)")
        results_layout = QVBoxLayout()

        from PyQt6.QtWidgets import QHeaderView, QTableWidget

        self._detected_regimes_table = QTableWidget()
        self._detected_regimes_table.setColumnCount(8)
        self._detected_regimes_table.setHorizontalHeaderLabels(
            [
                "Start Date",
                "Start Time",
                "End Date",
                "End Time",
                "Regime",
                "Score",
                "Duration (Bars)",
                "Duration (Time)",
            ]
        )
        self._detected_regimes_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._detected_regimes_table.setAlternatingRowColors(True)
        self._detected_regimes_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )  # Read-only
        self._detected_regimes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        results_layout.addWidget(self._detected_regimes_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Regime Config (JSON)
        config_group = QGroupBox("Regime Config (JSON)")
        config_layout = QVBoxLayout()

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Config Path:"))

        self._regime_config_path_label = QLabel("Not loaded")
        self._regime_config_path_label.setStyleSheet("color: #888;")
        path_layout.addWidget(self._regime_config_path_label, 1)

        self._regime_config_load_btn = QPushButton("Load Regime Config")
        self._regime_config_load_btn.clicked.connect(self._on_load_regime_config_clicked)
        path_layout.addWidget(self._regime_config_load_btn)

        config_layout.addLayout(path_layout)

        from PyQt6.QtWidgets import QHeaderView, QTableWidget

        self._regime_config_table = QTableWidget()
        self._regime_config_table.setColumnCount(6)
        self._regime_config_table.setHorizontalHeaderLabels([
            "Type", "ID", "Name/Indicator", "Priority", "Parameters", "Conditions"
        ])
        header = self._regime_config_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self._regime_config_table.setAlternatingRowColors(True)
        self._regime_config_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._regime_config_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Make table sortable
        self._regime_config_table.setSortingEnabled(True)

        config_layout.addWidget(self._regime_config_table)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Load default config (Entry Analyzer Regime)
        self._load_default_regime_config()

        layout.addStretch()

    def _default_regime_config_path(self) -> Path:
        """Default JSON config path for Entry Analyzer regime detection."""
        return Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")

    def _load_default_regime_config(self) -> None:
        """Load the default regime config from the Entry Analyzer directory."""
        default_path = self._default_regime_config_path()
        default_path.parent.mkdir(parents=True, exist_ok=True)
        if default_path.exists():
            self._load_regime_config(default_path, show_error=False)
        else:
            self._regime_config_path_label.setText(str(default_path))
            self._regime_config_path_label.setStyleSheet("color: #f59e0b;")

    def _on_load_regime_config_clicked(self) -> None:
        """Load regime config from JSON file and populate table."""
        base_dir = Path("03_JSON/Entry_Analyzer/Regime")
        base_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Regime Config", str(base_dir), "JSON Files (*.json)"
        )
        if not file_path:
            return

        self._load_regime_config(Path(file_path))

    def _load_regime_config(self, config_path: Path, show_error: bool = True) -> None:
        """Load regime config and update UI state.

        Supports both v1.0 (Trading Bot format) and v2.0 (Entry Analyzer format).
        """
        from src.core.tradingbot.config.regime_loader_v2 import (
            RegimeConfigLoaderV2,
            RegimeConfigLoadError,
        )

        loader = RegimeConfigLoaderV2()
        try:
            config = loader.load_config(config_path)
        except RegimeConfigLoadError as e:
            logger.error(f"Failed to load regime config: {e}")
            if show_error:
                QMessageBox.critical(
                    self, "Regime Config Error", f"Failed to load regime config:\n\n{e}"
                )
            return

        self._regime_config = config
        self._regime_config_path = config_path

        # Build path display with optimization score if available
        path_text = str(config_path)
        if "optimization_results" in config and config["optimization_results"]:
            applied = [r for r in config["optimization_results"] if r.get('applied', False)]
            result = applied[-1] if applied else config["optimization_results"][0]
            score = result.get('score', 0)
            path_text = f"{config_path.name}  |  Score: {score:.1f}"

        self._regime_config_path_label.setText(path_text)
        self._regime_config_path_label.setStyleSheet("color: #10b981;")
        self._populate_regime_config_table(config)

    def _populate_regime_config_table(self, config: dict) -> None:
        """Populate the regime config table with indicators and regimes.

        Supports v2.0 format with optimization_results[].indicators[] and regimes[].

        Enhanced table with 6 columns:
        - Type: "Indicator" or "Regime"
        - ID: Unique identifier (indicator name or regime id)
        - Name/Indicator: Indicator type or regime name
        - Priority: Regime priority (empty for indicators)
        - Parameters: Indicator/Regime parameters
        - Thresholds: Regime thresholds (empty for indicators)
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QTableWidgetItem

        def format_params_v2(params: list[dict]) -> tuple[str, str]:
            """Format v2.0 indicator parameters (array format)."""
            if not params:
                return "", ""
            # params is array of {name, value, range}
            parts = []
            for param in params:
                name = param.get("name", "?")
                value = param.get("value", "?")
                parts.append(f"{name}: {value}")

            text = ", ".join(parts)
            display = text if len(text) <= 80 else f"{text[:77]}..."
            return display, text

        def format_thresholds_v2(thresholds: list[dict]) -> tuple[str, str]:
            """Format v2.0 regime thresholds (array format)."""
            if not thresholds:
                return "", ""
            # thresholds is array of {name, value, range}
            parts = []
            for threshold in thresholds:
                name = threshold.get("name", "?")
                value = threshold.get("value", "?")
                parts.append(f"{name}: {value}")

            text = ", ".join(parts)
            display = text if len(text) <= 120 else f"{text[:117]}..."
            return display, text

        # Disable sorting while populating
        self._regime_config_table.setSortingEnabled(False)
        self._regime_config_table.setRowCount(0)

        # Get applied result from optimization_results (v2.0 format)
        indicators = []
        regimes = []

        if "optimization_results" in config and config["optimization_results"]:
            # Find the latest applied result, or use the first one
            applied = [r for r in config["optimization_results"] if r.get('applied', False)]
            result = applied[-1] if applied else config["optimization_results"][0]

            indicators = result.get('indicators', [])
            regimes = result.get('regimes', [])

        # Populate indicators
        for indicator in indicators:
            row = self._regime_config_table.rowCount()
            self._regime_config_table.insertRow(row)

            # Get params and format
            params = indicator.get('params', [])
            params_display, params_full = format_params_v2(params)

            # Type
            type_item = QTableWidgetItem("Indicator")
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 0, type_item)

            # ID (name in v2.0)
            indicator_name = indicator.get('name', '?')
            self._regime_config_table.setItem(row, 1, QTableWidgetItem(indicator_name))

            # Indicator Type
            indicator_type = indicator.get('type', '?')
            self._regime_config_table.setItem(row, 2, QTableWidgetItem(indicator_type))

            # Priority (empty for indicators)
            priority_item = QTableWidgetItem("")
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 3, priority_item)

            # Parameters
            params_item = QTableWidgetItem(params_display)
            params_item.setToolTip(params_full)
            self._regime_config_table.setItem(row, 4, params_item)

            # Thresholds (empty for indicators)
            self._regime_config_table.setItem(row, 5, QTableWidgetItem(""))

        # Populate regimes
        for regime in regimes:
            row = self._regime_config_table.rowCount()
            self._regime_config_table.insertRow(row)

            # Get thresholds and format
            thresholds = regime.get('thresholds', [])
            thresh_display, thresh_full = format_thresholds_v2(thresholds)

            # Type
            type_item = QTableWidgetItem("Regime")
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 0, type_item)

            # ID
            regime_id = regime.get('id', '?')
            id_item = QTableWidgetItem(regime_id)
            # Color code regime IDs
            if "BULL" in regime_id.upper():
                id_item.setForeground(Qt.GlobalColor.darkGreen)
            elif "BEAR" in regime_id.upper():
                id_item.setForeground(Qt.GlobalColor.darkRed)
            elif "SIDEWAYS" in regime_id.upper() or "CHOP" in regime_id.upper():
                id_item.setForeground(Qt.GlobalColor.darkYellow)
            self._regime_config_table.setItem(row, 1, id_item)

            # Name
            regime_name = regime.get('name', '?')
            self._regime_config_table.setItem(row, 2, QTableWidgetItem(regime_name))

            # Priority
            priority = regime.get('priority', 0)
            priority_item = QTableWidgetItem(str(priority))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 3, priority_item)

            # Parameters (empty for regimes)
            self._regime_config_table.setItem(row, 4, QTableWidgetItem(""))

            # Thresholds (v2.0 uses thresholds instead of conditions)
            thresh_item = QTableWidgetItem(thresh_display)
            thresh_item.setToolTip(thresh_full)
            self._regime_config_table.setItem(row, 5, thresh_item)

        # Re-enable sorting
        self._regime_config_table.setSortingEnabled(True)
        self._regime_config_table.resizeColumnsToContents()

    def _on_analyze_visible_range_clicked(self) -> None:
        """Analyze visible chart range for regime detection (Issue #21).

        Workflow:
        1. Read chart data (Start Day, End Day, Period, Bars)
        2. Perform incremental regime detection (candle-by-candle)
        3. Display vertical lines with regime labels in chart
        4. Populate results table with timestamps
        """
        if not self._candles or len(self._candles) < 50:
            QMessageBox.warning(
                self,
                "Insufficient Data",
                "Need at least 50 candles for regime analysis.\n" "Load more chart data first.",
            )
            return

        try:
            logger.info("Starting visible range regime analysis...")

            # Step 1: Extract chart data information
            from datetime import datetime

            start_timestamp = self._candles[0].get("timestamp") or self._candles[0].get("time")
            end_timestamp = self._candles[-1].get("timestamp") or self._candles[-1].get("time")
            num_bars = len(self._candles)

            # Convert timestamps to datetime
            start_dt = (
                datetime.fromtimestamp(start_timestamp / 1000)
                if start_timestamp > 1e10
                else datetime.fromtimestamp(start_timestamp)
            )
            end_dt = (
                datetime.fromtimestamp(end_timestamp / 1000)
                if end_timestamp > 1e10
                else datetime.fromtimestamp(end_timestamp)
            )
            period_days = (end_dt - start_dt).days

            # Update UI fields
            self._regime_start_day.setText(start_dt.strftime("%Y-%m-%d %H:%M"))
            self._regime_start_day.setStyleSheet("color: #10b981;")  # Green
            self._regime_end_day.setText(end_dt.strftime("%Y-%m-%d %H:%M"))
            self._regime_end_day.setStyleSheet("color: #10b981;")
            self._regime_period_days.setText(f"{period_days} days")
            self._regime_period_days.setStyleSheet("color: #10b981;")
            self._regime_num_bars.setText(f"{num_bars} bars")
            self._regime_num_bars.setStyleSheet("color: #10b981;")

            # Step 2: Incremental regime detection (candle-by-candle)
            logger.info("Performing incremental regime detection...")
            detected_regimes = self._perform_incremental_regime_detection()

            # Step 3: Update results table with COMPLETE regime periods (Start + End)
            logger.info(f"About to populate table with {len(detected_regimes)} regime periods")
            logger.info(f"Table widget: {self._detected_regimes_table}")
            logger.info(f"Table column count: {self._detected_regimes_table.columnCount()}")

            self._detected_regimes_table.setRowCount(0)  # Clear existing rows

            if not detected_regimes:
                logger.warning("No regime periods detected in the visible range")
                QMessageBox.warning(
                    self,
                    "No Regimes Detected",
                    "No regime changes were detected in the visible range.\n\n"
                    "Possible reasons:\n"
                    "- Not enough data (need at least 50 candles)\n"
                    "- Regime config is not loaded\n"
                    "- All indicator values are invalid (NaN)\n"
                    "- No regime conditions are met\n\n"
                    f"Candles available: {len(self._candles)}\n"
                    f"Regime config loaded: {'Yes' if self._regime_config else 'No'}"
                )
                return

            logger.info(f"Starting to populate {len(detected_regimes)} rows in table")

            from PyQt6.QtCore import Qt
            from PyQt6.QtWidgets import QTableWidgetItem

            for idx, regime_data in enumerate(detected_regimes):
                try:
                    row = self._detected_regimes_table.rowCount()
                    logger.debug(f"Inserting row {row} (index {idx}) for regime {regime_data.get('regime', 'UNKNOWN')}")
                    self._detected_regimes_table.insertRow(row)

                    # Start Date
                    start_date_item = QTableWidgetItem(regime_data["start_date"])
                    start_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 0, start_date_item)

                    # Start Time
                    start_time_item = QTableWidgetItem(regime_data["start_time"])
                    start_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 1, start_time_item)

                    # End Date
                    end_date_item = QTableWidgetItem(regime_data["end_date"])
                    end_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 2, end_date_item)

                    # End Time
                    end_time_item = QTableWidgetItem(regime_data["end_time"])
                    end_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 3, end_time_item)

                    # Regime
                    regime_item = QTableWidgetItem(regime_data["regime"])
                    regime_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 4, regime_item)

                    # Score
                    score_item = QTableWidgetItem(f"{regime_data['score']:.2f}")
                    score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 5, score_item)

                    # Duration (Bars)
                    duration_bars_item = QTableWidgetItem(str(regime_data["duration_bars"]))
                    duration_bars_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 6, duration_bars_item)

                    # Duration (Time)
                    duration_time_item = QTableWidgetItem(regime_data["duration_time"])
                    duration_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._detected_regimes_table.setItem(row, 7, duration_time_item)

                except Exception as row_error:
                    logger.error(f"Error populating row {idx} for regime {regime_data.get('regime', 'UNKNOWN')}: {row_error}", exc_info=True)
                    continue

            # Log table population completion
            final_row_count = self._detected_regimes_table.rowCount()
            logger.info(f"✓ Table population complete! Final row count: {final_row_count}")
            logger.info(f"  Expected: {len(detected_regimes)}, Actual: {final_row_count}")

            if final_row_count == 0:
                logger.error("⚠️ TABLE IS EMPTY after population attempt!")
                logger.error(f"  detected_regimes length: {len(detected_regimes)}")
                logger.error(f"  Table widget valid: {self._detected_regimes_table is not None}")

            # Step 4: Draw vertical lines in chart (Issue #21: Emit signal to chart)
            if hasattr(self, "draw_regime_lines_requested"):
                # Emit signal with regime data for chart visualization
                self.draw_regime_lines_requested.emit(detected_regimes)
                logger.info(f"Emitted signal to draw {len(detected_regimes)} regime lines in chart")

            logger.info(f"Detected {len(detected_regimes)} regime changes")
            QMessageBox.information(
                self,
                "Regime Analysis Complete",
                f"Successfully analyzed {num_bars} candles.\n"
                f"Detected {len(detected_regimes)} regime changes.\n"
                f"Period: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')} ({period_days} days)",
            )

        except Exception as e:
            logger.error(f"Regime analysis failed: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Analysis Error", f"Failed to analyze visible range:\n\n{str(e)}"
            )

    def _perform_incremental_regime_detection(self) -> list[dict]:
        """Perform regime detection on visible chart range (v2 JSON optimized).

        Evaluates v2.0 regime thresholds directly against calculated indicator values.
        No legacy model conversions - pure v2 format.

        Returns:
            List of regime periods with start, end, duration for each regime.
        """
        from datetime import datetime
        import pandas as pd
        import numpy as np

        from src.core.indicators.types import IndicatorConfig, IndicatorType
        from src.core.tradingbot.regime_engine_json import RegimeEngineJSON

        # ===== 1. Load and validate v2 config =====
        if self._regime_config is None:
            self._load_default_regime_config()
        
        config = self._regime_config
        if config is None:
            raise ValueError("Keine Regime-Config geladen. Bitte zuerst eine Config laden.")

        # Extract v2 data from optimization_results
        if "optimization_results" not in config or not config["optimization_results"]:
            raise ValueError("Config hat kein 'optimization_results' - kein v2 Format?")

        applied = [r for r in config["optimization_results"] if r.get('applied', False)]
        opt_result = applied[-1] if applied else config["optimization_results"][0]

        indicators_v2 = opt_result.get('indicators', [])
        regimes_v2 = opt_result.get('regimes', [])

        if not indicators_v2 or not regimes_v2:
            raise ValueError(f"Config enthält keine Indikatoren oder Regimes: {len(indicators_v2)} indicators, {len(regimes_v2)} regimes")

        logger.info(f"V2 Config: {len(indicators_v2)} Indikatoren, {len(regimes_v2)} Regimes")

        # ===== 2. Build DataFrame =====
        df = pd.DataFrame(self._candles)
        if "timestamp" not in df.columns and "time" in df.columns:
            df["timestamp"] = df["time"]

        required = ["open", "high", "low", "close", "volume", "timestamp"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Fehlende Spalten: {missing}")

        # ===== 3. Calculate all indicators once =====
        engine = RegimeEngineJSON()
        indicator_values = {}  # name -> pd.Series or DataFrame

        for ind in indicators_v2:
            name = ind['name']
            ind_type = ind['type'].upper()
            params = {p['name']: p['value'] for p in ind.get('params', [])}

            try:
                ind_config = IndicatorConfig(
                    indicator_type=IndicatorType(ind_type.lower()),
                    params=params,
                    use_talib=False,
                    cache_results=True,
                )
                result = engine.indicator_engine.calculate(df, ind_config)
                indicator_values[name] = result.values
                logger.debug(f"Indikator {name} ({ind_type}) berechnet: {len(result.values)} Werte")
            except Exception as e:
                logger.error(f"Fehler bei Indikator {name}: {e}")
                indicator_values[name] = pd.Series([np.nan] * len(df))

        # ===== 3b. Calculate ADX/DI components for ADX/DI-based regime detection =====
        # Find ADX indicator config to get period
        adx_period = 14  # Default
        for ind in indicators_v2:
            if ind['type'].upper() == 'ADX':
                for p in ind.get('params', []):
                    if p['name'] == 'period':
                        adx_period = p['value']
                        break
                break

        try:
            import pandas_ta as ta
            # Calculate DI+ and DI-
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=adx_period)
            if adx_df is not None and not adx_df.empty:
                # pandas_ta returns columns like ADX_14, DMP_14, DMN_14
                di_plus_col = f'DMP_{adx_period}'
                di_minus_col = f'DMN_{adx_period}'
                if di_plus_col in adx_df.columns:
                    indicator_values['PLUS_DI'] = adx_df[di_plus_col]
                    indicator_values['MINUS_DI'] = adx_df[di_minus_col]
                    indicator_values['DI_DIFF'] = adx_df[di_plus_col] - adx_df[di_minus_col]
                    logger.debug(f"DI+/DI-/DI_DIFF berechnet mit Periode {adx_period}")
        except Exception as e:
            logger.warning(f"Could not calculate DI+/DI-: {e}")
            indicator_values['PLUS_DI'] = pd.Series([np.nan] * len(df))
            indicator_values['MINUS_DI'] = pd.Series([np.nan] * len(df))
            indicator_values['DI_DIFF'] = pd.Series([np.nan] * len(df))

        # ===== 3c. Calculate price change percentage for extreme move detection =====
        try:
            indicator_values['PRICE_CHANGE_PCT'] = df['close'].pct_change() * 100
            logger.debug("Price change percentage berechnet")
        except Exception as e:
            logger.warning(f"Could not calculate price change %: {e}")
            indicator_values['PRICE_CHANGE_PCT'] = pd.Series([np.nan] * len(df))

        # ===== 4. Build threshold evaluation functions =====
        def get_indicator_value(ind_name: str, idx: int) -> float:
            """Get indicator value at specific bar index."""
            if ind_name not in indicator_values:
                return np.nan
            vals = indicator_values[ind_name]
            if isinstance(vals, pd.DataFrame):
                # Multi-column indicator (e.g., BB) - use first numeric column
                return float(vals.iloc[idx, 0]) if idx < len(vals) else np.nan
            elif isinstance(vals, pd.Series):
                return float(vals.iloc[idx]) if idx < len(vals) else np.nan
            return np.nan

        def evaluate_regime_at(regime: dict, idx: int) -> bool:
            """Evaluate if regime conditions are met at bar index.

            Supports ADX/DI-based thresholds:
            - adx_min: ADX >= value (trend strength)
            - adx_max: ADX < value (weak trend)
            - di_diff_min: (DI+ - DI-) > value (for BULL) or (DI- - DI+) > value (for BEAR)
            - rsi_strong_bull: RSI > value (bullish momentum confirmation)
            - rsi_strong_bear: RSI < value (bearish momentum confirmation)
            - rsi_confirm_bull: RSI > value (confirms STRONG_BULL with momentum)
            - rsi_confirm_bear: RSI < value (confirms STRONG_BEAR with momentum)
            - rsi_exhaustion_max: RSI < value (BULL losing momentum = reversal warning)
            - rsi_exhaustion_min: RSI > value (BEAR losing momentum = reversal warning)
            - extreme_move_pct: |price_change| >= value (extreme price moves)
            """
            thresholds = regime.get('thresholds', [])
            regime_id = regime.get('id', '').upper()

            for thresh in thresholds:
                name = thresh['name']
                value = thresh['value']

                # ===== ADX/DI-based threshold handling =====

                # DI difference threshold (direction confirmation)
                if name == 'di_diff_min':
                    di_diff = get_indicator_value('DI_DIFF', idx)
                    if np.isnan(di_diff):
                        return False
                    # For TF/TREND_FOLLOWING: absolute DI diff >= threshold (either direction)
                    # For BULL: DI+ > DI- (positive diff)
                    # For BEAR: DI- > DI+ (negative diff)
                    if regime_id in ('TF', 'STRONG_TF') or 'TREND' in regime_id or 'FOLLOWING' in regime_id:
                        # Strong trend in either direction (direction-agnostic)
                        if abs(di_diff) < value:
                            return False
                    elif 'BULL' in regime_id:
                        if di_diff < value:  # DI+ - DI- must be > threshold
                            return False
                    elif 'BEAR' in regime_id:
                        if di_diff > -value:  # DI- - DI+ must be > threshold (diff < -threshold)
                            return False
                    else:
                        # Unknown regime type - check absolute value
                        if abs(di_diff) < value:
                            return False
                    continue

                # RSI strong bull threshold
                if name == 'rsi_strong_bull':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val < value:
                        return False
                    continue

                # RSI strong bear threshold
                if name == 'rsi_strong_bear':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val > value:
                        return False
                    continue

                # RSI confirmation for bullish momentum (STRONG_BULL)
                # RSI must be ABOVE threshold to confirm bullish momentum
                if name == 'rsi_confirm_bull':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val < value:
                        return False
                    continue

                # RSI confirmation for bearish momentum (STRONG_BEAR)
                # RSI must be BELOW threshold to confirm bearish momentum
                if name == 'rsi_confirm_bear':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val > value:
                        return False
                    continue

                # RSI exhaustion for bullish trend (BULL_EXHAUSTION)
                # Bullish trend but RSI BELOW threshold = losing momentum = potential reversal
                if name == 'rsi_exhaustion_max':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val > value:
                        return False
                    continue

                # RSI exhaustion for bearish trend (BEAR_EXHAUSTION)
                # Bearish trend but RSI ABOVE threshold = losing momentum = potential reversal
                if name == 'rsi_exhaustion_min':
                    rsi_val = get_indicator_value('MOMENTUM_RSI', idx)
                    if np.isnan(rsi_val) or rsi_val < value:
                        return False
                    continue

                # Extreme price move percentage
                if name == 'extreme_move_pct':
                    price_change = get_indicator_value('PRICE_CHANGE_PCT', idx)
                    if np.isnan(price_change):
                        return False
                    # For BULL: price_change >= value
                    # For BEAR: price_change <= -value
                    if 'BULL' in regime_id:
                        if price_change < value:
                            return False
                    elif 'BEAR' in regime_id:
                        if price_change > -value:
                            return False
                    continue

                # ===== Standard _min/_max threshold handling =====
                if name.endswith('_min'):
                    base = name[:-4]  # adx, rsi
                    ind_name = self._threshold_to_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val < value:
                        return False

                elif name.endswith('_max'):
                    base = name[:-4]
                    ind_name = self._threshold_to_indicator_name(base)
                    ind_val = get_indicator_value(ind_name, idx)
                    if np.isnan(ind_val) or ind_val >= value:
                        return False
                else:
                    # Unknown threshold - log but don't fail
                    logger.debug(f"Unbekanntes Threshold-Format: {name} (ignored)")

            return True  # All thresholds passed

        # ===== 5. Iterate through candles and detect regimes =====
        min_candles = 50  # Warmup for indicator calculation
        regime_periods = []
        current_regime = None

        # Sort regimes by priority (highest first)
        sorted_regimes = sorted(regimes_v2, key=lambda r: r.get('priority', 0), reverse=True)
        
        # Fallback to lowest priority regime (usually SIDEWAYS) instead of UNKNOWN
        fallback_regime_id = sorted_regimes[-1]['id'] if sorted_regimes else "SIDEWAYS"

        for i in range(min_candles, len(df)):
            # Find first matching regime (highest priority)
            active_regime_id = fallback_regime_id  # Use fallback instead of UNKNOWN
            for regime in sorted_regimes:
                if evaluate_regime_at(regime, i):
                    active_regime_id = regime['id']
                    break

            # Get timestamp for this bar
            ts = df.iloc[i]["timestamp"]
            dt = datetime.fromtimestamp(ts / 1000 if ts > 1e10 else ts)

            # Track regime changes
            if current_regime is None:
                # First regime
                current_regime = {
                    "regime": active_regime_id,
                    "score": 100.0,  # Simplified: 100 if active
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }
            elif current_regime["regime"] != active_regime_id:
                # Regime changed - close previous
                current_regime["end_timestamp"] = ts
                current_regime["end_date"] = dt.strftime("%Y-%m-%d")
                current_regime["end_time"] = dt.strftime("%H:%M:%S")
                current_regime["end_bar_index"] = i
                current_regime["duration_bars"] = i - current_regime["start_bar_index"]
                
                duration_s = (ts - current_regime["start_timestamp"])
                if current_regime["start_timestamp"] > 1e10:
                    duration_s /= 1000
                current_regime["duration_time"] = self._format_duration(duration_s)
                
                regime_periods.append(current_regime)
                
                # Start new
                current_regime = {
                    "regime": active_regime_id,
                    "score": 100.0,
                    "start_timestamp": ts,
                    "start_date": dt.strftime("%Y-%m-%d"),
                    "start_time": dt.strftime("%H:%M:%S"),
                    "start_bar_index": i,
                }

        # ===== 6. Close final regime =====
        if current_regime is not None:
            last_ts = df.iloc[-1]["timestamp"]
            last_dt = datetime.fromtimestamp(last_ts / 1000 if last_ts > 1e10 else last_ts)
            
            current_regime["end_timestamp"] = last_ts
            current_regime["end_date"] = last_dt.strftime("%Y-%m-%d")
            current_regime["end_time"] = last_dt.strftime("%H:%M:%S")
            current_regime["end_bar_index"] = len(df)
            current_regime["duration_bars"] = len(df) - current_regime["start_bar_index"]
            
            duration_s = (last_ts - current_regime["start_timestamp"])
            if current_regime["start_timestamp"] > 1e10:
                duration_s /= 1000
            current_regime["duration_time"] = self._format_duration(duration_s)
            
            regime_periods.append(current_regime)

        logger.info(f"Regime-Erkennung abgeschlossen: {len(regime_periods)} Perioden aus {len(df)} Kerzen")
        return regime_periods

    def _threshold_to_indicator_name(self, base: str) -> str:
        """Map threshold base name to indicator name from v2 config.
        
        Args:
            base: Threshold base name like 'adx', 'rsi'
            
        Returns:
            Indicator name from config like 'STRENGTH_ADX', 'MOMENTUM_RSI'
        """
        # Standard mappings based on common v2 naming conventions
        mappings = {
            'adx': 'STRENGTH_ADX',
            'rsi': 'MOMENTUM_RSI',
            'ema': 'TREND_FILTER',
            'sma': 'TREND_SMA',
            'bb': 'VOLATILITY_BB',
            'atr': 'VOLATILITY_ATR',
        }
        return mappings.get(base.lower(), base.upper())

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string like "2h 15m" or "45m" or "30s"
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            if minutes > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{hours}h"

    # Issue #21: Removed old methods (_on_load_strategy_clicked, _on_run_backtest_clicked)
    # These are no longer needed in the Regime tab

    def _on_run_backtest_clicked(self) -> None:
        """Handle run backtest button click.

        Original: entry_analyzer_backtest.py:491-533

        Starts backtest execution with BacktestWorker:
        - Validates strategy file loaded
        - Gets parameters from UI (symbol, dates, capital)
        - Converts chart candles to DataFrame if available
        - Creates BacktestWorker thread
        - Connects finished/error/progress signals
        - Starts background backtest
        """
        strategy_path = self._bt_strategy_path_label.text()
        if strategy_path == "No strategy loaded":
            QMessageBox.warning(self, "No Strategy", "Please load a strategy first")
            return

        # Get parameters
        symbol = self._symbol or "BTC/USD"
        start_date = self._bt_start_date.date().toPyDate()
        end_date = self._bt_end_date.date().toPyDate()
        initial_capital = self._bt_initial_capital.value()

        # Disable button and show progress
        self._bt_run_btn.setEnabled(False)
        self._bt_status_label.setText("Running backtest...")

        # Convert chart candles to DataFrame if available
        chart_df = None
        data_timeframe = None
        if self._candles:
            chart_df = self._convert_candles_to_dataframe(self._candles)
            data_timeframe = self._timeframe

        # Create worker
        from .entry_analyzer_workers import BacktestWorker

        self._backtest_worker = BacktestWorker(
            config_path=strategy_path,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            chart_data=chart_df,
            data_timeframe=data_timeframe,
            parent=self,
        )
        self._backtest_worker.finished.connect(self._on_backtest_finished)
        self._backtest_worker.error.connect(self._on_backtest_error)
        self._backtest_worker.progress.connect(lambda msg: self._bt_status_label.setText(msg))
        self._backtest_worker.start()

    def _convert_candles_to_dataframe(self, candles: list[dict]) -> pd.DataFrame:
        """Convert chart candles to DataFrame for backtest.

        Original: entry_analyzer_backtest.py:534-578

        Args:
            candles: List of candle dictionaries with OHLCV data

        Returns:
            DataFrame with timestamp index and OHLCV columns
        """
        df = pd.DataFrame(candles)

        # Ensure timestamp column exists
        if "timestamp" not in df.columns and "time" in df.columns:
            df["timestamp"] = df["time"]

        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)

        # Validate required columns
        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            logger.warning(f"Missing columns in candle data: {missing_cols}")

        return df

    def _backtest_regime_set(self, config_path: Path) -> None:
        """Run backtest on regime set configuration.

        Original: entry_analyzer_backtest.py:1126-1188

        Args:
            config_path: Path to regime set JSON config
        """
        logger.info(f"Starting regime set backtest: {config_path}")

        try:
            # Load config
            from src.core.tradingbot.config.loader import ConfigLoader

            loader = ConfigLoader()
            config = loader.load_config(str(config_path))

            # Get parameters from UI
            symbol = self._symbol or "BTC/USD"
            start_date = self._bt_start_date.date().toPyDate()
            end_date = self._bt_end_date.date().toPyDate()
            capital = self._bt_initial_capital.value()

            # Show progress
            self._bt_run_btn.setEnabled(False)
            QMessageBox.information(
                self,
                "Backtest Started",
                f"Running backtest on regime set...\n" f"This may take a few moments.",
            )

            # Run backtest
            from src.backtesting.engine import BacktestEngine

            engine = BacktestEngine()
            results = engine.run(
                config=config,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=capital,
            )

            # Display results summary
            self._show_backtest_summary(results, f"Regime Set: {config_path.stem}")

            self._bt_run_btn.setEnabled(True)

            logger.info(f"Regime set backtest completed")

        except Exception as e:
            logger.error(f"Regime set backtest failed: {e}", exc_info=True)
            self._bt_run_btn.setEnabled(True)

            QMessageBox.critical(
                self, "Backtest Error", f"Failed to backtest regime set:\n\n{str(e)}"
            )

    def _on_backtest_finished(self, results: dict) -> None:
        """Handle backtest completion (summary only)."""
        self._backtest_result = results
        self._bt_run_btn.setEnabled(True)
        self._bt_status_label.setText("Backtest complete")
        self._show_backtest_summary(results, "Backtest Results")
        logger.info("Backtest completed (summary displayed)")

    def _on_backtest_error(self, error_msg: str) -> None:
        """Handle backtest error (summary only)."""
        self._bt_run_btn.setEnabled(True)
        self._bt_status_label.setText("Error")
        QMessageBox.critical(self, "Backtest Error", f"Failed to run backtest:\n\n{error_msg}")
        logger.error(f"Backtest error: {error_msg}")

    def _show_backtest_summary(self, results: dict, title: str) -> None:
        """Show a compact backtest summary dialog."""
        stats = results.get("statistics", {}) if isinstance(results, dict) else {}
        summary_lines = [
            title,
            "",
            f"Net Profit: ${stats.get('net_profit', 0):.2f}",
            f"Return: {stats.get('return_pct', 0):.2f}%",
            f"Win Rate: {stats.get('win_rate', 0):.2f}%",
            f"Profit Factor: {stats.get('profit_factor', 0):.2f}",
            f"Total Trades: {stats.get('total_trades', 0)}",
        ]
        QMessageBox.information(self, "Backtest Results", "\n".join(summary_lines))
