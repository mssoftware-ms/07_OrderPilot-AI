"""Entry Analyzer - Indicator Optimization Execution Mixin.

Extracted from entry_analyzer_indicators.py to keep files under 550 LOC.
Handles indicator optimization execution:
- Optimization thread management
- Parameter extraction from UI
- Progress tracking
- Results handling and table population
- Error handling

Date: 2026-01-21
LOC: ~260
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
)

if TYPE_CHECKING:
    import pandas as pd
    from PyQt6.QtCore import QThread

logger = logging.getLogger(__name__)


class IndicatorsOptimizationMixin:
    """Indicator optimization execution functionality.

    Provides optimization workflow with:
    - Parameter extraction from dynamic UI widgets
    - IndicatorOptimizationThread creation and management
    - Progress tracking during optimization
    - Results table population with color-coded scores
    - Error handling and user feedback

    Attributes (defined in parent class):
        _opt_indicator_checkboxes: dict[str, QCheckBox] - Indicator selection
        _param_widgets: dict - Parameter range widgets
        _test_type_entry: QCheckBox - Entry test mode
        _test_type_exit: QCheckBox - Exit test mode
        _trade_side_long: QCheckBox - Long trade side
        _trade_side_short: QCheckBox - Short trade side
        _optimize_btn: QPushButton - Optimize button
        _optimization_progress: QLabel - Progress label
        _optimization_results_table: QTableWidget - Results table
        _draw_indicators_btn: QPushButton - Draw button
        _show_entries_btn: QPushButton - Show entries button
        _create_regime_set_btn: QPushButton - Create regime set button
        _optimization_thread: QThread | None - Worker thread
        _optimization_results: list - Optimization results
        _candles: list[dict] - Chart candles
        _symbol: str - Trading symbol
        _timeframe: str - Chart timeframe
    """

    # Type hints for parent class attributes
    _opt_indicator_checkboxes: dict[str, QCheckBox]
    _param_widgets: dict
    _test_type_entry: QCheckBox
    _test_type_exit: QCheckBox
    _trade_side_long: QCheckBox
    _trade_side_short: QCheckBox
    _optimize_btn: QPushButton
    _optimization_progress: QLabel
    _optimization_results_table: QTableWidget
    _draw_indicators_btn: QPushButton
    _show_entries_btn: QPushButton
    _create_regime_set_btn: QPushButton
    _optimization_thread: QThread | None
    _optimization_results: list
    _candles: list[dict]
    _symbol: str
    _timeframe: str

    def _on_optimize_indicators_clicked(self) -> None:
        """Handle optimize indicators button click.

        Original: entry_analyzer_indicators.py:463-560

        Starts optimization with:
        - Selected indicators and parameter ranges
        - Test mode (entry/exit) and trade side (long/short)
        - Chart data from parent
        - IndicatorOptimizationThread for async execution
        """
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

        # Get parameter ranges from dynamic widgets
        param_ranges = {}
        for indicator_id, params in self._param_widgets.items():
            param_ranges[indicator_id] = {}
            for param_name, widgets in params.items():
                param_ranges[indicator_id][param_name] = {
                    'min': widgets['min'].value(),
                    'max': widgets['max'].value(),
                    'step': widgets['step'].value()
                }

        # Get test mode
        test_type = "entry" if self._test_type_entry.isChecked() else "exit"
        trade_side = "long" if self._trade_side_long.isChecked() else "short"

        # Get chart data from parent
        parent = self.parent()
        if not hasattr(parent, 'data') or parent.data is None:
            QMessageBox.warning(
                self,
                "No Chart Data",
                "Please load chart data before running optimization."
            )
            return

        # Get optimization parameters
        symbol = self._symbol or "UNKNOWN"
        start_date = datetime.now().replace(year=datetime.now().year - 1)
        end_date = datetime.now()
        capital = 10000.0

        # Convert chart candles to DataFrame if available
        chart_df = None
        if self._candles:
            try:
                chart_df = self._convert_candles_to_dataframe(self._candles)
                logger.info(f"Converted {len(chart_df)} candles to DataFrame for optimization")
            except Exception as e:
                logger.error(f"Failed to convert candles: {e}")
                QMessageBox.warning(
                    self,
                    "Data Conversion Error",
                    f"Could not convert candle data to DataFrame.\n\nError: {str(e)}"
                )
                return

        # Create and start optimization thread
        from src.ui.threads.indicator_optimization_thread import IndicatorOptimizationThread

        regime_config_path = None
        if getattr(self, "_regime_config_path", None):
            regime_config_path = str(self._regime_config_path)

        self._optimization_thread = IndicatorOptimizationThread(
            selected_indicators=selected_indicators,
            param_ranges=param_ranges,
            json_config_path=regime_config_path,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital,
            test_type=test_type,
            trade_side=trade_side,
            chart_data=chart_df,
            data_timeframe=self._timeframe,
            parent=self
        )

        # Connect signals
        self._optimization_thread.finished.connect(self._on_optimization_finished)
        self._optimization_thread.progress.connect(self._on_optimization_progress)
        self._optimization_thread.error.connect(self._on_optimization_error)

        # Disable optimize button and start
        self._optimize_btn.setEnabled(False)
        self._optimization_progress.setText("Optimizing...")
        self._optimization_thread.start()

    def _on_optimization_finished(self, results: list) -> None:
        """Handle optimization thread completion.

        Original: entry_analyzer_indicators.py:562-655

        Displays:
        - Sorted results table (by score descending)
        - Color-coded score column (green >70, orange 40-70, red <40)
        - Enables action buttons (Draw Indicators, Show Entries, Create Regime Set)
        - Shows completion message with best result
        """
        # Re-enable optimize button
        self._optimize_btn.setEnabled(True)
        self._optimization_progress.setText("Completed!")

        # Store results
        self._optimization_results = results

        # Enable action buttons
        self._create_regime_set_btn.setEnabled(True)
        self._draw_indicators_btn.setEnabled(True)
        self._show_entries_btn.setEnabled(True)

        if not results:
            QMessageBox.information(
                self,
                "Optimization Complete",
                "No valid results found. Try different parameter ranges or indicators."
            )
            return

        # Sort results by score (descending)
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)

        # Populate results table
        self._optimization_results_table.setRowCount(len(sorted_results))

        for row, result in enumerate(sorted_results):
            # Indicator name
            self._optimization_results_table.setItem(row, 0, QTableWidgetItem(result['indicator']))

            # Parameters (formatted string)
            params_str = ", ".join([f"{k}={v}" for k, v in result['params'].items()])
            self._optimization_results_table.setItem(row, 1, QTableWidgetItem(params_str))

            # Regime
            self._optimization_results_table.setItem(row, 2, QTableWidgetItem(result.get('regime', 'unknown')))

            # Test Type
            self._optimization_results_table.setItem(row, 3, QTableWidgetItem(result.get('test_type', 'entry')))

            # Trade Side
            self._optimization_results_table.setItem(row, 4, QTableWidgetItem(result.get('trade_side', 'long')))

            # Score (color-coded)
            score = result['score']
            score_item = QTableWidgetItem(f"{score:.2f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Color code based on score
            if score >= 70:
                score_item.setBackground(Qt.GlobalColor.green)
            elif score >= 40:
                score_item.setBackground(Qt.GlobalColor.yellow)
            else:
                score_item.setBackground(Qt.GlobalColor.red)

            self._optimization_results_table.setItem(row, 5, score_item)

            # Win Rate
            win_rate = result.get('win_rate', 0.0)
            self._optimization_results_table.setItem(row, 6, QTableWidgetItem(f"{win_rate:.1%}"))

            # Profit Factor
            profit_factor = result.get('profit_factor', 0.0)
            self._optimization_results_table.setItem(row, 7, QTableWidgetItem(f"{profit_factor:.2f}"))

            # Trades
            trades = result.get('trades', 0)
            self._optimization_results_table.setItem(row, 8, QTableWidgetItem(str(trades)))

        # Show completion message
        best = sorted_results[0]
        QMessageBox.information(
            self,
            "Optimization Complete",
            f"Optimization completed with {len(sorted_results)} results.\n\n"
            f"Best result:\n"
            f"• Indicator: {best['indicator']}\n"
            f"• Regime: {best.get('regime', 'unknown')}\n"
            f"• Score: {best['score']:.2f}\n"
            f"• Win Rate: {best.get('win_rate', 0.0):.1%}\n"
            f"• Profit Factor: {best.get('profit_factor', 0.0):.2f}"
        )

    def _on_optimization_progress(self, percentage: int, message: str) -> None:
        """Handle optimization progress updates.

        Original: entry_analyzer_indicators.py:657-664

        Updates progress label with percentage and message.
        """
        self._optimization_progress.setText(f"{percentage}% - {message}")

    def _on_optimization_error(self, error_message: str) -> None:
        """Handle optimization error.

        Original: entry_analyzer_indicators.py:666-682

        Displays error message and re-enables optimize button.
        """
        self._optimize_btn.setEnabled(True)
        self._optimization_progress.setText("Error!")

        QMessageBox.critical(
            self,
            "Optimization Error",
            f"An error occurred during optimization:\n\n{error_message}"
        )

        logger.error(f"Optimization error: {error_message}")

    # Helper method reference (implemented in BacktestConfigMixin)
    def _convert_candles_to_dataframe(self, candles: list[dict]) -> pd.DataFrame:
        """Convert candles list to pandas DataFrame.

        This method is implemented in BacktestConfigMixin.
        """
        pass
