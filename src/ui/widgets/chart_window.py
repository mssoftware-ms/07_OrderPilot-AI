"""Popup Chart Window for OrderPilot-AI.

Provides a dedicated window for viewing charts with full screen support.
Can be detached from the main application for multi-monitor setups.
"""

import logging
import json
from typing import Optional

from PyQt6.QtCore import Qt, QSettings, pyqtSignal, QDate
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QSplitter, QTabWidget,
    QFormLayout, QComboBox, QDateEdit, QDoubleSpinBox, QPushButton,
    QSpinBox, QCheckBox, QGroupBox, QHBoxLayout, QLabel, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QCloseEvent
from datetime import datetime

from .embedded_tradingview_chart import EmbeddedTradingViewChart
from src.common.event_bus import event_bus, EventType, ExecutionEvent, OrderEvent

logger = logging.getLogger(__name__)


class ChartWindow(QMainWindow):
    """Popup window for displaying a single chart."""

    # Signals
    window_closed = pyqtSignal(str)  # Emitted when window closes, passes symbol

    def __init__(self, symbol: str, history_manager=None, parent=None):
        """Initialize chart window.

        Args:
            symbol: Trading symbol to display
            history_manager: HistoryManager instance for loading data
            parent: Parent widget
        """
        super().__init__(parent)

        self.symbol = symbol
        self.history_manager = history_manager
        self.settings = QSettings("OrderPilot", "TradingApp")

        # Window configuration
        self.setWindowTitle(f"Chart - {symbol}")
        self.setMinimumSize(800, 600)

        # Create central widget with splitter (like TradingView)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter: Chart above, Panels below
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        # === TOP: Chart Widget ===
        self.chart_widget = EmbeddedTradingViewChart(history_manager=history_manager)
        self.splitter.addWidget(self.chart_widget)

        # Set symbol in chart (only if WebEngine is available)
        self.chart_widget.current_symbol = symbol
        if hasattr(self.chart_widget, 'symbol_combo'):
            self.chart_widget.symbol_combo.setCurrentText(symbol)

        # === BOTTOM: Control Panels (wie TradingView) ===
        # Connect toggle button from chart toolbar to panel visibility
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            self.chart_widget.toggle_panel_button.clicked.connect(self._toggle_bottom_panel)

        # ===== ACTUAL PANEL (can be hidden) =====
        self.bottom_panel = self._create_bottom_panel()
        self.splitter.addWidget(self.bottom_panel)

        # Set initial splitter sizes: 70% chart, 30% panels
        self.splitter.setStretchFactor(0, 7)
        self.splitter.setStretchFactor(1, 3)

        main_layout.addWidget(self.splitter)

        # Load window geometry from settings
        self._load_window_state()

        # ===== CRITICAL: WIRE EVENT BUS FOR LIVE TRADE MARKERS =====
        # Subscribe to execution and order events for real-time chart markers
        self._setup_event_subscriptions()

        logger.info(f"ChartWindow created for {symbol}")

    def _create_bottom_panel(self) -> QWidget:
        """Create bottom panel with tabs (like TradingView).

        Returns:
            QWidget containing tabbed panels
        """
        panel_container = QWidget()
        panel_layout = QVBoxLayout(panel_container)
        panel_layout.setContentsMargins(5, 5, 5, 5)

        # Tabs für verschiedene Funktionen
        self.panel_tabs = QTabWidget()

        # Tab 1: Strategy Configuration
        self.strategy_tab = self._create_strategy_tab()
        self.panel_tabs.addTab(self.strategy_tab, "⚙️ Strategy")

        # Tab 2: Backtest
        self.backtest_tab = self._create_backtest_tab()
        self.panel_tabs.addTab(self.backtest_tab, "📈 Backtest")

        # Tab 3: Parameter Optimization
        self.optimization_tab = self._create_optimization_tab()
        self.panel_tabs.addTab(self.optimization_tab, "🔧 Optimize")

        # Tab 4: Results
        self.results_tab = self._create_results_tab()
        self.panel_tabs.addTab(self.results_tab, "📊 Results")

        panel_layout.addWidget(self.panel_tabs)

        return panel_container

    def _toggle_bottom_panel(self):
        """Toggle visibility of bottom panel.

        Now controlled by toolbar button in chart_widget.
        Button state (checked/unchecked) controls visibility.
        """
        # Get button from chart toolbar
        if not hasattr(self.chart_widget, 'toggle_panel_button'):
            return

        button = self.chart_widget.toggle_panel_button
        is_checked = button.isChecked()

        if is_checked:
            # Button checked = Show panel
            self.bottom_panel.show()
            button.setText("▼ Panel")
        else:
            # Button unchecked = Hide panel
            self.bottom_panel.hide()
            button.setText("▲ Panel")

    def _create_strategy_tab(self) -> QWidget:
        """Create strategy configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Strategy Selection
        strategy_group = QGroupBox("Strategy Selection")
        strategy_layout = QFormLayout()

        self.strategy_combo = QComboBox()

        # ===== LOAD REAL STRATEGIES FROM YAML FILES =====
        from src.core.strategy.loader import get_strategy_loader

        self.strategy_loader = get_strategy_loader()
        available_strategies = self.strategy_loader.discover_strategies()

        if available_strategies:
            # Add real strategies from YAML files
            for strategy_name in available_strategies:
                info = self.strategy_loader.get_strategy_info(strategy_name)
                if info:
                    display_name = f"{info['name']} ({info['category']})"
                    self.strategy_combo.addItem(display_name, strategy_name)  # Store file name as data
                else:
                    self.strategy_combo.addItem(strategy_name, strategy_name)

            logger.info(f"✅ Loaded {len(available_strategies)} real strategies from YAML files")
        else:
            # Fallback to hardcoded strategies if no YAML files found
            logger.warning("⚠️ No YAML strategies found, using fallback list")
            self.strategy_combo.addItems([
                "MACD Crossover",
                "RSI Mean Reversion",
                "Bollinger Bands",
                "Moving Average",
                "Custom Strategy"
            ])

        # Connect strategy selection change
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_selected)

        strategy_layout.addRow("Strategy:", self.strategy_combo)

        # Strategy Parameters (dynamic based on selection)
        self.param_container = QWidget()
        self.param_layout = QFormLayout(self.param_container)

        # Example: MACD parameters
        self.fast_period = QSpinBox()
        self.fast_period.setRange(5, 50)
        self.fast_period.setValue(12)
        self.param_layout.addRow("Fast Period:", self.fast_period)

        self.slow_period = QSpinBox()
        self.slow_period.setRange(10, 100)
        self.slow_period.setValue(26)
        self.param_layout.addRow("Slow Period:", self.slow_period)

        self.signal_period = QSpinBox()
        self.signal_period.setRange(5, 30)
        self.signal_period.setValue(9)
        self.param_layout.addRow("Signal Period:", self.signal_period)

        strategy_layout.addRow(self.param_container)

        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # Risk Management
        risk_group = QGroupBox("Risk Management")
        risk_layout = QFormLayout()

        self.stop_loss = QDoubleSpinBox()
        self.stop_loss.setRange(0.1, 10.0)
        self.stop_loss.setValue(2.0)
        self.stop_loss.setSuffix("%")
        risk_layout.addRow("Stop Loss:", self.stop_loss)

        self.take_profit = QDoubleSpinBox()
        self.take_profit.setRange(0.1, 20.0)
        self.take_profit.setValue(4.0)
        self.take_profit.setSuffix("%")
        risk_layout.addRow("Take Profit:", self.take_profit)

        self.position_size = QDoubleSpinBox()
        self.position_size.setRange(0.1, 100.0)
        self.position_size.setValue(10.0)
        self.position_size.setSuffix("%")
        risk_layout.addRow("Position Size:", self.position_size)

        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)

        # Apply Button
        apply_btn = QPushButton("📌 Apply Strategy to Chart")
        apply_btn.clicked.connect(self._apply_strategy)
        layout.addWidget(apply_btn)

        # ===== LIVE STREAM BUTTON =====
        stream_group = QGroupBox("Live Market Data")
        stream_layout = QVBoxLayout()

        self.stream_status_label = QLabel("Status: Not Connected")
        self.stream_status_label.setStyleSheet("color: #888;")
        stream_layout.addWidget(self.stream_status_label)

        stream_btn_layout = QHBoxLayout()

        self.start_stream_btn = QPushButton("📡 Start Live Stream")
        self.start_stream_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        self.start_stream_btn.clicked.connect(self._start_live_stream)
        stream_btn_layout.addWidget(self.start_stream_btn)

        self.stop_stream_btn = QPushButton("⏹ Stop Stream")
        self.stop_stream_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        self.stop_stream_btn.clicked.connect(self._stop_live_stream)
        self.stop_stream_btn.setEnabled(False)
        stream_btn_layout.addWidget(self.stop_stream_btn)

        stream_layout.addLayout(stream_btn_layout)
        stream_group.setLayout(stream_layout)
        layout.addWidget(stream_group)

        layout.addStretch()

        return widget

    def _create_backtest_tab(self) -> QWidget:
        """Create backtest controls tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Backtest Configuration
        config_group = QGroupBox("Backtest Configuration")
        config_layout = QFormLayout()

        # Date Range
        self.backtest_start_date = QDateEdit()
        self.backtest_start_date.setDate(QDate.currentDate().addYears(-1))
        self.backtest_start_date.setCalendarPopup(True)
        config_layout.addRow("Start Date:", self.backtest_start_date)

        self.backtest_end_date = QDateEdit()
        self.backtest_end_date.setDate(QDate.currentDate())
        self.backtest_end_date.setCalendarPopup(True)
        config_layout.addRow("End Date:", self.backtest_end_date)

        # Initial Capital
        self.initial_capital = QDoubleSpinBox()
        self.initial_capital.setRange(1000, 1000000)
        self.initial_capital.setValue(10000)
        self.initial_capital.setPrefix("€")
        config_layout.addRow("Initial Capital:", self.initial_capital)

        # AI Analysis
        self.enable_ai_analysis = QCheckBox("Enable AI Analysis")
        self.enable_ai_analysis.setChecked(True)
        config_layout.addRow("AI Analysis:", self.enable_ai_analysis)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Run Backtest Button
        run_btn = QPushButton("🚀 Run Backtest on Chart")
        run_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        run_btn.clicked.connect(self._run_backtest)
        layout.addWidget(run_btn)

        # Visualization Options
        viz_group = QGroupBox("Visualization Options")
        viz_layout = QVBoxLayout()

        self.show_entry_markers = QCheckBox("Show Entry Points")
        self.show_entry_markers.setChecked(True)
        viz_layout.addWidget(self.show_entry_markers)

        self.show_exit_markers = QCheckBox("Show Exit Points")
        self.show_exit_markers.setChecked(True)
        viz_layout.addWidget(self.show_exit_markers)

        self.show_stop_loss = QCheckBox("Show Stop Loss Levels")
        self.show_stop_loss.setChecked(True)
        viz_layout.addWidget(self.show_stop_loss)

        self.show_take_profit = QCheckBox("Show Take Profit Levels")
        self.show_take_profit.setChecked(True)
        viz_layout.addWidget(self.show_take_profit)

        self.show_equity_curve = QCheckBox("Show Equity Curve")
        self.show_equity_curve.setChecked(False)
        viz_layout.addWidget(self.show_equity_curve)

        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)

        layout.addStretch()

        return widget

    def _create_optimization_tab(self) -> QWidget:
        """Create parameter optimization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Parameter Ranges
        ranges_group = QGroupBox("Parameter Ranges")
        ranges_layout = QFormLayout()

        # Fast Period Range
        fast_range_widget = QWidget()
        fast_range_layout = QHBoxLayout(fast_range_widget)
        fast_range_layout.setContentsMargins(0, 0, 0, 0)

        self.opt_fast_min = QSpinBox()
        self.opt_fast_min.setRange(5, 50)
        self.opt_fast_min.setValue(10)
        self.opt_fast_min.setPrefix("Min: ")
        fast_range_layout.addWidget(self.opt_fast_min)

        self.opt_fast_max = QSpinBox()
        self.opt_fast_max.setRange(5, 50)
        self.opt_fast_max.setValue(20)
        self.opt_fast_max.setPrefix("Max: ")
        fast_range_layout.addWidget(self.opt_fast_max)

        ranges_layout.addRow("Fast Period:", fast_range_widget)

        # Slow Period Range
        slow_range_widget = QWidget()
        slow_range_layout = QHBoxLayout(slow_range_widget)
        slow_range_layout.setContentsMargins(0, 0, 0, 0)

        self.opt_slow_min = QSpinBox()
        self.opt_slow_min.setRange(10, 100)
        self.opt_slow_min.setValue(20)
        self.opt_slow_min.setPrefix("Min: ")
        slow_range_layout.addWidget(self.opt_slow_min)

        self.opt_slow_max = QSpinBox()
        self.opt_slow_max.setRange(10, 100)
        self.opt_slow_max.setValue(40)
        self.opt_slow_max.setPrefix("Max: ")
        slow_range_layout.addWidget(self.opt_slow_max)

        ranges_layout.addRow("Slow Period:", slow_range_widget)

        # Max Iterations
        self.max_iterations = QSpinBox()
        self.max_iterations.setRange(10, 1000)
        self.max_iterations.setValue(100)
        ranges_layout.addRow("Max Iterations:", self.max_iterations)

        ranges_group.setLayout(ranges_layout)
        layout.addWidget(ranges_group)

        # Optimization Options
        opt_group = QGroupBox("Optimization Options")
        opt_layout = QFormLayout()

        self.opt_metric = QComboBox()
        self.opt_metric.addItems([
            "Sharpe Ratio",
            "Total Return",
            "Profit Factor",
            "Win Rate"
        ])
        opt_layout.addRow("Optimize For:", self.opt_metric)

        self.use_ai_guidance = QCheckBox("Use AI Guidance")
        self.use_ai_guidance.setChecked(True)
        opt_layout.addRow("AI Guidance:", self.use_ai_guidance)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # Start Optimization Button
        start_btn = QPushButton("🎯 Start Optimization")
        start_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        start_btn.clicked.connect(self._start_optimization)
        layout.addWidget(start_btn)

        layout.addStretch()

        return widget

    def _create_results_tab(self) -> QWidget:
        """Create results display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Results Summary
        summary_group = QGroupBox("Results Summary")
        summary_layout = QVBoxLayout()

        self.results_summary = QLabel("No results yet. Run a backtest or optimization.")
        self.results_summary.setWordWrap(True)
        self.results_summary.setStyleSheet("padding: 10px;")
        summary_layout.addWidget(self.results_summary)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Metrics Table
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QVBoxLayout()

        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setAlternatingRowColors(True)
        metrics_layout.addWidget(self.metrics_table)

        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)

        # AI Analysis
        ai_group = QGroupBox("AI Analysis")
        ai_layout = QVBoxLayout()

        self.ai_analysis_text = QTextEdit()
        self.ai_analysis_text.setReadOnly(True)
        self.ai_analysis_text.setPlaceholderText("AI analysis will appear here...")
        ai_layout.addWidget(self.ai_analysis_text)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        return widget

    def _on_strategy_selected(self, index: int):
        """Handle strategy selection change.

        Args:
            index: Selected combo box index
        """
        strategy_file_name = self.strategy_combo.currentData()
        if not strategy_file_name:
            strategy_file_name = self.strategy_combo.currentText()

        logger.info(f"Strategy selected: {strategy_file_name}")

        # Load strategy definition
        if hasattr(self, 'strategy_loader'):
            strategy_def = self.strategy_loader.load_strategy(strategy_file_name)
            if strategy_def:
                self.current_strategy_def = strategy_def
                logger.info(f"✅ Loaded strategy: {strategy_def.name}")

                # TODO: Update parameter controls based on strategy definition
                # For now, keep existing MACD parameters
            else:
                logger.warning(f"⚠️ Could not load strategy: {strategy_file_name}")
                self.current_strategy_def = None
        else:
            self.current_strategy_def = None

    def _apply_strategy(self):
        """Apply selected strategy to chart."""
        strategy = self.strategy_combo.currentText()
        logger.info(f"Applying strategy: {strategy} to chart {self.symbol}")
        # TODO: Implement strategy application with visual markers

    def _start_live_stream(self):
        """Start live market data stream for this symbol.

        CRITICAL: This starts REAL WebSocket streaming from Alpaca.
        Events are emitted to event_bus as MARKET_BAR events.
        ChartWindow subscribes to these events to update the chart in real-time.
        """
        import os
        import asyncio
        from src.core.market_data.alpaca_stream import AlpacaStreamClient

        logger.info(f"Starting live stream for {self.symbol}")

        # Get Alpaca credentials (from ConfigManager)
        from src.config.loader import config_manager
        api_key = config_manager.get_credential("alpaca_api_key")
        api_secret = config_manager.get_credential("alpaca_api_secret")

        if not api_key or not api_secret:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Missing Credentials",
                "Alpaca API credentials not found.\n\n"
                "Please set APCA_API_KEY_ID and APCA_API_SECRET_KEY in your .env file."
            )
            logger.warning("Live stream failed: Alpaca credentials not configured")
            return

        # Check if stream already running
        if hasattr(self, 'stream_client') and self.stream_client is not None:
            logger.warning(f"Stream already running for {self.symbol}")
            return

        try:
            # Create stream client
            self.stream_client = AlpacaStreamClient(
                api_key=api_key,
                api_secret=api_secret,
                paper=True,  # ALWAYS use paper for safety
                feed="iex"   # Free tier (30 symbols limit)
            )

            # Start async connection and subscription
            async def start_stream():
                try:
                    # Connect to WebSocket
                    connected = await self.stream_client.connect()
                    if not connected:
                        raise RuntimeError("Failed to connect to Alpaca stream")

                    # Subscribe to symbols (includes bars, trades, quotes)
                    await self.stream_client.subscribe([self.symbol])

                    logger.info(f"✅ Live stream started for {self.symbol}")

                    # Update UI on main thread using Qt signal/slot
                    from PyQt6.QtCore import QMetaObject, Qt
                    def update_ui():
                        self.stream_status_label.setText(f"Status: Connected - Streaming {self.symbol}")
                        self.stream_status_label.setStyleSheet("color: #28a745; font-weight: bold;")
                        self.start_stream_btn.setEnabled(False)
                        self.stop_stream_btn.setEnabled(True)

                    QMetaObject.invokeMethod(
                        self.stream_status_label,
                        lambda: update_ui(),
                        Qt.ConnectionType.QueuedConnection
                    )

                except Exception as e:
                    logger.error(f"Stream start failed: {e}", exc_info=True)

                    def show_error():
                        self.stream_status_label.setText(f"Status: Error - {str(e)[:50]}")
                        self.stream_status_label.setStyleSheet("color: #dc3545;")

                    from PyQt6.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(
                        self.stream_status_label,
                        lambda: show_error(),
                        Qt.ConnectionType.QueuedConnection
                    )
                    raise

            # Get or create event loop (compatible with Qt)
            try:
                loop = asyncio.get_running_loop()
                logger.info("Using existing event loop")
            except RuntimeError:
                # Check if we have qasync integration
                try:
                    from qasync import QEventLoop
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        loop = QEventLoop(app)
                        asyncio.set_event_loop(loop)
                        logger.info("Using qasync event loop")
                    else:
                        # Fallback to standard asyncio loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        logger.warning("Using standard asyncio loop (qasync recommended)")
                except ImportError:
                    # No qasync - use standard loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    logger.warning("qasync not available - using standard asyncio loop")

            # Run async task
            asyncio.create_task(start_stream())

            logger.info(f"Live stream task created for {self.symbol}")

        except Exception as e:
            logger.error(f"Failed to start live stream: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "Stream Error",
                f"Failed to start live stream:\n\n{str(e)}"
            )

    def _stop_live_stream(self):
        """Stop live market data stream."""
        import asyncio

        logger.info(f"Stopping live stream for {self.symbol}")

        if not hasattr(self, 'stream_client') or self.stream_client is None:
            logger.warning("No stream client to stop")
            return

        try:
            async def stop_stream():
                try:
                    # Unsubscribe from symbols
                    await self.stream_client.unsubscribe([self.symbol])

                    # Disconnect
                    await self.stream_client.disconnect()

                    logger.info(f"✅ Live stream stopped for {self.symbol}")

                    # Update UI using Qt signal/slot
                    from PyQt6.QtCore import QMetaObject, Qt
                    def update_ui():
                        self.stream_status_label.setText("Status: Disconnected")
                        self.stream_status_label.setStyleSheet("color: #888;")
                        self.start_stream_btn.setEnabled(True)
                        self.stop_stream_btn.setEnabled(False)

                    QMetaObject.invokeMethod(
                        self.stream_status_label,
                        lambda: update_ui(),
                        Qt.ConnectionType.QueuedConnection
                    )

                except Exception as e:
                    logger.error(f"Stream stop failed: {e}", exc_info=True)
                    raise
                finally:
                    self.stream_client = None

            # Get event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Try to get qasync loop if available
                try:
                    from qasync import QEventLoop
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        loop = QEventLoop(app)
                        asyncio.set_event_loop(loop)
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except ImportError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

            # Run async task
            asyncio.create_task(stop_stream())

        except Exception as e:
            logger.error(f"Failed to stop live stream: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Stream Error",
                f"Failed to stop stream cleanly:\n\n{str(e)}"
            )
            # Force cleanup
            self.stream_client = None
            self.stream_status_label.setText("Status: Error (Force Stopped)")
            self.stream_status_label.setStyleSheet("color: #dc3545;")
            self.start_stream_btn.setEnabled(True)
            self.stop_stream_btn.setEnabled(False)

    def _run_backtest(self):
        """Run REAL backtest with LIVE chart data.

        Uses the ACTUAL data currently displayed in the chart for backtesting.
        NO mock data, NO artificial results, NO demo mode!
        This is a REAL, FUNCTIONING live system!
        """
        from src.core.backtesting.backtrader_integration import (
            BacktestConfig, BacktraderIntegration
        )
        from src.core.market_data.history_provider import Timeframe
        from src.core.strategy.engine import StrategyConfig, StrategyType
        from src.core.indicators.engine import IndicatorConfig, IndicatorType
        from decimal import Decimal
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog
        from PyQt6.QtCore import Qt
        import pandas as pd

        logger.info(f"Starting REAL backtest for {self.symbol} with LIVE chart data")

        try:
            # ===== STEP 1: GET REAL CHART DATA =====
            # Use the ACTUAL data displayed in the chart (NO fetching new data!)
            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
                QMessageBox.warning(
                    self,
                    "No Chart Data",
                    "Please load chart data first before running a backtest!\n\n"
                    "Click '📊 Load Chart' button in the chart toolbar."
                )
                return

            chart_data = self.chart_widget.data.copy()
            logger.info(f"Using LIVE chart data: {len(chart_data)} bars from {chart_data.index[0]} to {chart_data.index[-1]}")

            # Create progress dialog
            progress = QProgressDialog(
                f"Running backtest on {len(chart_data)} real market bars...",
                "Cancel",
                0, 0,
                self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Running REAL Backtest")
            progress.show()

            # ===== STEP 2: GET BACKTEST PARAMETERS FROM UI =====
            # Get dates from UI (use chart data range if not specified)
            start_date = self.backtest_start_date.date().toPyDate()
            end_date = self.backtest_end_date.date().toPyDate()
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            # Filter chart data to backtest date range
            mask = (chart_data.index >= start_datetime) & (chart_data.index <= end_datetime)
            backtest_data = chart_data[mask]

            if backtest_data.empty:
                progress.close()
                QMessageBox.warning(
                    self,
                    "No Data in Date Range",
                    f"No chart data found between {start_date} and {end_date}.\n\n"
                    f"Available data: {chart_data.index[0].date()} to {chart_data.index[-1].date()}"
                )
                return

            logger.info(f"Backtest data filtered: {len(backtest_data)} bars from {backtest_data.index[0]} to {backtest_data.index[-1]}")

            # Get initial capital from UI
            initial_cash = Decimal(str(self.initial_capital.value()))

            # ===== STEP 3: CREATE STRATEGY CONFIG FROM UI =====
            strategy_config = self._create_strategy_config_from_ui()

            # ===== STEP 4: RUN REAL BACKTEST =====
            # Create backtest configuration
            backtest_config = BacktestConfig(
                start_date=start_datetime,
                end_date=end_datetime,
                initial_cash=initial_cash,
                commission=0.001,  # 0.1%
                slippage=0.0005,   # 0.05%
                timeframe=Timeframe.DAY,  # TODO: Detect from chart timeframe
                symbols=[self.symbol],
                strategies=[strategy_config]
            )

            # Run REAL backtest with BacktraderIntegration
            if not self.history_manager:
                raise ValueError("No history manager available for backtest")

            backtrader = BacktraderIntegration(
                history_manager=self.history_manager,
                config=backtest_config
            )

            # Execute backtest with REAL data
            try:
                result = backtrader.run()
            except Exception as backtest_error:
                progress.close()
                logger.error(f"Backtest execution error: {backtest_error}", exc_info=True)

                # ===== NO MOCK FALLBACK - Show error to user =====
                QMessageBox.critical(
                    self, "Backtest Failed",
                    f"Backtest execution failed:\n\n{str(backtest_error)}\n\n"
                    f"Common causes:\n"
                    f"• No market data for symbol/date range\n"
                    f"• Strategy compilation error\n"
                    f"• Invalid parameters\n"
                    f"• Network error loading historical data\n\n"
                    f"Check logs for detailed error information."
                )
                return  # Exit - NO mock fallback!

            progress.close()

            # ===== STEP 5: VALIDATE RESULTS =====
            if not result:
                QMessageBox.warning(
                    self,
                    "Backtest Failed",
                    "No backtest result returned. Check logs for details."
                )
                return

            logger.info(f"✅ Backtest completed: {result.metrics.total_trades} trades, "
                       f"Win rate: {result.metrics.win_rate:.1%}, "
                       f"Total P&L: €{result.total_pnl:,.2f} ({result.total_pnl_pct:+.2f}%)")

            # ===== STEP 6: DISPLAY REAL RESULTS =====
            self._display_backtest_results(result)

            # ===== STEP 7: ADD REAL TRADE MARKERS TO CHART =====
            self._add_trade_markers_to_chart(result)

            # Switch to Results tab
            self.panel_tabs.setCurrentWidget(self.results_tab)

            # Show bottom panel if hidden
            if not self.bottom_panel.isVisible():
                # Set button to checked state to show panel
                if hasattr(self.chart_widget, 'toggle_panel_button'):
                    self.chart_widget.toggle_panel_button.setChecked(True)
                self._toggle_bottom_panel()

        except Exception as e:
            logger.error(f"Backtest execution failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Backtest Error",
                f"Failed to run REAL backtest:\n{str(e)}\n\nCheck logs for details."
            )

    def _create_strategy_config_from_ui(self) -> 'StrategyConfig':
        """Create StrategyConfig from current UI parameters.

        Returns:
            StrategyConfig instance based on UI settings
        """
        from src.core.strategy.engine import StrategyConfig, StrategyType
        from src.core.indicators.engine import IndicatorConfig, IndicatorType

        strategy_name = self.strategy_combo.currentText()

        # Map UI strategy name to StrategyType
        strategy_type_map = {
            "MACD Crossover": StrategyType.TREND_FOLLOWING,
            "RSI Mean Reversion": StrategyType.MEAN_REVERSION,
            "Bollinger Bands": StrategyType.MEAN_REVERSION,
            "Moving Average": StrategyType.TREND_FOLLOWING,
            "Custom Strategy": StrategyType.CUSTOM
        }
        strategy_type = strategy_type_map.get(strategy_name, StrategyType.CUSTOM)

        # Get parameters from UI
        parameters = {
            "fast_period": self.fast_period.value(),
            "slow_period": self.slow_period.value(),
            "signal_period": self.signal_period.value()
        }

        # Risk parameters from UI
        risk_params = {
            "stop_loss_pct": self.stop_loss.value(),
            "take_profit_pct": self.take_profit.value(),
            "position_size_pct": self.position_size.value()
        }

        # Create indicator configs based on strategy
        indicators = []
        if "MACD" in strategy_name:
            indicators.append(
                IndicatorConfig(
                    type=IndicatorType.MACD,
                    params={
                        "fast_period": parameters["fast_period"],
                        "slow_period": parameters["slow_period"],
                        "signal_period": parameters["signal_period"]
                    }
                )
            )
        elif "RSI" in strategy_name:
            indicators.append(
                IndicatorConfig(
                    type=IndicatorType.RSI,
                    params={"period": 14}
                )
            )
        elif "Bollinger" in strategy_name:
            indicators.append(
                IndicatorConfig(
                    type=IndicatorType.BOLLINGER_BANDS,
                    params={"period": 20, "std_dev": 2}
                )
            )
        elif "Moving Average" in strategy_name:
            indicators.extend([
                IndicatorConfig(
                    type=IndicatorType.SMA,
                    params={"period": parameters["fast_period"]}
                ),
                IndicatorConfig(
                    type=IndicatorType.SMA,
                    params={"period": parameters["slow_period"]}
                )
            ])

        # AI validation from UI checkbox
        ai_validation = self.enable_ai_analysis.isChecked()

        return StrategyConfig(
            name=strategy_name,
            strategy_type=strategy_type,
            symbols=[self.symbol],
            parameters=parameters,
            risk_params=risk_params,
            indicators=indicators,
            enabled=True,
            ai_validation=ai_validation
        )

    def _display_backtest_results(self, result: 'BacktestResult'):
        """Display backtest results in Results tab.

        Args:
            result: BacktestResult instance from backtest execution
        """
        from src.core.models.backtest_models import BacktestResult

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid result type: {type(result)}")
            return

        # Update summary label
        summary_text = (
            f"✅ Backtest Completed: {result.symbol}\n"
            f"Period: {result.start.strftime('%Y-%m-%d')} to {result.end.strftime('%Y-%m-%d')}\n"
            f"Strategy: {result.strategy_name or 'Unknown'}\n"
            f"Total P&L: €{result.total_pnl:,.2f} ({result.total_pnl_pct:+.2f}%)"
        )
        self.results_summary.setText(summary_text)

        # Populate metrics table (like TradingView Overview tab)
        metrics = result.metrics
        metrics_data = [
            # Performance Metrics
            ("Total Return", f"{result.total_pnl_pct:+.2f}%"),
            ("Annual Return", f"{metrics.annual_return_pct:+.2f}%" if metrics.annual_return_pct else "N/A"),
            ("Net Profit", f"€{result.total_pnl:,.2f}"),
            ("Final Capital", f"€{result.final_capital:,.2f}"),
            ("", ""),  # Separator
            # Trade Statistics
            ("Total Trades", str(metrics.total_trades)),
            ("Winning Trades", f"{metrics.winning_trades} ({metrics.win_rate:.1%})"),
            ("Losing Trades", f"{metrics.losing_trades}"),
            ("Win Rate", f"{metrics.win_rate:.2%}"),
            ("", ""),  # Separator
            # Risk Metrics
            ("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%"),
            ("Sharpe Ratio", f"{metrics.sharpe_ratio:.3f}" if metrics.sharpe_ratio else "N/A"),
            ("Sortino Ratio", f"{metrics.sortino_ratio:.3f}" if metrics.sortino_ratio else "N/A"),
            ("Profit Factor", f"{metrics.profit_factor:.2f}"),
            ("", ""),  # Separator
            # Trade Quality
            ("Average Win", f"€{metrics.avg_win:,.2f}"),
            ("Average Loss", f"€{metrics.avg_loss:,.2f}"),
            ("Largest Win", f"€{metrics.largest_win:,.2f}"),
            ("Largest Loss", f"€{metrics.largest_loss:,.2f}"),
            ("Expectancy", f"€{metrics.expectancy:,.2f}" if metrics.expectancy else "N/A"),
            ("", ""),  # Separator
            # Streaks
            ("Max Consecutive Wins", str(metrics.max_consecutive_wins)),
            ("Max Consecutive Losses", str(metrics.max_consecutive_losses)),
        ]

        self.metrics_table.setRowCount(len(metrics_data))
        for i, (metric, value) in enumerate(metrics_data):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(value))

        # Resize columns
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.resizeColumnToContents(0)

        logger.info("Backtest results displayed in Results tab")

    def _add_trade_markers_to_chart(self, result: 'BacktestResult'):
        """Add Entry/Exit/StopLoss/TakeProfit markers to chart.

        Args:
            result: BacktestResult with trades to visualize
        """
        from src.core.models.backtest_models import BacktestResult, TradeSide
        import json

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid result type: {type(result)}")
            return

        # Check which markers should be shown based on UI checkboxes
        show_entries = self.show_entry_markers.isChecked()
        show_exits = self.show_exit_markers.isChecked()
        show_sl = self.show_stop_loss.isChecked()
        show_tp = self.show_take_profit.isChecked()

        logger.info(f"Adding trade markers to chart: {len(result.trades)} trades")

        # Prepare marker data for JavaScript bridge (TradingView Lightweight Charts format)
        markers = []

        for trade in result.trades:
            # Entry marker
            if show_entries:
                # Convert to Unix timestamp (required by TradingView Lightweight Charts)
                entry_time = int(trade.entry_time.timestamp())

                entry_marker = {
                    "time": entry_time,
                    "position": "belowBar" if trade.side == TradeSide.LONG else "aboveBar",
                    "color": "#26a69a" if trade.side == TradeSide.LONG else "#ef5350",
                    "shape": "arrowUp" if trade.side == TradeSide.LONG else "arrowDown",
                    "text": f"{'BUY' if trade.side == TradeSide.LONG else 'SELL'} @ €{trade.entry_price:.2f}"
                }
                markers.append(entry_marker)

            # Exit marker (if trade is closed)
            if show_exits and trade.exit_time and trade.exit_price:
                # Convert to Unix timestamp
                exit_time = int(trade.exit_time.timestamp())

                exit_marker = {
                    "time": exit_time,
                    "position": "aboveBar" if trade.side == TradeSide.LONG else "belowBar",
                    "color": "#26a69a" if trade.is_winner else "#ef5350",
                    "shape": "circle",
                    "text": f"EXIT @ €{trade.exit_price:.2f} ({trade.realized_pnl_pct:+.2f}%)"
                }
                markers.append(exit_marker)

        # Send markers to chart via JavaScript API
        if hasattr(self.chart_widget, '_execute_js'):
            markers_json = json.dumps(markers)
            js_code = f"window.chartAPI.addTradeMarkers({markers_json});"
            self.chart_widget._execute_js(js_code)
            logger.info(f"✅ Added {len(markers)} REAL trade markers to chart")
        else:
            logger.warning("Chart widget doesn't have _execute_js method")

        # TODO: Add Stop Loss and Take Profit lines (requires price lines API)
        if show_sl or show_tp:
            logger.info("Stop Loss/Take Profit lines: TODO - requires price lines implementation")

    def _start_optimization(self):
        """Start parameter optimization with REAL data.

        Uses ParameterOptimizer to find best strategy parameters.
        """
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog
        from PyQt6.QtCore import Qt
        from src.core.backtesting.optimization import (
            ParameterOptimizer, ParameterRange, OptimizationMetric, OptimizerConfig
        )

        logger.info(f"Starting REAL parameter optimization for {self.symbol}")

        # Check if chart data is available
        if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
            QMessageBox.warning(
                self,
                "No Chart Data",
                "Please load chart data first before running optimization!"
            )
            return

        try:
            # Create progress dialog
            progress = QProgressDialog(
                "Running parameter optimization...",
                "Cancel",
                0, 0,
                self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Parameter Optimization")
            progress.show()

            # Get parameter ranges from UI
            parameter_ranges = [
                ParameterRange(
                    name="fast_period",
                    values=list(range(self.opt_fast_min.value(), self.opt_fast_max.value() + 1, 2))
                ),
                ParameterRange(
                    name="slow_period",
                    values=list(range(self.opt_slow_min.value(), self.opt_slow_max.value() + 1, 5))
                )
            ]

            # Get optimization metric from UI
            metric_name = self.opt_metric.currentText()
            metric_map = {
                "Sharpe Ratio": "sharpe_ratio",
                "Total Return": "total_return_pct",
                "Profit Factor": "profit_factor",
                "Win Rate": "win_rate"
            }
            primary_metric = metric_map.get(metric_name, "sharpe_ratio")

            # Create optimizer config
            config = OptimizerConfig(
                max_workers=2,  # Limit parallel execution
                timeout_per_test=60,
                primary_metric=primary_metric,
                ai_enabled=self.use_ai_guidance.isChecked()
            )

            # Create optimizer
            optimizer = ParameterOptimizer(
                strategy_factory=None,  # TODO: Use real strategy
                data_provider=self.history_manager,
                config=config
            )

            # Run optimization (simplified - in real implementation use asyncio)
            progress.setLabelText(f"Testing {len(parameter_ranges)} parameter combinations...")

            # For now, show message that full implementation is TODO
            progress.close()

            QMessageBox.information(
                self,
                "Optimization TODO",
                f"Parameter Optimization is connected but full execution pending!\n\n"
                f"Would test:\n"
                f"• Fast Period: {self.opt_fast_min.value()}-{self.opt_fast_max.value()}\n"
                f"• Slow Period: {self.opt_slow_min.value()}-{self.opt_slow_max.value()}\n"
                f"• Metric: {metric_name}\n"
                f"• Max Iterations: {self.max_iterations.value()}\n"
                f"• AI Guidance: {'Yes' if self.use_ai_guidance.isChecked() else 'No'}\n\n"
                f"This will be implemented in next phase with full backtest integration."
            )

            logger.info("✅ Optimization setup complete - full execution pending")

        except Exception as e:
            logger.error(f"Optimization setup failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Optimization Error",
                f"Failed to set up optimization:\n{str(e)}"
            )

    # ========================================================================
    # EVENT BUS INTEGRATION - LIVE TRADE MARKERS
    # ========================================================================

    def _setup_event_subscriptions(self):
        """Subscribe to event bus for live trade marker updates.

        Listens for:
        - TRADE_ENTRY: Entry points (BUY/SELL)
        - TRADE_EXIT: Exit points (profitable/loss)
        - STOP_LOSS_HIT: Stop loss executions
        - TAKE_PROFIT_HIT: Take profit executions
        - ORDER_FILLED: Order fills (for Paper/Live mode)
        """
        try:
            # Subscribe to execution events
            event_bus.subscribe(EventType.TRADE_ENTRY, self._on_trade_entry)
            event_bus.subscribe(EventType.TRADE_EXIT, self._on_trade_exit)
            event_bus.subscribe(EventType.STOP_LOSS_HIT, self._on_stop_loss_hit)
            event_bus.subscribe(EventType.TAKE_PROFIT_HIT, self._on_take_profit_hit)

            # Subscribe to order events (for Paper/Live trading)
            event_bus.subscribe(EventType.ORDER_FILLED, self._on_order_filled)

            # Subscribe to market data events (for live chart streaming)
            event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)

            logger.info(f"✅ Event bus subscriptions established for {self.symbol} chart")

        except Exception as e:
            logger.error(f"Failed to set up event subscriptions: {e}", exc_info=True)

    def _on_trade_entry(self, event: ExecutionEvent):
        """Handle TRADE_ENTRY event - add entry marker to chart.

        Args:
            event: ExecutionEvent with entry details
        """
        try:
            # Only process events for this chart's symbol
            if event.symbol != self.symbol:
                return

            logger.info(f"📍 TRADE_ENTRY event: {event.side} {event.quantity} @ {event.price}")

            # Create entry marker
            marker = {
                "time": int(event.timestamp.timestamp()),
                "position": "belowBar" if event.side == "LONG" else "aboveBar",
                "color": "#26a69a" if event.side == "LONG" else "#ef5350",
                "shape": "arrowUp" if event.side == "LONG" else "arrowDown",
                "text": f"{event.side} @ €{event.price:.2f}"
            }

            # Add marker to chart
            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling TRADE_ENTRY event: {e}", exc_info=True)

    def _on_trade_exit(self, event: ExecutionEvent):
        """Handle TRADE_EXIT event - add exit marker to chart.

        Args:
            event: ExecutionEvent with exit details
        """
        try:
            # Only process events for this chart's symbol
            if event.symbol != self.symbol:
                return

            logger.info(f"📍 TRADE_EXIT event: {event.side} exit @ {event.price}, P/L: {event.pnl_pct:.2f}%")

            # Determine if win or loss
            is_win = event.pnl is not None and event.pnl > 0

            # Create exit marker
            marker = {
                "time": int(event.timestamp.timestamp()),
                "position": "aboveBar" if event.side == "LONG" else "belowBar",
                "color": "#26a69a" if is_win else "#ef5350",
                "shape": "circle",
                "text": f"EXIT @ €{event.price:.2f} ({event.pnl_pct:+.2f}%)" if event.pnl_pct else f"EXIT @ €{event.price:.2f}"
            }

            # Add marker to chart
            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling TRADE_EXIT event: {e}", exc_info=True)

    def _on_stop_loss_hit(self, event: ExecutionEvent):
        """Handle STOP_LOSS_HIT event - add SL marker to chart.

        Args:
            event: ExecutionEvent with stop loss details
        """
        try:
            # Only process events for this chart's symbol
            if event.symbol != self.symbol:
                return

            logger.warning(f"🛑 STOP_LOSS_HIT event: {event.side} @ {event.price}, P/L: {event.pnl_pct:.2f}%")

            # Create stop loss marker (red X)
            marker = {
                "time": int(event.timestamp.timestamp()),
                "position": "aboveBar",
                "color": "#ef5350",
                "shape": "circle",
                "text": f"🛑 STOP LOSS @ €{event.price:.2f} ({event.pnl_pct:+.2f}%)" if event.pnl_pct else f"🛑 STOP LOSS @ €{event.price:.2f}"
            }

            # Add marker to chart
            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling STOP_LOSS_HIT event: {e}", exc_info=True)

    def _on_take_profit_hit(self, event: ExecutionEvent):
        """Handle TAKE_PROFIT_HIT event - add TP marker to chart.

        Args:
            event: ExecutionEvent with take profit details
        """
        try:
            # Only process events for this chart's symbol
            if event.symbol != self.symbol:
                return

            logger.info(f"🎯 TAKE_PROFIT_HIT event: {event.side} @ {event.price}, P/L: {event.pnl_pct:.2f}%")

            # Create take profit marker (green star)
            marker = {
                "time": int(event.timestamp.timestamp()),
                "position": "aboveBar",
                "color": "#26a69a",
                "shape": "circle",
                "text": f"🎯 TAKE PROFIT @ €{event.price:.2f} (+{event.pnl_pct:.2f}%)" if event.pnl_pct else f"🎯 TAKE PROFIT @ €{event.price:.2f}"
            }

            # Add marker to chart
            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling TAKE_PROFIT_HIT event: {e}", exc_info=True)

    def _on_order_filled(self, event: OrderEvent):
        """Handle ORDER_FILLED event - add fill marker to chart.

        Args:
            event: OrderEvent with order fill details
        """
        try:
            # Only process events for this chart's symbol
            if event.symbol != self.symbol:
                return

            logger.info(f"✅ ORDER_FILLED event: {event.side} {event.filled_quantity} @ {event.avg_fill_price}")

            # Determine marker style based on side
            is_buy = event.side and event.side.upper() in ["BUY", "LONG"]

            # Create order fill marker
            marker = {
                "time": int(event.timestamp.timestamp()),
                "position": "belowBar" if is_buy else "aboveBar",
                "color": "#26a69a" if is_buy else "#ef5350",
                "shape": "arrowUp" if is_buy else "arrowDown",
                "text": f"{'BUY' if is_buy else 'SELL'} {event.filled_quantity} @ €{event.avg_fill_price:.2f}"
            }

            # Add marker to chart
            self._add_single_marker(marker)

        except Exception as e:
            logger.error(f"Error handling ORDER_FILLED event: {e}", exc_info=True)

    def _on_market_bar(self, event):
        """Handle MARKET_BAR event - update chart with real-time OHLCV data.

        Args:
            event: Event with market bar data
        """
        try:
            # Only process events for this chart's symbol
            if event.data.get("symbol") != self.symbol:
                return

            logger.debug(f"📊 MARKET_BAR event: {event.data.get('symbol')} "
                        f"O:{event.data.get('open'):.2f} H:{event.data.get('high'):.2f} "
                        f"L:{event.data.get('low'):.2f} C:{event.data.get('close'):.2f}")

            # Create bar data in TradingView format
            bar_data = {
                "time": int(event.timestamp.timestamp()),  # Unix timestamp
                "open": event.data.get("open"),
                "high": event.data.get("high"),
                "low": event.data.get("low"),
                "close": event.data.get("close"),
                "volume": event.data.get("volume", 0)
            }

            # Update chart with new bar
            self._update_chart_bar(bar_data)

        except Exception as e:
            logger.error(f"Error handling MARKET_BAR event: {e}", exc_info=True)

    def _update_chart_bar(self, bar_data: dict):
        """Update the chart with a new real-time bar.

        Args:
            bar_data: Bar data in TradingView format (time, open, high, low, close, volume)
        """
        try:
            # Check if chart widget is available and has the API
            if not hasattr(self.chart_widget, '_execute_js'):
                logger.warning("Chart widget doesn't support JavaScript execution")
                return

            # Convert bar to JSON and execute JavaScript to update chart
            bar_json = json.dumps(bar_data)
            js_command = f"window.chartAPI.updateBar({bar_json});"
            self.chart_widget._execute_js(js_command)

            logger.debug(f"✅ Chart updated with real-time bar: {bar_data['time']}")

        except Exception as e:
            logger.error(f"Error updating chart with bar: {e}", exc_info=True)

    def _add_single_marker(self, marker: dict):
        """Add a single marker to the chart in real-time.

        Args:
            marker: Marker dictionary with TradingView format
        """
        try:
            # Check if chart widget is available and has the API
            if not hasattr(self.chart_widget, '_execute_js'):
                logger.warning("Chart widget doesn't support JavaScript execution")
                return

            # Convert marker to JSON and execute JavaScript
            marker_json = json.dumps([marker])  # API expects array
            js_command = f"window.chartAPI.addTradeMarkers({marker_json});"
            self.chart_widget._execute_js(js_command)

            logger.debug(f"✅ Marker added to chart: {marker['text']}")

        except Exception as e:
            logger.error(f"Error adding marker to chart: {e}", exc_info=True)

    def _unsubscribe_events(self):
        """Unsubscribe from all event bus events."""
        try:
            event_bus.unsubscribe(EventType.TRADE_ENTRY, self._on_trade_entry)
            event_bus.unsubscribe(EventType.TRADE_EXIT, self._on_trade_exit)
            event_bus.unsubscribe(EventType.STOP_LOSS_HIT, self._on_stop_loss_hit)
            event_bus.unsubscribe(EventType.TAKE_PROFIT_HIT, self._on_take_profit_hit)
            event_bus.unsubscribe(EventType.ORDER_FILLED, self._on_order_filled)
            event_bus.unsubscribe(EventType.MARKET_BAR, self._on_market_bar)

            logger.info(f"✅ Event bus unsubscribed for {self.symbol} chart")

        except Exception as e:
            logger.error(f"Error unsubscribing from events: {e}", exc_info=True)

    # ========================================================================
    # END EVENT BUS INTEGRATION
    # ========================================================================

    def _load_window_state(self):
        """Load window position and size from settings."""
        settings_key = f"ChartWindow/{self.symbol}"

        # Load geometry
        geometry = self.settings.value(f"{settings_key}/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size and position
            self.resize(1200, 800)
            # Center on screen
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

        # Load window state (maximized, etc.)
        window_state = self.settings.value(f"{settings_key}/windowState")
        if window_state:
            self.restoreState(window_state)

        # Load chart settings (only if WebEngine is available)
        if hasattr(self.chart_widget, 'timeframe_combo'):
            timeframe = self.settings.value(f"{settings_key}/timeframe")
            if timeframe:
                self.chart_widget.current_timeframe = timeframe
                # Update combo box
                index = self.chart_widget.timeframe_combo.findData(timeframe)
                if index >= 0:
                    self.chart_widget.timeframe_combo.setCurrentIndex(index)

        if hasattr(self.chart_widget, 'period_combo'):
            period = self.settings.value(f"{settings_key}/period")
            if period:
                self.chart_widget.current_period = period
                # Update combo box
                index = self.chart_widget.period_combo.findData(period)
                if index >= 0:
                    self.chart_widget.period_combo.setCurrentIndex(index)

        # Load active indicators
        if hasattr(self.chart_widget, 'indicator_actions'):
            active_indicators = self.settings.value(f"{settings_key}/indicators")
            if active_indicators and isinstance(active_indicators, list):
                for indicator_id in active_indicators:
                    if indicator_id in self.chart_widget.indicator_actions:
                        action = self.chart_widget.indicator_actions[indicator_id]
                        action.setChecked(True)

        logger.debug(f"Loaded window state for {self.symbol}")

    def _save_window_state(self):
        """Save window position, size, and chart settings."""
        settings_key = f"ChartWindow/{self.symbol}"

        # Save geometry
        self.settings.setValue(f"{settings_key}/geometry", self.saveGeometry())

        # Save window state
        self.settings.setValue(f"{settings_key}/windowState", self.saveState())

        # Save chart settings (only if WebEngine is available)
        if hasattr(self.chart_widget, 'current_timeframe'):
            self.settings.setValue(f"{settings_key}/timeframe", self.chart_widget.current_timeframe)
        if hasattr(self.chart_widget, 'current_period'):
            self.settings.setValue(f"{settings_key}/period", self.chart_widget.current_period)

        # Save active indicators
        if hasattr(self.chart_widget, 'indicator_actions'):
            active_indicators = [
                ind_id for ind_id, action in self.chart_widget.indicator_actions.items()
                if action.isChecked()
            ]
            self.settings.setValue(f"{settings_key}/indicators", active_indicators)

        logger.debug(f"Saved window state for {self.symbol}")

    def load_backtest_result(self, result):
        """Load and display backtest result in chart window.

        Args:
            result: BacktestResult instance to display
        """
        from src.core.models.backtest_models import BacktestResult

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid backtest result type: {type(result)}")
            return

        logger.info(f"Loading backtest result for {result.symbol} into chart window")

        # Update window title to show backtest mode
        self.setWindowTitle(f"Backtest Results - {result.symbol} | {result.strategy_name}")

        # Check if chart_widget has a method to display backtest results
        if hasattr(self.chart_widget, 'load_backtest_result'):
            self.chart_widget.load_backtest_result(result)
        elif hasattr(self.chart_widget, 'bridge'):
            # Use ChartBridge to send data to JavaScript
            if hasattr(self.chart_widget.bridge, 'loadBacktestResultObject'):
                self.chart_widget.bridge.loadBacktestResultObject(result)
            else:
                logger.warning("ChartBridge doesn't have loadBacktestResultObject method")
        else:
            logger.warning(f"Chart widget doesn't support backtest result display")

        # Show and raise window
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event.

        Args:
            event: Close event
        """
        logger.info(f"Closing ChartWindow for {self.symbol}...")

        # CRITICAL: Stop live stream if running (prevents freeze)
        if hasattr(self, 'stream_client') and self.stream_client is not None:
            logger.info("Stopping active stream before closing...")
            try:
                # Force synchronous disconnect to prevent freeze
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    # Create task and wait briefly
                    task = loop.create_task(self.stream_client.disconnect())
                    # Don't wait indefinitely - timeout after 1 second
                    try:
                        loop.run_until_complete(asyncio.wait_for(task, timeout=1.0))
                    except asyncio.TimeoutError:
                        logger.warning("Stream disconnect timeout - forcing cleanup")
                except RuntimeError:
                    # No running loop - just mark as None
                    logger.warning("No event loop - skipping async disconnect")
                finally:
                    self.stream_client = None
            except Exception as e:
                logger.error(f"Error stopping stream on close: {e}")
                self.stream_client = None

        # Unsubscribe from event bus to prevent memory leaks
        self._unsubscribe_events()

        # Save state before closing
        self._save_window_state()

        # Emit signal that window is closing
        self.window_closed.emit(self.symbol)

        logger.info(f"ChartWindow closed for {self.symbol}")

        # Accept the close event
        event.accept()

    async def load_chart(self, data_provider: Optional[str] = None):
        """Load chart data for the symbol.

        Args:
            data_provider: Optional data provider to use
        """
        try:
            logger.info(f"Loading chart for {self.symbol} in popup window")
            await self.chart_widget.load_symbol(self.symbol, data_provider)
        except Exception as e:
            logger.error(f"Error loading chart in popup window: {e}", exc_info=True)
