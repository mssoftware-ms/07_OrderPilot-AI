"""Parameter Optimization Dialog with AI Guidance.

Provides visual interface for automated parameter optimization.
"""

import asyncio
import os
from datetime import datetime

import qasync
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.backtesting.optimization import (
    OptimizerConfig,
    ParameterOptimizer,
    ParameterRange,
)
from src.core.models.backtest_models import BacktestMetrics, BacktestResult
from src.ui.widgets.backtest_chart_widget import BacktestChartWidget


class ParameterOptimizationDialog(QDialog):
    """Dialog for AI-guided parameter optimization."""

    def __init__(self, parent=None, current_symbol: str = None):
        """Initialize Parameter Optimization Dialog.

        Args:
            parent: Parent widget
            current_symbol: Currently selected symbol from chart (optional)
        """
        super().__init__(parent)
        self.setWindowTitle("AI Parameter Optimization")
        self.setModal(True)
        self.setMinimumSize(950, 750)

        self.optimization_result = None
        self.ai_insights = None
        self.current_symbol = current_symbol
        self.best_backtest_result = None  # Store best result for chart

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Configuration
        config_tab = self._create_config_tab()
        tabs.addTab(config_tab, "⚙️ Configuration")

        # Tab 2: Progress
        self.progress_tab = self._create_progress_tab()
        tabs.addTab(self.progress_tab, "⏱️ Progress")

        # Tab 3: Results
        self.results_tab = self._create_results_tab()
        tabs.addTab(self.results_tab, "📊 Results")

        # Tab 4: AI Insights
        self.ai_tab = self._create_ai_tab()
        tabs.addTab(self.ai_tab, "🤖 AI Insights")

        # Tab 5: Chart Visualization ✨ NEW
        self.chart_tab = self._create_chart_tab()
        tabs.addTab(self.chart_tab, "📈 Best Result Chart")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self.optimize_btn = QPushButton("🚀 Start Optimization")
        self.optimize_btn.clicked.connect(self.start_optimization)
        button_layout.addWidget(self.optimize_btn)

        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_optimization)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.tabs = tabs
        self.is_running = False

    def _create_config_tab(self) -> QWidget:
        """Create configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Strategy Selection
        strategy_group = QGroupBox("Strategy")
        strategy_layout = QFormLayout()

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "SMA Crossover",
            "RSI Mean Reversion",
            "MACD Momentum"
        ])
        strategy_layout.addRow("Strategy:", self.strategy_combo)

        self.symbol_edit = QLineEdit()
        self.symbol_edit.setText(self.current_symbol.upper() if self.current_symbol else "AAPL")
        strategy_layout.addRow("Symbol:", self.symbol_edit)

        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)

        # Parameter Ranges
        param_group = QGroupBox("Parameter Ranges to Optimize")
        param_layout = QFormLayout()

        # Fast Period
        fast_label = QLabel("Fast Period:")
        fast_widget = QWidget()
        fast_layout = QHBoxLayout(fast_widget)
        fast_layout.setContentsMargins(0, 0, 0, 0)

        self.fast_min = QSpinBox()
        self.fast_min.setRange(5, 50)
        self.fast_min.setValue(10)
        self.fast_min.setPrefix("Min: ")
        fast_layout.addWidget(self.fast_min)

        self.fast_max = QSpinBox()
        self.fast_max.setRange(5, 50)
        self.fast_max.setValue(20)
        self.fast_max.setPrefix("Max: ")
        fast_layout.addWidget(self.fast_max)

        self.fast_step = QSpinBox()
        self.fast_step.setRange(1, 10)
        self.fast_step.setValue(5)
        self.fast_step.setPrefix("Step: ")
        fast_layout.addWidget(self.fast_step)

        param_layout.addRow(fast_label, fast_widget)

        # Slow Period
        slow_label = QLabel("Slow Period:")
        slow_widget = QWidget()
        slow_layout = QHBoxLayout(slow_widget)
        slow_layout.setContentsMargins(0, 0, 0, 0)

        self.slow_min = QSpinBox()
        self.slow_min.setRange(20, 100)
        self.slow_min.setValue(40)
        self.slow_min.setPrefix("Min: ")
        slow_layout.addWidget(self.slow_min)

        self.slow_max = QSpinBox()
        self.slow_max.setRange(20, 100)
        self.slow_max.setValue(60)
        self.slow_max.setPrefix("Max: ")
        slow_layout.addWidget(self.slow_max)

        self.slow_step = QSpinBox()
        self.slow_step.setRange(5, 20)
        self.slow_step.setValue(10)
        self.slow_step.setPrefix("Step: ")
        slow_layout.addWidget(self.slow_step)

        param_layout.addRow(slow_label, slow_widget)

        # Stop Loss
        sl_label = QLabel("Stop Loss %:")
        sl_widget = QWidget()
        sl_layout = QHBoxLayout(sl_widget)
        sl_layout.setContentsMargins(0, 0, 0, 0)

        self.sl_min = QDoubleSpinBox()
        self.sl_min.setRange(0.5, 10.0)
        self.sl_min.setValue(1.5)
        self.sl_min.setSingleStep(0.5)
        self.sl_min.setPrefix("Min: ")
        self.sl_min.setSuffix("%")
        sl_layout.addWidget(self.sl_min)

        self.sl_max = QDoubleSpinBox()
        self.sl_max.setRange(0.5, 10.0)
        self.sl_max.setValue(3.0)
        self.sl_max.setSingleStep(0.5)
        self.sl_max.setPrefix("Max: ")
        self.sl_max.setSuffix("%")
        sl_layout.addWidget(self.sl_max)

        self.sl_step = QDoubleSpinBox()
        self.sl_step.setRange(0.1, 2.0)
        self.sl_step.setValue(0.5)
        self.sl_step.setSingleStep(0.1)
        self.sl_step.setPrefix("Step: ")
        self.sl_step.setSuffix("%")
        sl_layout.addWidget(self.sl_step)

        param_layout.addRow(sl_label, sl_widget)

        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

        # Optimization Settings
        opt_group = QGroupBox("Optimization Settings")
        opt_layout = QFormLayout()

        self.metric_combo = QComboBox()
        self.metric_combo.addItems([
            "Sharpe Ratio",
            "Sortino Ratio",
            "Total Return",
            "Profit Factor"
        ])
        opt_layout.addRow("Optimize For:", self.metric_combo)

        self.ai_guidance = QCheckBox("Enable AI Guidance")
        self.ai_guidance.setChecked(True)
        opt_layout.addRow("AI Guidance:", self.ai_guidance)

        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 5)
        self.iterations_spin.setValue(2)
        opt_layout.addRow("AI Iterations:", self.iterations_spin)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # Combination info
        self.combo_label = QLabel()
        self.combo_label.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
        self._update_combination_count()

        # Connect signals to update count
        for widget in [self.fast_min, self.fast_max, self.fast_step,
                      self.slow_min, self.slow_max, self.slow_step,
                      self.sl_min, self.sl_max, self.sl_step]:
            widget.valueChanged.connect(self._update_combination_count)

        layout.addWidget(self.combo_label)
        layout.addStretch()

        return widget

    def _update_combination_count(self):
        """Update total combination count label."""
        import numpy as np

        fast_count = len(np.arange(
            self.fast_min.value(),
            self.fast_max.value() + 1,
            self.fast_step.value()
        ))

        slow_count = len(np.arange(
            self.slow_min.value(),
            self.slow_max.value() + 1,
            self.slow_step.value()
        ))

        sl_count = len(np.arange(
            self.sl_min.value(),
            self.sl_max.value() + 0.01,
            self.sl_step.value()
        ))

        total = fast_count * slow_count * sl_count

        self.combo_label.setText(
            f"Total combinations to test: {total} "
            f"({fast_count} × {slow_count} × {sl_count})\n"
            f"Estimated time: {total * 0.2:.1f}s (mock backtests)"
        )

    def _create_progress_tab(self) -> QWidget:
        """Create progress monitoring tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready to optimize")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; padding: 20px;")
        layout.addWidget(self.status_label)

        # Progress log
        self.progress_log = QTextEdit()
        self.progress_log.setReadOnly(True)
        layout.addWidget(self.progress_log)

        return widget

    def _create_results_tab(self) -> QWidget:
        """Create results display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlainText("Run optimization to see results...")

        layout.addWidget(self.results_text)

        return widget

    def _create_ai_tab(self) -> QWidget:
        """Create AI insights tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.ai_content = QWidget()
        self.ai_layout = QVBoxLayout(self.ai_content)

        placeholder = QLabel("AI insights will appear here after optimization with AI guidance...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; padding: 40px;")
        self.ai_layout.addWidget(placeholder)

        scroll.setWidget(self.ai_content)
        layout.addWidget(scroll)

        return widget

    def _create_chart_tab(self) -> QWidget:
        """Create chart visualization tab for best result."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Info label
        info_label = QLabel("Best parameter set backtest visualization:")
        info_label.setStyleSheet("padding: 10px; font-weight: bold;")
        layout.addWidget(info_label)

        # Add BacktestChartWidget
        self.best_result_chart = BacktestChartWidget()
        layout.addWidget(self.best_result_chart)

        return widget

    @qasync.asyncSlot()
    async def start_optimization(self):
        """Start parameter optimization."""
        import numpy as np

        self.is_running = True
        self.optimize_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Get parameter ranges
        fast_values = list(np.arange(
            self.fast_min.value(),
            self.fast_max.value() + 1,
            self.fast_step.value()
        ))

        slow_values = list(np.arange(
            self.slow_min.value(),
            self.slow_max.value() + 1,
            self.slow_step.value()
        ))

        sl_values = list(np.arange(
            self.sl_min.value(),
            self.sl_max.value() + 0.01,
            self.sl_step.value()
        ))

        ranges = [
            ParameterRange(name="fast_period", values=[int(v) for v in fast_values]),
            ParameterRange(name="slow_period", values=[int(v) for v in slow_values]),
            ParameterRange(name="stop_loss_pct", values=[float(v) for v in sl_values])
        ]

        total_tests = len(fast_values) * len(slow_values) * len(sl_values)

        # Switch to progress tab
        self.tabs.setCurrentIndex(1)

        # Clear progress log
        self.progress_log.clear()
        self.log_progress(f"Starting optimization with {total_tests} combinations...")

        try:
            # Create optimizer
            metric_map = {
                "Sharpe Ratio": "sharpe_ratio",
                "Sortino Ratio": "sortino_ratio",
                "Total Return": "total_return_pct",
                "Profit Factor": "profit_factor"
            }

            config = OptimizerConfig(
                use_ai_guidance=self.ai_guidance.isChecked(),
                primary_metric=metric_map[self.metric_combo.currentText()],
                ai_analysis_frequency=max(total_tests // 4, 5)
            )

            # CRITICAL: Use REAL backtest runner, not mock
            optimizer = ParameterOptimizer(self._run_real_backtest, config)

            # Run optimization
            tests_completed = 0

            async def track_progress():
                nonlocal tests_completed
                while self.is_running and tests_completed < total_tests:
                    await asyncio.sleep(0.1)

            # Start progress tracking
            progress_task = asyncio.create_task(track_progress())

            # Run optimization
            if self.ai_guidance.isChecked():
                self.log_progress("Using AI guidance for optimization...")

                # Check for API key
                api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("AI guidance requires API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)")

                result, insights = await optimizer.optimize_with_ai(
                    ranges,
                    max_iterations=self.iterations_spin.value()
                )
                self.ai_insights = insights

            else:
                self.log_progress("Running standard grid search...")
                result = await optimizer.grid_search(ranges)

            self.optimization_result = result

            # Display results
            self.log_progress(f"\nOptimization complete! Best score: {result.best_score:.4f}")
            self._display_results(result)

            # Display AI insights if available
            if self.ai_insights:
                self._display_ai_insights(self.ai_insights)

            # Switch to results tab
            self.tabs.setCurrentIndex(2)

            QMessageBox.information(
                self,
                "Optimization Complete",
                f"Found best parameters with score {result.best_score:.4f}\n\n"
                f"Check Results and AI Insights tabs for details."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Optimization failed:\n{str(e)}")
            self.log_progress(f"\nError: {str(e)}")

        finally:
            self.is_running = False
            self.optimize_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setValue(100)

    async def _run_real_backtest(self, params: dict) -> BacktestResult:
        """Run REAL backtest with actual market data (NO MOCK!).

        Args:
            params: Strategy parameters to test

        Returns:
            BacktestResult with real metrics from backtrader
        """
        from src.core.backtesting.backtrader_integration import BacktraderIntegration, BacktestConfig
        from src.core.strategy.definition import StrategyConfig
        from src.core.market_data.history_provider import HistoryManager
        from src.core.models.common import Timeframe

        # Get history manager for real data
        history_manager = HistoryManager()

        # Create strategy config from parameters
        strategy_config = StrategyConfig(
            name=self.strategy_combo.currentText(),
            type="technical",  # or get from UI
            parameters=params,
            risk_params={
                "stop_loss_pct": params.get("stop_loss_pct", 2.0),
                "take_profit_pct": params.get("take_profit_pct", 5.0),
                "position_size_pct": params.get("position_size_pct", 100.0)
            }
        )

        # Create backtest config
        backtest_config = BacktestConfig(
            symbol=self.symbol_edit.text() or "AAPL",
            timeframe=Timeframe.DAY,
            start_date=datetime(2023, 1, 1),  # Get from UI if available
            end_date=datetime(2023, 12, 31),
            initial_capital=float(self.capital_spin.value()) if hasattr(self, 'capital_spin') else 10000.0,
            commission=0.001,  # 0.1%
            slippage=0.0005,   # 0.05%
            strategy=strategy_config
        )

        # Run REAL backtest
        backtrader = BacktraderIntegration(
            history_manager=history_manager,
            config=backtest_config
        )

        # Execute (this runs the actual backtest with real data)
        result = backtrader.run()

        return result

    def _display_results(self, result):
        """Display optimization results."""
        text = "=" * 70 + "\n"
        text += "PARAMETER OPTIMIZATION RESULTS\n"
        text += "=" * 70 + "\n\n"

        text += f"Total Tests: {result.total_tests}\n"
        text += f"Successful: {result.successful_tests}\n"
        text += f"Time: {result.optimization_time_seconds:.2f}s\n\n"

        text += "BEST PARAMETERS:\n"
        text += "-" * 70 + "\n"
        for param, value in result.best_parameters.items():
            text += f"  {param}: {value}\n"
        text += f"\nBest Score: {result.best_score:.4f}\n\n"

        if result.best_result:
            text += "BEST RESULT METRICS:\n"
            text += "-" * 70 + "\n"
            text += f"  Total Return: {result.best_result.metrics.total_return_pct:.2f}%\n"
            text += f"  Sharpe Ratio: {result.best_result.metrics.sharpe_ratio:.2f}\n"
            text += f"  Win Rate: {result.best_result.metrics.win_rate:.2%}\n"
            text += f"  Max Drawdown: {result.best_result.metrics.max_drawdown_pct:.2f}%\n\n"

        text += "PARAMETER SENSITIVITY:\n"
        text += "-" * 70 + "\n"
        for param, analysis in result.sensitivity_analysis.items():
            text += f"  {param}: {analysis['impact'].upper()} impact "
            text += f"(score: {analysis['sensitivity_score']:.4f})\n"

        self.results_text.setPlainText(text)

        # ✨ NEW: Display best result in embedded chart
        if result.best_result:
            self.best_backtest_result = result.best_result
            self.best_result_chart.load_backtest_result(result.best_result)

            # ✨ NEW: Open chart POPUP window with best result
            self._open_chart_popup(result.best_result)

            # Switch to results tab
            self.tabs.setCurrentIndex(2)

    def _open_chart_popup(self, result):
        """Open chart popup window with backtest results.

        Args:
            result: BacktestResult to display
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get parent app to access chart_window_manager
        parent_app = self.parent()
        if not hasattr(parent_app, 'chart_window_manager'):
            logger.warning("Parent app doesn't have chart_window_manager")
            return

        # Open or focus chart window for symbol
        chart_window = parent_app.chart_window_manager.open_or_focus_chart(result.symbol)

        # Load backtest result into chart
        chart_window.load_backtest_result(result)

        logger.info(f"Opened chart popup for {result.symbol} with optimization results")

    def _display_ai_insights(self, insights):
        """Display AI insights."""
        # Clear previous
        for i in reversed(range(self.ai_layout.count())):
            self.ai_layout.itemAt(i).widget().setParent(None)

        # Summary
        summary_group = QGroupBox("📊 Summary")
        summary_layout = QVBoxLayout()
        summary_label = QLabel(insights.summary)
        summary_label.setWordWrap(True)
        summary_layout.addWidget(summary_label)
        summary_group.setLayout(summary_layout)
        self.ai_layout.addWidget(summary_group)

        # Best parameter analysis
        best_group = QGroupBox("🎯 Best Parameter Analysis")
        best_layout = QVBoxLayout()
        best_label = QLabel(insights.best_parameter_analysis)
        best_label.setWordWrap(True)
        best_layout.addWidget(best_label)
        best_group.setLayout(best_layout)
        self.ai_layout.addWidget(best_group)

        # Parameter importance
        if insights.parameter_importance:
            imp_group = QGroupBox("📈 Parameter Importance")
            imp_layout = QFormLayout()
            for param, score in sorted(
                insights.parameter_importance.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                imp_layout.addRow(f"{param}:", QLabel(f"{score:.2f}"))
            imp_group.setLayout(imp_layout)
            self.ai_layout.addWidget(imp_group)

        # Recommendations
        if insights.recommendations:
            rec_group = QGroupBox("💡 Recommendations")
            rec_layout = QVBoxLayout()
            for i, rec in enumerate(insights.recommendations, 1):
                rec_label = QLabel(f"{i}. {rec.get('improvement', 'N/A')}")
                rec_label.setWordWrap(True)
                rec_layout.addWidget(rec_label)
            rec_group.setLayout(rec_layout)
            self.ai_layout.addWidget(rec_group)

        # Confidence
        conf_label = QLabel(f"🎯 Confidence: {insights.confidence_score:.1%}")
        conf_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        self.ai_layout.addWidget(conf_label)

        self.ai_layout.addStretch()

    def log_progress(self, message: str):
        """Log progress message."""
        self.progress_log.append(message)
        self.status_label.setText(message.split('\n')[0])  # First line only

    @pyqtSlot()
    def stop_optimization(self):
        """Stop optimization."""
        self.is_running = False
        self.log_progress("\nOptimization stopped by user.")
