"""Entry Analyzer Popup Dialog.

Displays analysis results for the visible chart range,
including optimized indicator sets and entry signals.

Phase 5: Added AI Copilot, Validation, Filters, Reports.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from PyQt6.QtCore import QDate, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult, EntryEvent

logger = logging.getLogger(__name__)


class CopilotWorker(QThread):
    """Background worker for AI Copilot analysis."""

    finished = pyqtSignal(object)  # CopilotResponse
    error = pyqtSignal(str)

    def __init__(
        self,
        analysis: Any,
        symbol: str,
        timeframe: str,
        validation: Any = None,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._analysis = analysis
        self._symbol = symbol
        self._timeframe = timeframe
        self._validation = validation

    def run(self) -> None:
        try:
            from src.analysis.visible_chart.entry_copilot import get_entry_analysis

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    get_entry_analysis(
                        self._analysis,
                        self._symbol,
                        self._timeframe,
                        self._validation,
                    )
                )
                if result:
                    self.finished.emit(result)
                else:
                    self.error.emit("AI analysis returned no result")
            finally:
                loop.close()
        except Exception as e:
            logger.exception("Copilot analysis failed")
            self.error.emit(str(e))


class ValidationWorker(QThread):
    """Background worker for walk-forward validation."""

    finished = pyqtSignal(object)  # ValidationResult
    error = pyqtSignal(str)

    def __init__(
        self,
        analysis: Any,
        candles: list[dict],
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._analysis = analysis
        self._candles = candles

    def run(self) -> None:
        try:
            from src.analysis.visible_chart.validation import validate_with_walkforward

            result = validate_with_walkforward(
                entries=self._analysis.entries,
                candles=self._candles,
                indicator_set=self._analysis.best_set,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Validation failed")
            self.error.emit(str(e))


class BacktestWorker(QThread):
    """Background worker for full history backtesting."""

    finished = pyqtSignal(object)  # Dict[str, Any] stats
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(
        self,
        config_path: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        chart_data: pd.DataFrame = None,
        data_timeframe: str = None,
        parent: Any = None
    ) -> None:
        super().__init__(parent)
        self.config_path = config_path
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.chart_data = chart_data
        self.data_timeframe = data_timeframe

    def run(self) -> None:
        try:
            import json
            from src.backtesting.engine import BacktestEngine
            from src.backtesting.schema_types import TradingBotConfig

            self.progress.emit("Loading strategy configuration...")
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            config = TradingBotConfig(**config_data)

            engine = BacktestEngine()

            if self.chart_data is not None and not self.chart_data.empty:
                self.progress.emit(f"Using chart data ({self.data_timeframe}, {len(self.chart_data)} candles)...")
            else:
                self.progress.emit(f"Loading data for {self.symbol}...")

            self.progress.emit("Running backtest simulation...")
            results = engine.run(
                config=config,
                symbol=self.symbol,
                start_date=self.start_date,
                end_date=self.end_date,
                initial_capital=self.initial_capital,
                chart_data=self.chart_data,
                data_timeframe=self.data_timeframe
            )

            self.finished.emit(results)

        except Exception as e:
            logger.exception("Backtest failed")
            self.error.emit(str(e))


class EntryAnalyzerPopup(QDialog):
    """Popup dialog for Entry Analyzer results.

    Displays:
    - Current regime detection
    - Optimized indicator set with parameters
    - List of detected entries (LONG green / SHORT red)
    - AI Copilot recommendations (Phase 5)
    - Walk-forward validation (Phase 4)
    - Report generation (Phase 4.5)
    - Full History Backtesting (New)
    """

    analyze_requested = pyqtSignal()
    draw_entries_requested = pyqtSignal(list)
    clear_entries_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("🎯 Entry Analyzer & Backtester")
        self.setMinimumSize(900, 750)
        self.resize(1000, 800)

        self._result: AnalysisResult | None = None
        self._validation_result: Any = None
        self._copilot_response: Any = None
        self._backtest_result: Any = None
        self._candles: list[dict] = []
        self._symbol: str = "UNKNOWN"
        self._timeframe: str = "1m"
        self._copilot_worker: CopilotWorker | None = None
        self._validation_worker: ValidationWorker | None = None
        self._backtest_worker: BacktestWorker | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header with status
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget for different views
        self._tabs = QTabWidget()

        # Tab 0: Backtest Setup (New)
        setup_tab = QWidget()
        self._setup_backtest_config_tab(setup_tab)
        self._tabs.addTab(setup_tab, "⚙️ Backtest Setup")

        # Tab 1: Indicator Optimization (Phase 1.3)
        optimization_tab = QWidget()
        self._setup_indicator_optimization_tab(optimization_tab)
        self._tabs.addTab(optimization_tab, "🔧 Indicator Optimization")

        # Tab 2: Pattern Recognition (NEW)
        pattern_tab = QWidget()
        self._setup_pattern_recognition_tab(pattern_tab)
        self._tabs.addTab(pattern_tab, "🔍 Pattern Recognition")

        # Tab 3: Analysis (entries + indicators) - Existing
        analysis_tab = QWidget()
        self._setup_analysis_tab(analysis_tab)
        self._tabs.addTab(analysis_tab, "📊 Visible Range")

        # Tab 4: Backtest Results (New)
        bt_results_tab = QWidget()
        self._setup_backtest_results_tab(bt_results_tab)
        self._tabs.addTab(bt_results_tab, "📈 Backtest Results")

        # Tab 5: AI Copilot
        ai_tab = QWidget()
        self._setup_ai_tab(ai_tab)
        self._tabs.addTab(ai_tab, "🤖 AI Copilot")

        # Tab 6: Validation
        validation_tab = QWidget()
        self._setup_validation_tab(validation_tab)
        self._tabs.addTab(validation_tab, "✅ Validation")

        layout.addWidget(self._tabs, stretch=1)

        # Footer with actions
        footer = self._create_footer()
        layout.addWidget(footer)

    def _setup_backtest_config_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)
        
        # Strategy Selection
        group_strat = QGroupBox("Strategy Configuration")
        layout_strat = QHBoxLayout(group_strat)
        
        self._strategy_path_edit = QLineEdit()
        self._strategy_path_edit.setPlaceholderText("Path to strategy JSON file...")
        self._strategy_load_btn = QPushButton("📂 Load")
        self._strategy_load_btn.clicked.connect(self._on_load_strategy_clicked)
        
        layout_strat.addWidget(self._strategy_path_edit)
        layout_strat.addWidget(self._strategy_load_btn)
        layout.addWidget(group_strat)
        
        # Data Selection
        group_data = QGroupBox("Data Selection (Chart Data if available, otherwise Bitunix API/SQLite)")
        layout_data = QGridLayout(group_data)
        
        layout_data.addWidget(QLabel("Symbol:"), 0, 0)
        self._bt_symbol_combo = QComboBox()
        self._bt_symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "bitunix:BTCUSDT", "bitunix:ETHUSDT"])
        self._bt_symbol_combo.setEditable(True)
        layout_data.addWidget(self._bt_symbol_combo, 0, 1)
        
        layout_data.addWidget(QLabel("Start Date:"), 1, 0)
        self._bt_start_date = QDateEdit()
        self._bt_start_date.setCalendarPopup(True)
        self._bt_start_date.setDate(QDate.currentDate().addDays(-30)) # Default last 30 days
        layout_data.addWidget(self._bt_start_date, 1, 1)
        
        layout_data.addWidget(QLabel("End Date:"), 2, 0)
        self._bt_end_date = QDateEdit()
        self._bt_end_date.setCalendarPopup(True)
        self._bt_end_date.setDate(QDate.currentDate())
        layout_data.addWidget(self._bt_end_date, 2, 1)
        
        layout_data.addWidget(QLabel("Capital ($):"), 3, 0)
        self._bt_capital = QSpinBox()
        self._bt_capital.setRange(100, 1000000)
        self._bt_capital.setValue(10000)
        layout_data.addWidget(self._bt_capital, 3, 1)
        
        layout.addWidget(group_data)
        
        # Action
        self._bt_run_btn = QPushButton("🚀 Run Backtest")
        self._bt_run_btn.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 10px; background-color: #2563eb;")
        self._bt_run_btn.clicked.connect(self._on_run_backtest_clicked)
        layout.addWidget(self._bt_run_btn)
        
        self._bt_status_label = QLabel("Ready")
        self._bt_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._bt_status_label)
        
        layout.addStretch()

    def _setup_backtest_results_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        # Data Source Information (NEW)
        self._bt_data_source_group = QGroupBox("📊 Data Source Information")
        layout_data_src = QGridLayout(self._bt_data_source_group)

        self._lbl_data_source = QLabel("--")
        self._lbl_data_source.setStyleSheet("font-weight: bold; color: #1976d2;")
        layout_data_src.addWidget(QLabel("Source:"), 0, 0)
        layout_data_src.addWidget(self._lbl_data_source, 0, 1)

        self._lbl_data_timeframe = QLabel("--")
        layout_data_src.addWidget(QLabel("Timeframe:"), 0, 2)
        layout_data_src.addWidget(self._lbl_data_timeframe, 0, 3)

        self._lbl_data_period = QLabel("--")
        layout_data_src.addWidget(QLabel("Period:"), 1, 0)
        layout_data_src.addWidget(self._lbl_data_period, 1, 1, 1, 3)

        self._lbl_data_candles = QLabel("--")
        layout_data_src.addWidget(QLabel("Total Candles:"), 2, 0)
        layout_data_src.addWidget(self._lbl_data_candles, 2, 1)

        layout.addWidget(self._bt_data_source_group)

        # Summary Metrics
        self._bt_summary_group = QGroupBox("Performance Summary")
        layout_sum = QGridLayout(self._bt_summary_group)

        self._lbl_net_profit = QLabel("--")
        self._lbl_net_profit.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout_sum.addWidget(QLabel("Net Profit:"), 0, 0)
        layout_sum.addWidget(self._lbl_net_profit, 0, 1)

        self._lbl_win_rate = QLabel("--")
        layout_sum.addWidget(QLabel("Win Rate:"), 1, 0)
        layout_sum.addWidget(self._lbl_win_rate, 1, 1)

        self._lbl_profit_factor = QLabel("--")
        layout_sum.addWidget(QLabel("Profit Factor:"), 0, 2)
        layout_sum.addWidget(self._lbl_profit_factor, 0, 3)

        self._lbl_trades = QLabel("--")
        layout_sum.addWidget(QLabel("Total Trades:"), 1, 2)
        layout_sum.addWidget(self._lbl_trades, 1, 3)

        layout.addWidget(self._bt_summary_group)

        # Trade List
        layout.addWidget(QLabel("Trade History:"))
        self._bt_trades_table = QTableWidget()
        self._bt_trades_table.setColumnCount(6)
        self._bt_trades_table.setHorizontalHeaderLabels(["Entry Time", "Side", "Entry Price", "Exit Price", "PnL", "Reason"])
        self._bt_trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._bt_trades_table)

    def _on_load_strategy_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Strategy JSON", str(Path.cwd()), "JSON Files (*.json)"
        )
        if file_path:
            self._strategy_path_edit.setText(file_path)

    def _on_run_backtest_clicked(self) -> None:
        config_path = self._strategy_path_edit.text()
        if not config_path or not Path(config_path).exists():
            QMessageBox.warning(self, "Error", "Please select a valid strategy JSON file.")
            return

        symbol = self._bt_symbol_combo.currentText()
        start_date = datetime.combine(self._bt_start_date.date().toPyDate(), datetime.min.time())
        end_date = datetime.combine(self._bt_end_date.date().toPyDate(), datetime.max.time())
        capital = self._bt_capital.value()

        # Convert chart candles to DataFrame if available
        chart_df = None
        if self._candles:
            try:
                chart_df = self._convert_candles_to_dataframe(self._candles)
                logger.info(f"Using chart data: {len(chart_df)} candles, timeframe={self._timeframe}, symbol={self._symbol}")
            except Exception as e:
                logger.warning(f"Failed to convert chart candles to DataFrame: {e}. Falling back to database.")
                chart_df = None

        self._bt_run_btn.setEnabled(False)
        self._bt_status_label.setText("Initializing Backtest...")

        self._backtest_worker = BacktestWorker(
            config_path=config_path,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=float(capital),
            chart_data=chart_df,
            data_timeframe=self._timeframe if chart_df is not None else None,
            parent=self
        )
        self._backtest_worker.progress.connect(self._bt_status_label.setText)
        self._backtest_worker.finished.connect(self._on_backtest_finished)
        self._backtest_worker.error.connect(self._on_backtest_error)
        self._backtest_worker.start()

    def _convert_candles_to_dataframe(self, candles: list[dict]) -> pd.DataFrame:
        """Convert chart candles (list of dicts) to DataFrame format expected by BacktestEngine.

        Args:
            candles: List of candle dicts with timestamp, open, high, low, close, volume

        Returns:
            DataFrame with DatetimeIndex and OHLCV columns
        """
        import pandas as pd

        if not candles:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(candles)

        # Ensure timestamp column exists and convert to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['time'])
            df.drop(columns=['time'], inplace=True)
        else:
            raise ValueError("No timestamp column found in candle data")

        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        # Ensure required OHLCV columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
            df[col] = pd.to_numeric(df[col])

        # Keep only required columns
        df = df[required_cols]

        logger.info(f"Converted {len(df)} candles to DataFrame. Date range: {df.index[0]} to {df.index[-1]}")

        return df

    def _on_backtest_finished(self, results: dict) -> None:
        self._backtest_result = results
        self._bt_run_btn.setEnabled(True)
        self._bt_status_label.setText("Backtest Complete")

        # Switch to results tab
        self._tabs.setCurrentIndex(2)

        # Populate Results
        if "error" in results:
            QMessageBox.critical(self, "Backtest Error", results["error"])
            return

        # Populate Data Source Information (NEW)
        data_source = results.get("data_source", {})
        source_type = data_source.get("source", "Unknown")
        timeframe = data_source.get("timeframe", "Unknown")
        start_date = data_source.get("start_date", "Unknown")
        end_date = data_source.get("end_date", "Unknown")
        total_candles = data_source.get("total_candles", 0)

        self._lbl_data_source.setText(source_type)
        self._lbl_data_timeframe.setText(timeframe)
        self._lbl_data_period.setText(f"{start_date} → {end_date}")
        self._lbl_data_candles.setText(f"{total_candles:,} candles")

        # Populate Performance Metrics
        net_profit = results.get("net_profit", 0.0)
        net_profit_pct = results.get("net_profit_pct", 0.0)
        color = "green" if net_profit >= 0 else "red"

        self._lbl_net_profit.setText(f"${net_profit:,.2f} ({net_profit_pct:+.2%})")
        self._lbl_net_profit.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {color};")

        self._lbl_win_rate.setText(f"{results.get('win_rate', 0.0):.1%}")
        self._lbl_profit_factor.setText(f"{results.get('profit_factor', 0.0):.2f}")
        self._lbl_trades.setText(str(results.get("total_trades", 0)))

        # Fill trade table
        trades = results.get("trades", [])
        self._bt_trades_table.setRowCount(len(trades))
        for row, t in enumerate(trades):
            self._bt_trades_table.setItem(row, 0, QTableWidgetItem(t["entry_time"]))
            self._bt_trades_table.setItem(row, 1, QTableWidgetItem(t["side"].upper()))
            self._bt_trades_table.setItem(row, 2, QTableWidgetItem(f"{t['entry_price']:.2f}"))
            self._bt_trades_table.setItem(row, 3, QTableWidgetItem(f"{t['exit_price']:.2f}" if t['exit_price'] else "--"))

            pnl_item = QTableWidgetItem(f"{t['pnl']:+.2f} ({t['pnl_pct']:+.2%})")
            pnl_color = "green" if t["pnl"] > 0 else "red"
            pnl_item.setForeground(Qt.GlobalColor.green if t["pnl"] > 0 else Qt.GlobalColor.red)
            self._bt_trades_table.setItem(row, 4, pnl_item)

            self._bt_trades_table.setItem(row, 5, QTableWidgetItem(t["reason"]))

        # Draw regime boundaries on chart
        self._draw_regime_boundaries(results)

    def _on_backtest_error(self, error: str) -> None:
        self._bt_run_btn.setEnabled(True)
        self._bt_status_label.setText("Error")
        QMessageBox.critical(self, "Backtest Failed", error)

    def _draw_regime_boundaries(self, results: dict) -> None:
        """Draw vertical lines for regime boundaries on chart.

        Args:
            results: Backtest results containing regime_history
        """
        from datetime import datetime
        import logging

        logger = logging.getLogger(__name__)

        # Get regime history from results
        regime_history = results.get("regime_history", [])
        if not regime_history:
            logger.info("No regime history to visualize")
            return

        # Get parent chart widget
        chart_widget = self.parent()
        if chart_widget is None:
            logger.warning("No parent chart widget found for regime visualization")
            return

        # Check if chart has regime line methods
        if not hasattr(chart_widget, 'clear_regime_lines') or not hasattr(chart_widget, 'add_regime_line'):
            logger.warning("Chart widget does not have regime line methods")
            return

        # Clear existing regime lines
        try:
            chart_widget.clear_regime_lines()
            logger.info("Cleared existing regime lines")
        except Exception as e:
            logger.error(f"Failed to clear regime lines: {e}", exc_info=True)
            return

        # Add regime lines for each regime change
        for idx, regime_change in enumerate(regime_history):
            try:
                timestamp = regime_change.get('timestamp')
                regime_ids = regime_change.get('regime_ids', [])
                regimes = regime_change.get('regimes', [])

                if not timestamp or not regimes:
                    continue

                # Convert timestamp string to datetime if needed
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

                # Get primary regime name (first in list)
                primary_regime = regimes[0] if regimes else {}
                regime_name = primary_regime.get('name', 'Unknown')
                regime_id = primary_regime.get('id', f'regime_{idx}')

                # Create label with all active regimes
                if len(regimes) > 1:
                    regime_names = [r.get('name', '') for r in regimes]
                    label = f"{' + '.join(regime_names)}"
                else:
                    label = regime_name

                # Add regime line to chart
                line_id = f"regime_{idx}_{regime_id}"
                chart_widget.add_regime_line(
                    line_id=line_id,
                    timestamp=timestamp,
                    regime_name=regime_name,
                    label=label
                )
                logger.debug(f"Added regime line: {line_id} at {timestamp} ({label})")

            except Exception as e:
                logger.error(f"Failed to add regime line {idx}: {e}", exc_info=True)
                continue

        logger.info(f"Drew {len(regime_history)} regime boundaries on chart")

    def _create_header(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 10)

        self._regime_label = QLabel("Regime: --")
        self._regime_label.setStyleSheet(
            "font-weight: bold; font-size: 14pt; padding: 5px;"
        )
        layout.addWidget(self._regime_label)

        layout.addStretch()

        self._signal_count_label = QLabel("Signals: 0 LONG / 0 SHORT")
        self._signal_count_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(self._signal_count_label)

        self._signal_rate_label = QLabel("Rate: 0/h")
        self._signal_rate_label.setStyleSheet("font-size: 11pt; color: #888;")
        layout.addWidget(self._signal_rate_label)

        return widget

    def _setup_analysis_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Indicator Set info
        indicator_group = self._create_indicator_group()
        splitter.addWidget(indicator_group)

        # Bottom: Entry table
        entries_group = self._create_entries_group()
        splitter.addWidget(entries_group)

        splitter.setSizes([200, 300])
        layout.addWidget(splitter)

    def _setup_ai_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        # AI Status / Action row
        action_row = QHBoxLayout()
        self._ai_analyze_btn = QPushButton("🤖 Run AI Analysis")
        self._ai_analyze_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #8B5CF6; color: white;"
        )
        self._ai_analyze_btn.clicked.connect(self._on_ai_analyze_clicked)
        action_row.addWidget(self._ai_analyze_btn)

        self._ai_progress = QProgressBar()
        self._ai_progress.setMaximumWidth(150)
        self._ai_progress.setVisible(False)
        action_row.addWidget(self._ai_progress)

        self._ai_status_label = QLabel("Ready")
        self._ai_status_label.setStyleSheet("color: #888;")
        action_row.addWidget(self._ai_status_label)
        action_row.addStretch()
        layout.addLayout(action_row)

        # AI Results
        self._ai_results_text = QTextEdit()
        self._ai_results_text.setReadOnly(True)
        self._ai_results_text.setStyleSheet(
            "font-family: monospace; background-color: #1a1a1a; color: #e0e0e0;"
        )
        self._ai_results_text.setPlaceholderText(
            "AI analysis results will appear here...\n\n"
            "Click 'Run AI Analysis' to get:\n"
            "• Entry quality assessments\n"
            "• Risk/reward analysis\n"
            "• Best entry recommendation\n"
            "• Trade suggestions"
        )
        layout.addWidget(self._ai_results_text)

    def _setup_validation_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        # Validation action row
        action_row = QHBoxLayout()
        self._validate_btn = QPushButton("✅ Run Validation")
        self._validate_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #10B981; color: white;"
        )
        self._validate_btn.clicked.connect(self._on_validate_clicked)
        action_row.addWidget(self._validate_btn)

        self._val_progress = QProgressBar()
        self._val_progress.setMaximumWidth(150)
        self._val_progress.setVisible(False)
        action_row.addWidget(self._val_progress)

        self._val_status_label = QLabel("Ready")
        self._val_status_label.setStyleSheet("color: #888;")
        action_row.addWidget(self._val_status_label)
        action_row.addStretch()
        layout.addLayout(action_row)

        # Validation summary
        self._val_summary = QLabel("No validation results yet")
        self._val_summary.setStyleSheet("font-size: 12pt; padding: 10px;")
        layout.addWidget(self._val_summary)

        # Folds table
        self._folds_table = QTableWidget()
        self._folds_table.setColumnCount(6)
        self._folds_table.setHorizontalHeaderLabels(
            ["Fold", "Train Score", "Test Score", "Ratio", "OOS WR", "Overfit"]
        )
        self._folds_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self._folds_table)

    def _create_indicator_group(self) -> QGroupBox:
        group = QGroupBox("📊 Optimized Indicator Set")
        layout = QVBoxLayout(group)

        self._set_name_label = QLabel("Active Set: --")
        self._set_name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._set_name_label)

        self._params_table = QTableWidget()
        self._params_table.setColumnCount(3)
        self._params_table.setHorizontalHeaderLabels(["Family", "Parameter", "Value"])
        self._params_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._params_table.setMaximumHeight(150)
        layout.addWidget(self._params_table)

        self._score_label = QLabel("Score: --")
        layout.addWidget(self._score_label)

        self._alternatives_label = QLabel("Alternatives: --")
        self._alternatives_label.setStyleSheet("color: #888; font-size: 10pt;")
        self._alternatives_label.setVisible(False)
        layout.addWidget(self._alternatives_label)

        return group

    def _create_entries_group(self) -> QGroupBox:
        group = QGroupBox("🎯 Detected Entries")
        layout = QVBoxLayout(group)

        # Filter toggle
        filter_row = QHBoxLayout()
        self._filter_checkbox = QCheckBox("Apply Trade Filters (no-trade zones)")
        self._filter_checkbox.setChecked(False)
        self._filter_checkbox.setToolTip(
            "Filter out entries during volatility spikes, low volume, etc."
        )
        filter_row.addWidget(self._filter_checkbox)
        self._filter_stats_label = QLabel("")
        self._filter_stats_label.setStyleSheet("color: #888;")
        filter_row.addWidget(self._filter_stats_label)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self._entries_table = QTableWidget()
        self._entries_table.setColumnCount(5)
        self._entries_table.setHorizontalHeaderLabels(
            ["Time", "Side", "Price", "Confidence", "Reasons"]
        )
        self._entries_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._entries_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self._entries_table)

        return group

    def _create_footer(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        # Analyze button
        self._analyze_btn = QPushButton("🔄 Analyze Visible Range")
        self._analyze_btn.setStyleSheet(
            "padding: 8px 16px; font-weight: bold; background-color: #3b82f6; color: white;"
        )
        self._analyze_btn.clicked.connect(self._on_analyze_clicked)
        layout.addWidget(self._analyze_btn)

        self._progress = QProgressBar()
        self._progress.setMaximumWidth(150)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        layout.addStretch()

        # Report button
        self._report_btn = QPushButton("📄 Generate Report")
        self._report_btn.setEnabled(False)
        self._report_btn.clicked.connect(self._on_report_clicked)
        layout.addWidget(self._report_btn)

        # Draw entries button
        self._draw_btn = QPushButton("📍 Draw on Chart")
        self._draw_btn.setEnabled(False)
        self._draw_btn.clicked.connect(self._on_draw_clicked)
        layout.addWidget(self._draw_btn)

        # Clear button
        self._clear_btn = QPushButton("🗑️ Clear Entries")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self._clear_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return widget

    def set_context(self, symbol: str, timeframe: str, candles: list[dict]) -> None:
        """Set context for AI/Validation."""
        self._symbol = symbol
        self._timeframe = timeframe
        self._candles = candles

    def set_analyzing(self, analyzing: bool) -> None:
        """Set analyzing state and update progress bar.

        Issue #27: Added debug logging for progress bar state changes.
        """
        # Import debug logger
        try:
            from src.analysis.visible_chart.debug_logger import debug_logger
        except ImportError:
            debug_logger = logger

        debug_logger.info("PROGRESS BAR: set_analyzing(%s)", analyzing)

        self._analyze_btn.setEnabled(not analyzing)
        self._progress.setVisible(analyzing)
        if analyzing:
            self._progress.setRange(0, 0)  # Indeterminate mode (busy spinner)
            debug_logger.debug("Progress bar: indeterminate mode (analyzing)")
        else:
            self._progress.setRange(0, 100)  # Determinate mode
            self._progress.setValue(100)  # Complete
            debug_logger.debug("Progress bar: complete (100%%)")

        # Force GUI update
        self._progress.update()
        debug_logger.debug("Progress bar updated, visible=%s", analyzing)

    def set_result(self, result: AnalysisResult) -> None:
        self._result = result

        # Update regime
        regime_colors = {
            "trend_up": "#22c55e",
            "trend_down": "#ef4444",
            "range": "#f59e0b",
            "high_vol": "#a855f7",
            "squeeze": "#3b82f6",
            "no_trade": "#6b7280",
        }
        regime_text = result.regime.value.replace("_", " ").title()
        color = regime_colors.get(result.regime.value, "#888")
        self._regime_label.setText(f"Regime: {regime_text}")
        self._regime_label.setStyleSheet(
            f"font-weight: bold; font-size: 14pt; padding: 5px; color: {color};"
        )

        # Update signal counts
        self._signal_count_label.setText(
            f"Signals: {result.long_count} LONG / {result.short_count} SHORT"
        )
        self._signal_rate_label.setText(f"Rate: {result.signal_rate_per_hour:.1f}/h")

        # Update indicator set
        if result.active_set:
            self._set_name_label.setText(f"Active Set: {result.active_set.name}")
            self._score_label.setText(f"Score: {result.active_set.score:.3f}")
            self._update_params_table(result.active_set.parameters)

            if result.alternative_sets:
                alt_names = [s.name for s in result.alternative_sets[:2]]
                self._alternatives_label.setText(f"Alternatives: {', '.join(alt_names)}")
                self._alternatives_label.setVisible(True)
            else:
                self._alternatives_label.setVisible(False)
        else:
            self._set_name_label.setText("Active Set: Default (no optimization)")
            self._score_label.setText("Score: --")
            self._params_table.setRowCount(0)
            self._alternatives_label.setVisible(False)

        # Update entries table
        self._update_entries_table(result.entries)

        # Enable buttons
        self._draw_btn.setEnabled(len(result.entries) > 0)
        self._report_btn.setEnabled(True)
        self._ai_analyze_btn.setEnabled(True)
        self._validate_btn.setEnabled(len(result.entries) > 0 and len(self._candles) > 0)

        logger.info(
            "Analysis result displayed: %d entries, regime=%s",
            len(result.entries),
            result.regime.value,
        )

    def _update_params_table(self, params: dict) -> None:
        self._params_table.setRowCount(0)
        row = 0

        for family, family_params in params.items():
            if isinstance(family_params, dict):
                for param, value in family_params.items():
                    self._params_table.insertRow(row)
                    self._params_table.setItem(row, 0, QTableWidgetItem(family))
                    self._params_table.setItem(row, 1, QTableWidgetItem(param))
                    self._params_table.setItem(row, 2, QTableWidgetItem(str(value)))
                    row += 1
            else:
                self._params_table.insertRow(row)
                self._params_table.setItem(row, 0, QTableWidgetItem(family))
                self._params_table.setItem(row, 1, QTableWidgetItem("value"))
                self._params_table.setItem(row, 2, QTableWidgetItem(str(family_params)))
                row += 1

    def _update_entries_table(self, entries: list[EntryEvent]) -> None:
        self._entries_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            time_str = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M")
            self._entries_table.setItem(row, 0, QTableWidgetItem(time_str))

            side_item = QTableWidgetItem(entry.side.value.upper())
            self._entries_table.setItem(row, 1, side_item)

            self._entries_table.setItem(row, 2, QTableWidgetItem(f"{entry.price:.2f}"))
            self._entries_table.setItem(row, 3, QTableWidgetItem(f"{entry.confidence:.0%}"))

            reasons_item = QTableWidgetItem(", ".join(entry.reason_tags))
            self._entries_table.setItem(row, 4, reasons_item)

    def _on_analyze_clicked(self) -> None:
        self.set_analyzing(True)
        self.analyze_requested.emit()

    def _on_draw_clicked(self) -> None:
        if self._result and self._result.entries:
            self.draw_entries_requested.emit(self._result.entries)

    def _on_clear_clicked(self) -> None:
        self.clear_entries_requested.emit()

    def _on_ai_analyze_clicked(self) -> None:
        if not self._result:
            QMessageBox.warning(self, "No Data", "Run analysis first")
            return

        self._ai_analyze_btn.setEnabled(False)
        self._ai_progress.setVisible(True)
        self._ai_progress.setRange(0, 0)
        self._ai_status_label.setText("Running AI analysis...")

        self._copilot_worker = CopilotWorker(
            analysis=self._result,
            symbol=self._symbol,
            timeframe=self._timeframe,
            validation=self._validation_result,
            parent=self,
        )
        self._copilot_worker.finished.connect(self._on_ai_finished)
        self._copilot_worker.error.connect(self._on_ai_error)
        self._copilot_worker.start()

    def _on_ai_finished(self, response: Any) -> None:
        self._copilot_response = response
        self._ai_progress.setVisible(False)
        self._ai_analyze_btn.setEnabled(True)
        self._ai_status_label.setText("Complete")

        # Format results
        lines = ["# AI Copilot Analysis\n"]

        lines.append(f"## Recommendation: {response.recommended_action.upper()}\n")
        lines.append(f"{response.reasoning}\n")

        lines.append(f"\n## Market Assessment\n{response.summary.market_assessment}")
        lines.append(f"\n**Bias:** {response.summary.overall_bias}")
        lines.append(f"**Best Entry:** #{response.summary.best_entry_idx + 1}" if response.summary.best_entry_idx >= 0 else "**Best Entry:** None recommended")

        if response.summary.risk_warning:
            lines.append(f"\n⚠️ **Risk Warning:** {response.summary.risk_warning}")

        if response.summary.key_levels:
            levels = ", ".join(f"{lv:.2f}" for lv in response.summary.key_levels)
            lines.append(f"\n**Key Levels:** {levels}")

        lines.append("\n\n## Entry Assessments\n")
        for i, assess in enumerate(response.entry_assessments):
            lines.append(f"### Entry {i + 1}: {assess.quality.value.upper()}")
            lines.append(f"Confidence adjustment: {assess.confidence_adjustment:+.1%}")
            lines.append(f"**Strengths:** {', '.join(assess.strengths)}")
            lines.append(f"**Weaknesses:** {', '.join(assess.weaknesses)}")
            lines.append(f"**Suggestion:** {assess.trade_suggestion}\n")

        self._ai_results_text.setPlainText("\n".join(lines))
        logger.info("AI analysis complete: %s", response.recommended_action)

    def _on_ai_error(self, error_msg: str) -> None:
        self._ai_progress.setVisible(False)
        self._ai_analyze_btn.setEnabled(True)
        self._ai_status_label.setText("Error")
        self._ai_results_text.setPlainText(f"❌ AI Analysis Error:\n\n{error_msg}")
        logger.error("AI analysis error: %s", error_msg)

    def _on_validate_clicked(self) -> None:
        if not self._result or not self._candles:
            QMessageBox.warning(self, "No Data", "Run analysis first and ensure candle data is available")
            return

        self._validate_btn.setEnabled(False)
        self._val_progress.setVisible(True)
        self._val_progress.setRange(0, 0)
        self._val_status_label.setText("Running validation...")

        self._validation_worker = ValidationWorker(
            analysis=self._result,
            candles=self._candles,
            parent=self,
        )
        self._validation_worker.finished.connect(self._on_validation_finished)
        self._validation_worker.error.connect(self._on_validation_error)
        self._validation_worker.start()

    def _on_validation_finished(self, result: Any) -> None:
        self._validation_result = result
        self._val_progress.setVisible(False)
        self._validate_btn.setEnabled(True)

        status = "✅ PASSED" if result.is_valid else "❌ FAILED"
        self._val_status_label.setText(status)

        summary = (
            f"**Status:** {status}\n"
            f"**OOS Score:** {result.avg_test_score:.3f}\n"
            f"**OOS Win Rate:** {result.oos_win_rate:.1%}\n"
            f"**Train/Test Ratio:** {result.avg_train_test_ratio:.2f}\n"
            f"**Total OOS Trades:** {result.total_oos_trades}"
        )
        if result.failure_reasons:
            summary += f"\n**Issues:** {', '.join(result.failure_reasons)}"
        self._val_summary.setText(summary)

        # Update folds table
        self._folds_table.setRowCount(len(result.folds))
        for row, fold in enumerate(result.folds):
            self._folds_table.setItem(row, 0, QTableWidgetItem(str(fold.fold_idx)))
            self._folds_table.setItem(row, 1, QTableWidgetItem(f"{fold.train_score:.3f}"))
            self._folds_table.setItem(row, 2, QTableWidgetItem(f"{fold.test_score:.3f}"))
            self._folds_table.setItem(row, 3, QTableWidgetItem(f"{fold.train_test_ratio:.2f}"))
            self._folds_table.setItem(row, 4, QTableWidgetItem(f"{fold.test_win_rate:.1%}"))
            overfit = "Yes" if fold.is_overfit else "No"
            self._folds_table.setItem(row, 5, QTableWidgetItem(overfit))

        logger.info("Validation complete: %s", "passed" if result.is_valid else "failed")

    def _on_validation_error(self, error_msg: str) -> None:
        self._val_progress.setVisible(False)
        self._validate_btn.setEnabled(True)
        self._val_status_label.setText("Error")
        self._val_summary.setText(f"❌ Validation Error: {error_msg}")
        logger.error("Validation error: %s", error_msg)

    def _setup_indicator_optimization_tab(self, tab: QWidget) -> None:
        """Setup Indicator Optimization tab (Phase 1.3).

        Allows testing individual indicators with different parameters
        to find optimal settings per regime.
        """
        layout = QVBoxLayout(tab)

        # Header with description
        header_label = QLabel(
            "Test individual indicators with various parameter settings to find "
            "optimal configurations for each market regime."
        )
        header_label.setWordWrap(True)
        header_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(header_label)

        # Indicator Selection Group
        indicator_group = QGroupBox("Indicator Selection")
        indicator_layout = QVBoxLayout(indicator_group)

        self._opt_indicator_checkboxes = {}
        indicators = [
            ('RSI', 'Relative Strength Index'),
            ('MACD', 'Moving Average Convergence Divergence'),
            ('ADX', 'Average Directional Index'),
            ('BB', 'Bollinger Bands'),
            ('SMA', 'Simple Moving Average'),
            ('EMA', 'Exponential Moving Average'),
            ('ATR', 'Average True Range'),
        ]

        for indicator_id, indicator_name in indicators:
            cb = QCheckBox(f"{indicator_id} - {indicator_name}")
            cb.setChecked(indicator_id in ['RSI', 'MACD', 'ADX'])  # Default: RSI, MACD, ADX
            self._opt_indicator_checkboxes[indicator_id] = cb
            indicator_layout.addWidget(cb)

        layout.addWidget(indicator_group)

        # Parameter Ranges Group
        param_group = QGroupBox("Parameter Ranges")
        param_layout = QFormLayout(param_group)

        # RSI Period Range
        rsi_range_layout = QHBoxLayout()
        self.rsi_min_spin = QSpinBox()
        self.rsi_min_spin.setRange(5, 50)
        self.rsi_min_spin.setValue(10)
        self.rsi_max_spin = QSpinBox()
        self.rsi_max_spin.setRange(5, 50)
        self.rsi_max_spin.setValue(20)
        self.rsi_step_spin = QSpinBox()
        self.rsi_step_spin.setRange(1, 10)
        self.rsi_step_spin.setValue(2)
        rsi_range_layout.addWidget(QLabel("Min:"))
        rsi_range_layout.addWidget(self.rsi_min_spin)
        rsi_range_layout.addWidget(QLabel("Max:"))
        rsi_range_layout.addWidget(self.rsi_max_spin)
        rsi_range_layout.addWidget(QLabel("Step:"))
        rsi_range_layout.addWidget(self.rsi_step_spin)
        param_layout.addRow("RSI Period Range:", rsi_range_layout)

        # MACD Fast Period Range
        macd_fast_layout = QHBoxLayout()
        self.macd_fast_min_spin = QSpinBox()
        self.macd_fast_min_spin.setRange(5, 30)
        self.macd_fast_min_spin.setValue(8)
        self.macd_fast_max_spin = QSpinBox()
        self.macd_fast_max_spin.setRange(5, 30)
        self.macd_fast_max_spin.setValue(16)
        self.macd_fast_step_spin = QSpinBox()
        self.macd_fast_step_spin.setRange(1, 5)
        self.macd_fast_step_spin.setValue(2)
        macd_fast_layout.addWidget(QLabel("Min:"))
        macd_fast_layout.addWidget(self.macd_fast_min_spin)
        macd_fast_layout.addWidget(QLabel("Max:"))
        macd_fast_layout.addWidget(self.macd_fast_max_spin)
        macd_fast_layout.addWidget(QLabel("Step:"))
        macd_fast_layout.addWidget(self.macd_fast_step_spin)
        param_layout.addRow("MACD Fast Period:", macd_fast_layout)

        # ADX Period Range
        adx_range_layout = QHBoxLayout()
        self.adx_min_spin = QSpinBox()
        self.adx_min_spin.setRange(5, 30)
        self.adx_min_spin.setValue(10)
        self.adx_max_spin = QSpinBox()
        self.adx_max_spin.setRange(5, 30)
        self.adx_max_spin.setValue(20)
        self.adx_step_spin = QSpinBox()
        self.adx_step_spin.setRange(1, 5)
        self.adx_step_spin.setValue(2)
        adx_range_layout.addWidget(QLabel("Min:"))
        adx_range_layout.addWidget(self.adx_min_spin)
        adx_range_layout.addWidget(QLabel("Max:"))
        adx_range_layout.addWidget(self.adx_max_spin)
        adx_range_layout.addWidget(QLabel("Step:"))
        adx_range_layout.addWidget(self.adx_step_spin)
        param_layout.addRow("ADX Period Range:", adx_range_layout)

        layout.addWidget(param_group)

        # Progress bar (hidden by default)
        self._opt_progress = QProgressBar()
        self._opt_progress.setVisible(False)
        layout.addWidget(self._opt_progress)

        # Optimize Button
        self._optimize_btn = QPushButton("🚀 Optimize Indicators")
        self._optimize_btn.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; "
            "padding: 10px; font-size: 14px;"
        )
        self._optimize_btn.clicked.connect(self._on_optimize_indicators_clicked)
        layout.addWidget(self._optimize_btn)

        # Results Table
        self._optimization_results_table = QTableWidget()
        self._optimization_results_table.setColumnCount(7)
        self._optimization_results_table.setHorizontalHeaderLabels([
            "Indicator", "Parameters", "Regime", "Score (0-100)",
            "Win Rate", "Profit Factor", "Trades"
        ])
        self._optimization_results_table.horizontalHeader().setStretchLastSection(True)
        self._optimization_results_table.setAlternatingRowColors(True)
        self._optimization_results_table.setSortingEnabled(True)
        layout.addWidget(self._optimization_results_table)

        # Regime Set Builder Button
        self._create_regime_set_btn = QPushButton("📦 Create Regime Set from Results")
        self._create_regime_set_btn.setEnabled(False)  # Enabled after optimization
        self._create_regime_set_btn.setStyleSheet(
            "background-color: #2196f3; color: white; font-weight: bold; "
            "padding: 8px; font-size: 13px;"
        )
        self._create_regime_set_btn.setToolTip(
            "Automatically create a regime-based strategy set from the top-performing "
            "indicators in each regime. Generates a JSON config and runs backtest."
        )
        self._create_regime_set_btn.clicked.connect(self._on_create_regime_set_clicked)
        layout.addWidget(self._create_regime_set_btn)

        # Info label
        info_label = QLabel(
            "💡 Tip: Select indicators and adjust parameter ranges, then click Optimize. "
            "Results will show the best parameter combinations for each market regime."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        layout.addWidget(info_label)

    def _on_optimize_indicators_clicked(self) -> None:
        """Handle optimize indicators button click."""
        # Get selected indicators
        selected_indicators = [
            ind_type
            for ind_type, cb in self._opt_indicator_checkboxes.items()
            if cb.isChecked()
        ]

        if not selected_indicators:
            QMessageBox.warning(
                self,
                "No Indicators Selected",
                "Please select at least one indicator to optimize."
            )
            return

        # Get parameter ranges
        param_ranges = {
            'RSI': {
                'min': self.rsi_min_spin.value(),
                'max': self.rsi_max_spin.value(),
                'step': self.rsi_step_spin.value()
            },
            'MACD_fast': {
                'min': self.macd_fast_min_spin.value(),
                'max': self.macd_fast_max_spin.value(),
                'step': self.macd_fast_step_spin.value()
            },
            'ADX': {
                'min': self.adx_min_spin.value(),
                'max': self.adx_max_spin.value(),
                'step': self.adx_step_spin.value()
            }
        }

        # Validate date range and config
        if not self.json_file_input.text():
            QMessageBox.warning(
                self,
                "No Config Selected",
                "Please select a JSON strategy configuration first."
            )
            return

        # Show progress bar
        self._opt_progress.setVisible(True)
        self._opt_progress.setValue(0)
        self._optimize_btn.setEnabled(False)

        # Clear previous results
        self._optimization_results_table.setRowCount(0)

        # Log optimization start
        logger.info(
            f"Starting indicator optimization: {selected_indicators} with ranges {param_ranges}"
        )

        # Get dates from UI
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()

        # Get symbol
        symbol = self.symbol_combo.currentText()

        # Get initial capital
        capital = self.capital_spin.value()

        # Create and start optimization thread
        from src.ui.threads import IndicatorOptimizationThread

        self._optimization_thread = IndicatorOptimizationThread(
            selected_indicators=selected_indicators,
            param_ranges=param_ranges,
            json_config_path=self.json_file_input.text(),
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital,
            parent=self
        )

        # Connect signals
        self._optimization_thread.finished.connect(self._on_optimization_finished)
        self._optimization_thread.progress.connect(self._on_optimization_progress)
        self._optimization_thread.error.connect(self._on_optimization_error)

        # Start thread
        self._optimization_thread.start()

        logger.info(f"Optimization thread started for {len(selected_indicators)} indicators")

    def _on_optimization_finished(self, results: list) -> None:
        """Handle optimization thread completion.

        Args:
            results: List of optimization result dictionaries
        """
        # Hide progress bar
        self._opt_progress.setVisible(False)
        self._optimize_btn.setEnabled(True)

        logger.info(f"Optimization finished: {len(results)} results")

        # Store results for regime set building
        self._optimization_results = results

        # Enable regime set builder button if we have results
        self._create_regime_set_btn.setEnabled(len(results) > 0)

        # Sort results by score (descending)
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)

        # Populate results table
        self._optimization_results_table.setRowCount(len(sorted_results))

        for row, result in enumerate(sorted_results):
            # Indicator column
            ind_item = QTableWidgetItem(result['indicator'])
            self._optimization_results_table.setItem(row, 0, ind_item)

            # Parameters column
            params_str = ", ".join([f"{k}={v}" for k, v in result['params'].items()])
            params_item = QTableWidgetItem(params_str)
            self._optimization_results_table.setItem(row, 1, params_item)

            # Regime column
            regime_item = QTableWidgetItem(result['regime'])
            self._optimization_results_table.setItem(row, 2, regime_item)

            # Score column (colored by value)
            score = result['score']
            score_item = QTableWidgetItem(f"{score:.2f}")
            # Color code: green > 70, yellow 40-70, red < 40
            if score >= 70:
                score_item.setForeground(QColor("#4caf50"))  # Green
            elif score >= 40:
                score_item.setForeground(QColor("#ff9800"))  # Orange
            else:
                score_item.setForeground(QColor("#f44336"))  # Red
            self._optimization_results_table.setItem(row, 3, score_item)

            # Win Rate column
            win_rate_item = QTableWidgetItem(f"{result['win_rate']:.1%}")
            self._optimization_results_table.setItem(row, 4, win_rate_item)

            # Profit Factor column
            pf_item = QTableWidgetItem(f"{result['profit_factor']:.2f}")
            self._optimization_results_table.setItem(row, 5, pf_item)

            # Total Trades column
            trades_item = QTableWidgetItem(str(result['total_trades']))
            self._optimization_results_table.setItem(row, 6, trades_item)

            # Avg Return column
            avg_ret_item = QTableWidgetItem(f"{result['avg_return']:.2f}%")
            self._optimization_results_table.setItem(row, 7, avg_ret_item)

        # Show completion message
        QMessageBox.information(
            self,
            "Optimization Complete",
            f"Optimization completed successfully.\n"
            f"Tested {len(results)} indicator/parameter/regime combinations.\n\n"
            f"Best result: {sorted_results[0]['indicator']} in {sorted_results[0]['regime']} "
            f"with score {sorted_results[0]['score']:.2f}"
        )

    def _on_optimization_progress(self, percentage: int, message: str) -> None:
        """Handle optimization progress updates.

        Args:
            percentage: Progress percentage (0-100)
            message: Status message
        """
        self._opt_progress.setValue(percentage)
        logger.debug(f"Optimization progress: {percentage}% - {message}")

    def _on_optimization_error(self, error_message: str) -> None:
        """Handle optimization errors.

        Args:
            error_message: Error description
        """
        # Hide progress bar
        self._opt_progress.setVisible(False)
        self._optimize_btn.setEnabled(True)

        logger.error(f"Optimization error: {error_message}")

        # Show error dialog
        QMessageBox.critical(
            self,
            "Optimization Error",
            f"An error occurred during optimization:\n\n{error_message}"
        )

    def _on_create_regime_set_clicked(self) -> None:
        """Handle create regime set button click.

        Creates a regime-based strategy set from optimization results:
        1. Groups results by regime
        2. Selects top N indicators per regime
        3. Calculates weights based on scores
        4. Generates JSON config
        5. Runs backtest on regime set
        """
        if not hasattr(self, '_optimization_results') or not self._optimization_results:
            QMessageBox.warning(
                self,
                "No Results",
                "Please run indicator optimization first."
            )
            return

        # Ask user for regime set name
        from PyQt6.QtWidgets import QInputDialog

        regime_set_name, ok = QInputDialog.getText(
            self,
            "Create Regime Set",
            "Enter name for regime set:",
            text=f"RegimeSet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        if not ok or not regime_set_name:
            return

        # Ask for top N indicators per regime
        top_n, ok = QInputDialog.getInt(
            self,
            "Top Indicators",
            "Select top N indicators per regime:",
            value=3,
            min=1,
            max=10
        )

        if not ok:
            return

        logger.info(f"Creating regime set '{regime_set_name}' with top {top_n} indicators per regime")

        try:
            # Build regime set
            regime_set = self._build_regime_set(self._optimization_results, top_n)

            # Generate JSON config
            config_dict = self._generate_regime_set_json(regime_set, regime_set_name)

            # Save config to file
            import json
            from pathlib import Path

            config_dir = Path("03_JSON/Trading_Bot/regime_sets")
            config_dir.mkdir(parents=True, exist_ok=True)

            config_path = config_dir / f"{regime_set_name}.json"
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Regime set config saved to: {config_path}")

            # Ask if user wants to backtest the regime set
            from PyQt6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Backtest Regime Set?",
                f"Regime set '{regime_set_name}' created successfully!\n"
                f"Config saved to: {config_path}\n\n"
                f"Do you want to run a backtest on this regime set now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._backtest_regime_set(config_path)

        except Exception as e:
            logger.error(f"Failed to create regime set: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Regime Set Error",
                f"Failed to create regime set:\n\n{str(e)}"
            )

    def _build_regime_set(self, results: list, top_n: int = 3) -> dict:
        """Build regime set from optimization results.

        Args:
            results: List of optimization result dictionaries
            top_n: Number of top indicators to select per regime

        Returns:
            Dictionary mapping regimes to their top indicators with weights
        """
        # Group results by regime
        regime_groups = {}

        for result in results:
            regime = result['regime']
            if regime not in regime_groups:
                regime_groups[regime] = []
            regime_groups[regime].append(result)

        # Build regime set
        regime_set = {}

        for regime, regime_results in regime_groups.items():
            # Skip 'ALL' regime if present
            if regime == 'ALL':
                continue

            # Sort by score (descending)
            sorted_results = sorted(regime_results, key=lambda x: x['score'], reverse=True)

            # Select top N
            top_indicators = sorted_results[:top_n]

            # Calculate weights (normalized scores)
            total_score = sum(ind['score'] for ind in top_indicators)

            weights = {}
            for ind in top_indicators:
                indicator_key = f"{ind['indicator']}_{str(ind['params'])}"
                weight = ind['score'] / total_score if total_score > 0 else 1.0 / len(top_indicators)
                weights[indicator_key] = weight

            regime_set[regime] = {
                'indicators': top_indicators,
                'weights': weights,
                'avg_score': total_score / len(top_indicators) if top_indicators else 0.0
            }

        logger.info(f"Built regime set with {len(regime_set)} regimes")

        return regime_set

    def _generate_regime_set_json(self, regime_set: dict, set_name: str) -> dict:
        """Generate JSON config from regime set.

        Args:
            regime_set: Regime set dictionary
            set_name: Name for the regime set

        Returns:
            JSON config dictionary
        """
        config = {
            "schema_version": "1.0.0",
            "name": set_name,
            "description": f"Auto-generated regime set from optimization results at {datetime.now().isoformat()}",
            "indicators": [],
            "regimes": [],
            "strategies": [],
            "strategy_sets": [],
            "routing": []
        }

        indicator_counter = 0
        strategy_counter = 0

        for regime_name, regime_data in regime_set.items():
            # Add regime definition
            regime_id = f"regime_{regime_name.lower().replace(' ', '_')}"

            config['regimes'].append({
                "id": regime_id,
                "name": regime_name,
                "description": f"Auto-generated regime definition for {regime_name}",
                "conditions": self._generate_regime_conditions(regime_name)
            })

            # Add indicators for this regime
            regime_indicators = []

            for ind_result in regime_data['indicators']:
                indicator_counter += 1
                ind_id = f"ind_{indicator_counter}_{ind_result['indicator'].lower()}"

                config['indicators'].append({
                    "id": ind_id,
                    "type": ind_result['indicator'],
                    "timeframe": "1m",  # Default timeframe
                    "params": ind_result['params']
                })

                regime_indicators.append(ind_id)

            # Add strategy for this regime
            strategy_counter += 1
            strategy_id = f"strategy_{strategy_counter}_{regime_name.lower().replace(' ', '_')}"

            config['strategies'].append({
                "id": strategy_id,
                "name": f"{regime_name} Strategy",
                "description": f"Auto-generated strategy for {regime_name} regime",
                "entry_conditions": self._generate_entry_conditions(regime_indicators),
                "exit_conditions": {
                    "type": "group",
                    "operator": "or",
                    "conditions": [
                        {"type": "stop_loss"},
                        {"type": "take_profit"},
                        {"type": "trailing_stop"}
                    ]
                },
                "risk": {
                    "position_size_pct": 2.0,
                    "stop_loss_pct": 2.0,
                    "take_profit_pct": 6.0
                }
            })

            # Add strategy set
            set_id = f"set_{regime_name.lower().replace(' ', '_')}"

            config['strategy_sets'].append({
                "id": set_id,
                "name": f"{regime_name} Set",
                "strategies": [strategy_id],
                "weights": {strategy_id: 1.0}
            })

            # Add routing rule
            config['routing'].append({
                "regimes": {"all_of": [regime_id]},
                "strategy_set_id": set_id
            })

        return config

    def _generate_regime_conditions(self, regime_name: str) -> dict:
        """Generate conditions for a regime based on its name.

        Args:
            regime_name: Name of the regime (e.g., 'TREND_UP', 'RANGE')

        Returns:
            Condition dictionary
        """
        # Simplified regime conditions
        # In production, these would be more sophisticated

        if "TREND_UP" in regime_name.upper():
            return {
                "type": "group",
                "operator": "and",
                "conditions": [
                    {"type": "condition", "indicator": "adx", "operator": "gt", "value": 25},
                    {"type": "condition", "indicator": "sma_fast", "operator": "gt", "indicator2": "sma_slow"}
                ]
            }
        elif "TREND_DOWN" in regime_name.upper():
            return {
                "type": "group",
                "operator": "and",
                "conditions": [
                    {"type": "condition", "indicator": "adx", "operator": "gt", "value": 25},
                    {"type": "condition", "indicator": "sma_fast", "operator": "lt", "indicator2": "sma_slow"}
                ]
            }
        elif "RANGE" in regime_name.upper():
            return {
                "type": "group",
                "operator": "and",
                "conditions": [
                    {"type": "condition", "indicator": "adx", "operator": "lt", "value": 25},
                    {"type": "condition", "indicator": "bb_width", "operator": "lt", "value": 0.05}
                ]
            }
        else:
            # Default condition
            return {
                "type": "condition",
                "indicator": "close",
                "operator": "gt",
                "value": 0
            }

    def _generate_entry_conditions(self, indicator_ids: list) -> dict:
        """Generate entry conditions using regime indicators.

        Args:
            indicator_ids: List of indicator IDs for this regime

        Returns:
            Entry conditions dictionary
        """
        # Generate combined entry conditions
        # In production, this would be more sophisticated

        conditions = []

        for ind_id in indicator_ids[:3]:  # Use top 3 indicators
            if 'rsi' in ind_id.lower():
                conditions.append({
                    "type": "condition",
                    "indicator": ind_id,
                    "operator": "between",
                    "value": [30, 70]
                })
            elif 'macd' in ind_id.lower():
                conditions.append({
                    "type": "condition",
                    "indicator": f"{ind_id}_histogram",
                    "operator": "gt",
                    "value": 0
                })
            elif 'adx' in ind_id.lower():
                conditions.append({
                    "type": "condition",
                    "indicator": ind_id,
                    "operator": "gt",
                    "value": 20
                })

        if not conditions:
            # Fallback condition
            conditions.append({
                "type": "condition",
                "indicator": "close",
                "operator": "gt",
                "value": 0
            })

        return {
            "type": "group",
            "operator": "and",
            "conditions": conditions
        }

    def _backtest_regime_set(self, config_path: Path) -> None:
        """Run backtest on regime set configuration.

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
            symbol = self.symbol_combo.currentText()
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            capital = self.capital_spin.value()

            # Show progress
            self._run_backtest_btn.setEnabled(False)
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
            self.tab_widget.setCurrentIndex(3)  # Results tab

            self._run_backtest_btn.setEnabled(True)

            logger.info(f"Regime set backtest completed")

        except Exception as e:
            logger.error(f"Regime set backtest failed: {e}", exc_info=True)
            self._run_backtest_btn.setEnabled(True)

            QMessageBox.critical(
                self,
                "Backtest Error",
                f"Failed to backtest regime set:\n\n{str(e)}"
            )

    def _setup_pattern_recognition_tab(self, tab: QWidget) -> None:
        """Setup Pattern Recognition tab.

        Uses the PatternService to find similar historical patterns
        and analyze win probability for current market situation.
        """
        layout = QVBoxLayout(tab)

        # Header
        header_label = QLabel(
            "🔍 Find similar historical patterns to the current chart situation.\n"
            "The system analyzes pattern outcomes to estimate win probability."
        )
        header_label.setWordWrap(True)
        header_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(header_label)

        # Pattern Analysis Settings Group
        settings_group = QGroupBox("Pattern Analysis Settings")
        settings_layout = QFormLayout(settings_group)

        # Window Size
        self.pattern_window_spin = QSpinBox()
        self.pattern_window_spin.setRange(10, 100)
        self.pattern_window_spin.setValue(20)
        self.pattern_window_spin.setToolTip("Number of bars to analyze for pattern matching")
        settings_layout.addRow("Pattern Window Size:", self.pattern_window_spin)

        # Similarity Threshold
        self.pattern_similarity_threshold_spin = QDoubleSpinBox()
        self.pattern_similarity_threshold_spin.setRange(0.5, 0.99)
        self.pattern_similarity_threshold_spin.setSingleStep(0.05)
        self.pattern_similarity_threshold_spin.setValue(0.75)
        self.pattern_similarity_threshold_spin.setToolTip("Minimum similarity score (0.5-0.99)")
        settings_layout.addRow("Similarity Threshold:", self.pattern_similarity_threshold_spin)

        # Min Similar Patterns
        self.pattern_min_matches_spin = QSpinBox()
        self.pattern_min_matches_spin.setRange(3, 50)
        self.pattern_min_matches_spin.setValue(5)
        self.pattern_min_matches_spin.setToolTip("Minimum number of similar patterns needed")
        settings_layout.addRow("Min Similar Patterns:", self.pattern_min_matches_spin)

        # Signal Direction
        self.pattern_signal_direction_combo = QComboBox()
        self.pattern_signal_direction_combo.addItems(["LONG", "SHORT"])
        self.pattern_signal_direction_combo.setCurrentIndex(0)
        settings_layout.addRow("Signal Direction:", self.pattern_signal_direction_combo)

        # Cross-Symbol Search
        self.pattern_cross_symbol_cb = QCheckBox("Search across all symbols")
        self.pattern_cross_symbol_cb.setChecked(True)
        self.pattern_cross_symbol_cb.setToolTip("Search patterns from all symbols (recommended)")
        settings_layout.addRow("", self.pattern_cross_symbol_cb)

        layout.addWidget(settings_group)

        # Analyze Button
        self.pattern_analyze_btn = QPushButton("🔍 Analyze Current Pattern")
        self.pattern_analyze_btn.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; "
            "padding: 10px; font-size: 14px;"
        )
        self.pattern_analyze_btn.clicked.connect(self._on_pattern_analyze_clicked)
        layout.addWidget(self.pattern_analyze_btn)

        # Progress bar
        self.pattern_progress = QProgressBar()
        self.pattern_progress.setVisible(False)
        layout.addWidget(self.pattern_progress)

        # Results Group
        results_group = QGroupBox("Pattern Analysis Results")
        results_layout = QVBoxLayout(results_group)

        # Summary Label
        self.pattern_summary_label = QLabel("No analysis performed yet")
        self.pattern_summary_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; "
            "background-color: #f5f5f5; border-radius: 5px;"
        )
        self.pattern_summary_label.setWordWrap(True)
        results_layout.addWidget(self.pattern_summary_label)

        # Statistics Grid
        stats_grid = QFormLayout()
        self.pattern_matches_count_label = QLabel("-")
        self.pattern_win_rate_label = QLabel("-")
        self.pattern_avg_return_label = QLabel("-")
        self.pattern_confidence_label = QLabel("-")
        self.pattern_avg_similarity_label = QLabel("-")
        self.pattern_recommendation_label = QLabel("-")

        stats_grid.addRow("Similar Patterns Found:", self.pattern_matches_count_label)
        stats_grid.addRow("Win Rate:", self.pattern_win_rate_label)
        stats_grid.addRow("Avg Return:", self.pattern_avg_return_label)
        stats_grid.addRow("Confidence:", self.pattern_confidence_label)
        stats_grid.addRow("Avg Similarity:", self.pattern_avg_similarity_label)
        stats_grid.addRow("Recommendation:", self.pattern_recommendation_label)

        results_layout.addLayout(stats_grid)
        layout.addWidget(results_group)

        # Similar Patterns Table
        patterns_table_group = QGroupBox("Top Similar Patterns")
        patterns_table_layout = QVBoxLayout(patterns_table_group)

        self.similar_patterns_table = QTableWidget()
        self.similar_patterns_table.setColumnCount(8)
        self.similar_patterns_table.setHorizontalHeaderLabels([
            "Symbol", "Timeframe", "Date", "Similarity",
            "Trend", "Win", "Return %", "Outcome"
        ])
        self.similar_patterns_table.horizontalHeader().setStretchLastSection(True)
        self.similar_patterns_table.setAlternatingRowColors(True)
        self.similar_patterns_table.setSortingEnabled(True)
        self.similar_patterns_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.similar_patterns_table.itemDoubleClicked.connect(self._on_pattern_double_clicked)

        patterns_table_layout.addWidget(self.similar_patterns_table)
        layout.addWidget(patterns_table_group)

        # Info label
        info_label = QLabel(
            "💡 Tip: Double-click a pattern to see detailed chart comparison. "
            "Higher similarity scores (>0.8) indicate very similar market conditions."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        layout.addWidget(info_label)

    def _on_pattern_analyze_clicked(self) -> None:
        """Handle pattern analyze button click."""
        try:
            # Get current chart data
            if not hasattr(self.parent(), 'chart_widget') or not hasattr(self.parent().chart_widget, 'data'):
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No chart data available for pattern analysis."
                )
                return

            chart_data = self.parent().chart_widget.data
            if chart_data is None or len(chart_data) == 0:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "Chart data is empty."
                )
                return

            # Get settings
            window_size = self.pattern_window_spin.value()
            similarity_threshold = self.pattern_similarity_threshold_spin.value()
            min_matches = self.pattern_min_matches_spin.value()
            signal_direction = self.pattern_signal_direction_combo.currentText().lower()
            cross_symbol = self.pattern_cross_symbol_cb.isChecked()

            # Show progress
            self.pattern_progress.setVisible(True)
            self.pattern_progress.setRange(0, 0)  # Indeterminate
            self.pattern_analyze_btn.setEnabled(False)

            # Convert chart_data to bars
            from src.core.market_data.types import HistoricalBar
            bars = []
            for timestamp, row in chart_data.tail(window_size + 50).iterrows():
                bar = HistoricalBar(
                    timestamp=timestamp,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row.get('volume', 0))
                )
                bars.append(bar)

            # Get symbol and timeframe
            symbol = getattr(self.parent().chart_widget, 'current_symbol', 'UNKNOWN')
            timeframe = getattr(self.parent().chart_widget, 'timeframe', '1m')

            # Run pattern analysis in background
            import asyncio
            from src.core.pattern_db.pattern_service import PatternService

            async def run_analysis():
                service = PatternService(
                    window_size=window_size,
                    min_similar_patterns=min_matches,
                    similarity_threshold=similarity_threshold
                )
                await service.initialize()
                return await service.analyze_signal(
                    bars=bars,
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_direction=signal_direction,
                    cross_symbol_search=cross_symbol
                )

            # Run in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create task
                task = asyncio.create_task(run_analysis())
                # Wait for completion (blocking UI is OK for analysis)
                loop.run_until_complete(task)
                result = task.result()
            else:
                result = loop.run_until_complete(run_analysis())

            # Display results
            self._display_pattern_analysis_results(result)

            # Hide progress
            self.pattern_progress.setVisible(False)
            self.pattern_analyze_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Pattern analysis failed:\n{e}"
            )
            self.pattern_progress.setVisible(False)
            self.pattern_analyze_btn.setEnabled(True)

    def _display_pattern_analysis_results(self, analysis) -> None:
        """Display pattern analysis results.

        Args:
            analysis: PatternAnalysis object or None
        """
        if analysis is None:
            self.pattern_summary_label.setText("❌ Analysis failed - not enough data")
            self.pattern_summary_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; padding: 10px; "
                "background-color: #ffebee; border-radius: 5px;"
            )
            return

        # Update summary
        recommendation_colors = {
            "strong_buy": "#4caf50",
            "buy": "#8bc34a",
            "neutral": "#ffeb3b",
            "avoid": "#ff9800",
            "strong_avoid": "#f44336"
        }
        bg_color = recommendation_colors.get(analysis.recommendation, "#f5f5f5")

        self.pattern_summary_label.setText(
            f"✓ Analysis Complete: {analysis.recommendation.upper().replace('_', ' ')}"
        )
        self.pattern_summary_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; padding: 10px; "
            f"background-color: {bg_color}; border-radius: 5px; color: white;"
        )

        # Update statistics
        self.pattern_matches_count_label.setText(str(analysis.similar_patterns_count))
        self.pattern_win_rate_label.setText(f"{analysis.win_rate:.1%}")
        self.pattern_avg_return_label.setText(f"{analysis.avg_return:+.2f}%")
        self.pattern_confidence_label.setText(f"{analysis.confidence:.1%}")
        self.pattern_avg_similarity_label.setText(f"{analysis.avg_similarity_score:.2f}")
        self.pattern_recommendation_label.setText(analysis.recommendation.replace('_', ' ').title())

        # Update table
        self.similar_patterns_table.setRowCount(0)
        for match in analysis.best_matches[:20]:  # Show top 20
            row = self.similar_patterns_table.rowCount()
            self.similar_patterns_table.insertRow(row)

            self.similar_patterns_table.setItem(row, 0, QTableWidgetItem(match.symbol))
            self.similar_patterns_table.setItem(row, 1, QTableWidgetItem(match.timeframe))
            self.similar_patterns_table.setItem(row, 2, QTableWidgetItem(match.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(match.timestamp, 'strftime') else str(match.timestamp)))
            self.similar_patterns_table.setItem(row, 3, QTableWidgetItem(f"{match.score:.3f}"))
            self.similar_patterns_table.setItem(row, 4, QTableWidgetItem(match.trend_direction.upper()))
            self.similar_patterns_table.setItem(row, 5, QTableWidgetItem("✓" if match.was_profitable else "✗"))
            self.similar_patterns_table.setItem(row, 6, QTableWidgetItem(f"{match.return_pct:+.2f}%"))

            outcome = "PROFIT" if match.was_profitable else "LOSS"
            outcome_item = QTableWidgetItem(outcome)
            outcome_item.setForeground(Qt.GlobalColor.green if match.was_profitable else Qt.GlobalColor.red)
            self.similar_patterns_table.setItem(row, 7, outcome_item)

        logger.info(f"Pattern analysis displayed: {analysis.similar_patterns_count} matches, {analysis.win_rate:.1%} win rate")

    def _on_pattern_double_clicked(self, item) -> None:
        """Handle pattern table double-click - show detailed comparison."""
        row = item.row()
        symbol = self.similar_patterns_table.item(row, 0).text()
        date = self.similar_patterns_table.item(row, 2).text()
        similarity = self.similar_patterns_table.item(row, 3).text()

        QMessageBox.information(
            self,
            "Pattern Details",
            f"Similar Pattern Details:\n\n"
            f"Symbol: {symbol}\n"
            f"Date: {date}\n"
            f"Similarity: {similarity}\n\n"
            f"Feature: Chart overlay comparison coming soon..."
        )

    def _on_report_clicked(self) -> None:
        if not self._result:
            QMessageBox.warning(self, "No Data", "Run analysis first")
            return

        # Ask for save location
        default_name = f"entry_analysis_{self._symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path.home() / f"{default_name}.md"),
            "Markdown (*.md);;JSON (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            from src.analysis.visible_chart.report_generator import (
                ReportGenerator,
                create_report_from_analysis,
            )

            # Create report data
            report_data = create_report_from_analysis(
                analysis=self._result,
                symbol=self._symbol,
                timeframe=self._timeframe,
                validation=self._validation_result,
            )

            generator = ReportGenerator()
            path = Path(file_path)

            if path.suffix == ".json":
                import json
                content = generator.generate_json(report_data)
                path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            else:
                content = generator.generate_markdown(report_data)
                path.write_text(content, encoding="utf-8")

            QMessageBox.information(self, "Report Saved", f"Report saved to:\n{path}")
            logger.info("Report saved: %s", path)

        except Exception as e:
            logger.exception("Report generation failed")
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{e}")
