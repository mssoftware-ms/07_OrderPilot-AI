"""Backtest Mixin for ChartWindow.

Contains backtest execution, visualization, and optimization methods.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QTableWidgetItem

logger = logging.getLogger(__name__)


class BacktestMixin:
    """Mixin providing backtest functionality for ChartWindow."""

    def _apply_strategy(self):
        """Apply selected strategy to chart."""
        from src.core.backtesting.backtrader_integration import (
            BacktestConfig, BacktraderIntegration
        )
        from src.core.market_data.history_provider import Timeframe

        strategy_name = self.strategy_combo.currentText()
        logger.info(f"Applying strategy: {strategy_name} to chart {self.symbol}")

        try:
            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
                QMessageBox.warning(self, "No Data", "Please load chart data first.")
                return

            chart_data = self.chart_widget.data.copy()
            start_datetime = chart_data.index[0].to_pydatetime()
            end_datetime = chart_data.index[-1].to_pydatetime()

            strategy_config = self._create_strategy_config_from_ui()

            backtest_config = BacktestConfig(
                start_date=start_datetime,
                end_date=end_datetime,
                initial_cash=Decimal("10000"),
                commission=0.001,
                slippage=0.0005,
                timeframe=Timeframe.DAY,
                symbols=[self.symbol],
                strategies=[strategy_config]
            )

            if not self.history_manager:
                logger.error("No history manager")
                return

            backtrader = BacktraderIntegration(
                history_manager=self.history_manager,
                config=backtest_config
            )

            result = backtrader.run()

            if not result:
                logger.warning("No result from strategy application")
                return

            if hasattr(self.chart_widget, '_execute_js'):
                self.chart_widget._execute_js("window.chartAPI.clearMarkers();")

            self._add_trade_markers_to_chart(result)

            trade_count = len(result.trades)
            win_rate = result.metrics.win_rate * 100 if result.metrics.total_trades > 0 else 0

            msg = f"Strategy applied: {trade_count} trades found (Win Rate: {win_rate:.1f}%)"
            logger.info(msg)

            if hasattr(self.chart_widget, 'market_status_label'):
                self.chart_widget.market_status_label.setText(msg)
                self.chart_widget.market_status_label.setStyleSheet("color: #28a745; font-weight: bold;")

        except Exception as e:
            logger.error(f"Failed to apply strategy: {e}", exc_info=True)
            QMessageBox.warning(self, "Strategy Error", f"Failed to apply strategy:\n{e}")

    def _run_backtest(self):
        """Run backtest with chart data."""
        from src.core.backtesting.backtrader_integration import (
            BacktestConfig, BacktraderIntegration
        )
        from src.core.market_data.history_provider import Timeframe

        logger.info(f"Starting backtest for {self.symbol}")

        try:
            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
                QMessageBox.warning(
                    self, "No Chart Data",
                    "Please load chart data first before running a backtest!"
                )
                return

            chart_data = self.chart_widget.data.copy()
            logger.info(f"Using chart data: {len(chart_data)} bars")

            progress = QProgressDialog(
                f"Running backtest on {len(chart_data)} bars...",
                "Cancel", 0, 0, self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Running Backtest")
            progress.show()

            start_date = self.backtest_start_date.date().toPyDate()
            end_date = self.backtest_end_date.date().toPyDate()
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            mask = (chart_data.index >= start_datetime) & (chart_data.index <= end_datetime)
            backtest_data = chart_data[mask]

            if backtest_data.empty:
                progress.close()
                QMessageBox.warning(
                    self, "No Data in Date Range",
                    f"No chart data found between {start_date} and {end_date}."
                )
                return

            initial_cash = Decimal(str(self.initial_capital.value()))
            strategy_config = self._create_strategy_config_from_ui()

            backtest_config = BacktestConfig(
                start_date=start_datetime,
                end_date=end_datetime,
                initial_cash=initial_cash,
                commission=0.001,
                slippage=0.0005,
                timeframe=Timeframe.DAY,
                symbols=[self.symbol],
                strategies=[strategy_config]
            )

            if not self.history_manager:
                raise ValueError("No history manager available for backtest")

            backtrader = BacktraderIntegration(
                history_manager=self.history_manager,
                config=backtest_config
            )

            try:
                result = backtrader.run()
            except Exception as backtest_error:
                progress.close()
                logger.error(f"Backtest execution error: {backtest_error}", exc_info=True)
                QMessageBox.critical(
                    self, "Backtest Failed",
                    f"Backtest execution failed:\n\n{str(backtest_error)}"
                )
                return

            progress.close()

            if not result:
                QMessageBox.warning(self, "Backtest Failed", "No backtest result returned.")
                return

            logger.info(f"Backtest completed: {result.metrics.total_trades} trades")

            self._display_backtest_results(result)
            self._add_trade_markers_to_chart(result)
            self.panel_tabs.setCurrentWidget(self.results_tab)

            if not self.dock_widget.isVisible():
                self.dock_widget.setVisible(True)
                if hasattr(self.chart_widget, 'toggle_panel_button'):
                    self.chart_widget.toggle_panel_button.setChecked(True)
                    self._update_toggle_button_text()

        except Exception as e:
            logger.error(f"Backtest execution failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Backtest Error", f"Failed to run backtest:\n{str(e)}")

    def _create_strategy_config_from_ui(self) -> 'StrategyConfig':
        """Create StrategyConfig from current UI parameters."""
        from src.core.strategy.engine import StrategyConfig, StrategyType
        from src.core.indicators.engine import IndicatorConfig, IndicatorType

        strategy_name = self.strategy_combo.currentText()

        strategy_type_map = {
            "MACD Crossover": StrategyType.TREND_FOLLOWING,
            "RSI Mean Reversion": StrategyType.MEAN_REVERSION,
            "Bollinger Bands": StrategyType.MEAN_REVERSION,
            "Moving Average": StrategyType.TREND_FOLLOWING,
            "Custom Strategy": StrategyType.CUSTOM
        }
        strategy_type = strategy_type_map.get(strategy_name, StrategyType.CUSTOM)

        parameters = {
            "fast_period": self.fast_period.value(),
            "slow_period": self.slow_period.value(),
            "signal_period": self.signal_period.value()
        }

        risk_params = {
            "stop_loss_pct": self.stop_loss.value(),
            "take_profit_pct": self.take_profit.value(),
            "position_size_pct": self.position_size.value()
        }

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
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14})
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
                IndicatorConfig(type=IndicatorType.SMA, params={"period": parameters["fast_period"]}),
                IndicatorConfig(type=IndicatorType.SMA, params={"period": parameters["slow_period"]})
            ])

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
        """Display backtest results in Results tab."""
        from src.core.models.backtest_models import BacktestResult

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid result type: {type(result)}")
            return

        summary_text = (
            f"Backtest Completed: {result.symbol}\n"
            f"Period: {result.start.strftime('%Y-%m-%d')} to {result.end.strftime('%Y-%m-%d')}\n"
            f"Strategy: {result.strategy_name or 'Unknown'}\n"
            f"Total P&L: €{result.total_pnl:,.2f} ({result.total_pnl_pct:+.2f}%)"
        )
        self.results_summary.setText(summary_text)

        metrics = result.metrics
        metrics_data = [
            ("Total Return", f"{result.total_pnl_pct:+.2f}%"),
            ("Annual Return", f"{metrics.annual_return_pct:+.2f}%" if metrics.annual_return_pct else "N/A"),
            ("Net Profit", f"€{result.total_pnl:,.2f}"),
            ("Final Capital", f"€{result.final_capital:,.2f}"),
            ("", ""),
            ("Total Trades", str(metrics.total_trades)),
            ("Winning Trades", f"{metrics.winning_trades} ({metrics.win_rate:.1%})"),
            ("Losing Trades", f"{metrics.losing_trades}"),
            ("Win Rate", f"{metrics.win_rate:.2%}"),
            ("", ""),
            ("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%"),
            ("Sharpe Ratio", f"{metrics.sharpe_ratio:.3f}" if metrics.sharpe_ratio else "N/A"),
            ("Sortino Ratio", f"{metrics.sortino_ratio:.3f}" if metrics.sortino_ratio else "N/A"),
            ("Profit Factor", f"{metrics.profit_factor:.2f}"),
            ("", ""),
            ("Average Win", f"€{metrics.avg_win:,.2f}"),
            ("Average Loss", f"€{metrics.avg_loss:,.2f}"),
            ("Largest Win", f"€{metrics.largest_win:,.2f}"),
            ("Largest Loss", f"€{metrics.largest_loss:,.2f}"),
            ("Expectancy", f"€{metrics.expectancy:,.2f}" if metrics.expectancy else "N/A"),
            ("", ""),
            ("Max Consecutive Wins", str(metrics.max_consecutive_wins)),
            ("Max Consecutive Losses", str(metrics.max_consecutive_losses)),
        ]

        self.metrics_table.setRowCount(len(metrics_data))
        for i, (metric, value) in enumerate(metrics_data):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(value))

        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.resizeColumnToContents(0)

        logger.info("Backtest results displayed in Results tab")

    def _add_trade_markers_to_chart(self, result: 'BacktestResult'):
        """Add Entry/Exit markers to chart."""
        from src.core.models.backtest_models import BacktestResult, TradeSide

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid result type: {type(result)}")
            return

        show_entries = self.show_entry_markers.isChecked()
        show_exits = self.show_exit_markers.isChecked()

        logger.info(f"Adding trade markers to chart: {len(result.trades)} trades")

        markers = []

        for trade in result.trades:
            if show_entries:
                entry_time = int(trade.entry_time.timestamp())
                entry_marker = {
                    "time": entry_time,
                    "position": "belowBar" if trade.side == TradeSide.LONG else "aboveBar",
                    "color": "#26a69a" if trade.side == TradeSide.LONG else "#ef5350",
                    "shape": "arrowUp" if trade.side == TradeSide.LONG else "arrowDown",
                    "text": f"{'BUY' if trade.side == TradeSide.LONG else 'SELL'} @ €{trade.entry_price:.2f}"
                }
                markers.append(entry_marker)

            if show_exits and trade.exit_time and trade.exit_price:
                exit_time = int(trade.exit_time.timestamp())
                exit_marker = {
                    "time": exit_time,
                    "position": "aboveBar" if trade.side == TradeSide.LONG else "belowBar",
                    "color": "#26a69a" if trade.is_winner else "#ef5350",
                    "shape": "circle",
                    "text": f"EXIT @ €{trade.exit_price:.2f} ({trade.realized_pnl_pct:+.2f}%)"
                }
                markers.append(exit_marker)

        if hasattr(self.chart_widget, '_execute_js'):
            markers_json = json.dumps(markers)
            js_code = f"window.chartAPI.addTradeMarkers({markers_json});"
            self.chart_widget._execute_js(js_code)
            logger.info(f"Added {len(markers)} trade markers to chart")
        else:
            logger.warning("Chart widget doesn't have _execute_js method")

    def _start_optimization(self):
        """Start parameter optimization."""
        from src.core.backtesting.optimization import (
            ParameterOptimizer, ParameterRange, OptimizerConfig
        )

        logger.info(f"Starting parameter optimization for {self.symbol}")

        if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
            QMessageBox.warning(
                self, "No Chart Data",
                "Please load chart data first before running optimization!"
            )
            return

        try:
            progress = QProgressDialog(
                "Running parameter optimization...",
                "Cancel", 0, 0, self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Parameter Optimization")
            progress.show()

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

            metric_name = self.opt_metric.currentText()
            metric_map = {
                "Sharpe Ratio": "sharpe_ratio",
                "Total Return": "total_return_pct",
                "Profit Factor": "profit_factor",
                "Win Rate": "win_rate"
            }
            primary_metric = metric_map.get(metric_name, "sharpe_ratio")

            config = OptimizerConfig(
                max_workers=2,
                timeout_per_test=60,
                primary_metric=primary_metric,
                ai_enabled=self.use_ai_guidance.isChecked()
            )

            progress.close()

            QMessageBox.information(
                self, "Optimization Setup",
                f"Parameter Optimization configured:\n\n"
                f"Fast Period: {self.opt_fast_min.value()}-{self.opt_fast_max.value()}\n"
                f"Slow Period: {self.opt_slow_min.value()}-{self.opt_slow_max.value()}\n"
                f"Metric: {metric_name}\n"
                f"Max Iterations: {self.max_iterations.value()}\n"
                f"AI Guidance: {'Yes' if self.use_ai_guidance.isChecked() else 'No'}"
            )

            logger.info("Optimization setup complete")

        except Exception as e:
            logger.error(f"Optimization setup failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Optimization Error", f"Failed to set up optimization:\n{str(e)}")
