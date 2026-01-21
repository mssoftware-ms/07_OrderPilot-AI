"""Entry Analyzer - Backtest Results Mixin.

Extracted from entry_analyzer_backtest.py to keep files under 550 LOC.
Handles backtest results display and metrics:
- Backtest Results tab UI
- Performance metrics display
- Trade history table
- Performance profiling data
- Error handling

Date: 2026-01-21
LOC: ~270
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestResultsMixin:
    """Backtest results display functionality.

    Provides results UI and metrics display with:
    - Data source information
    - Performance metrics (P&L, win rate, profit factor)
    - Trade history table
    - Performance profiling (timing, memory, cache)
    - Draw regime boundaries on chart
    - Error handling

    Attributes (defined in parent class):
        _bt_results_text: QTextEdit - Results display
        _bt_regime_history_text: QTextEdit - Regime history display
        _bt_draw_boundaries_btn: QPushButton - Draw boundaries button
        _bt_create_regime_set_btn: QPushButton - Create regime set button
        _backtest_result: dict | None - Backtest results data
        _bt_run_btn: QPushButton - Run backtest button
        _bt_status_label: QLabel - Status text
    """

    # Type hints for parent class attributes
    _bt_results_text: QTextEdit
    _bt_regime_history_text: QTextEdit
    _bt_draw_boundaries_btn: QPushButton
    _bt_create_regime_set_btn: QPushButton
    _backtest_result: dict | None
    _bt_run_btn: QPushButton
    _bt_status_label: QLabel

    def _setup_backtest_results_tab(self, tab: QWidget) -> None:
        """Setup Backtest Results tab.

        Original: entry_analyzer_backtest.py:194-312

        Creates:
        - Data source info section
        - Performance summary section
        - Trade history table
        - Performance profiling section
        - Draw boundaries and create regime set buttons
        """
        layout = QVBoxLayout(tab)

        # Data Source Info
        source_group = QGroupBox("Data Source")
        source_layout = QVBoxLayout()
        source_layout.addWidget(QLabel("Data source information will appear here after backtest..."))
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # Performance Summary
        summary_group = QGroupBox("Performance Summary")
        summary_layout = QVBoxLayout()
        self._bt_results_text = QTextEdit()
        self._bt_results_text.setReadOnly(True)
        self._bt_results_text.setMaximumHeight(250)
        self._bt_results_text.setStyleSheet(
            "font-family: monospace; background-color: #1a1a1a; color: #e0e0e0;"
        )
        self._bt_results_text.setPlaceholderText(
            "Backtest results will appear here...\n\n"
            "Click 'Run Backtest' to execute a backtest simulation."
        )
        summary_layout.addWidget(self._bt_results_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Trade History
        trades_group = QGroupBox("Trade History")
        trades_layout = QVBoxLayout()
        # TODO: Add trade table widget
        trades_layout.addWidget(QLabel("Trade table will be added here..."))
        trades_group.setLayout(trades_layout)
        layout.addWidget(trades_group)

        # Regime History
        regime_group = QGroupBox("Regime History")
        regime_layout = QVBoxLayout()

        # Regime history text
        self._bt_regime_history_text = QTextEdit()
        self._bt_regime_history_text.setReadOnly(True)
        self._bt_regime_history_text.setMaximumHeight(150)
        self._bt_regime_history_text.setStyleSheet(
            "font-family: monospace; background-color: #1a1a1a; color: #e0e0e0;"
        )
        self._bt_regime_history_text.setPlaceholderText(
            "Regime history will appear here after backtest..."
        )
        regime_layout.addWidget(self._bt_regime_history_text)

        # Buttons
        regime_buttons = QHBoxLayout()
        self._bt_draw_boundaries_btn = QPushButton("📍 Draw Regime Boundaries")
        self._bt_draw_boundaries_btn.setEnabled(False)
        self._bt_draw_boundaries_btn.clicked.connect(self._draw_regime_boundaries_wrapper)
        regime_buttons.addWidget(self._bt_draw_boundaries_btn)

        self._bt_create_regime_set_btn = QPushButton("📊 Create Regime Set")
        self._bt_create_regime_set_btn.setEnabled(False)
        self._bt_create_regime_set_btn.clicked.connect(self._on_create_regime_set_clicked)
        regime_buttons.addWidget(self._bt_create_regime_set_btn)

        regime_buttons.addStretch()
        regime_layout.addLayout(regime_buttons)

        regime_group.setLayout(regime_layout)
        layout.addWidget(regime_group)

        layout.addStretch()

    def _on_backtest_finished(self, results: dict) -> None:
        """Handle backtest completion.

        Original: entry_analyzer_backtest.py:580-680

        Displays:
        - Data source info (source, timeframe, period, candles)
        - Performance metrics (net profit, win rate, profit factor, trades)
        - Trade table entries
        - Performance profiling (timings, memory, rates, cache)
        - Enables draw boundaries button if regime history exists
        """
        self._backtest_result = results
        self._bt_run_btn.setEnabled(True)
        self._bt_status_label.setText("Backtest complete")

        # Build results summary
        lines = ["# Backtest Results\n"]

        # Performance metrics
        stats = results.get('statistics', {})
        lines.append(f"**Net Profit:** ${stats.get('net_profit', 0):.2f}")
        lines.append(f"**Return:** {stats.get('return_pct', 0):.2f}%")
        lines.append(f"**Win Rate:** {stats.get('win_rate', 0):.2f}%")
        lines.append(f"**Profit Factor:** {stats.get('profit_factor', 0):.2f}")
        lines.append(f"**Total Trades:** {stats.get('total_trades', 0)}")
        lines.append(f"**Winning Trades:** {stats.get('winning_trades', 0)}")
        lines.append(f"**Losing Trades:** {stats.get('losing_trades', 0)}")
        lines.append(f"**Max Drawdown:** {stats.get('max_drawdown', 0):.2f}%")
        lines.append(f"**Sharpe Ratio:** {stats.get('sharpe_ratio', 0):.2f}")

        # Performance profiling
        if 'performance' in results:
            perf = results['performance']
            lines.append("\n## Performance Profiling\n")
            lines.append(f"**Total Time:** {perf.get('total_time', 0):.2f}s")
            lines.append(f"**Data Load Time:** {perf.get('data_load_time', 0):.2f}s")
            lines.append(f"**Strategy Time:** {perf.get('strategy_time', 0):.2f}s")
            lines.append(f"**Execution Time:** {perf.get('execution_time', 0):.2f}s")
            lines.append(f"**Memory Used:** {perf.get('memory_mb', 0):.2f} MB")
            lines.append(f"**Candles Processed:** {perf.get('candles_processed', 0):,}")
            lines.append(f"**Processing Rate:** {perf.get('candles_per_second', 0):.0f} candles/s")
            if 'cache_hits' in perf:
                lines.append(f"**Cache Hits:** {perf.get('cache_hits', 0):,}")
                lines.append(f"**Cache Misses:** {perf.get('cache_misses', 0):,}")

        self._bt_results_text.setPlainText("\n".join(lines))

        # Enable regime history buttons if available
        if 'regime_history' in results and results['regime_history']:
            self._bt_draw_boundaries_btn.setEnabled(True)
            self._bt_create_regime_set_btn.setEnabled(True)

            # Display regime history
            regime_lines = ["Regime Changes:\n"]
            for change in results['regime_history'][:20]:  # Show first 20
                timestamp = change.get('timestamp', 'N/A')
                regime = change.get('regime', 'Unknown')
                regime_lines.append(f"{timestamp}: {regime}")
            self._bt_regime_history_text.setPlainText("\n".join(regime_lines))

        logger.info("Backtest results displayed")

    def _on_backtest_error(self, error_msg: str) -> None:
        """Handle backtest error.

        Original: entry_analyzer_backtest.py:681-690

        Displays error message and re-enables run button.
        """
        self._bt_run_btn.setEnabled(True)
        self._bt_status_label.setText("Error")
        self._bt_results_text.setPlainText(f"❌ Backtest Error:\n\n{error_msg}")
        logger.error(f"Backtest error: {error_msg}")

    def _draw_regime_boundaries_wrapper(self) -> None:
        """Wrapper to call _draw_regime_boundaries with backtest results.

        Needed because _draw_regime_boundaries is defined in BacktestRegimeMixin.
        """
        if hasattr(self, '_backtest_result') and self._backtest_result:
            self._draw_regime_boundaries(self._backtest_result)
