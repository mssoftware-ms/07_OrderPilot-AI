"""Panels Mixin for ChartWindow.

Contains tab creation methods (Strategy, Backtest, Optimization, Results).
"""

import logging

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class PanelsMixin:
    """Mixin providing panel/tab creation for ChartWindow."""

    def _create_bottom_panel(self) -> QWidget:
        """Create bottom panel with tabs."""
        panel_container = QWidget()
        panel_layout = QVBoxLayout(panel_container)
        panel_layout.setContentsMargins(5, 5, 5, 5)

        self.panel_tabs = QTabWidget()

        # Tab 1: Strategy Configuration
        self.strategy_tab = self._create_strategy_tab()
        self.panel_tabs.addTab(self.strategy_tab, "Strategy")

        # Tab 2: Backtest
        self.backtest_tab = self._create_backtest_tab()
        self.panel_tabs.addTab(self.backtest_tab, "Backtest")

        # Tab 3: Parameter Optimization
        self.optimization_tab = self._create_optimization_tab()
        self.panel_tabs.addTab(self.optimization_tab, "Optimize")

        # Tab 4: Results
        self.results_tab = self._create_results_tab()
        self.panel_tabs.addTab(self.results_tab, "Results")

        panel_layout.addWidget(self.panel_tabs)
        return panel_container

    def _toggle_bottom_panel(self):
        """Toggle visibility of bottom panel dock widget."""
        if not hasattr(self.chart_widget, 'toggle_panel_button'):
            return

        button = self.chart_widget.toggle_panel_button
        should_show = button.isChecked()

        self.dock_widget.setVisible(should_show)
        self._update_toggle_button_text()

    def _on_dock_visibility_changed(self, visible: bool):
        """Handle dock visibility changes."""
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            self.chart_widget.toggle_panel_button.setChecked(visible)
            self._update_toggle_button_text()

    def _update_toggle_button_text(self):
        """Update the toggle button text based on state."""
        if hasattr(self.chart_widget, 'toggle_panel_button'):
            button = self.chart_widget.toggle_panel_button
            if button.isChecked():
                button.setText("Panel")
            else:
                button.setText("Panel")

    def _create_strategy_tab(self) -> QWidget:
        """Create strategy configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Strategy Selection
        strategy_group = QGroupBox("Strategy Selection")
        strategy_layout = QFormLayout()

        self.strategy_combo = QComboBox()

        # Load real strategies from YAML files
        from src.core.strategy.loader import get_strategy_loader

        self.strategy_loader = get_strategy_loader()
        available_strategies = self.strategy_loader.discover_strategies()

        if available_strategies:
            for strategy_name in available_strategies:
                info = self.strategy_loader.get_strategy_info(strategy_name)
                if info:
                    display_name = f"{info['name']} ({info['category']})"
                    self.strategy_combo.addItem(display_name, strategy_name)
                else:
                    self.strategy_combo.addItem(strategy_name, strategy_name)
            logger.info(f"Loaded {len(available_strategies)} strategies from YAML files")
        else:
            logger.warning("No YAML strategies found, using fallback list")
            self.strategy_combo.addItems([
                "MACD Crossover", "RSI Mean Reversion", "Bollinger Bands",
                "Moving Average", "Custom Strategy"
            ])

        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_selected)
        strategy_layout.addRow("Strategy:", self.strategy_combo)

        # Strategy Parameters
        self.param_container = QWidget()
        self.param_layout = QFormLayout(self.param_container)

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
        apply_btn = QPushButton("Apply Strategy to Chart")
        apply_btn.clicked.connect(self._apply_strategy)
        layout.addWidget(apply_btn)

        # Clear Markers Button
        clear_markers_btn = QPushButton("Clear Strategy Markers")
        clear_markers_btn.clicked.connect(self._clear_strategy_markers)
        clear_markers_btn.setStyleSheet("background-color: #555; color: white;")
        layout.addWidget(clear_markers_btn)

        layout.addStretch()
        return widget

    def _create_backtest_tab(self) -> QWidget:
        """Create backtest controls tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Backtest Configuration
        config_group = QGroupBox("Backtest Configuration")
        config_layout = QFormLayout()

        self.backtest_start_date = QDateEdit()
        self.backtest_start_date.setDate(QDate.currentDate().addYears(-1))
        self.backtest_start_date.setCalendarPopup(True)
        config_layout.addRow("Start Date:", self.backtest_start_date)

        self.backtest_end_date = QDateEdit()
        self.backtest_end_date.setDate(QDate.currentDate())
        self.backtest_end_date.setCalendarPopup(True)
        config_layout.addRow("End Date:", self.backtest_end_date)

        self.initial_capital = QDoubleSpinBox()
        self.initial_capital.setRange(1000, 1000000)
        self.initial_capital.setValue(10000)
        self.initial_capital.setPrefix("€")
        config_layout.addRow("Initial Capital:", self.initial_capital)

        self.enable_ai_analysis = QCheckBox("Enable AI Analysis")
        self.enable_ai_analysis.setChecked(True)
        config_layout.addRow("AI Analysis:", self.enable_ai_analysis)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Run Backtest Button
        run_btn = QPushButton("Run Backtest on Chart")
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
            "Sharpe Ratio", "Total Return", "Profit Factor", "Win Rate"
        ])
        opt_layout.addRow("Optimize For:", self.opt_metric)

        self.use_ai_guidance = QCheckBox("Use AI Guidance")
        self.use_ai_guidance.setChecked(True)
        opt_layout.addRow("AI Guidance:", self.use_ai_guidance)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # Start Optimization Button
        start_btn = QPushButton("Start Optimization")
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
        """Handle strategy selection change."""
        strategy_file_name = self.strategy_combo.currentData()
        if not strategy_file_name:
            strategy_file_name = self.strategy_combo.currentText()

        logger.info(f"Strategy selected: {strategy_file_name}")

        if hasattr(self, 'strategy_loader'):
            strategy_def = self.strategy_loader.load_strategy(strategy_file_name)
            if strategy_def:
                self.current_strategy_def = strategy_def
                logger.info(f"Loaded strategy: {strategy_def.name}")
            else:
                logger.warning(f"Could not load strategy: {strategy_file_name}")
                self.current_strategy_def = None
        else:
            self.current_strategy_def = None
