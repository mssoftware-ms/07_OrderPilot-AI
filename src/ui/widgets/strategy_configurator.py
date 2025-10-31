"""Strategy Configurator Widget.

Provides UI for configuring and managing trading strategies,
including parameter tuning, backtesting, and optimization.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.strategy.engine import StrategyConfig, StrategyEngine, StrategyType

logger = logging.getLogger(__name__)


class StrategyWorker(QThread):
    """Worker thread for strategy operations."""

    progress = pyqtSignal(int)
    result = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, operation: str, data: dict[str, Any]):
        """Initialize worker.

        Args:
            operation: Operation to perform
            data: Operation data
        """
        super().__init__()
        self.operation = operation
        self.data = data

    def run(self):
        """Run the operation."""
        try:
            if self.operation == "backtest":
                # Run backtest
                self.progress.emit(50)
                # Simulate backtest result
                result = {
                    'total_return': 0.15,
                    'sharpe_ratio': 1.2,
                    'max_drawdown': -0.08,
                    'total_trades': 42
                }
                self.progress.emit(100)
                self.result.emit(result)

            elif self.operation == "optimize":
                # Run optimization
                for i in range(101):
                    self.progress.emit(i)
                    self.msleep(10)

                result = {
                    'best_params': {'period': 25, 'threshold': 0.7},
                    'best_sharpe': 1.5
                }
                self.result.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class StrategyConfigurator(QWidget):
    """Widget for configuring trading strategies."""

    # Signals
    strategy_created = pyqtSignal(dict)
    strategy_updated = pyqtSignal(str, dict)
    strategy_deleted = pyqtSignal(str)
    backtest_requested = pyqtSignal(dict)

    def __init__(self):
        """Initialize strategy configurator."""
        super().__init__()

        self.strategy_engine = StrategyEngine()
        self.current_strategy: StrategyConfig | None = None
        self.worker: StrategyWorker | None = None

        self._setup_ui()
        self._load_strategies()

    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()

        # Strategy configuration tab
        self.config_tab = self._create_config_tab()
        self.tabs.addTab(self.config_tab, "Configuration")

        # Parameters tab
        self.params_tab = self._create_params_tab()
        self.tabs.addTab(self.params_tab, "Parameters")

        # Indicators tab
        self.indicators_tab = self._create_indicators_tab()
        self.tabs.addTab(self.indicators_tab, "Indicators")

        # Backtesting tab
        self.backtest_tab = self._create_backtest_tab()
        self.tabs.addTab(self.backtest_tab, "Backtesting")

        # Optimization tab
        self.optimize_tab = self._create_optimize_tab()
        self.tabs.addTab(self.optimize_tab, "Optimization")

        layout.addWidget(self.tabs)

        # Control buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save Strategy")
        self.save_button.clicked.connect(self._save_strategy)
        button_layout.addWidget(self.save_button)

        self.load_button = QPushButton("Load Strategy")
        self.load_button.clicked.connect(self._load_strategy_file)
        button_layout.addWidget(self.load_button)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self._export_strategy)
        button_layout.addWidget(self.export_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._delete_strategy)
        self.delete_button.setStyleSheet("QPushButton { background-color: #ff4444; }")
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _create_config_tab(self) -> QWidget:
        """Create configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Strategy selection
        select_group = QGroupBox("Strategy Selection")
        select_layout = QVBoxLayout()

        # Strategy list
        self.strategy_list = QComboBox()
        self.strategy_list.currentTextChanged.connect(self._on_strategy_selected)
        select_layout.addWidget(QLabel("Active Strategies:"))
        select_layout.addWidget(self.strategy_list)

        # New strategy
        new_layout = QHBoxLayout()
        self.new_name_edit = QLineEdit()
        self.new_name_edit.setPlaceholderText("Enter strategy name...")
        new_layout.addWidget(self.new_name_edit)

        self.new_type_combo = QComboBox()
        self.new_type_combo.addItems([
            "trend_following", "mean_reversion", "momentum",
            "breakout", "scalping", "pairs_trading", "custom"
        ])
        new_layout.addWidget(self.new_type_combo)

        self.create_button = QPushButton("Create New")
        self.create_button.clicked.connect(self._create_new_strategy)
        new_layout.addWidget(self.create_button)

        select_layout.addWidget(QLabel("Create New Strategy:"))
        select_layout.addLayout(new_layout)

        select_group.setLayout(select_layout)
        layout.addWidget(select_group)

        # Basic settings
        settings_group = QGroupBox("Basic Settings")
        settings_layout = QVBoxLayout()

        # Symbols
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Symbols:"))
        self.symbols_edit = QLineEdit()
        self.symbols_edit.setPlaceholderText("AAPL,GOOGL,MSFT")
        symbol_layout.addWidget(self.symbols_edit)
        settings_layout.addLayout(symbol_layout)

        # Position sizing
        sizing_layout = QHBoxLayout()
        sizing_layout.addWidget(QLabel("Position Sizing:"))
        self.sizing_combo = QComboBox()
        self.sizing_combo.addItems(["fixed", "kelly", "risk_parity"])
        sizing_layout.addWidget(self.sizing_combo)
        settings_layout.addLayout(sizing_layout)

        # Max positions
        positions_layout = QHBoxLayout()
        positions_layout.addWidget(QLabel("Max Positions:"))
        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 20)
        self.max_positions_spin.setValue(5)
        positions_layout.addWidget(self.max_positions_spin)
        settings_layout.addLayout(positions_layout)

        # Options
        self.enabled_check = QCheckBox("Strategy Enabled")
        self.enabled_check.setChecked(True)
        settings_layout.addWidget(self.enabled_check)

        self.ai_validation_check = QCheckBox("AI Validation")
        self.ai_validation_check.setChecked(True)
        settings_layout.addWidget(self.ai_validation_check)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Strategy info
        info_group = QGroupBox("Strategy Information")
        info_layout = QVBoxLayout()

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        info_layout.addWidget(self.info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        return widget

    def _create_params_tab(self) -> QWidget:
        """Create parameters tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Strategy parameters
        params_group = QGroupBox("Strategy Parameters")
        params_layout = QVBoxLayout()

        self.params_tree = QTreeWidget()
        self.params_tree.setHeaderLabels(["Parameter", "Value", "Min", "Max", "Step"])
        self.params_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        params_layout.addWidget(self.params_tree)

        # Add parameter button
        add_param_layout = QHBoxLayout()
        self.param_name_edit = QLineEdit()
        self.param_name_edit.setPlaceholderText("Parameter name")
        add_param_layout.addWidget(self.param_name_edit)

        self.param_value_edit = QLineEdit()
        self.param_value_edit.setPlaceholderText("Default value")
        add_param_layout.addWidget(self.param_value_edit)

        self.add_param_button = QPushButton("Add Parameter")
        self.add_param_button.clicked.connect(self._add_parameter)
        add_param_layout.addWidget(self.add_param_button)

        params_layout.addLayout(add_param_layout)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Risk parameters
        risk_group = QGroupBox("Risk Parameters")
        risk_layout = QVBoxLayout()

        # Allocation percentage
        alloc_layout = QHBoxLayout()
        alloc_layout.addWidget(QLabel("Allocation %:"))
        self.allocation_spin = QDoubleSpinBox()
        self.allocation_spin.setRange(0.01, 0.5)
        self.allocation_spin.setSingleStep(0.01)
        self.allocation_spin.setValue(0.1)
        alloc_layout.addWidget(self.allocation_spin)
        risk_layout.addLayout(alloc_layout)

        # Stop loss
        stop_layout = QHBoxLayout()
        stop_layout.addWidget(QLabel("Stop Loss %:"))
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(0.01, 0.2)
        self.stop_loss_spin.setSingleStep(0.01)
        self.stop_loss_spin.setValue(0.05)
        stop_layout.addWidget(self.stop_loss_spin)
        risk_layout.addLayout(stop_layout)

        # Take profit
        profit_layout = QHBoxLayout()
        profit_layout.addWidget(QLabel("Take Profit %:"))
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setRange(0.01, 0.5)
        self.take_profit_spin.setSingleStep(0.01)
        self.take_profit_spin.setValue(0.1)
        profit_layout.addWidget(self.take_profit_spin)
        risk_layout.addLayout(profit_layout)

        # Max drawdown
        dd_layout = QHBoxLayout()
        dd_layout.addWidget(QLabel("Max Drawdown %:"))
        self.max_drawdown_spin = QDoubleSpinBox()
        self.max_drawdown_spin.setRange(0.05, 0.5)
        self.max_drawdown_spin.setSingleStep(0.05)
        self.max_drawdown_spin.setValue(0.2)
        dd_layout.addWidget(self.max_drawdown_spin)
        risk_layout.addLayout(dd_layout)

        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)

        layout.addStretch()
        return widget

    def _create_indicators_tab(self) -> QWidget:
        """Create indicators tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Available indicators
        available_group = QGroupBox("Available Indicators")
        available_layout = QVBoxLayout()

        self.indicators_list = QTableWidget()
        self.indicators_list.setColumnCount(4)
        self.indicators_list.setHorizontalHeaderLabels(["Indicator", "Type", "Parameters", "Enabled"])
        self.indicators_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Add sample indicators
        indicators = [
            ("SMA", "Trend", "period=20", True),
            ("EMA", "Trend", "period=20", False),
            ("RSI", "Momentum", "period=14", True),
            ("MACD", "Trend", "fast=12,slow=26,signal=9", True),
            ("BB", "Volatility", "period=20,std=2", False),
            ("ATR", "Volatility", "period=14", False),
            ("STOCH", "Momentum", "k=14,d=3", False)
        ]

        self.indicators_list.setRowCount(len(indicators))
        for i, (name, ind_type, params, enabled) in enumerate(indicators):
            self.indicators_list.setItem(i, 0, QTableWidgetItem(name))
            self.indicators_list.setItem(i, 1, QTableWidgetItem(ind_type))
            self.indicators_list.setItem(i, 2, QTableWidgetItem(params))

            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
            self.indicators_list.setItem(i, 3, check_item)

        available_layout.addWidget(self.indicators_list)

        # Add indicator controls
        add_indicator_layout = QHBoxLayout()

        self.indicator_type_combo = QComboBox()
        self.indicator_type_combo.addItems([
            "SMA", "EMA", "RSI", "MACD", "BB", "ATR", "STOCH", "ADX", "CCI", "MFI"
        ])
        add_indicator_layout.addWidget(self.indicator_type_combo)

        self.indicator_params_edit = QLineEdit()
        self.indicator_params_edit.setPlaceholderText("Parameters (e.g., period=20)")
        add_indicator_layout.addWidget(self.indicator_params_edit)

        self.add_indicator_button = QPushButton("Add Indicator")
        self.add_indicator_button.clicked.connect(self._add_indicator)
        add_indicator_layout.addWidget(self.add_indicator_button)

        available_layout.addLayout(add_indicator_layout)
        available_group.setLayout(available_layout)
        layout.addWidget(available_group)

        # Indicator settings
        settings_group = QGroupBox("Indicator Settings")
        settings_layout = QVBoxLayout()

        self.use_talib_check = QCheckBox("Use TA-Lib (if available)")
        self.use_talib_check.setChecked(True)
        settings_layout.addWidget(self.use_talib_check)

        self.cache_indicators_check = QCheckBox("Cache Indicator Results")
        self.cache_indicators_check.setChecked(True)
        settings_layout.addWidget(self.cache_indicators_check)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        layout.addStretch()
        return widget

    def _create_backtest_tab(self) -> QWidget:
        """Create backtesting tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Backtest settings
        settings_group = QGroupBox("Backtest Settings")
        settings_layout = QVBoxLayout()

        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QLineEdit()
        self.start_date_edit.setText((datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        date_layout.addWidget(self.start_date_edit)

        date_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QLineEdit()
        self.end_date_edit.setText(datetime.now().strftime("%Y-%m-%d"))
        date_layout.addWidget(self.end_date_edit)
        settings_layout.addLayout(date_layout)

        # Capital and fees
        capital_layout = QHBoxLayout()
        capital_layout.addWidget(QLabel("Initial Capital:"))
        self.capital_spin = QSpinBox()
        self.capital_spin.setRange(1000, 1000000)
        self.capital_spin.setSingleStep(1000)
        self.capital_spin.setValue(10000)
        capital_layout.addWidget(self.capital_spin)

        capital_layout.addWidget(QLabel("Commission:"))
        self.commission_spin = QDoubleSpinBox()
        self.commission_spin.setRange(0.0, 0.01)
        self.commission_spin.setSingleStep(0.001)
        self.commission_spin.setValue(0.001)
        capital_layout.addWidget(self.commission_spin)
        settings_layout.addLayout(capital_layout)

        # Run backtest button
        self.run_backtest_button = QPushButton("Run Backtest")
        self.run_backtest_button.clicked.connect(self._run_backtest)
        settings_layout.addWidget(self.run_backtest_button)

        # Progress bar
        self.backtest_progress = QProgressBar()
        self.backtest_progress.setVisible(False)
        settings_layout.addWidget(self.backtest_progress)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Results
        results_group = QGroupBox("Backtest Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        return widget

    def _create_optimize_tab(self) -> QWidget:
        """Create optimization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Optimization settings
        settings_group = QGroupBox("Optimization Settings")
        settings_layout = QVBoxLayout()

        # Parameter ranges
        param_label = QLabel("Parameter Ranges:")
        settings_layout.addWidget(param_label)

        self.optimize_params_table = QTableWidget()
        self.optimize_params_table.setColumnCount(5)
        self.optimize_params_table.setHorizontalHeaderLabels(
            ["Parameter", "Min", "Max", "Step", "Optimize"]
        )
        self.optimize_params_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Add sample parameters
        sample_params = [
            ("sma_period", 10, 50, 5, True),
            ("rsi_period", 10, 20, 2, True),
            ("stop_loss", 0.02, 0.1, 0.01, False)
        ]

        self.optimize_params_table.setRowCount(len(sample_params))
        for i, (name, min_val, max_val, step, optimize) in enumerate(sample_params):
            self.optimize_params_table.setItem(i, 0, QTableWidgetItem(name))
            self.optimize_params_table.setItem(i, 1, QTableWidgetItem(str(min_val)))
            self.optimize_params_table.setItem(i, 2, QTableWidgetItem(str(max_val)))
            self.optimize_params_table.setItem(i, 3, QTableWidgetItem(str(step)))

            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check_item.setCheckState(Qt.CheckState.Checked if optimize else Qt.CheckState.Unchecked)
            self.optimize_params_table.setItem(i, 4, check_item)

        settings_layout.addWidget(self.optimize_params_table)

        # Optimization target
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Optimize For:"))
        self.optimize_target_combo = QComboBox()
        self.optimize_target_combo.addItems([
            "Sharpe Ratio", "Total Return", "Win Rate", "Profit Factor", "Min Drawdown"
        ])
        target_layout.addWidget(self.optimize_target_combo)
        settings_layout.addLayout(target_layout)

        # Run optimization button
        self.run_optimize_button = QPushButton("Run Optimization")
        self.run_optimize_button.clicked.connect(self._run_optimization)
        settings_layout.addWidget(self.run_optimize_button)

        # Progress bar
        self.optimize_progress = QProgressBar()
        self.optimize_progress.setVisible(False)
        settings_layout.addWidget(self.optimize_progress)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Optimization results
        results_group = QGroupBox("Optimization Results")
        results_layout = QVBoxLayout()

        self.optimize_results_text = QTextEdit()
        self.optimize_results_text.setReadOnly(True)
        results_layout.addWidget(self.optimize_results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        return widget

    def _load_strategies(self):
        """Load available strategies."""
        # Load from strategy engine
        for name, strategy in self.strategy_engine.strategies.items():
            self.strategy_list.addItem(name)

    def _on_strategy_selected(self, name: str):
        """Handle strategy selection.

        Args:
            name: Strategy name
        """
        if not name:
            return

        # Load strategy configuration
        if name in self.strategy_engine.strategies:
            strategy = self.strategy_engine.strategies[name]
            config = strategy.config

            self.current_strategy = config

            # Update UI with strategy details
            self.symbols_edit.setText(",".join(config.symbols))
            self.sizing_combo.setCurrentText(config.position_sizing)
            self.max_positions_spin.setValue(config.max_positions)
            self.enabled_check.setChecked(config.enabled)
            self.ai_validation_check.setChecked(config.ai_validation)

            # Update info
            info = f"Strategy: {config.name}\n"
            info += f"Type: {config.strategy_type.value}\n"
            info += f"Status: {'Enabled' if config.enabled else 'Disabled'}\n"
            info += f"AI Validation: {'Yes' if config.ai_validation else 'No'}"
            self.info_text.setText(info)

            # Update parameters
            self._update_params_tree(config.parameters)

            # Update risk parameters
            if 'allocation_pct' in config.risk_params:
                self.allocation_spin.setValue(config.risk_params['allocation_pct'])
            if 'stop_loss_pct' in config.risk_params:
                self.stop_loss_spin.setValue(config.risk_params['stop_loss_pct'])
            if 'take_profit_pct' in config.risk_params:
                self.take_profit_spin.setValue(config.risk_params['take_profit_pct'])

    def _create_new_strategy(self):
        """Create a new strategy."""
        name = self.new_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a strategy name")
            return

        # Create strategy configuration
        strategy_type = StrategyType(self.new_type_combo.currentText())

        config = StrategyConfig(
            name=name,
            strategy_type=strategy_type,
            symbols=self.symbols_edit.text().split(",") if self.symbols_edit.text() else ["AAPL"],
            parameters={},
            risk_params={
                'allocation_pct': self.allocation_spin.value(),
                'stop_loss_pct': self.stop_loss_spin.value(),
                'take_profit_pct': self.take_profit_spin.value()
            },
            indicators=[],
            enabled=self.enabled_check.isChecked(),
            position_sizing=self.sizing_combo.currentText(),
            ai_validation=self.ai_validation_check.isChecked()
        )

        # Create strategy instance
        try:
            strategy = self.strategy_engine.create_strategy(config)

            # Add to list
            self.strategy_list.addItem(name)
            self.strategy_list.setCurrentText(name)

            # Clear new strategy fields
            self.new_name_edit.clear()

            # Emit signal
            self.strategy_created.emit(config.__dict__)

            QMessageBox.information(self, "Success", f"Strategy '{name}' created successfully")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create strategy: {e}")

    def _save_strategy(self):
        """Save current strategy configuration."""
        if not self.current_strategy:
            QMessageBox.warning(self, "Error", "No strategy selected")
            return

        # Update configuration
        self.current_strategy.symbols = self.symbols_edit.text().split(",")
        self.current_strategy.position_sizing = self.sizing_combo.currentText()
        self.current_strategy.max_positions = self.max_positions_spin.value()
        self.current_strategy.enabled = self.enabled_check.isChecked()
        self.current_strategy.ai_validation = self.ai_validation_check.isChecked()

        # Update risk parameters
        self.current_strategy.risk_params.update({
            'allocation_pct': self.allocation_spin.value(),
            'stop_loss_pct': self.stop_loss_spin.value(),
            'take_profit_pct': self.take_profit_spin.value(),
            'max_drawdown_pct': self.max_drawdown_spin.value()
        })

        # Emit signal
        self.strategy_updated.emit(
            self.current_strategy.name,
            self.current_strategy.__dict__
        )

        QMessageBox.information(self, "Success", "Strategy configuration saved")

    def _delete_strategy(self):
        """Delete current strategy."""
        if not self.current_strategy:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete strategy '{self.current_strategy.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Disable strategy
            self.strategy_engine.disable_strategy(self.current_strategy.name)

            # Remove from list
            index = self.strategy_list.findText(self.current_strategy.name)
            if index >= 0:
                self.strategy_list.removeItem(index)

            # Emit signal
            self.strategy_deleted.emit(self.current_strategy.name)

            self.current_strategy = None
            QMessageBox.information(self, "Success", "Strategy deleted")

    def _load_strategy_file(self):
        """Load strategy from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Strategy", "", "JSON Files (*.json)"
        )

        if filename:
            try:
                with open(filename) as f:
                    data = json.load(f)

                # Create strategy from data
                config = StrategyConfig(**data)
                strategy = self.strategy_engine.create_strategy(config)

                # Add to list
                self.strategy_list.addItem(config.name)
                self.strategy_list.setCurrentText(config.name)

                QMessageBox.information(self, "Success", f"Strategy loaded from {filename}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load strategy: {e}")

    def _export_strategy(self):
        """Export strategy to file."""
        if not self.current_strategy:
            QMessageBox.warning(self, "Error", "No strategy selected")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Strategy", f"{self.current_strategy.name}.json", "JSON Files (*.json)"
        )

        if filename:
            try:
                data = {
                    'name': self.current_strategy.name,
                    'strategy_type': self.current_strategy.strategy_type.value,
                    'symbols': self.current_strategy.symbols,
                    'parameters': self.current_strategy.parameters,
                    'risk_params': self.current_strategy.risk_params,
                    'indicators': [ind.__dict__ for ind in self.current_strategy.indicators],
                    'enabled': self.current_strategy.enabled,
                    'max_positions': self.current_strategy.max_positions,
                    'position_sizing': self.current_strategy.position_sizing,
                    'ai_validation': self.current_strategy.ai_validation
                }

                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

                QMessageBox.information(self, "Success", f"Strategy exported to {filename}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export strategy: {e}")

    def _update_params_tree(self, parameters: dict[str, Any]):
        """Update parameters tree.

        Args:
            parameters: Strategy parameters
        """
        self.params_tree.clear()

        for name, value in parameters.items():
            item = QTreeWidgetItem([name, str(value), "", "", ""])
            self.params_tree.addTopLevelItem(item)

    def _add_parameter(self):
        """Add a new parameter."""
        name = self.param_name_edit.text().strip()
        value = self.param_value_edit.text().strip()

        if name and value:
            item = QTreeWidgetItem([name, value, "", "", ""])
            self.params_tree.addTopLevelItem(item)

            self.param_name_edit.clear()
            self.param_value_edit.clear()

    def _add_indicator(self):
        """Add a new indicator."""
        ind_type = self.indicator_type_combo.currentText()
        params = self.indicator_params_edit.text()

        row = self.indicators_list.rowCount()
        self.indicators_list.insertRow(row)

        self.indicators_list.setItem(row, 0, QTableWidgetItem(ind_type))
        self.indicators_list.setItem(row, 1, QTableWidgetItem("Custom"))
        self.indicators_list.setItem(row, 2, QTableWidgetItem(params))

        check_item = QTableWidgetItem()
        check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        check_item.setCheckState(Qt.CheckState.Checked)
        self.indicators_list.setItem(row, 3, check_item)

        self.indicator_params_edit.clear()

    def _run_backtest(self):
        """Run backtest."""
        if not self.current_strategy:
            QMessageBox.warning(self, "Error", "No strategy selected")
            return

        # Show progress bar
        self.backtest_progress.setVisible(True)
        self.run_backtest_button.setEnabled(False)

        # Prepare backtest data
        data = {
            'strategy': self.current_strategy.__dict__,
            'start_date': self.start_date_edit.text(),
            'end_date': self.end_date_edit.text(),
            'initial_capital': self.capital_spin.value(),
            'commission': self.commission_spin.value()
        }

        # Create and start worker
        self.worker = StrategyWorker("backtest", data)
        self.worker.progress.connect(self.backtest_progress.setValue)
        self.worker.result.connect(self._on_backtest_result)
        self.worker.error.connect(self._on_backtest_error)
        self.worker.finished.connect(self._on_backtest_complete)
        self.worker.start()

        # Emit signal
        self.backtest_requested.emit(data)

    @pyqtSlot(dict)
    def _on_backtest_result(self, result: dict[str, Any]):
        """Handle backtest result.

        Args:
            result: Backtest result
        """
        text = "Backtest Results:\n" + "=" * 50 + "\n"
        text += f"Total Return: {result.get('total_return', 0):.2%}\n"
        text += f"Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}\n"
        text += f"Max Drawdown: {result.get('max_drawdown', 0):.2%}\n"
        text += f"Total Trades: {result.get('total_trades', 0)}\n"

        self.results_text.setText(text)

    @pyqtSlot(str)
    def _on_backtest_error(self, error: str):
        """Handle backtest error.

        Args:
            error: Error message
        """
        QMessageBox.critical(self, "Backtest Error", error)
        self.results_text.setText(f"Error: {error}")

    def _on_backtest_complete(self):
        """Handle backtest completion."""
        self.backtest_progress.setVisible(False)
        self.run_backtest_button.setEnabled(True)
        self.worker = None

    def _run_optimization(self):
        """Run optimization."""
        if not self.current_strategy:
            QMessageBox.warning(self, "Error", "No strategy selected")
            return

        # Show progress bar
        self.optimize_progress.setVisible(True)
        self.run_optimize_button.setEnabled(False)

        # Prepare optimization data
        params = {}
        for i in range(self.optimize_params_table.rowCount()):
            if self.optimize_params_table.item(i, 4).checkState() == Qt.CheckState.Checked:
                name = self.optimize_params_table.item(i, 0).text()
                params[name] = {
                    'min': float(self.optimize_params_table.item(i, 1).text()),
                    'max': float(self.optimize_params_table.item(i, 2).text()),
                    'step': float(self.optimize_params_table.item(i, 3).text())
                }

        data = {
            'strategy': self.current_strategy.__dict__,
            'params': params,
            'target': self.optimize_target_combo.currentText()
        }

        # Create and start worker
        self.worker = StrategyWorker("optimize", data)
        self.worker.progress.connect(self.optimize_progress.setValue)
        self.worker.result.connect(self._on_optimize_result)
        self.worker.error.connect(self._on_optimize_error)
        self.worker.finished.connect(self._on_optimize_complete)
        self.worker.start()

    @pyqtSlot(dict)
    def _on_optimize_result(self, result: dict[str, Any]):
        """Handle optimization result.

        Args:
            result: Optimization result
        """
        text = "Optimization Results:\n" + "=" * 50 + "\n"
        text += "Best Parameters:\n"

        for param, value in result.get('best_params', {}).items():
            text += f"  {param}: {value}\n"

        text += f"\nBest Sharpe Ratio: {result.get('best_sharpe', 0):.2f}\n"

        self.optimize_results_text.setText(text)

    @pyqtSlot(str)
    def _on_optimize_error(self, error: str):
        """Handle optimization error.

        Args:
            error: Error message
        """
        QMessageBox.critical(self, "Optimization Error", error)
        self.optimize_results_text.setText(f"Error: {error}")

    def _on_optimize_complete(self):
        """Handle optimization completion."""
        self.optimize_progress.setVisible(False)
        self.run_optimize_button.setEnabled(True)
        self.worker = None