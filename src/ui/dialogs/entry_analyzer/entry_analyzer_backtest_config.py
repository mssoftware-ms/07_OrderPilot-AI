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

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
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

if TYPE_CHECKING:
    from PyQt6.QtCore import QThread

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

    # Type hints for parent class attributes
    _bt_strategy_path_label: QLabel
    _bt_start_date: QDateEdit
    _bt_end_date: QDateEdit
    _bt_initial_capital: QDoubleSpinBox
    _bt_regime_set_combo: QComboBox
    _bt_run_btn: QPushButton
    _bt_progress: Any
    _bt_status_label: QLabel
    _backtest_worker: QThread | None
    _candles: list[dict]
    _symbol: str
    _timeframe: str

    def _setup_backtest_config_tab(self, tab: QWidget) -> None:
        """Setup Backtest Configuration tab.

        Original: entry_analyzer_backtest.py:112-193

        Creates:
        - Strategy selection section
        - Date range inputs
        - Capital input
        - Regime set selection
        - Run backtest button with progress bar
        """
        layout = QVBoxLayout(tab)

        # Strategy Selection
        strategy_group = QGroupBox("Strategy Configuration")
        strategy_layout = QFormLayout()

        # Strategy file path
        strategy_file_layout = QHBoxLayout()
        self._bt_strategy_path_label = QLabel("No strategy loaded")
        self._bt_strategy_path_label.setStyleSheet("color: #888;")
        strategy_file_layout.addWidget(self._bt_strategy_path_label, stretch=1)

        load_strategy_btn = QPushButton("📁 Load Strategy")
        load_strategy_btn.clicked.connect(self._on_load_strategy_clicked)
        strategy_file_layout.addWidget(load_strategy_btn)

        strategy_layout.addRow("Strategy File:", strategy_file_layout)

        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # Backtest Parameters
        params_group = QGroupBox("Backtest Parameters")
        params_layout = QFormLayout()

        # Date range
        self._bt_start_date = QDateEdit()
        self._bt_start_date.setCalendarPopup(True)
        self._bt_start_date.setDate(QDate.currentDate().addDays(-30))
        params_layout.addRow("Start Date:", self._bt_start_date)

        self._bt_end_date = QDateEdit()
        self._bt_end_date.setCalendarPopup(True)
        self._bt_end_date.setDate(QDate.currentDate())
        params_layout.addRow("End Date:", self._bt_end_date)

        # Initial capital
        self._bt_initial_capital = QDoubleSpinBox()
        self._bt_initial_capital.setRange(100, 1000000)
        self._bt_initial_capital.setValue(10000)
        self._bt_initial_capital.setPrefix("$")
        self._bt_initial_capital.setSingleStep(1000)
        params_layout.addRow("Initial Capital:", self._bt_initial_capital)

        # Regime set selection
        self._bt_regime_set_combo = QComboBox()
        self._bt_regime_set_combo.addItem("None - Use Default Strategy")
        # TODO: Populate with available regime sets
        params_layout.addRow("Regime Set:", self._bt_regime_set_combo)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Analyze Current Regime button
        analyze_regime_btn = QPushButton("🔍 Analyze Current Regime")
        analyze_regime_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #10b981; color: white;"
        )
        analyze_regime_btn.clicked.connect(self._on_analyze_current_regime_clicked)
        layout.addWidget(analyze_regime_btn)

        # Run button
        action_layout = QHBoxLayout()
        self._bt_run_btn = QPushButton("🚀 Run Backtest")
        self._bt_run_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #3b82f6; color: white;"
        )
        self._bt_run_btn.clicked.connect(self._on_run_backtest_clicked)
        action_layout.addWidget(self._bt_run_btn)

        self._bt_progress = Any()  # QProgressBar from parent
        self._bt_status_label = QLabel("Ready")
        self._bt_status_label.setStyleSheet("color: #888;")
        action_layout.addWidget(self._bt_status_label)
        action_layout.addStretch()

        layout.addLayout(action_layout)
        layout.addStretch()

    def _on_load_strategy_clicked(self) -> None:
        """Handle load strategy button click.

        Original: entry_analyzer_backtest.py:315-325

        Opens file dialog to select strategy JSON config file.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Strategy Configuration",
            "03_JSON/Trading_Bot",
            "JSON Files (*.json)"
        )

        if file_path:
            self._bt_strategy_path_label.setText(file_path)
            self._bt_strategy_path_label.setStyleSheet("color: #10b981;")
            logger.info(f"Strategy loaded: {file_path}")

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
        if 'timestamp' not in df.columns and 'time' in df.columns:
            df['timestamp'] = df['time']

        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

        # Validate required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
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
                f"Running backtest on regime set...\n"
                f"This may take a few moments."
            )

            # Run backtest
            from src.backtesting.engine import BacktestEngine

            engine = BacktestEngine()
            results = engine.run(
                config=config,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=capital
            )

            # Display results in Results tab
            self._display_backtest_results(results, f"Regime Set: {config_path.stem}")

            # Switch to Results tab
            self._tabs.setCurrentIndex(1)  # Results tab

            self._bt_run_btn.setEnabled(True)

            logger.info(f"Regime set backtest completed")

        except Exception as e:
            logger.error(f"Regime set backtest failed: {e}", exc_info=True)
            self._bt_run_btn.setEnabled(True)

            QMessageBox.critical(
                self,
                "Backtest Error",
                f"Failed to backtest regime set:\n\n{str(e)}"
            )
