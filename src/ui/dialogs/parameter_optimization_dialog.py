"""Parameter Optimization Dialog with AI Guidance.

Provides visual interface for automated parameter optimization.

REFACTORED: Tab creation methods extracted to optimization_tabs_mixin.py
"""

import asyncio
import os
from datetime import datetime

import qasync
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
)

from src.core.backtesting.optimization import (
    OptimizerConfig,
    ParameterOptimizer,
    ParameterRange,
)
from src.core.models.backtest_models import BacktestResult

from .optimization_tabs_mixin import OptimizationTabsMixin


class ParameterOptimizationDialog(OptimizationTabsMixin, QDialog):
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

        # Tab 1: Configuration (from mixin)
        config_tab = self._create_config_tab()
        tabs.addTab(config_tab, "Configuration")

        # Tab 2: Progress (from mixin)
        self.progress_tab = self._create_progress_tab()
        tabs.addTab(self.progress_tab, "Progress")

        # Tab 3: Results (from mixin)
        self.results_tab = self._create_results_tab()
        tabs.addTab(self.results_tab, "Results")

        # Tab 4: AI Insights (from mixin)
        self.ai_tab = self._create_ai_tab()
        tabs.addTab(self.ai_tab, "AI Insights")

        # Tab 5: Chart Visualization (from mixin)
        self.chart_tab = self._create_chart_tab()
        tabs.addTab(self.chart_tab, "Best Result Chart")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self.optimize_btn = QPushButton("Start Optimization")
        self.optimize_btn.clicked.connect(self.start_optimization)
        button_layout.addWidget(self.optimize_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_optimization)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.tabs = tabs
        self.is_running = False

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
            type="technical",
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
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=float(self.capital_spin.value()) if hasattr(self, 'capital_spin') else 10000.0,
            commission=0.001,
            slippage=0.0005,
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

        # Display best result in embedded chart
        if result.best_result:
            self.best_backtest_result = result.best_result
            self.best_result_chart.load_backtest_result(result.best_result)

            # Open chart POPUP window with best result
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
        if not hasattr(parent_app, 'backtest_chart_manager'):
            logger.warning("Parent app doesn't have backtest_chart_manager")
            return

        # Open or focus chart window for symbol
        chart_window = parent_app.backtest_chart_manager.open_or_focus_chart(result.symbol)

        # Load backtest result into chart
        chart_window.load_backtest_result(result)

        logger.info(f"Opened chart popup for {result.symbol} with optimization results")

    def _display_ai_insights(self, insights):
        """Display AI insights."""
        # Clear previous
        for i in reversed(range(self.ai_layout.count())):
            self.ai_layout.itemAt(i).widget().setParent(None)

        # Summary
        summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout()
        summary_label = QLabel(insights.summary)
        summary_label.setWordWrap(True)
        summary_layout.addWidget(summary_label)
        summary_group.setLayout(summary_layout)
        self.ai_layout.addWidget(summary_group)

        # Best parameter analysis
        best_group = QGroupBox("Best Parameter Analysis")
        best_layout = QVBoxLayout()
        best_label = QLabel(insights.best_parameter_analysis)
        best_label.setWordWrap(True)
        best_layout.addWidget(best_label)
        best_group.setLayout(best_layout)
        self.ai_layout.addWidget(best_group)

        # Parameter importance
        if insights.parameter_importance:
            imp_group = QGroupBox("Parameter Importance")
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
            rec_group = QGroupBox("Recommendations")
            rec_layout = QVBoxLayout()
            for i, rec in enumerate(insights.recommendations, 1):
                rec_label = QLabel(f"{i}. {rec.get('improvement', 'N/A')}")
                rec_label.setWordWrap(True)
                rec_layout.addWidget(rec_label)
            rec_group.setLayout(rec_layout)
            self.ai_layout.addWidget(rec_group)

        # Confidence
        conf_label = QLabel(f"Confidence: {insights.confidence_score:.1%}")
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
