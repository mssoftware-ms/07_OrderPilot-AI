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
    _regime_results_table: QWidget  # Results table (QTableWidget)
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

        self._regime_results_table = QTableWidget()
        self._regime_results_table.setColumnCount(8)
        self._regime_results_table.setHorizontalHeaderLabels(
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
        self._regime_results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._regime_results_table.setAlternatingRowColors(True)
        self._regime_results_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )  # Read-only
        self._regime_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        results_layout.addWidget(self._regime_results_table)
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
        """Load regime config and update UI state."""
        from src.core.tradingbot.config.loader import ConfigLoader, ConfigLoadError

        loader = ConfigLoader()
        try:
            config = loader.load_config(config_path)
        except ConfigLoadError as e:
            logger.error(f"Failed to load regime config: {e}")
            if show_error:
                QMessageBox.critical(
                    self, "Regime Config Error", f"Failed to load regime config:\n\n{e}"
                )
            return

        self._regime_config = config
        self._regime_config_path = config_path
        self._regime_config_path_label.setText(str(config_path))
        self._regime_config_path_label.setStyleSheet("color: #10b981;")
        self._populate_regime_config_table(config)

    def _populate_regime_config_table(self, config) -> None:
        """Populate the regime config table with indicators and regimes.

        Enhanced table with 6 columns:
        - Type: "Indicator" or "Regime"
        - ID: Unique identifier
        - Name/Indicator: Display name or indicator type
        - Priority: Regime priority (empty for indicators)
        - Parameters: Indicator parameters (empty for regimes)
        - Conditions: Regime conditions (empty for indicators)
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QTableWidgetItem

        def format_params(params: dict) -> tuple[str, str]:
            """Format indicator parameters."""
            if not params:
                return "", ""
            # Create readable format: "period: 14, std_dev: 2.0"
            parts = [f"{k}: {v}" for k, v in params.items()]
            text = ", ".join(parts)
            display = text if len(text) <= 80 else f"{text[:77]}..."
            return display, text

        def format_conditions(conditions: dict) -> tuple[str, str]:
            """Format regime conditions in readable form."""
            if not conditions:
                return "", ""

            # Extract condition logic
            text_parts = []

            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    op = cond.get("op", "")
                    right = cond.get("right", {})

                    # Format: "indicator.field op value"
                    ind_id = left.get("indicator_id", "?")
                    field = left.get("field", "value")

                    if op == "gt":
                        op_str = ">"
                    elif op == "lt":
                        op_str = "<"
                    elif op == "eq":
                        op_str = "=="
                    elif op == "between":
                        min_val = right.get("min", "?")
                        max_val = right.get("max", "?")
                        text_parts.append(f"{ind_id}.{field} in [{min_val}, {max_val}]")
                        continue
                    else:
                        op_str = op

                    right_val = right.get("value", "?")
                    text_parts.append(f"{ind_id}.{field} {op_str} {right_val}")

            elif "any" in conditions:
                text_parts.append("OR: " + ", ".join([str(c) for c in conditions["any"]]))

            text = " AND ".join(text_parts)
            full_text = json.dumps(conditions, ensure_ascii=True, separators=(",", ":"))
            display = text if len(text) <= 120 else f"{text[:117]}..."

            return display, full_text

        # Disable sorting while populating
        self._regime_config_table.setSortingEnabled(False)
        self._regime_config_table.setRowCount(0)

        # Indicators
        for indicator in config.indicators:
            row = self._regime_config_table.rowCount()
            self._regime_config_table.insertRow(row)

            params_display, params_full = format_params(indicator.params)

            # Type
            type_item = QTableWidgetItem("Indicator")
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 0, type_item)

            # ID
            self._regime_config_table.setItem(row, 1, QTableWidgetItem(indicator.id))

            # Indicator Type
            indicator_type = (
                indicator.type.value if hasattr(indicator.type, "value") else str(indicator.type)
            )
            self._regime_config_table.setItem(row, 2, QTableWidgetItem(indicator_type))

            # Priority (empty for indicators)
            priority_item = QTableWidgetItem("")
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 3, priority_item)

            # Parameters
            params_item = QTableWidgetItem(params_display)
            params_item.setToolTip(params_full)
            self._regime_config_table.setItem(row, 4, params_item)

            # Conditions (empty for indicators)
            self._regime_config_table.setItem(row, 5, QTableWidgetItem(""))

        # Regimes
        for regime in config.regimes:
            row = self._regime_config_table.rowCount()
            self._regime_config_table.insertRow(row)

            conditions = regime.conditions.model_dump()
            cond_display, cond_full = format_conditions(conditions)

            # Type
            type_item = QTableWidgetItem("Regime")
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 0, type_item)

            # ID
            id_item = QTableWidgetItem(regime.id)
            # Color code regime IDs
            if "BULL" in regime.id:
                id_item.setForeground(Qt.GlobalColor.darkGreen)
            elif "BEAR" in regime.id:
                id_item.setForeground(Qt.GlobalColor.darkRed)
            elif "SIDEWAYS" in regime.id:
                id_item.setForeground(Qt.GlobalColor.darkYellow)
            self._regime_config_table.setItem(row, 1, id_item)

            # Name
            self._regime_config_table.setItem(row, 2, QTableWidgetItem(regime.name))

            # Priority
            priority_item = QTableWidgetItem(str(regime.priority))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_config_table.setItem(row, 3, priority_item)

            # Parameters (empty for regimes)
            self._regime_config_table.setItem(row, 4, QTableWidgetItem(""))

            # Conditions
            cond_item = QTableWidgetItem(cond_display)
            cond_item.setToolTip(cond_full)
            self._regime_config_table.setItem(row, 5, cond_item)

        # Re-enable sorting
        self._regime_config_table.setSortingEnabled(True)

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
            logger.info(f"Table widget: {self._regime_results_table}")
            logger.info(f"Table column count: {self._regime_results_table.columnCount()}")

            self._regime_results_table.setRowCount(0)  # Clear existing rows

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
                    row = self._regime_results_table.rowCount()
                    logger.debug(f"Inserting row {row} (index {idx}) for regime {regime_data.get('regime', 'UNKNOWN')}")
                    self._regime_results_table.insertRow(row)

                    # Start Date
                    start_date_item = QTableWidgetItem(regime_data["start_date"])
                start_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 0, start_date_item)

                # Start Time
                start_time_item = QTableWidgetItem(regime_data["start_time"])
                start_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 1, start_time_item)

                # End Date
                end_date_item = QTableWidgetItem(regime_data["end_date"])
                end_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 2, end_date_item)

                # End Time
                end_time_item = QTableWidgetItem(regime_data["end_time"])
                end_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 3, end_time_item)

                # Regime
                regime_item = QTableWidgetItem(regime_data["regime"])
                regime_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 4, regime_item)

                # Score
                score_item = QTableWidgetItem(f"{regime_data['score']:.2f}")
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 5, score_item)

                # Duration (Bars)
                duration_bars_item = QTableWidgetItem(str(regime_data["duration_bars"]))
                duration_bars_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 6, duration_bars_item)

                # Duration (Time)
                duration_time_item = QTableWidgetItem(regime_data["duration_time"])
                duration_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_results_table.setItem(row, 7, duration_time_item)

                except Exception as row_error:
                    logger.error(f"Error populating row {idx} for regime {regime_data.get('regime', 'UNKNOWN')}: {row_error}", exc_info=True)
                    continue

            # Log table population completion
            final_row_count = self._regime_results_table.rowCount()
            logger.info(f"✓ Table population complete! Final row count: {final_row_count}")
            logger.info(f"  Expected: {len(detected_regimes)}, Actual: {final_row_count}")

            if final_row_count == 0:
                logger.error("⚠️ TABLE IS EMPTY after population attempt!")
                logger.error(f"  detected_regimes length: {len(detected_regimes)}")
                logger.error(f"  Table widget valid: {self._regime_results_table is not None}")

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
        """Perform incremental regime detection candle-by-candle (Issue #21 COMPLETE).

        Returns:
            List of regime PERIODS with start, end, duration for each regime.
            Structure: {
                'start_date', 'start_time', 'end_date', 'end_time',
                'regime', 'score', 'duration_bars', 'duration_time',
                'start_timestamp', 'end_timestamp', 'start_bar_index', 'end_bar_index'
            }
        """
        from datetime import datetime

        import pandas as pd

        from src.core.indicators.types import IndicatorConfig, IndicatorType
        from src.core.tradingbot.config.detector import RegimeDetector
        from src.core.tradingbot.config.evaluator import ConditionEvaluationError
        from src.core.tradingbot.regime_engine_json import RegimeEngineJSON

        regime_periods = []  # List of complete regime periods
        current_regime = None  # Currently active regime
        min_candles = 50  # Minimum candles needed for regime detection

        # Load config (JSON-based)
        if self._regime_config is None:
            logger.info("Regime config not loaded, attempting to load default config...")
            self._load_default_regime_config()
        config = self._regime_config
        if config is None:
            logger.error("Failed to load regime config - cannot perform detection")
            raise ValueError(
                "Regime config is not loaded. Please load a regime config using 'Load Regime Config' button first."
            )

        logger.info(f"Using regime config with {len(config.indicators)} indicators and {len(config.regimes)} regimes")

        # Build DataFrame once
        df = pd.DataFrame(self._candles)

        # Ensure required columns
        if "timestamp" not in df.columns and "time" in df.columns:
            df["timestamp"] = df["time"]

        required_cols = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Pre-calculate indicator results for full range
        engine = RegimeEngineJSON()
        indicator_results = {}
        for ind_def in config.indicators:
            ind_config = IndicatorConfig(
                indicator_type=IndicatorType(ind_def.type.lower()),
                params=ind_def.params,
                use_talib=False,
                cache_results=True,
            )
            result = engine.indicator_engine.calculate(df, ind_config)
            indicator_results[ind_def.id] = result.values

        detector = RegimeDetector(config.regimes)

        def _safe_value(value) -> float:
            if pd.isna(value):
                return float("nan")
            return float(value)

        def _indicator_values_at(index: int) -> dict[str, dict[str, float]]:
            values: dict[str, dict[str, float]] = {}
            for ind_id, result in indicator_results.items():
                if isinstance(result, pd.Series):
                    val = result.iloc[index] if index < len(result) else float("nan")
                    values[ind_id] = {"value": _safe_value(val)}
                elif isinstance(result, pd.DataFrame):
                    values[ind_id] = {}
                    for col in result.columns:
                        val = result[col].iloc[index] if index < len(result) else float("nan")
                        values[ind_id][col] = _safe_value(val)
                    if "bandwidth" in values[ind_id]:
                        values[ind_id]["width"] = values[ind_id]["bandwidth"]
                elif isinstance(result, dict):
                    values[ind_id] = result
                else:
                    values[ind_id] = {"value": float("nan")}
            return values

        detector_logger = logging.getLogger("src.core.tradingbot.config.detector")
        prev_level = detector_logger.level
        detector_logger.setLevel(logging.WARNING)
        try:
            # Iterate through candles incrementally
            for i in range(min_candles - 1, len(df)):
                try:
                    indicator_values = _indicator_values_at(i)
                    active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")
                    regime_state = engine._convert_to_regime_state(
                        active_regimes=active_regimes,
                        indicator_values=indicator_values,
                        timestamp=datetime.utcnow(),
                    )
                except ConditionEvaluationError as e:
                    logger.debug(f"Skipping bar {i} due to condition evaluation error: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error calculating regimes at bar {i}: {e}")
                    continue

                # Determine regime label
                if active_regimes:
                    regime_label = active_regimes[0].id.upper()
                else:
                    regime_label = "UNKNOWN"

                # Score based on regime confidence
                score = max(0.0, min(100.0, regime_state.regime_confidence * 100))

                # Get timestamp
                timestamp = df.iloc[i]["timestamp"]
                dt = (
                    datetime.fromtimestamp(timestamp / 1000)
                    if timestamp > 1e10
                    else datetime.fromtimestamp(timestamp)
                )

                # Check if regime changed
                if current_regime is None:
                    # First regime detected - start new period
                    current_regime = {
                        "regime": regime_label,
                        "score": score,
                        "start_timestamp": timestamp,
                        "start_date": dt.strftime("%Y-%m-%d"),
                        "start_time": dt.strftime("%H:%M:%S"),
                        "start_bar_index": i,
                    }
                    logger.debug(
                        f"First regime started at bar {i}: {regime_label} (score: {score:.2f})"
                    )

                elif current_regime["regime"] != regime_label:
                    # Regime changed - close previous period and start new one
                    current_regime["end_timestamp"] = timestamp
                    current_regime["end_date"] = dt.strftime("%Y-%m-%d")
                    current_regime["end_time"] = dt.strftime("%H:%M:%S")
                    current_regime["end_bar_index"] = i

                    # Calculate duration
                    duration_bars = (
                        current_regime["end_bar_index"] - current_regime["start_bar_index"]
                    )
                    duration_seconds = (
                        (current_regime["end_timestamp"] - current_regime["start_timestamp"]) / 1000
                        if current_regime["end_timestamp"] > 1e10
                        else (current_regime["end_timestamp"] - current_regime["start_timestamp"])
                    )
                    duration_time = self._format_duration(duration_seconds)

                    current_regime["duration_bars"] = duration_bars
                    current_regime["duration_time"] = duration_time

                    # Add to periods list
                    regime_periods.append(current_regime)
                    logger.debug(
                        f"Regime ended at bar {i}: {current_regime['regime']} -> {regime_label} "
                        f"(duration: {duration_bars} bars, {duration_time})"
                    )

                    # Start new regime
                    current_regime = {
                        "regime": regime_label,
                        "score": score,
                        "start_timestamp": timestamp,
                        "start_date": dt.strftime("%Y-%m-%d"),
                        "start_time": dt.strftime("%H:%M:%S"),
                        "start_bar_index": i,
                    }
        finally:
            detector_logger.setLevel(prev_level)

        logger.info(f"Processed {len(df)} candles, detected {len(regime_periods)} regime changes so far")

        # Close the last regime with the final candle
        if current_regime is not None:
            last_candle = self._candles[-1]
            last_timestamp = last_candle.get("timestamp") or last_candle.get("time")
            last_dt = (
                datetime.fromtimestamp(last_timestamp / 1000)
                if last_timestamp > 1e10
                else datetime.fromtimestamp(last_timestamp)
            )

            current_regime["end_timestamp"] = last_timestamp
            current_regime["end_date"] = last_dt.strftime("%Y-%m-%d")
            current_regime["end_time"] = last_dt.strftime("%H:%M:%S")
            current_regime["end_bar_index"] = len(self._candles)

            # Calculate duration
            duration_bars = current_regime["end_bar_index"] - current_regime["start_bar_index"]
            duration_seconds = (
                (current_regime["end_timestamp"] - current_regime["start_timestamp"]) / 1000
                if current_regime["end_timestamp"] > 1e10
                else (current_regime["end_timestamp"] - current_regime["start_timestamp"])
            )
            duration_time = self._format_duration(duration_seconds)

            current_regime["duration_bars"] = duration_bars
            current_regime["duration_time"] = duration_time

            # Add final regime
            regime_periods.append(current_regime)
            logger.debug(
                f"Last regime closed at final candle: {current_regime['regime']} (duration: {duration_bars} bars, {duration_time})"
            )

        logger.info(
            f"Regime detection complete: {len(regime_periods)} regime periods detected "
            f"from {len(df)} candles (starting at candle {min_candles})"
        )
        if len(regime_periods) == 0:
            logger.warning(
                "No regime periods detected! This may indicate:\n"
                "  - All indicator values are NaN (check calculation)\n"
                "  - No regime conditions are met (check thresholds in config)\n"
                "  - Errors during detection (check logs above)"
            )

        return regime_periods

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
